"""
Authentication routes blueprint — DB-backed Flask-Login with session cookies.
"""

import json

import flask_login
from flask import Blueprint, Response, current_app
from werkzeug.security import check_password_hash

from app.auth.decorators import login_required_api
from app.extensions import db, login_manager
from app.models import User as DBUser
from app.schemas import LoginRequest
from app.schemas import UserResponse as UserResponseSchema
from app.validation import parse_request

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def user_loader(user_id: str):
    """Load a user from the DB by the primary key stored in the session cookie."""
    try:
        return db.session.get(DBUser, int(user_id))
    except Exception:
        return None


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    """Authenticate with username + password; sets an HTTP-only session cookie."""
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


@auth_bp.route("/api/auth/me", methods=["GET"])
@login_required_api
def api_me():
    """Return the currently authenticated user's profile."""
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


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required_api
def api_logout():
    """Invalidate the session cookie."""
    current_app.logger.info(f"User '{flask_login.current_user.username}' logged out")
    flask_login.logout_user()
    return Response(
        json.dumps({"reply": "done"}),
        status=200,
        mimetype="application/json",
    )
