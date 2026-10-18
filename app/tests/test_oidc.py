"""
OIDC login flow with a stubbed Authentik client (no network).
"""

import pytest
from werkzeug.security import generate_password_hash

from app.auth.oidc import hash_door_code
from app.extensions import db
from app.models import User


class FakeAuthentik:
    """Stands in for the Authlib client registered by init_oidc."""

    def __init__(self):
        self.claims = {}
        self.fail = False
        self.last_authorize_kwargs = None

    def authorize_redirect(self, redirect_uri, **kwargs):
        from flask import redirect

        self.last_authorize_kwargs = {"redirect_uri": redirect_uri, **kwargs}
        return redirect("https://auth.example/authorize")

    def authorize_access_token(self):
        if self.fail:
            raise RuntimeError("state mismatch")
        return {"userinfo": dict(self.claims)}


@pytest.fixture
def sso(app):
    app.config.update(
        OIDC_ISSUER="https://auth.example/application/o/repaircafe-page/",
        OIDC_CLIENT_ID="repaircafe-page",
        OIDC_CLIENT_SECRET="secret",
        PUBLIC_URL="https://reparaturen.example",
        OIDC_DENIED_GROUPS=["Kind"],
    )
    fake = FakeAuthentik()
    app.extensions["oidc_client"] = fake
    return fake


def _claims(**overrides):
    claims = {
        "sub": "hashed-sub-1",
        "email": "Anna@Example.org",
        "name": "Anna Beispiel",
        "preferred_username": "anna",
        "groups": ["Ordentliches Mitglied"],
        "repaircafe_admin": False,
        "door_code": "123456",
    }
    claims.update(overrides)
    return claims


def _sso_login(client, sso, **overrides):
    sso.claims = _claims(**overrides)
    return client.get("/api/auth/oidc/callback")


def test_auth_config_reports_sso(client, sso):
    assert client.get("/api/auth/config").get_json() == {"oidc_enabled": True}


def test_auth_config_without_sso(client):
    assert client.get("/api/auth/config").get_json() == {"oidc_enabled": False}


def test_login_redirects_with_prompt_login(client, sso):
    resp = client.get("/api/auth/oidc/login?next=/repairs")
    assert resp.status_code == 302
    assert sso.last_authorize_kwargs == {
        "redirect_uri": "https://reparaturen.example/api/auth/oidc/callback",
        "prompt": "login",
    }


def test_callback_creates_user_and_logs_in(client, sso):
    client.get("/api/auth/oidc/login?next=/repairs")
    resp = _sso_login(client, sso)

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/repairs"
    user = User.query.filter_by(oidc_sub="hashed-sub-1").one()
    assert (user.username, user.email, user.vorname, user.nachname) == (
        "anna", "anna@example.org", "Anna", "Beispiel",
    )
    assert user.is_admin is False
    assert user.door_code_hash == hash_door_code("123456")
    assert "123456" not in (user.door_code_hash or "")
    assert client.get("/api/auth/me").status_code == 200


@pytest.mark.parametrize("next_param", ["//evil.example", "https://evil.example", "/\\evil"])
def test_open_redirect_is_blocked(client, sso, next_param):
    client.get("/api/auth/oidc/login", query_string={"next": next_param})
    assert _sso_login(client, sso).headers["Location"] == "/"


def test_admin_role_follows_claim(client, sso):
    _sso_login(client, sso, repaircafe_admin=True)
    assert User.query.filter_by(oidc_sub="hashed-sub-1").one().is_admin is True
    _sso_login(client, sso, repaircafe_admin=False)
    assert User.query.filter_by(oidc_sub="hashed-sub-1").one().is_admin is False


def test_denied_group_is_refused(client, sso):
    resp = _sso_login(client, sso, groups=["Kind"])
    assert resp.headers["Location"] == "/login?error=forbidden"
    assert User.query.filter_by(oidc_sub="hashed-sub-1").first() is None
    assert client.get("/api/auth/me").status_code == 401


def test_failed_token_exchange(client, sso):
    sso.fail = True
    assert client.get("/api/auth/oidc/callback").headers["Location"] == "/login?error=sso_failed"


def test_existing_local_repairer_is_adopted_by_email(client, sso):
    db.session.add(User(username="anna_alt", email="anna@example.org", password_hash="x"))
    db.session.commit()
    _sso_login(client, sso)
    anna = User.query.filter_by(email="anna@example.org").all()
    assert [(u.username, u.oidc_sub) for u in anna] == [("anna_alt", "hashed-sub-1")]


def test_local_admin_is_never_adopted(client, sso):
    # create_app already ensured a local "admin"; give it the member's e-mail
    admin = User.query.filter_by(username="admin").one()
    admin.email = "anna@example.org"
    db.session.commit()

    resp = _sso_login(client, sso)
    assert resp.headers["Location"] == "/login?error=account_conflict"
    assert admin.oidc_sub is None


def test_invalid_door_code_is_not_stored(client, sso):
    _sso_login(client, sso, door_code="12ab")
    assert User.query.filter_by(oidc_sub="hashed-sub-1").one().door_code_hash is None


def test_reassigned_door_code_moves_to_new_holder(client, sso):
    _sso_login(client, sso)
    client.post("/api/auth/logout")
    _sso_login(client, sso, sub="hashed-sub-2", email="bernd@example.org", preferred_username="bernd")

    holders = User.query.filter(User.door_code_hash == hash_door_code("123456")).all()
    assert [u.oidc_sub for u in holders] == ["hashed-sub-2"]


def _local_user(username, is_admin, oidc_sub=None):
    db.session.add(
        User(
            username=username,
            email=f"{username}@example.org",
            password_hash=generate_password_hash("secret"),
            is_admin=is_admin,
            oidc_sub=oidc_sub,
        )
    )
    db.session.commit()


def test_password_login_only_for_local_admins_when_sso_enabled(client, sso):
    _local_user("chef", is_admin=True)
    _local_user("helfer", is_admin=False)
    _local_user("sso_admin", is_admin=True, oidc_sub="sub-x")

    login = lambda u: client.post("/api/auth/login", json={"username": u, "password": "secret"})
    assert login("chef").status_code == 200
    client.post("/api/auth/logout")
    assert login("helfer").status_code == 403
    assert login("sso_admin").status_code == 403


def test_password_login_unrestricted_without_sso(client):
    _local_user("helfer", is_admin=False)
    resp = client.post("/api/auth/login", json={"username": "helfer", "password": "secret"})
    assert resp.status_code == 200
