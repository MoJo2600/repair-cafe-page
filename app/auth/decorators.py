"""
Auth decorators for protecting API endpoints.
"""

import json
from functools import wraps

import flask_login
from flask import Response


def login_required_api(f):
    """Like @login_required but returns 401 JSON instead of redirecting."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not flask_login.current_user.is_authenticated:
            return Response(
                json.dumps({"reply": "error", "error": "Authentication required"}),
                status=401,
                mimetype="application/json",
            )
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Requires the current user to be authenticated AND is_admin=True."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not flask_login.current_user.is_authenticated:
            return Response(
                json.dumps({"reply": "error", "error": "Authentication required"}),
                status=401,
                mimetype="application/json",
            )
        if not flask_login.current_user.is_admin:
            return Response(
                json.dumps({"reply": "error", "error": "Admin access required"}),
                status=403,
                mimetype="application/json",
            )
        return f(*args, **kwargs)

    return decorated
