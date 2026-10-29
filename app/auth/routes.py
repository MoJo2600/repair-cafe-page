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
from app.models import Repair
from app.models import User as DBUser
from app.schemas import (
    AuthResponse,
    LoginRequest,
    PinDashboardSummaryResponse,
    PinGeneratedResponse,
    PinGenerateRequest,
    PinSessionActionResponse,
    PinSessionStatusResponse,
    PinStatusResponse,
    PinUnlockRequest,
    RepairsTimelinePoint,
)
from app.schemas import UserResponse as UserResponseSchema
from app.services.pin_service import PinError, generate_pin, require_pin_mode
from app.services.pin_unlock_service import (
    arm_pin_unlock_session,
    current_pin_session,
    expire_pin_session_if_idle,
    lock_pin_session,
    record_pin_activity,
    revoke_pin_unlock_session,
    unlock_pin_session,
    utc_now,
)
from app.validation import parse_request

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
            json.dumps({"reply": "error", "error": "Bitte mit SSO anmelden"}),
            status=403,
            mimetype="application/json",
        )

    flask_login.login_user(user, remember=False)
    try:
        arm_pin_unlock_session(user.id)
    except Exception:
        db.session.rollback()
        flask_login.logout_user()
        current_app.logger.exception("Could not establish PIN session after login")
        return Response(
            json.dumps({"reply": "error", "error": "Login temporarily unavailable"}),
            status=503,
            mimetype="application/json",
        )
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
    if not _same_origin_request():
        return _pin_error("Cross-site session changes are not allowed", 403)
    username = (
        flask_login.current_user.username
        if flask_login.current_user.is_authenticated
        else None
    )
    revoke_pin_unlock_session()
    flask_login.logout_user()
    if username:
        current_app.logger.info("User '%s' logged out", username)
    return Response(
        json.dumps({"reply": "done"}),
        status=200,
        mimetype="application/json",
    )


@auth_bp.route("/auth/pin-session", methods=["GET"])
def api_pin_session_status():
    """
    Return whether the current authenticated browser session is unlocked.
    ---
    tags:
      - Auth
    operationId: pinSessionStatus
    responses:
      200:
        description: PIN session state
        schema:
          $ref: '#/definitions/PinSessionStatusResponse'
      401:
        description: Primary login required
    """
    grant = _get_pin_session()
    if isinstance(grant, Response):
        return grant
    locked = expire_pin_session_if_idle(grant)
    result = PinSessionStatusResponse(
        eligible=True,
        locked=locked,
        user=(
            None
            if locked
            else UserResponseSchema.model_validate(
                flask_login.current_user._get_current_object()
            )
        ),
    )
    return _pin_response(result)


@auth_bp.route("/auth/pin-session/lock", methods=["POST"])
def api_pin_lock():
    """
    Lock the current authenticated browser session.
    ---
    tags:
      - Auth
    operationId: lockPinSession
    responses:
      200:
        description: Session locked
        schema:
          $ref: '#/definitions/PinSessionActionResponse'
      401:
        description: Primary login required
    """
    if not _same_origin_request():
        return _pin_error("Cross-site session changes are not allowed", 403)
    grant = _get_pin_session()
    if isinstance(grant, Response):
        return grant
    lock_pin_session()
    return _pin_response(PinSessionActionResponse(locked=True))


@auth_bp.route("/auth/pin-session/activity", methods=["POST"])
def api_pin_activity():
    """
    Record real user activity for the session idle timeout.
    ---
    tags:
      - Auth
    operationId: recordPinSessionActivity
    responses:
      200:
        description: Session remains unlocked
        schema:
          $ref: '#/definitions/PinSessionActionResponse'
      401:
        description: Primary login required
      423:
        description: Session has expired and is locked
    """
    if not _same_origin_request():
        return _pin_error("Cross-site session changes are not allowed", 403)
    grant = _get_pin_session()
    if isinstance(grant, Response):
        return grant
    if not record_pin_activity():
        return _pin_error("Session locked", 423)
    return _pin_response(PinSessionActionResponse(locked=False))


@auth_bp.route("/auth/pin-session/unlock", methods=["POST"])
def api_pin_unlock():
    """
    Switch to the active helper who owns the submitted PIN.
    ---
    tags:
      - Auth
    operationId: unlockPinSession
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/PinUnlockRequest'
    responses:
      200:
        description: Session unlocked as the PIN owner
        schema:
          $ref: '#/definitions/AuthResponse'
      400:
        description: Invalid request
      401:
        description: Incorrect PIN or primary login required
      429:
        description: PIN attempts temporarily limited
      423:
        description: Session is not locked
    """
    if not _same_origin_request():
        return _pin_error("Cross-site session changes are not allowed", 403)
    grant = _get_pin_session()
    if isinstance(grant, Response):
        return grant
    if not grant.is_locked:
        return _pin_error("Session must be locked before PIN unlock", 423)
    if not request.is_json or not isinstance(request.get_json(silent=True), dict):
        return _pin_error("A JSON object is required", 400)
    body, error = parse_request(PinUnlockRequest)
    if error:
        return _pin_error("PIN is incorrect", 401)
    assert body is not None
    try:
        user = unlock_pin_session(body.pin_code)
    except PinError as error:
        db.session.rollback()
        return _pin_error(str(error), error.status)
    flask_login.login_user(user, remember=False, fresh=True)
    return _pin_response(
        AuthResponse(reply="done", data=UserResponseSchema.model_validate(user))
    )


@auth_bp.route("/auth/pin-session/dashboard", methods=["GET"])
def api_pin_dashboard_summary():
    """
    Return aggregate dashboard metrics allowed on the PIN lock screen.
    ---
    tags:
      - Auth
    operationId: pinDashboardSummary
    responses:
      200:
        description: Non-identifying dashboard metrics and next repair ID
        schema:
          $ref: '#/definitions/PinDashboardSummaryResponse'
      401:
        description: Primary login required
      403:
        description: Session is not locked
    """
    grant = _get_pin_session()
    if isinstance(grant, Response):
        return grant
    if not grant.is_locked:
        return _pin_error("Dashboard summary is only available while locked", 403)

    from collections import defaultdict
    from datetime import date, timedelta

    from sqlalchemy import func

    counts = dict(
        db.session.query(Repair.status, func.count(Repair.id))
        .group_by(Repair.status)
        .all()
    )
    total = sum(counts.values())
    repaired = counts.get("Repariert", 0)
    not_repaired = counts.get("Nicht Repariert", 0)
    denominator = repaired + not_repaired
    cutoff = date.today() - timedelta(days=365)
    rows = (
        db.session.query(Repair.datum, Repair.status)
        .filter(Repair.datum >= cutoff)
        .all()
    )
    weekly_counts = defaultdict(lambda: defaultdict(int))
    for row in rows:
        year, week, _ = row.datum.isocalendar()
        weekly_counts[f"{year}-{week:02d}"][row.status] += 1
    timeline = []
    for week_key in sorted(weekly_counts):
        year, week = week_key.split("-")
        label = f"KW {int(week)} {year}"
        timeline.append(
            RepairsTimelinePoint(
                week=week_key,
                label=label,
                offen=weekly_counts[week_key].get("Offen", 0),
                in_bearbeitung=weekly_counts[week_key].get("In Bearbeitung", 0),
                abgeschlossen=weekly_counts[week_key].get("Repariert", 0),
                nicht_repariert=weekly_counts[week_key].get("Nicht Repariert", 0),
            )
        )
    result = PinDashboardSummaryResponse(
        total_repairs=total,
        open_repairs=counts.get("Offen", 0),
        next_repair_id=db.session.query(func.min(Repair.id))
        .filter(Repair.status == "Offen")
        .scalar(),
        in_progress_repairs=counts.get("In Bearbeitung", 0),
        repaired_repairs=repaired,
        not_repaired_repairs=not_repaired,
        success_rate=round(repaired / denominator * 100) if denominator else None,
        timeline=timeline,
    )
    return _pin_response(result)


def _get_pin_session():
    if not flask_login.current_user.is_authenticated:
        return _pin_error("Primary login required", 401)
    grant = current_pin_session()
    if not grant or grant.active_user_id != flask_login.current_user.id:
        return _pin_error("Primary login required", 401)
    return grant


def _same_origin_request() -> bool:
    origin = request.headers.get("Origin")
    if origin:
        source = urlsplit(origin)
        allowed = [urlsplit(request.host_url)]
        if current_app.config.get("PUBLIC_URL"):
            allowed.append(urlsplit(current_app.config["PUBLIC_URL"]))
        if not any(
            (source.scheme, source.netloc) == (target.scheme, target.netloc)
            for target in allowed
        ):
            request_origin = urlsplit(request.host_url)
            development_proxy = (
                current_app.debug
                and source.scheme == request_origin.scheme
                and source.hostname == request_origin.hostname
                and source.hostname in {"localhost", "127.0.0.1", "::1"}
            )
            if not development_proxy:
                return False
    return request.headers.get("Sec-Fetch-Site") != "cross-site"


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
    if not _same_origin_request():
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
    return Response(
        result.model_dump_json(),
        mimetype="application/json",
        headers={"Cache-Control": "no-store"},
    )


def _pin_error(message, status):
    return Response(
        json.dumps({"reply": "error", "error": message}),
        status=status,
        mimetype="application/json",
        headers={"Cache-Control": "no-store"},
    )
