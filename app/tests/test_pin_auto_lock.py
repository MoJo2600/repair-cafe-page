"""
The idle auto-lock can be switched off per browser session (personal devices in the
workshop network); the workshop PC keeps it on by default.
"""

from datetime import timedelta

from app.extensions import db
from app.models import PinUnlockSession
from app.services.pin_unlock_service import utc_now

CLOUDFLARE = {"Cf-Ray": "8c1a2b3c4d5e6f70-FRA"}


def _grant(client) -> PinUnlockSession:
    with client.session_transaction() as browser_session:
        session_id = browser_session.get("pin_unlock_session_id")
    return PinUnlockSession.query.filter_by(session_id=session_id).one()


def _go_idle(client, seconds=61):
    grant = _grant(client)
    grant.last_activity_at = utc_now() - timedelta(seconds=seconds)
    db.session.commit()
    return grant


def test_status_reports_auto_lock_and_timeout(helper_client):
    status = helper_client.get("/api/auth/pin-session").get_json()

    assert status["auto_lock_enabled"] is True
    assert status["idle_timeout_seconds"] == 60


def test_disabled_auto_lock_never_locks_an_idle_session(helper_client):
    resp = helper_client.put("/api/auth/pin-session/auto-lock", json={"enabled": False})
    assert resp.status_code == 200

    _go_idle(helper_client, seconds=3600)

    assert helper_client.get("/api/list").status_code == 200
    status = helper_client.get("/api/auth/pin-session").get_json()
    assert status["locked"] is False
    assert status["auto_lock_enabled"] is False


def test_manual_lock_still_works_with_auto_lock_off(helper_client):
    helper_client.put("/api/auth/pin-session/auto-lock", json={"enabled": False})

    helper_client.post("/api/auth/pin-session/lock", json={})

    assert helper_client.get("/api/list").status_code == 423


def test_enabling_again_starts_a_fresh_idle_period(helper_client):
    helper_client.put("/api/auth/pin-session/auto-lock", json={"enabled": False})
    _go_idle(helper_client, seconds=3600)

    resp = helper_client.put("/api/auth/pin-session/auto-lock", json={"enabled": True})
    assert resp.status_code == 200

    # Not locked right away although the last activity was an hour ago
    assert helper_client.get("/api/list").status_code == 200
    _go_idle(helper_client)
    assert helper_client.get("/api/list").status_code == 423


def test_cannot_switch_off_an_already_expired_session(helper_client):
    _go_idle(helper_client)

    resp = helper_client.put("/api/auth/pin-session/auto-lock", json={"enabled": False})

    assert resp.status_code == 423
    assert _grant(helper_client).auto_lock_enabled is True


def test_new_login_starts_with_auto_lock_on(helper_client):
    helper_client.put("/api/auth/pin-session/auto-lock", json={"enabled": False})

    helper_client.post("/api/auth/logout")
    helper_client.post("/api/auth/login", json={"username": "helfer", "password": "secret"})

    assert helper_client.get("/api/auth/pin-session").get_json()["auto_lock_enabled"] is True


def test_invalid_body_is_rejected(helper_client):
    resp = helper_client.put("/api/auth/pin-session/auto-lock", json={"enabled": "nope"})

    assert resp.status_code == 400


def test_only_in_the_workshop_network(helper_client):
    resp = helper_client.put(
        "/api/auth/pin-session/auto-lock", json={"enabled": False}, headers=CLOUDFLARE
    )

    assert resp.status_code == 403
