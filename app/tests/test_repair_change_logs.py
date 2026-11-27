"""
Status and assignee changes are logged by the backend in the same transaction as the
update (the frontend used to write these entries itself with a second request).
"""

from app.extensions import db
from app.models import AppConfig, RepairLog, Setting
from app.tests.conftest import _make_user


def _create_repair(client) -> int:
    repair_type = Setting(category="repair_type", name="Elektro", is_active=True)
    db.session.add(repair_type)
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
    return resp.get_json()["id"]


def _logs(repair_id: int) -> list[RepairLog]:
    return RepairLog.query.filter_by(repair_id=repair_id).order_by(RepairLog.id).all()


def _enable_handover() -> None:
    db.session.add(AppConfig(key="repair_handover_enabled", value="true"))
    db.session.commit()


def test_status_change_is_logged_for_the_repairer(helper_client, helper_user):
    repairer = _make_user("reparateur")
    repair_id = _create_repair(helper_client)

    resp = helper_client.put(
        f"/api/repairs/{repair_id}", json={"status": "In Bearbeitung", "user_id": repairer.id}
    )
    assert resp.status_code == 200

    [log] = _logs(repair_id)
    assert log.log_type == "status_change"
    assert (log.status_from, log.status_to) == ("Offen", "In Bearbeitung")
    assert log.user_id == repairer.id
    assert log.reparatur_besch == ""


def test_closing_logs_the_repair_description(helper_client, helper_user):
    repair_id = _create_repair(helper_client)
    helper_client.put(
        f"/api/repairs/{repair_id}", json={"status": "In Bearbeitung", "user_id": helper_user.id}
    )

    resp = helper_client.put(
        f"/api/repairs/{repair_id}",
        json={"status": "Repariert", "reparatur_besch": "Thermostat getauscht", "reparatur_dauer": 30},
    )
    assert resp.status_code == 200

    closing = _logs(repair_id)[-1]
    assert (closing.status_from, closing.status_to) == ("In Bearbeitung", "Repariert")
    assert closing.reparatur_besch == "Thermostat getauscht"


def test_reopening_is_logged_once_and_keeps_previous_repairer(helper_client, helper_user):
    repair_id = _create_repair(helper_client)
    helper_client.put(
        f"/api/repairs/{repair_id}", json={"status": "In Bearbeitung", "user_id": helper_user.id}
    )

    helper_client.put(f"/api/repairs/{repair_id}", json={"status": "Offen"})

    logs = _logs(repair_id)
    assert [log.log_type for log in logs] == ["status_change", "status_change"]
    assert logs[-1].user_id == helper_user.id


def test_assignee_change_is_logged_for_the_acting_user(helper_client, helper_user):
    other = _make_user("kollegin")
    repair_id = _create_repair(helper_client)

    helper_client.put(f"/api/repairs/{repair_id}", json={"user_id": other.id})
    helper_client.put(f"/api/repairs/{repair_id}", json={"user_id": None})

    assigned, removed = _logs(repair_id)
    assert assigned.log_type == removed.log_type == "assignee_change"
    assert assigned.user_id == helper_user.id
    assert assigned.reparatur_besch == "Zugewiesen an: Kollegin Test"
    assert removed.reparatur_besch == "Zuweisung entfernt"


def test_update_without_status_or_assignee_change_writes_no_log(helper_client):
    repair_id = _create_repair(helper_client)

    helper_client.put(f"/api/repairs/{repair_id}", json={"geraet_art": "Wasserkocher"})

    assert _logs(repair_id) == []


def test_rejected_transition_writes_no_log(helper_client):
    repair_id = _create_repair(helper_client)

    # Offen -> In Bearbeitung needs a repairer
    resp = helper_client.put(f"/api/repairs/{repair_id}", json={"status": "In Bearbeitung"})
    assert resp.status_code == 422

    assert _logs(repair_id) == []


def _close_repair(client, repair_id: int, user_id: int) -> None:
    assert (
        client.put(
            f"/api/repairs/{repair_id}",
            json={"status": "In Bearbeitung", "user_id": user_id},
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/repairs/{repair_id}",
            json={
                "status": "Repariert",
                "reparatur_besch": "Gerät instand gesetzt",
            },
        ).status_code
        == 200
    )


def test_completed_repair_handover_can_be_recorded_and_reset(helper_client, helper_user):
    _enable_handover()
    repair_id = _create_repair(helper_client)
    _close_repair(helper_client, repair_id, helper_user.id)

    from app.models import Repair

    repair = db.session.get(Repair, repair_id)
    assert repair.handed_over_at is None

    response = helper_client.post(f"/api/repairs/{repair_id}/handover")
    assert response.status_code == 200
    assert response.get_json()["data"]["handed_over_at"] is not None
    assert response.get_json()["data"]["handed_over_by_id"] == helper_user.id

    # Recording an already recorded handover is idempotent and does not add a log.
    assert helper_client.post(f"/api/repairs/{repair_id}/handover").status_code == 200
    assert [log.log_type for log in _logs(repair_id)].count("handover_change") == 1

    response = helper_client.delete(f"/api/repairs/{repair_id}/handover")
    assert response.status_code == 200
    assert response.get_json()["data"]["handed_over_at"] is None
    assert response.get_json()["data"]["handed_over_by_id"] is None
    assert [log.log_type for log in _logs(repair_id)].count("handover_change") == 2


def test_open_repair_cannot_be_handed_over(helper_client):
    _enable_handover()
    repair_id = _create_repair(helper_client)

    response = helper_client.post(f"/api/repairs/{repair_id}/handover")

    assert response.status_code == 409
    assert _logs(repair_id) == []


def test_reopening_clears_handover(helper_client, helper_user):
    _enable_handover()
    repair_id = _create_repair(helper_client)
    _close_repair(helper_client, repair_id, helper_user.id)
    helper_client.post(f"/api/repairs/{repair_id}/handover")

    response = helper_client.put(
        f"/api/repairs/{repair_id}", json={"status": "In Bearbeitung"}
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["handed_over_at"] is None
    assert data["handed_over_by_id"] is None


def test_handover_endpoints_are_blocked_when_feature_is_disabled(helper_client):
    repair_id = _create_repair(helper_client)

    assert helper_client.post(f"/api/repairs/{repair_id}/handover").status_code == 409
    assert helper_client.delete(f"/api/repairs/{repair_id}/handover").status_code == 409
    assert _logs(repair_id) == []


def test_handover_feature_flag_is_configurable(helper_client):
    assert helper_client.get("/api/config/features").get_json()["repair_handover"] is False

    _make_user("handover_admin", is_admin=True)
    login = helper_client.post(
        "/api/auth/login",
        json={"username": "handover_admin", "password": "secret"},
    )
    assert login.status_code == 200

    response = helper_client.put(
        "/api/config/app-config",
        json={"repair_handover_enabled": True},
    )
    assert response.status_code == 200
    assert response.get_json()["repair_handover_enabled"] is True
    assert helper_client.get("/api/config/features").get_json()["repair_handover"] is True


def test_status_change_clears_incompatible_status_detail(helper_client, helper_user):
    repair_id = _create_repair(helper_client)
    helper_client.put(
        f"/api/repairs/{repair_id}",
        json={"status": "In Bearbeitung", "user_id": helper_user.id},
    )
    response = helper_client.put(
        f"/api/repairs/{repair_id}",
        json={
            "status": "Nicht Repariert",
            "status_detail": "Nicht moeglich",
            "reparatur_besch": "Ersatzteil nicht erhältlich",
        },
    )
    assert response.status_code == 200

    response = helper_client.put(
        f"/api/repairs/{repair_id}", json={"status": "In Bearbeitung"}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["status_detail"] is None


def test_list_includes_latest_log(helper_client, helper_user):
    repair_id = _create_repair(helper_client)
    helper_client.put(
        f"/api/repairs/{repair_id}", json={"status": "In Bearbeitung", "user_id": helper_user.id}
    )
    helper_client.post(
        f"/api/repairs/{repair_id}/logs",
        json={"repair_id": repair_id, "user_id": helper_user.id, "reparatur_besch": "Gehäuse geöffnet"},
    )

    [item] = helper_client.get("/api/list").get_json()["data"]

    assert item["latest_log"]["reparatur_besch"] == "Gehäuse geöffnet"
    assert item["latest_log"]["user"]["id"] == helper_user.id


def test_list_latest_log_is_null_without_logs(helper_client):
    _create_repair(helper_client)

    [item] = helper_client.get("/api/list").get_json()["data"]

    assert item["latest_log"] is None


def _upload_png(client, repair_id: int, attachment_type: str) -> int:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (16, 16), "blue").save(buf, format="PNG")
    buf.seek(0)
    resp = client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={"files": (buf, "photo.png", "image/png"), "attachment_type": attachment_type},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    return resp.get_json()["data"][0]["id"]


def test_list_includes_newest_device_photo(helper_client, app):
    repair_id = _create_repair(helper_client)
    _upload_png(helper_client, repair_id, "misc")
    _upload_png(helper_client, repair_id, "device_photo")
    newest = _upload_png(helper_client, repair_id, "device_photo")

    [item] = helper_client.get("/api/list").get_json()["data"]

    assert item["device_photo_id"] == newest


def test_list_device_photo_is_null_without_photos(helper_client):
    repair_id = _create_repair(helper_client)
    _upload_png(helper_client, repair_id, "misc")

    [item] = helper_client.get("/api/list").get_json()["data"]

    assert item["device_photo_id"] is None


def test_new_device_photo_replaces_the_old_one(helper_client, app):
    from pathlib import Path

    from app.models import RepairAttachment

    repair_id = _create_repair(helper_client)
    first = _upload_png(helper_client, repair_id, "device_photo")
    first_file = Path(app.config["DATA_DIR"]) / "attachments" / str(repair_id) / (
        RepairAttachment.query.get(first).stored_filename
    )
    assert first_file.exists()

    second = _upload_png(helper_client, repair_id, "device_photo")

    photos = RepairAttachment.query.filter_by(repair_id=repair_id, attachment_type="device_photo").all()
    assert [p.id for p in photos] == [second]
    assert not first_file.exists()


def test_device_photo_upload_takes_exactly_one_image(helper_client):
    import io

    from PIL import Image

    repair_id = _create_repair(helper_client)

    def png():
        buf = io.BytesIO()
        Image.new("RGB", (8, 8), "red").save(buf, format="PNG")
        buf.seek(0)
        return buf

    resp = helper_client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={
            "files": [(png(), "a.png", "image/png"), (png(), "b.png", "image/png")],
            "attachment_type": "device_photo",
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400

    pdf = io.BytesIO(b"%PDF-1.4\n%fake\n")
    resp = helper_client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={"files": (pdf, "scan.pdf", "application/pdf"), "attachment_type": "device_photo"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
