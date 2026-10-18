"""
OIDC login against Authentik (authorization code flow via Authlib).

Claims used (scope "repaircafe" is a custom Authentik scope mapping, see the
infrastructure repo's repaircafe-page-sso.yaml blueprint):
  sub, email, name, preferred_username, groups  — standard
  repaircafe_admin                              — admin role, managed in Authentik
  door_code                                     — member's door code, used as quick-unlock PIN
"""

import hashlib
import hmac
import json
import re
from typing import Optional

import flask_login
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, Response, current_app, redirect, request, session

from app.auth.decorators import public_endpoint
from app.extensions import db
from app.models import User

oidc_bp = Blueprint("oidc", __name__)

_DOOR_CODE_RE = re.compile(r"^\d{6}$")
_UNUSABLE_PASSWORD = "!"  # not a valid werkzeug hash, so check_password_hash always fails


def oidc_enabled(app=None) -> bool:
    cfg = (app or current_app).config
    return all(
        cfg.get(k)
        for k in ("OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "PUBLIC_URL")
    )


def init_oidc(app):
    """Register the Authentik client on the app (no-op when OIDC is not configured)."""
    if not oidc_enabled(app):
        app.logger.info("OIDC login disabled (OIDC_* / PUBLIC_URL not set)")
        return
    oauth = OAuth(app)
    app.extensions["oidc_client"] = oauth.register(
        "authentik",
        client_id=app.config["OIDC_CLIENT_ID"],
        client_secret=app.config["OIDC_CLIENT_SECRET"],
        server_metadata_url=app.config["OIDC_ISSUER"].rstrip("/")
        + "/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile repaircafe"},
    )


def hash_door_code(code: str) -> str:
    """Keyed hash of a door code. Without the server secret a database dump does
    not reveal door codes (a plain hash of 6 digits is brute-forced instantly)."""
    key = hashlib.sha256(
        b"repaircafe-door-code:" + current_app.config["SECRET_KEY"].encode()
    ).digest()
    return hmac.new(key, code.encode(), hashlib.sha256).hexdigest()


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
      200:
        description: Which login methods are available
    """
    return Response(
        json.dumps({"oidc_enabled": oidc_enabled()}),
        status=200,
        mimetype="application/json",
    )


@oidc_bp.route("/auth/oidc/login", methods=["GET"])
@public_endpoint
def oidc_login():
    """
    Start the SSO login (redirects to Authentik).
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
        description: Redirect to Authentik
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
    # prompt=login: the café PC is shared, so never silently reuse a previous
    # helper's Authentik session — always ask for credentials (and 2FA).
    return current_app.extensions["oidc_client"].authorize_redirect(
        _redirect_uri(), prompt="login"
    )


@oidc_bp.route("/auth/oidc/callback", methods=["GET"])
@public_endpoint
def oidc_callback():
    """
    SSO callback from Authentik; logs the user in and redirects into the app.
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

    denied = set(current_app.config["OIDC_DENIED_GROUPS"]) & set(claims.get("groups") or [])
    if denied:
        current_app.logger.info(f"OIDC login refused for groups {sorted(denied)}")
        return _login_error("forbidden")

    user = _upsert_user(claims)
    if user is None:
        return _login_error("account_conflict")
    if not user.is_active:
        return _login_error("disabled")

    flask_login.login_user(user, remember=False)
    current_app.logger.info(f"User '{user.username}' logged in via SSO")
    return redirect(_safe_next(session.pop("oidc_next", None)))


def _upsert_user(claims: dict) -> Optional[User]:
    """Find or create the local user for these claims and sync profile data."""
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
            username=_unique_username(claims.get("preferred_username") or email or sub),
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
    # Authentik is the source of truth for the role
    user.is_admin = bool(claims.get("repaircafe_admin"))
    _sync_door_code(user, claims.get("door_code"))

    db.session.commit()
    return user


def _sync_door_code(user: User, raw) -> None:
    code = str(raw).strip() if raw is not None else ""
    if not _DOOR_CODE_RE.match(code):
        if code:
            current_app.logger.warning(
                f"Ignoring door_code for '{user.username}': not 6 digits"
            )
        user.door_code_hash = None
        return
    digest = hash_door_code(code)
    # Door codes are unique per member; if a code was reassigned, drop it from
    # the previous holder so a PIN can never unlock two accounts.
    User.query.filter(User.door_code_hash == digest, User.id != user.id).update(
        {"door_code_hash": None}
    )
    user.door_code_hash = digest


def _unique_username(base: str) -> str:
    base = re.sub(r"[^\w.@-]", "", base)[:90] or "user"
    candidate, n = base, 1
    while User.query.filter_by(username=candidate).first():
        n += 1
        candidate = f"{base}{n}"
    return candidate
