"""Per-browser session grants for PIN-based helper switching."""

import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app, session
import flask_login
from sqlalchemy import select

from app.extensions import db
from app.models import PinUnlockSession, User
from app.services.pin_service import (
    PinError,
    hash_pin_code,
    normalize_pin,
    require_pin_mode,
)

SESSION_KEY = "pin_unlock_session_id"
IDLE_TIMEOUT = timedelta(seconds=60)
MAX_FAILED_ATTEMPTS = 5
MAX_COOLDOWN = timedelta(minutes=15)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def arm_pin_unlock_session(user_id: int) -> None:
    """Create a fresh PIN-switch grant after primary authentication succeeds."""
    previous_id = session.get(SESSION_KEY)
    if previous_id:
        PinUnlockSession.query.filter_by(session_id=previous_id).delete(
            synchronize_session=False
        )

    session_id = secrets.token_urlsafe(32)
    db.session.add(
        PinUnlockSession(session_id=session_id, active_user_id=user_id)
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


def expire_pin_session_if_idle(grant: PinUnlockSession) -> bool:
    if grant.is_locked:
        return True
    if grant.last_activity_at <= utc_now() - IDLE_TIMEOUT:
        grant.is_locked = True
        db.session.commit()
        return True
    return False


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
        grant.failed_attempts += 1
        if grant.failed_attempts >= MAX_FAILED_ATTEMPTS:
            grant.cooldown_level += 1
            cooldown_seconds = min(60 * (2 ** (grant.cooldown_level - 1)),
                                   int(MAX_COOLDOWN.total_seconds()))
            grant.locked_until = now + timedelta(seconds=cooldown_seconds)
            grant.failed_attempts = 0
        db.session.commit()
        raise PinError("PIN is incorrect", 401)

    grant.active_user_id = user.id
    grant.is_locked = False
    grant.last_activity_at = now
    grant.failed_attempts = 0
    grant.cooldown_level = 0
    grant.locked_until = None
    db.session.commit()
    return user