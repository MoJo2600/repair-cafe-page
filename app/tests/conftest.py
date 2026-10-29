"""
Shared pytest fixtures: a Flask app on an in-memory SQLite database.

Run from the project root:
    python -m pytest app/tests -v
"""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret")
os.environ["CREATE_TABLES_ON_STARTUP"] = "1"
for key in ("OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "PUBLIC_URL"):
    os.environ[key] = ""
os.environ["PIN_MODE"] = "oidc"
os.environ["PIN_MODE_RESET_ACK"] = ""
os.environ["OIDC_SCOPES"] = "openid email profile"
os.environ["OIDC_PIN_CLAIM"] = "pin_code"
os.environ["OIDC_ADMIN_CLAIM"] = "repaircafe_admin"
os.environ["OIDC_GROUPS_CLAIM"] = "groups"
os.environ["OIDC_DENIED_GROUPS"] = ""

from werkzeug.security import generate_password_hash  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    app = create_app("development")
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _make_user(username, is_admin=False, password="secret"):
    user = User(
        username=username,
        vorname=username.title(),
        nachname="Test",
        email=f"{username}@example.org",
        password_hash=generate_password_hash(password),
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def helper_user(app):
    return _make_user("helfer")


@pytest.fixture
def helper_client(client, helper_user):
    resp = client.post("/api/auth/login",
                       json={"username": "helfer", "password": "secret"})
    assert resp.status_code == 200
    return client
