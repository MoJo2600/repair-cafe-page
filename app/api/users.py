"""
Users API endpoints (Reparateur accounts).
"""

import json

from flask import Blueprint, Response, current_app, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth.decorators import admin_required, login_required_api
from app.extensions import db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate
from app.validation import parse_request

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
def api_list_users():
    """List all users."""
    try:
        users = User.query.order_by(User.nachname, User.vorname).all()
        data = [UserResponse.model_validate(u).model_dump(mode="json") for u in users]
        return Response(
            json.dumps({"reply": "done", "data": data, "count": len(data)}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error listing users: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@users_bp.route("/users/<int:user_id>", methods=["GET"])
def api_get_user(user_id):
    """Get a single user by ID."""
    user = db.session.get(User, user_id)
    if not user:
        return Response(
            json.dumps({"reply": "error", "error": "User not found"}),
            status=404,
            mimetype="application/json",
        )
    return Response(
        json.dumps(
            {
                "reply": "done",
                "data": UserResponse.model_validate(user).model_dump(mode="json"),
            }
        ),
        status=200,
        mimetype="application/json",
    )


@users_bp.route("/users", methods=["POST"])
@admin_required
def api_create_user():
    """Create a new user."""
    body, err = parse_request(UserCreate)
    if err:
        return err

    if User.query.filter_by(email=body.email).first():
        return Response(
            json.dumps({"reply": "error", "error": "Email already in use"}),
            status=409,
            mimetype="application/json",
        )

    try:
        from datetime import datetime

        user = User(
            username=body.username,
            vorname=body.vorname,
            nachname=body.nachname,
            email=body.email,
            password_hash=generate_password_hash(body.password),
            is_admin=body.is_admin,
            is_active=body.is_active,
            created_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()
        return Response(
            json.dumps(
                {
                    "reply": "done",
                    "data": UserResponse.model_validate(user).model_dump(mode="json"),
                }
            ),
            status=201,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating user: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def api_update_user(user_id):
    """Update an existing user."""
    user = db.session.get(User, user_id)
    if not user:
        return Response(
            json.dumps({"reply": "error", "error": "User not found"}),
            status=404,
            mimetype="application/json",
        )

    body, err = parse_request(UserUpdate)
    if err:
        return err

    try:
        if body.username is not None:
            if User.query.filter(
                User.username == body.username, User.id != user_id
            ).first():
                return Response(
                    json.dumps({"reply": "error", "error": "Username already in use"}),
                    status=409,
                    mimetype="application/json",
                )
            user.username = body.username
        if body.vorname is not None:
            user.vorname = body.vorname
        if body.nachname is not None:
            user.nachname = body.nachname
        if body.email is not None:
            conflict = User.query.filter(
                User.email == body.email, User.id != user_id
            ).first()
            if conflict:
                return Response(
                    json.dumps({"reply": "error", "error": "Email already in use"}),
                    status=409,
                    mimetype="application/json",
                )
            user.email = body.email
        if body.password is not None:
            user.password_hash = generate_password_hash(body.password)
        if body.is_admin is not None:
            user.is_admin = body.is_admin
        if body.is_active is not None:
            user.is_active = body.is_active

        db.session.commit()
        return Response(
            json.dumps(
                {
                    "reply": "done",
                    "data": UserResponse.model_validate(user).model_dump(mode="json"),
                }
            ),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def api_delete_user(user_id):
    """Soft-delete a user by setting is_active=False."""
    user = db.session.get(User, user_id)
    if not user:
        return Response(
            json.dumps({"reply": "error", "error": "User not found"}),
            status=404,
            mimetype="application/json",
        )
    try:
        user.is_active = False
        db.session.commit()
        return Response(
            json.dumps({"reply": "done"}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deactivating user: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )
