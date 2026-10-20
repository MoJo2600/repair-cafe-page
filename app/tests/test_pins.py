"""PIN ownership, self-service and deployment-mode safety."""

from importlib import import_module
from concurrent.futures import ThreadPoolExecutor
import os
from threading import Barrier

import pytest
import sqlalchemy as sa
from flask import Flask
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import PinState, User
from app.services.pin_service import PinError, generate_pin, hash_pin_code, reconcile_pin_mode


def test_database_rejects_duplicate_pins(app, helper_user):
    helper_user.pin_code_hash = hash_pin_code("123456")
    db.session.commit()
    db.session.add(User(username="other", email="other@example.org", password_hash="!",
                        pin_code_hash=hash_pin_code("123456")))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_local_generation_retries_collision(app, helper_user, monkeypatch):
    app.config.update(PIN_MODE="local", PIN_MODE_RESET_ACK="oidc-to-local")
    reconcile_pin_mode()
    admin = User.query.filter_by(username="admin").one()
    admin.pin_code_hash = hash_pin_code("123456")
    db.session.commit()
    values = iter([123456, 42])
    monkeypatch.setattr(
        "app.services.pin_service.secrets.randbelow", lambda maximum: next(values))
    assert generate_pin(helper_user.id) == "000042"
    assert helper_user.pin_code_hash == hash_pin_code("000042")


def test_mode_change_requires_ack_and_only_resets_once(app, helper_user):
    helper_user.pin_code_hash = hash_pin_code("123456")
    db.session.commit()
    app.config.update(PIN_MODE="local", PIN_MODE_RESET_ACK="")
    with pytest.raises(RuntimeError, match="deletes ALL"):
        reconcile_pin_mode()
    assert helper_user.pin_code_hash == hash_pin_code("123456")
    assert db.session.get(PinState, 1).mode == "oidc"
    app.config["PIN_MODE_RESET_ACK"] = "oidc-to-local"
    reconcile_pin_mode()
    db.session.refresh(helper_user)
    assert helper_user.pin_code_hash is None
    generate_pin(helper_user.id)
    digest = helper_user.pin_code_hash
    reconcile_pin_mode()
    assert helper_user.pin_code_hash == digest


@pytest.fixture
def local_pins(app):
    app.config.update(PIN_MODE="local", PIN_MODE_RESET_ACK="oidc-to-local")
    reconcile_pin_mode()


def test_profile_generation_is_explicit_and_one_time(helper_client, helper_user, local_pins):
    response = helper_client.get("/api/auth/me/pin")
    assert response.get_json() == {"mode": "local",
                                   "has_pin": False, "can_generate": True}
    assert helper_user.pin_code_hash is None
    response = helper_client.post("/api/auth/me/pin", json={})
    assert response.status_code == 200
    code = response.get_json()["pin_code"]
    assert helper_user.pin_code_hash == hash_pin_code(code)
    assert response.headers["Cache-Control"] == "no-store"
    status = helper_client.get("/api/auth/me/pin")
    assert status.get_json() == {"mode": "local",
                                 "has_pin": True, "can_generate": True}
    assert code not in status.get_data(as_text=True)
    assert "pin" not in helper_client.get(
        "/api/auth/me").get_data(as_text=True)
    assert helper_client.post("/api/auth/me/pin", json={}).status_code == 409
    replacement = helper_client.post(
        "/api/auth/me/pin", json={"replace": True})
    assert replacement.status_code == 200
    assert replacement.get_json()["pin_code"] != code


def test_provider_mode_disables_generation(helper_client):
    assert helper_client.get(
        "/api/auth/me/pin").get_json()["can_generate"] is False
    assert helper_client.post("/api/auth/me/pin", json={}).status_code == 403


def test_openapi_registers_pin_contracts(client):
    response = client.get("/apispec_1.json")
    assert response.status_code == 200
    spec = response.get_json()
    assert spec["definitions"]["PinStatusResponse"]["properties"]["mode"]["enum"] == [
        "local", "oidc"]
    operation = spec["paths"]["/api/auth/me/pin"]["post"]
    assert operation["responses"]["200"]["schema"]["$ref"] == "#/definitions/PinGeneratedResponse"


def test_anonymous_cannot_access_pins(client):
    assert client.get("/api/auth/me/pin").status_code == 401
    assert client.post("/api/auth/me/pin", json={}).status_code == 401


def test_pin_mutation_rejects_cross_site_and_invalid_requests(helper_client, local_pins):
    assert helper_client.post("/api/auth/me/pin", json={},
                              headers={"Origin": "https://evil.example"}).status_code == 403
    assert helper_client.post("/api/auth/me/pin", json={},
                              headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert helper_client.post("/api/auth/me/pin", data={}).status_code == 400
    assert helper_client.post(
        "/api/auth/me/pin", json={"replace": "false"}).status_code == 400
    assert helper_client.post(
        "/api/auth/me/pin", json={"user_id": 1}).status_code == 400
    for body in ([], None, "not-an-object"):
        assert helper_client.post(
            "/api/auth/me/pin", json=body).status_code == 400
    assert helper_client.post("/api/auth/me/pin", data="{",
                              content_type="application/json").status_code == 400


def test_disabled_user_cannot_manage_pin(helper_client, helper_user, local_pins):
    helper_user.is_active = False
    db.session.commit()
    assert helper_client.get("/api/auth/me/pin").status_code == 401
    assert helper_client.post("/api/auth/me/pin", json={}).status_code == 401


def test_failed_allocation_preserves_previous_pin(app, helper_user, local_pins, monkeypatch):
    helper_user.pin_code_hash = hash_pin_code("000042")
    db.session.commit()
    monkeypatch.setattr(
        "app.services.pin_service.secrets.randbelow", lambda maximum: 42)
    with pytest.raises(PinError, match="unique PIN"):
        generate_pin(helper_user.id, replace=True)
    db.session.rollback()
    assert helper_user.pin_code_hash == hash_pin_code("000042")


def test_runtime_mode_mismatch_blocks_pin_operations(app, helper_client):
    app.config["PIN_MODE"] = "local"
    assert helper_client.get("/api/auth/me/pin").status_code == 503
    assert helper_client.post("/api/auth/me/pin", json={}).status_code == 503


def test_reverse_mode_transition_requires_its_own_ack(app, helper_user, local_pins):
    generate_pin(helper_user.id)
    digest = helper_user.pin_code_hash
    app.config["PIN_MODE"] = "oidc"
    with pytest.raises(RuntimeError, match="local-to-oidc"):
        reconcile_pin_mode()
    assert helper_user.pin_code_hash == digest
    app.config["PIN_MODE_RESET_ACK"] = "local-to-oidc"
    reconcile_pin_mode()
    db.session.refresh(helper_user)
    assert helper_user.pin_code_hash is None


@pytest.mark.parametrize("mode", ["", "custom", "OIDC"])
def test_invalid_mode_fails_startup_check(app, mode):
    app.config["PIN_MODE"] = mode
    with pytest.raises(RuntimeError, match="PIN_MODE must"):
        reconcile_pin_mode()


def test_fresh_state_adopts_requested_mode(app):
    PinState.query.delete()
    db.session.commit()
    app.config.update(PIN_MODE="local", PIN_MODE_RESET_ACK="")
    reconcile_pin_mode()
    assert db.session.get(PinState, 1).mode == "local"


def test_untracked_legacy_pins_require_reset(app, helper_user):
    PinState.query.delete()
    helper_user.pin_code_hash = hash_pin_code("123456")
    db.session.commit()
    app.config.update(PIN_MODE="local", PIN_MODE_RESET_ACK="")
    with pytest.raises(RuntimeError, match="deletes ALL"):
        reconcile_pin_mode()
    assert helper_user.pin_code_hash == hash_pin_code("123456")


@pytest.mark.parametrize("database", ["sqlite", "mariadb"])
@pytest.mark.parametrize("duplicate", [False, True])
def test_pin_migration_preserves_hashes_and_round_trips(monkeypatch, duplicate, database):
    url = "sqlite://" if database == "sqlite" else _integration_url()
    engine = sa.create_engine(url)
    migration = import_module("app.migrations.versions.012_generic_pin_codes")
    with engine.begin() as connection:
        connection.execute(sa.text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, door_code_hash VARCHAR(64))"))
        connection.execute(
            sa.text("CREATE INDEX ix_users_door_code_hash ON users (door_code_hash)"))
        connection.execute(
            sa.text("INSERT INTO users VALUES (1, 'legacy-hash')"))
        if duplicate:
            connection.execute(
                sa.text("INSERT INTO users VALUES (2, 'legacy-hash')"))
        monkeypatch.setattr(migration, "op", Operations(
            MigrationContext.configure(connection)))
        if duplicate:
            with pytest.raises(RuntimeError, match="Duplicate legacy"):
                migration.upgrade()
            connection.execute(sa.text("DROP TABLE users"))
            return
        migration.upgrade()
        assert connection.execute(
            sa.text("SELECT pin_code_hash FROM users")).scalar() == "legacy-hash"
        assert connection.execute(
            sa.text("SELECT mode FROM pin_state")).scalar() == "oidc"
        assert sa.inspect(connection).get_unique_constraints(
            "users")[0]["column_names"] == ["pin_code_hash"]
        migration.downgrade()
        assert connection.execute(
            sa.text("SELECT door_code_hash FROM users")).scalar() == "legacy-hash"
        migration.upgrade()
        assert connection.execute(
            sa.text("SELECT pin_code_hash FROM users")).scalar() == "legacy-hash"
        connection.execute(sa.text("DROP TABLE pin_state"))
        connection.execute(sa.text("DROP TABLE users"))
    engine.dispose()


def _integration_url():
    url = os.environ.get("PIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "Set PIN_TEST_DATABASE_URL to a disposable MariaDB pin_tests database")
    if sa.engine.make_url(url).database != "pin_tests":
        raise ValueError(
            "Integration tests require a disposable database named pin_tests")
    return url


@pytest.fixture
def production_pin_app():
    integration = Flask("pin-integration")
    integration.config.update(
        SQLALCHEMY_DATABASE_URI=_integration_url(),
        SECRET_KEY="pin-integration-only",
        PIN_MODE="local", PIN_MODE_RESET_ACK="",
        OIDC_SCOPES="openid email profile",
    )
    db.init_app(integration)
    with integration.app_context():
        tables = [User.__table__, PinState.__table__]
        db.metadata.create_all(db.engine, tables=tables)
        reconcile_pin_mode()
        db.session.add(User(username="concurrent",
                       email="concurrent@example.org", password_hash="!"))
        db.session.commit()
    try:
        yield integration
    finally:
        with integration.app_context():
            db.session.remove()
            db.metadata.drop_all(db.engine, tables=tables)
            db.engine.dispose()


def test_concurrent_generation_does_not_replace_pin(production_pin_app):
    barrier = Barrier(2)

    def generate():
        with production_pin_app.app_context():
            user_id = User.query.filter_by(username="concurrent").one().id
            barrier.wait(timeout=10)
            try:
                return generate_pin(user_id)
            except PinError as error:
                db.session.rollback()
                return error.status

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: generate(), range(2)))
    codes = [result for result in results if isinstance(result, str)]
    assert len(codes) == 1
    assert 409 in results
    with production_pin_app.app_context():
        assert User.query.filter_by(username="concurrent").one(
        ).pin_code_hash == hash_pin_code(codes[0])


def test_concurrent_mode_reconciliation_is_atomic(production_pin_app):
    with production_pin_app.app_context():
        user = User.query.filter_by(username="concurrent").one()
        user.pin_code_hash = hash_pin_code("123456")
        db.session.commit()
    production_pin_app.config.update(
        PIN_MODE="oidc", PIN_MODE_RESET_ACK="local-to-oidc")
    barrier = Barrier(2)

    def reconcile():
        with production_pin_app.app_context():
            barrier.wait(timeout=10)
            reconcile_pin_mode()

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _: reconcile(), range(2)))
    with production_pin_app.app_context():
        assert db.session.get(PinState, 1).mode == "oidc"
        user = User.query.filter_by(username="concurrent").one()
        assert user.pin_code_hash is None
        user.pin_code_hash = hash_pin_code("654321")
        db.session.commit()
        reconcile_pin_mode()
        assert user.pin_code_hash == hash_pin_code("654321")
