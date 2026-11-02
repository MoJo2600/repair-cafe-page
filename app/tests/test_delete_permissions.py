"""
Repairs and customers can only be deleted by admins. Attachments and repair
log entries can also be deleted by the user who uploaded/owns them.
"""

import io

import pytest

from app.extensions import db
from app.models import Customer
from app.tests.conftest import _make_user, login_as
from app.tests.test_repairs_and_cancellation import _create_sample_repair


@pytest.fixture
def admin_user(app):
    return _make_user("testadmin", is_admin=True)


def _add_log(client, repair_id, user_id):
    resp = client.post(
        f"/api/repairs/{repair_id}/logs",
        json={
            "repair_id": repair_id,
            "user_id": user_id,
            "reparatur_dauer": 10,
            "reparatur_besch": "Sicherung getauscht",
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


def _add_attachment(client, repair_id):
    resp = client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={"files": (io.BytesIO(b"%PDF-1.4\n%%EOF\n"), "beleg.pdf", "application/pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    return resp.get_json()["data"][0]["id"]


def test_helper_cannot_delete_repair_or_customer(helper_client, admin_user):
    repair_id = _create_sample_repair(helper_client)
    customer = Customer(vorname="Max", nachname="Muster")
    db.session.add(customer)
    db.session.commit()

    assert helper_client.delete(f"/api/repairs/{repair_id}").status_code == 403
    assert helper_client.delete(f"/api/customers/{customer.id}").status_code == 403

    admin = login_as(helper_client, "testadmin")
    assert admin.delete(f"/api/repairs/{repair_id}").status_code == 200
    assert admin.delete(f"/api/customers/{customer.id}").status_code == 200


def test_helper_deletes_only_own_log_entries(helper_client, helper_user, admin_user):
    repair_id = _create_sample_repair(helper_client)
    other = _make_user("kollege")
    own_log = _add_log(helper_client, repair_id, helper_user.id)
    other_log = _add_log(helper_client, repair_id, other.id)

    url = f"/api/repairs/{repair_id}/logs"
    assert helper_client.delete(f"{url}/{other_log}").status_code == 403
    assert helper_client.delete(f"{url}/{own_log}").status_code == 200
    admin = login_as(helper_client, "testadmin")
    assert admin.delete(f"{url}/{other_log}").status_code == 200


def test_helper_deletes_only_own_attachments(helper_client, admin_user):
    repair_id = _create_sample_repair(helper_client)
    own = _add_attachment(helper_client, repair_id)
    from_admin = _add_attachment(login_as(helper_client, "testadmin"), repair_id)

    url = f"/api/repairs/{repair_id}/attachments"
    helper = login_as(helper_client, "helfer")
    assert helper.delete(f"{url}/{from_admin}").status_code == 403
    assert helper.delete(f"{url}/{own}").status_code == 200
    admin = login_as(helper_client, "testadmin")
    assert admin.delete(f"{url}/{from_admin}").status_code == 200
