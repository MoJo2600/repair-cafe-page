"""
Authentication routes blueprint — DB-backed Flask-Login with session cookies.
"""

import json
from urllib.parse import urlsplit

import flask_login
from flask import Blueprint, Response, current_app, request
from werkzeug.security import check_password_hash

from app.auth.decorators import login_required_api, public_endpoint
from app.auth.oidc import oidc_enabled
from app.extensions import db, login_manager
from app.models import User as DBUser
from app.schemas import LoginRequest, PinGeneratedResponse, PinGenerateRequest, PinStatusResponse
from app.schemas import UserResponse as UserResponseSchema
from app.validation import parse_request
from app.services.pin_service import PinError, generate_pin, require_pin_mode

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def user_loader(user_id: str):
    """Load a user from the DB by the primary key stored in the session cookie."""
    try:
        return db.session.get(DBUser, int(user_id))
    except Exception:
        return None


@auth_bp.route("/auth/login", methods=["POST"])
@public_endpoint
def api_login():
    """
    Authenticate with username and password.
    ---
    tags:
      - Auth
    operationId: login
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/LoginRequest'
    responses:
      200:
        description: Login successful, session cookie set
        schema:
          $ref: '#/definitions/AuthResponse'
      401:
        description: Invalid credentials
      403:
        description: Account disabled
    """
    body, err = parse_request(LoginRequest)
    if err:
        return err
    assert body is not None

    user = DBUser.query.filter_by(username=body.username).first()
    if not user or not check_password_hash(user.password_hash, body.password):
        return Response(
            json.dumps({"reply": "error", "error": "Invalid credentials"}),
            status=401,
            mimetype="application/json",
        )

    if not user.is_active:
        return Response(
            json.dumps({"reply": "error", "error": "Account is disabled"}),
            status=403,
            mimetype="application/json",
        )

    # With SSO enabled, password login is only the break-glass path for local admins.
    if oidc_enabled() and (user.oidc_sub or not user.is_admin):
        return Response(
            json.dumps(
                {"reply": "error", "error": "Bitte mit SSO anmelden"}
            ),
            status=403,
            mimetype="application/json",
        )

    flask_login.login_user(user, remember=False)
    current_app.logger.info(f"User '{user.username}' logged in")
    return Response(
        json.dumps(
            {
                "reply": "done",
                "data": UserResponseSchema.model_validate(user).model_dump(mode="json"),
            }
        ),
        status=200,
        mimetype="application/json",
    )


@auth_bp.route("/auth/me", methods=["GET"])
@login_required_api
def api_me():
    """
    Return the currently authenticated user's profile.
    ---
    tags:
      - Auth
    operationId: me
    responses:
      200:
        description: Current user profile
        schema:
          $ref: '#/definitions/AuthResponse'
      401:
        description: Not authenticated
    """
    user = flask_login.current_user
    return Response(
        json.dumps(
            {
                "reply": "done",
                "data": UserResponseSchema.model_validate(user).model_dump(mode="json"),
            }
        ),
        status=200,
        mimetype="application/json",
    )


@auth_bp.route("/auth/logout", methods=["POST"])
@login_required_api
def api_logout():
    """
    Invalidate the current session cookie.
    ---
    tags:
      - Auth
    operationId: logout
    responses:
      200:
        description: Logged out successfully
        schema:
          $ref: '#/definitions/APIResponse'
      401:
        description: Not authenticated
    """
    current_app.logger.info(
        f"User '{flask_login.current_user.username}' logged out")
    flask_login.logout_user()
    return Response(
        json.dumps({"reply": "done"}),
        status=200,
        mimetype="application/json",
    )


@auth_bp.route("/auth/me/pin", methods=["GET"])
@login_required_api
def api_pin_status():
    """
    Return the current user's PIN status, never the PIN itself.
    ---
    tags:
      - Auth
    operationId: pinStatus
    responses:
      200:
        description: PIN mode and availability
        schema:
          $ref: '#/definitions/PinStatusResponse'
      401:
        description: Not authenticated
      403:
        description: Account disabled
      503:
        description: Deployment PIN mode mismatch
    """
    if not flask_login.current_user.is_active:
        return _pin_error("Account is disabled", 403)
    try:
        mode = require_pin_mode()
        db.session.refresh(flask_login.current_user._get_current_object())
        result = PinStatusResponse(
            mode=mode,
            has_pin=flask_login.current_user.pin_code_hash is not None,
            can_generate=mode == "local",
        )
        db.session.rollback()
        return _pin_response(result)
    except PinError as error:
        db.session.rollback()
        return _pin_error(str(error), error.status)


@auth_bp.route("/auth/me/pin", methods=["POST"])
@login_required_api
def api_generate_pin():
    """
    Generate or explicitly replace the current user's local PIN, revealing it once.
    ---
    tags:
      - Auth
    operationId: generatePin
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/PinGenerateRequest'
    responses:
      200:
        description: New PIN, shown only in this response
        schema:
          $ref: '#/definitions/PinGeneratedResponse'
      400:
        description: Invalid request
      401:
        description: Not authenticated
      403:
        description: Provider-managed PIN, disabled account or cross-site request
      409:
        description: PIN exists and replacement was not confirmed
      503:
        description: PIN allocation unavailable
    """
    origin = request.headers.get("Origin")
    if origin:
        source = urlsplit(origin)
        allowed = [urlsplit(request.host_url)]
        if current_app.config.get("PUBLIC_URL"):
            allowed.append(urlsplit(current_app.config["PUBLIC_URL"]))
        if not any((source.scheme, source.netloc) == (target.scheme, target.netloc)
                   for target in allowed):
            return _pin_error("Cross-site PIN changes are not allowed", 403)
    if request.headers.get("Sec-Fetch-Site") == "cross-site":
        return _pin_error("Cross-site PIN changes are not allowed", 403)
    if not request.is_json:
        return _pin_error("A JSON request body is required", 400)
    if not isinstance(request.get_json(silent=True), dict):
        return _pin_error("A JSON object is required", 400)
    body, error = parse_request(PinGenerateRequest)
    if error:
        return error
    assert body is not None
    try:
        code = generate_pin(flask_login.current_user.id, replace=body.replace)
        return _pin_response(PinGeneratedResponse(pin_code=code))
    except PinError as error:
        db.session.rollback()
        return _pin_error(str(error), error.status)


def _pin_response(result):
    return Response(result.model_dump_json(), mimetype="application/json",
                    headers={"Cache-Control": "no-store"})


def _pin_error(message, status):
    return Response(json.dumps({"reply": "error", "error": message}), status=status,
                    mimetype="application/json", headers={"Cache-Control": "no-store"})
