"""
Contract tests: real responses must match the response models the OpenAPI spec
declares, because the frontend client is generated from that spec.
"""

from pydantic import TypeAdapter

from app.extensions import db
from app.models import Setting
from app.tests.conftest import _make_user, login_as
from app.schemas import (
    APIResponse,
    CustomerSearchResponse,
    CustomerSingleResponse,
    DropdownConfigResponse,
    IdResponse,
    RepairAttachmentListResponse,
    RepairListResponse,
    RepairLogCreateResponse,
    RepairLogListResponse,
    RepairLogSingleResponse,
    RepairSingleResponse,
    SettingOption,
    UserListResponse,
    UserSingleResponse,
    VdeTestCreateResponse,
    VdeTestListResponse,
    VdeTestSingleResponse,
)


def _validate(model, response, status=200):
    assert response.status_code == status, response.get_data(as_text=True)
    return model.model_validate(response.get_json())


def _create_repair(client) -> dict:
    repair_type = Setting(category="repair_type", name="Elektro", is_active=True)
    device = Setting(
        category="pruefgeraet", name="Benning ST 755", serial_number="SN-1", is_active=True
    )
    db.session.add_all([repair_type, device])
    db.session.commit()
    resp = client.post(
        "/api/repairs",
        json={
            "datum": "2026-11-03",
            "vorname": "Erika",
            "nachname": "Mustermann",
            "geraet_art": "Toaster",
            "defekt_besch": "Heizt nicht",
            "repair_type_id": repair_type.id,
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["data"]


def test_repair_endpoints_match_spec(helper_client):
    repair = _create_repair(helper_client)
    repair_id = repair["id"]

    listing = _validate(RepairListResponse, helper_client.get("/api/list"))
    assert listing.count == len(listing.data) == 1

    single = _validate(
        RepairSingleResponse, helper_client.get(f"/api/repairs/by-token/{repair['qr_token']}")
    )
    assert single.data.id == repair_id


def test_repair_log_endpoints_match_spec(helper_client, helper_user):
    repair_id = _create_repair(helper_client)["id"]
    base = f"/api/repairs/{repair_id}/logs"

    created = _validate(
        RepairLogCreateResponse,
        helper_client.post(
            base,
            json={
                "repair_id": repair_id,
                "user_id": helper_user.id,
                "reparatur_dauer": 15,
                "reparatur_besch": "Sicherung getauscht",
            },
        ),
        status=201,
    )
    log_id = created.id
    assert created.data.id == log_id

    _validate(RepairLogListResponse, helper_client.get(base))
    _validate(RepairLogSingleResponse, helper_client.get(f"{base}/{log_id}"))
    _validate(
        RepairLogSingleResponse,
        helper_client.put(f"{base}/{log_id}", json={"reparatur_besch": "Kabel ersetzt"}),
    )
    _validate(APIResponse, helper_client.delete(f"{base}/{log_id}"))


def test_vde_test_endpoints_match_spec(helper_client, helper_user):
    repair_id = _create_repair(helper_client)["id"]
    base = f"/api/repairs/{repair_id}/vde-tests"

    created = _validate(
        VdeTestCreateResponse,
        helper_client.post(
            base,
            json={"repair_id": repair_id, "prufer_user_id": helper_user.id, "gesamtergebnis": True},
        ),
        status=201,
    )
    assert created.id is not None

    _validate(VdeTestListResponse, helper_client.get(base))
    _validate(VdeTestSingleResponse, helper_client.get(f"{base}/{created.id}"))


def test_lookup_endpoints_match_spec(helper_client):
    repair_id = _create_repair(helper_client)["id"]

    _validate(RepairAttachmentListResponse, helper_client.get(f"/api/repairs/{repair_id}/attachments"))
    dropdowns = _validate(DropdownConfigResponse, helper_client.get("/api/config/dropdowns"))
    assert [option.name for option in dropdowns.repair_type] == ["Elektro"]

    resp = helper_client.get("/api/settings")
    assert resp.status_code == 200
    grouped = TypeAdapter(dict[str, list[SettingOption]]).validate_python(resp.get_json())
    assert grouped["pruefgeraet"][0].serial_number == "SN-1"


def test_customer_endpoints_match_spec(client, app):
    _make_user("chefin", is_admin=True)
    login_as(client, "chefin")

    created = _validate(
        CustomerSingleResponse,
        client.post("/api/customers", json={"vorname": "Max", "nachname": "Muster"}),
        status=201,
    )
    customer_id = created.data.id

    _validate(CustomerSingleResponse, client.get(f"/api/customers/{customer_id}"))
    _validate(
        CustomerSingleResponse,
        client.put(f"/api/customers/{customer_id}", json={"vorname": "Max", "nachname": "Mustermann"}),
    )
    found = _validate(CustomerSearchResponse, client.get("/api/customers/search?q=Muster"))
    assert [c.id for c in found.data] == [customer_id]
    deleted = _validate(IdResponse, client.delete(f"/api/customers/{customer_id}"))
    assert deleted.id == customer_id


def test_user_endpoints_match_spec(client, app):
    _make_user("chefin", is_admin=True)
    login_as(client, "chefin")

    created = _validate(
        UserSingleResponse,
        client.post(
            "/api/users",
            json={
                "username": "neu",
                "vorname": "Neue",
                "nachname": "Helferin",
                "email": "neu@example.org",
                "password": "geheim123",
            },
        ),
        status=201,
    )
    user_id = created.data.id

    listing = _validate(UserListResponse, client.get("/api/users"))
    assert listing.count == len(listing.data)
    _validate(UserSingleResponse, client.get(f"/api/users/{user_id}"))
    _validate(UserSingleResponse, client.put(f"/api/users/{user_id}", json={"vorname": "Neu"}))
    _validate(APIResponse, client.delete(f"/api/users/{user_id}"))


def test_repair_delete_matches_spec(client, app):
    _make_user("chefin", is_admin=True)
    login_as(client, "chefin")
    repair_id = _create_repair(client)["id"]

    deleted = _validate(IdResponse, client.delete(f"/api/repairs/{repair_id}"))
    assert deleted.id == repair_id
