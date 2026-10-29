"""PIN ownership, self-service and deployment-mode safety."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from importlib import import_module
from threading import Barrier

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from flask import Flask
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Customer, PinState, PinUnlockSession, Repair, Setting, User
from app.services.pin_service import (
    PinError,
    generate_pin,
    hash_pin_code,
    reconcile_pin_mode,
)
from app.services.pin_unlock_service import utc_now


def test_database_rejects_duplicate_pins(app, helper_user):
    helper_user.pin_code_hash = hash_pin_code("123456")
    db.session.commit()
    db.session.add(
        User(
            username="other",
            email="other@example.org",
            password_hash="!",
            pin_code_hash=hash_pin_code("123456"),
        )
    )
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
        "app.services.pin_service.secrets.randbelow", lambda maximum: next(values)
    )
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


def test_profile_generation_is_explicit_and_one_time(
    helper_client, helper_user, local_pins
):
    response = helper_client.get("/api/auth/me/pin")
    assert response.get_json() == {
        "mode": "local",
        "has_pin": False,
        "can_generate": True,
    }
    assert helper_user.pin_code_hash is None
    response = helper_client.post("/api/auth/me/pin", json={})
    assert response.status_code == 200
    code = response.get_json()["pin_code"]
    assert helper_user.pin_code_hash == hash_pin_code(code)
    assert response.headers["Cache-Control"] == "no-store"
    status = helper_client.get("/api/auth/me/pin")
    assert status.get_json() == {"mode": "local", "has_pin": True, "can_generate": True}
    assert code not in status.get_data(as_text=True)
    assert "pin" not in helper_client.get("/api/auth/me").get_data(as_text=True)
    assert helper_client.post("/api/auth/me/pin", json={}).status_code == 409
    replacement = helper_client.post("/api/auth/me/pin", json={"replace": True})
    assert replacement.status_code == 200
    assert replacement.get_json()["pin_code"] != code


def test_provider_mode_disables_generation(helper_client):
    assert helper_client.get("/api/auth/me/pin").get_json()["can_generate"] is False
    assert helper_client.post("/api/auth/me/pin", json={}).status_code == 403


def test_primary_password_login_arms_browser_pin_session(client, helper_user):
    response = client.post(
        "/api/auth/login", json={"username": "helfer", "password": "secret"}
    )
    assert response.status_code == 200
    with client.session_transaction() as browser_session:
        session_id = browser_session.get("pin_unlock_session_id")
    assert session_id
    grant = PinUnlockSession.query.filter_by(session_id=session_id).one()
    assert grant.active_user_id == helper_user.id
    assert grant.is_locked is False


def test_locked_session_blocks_repairs_and_pin_switches_helper(
    app, helper_client, helper_user, local_pins
):
    from werkzeug.security import generate_password_hash

    second_user = User(
        username="second-helper",
        vorname="Second",
        nachname="Helper",
        email="second@example.org",
        password_hash=generate_password_hash("secret"),
        pin_code_hash=hash_pin_code("123456"),
    )
    db.session.add(second_user)
    db.session.commit()

    locked = helper_client.post("/api/auth/pin-session/lock", json={})
    assert locked.status_code == 200
    assert locked.get_json() == {"locked": True}
    assert helper_client.get("/api/list").status_code == 423
    assert helper_client.get("/api/auth/pin-session").get_json()["locked"] is True

    unlocked = helper_client.post(
        "/api/auth/pin-session/unlock", json={"pin_code": "123456"}
    )
    assert unlocked.status_code == 200
    assert unlocked.get_json()["data"]["username"] == "second-helper"
    assert helper_client.get("/api/list").status_code == 200

    with helper_client.session_transaction() as browser_session:
        session_id = browser_session["pin_unlock_session_id"]
    grant = PinUnlockSession.query.filter_by(session_id=session_id).one()
    assert grant.active_user_id == second_user.id


def test_pin_grant_is_isolated_to_the_primary_login_browser(app, helper_user):
    first_browser = app.test_client()
    second_browser = app.test_client()
    response = first_browser.post(
        "/api/auth/login", json={"username": "helfer", "password": "secret"}
    )
    assert response.status_code == 200
    assert first_browser.get("/api/auth/pin-session").status_code == 200
    assert second_browser.get("/api/auth/pin-session").status_code == 401
    assert (
        second_browser.post(
            "/api/auth/pin-session/unlock", json={"pin_code": "123456"}
        ).status_code
        == 401
    )


def test_locked_pin_session_expires_after_sixty_seconds(helper_client, helper_user):
    helper_client.post("/api/auth/pin-session/lock", json={})
    with helper_client.session_transaction() as browser_session:
        session_id = browser_session["pin_unlock_session_id"]
    grant = PinUnlockSession.query.filter_by(session_id=session_id).one()
    grant.is_locked = False
    grant.last_activity_at = utc_now() - timedelta(seconds=61)
    db.session.commit()

    response = helper_client.get("/api/list")
    assert response.status_code == 423
    db.session.refresh(grant)
    assert grant.is_locked is True


def test_pin_unlock_attempts_enter_server_side_cooldown(
    helper_client, helper_user, local_pins
):
    helper_user.pin_code_hash = hash_pin_code("123456")
    db.session.commit()
    helper_client.post("/api/auth/pin-session/lock", json={})

    responses = [
        helper_client.post("/api/auth/pin-session/unlock", json={"pin_code": "000000"})
        for _ in range(5)
    ]
    assert all(response.status_code == 401 for response in responses)
    assert (
        helper_client.post(
            "/api/auth/pin-session/unlock", json={"pin_code": "000000"}
        ).status_code
        == 429
    )
    with helper_client.session_transaction() as browser_session:
        session_id = browser_session["pin_unlock_session_id"]
    grant = PinUnlockSession.query.filter_by(session_id=session_id).one()
    assert grant.cooldown_level == 1
    assert grant.locked_until is not None


def test_pin_unlock_fails_closed_on_runtime_mode_mismatch(
    app, helper_client, helper_user, local_pins
):
    generate_pin(helper_user.id)
    helper_client.post("/api/auth/pin-session/lock", json={})
    app.config["PIN_MODE"] = "oidc"
    response = helper_client.post(
        "/api/auth/pin-session/unlock", json={"pin_code": "123456"}
    )
    assert response.status_code == 503


def test_full_logout_revokes_pin_session(helper_client):
    with helper_client.session_transaction() as browser_session:
        session_id = browser_session["pin_unlock_session_id"]
    response = helper_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert PinUnlockSession.query.filter_by(session_id=session_id).first() is None
    assert helper_client.get("/api/auth/pin-session").status_code == 401


def test_locked_logout_rejects_cross_site_request(helper_client):
    helper_client.post("/api/auth/pin-session/lock", json={})
    response = helper_client.post(
        "/api/auth/logout",
        headers={"Origin": "https://attacker.example"},
    )
    assert response.status_code == 403
    assert helper_client.get("/api/auth/pin-session").get_json()["locked"] is True


def test_pin_unlock_session_migration_round_trips():
    engine = sa.create_engine("sqlite://")
    migration = import_module("app.migrations.versions.013_pin_unlock_sessions")
    with engine.begin() as connection:
        connection.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(
            migration, "op", Operations(MigrationContext.configure(connection))
        )
        try:
            migration.upgrade()
            assert "pin_unlock_sessions" in sa.inspect(connection).get_table_names()
            migration.downgrade()
            assert "pin_unlock_sessions" not in sa.inspect(connection).get_table_names()
        finally:
            monkeypatch.undo()
    engine.dispose()


def test_locked_dashboard_summary_excludes_private_repair_data(
    app, helper_client, helper_user
):
    from datetime import date

    elektro = Setting(category="repair_type", name="Elektro", sort_order=1)
    textil = Setting(category="repair_type", name="Textil", sort_order=2)
    db.session.add_all([elektro, textil])
    customer = Customer(vorname="Private", nachname="Customer")
    db.session.add(customer)
    db.session.flush()
    next_repair = Repair(
        customer_id=customer.id,
        repair_type_id=elektro.id,
        datum=date.today(),
        geraet_art="Private Device",
        status="Offen",
        qr_token="a" * 32,
    )
    active_repair = Repair(
        customer_id=customer.id,
        repair_type_id=textil.id,
        datum=date.today(),
        geraet_art="Another Private Device",
        status="In Bearbeitung",
        user_id=helper_user.id,
        qr_token="b" * 32,
    )
    db.session.add_all([next_repair, active_repair])
    db.session.commit()

    # Dashboard summary works while unlocked (menu access)
    unlocked_response = helper_client.get("/api/auth/pin-session/dashboard")
    assert unlocked_response.status_code == 200

    # And works while locked (wall projection)
    assert helper_client.post("/api/auth/pin-session/lock", json={}).status_code == 200

    response = helper_client.get("/api/auth/pin-session/dashboard")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_repairs"] == 2
    assert payload["open_repairs"] == 1
    assert payload["next_repair_id"] == next_repair.id
    assert payload["next_repair_category"] == "Elektro"
    assert payload["in_progress_repairs"] == 1
    assert payload["in_progress_items"] == [
        {"id": active_repair.id, "category": "Textil"}
    ]
    assert payload["top_categories"] == [
        {"name": "Elektro", "count": 1},
        {"name": "Textil", "count": 1},
    ]
    serialized = response.get_data(as_text=True)
    assert "Private" not in serialized
    assert "Device" not in serialized
    assert "customer" not in serialized
    assert helper_user.username not in serialized
    assert helper_client.get("/api/list").status_code == 423


def test_openapi_registers_pin_contracts(client):
    response = client.get("/apispec_1.json")
    assert response.status_code == 200
    spec = response.get_json()
    assert spec["definitions"]["PinStatusResponse"]["properties"]["mode"]["enum"] == [
        "local",
        "oidc",
    ]
    operation = spec["paths"]["/api/auth/me/pin"]["post"]
    assert (
        operation["responses"]["200"]["schema"]["$ref"]
        == "#/definitions/PinGeneratedResponse"
    )
    dashboard_schema = spec["definitions"]["PinDashboardSummaryResponse"]
    assert "next_repair_id" in dashboard_schema["properties"]
    assert "next_repair_category" in dashboard_schema["properties"]
    assert "in_progress_items" in dashboard_schema["properties"]
    assert "top_categories" in dashboard_schema["properties"]
    assert "PinDashboardRepairItem" in spec["definitions"]
    assert "PinDashboardCategoryCount" in spec["definitions"]
    dashboard_operation = spec["paths"]["/api/auth/pin-session/dashboard"]["get"]
    assert (
        dashboard_operation["responses"]["200"]["schema"]["$ref"]
        == "#/definitions/PinDashboardSummaryResponse"
    )


def test_pin_mutation_rejects_cross_site_and_invalid_requests(
    helper_client, local_pins
):
    assert (
        helper_client.post(
            "/api/auth/me/pin", json={}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        helper_client.post(
            "/api/auth/me/pin", json={}, headers={"Sec-Fetch-Site": "cross-site"}
        ).status_code
        == 403
    )
    assert helper_client.post("/api/auth/me/pin", data={}).status_code == 400
    assert (
        helper_client.post("/api/auth/me/pin", json={"replace": "false"}).status_code
        == 400
    )
    assert (
        helper_client.post("/api/auth/me/pin", json={"user_id": 1}).status_code == 400
    )
    for body in ([], None, "not-an-object"):
        assert helper_client.post("/api/auth/me/pin", json=body).status_code == 400
    assert (
        helper_client.post(
            "/api/auth/me/pin", data="{", content_type="application/json"
        ).status_code
        == 400
    )


def test_pin_mutation_accepts_vite_localhost_origin(helper_client, local_pins, app):
    app.config["DEBUG"] = True
    response = helper_client.post(
        "/api/auth/me/pin",
        json={},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200


def test_disabled_user_cannot_manage_pin(helper_client, helper_user, local_pins):
    helper_user.is_active = False
    db.session.commit()
    assert helper_client.get("/api/auth/me/pin").status_code == 401
    assert helper_client.post("/api/auth/me/pin", json={}).status_code == 401


def test_failed_allocation_preserves_previous_pin(
    app, helper_user, local_pins, monkeypatch
):
    helper_user.pin_code_hash = hash_pin_code("000042")
    db.session.commit()
    monkeypatch.setattr(
        "app.services.pin_service.secrets.randbelow", lambda maximum: 42
    )
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
def test_pin_migration_creates_generic_schema_and_round_trips(monkeypatch, database):
    url = "sqlite://" if database == "sqlite" else _integration_url()
    engine = sa.create_engine(url)
    migration = import_module("app.migrations.versions.011_user_oidc")
    with engine.begin() as connection:
        connection.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        monkeypatch.setattr(
            migration, "op", Operations(MigrationContext.configure(connection))
        )
        migration.upgrade()
        columns = {
            column["name"] for column in sa.inspect(connection).get_columns("users")
        }
        assert {"oidc_sub", "pin_code_hash"} <= columns
        constraints = {
            constraint["name"]: constraint["column_names"]
            for constraint in sa.inspect(connection).get_unique_constraints("users")
        }
        assert constraints["uq_users_oidc_sub"] == ["oidc_sub"]
        assert constraints["uq_users_pin_code_hash"] == ["pin_code_hash"]
        assert {
            column["name"] for column in sa.inspect(connection).get_columns("pin_state")
        } == {"id", "mode"}
        assert (
            connection.execute(sa.text("SELECT COUNT(*) FROM pin_state")).scalar() == 0
        )
        migration.downgrade()
        assert {
            column["name"] for column in sa.inspect(connection).get_columns("users")
        } == {"id"}
        migration.upgrade()
        connection.execute(sa.text("DROP TABLE pin_state"))
        connection.execute(sa.text("DROP TABLE users"))
    engine.dispose()


def _integration_url():
    url = os.environ.get("PIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "Set PIN_TEST_DATABASE_URL to a disposable MariaDB pin_tests database"
        )
    if sa.engine.make_url(url).database != "pin_tests":
        raise ValueError(
            "Integration tests require a disposable database named pin_tests"
        )
    return url


@pytest.fixture
def production_pin_app():
    integration = Flask("pin-integration")
    integration.config.update(
        SQLALCHEMY_DATABASE_URI=_integration_url(),
        SECRET_KEY="pin-integration-only",
        PIN_MODE="local",
        PIN_MODE_RESET_ACK="",
        OIDC_SCOPES="openid email profile",
    )
    db.init_app(integration)
    with integration.app_context():
        tables = [User.__table__, PinState.__table__]
        db.metadata.create_all(db.engine, tables=tables)
        reconcile_pin_mode()
        db.session.add(
            User(
                username="concurrent", email="concurrent@example.org", password_hash="!"
            )
        )
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
        assert User.query.filter_by(
            username="concurrent"
        ).one().pin_code_hash == hash_pin_code(codes[0])


def test_concurrent_mode_reconciliation_is_atomic(production_pin_app):
    with production_pin_app.app_context():
        user = User.query.filter_by(username="concurrent").one()
        user.pin_code_hash = hash_pin_code("123456")
        db.session.commit()
    production_pin_app.config.update(
        PIN_MODE="oidc", PIN_MODE_RESET_ACK="local-to-oidc"
    )
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
