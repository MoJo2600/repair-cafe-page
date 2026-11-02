"""Break-glass admin password reset command."""

import pytest
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import User
from app.reset_admin_password import ResetError, reset_admin_password, run
from app.tests.conftest import _make_user

NEW_PASSWORD = "correct-horse-battery"


def test_resets_local_admin_and_reactivates(app):
    admin = User.query.filter_by(username="admin").one()
    admin.is_active = False
    db.session.commit()

    assert reset_admin_password("admin", NEW_PASSWORD) is False

    db.session.refresh(admin)
    assert check_password_hash(admin.password_hash, NEW_PASSWORD)
    assert admin.is_active


def test_recreates_missing_admin(app):
    assert reset_admin_password("notfall", NEW_PASSWORD) is True

    user = User.query.filter_by(username="notfall").one()
    assert user.is_admin and user.is_active and user.oidc_sub is None
    assert check_password_hash(user.password_hash, NEW_PASSWORD)


def test_refuses_sso_and_non_admin_accounts(app):
    sso = _make_user("sso", is_admin=True)
    sso.oidc_sub = "sub-1"
    _make_user("helper")
    db.session.commit()

    with pytest.raises(ResetError, match="SSO"):
        reset_admin_password("sso", NEW_PASSWORD)
    with pytest.raises(ResetError, match="not an admin"):
        reset_admin_password("helper", NEW_PASSWORD)
    assert not check_password_hash(sso.password_hash, NEW_PASSWORD)


def test_refuses_short_password(app):
    with pytest.raises(ResetError, match="at least"):
        reset_admin_password("admin", "short")


def test_generate_prints_working_password(app, capsys):
    assert run(["--generate"]) == 0

    password = capsys.readouterr().out.split("New password: ")[1].split()[0]
    admin = User.query.filter_by(username="admin").one()
    assert check_password_hash(admin.password_hash, password)


def test_prompt_requires_terminal(app, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    assert run([]) == 1
    assert "--generate" in capsys.readouterr().err


def test_prompt_sets_password(app, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda prompt="": NEW_PASSWORD)

    assert run([]) == 0
    admin = User.query.filter_by(username="admin").one()
    assert check_password_hash(admin.password_hash, NEW_PASSWORD)


def test_reset_env_var_is_ignored(monkeypatch, tmp_path):
    from app import create_app

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("RESET_ADMIN_PASSWORD", "1")
    app = create_app("development")
    with app.app_context():
        admin = User.query.filter_by(username="admin").one()
        before = admin.password_hash
        from app import ensure_admin_user

        ensure_admin_user(app)
        assert User.query.filter_by(username="admin").one().password_hash == before
        db.session.remove()
        db.drop_all()
