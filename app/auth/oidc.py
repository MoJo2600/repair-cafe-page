"""Provider-neutral OIDC authorization code flow via Authlib."""

import json
import re
from typing import Optional

import flask_login
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, Response, current_app, redirect, request, session

from app.auth.decorators import public_endpoint
from app.extensions import db
from app.models import User
from app.schemas import AuthConfigResponse
from app.services.pin_service import PinError, pin_transaction, require_pin_mode, sync_provider_pin

oidc_bp = Blueprint("oidc", __name__)

# not a valid werkzeug hash, so check_password_hash always fails
_UNUSABLE_PASSWORD = "!"


def oidc_enabled(app=None) -> bool:
    cfg = (app or current_app).config
    return all(
        cfg.get(k)
        for k in ("OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "PUBLIC_URL")
    )


def init_oidc(app):
    """Register the provider client when OIDC is configured."""
    if not oidc_enabled(app):
        app.logger.info("OIDC login disabled (OIDC_* / PUBLIC_URL not set)")
        return
    oauth = OAuth(app)
    app.extensions["oidc_client"] = oauth.register(
        "oidc",
        client_id=app.config["OIDC_CLIENT_ID"],
        client_secret=app.config["OIDC_CLIENT_SECRET"],
        server_metadata_url=app.config["OIDC_ISSUER"].rstrip("/")
        + "/.well-known/openid-configuration",
        client_kwargs={"scope": app.config["OIDC_SCOPES"]},
    )


def _redirect_uri() -> str:
    return current_app.config["PUBLIC_URL"] + "/api/auth/oidc/callback"


def _safe_next(target: Optional[str]) -> str:
    """Only allow same-site relative paths as post-login redirect targets."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return "/"


def _login_error(code: str):
    return redirect(f"/login?error={code}")


@oidc_bp.route("/auth/config", methods=["GET"])
@public_endpoint
def auth_config():
    """
    Login options for the login page.
    ---
    tags:
      - Auth
    operationId: authConfig
    responses:
            200: {description: Login methods, schema: {$ref: '#/definitions/AuthConfigResponse'}}
    """
    return Response(
        AuthConfigResponse(oidc_enabled=oidc_enabled()).model_dump_json(),
        status=200,
        mimetype="application/json",
    )


@oidc_bp.route("/auth/oidc/login", methods=["GET"])
@public_endpoint
def oidc_login():
    """
    Start the SSO login (redirects to the identity provider).
    ---
    tags:
      - Auth
    operationId: oidcLogin
    parameters:
      - in: query
        name: next
        type: string
        required: false
        description: Relative path to return to after login
    responses:
      302:
        description: Redirect to the identity provider
      404:
        description: OIDC not configured
    """
    if not oidc_enabled():
        return Response(
            json.dumps({"reply": "error", "error": "SSO is not configured"}),
            status=404,
            mimetype="application/json",
        )
    session["oidc_next"] = _safe_next(request.args.get("next"))
    return current_app.extensions["oidc_client"].authorize_redirect(
        _redirect_uri(), prompt="login"
    )


@oidc_bp.route("/auth/oidc/callback", methods=["GET"])
@public_endpoint
def oidc_callback():
    """
    SSO callback; logs the user in and redirects into the app.
    ---
    tags:
      - Auth
    operationId: oidcCallback
    responses:
      302:
        description: Redirect into the app, or to /login?error=... on failure
    """
    if not oidc_enabled():
        return _login_error("sso_unavailable")
    try:
        token = current_app.extensions["oidc_client"].authorize_access_token()
    except Exception as e:
        current_app.logger.warning(f"OIDC callback failed: {e}")
        return _login_error("sso_failed")

    claims = token.get("userinfo") or {}
    if not claims.get("sub"):
        current_app.logger.warning("OIDC callback without sub claim")
        return _login_error("sso_failed")

    groups = claims.get(current_app.config["OIDC_GROUPS_CLAIM"]) or []
    if isinstance(groups, str):
        groups = [groups]
    if not isinstance(groups, list):
        groups = []
    denied = set(current_app.config["OIDC_DENIED_GROUPS"]) & {
        group for group in groups if isinstance(group, str)
    }
    if denied:
        current_app.logger.info(
            f"OIDC login refused for groups {sorted(denied)}")
        return _login_error("forbidden")

    try:
        user = _upsert_user(claims)
    except PinError:
        db.session.rollback()
        return _login_error("sso_unavailable")
    if user is None:
        return _login_error("account_conflict")
    if not user.is_active:
        return _login_error("disabled")

    flask_login.login_user(user, remember=False)
    current_app.logger.info(f"User '{user.username}' logged in via SSO")
    return redirect(_safe_next(session.pop("oidc_next", None)))


@pin_transaction
def _upsert_user(claims: dict) -> Optional[User]:
    """Find or create the local user for these claims and sync profile data."""
    require_pin_mode()
    sub = claims["sub"]
    email = (claims.get("email") or "").strip().lower() or None

    user = User.query.filter_by(oidc_sub=sub).first()
    if user is None and email:
        # Adopt a pre-existing local repairer account with the same e-mail.
        # Local admins are never adopted — they stay the break-glass login.
        user = User.query.filter(
            db.func.lower(User.email) == email,
            User.oidc_sub.is_(None),
            User.is_admin.is_(False),
        ).first()

    if user is None:
        if email and User.query.filter(db.func.lower(User.email) == email).first():
            current_app.logger.warning(
                "OIDC login: e-mail already used by a local admin account"
            )
            return None
        user = User(
            username=_unique_username(claims.get(
                "preferred_username") or email or sub),
            email=email or f"{sub[:40]}@sso.invalid",
            password_hash=_UNUSABLE_PASSWORD,
        )
        db.session.add(user)

    user.oidc_sub = sub
    vorname, _, nachname = (claims.get("name") or "").strip().partition(" ")
    if vorname:
        user.vorname, user.nachname = vorname, nachname or None
    if email and email != (user.email or "").lower():
        if not User.query.filter(db.func.lower(User.email) == email, User.id != user.id).first():
            user.email = email
    admin = claims.get(current_app.config["OIDC_ADMIN_CLAIM"])
    user.is_admin = admin is True or (
        isinstance(admin, str) and admin.lower() == "true")
    sync_provider_pin(user, claims.get(current_app.config["OIDC_PIN_CLAIM"]))

    db.session.commit()
    return user


def _unique_username(base: str) -> str:
    base = re.sub(r"[^\w.@-]", "", base)[:90] or "user"
    candidate, n = base, 1
    while User.query.filter_by(username=candidate).first():
        n += 1
        candidate = f"{base}{n}"
    return candidate
