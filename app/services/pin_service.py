"""Provider-neutral PIN ownership and deployment mode management."""

import hashlib
import hmac
import re
import secrets
from functools import wraps

from flask import current_app
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models import PinState, User

_PIN_RE = re.compile(r"[0-9]{6}")
_MAX_ATTEMPTS = 20


class PinError(Exception):
    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status


def pin_transaction(operation):
    @wraps(operation)
    def run(*args, **kwargs):
        for attempt in range(3):
            db.session.rollback()
            try:
                return operation(*args, **kwargs)
            except OperationalError as error:
                db.session.rollback()
                code = error.orig.args[0] if error.orig.args else None
                if code not in (1020, 1205, 1213, 3572):
                    raise
                if attempt == 2:
                    raise PinError("PIN storage is busy; please try again", 503) from error
    return run


def hash_pin_code(code: str) -> str:
    """Keep the original HMAC domain so migrated hashes remain usable."""
    key = hashlib.sha256(
        b"repaircafe-door-code:" + current_app.config["SECRET_KEY"].encode()
    ).digest()
    return hmac.new(key, code.encode(), hashlib.sha256).hexdigest()


def normalize_pin(raw) -> str | None:
    code = str(raw).strip() if raw is not None else ""
    return code if _PIN_RE.fullmatch(code) else None


@pin_transaction
def reconcile_pin_mode() -> None:
    mode = current_app.config["PIN_MODE"]
    if mode not in ("local", "oidc"):
        raise RuntimeError("PIN_MODE must be local or oidc")
    if not current_app.config["OIDC_SCOPES"].strip():
        raise RuntimeError("OIDC_SCOPES must not be empty")
    if db.session.get(PinState, 1) is None:
        try:
            with db.session.begin_nested():
                legacy = User.query.filter(User.pin_code_hash.is_not(None)).first()
                db.session.add(PinState(id=1, mode="oidc" if legacy else mode))
                db.session.flush()
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    state = _lock_state()
    if state.mode != mode:
        transition = f"{state.mode}-to-{mode}"
        if current_app.config["PIN_MODE_RESET_ACK"] != transition:
            db.session.rollback()
            raise RuntimeError(
                f"PIN mode change {transition} deletes ALL existing PINs. "
                f"Back up the database, stop old workers and set "
                f"PIN_MODE_RESET_ACK={transition} to acknowledge."
            )
        count = User.query.filter(User.pin_code_hash.is_not(None)).update(
            {"pin_code_hash": None}, synchronize_session=False
        )
        current_app.logger.warning(
            "PIN MODE CHANGE %s: invalidating %d PINs", transition, count
        )
        state.mode = mode
    db.session.commit()


def require_pin_mode(expected: str | None = None) -> str:
    state = _lock_state()
    mode = current_app.config["PIN_MODE"]
    if state.mode != mode:
        raise PinError("PIN deployment mode changed; restart this service", 503)
    if expected is not None and mode != expected:
        raise PinError("PINs are managed by your identity provider", 403)
    return mode


def _lock_state() -> PinState:
    db.session.execute(update(PinState).where(PinState.id == 1).values(mode=PinState.mode))
    return PinState.query.filter_by(id=1).populate_existing().with_for_update().one()


def sync_provider_pin(user: User, raw) -> None:
    mode = require_pin_mode()
    if mode != "oidc":
        return
    code = normalize_pin(raw)
    if code is None:
        user.pin_code_hash = None
        return
    digest = hash_pin_code(code)
    User.query.filter(User.pin_code_hash == digest, User.id != user.id).update(
        {"pin_code_hash": None}, synchronize_session="fetch"
    )
    db.session.flush()
    user.pin_code_hash = digest


@pin_transaction
def generate_pin(user_id: int, replace: bool = False) -> str:
    require_pin_mode("local")
    user = User.query.filter_by(id=user_id).with_for_update().populate_existing().one()
    if not user.is_active:
        raise PinError("Account is disabled", 403)
    previous = user.pin_code_hash
    if previous and not replace:
        raise PinError("A PIN already exists; confirm replacement")
    for _ in range(_MAX_ATTEMPTS):
        code = f"{secrets.randbelow(1_000_000):06d}"
        digest = hash_pin_code(code)
        if digest == previous:
            continue
        try:
            with db.session.begin_nested():
                user.pin_code_hash = digest
                db.session.flush()
            db.session.commit()
            return code
        except IntegrityError:
            continue
    raise PinError("Could not allocate a unique PIN; please try again", 503)