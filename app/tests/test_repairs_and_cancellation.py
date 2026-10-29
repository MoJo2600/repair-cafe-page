"""
Integration tests for:
- Configurable DATA_DIR / CONFIG_DIR isolation
- Cancellation PDF template (GET/POST /api/config/cancellation)
- Per-repair cancellation PDF signing & download (POST/GET /api/repairs/<id>/cancellation)
- VDE test din_pruef boolean update
- Unified RepairAttachment upload (with log_id), SVG XSS blocking, and deletion cleanup
- Legacy endpoints removal verification
"""

import base64
import io
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

from app.extensions import db
from app.models import Repair, Setting
from app.tests.conftest import _make_user


def _make_signature_b64() -> str:
    img = Image.new("RGBA", (200, 60), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(10, 30), (100, 50), (190, 20)], fill="black", width=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _create_sample_repair(helper_client) -> int:
    rt = Setting(category="repair_type", name="Elektro", is_active=True)
    db.session.add(rt)
    db.session.commit()

    resp = helper_client.post(
        "/api/repairs",
        json={
            "datum": "2026-10-29",
            "vorname": "Erika",
            "nachname": "Mustermann",
            "telefon": "0123456789",
            "email": "erika@example.org",
            "geraet_art": "Toaster",
            "defekt_besch": "Heizt nicht",
            "repair_type_id": rt.id,
        },
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_data_dir_and_config_dir_configured(app):
    data_dir = Path(app.config["DATA_DIR"])
    config_dir = Path(app.config["CONFIG_DIR"])
    assert data_dir.exists()
    assert (config_dir / "Disclaimer_sample.pdf").exists()
    assert (config_dir / "Cancellation_sample.pdf").exists()


def test_cancellation_template_get_and_admin_upload(client, helper_client, app):
    # Helper can view default cancellation template
    resp = helper_client.get("/api/config/cancellation")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data.startswith(b"%PDF")

    # Non-admin cannot upload a new cancellation template
    sample_bytes = (Path(app.config["CONFIG_DIR"]) / "Cancellation_sample.pdf").read_bytes()
    resp_forbidden = helper_client.post(
        "/api/config/cancellation",
        data={"file": (io.BytesIO(sample_bytes), "custom_cancellation.pdf")},
        content_type="multipart/form-data",
    )
    assert resp_forbidden.status_code == 403

    # Admin can upload a valid cancellation template
    _make_user("admin_user", is_admin=True, password="secret")
    login_resp = client.post(
        "/api/auth/login", json={"username": "admin_user", "password": "secret"}
    )
    assert login_resp.status_code == 200

    resp_upload = client.post(
        "/api/config/cancellation",
        data={"file": (io.BytesIO(sample_bytes), "custom_cancellation.pdf")},
        content_type="multipart/form-data",
    )
    assert resp_upload.status_code == 200
    assert (Path(app.config["DATA_DIR"]) / "cancellation.pdf").exists()


def test_repair_cancellation_pdf_sign_and_download(helper_client):
    repair_id = _create_sample_repair(helper_client)

    # Initially no cancellation PDF exists
    resp_missing = helper_client.get(f"/api/repairs/{repair_id}/cancellation")
    assert resp_missing.status_code == 404

    # Sign cancellation PDF with base64 signature
    sig = _make_signature_b64()
    resp_sign = helper_client.post(
        f"/api/repairs/{repair_id}/cancellation",
        json={"signature": sig},
    )
    assert resp_sign.status_code == 201
    assert resp_sign.get_json()["reply"] == "done"

    # Download signed cancellation PDF and verify customer name + image embedded
    resp_pdf = helper_client.get(f"/api/repairs/{repair_id}/cancellation")
    assert resp_pdf.status_code == 200
    assert resp_pdf.mimetype == "application/pdf"
    doc = fitz.open(stream=resp_pdf.data, filetype="pdf")
    page = doc.load_page(0)
    text = page.get_text()
    images = page.get_images(full=True)
    doc.close()
    assert "Erika Mustermann" in text
    assert len(images) > 0


def test_vde_test_updates_repair_din_pruef_boolean(helper_client, helper_user):
    repair_id = _create_sample_repair(helper_client)

    resp = helper_client.post(
        f"/api/repairs/{repair_id}/vde-tests",
        json={
            "repair_id": repair_id,
            "prufer_user_id": helper_user.id,
            "gesamtergebnis": True,
        },
    )
    assert resp.status_code == 201

    repair = db.session.get(Repair, repair_id)
    assert repair is not None
    assert repair.din_pruef is True


def test_attachments_unified_log_link_svg_blocked_and_delete_cleanup(
    helper_client, helper_user, app
):
    repair_id = _create_sample_repair(helper_client)

    # Create a repair log entry
    log_resp = helper_client.post(
        f"/api/repairs/{repair_id}/logs",
        json={
            "repair_id": repair_id,
            "user_id": helper_user.id,
            "reparatur_dauer": 15,
            "reparatur_besch": "Gehäuse geöffnet",
        },
    )
    assert log_resp.status_code == 201
    log_id = log_resp.get_json()["id"]

    # SVG upload must be rejected (XSS protection)
    svg_resp = helper_client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={
            "files": (io.BytesIO(b"<svg><script>alert(1)</script></svg>"), "xss.svg", "image/svg+xml"),
            "attachment_type": "log_entry",
            "log_id": str(log_id),
        },
        content_type="multipart/form-data",
    )
    assert svg_resp.status_code == 400

    # Valid PNG upload linked to log_id succeeds and records current_user as uploaded_by_id
    img = Image.new("RGB", (32, 32), "blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    upload_resp = helper_client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={
            "files": (buf, "photo.png", "image/png"),
            "attachment_type": "log_entry",
            "log_id": str(log_id),
        },
        content_type="multipart/form-data",
    )
    assert upload_resp.status_code == 201
    att_data = upload_resp.get_json()["data"][0]
    assert att_data["log_id"] == log_id
    assert att_data["uploaded_by_id"] == helper_user.id

    attach_dir = Path(app.config["DATA_DIR"]) / "attachments" / str(repair_id)
    assert attach_dir.exists()

    # Deleting the repair removes the attachment directory on disk
    del_resp = helper_client.delete(f"/api/repairs/{repair_id}")
    assert del_resp.status_code == 200
    assert not attach_dir.exists()


def test_legacy_endpoints_removed(helper_client):
    repair_id = _create_sample_repair(helper_client)
    assert helper_client.post(f"/api/repairs/{repair_id}/update", json={}).status_code == 404
    assert helper_client.get(f"/api/createDisclaimer/{repair_id}").status_code == 404
