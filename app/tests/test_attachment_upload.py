"""
Attachment types are detected from the file content, not from the client's
Content-Type or file name, and files are served with nosniff + sandbox CSP.
"""

import io
from pathlib import Path

from PIL import Image

from app.extensions import db
from app.models import RepairAttachment
from app.tests.test_repairs_and_cancellation import _create_sample_repair


def _png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buf, format="PNG")
    return buf.getvalue()


def _upload(client, repair_id, content, filename, content_type):
    return client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={"files": (io.BytesIO(content), filename, content_type)},
        content_type="multipart/form-data",
    )


def test_html_disguised_as_image_is_rejected(helper_client, app):
    repair_id = _create_sample_repair(helper_client)
    html = b"<html><script>alert(document.cookie)</script></html>"
    resp = _upload(helper_client, repair_id, html, "foto.jpg", "image/x,y")
    assert resp.status_code == 400
    assert RepairAttachment.query.count() == 0


def test_rejected_file_in_batch_stores_nothing(helper_client, app):
    repair_id = _create_sample_repair(helper_client)
    resp = helper_client.post(
        f"/api/repairs/{repair_id}/attachments",
        data={
            "files": [
                (io.BytesIO(_png_bytes()), "ok.png", "image/png"),
                (io.BytesIO(b"<svg/>"), "bad.png", "image/png"),
            ]
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert RepairAttachment.query.count() == 0
    attach_dir = Path(app.config["DATA_DIR"]) / "attachments" / str(repair_id)
    assert not attach_dir.exists() or not any(attach_dir.iterdir())


def test_type_and_extension_come_from_content(helper_client):
    repair_id = _create_sample_repair(helper_client)
    resp = _upload(helper_client, repair_id, _png_bytes(), "bild.html", "text/html")
    assert resp.status_code == 201
    att = resp.get_json()["data"][0]
    assert att["content_type"] == "image/png"
    assert RepairAttachment.query.get(att["id"]).stored_filename.endswith(".png")


def test_images_inline_other_types_as_download(helper_client):
    repair_id = _create_sample_repair(helper_client)
    png = _upload(helper_client, repair_id, _png_bytes(), "a.png", "image/png")
    pdf = _upload(helper_client, repair_id, b"%PDF-1.4\n%%EOF\n", "a.pdf", "application/pdf")
    url = f"/api/repairs/{repair_id}/attachments"

    resp = helper_client.get(f"{url}/{png.get_json()['data'][0]['id']}")
    assert resp.mimetype == "image/png"
    assert "attachment" not in resp.headers.get("Content-Disposition", "")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["Content-Security-Policy"] == "sandbox"

    resp = helper_client.get(f"{url}/{pdf.get_json()['data'][0]['id']}")
    assert resp.headers["Content-Disposition"].startswith("attachment")
    assert resp.headers["Content-Security-Policy"] == "sandbox"


def test_legacy_row_with_client_type_is_served_as_download(helper_client):
    repair_id = _create_sample_repair(helper_client)
    resp = _upload(helper_client, repair_id, _png_bytes(), "a.png", "image/png")
    att = RepairAttachment.query.get(resp.get_json()["data"][0]["id"])
    att.content_type = "image/x,y"  # stored by the old upload code
    db.session.commit()

    resp = helper_client.get(f"/api/repairs/{repair_id}/attachments/{att.id}")
    assert resp.mimetype == "application/octet-stream"
    assert resp.headers["Content-Disposition"].startswith("attachment")
