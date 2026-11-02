"""
Failed password logins are limited per username and per client IP.
"""

import pytest


def _login(client, username, password, ip="198.51.100.1"):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
        environ_base={"REMOTE_ADDR": ip},
    )


@pytest.fixture
def limits(app):
    app.config.update(LOGIN_MAX_FAILED_PER_USER=3, LOGIN_MAX_FAILED_PER_IP=5)


def test_username_is_blocked_after_failures_even_with_right_password(client, helper_user, limits):
    for _ in range(3):
        assert _login(client, "helfer", "wrong").status_code == 401
    resp = _login(client, "helfer", "secret", ip="198.51.100.2")
    assert resp.status_code == 429
    assert int(resp.headers["Retry-After"]) > 0


def test_ip_is_blocked_across_usernames(client, helper_user, limits):
    for name in ("a", "b", "c", "d", "e"):
        assert _login(client, name, "wrong").status_code == 401
    assert _login(client, "helfer", "secret").status_code == 429
    assert _login(client, "helfer", "secret", ip="198.51.100.9").status_code == 200


def test_success_resets_username_failures(client, helper_user, limits):
    for _ in range(2):
        _login(client, "helfer", "wrong")
    assert _login(client, "helfer", "secret").status_code == 200
    for _ in range(2):
        assert _login(client, "helfer", "wrong").status_code == 401
    assert _login(client, "helfer", "secret").status_code == 200


def test_failures_expire_after_window(client, helper_user, limits, monkeypatch):
    import app.services.login_rate_limit as mod

    now = [1000.0]
    monkeypatch.setattr(mod.time, "monotonic", lambda: now[0])
    for _ in range(3):
        _login(client, "helfer", "wrong")
    assert _login(client, "helfer", "secret").status_code == 429
    now[0] += 15 * 60 + 1
    assert _login(client, "helfer", "secret").status_code == 200
