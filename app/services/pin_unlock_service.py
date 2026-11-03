"""Per-browser session grants for PIN-based helper switching."""

import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app, request, session
import flask_login
from sqlalchemy import func, select

from app.extensions import db
from app.models import PinUnlockFailure, PinUnlockSession, User
from app.services.pin_service import (
    PinError,
    hash_pin_code,
    normalize_pin,
    require_pin_mode,
)

SESSION_KEY = "pin_unlock_session_id"
IDLE_TIMEOUT = timedelta(seconds=60)
# Short pause after every few wrong PINs; the hard limit is PIN_MAX_FAILED_PER_SESSION
COOLDOWN_EVERY = 3
COOLDOWN = timedelta(seconds=60)
FAILURE_RETENTION = timedelta(hours=24)

# Headers the Cloudflare edge sets on every request through the tunnel. A client
# cannot remove them; adding them on the LAN only disables PIN unlock for itself.
_CLOUDFLARE_HEADERS = ("Cf-Ray", "Cf-Connecting-Ip", "Cf-Access-Jwt-Assertion")


class PinSessionRevoked(PinError):
    """Too many wrong PINs: the browser session must log in again."""

    def __init__(self):
        super().__init__("Too many incorrect PINs; please log in again", 401)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def request_via_cloudflare() -> bool:
    return any(request.headers.get(name) for name in _CLOUDFLARE_HEADERS)


def pin_unlock_available() -> bool:
    """PIN locking/switching is only offered inside the workshop network."""
    return not request_via_cloudflare()


def arm_pin_unlock_session(user_id: int) -> None:
    """Create a fresh PIN-switch grant after primary authentication succeeds."""
    previous_id = session.get(SESSION_KEY)
    if previous_id:
        PinUnlockSession.query.filter_by(session_id=previous_id).delete(
            synchronize_session=False
        )

    session_id = secrets.token_urlsafe(32)
    db.session.add(
        PinUnlockSession(
            session_id=session_id, active_user_id=user_id, primary_user_id=user_id
        )
    )
    db.session.commit()
    session[SESSION_KEY] = session_id


def current_pin_session() -> PinUnlockSession | None:
    session_id = session.get(SESSION_KEY)
    if not session_id:
        return None
    return db.session.get(PinUnlockSession, session_id)


def revoke_pin_unlock_session() -> None:
    session_id = session.pop(SESSION_KEY, None)
    if session_id:
        PinUnlockSession.query.filter_by(session_id=session_id).delete(
            synchronize_session=False
        )
        db.session.commit()


def end_browser_session() -> None:
    """Revoke the PIN grant and the primary login of this browser."""
    revoke_pin_unlock_session()
    flask_login.logout_user()


def expire_pin_session_if_idle(grant: PinUnlockSession) -> bool:
    if grant.is_locked:
        return True
    if not grant.auto_lock_enabled:
        return False
    if grant.last_activity_at <= utc_now() - IDLE_TIMEOUT:
        grant.is_locked = True
        db.session.commit()
        return True
    return False


def set_auto_lock(enabled: bool) -> PinUnlockSession:
    """Switch the idle auto-lock for the current browser session."""
    grant = current_pin_session()
    if not grant:
        raise PinError("PIN session is unavailable", 401)
    grant.auto_lock_enabled = enabled
    if enabled:
        # Start a fresh idle period instead of locking right away
        grant.last_activity_at = utc_now()
    db.session.commit()
    return grant


def lock_pin_session() -> None:
    grant = current_pin_session()
    if not grant:
        raise PinError("PIN session is unavailable", 401)
    grant.is_locked = True
    db.session.commit()


def record_pin_activity() -> bool:
    grant = current_pin_session()
    if not grant:
        raise PinError("PIN session is unavailable", 401)
    if expire_pin_session_if_idle(grant):
        return False
    grant.last_activity_at = utc_now()
    db.session.commit()
    return True


def _check_rate_limits(grant: PinUnlockSession, now: datetime) -> None:
    """Reject before looking at the PIN, so a lockout is not a PIN oracle."""
    cfg = current_app.config
    since = now - timedelta(minutes=cfg["PIN_RATE_WINDOW_MINUTES"])
    recent = PinUnlockFailure.query.filter(PinUnlockFailure.created_at > since)
    global_count = recent.with_entities(func.count(PinUnlockFailure.id)).scalar()
    if global_count >= cfg["PIN_MAX_FAILED_GLOBAL"]:
        current_app.logger.warning(
            "PIN unlock paused globally: %d wrong PINs in %d min",
            global_count, cfg["PIN_RATE_WINDOW_MINUTES"],
        )
        raise PinError("PIN unlock is temporarily paused; please log in via SSO", 429)
    if grant.primary_user_id is not None:
        account_count = (
            recent.filter(PinUnlockFailure.primary_user_id == grant.primary_user_id)
            .with_entities(func.count(PinUnlockFailure.id))
            .scalar()
        )
        if account_count >= cfg["PIN_MAX_FAILED_PER_ACCOUNT"]:
            current_app.logger.warning(
                "PIN unlock blocked for account %s: %d wrong PINs in %d min",
                grant.primary_user_id, account_count, cfg["PIN_RATE_WINDOW_MINUTES"],
            )
            raise PinError("Too many attempts; try again later", 429)


def _record_failure(grant: PinUnlockSession, now: datetime) -> None:
    PinUnlockFailure.query.filter(
        PinUnlockFailure.created_at < now - FAILURE_RETENTION
    ).delete(synchronize_session=False)
    db.session.add(
        PinUnlockFailure(
            created_at=now,
            session_id=grant.session_id,
            primary_user_id=grant.primary_user_id,
        )
    )
    grant.failed_attempts += 1
    if grant.failed_attempts >= current_app.config["PIN_MAX_FAILED_PER_SESSION"]:
        current_app.logger.warning(
            "PIN session of account %s revoked after %d wrong PINs",
            grant.primary_user_id, grant.failed_attempts,
        )
        db.session.delete(grant)
        db.session.commit()
        session.pop(SESSION_KEY, None)
        raise PinSessionRevoked()
    if grant.failed_attempts % COOLDOWN_EVERY == 0:
        grant.cooldown_level += 1
        grant.locked_until = now + COOLDOWN
    db.session.commit()


def unlock_pin_session(code: str) -> User:
    require_pin_mode()
    session_id = session.get(SESSION_KEY)
    grant = None
    if session_id:
        grant = db.session.execute(
            select(PinUnlockSession)
            .where(PinUnlockSession.session_id == session_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()
    if not grant or not grant.is_locked:
        raise PinError("PIN unlock is unavailable", 401)

    now = utc_now()
    if grant.locked_until and grant.locked_until > now:
        raise PinError("Too many attempts; try again later", 429)
    _check_rate_limits(grant, now)

    normalized = normalize_pin(code)
    user = None
    if normalized:
        user = db.session.execute(
            select(User).where(
                User.pin_code_hash == hash_pin_code(normalized),
                User.is_active.is_(True),
            )
        ).scalar_one_or_none()

    if user is None:
        _record_failure(grant, now)
        raise PinError("PIN is incorrect", 401)

    grant.active_user_id = user.id
    grant.is_locked = False
    grant.last_activity_at = now
    grant.failed_attempts = 0
    grant.cooldown_level = 0
    grant.locked_until = None
    db.session.commit()
    return user
