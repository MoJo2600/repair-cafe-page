"""Security and compatibility coverage for versioned customer documents."""

import base64
import io
from pathlib import Path

import pymupdf
import pytest
from PIL import Image, ImageDraw

from app.extensions import db
from app.models import (
    DocumentTemplate,
    DocumentTemplateVersion,
    Repair,
    RepairAttachment,
    Setting,
)
from app.tests.conftest import _make_user, login_as


def _signature() -> str:
    image = Image.new("RGBA", (180, 50), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.line([(5, 30), (80, 10), (175, 35)], fill="black", width=3)
    stream = io.BytesIO()
    image.save(stream, "PNG")
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode()


def _repair_payload(repair_type_id: int, **extra) -> dict:
    payload = {
        "datum": "2026-11-20",
        "vorname": "Erika",
        "nachname": "Mustermann",
        "telefon": "0123456789",
        "email": "erika@example.org",
        "geraet_art": "Toaster",
        "defekt_besch": "Heizt nicht",
        "repair_type_id": repair_type_id,
    }
    payload.update(extra)
    return payload


def _repair_type() -> Setting:
    setting = Setting(category="repair_type", name="Elektro", is_active=True)
    db.session.add(setting)
    db.session.commit()
    return setting


def _system_template(role: str) -> DocumentTemplate:
    return DocumentTemplate.query.filter_by(role=role).one()


def _admin(client, name: str = "documents_admin"):
    _make_user(name, is_admin=True)
    return login_as(client, name)


def test_document_contract_is_registered_in_swagger(client):
    spec = client.get("/apispec_1.json").get_json()
    expected_operations = {
        (
            "paths",
            "/api/document-templates/active/{role}",
            "get",
        ): "getActiveDocumentTemplate",
        ("paths", "/api/document-templates", "get"): "listDocumentTemplates",
        (
            "paths",
            "/api/document-templates/{template_id}/versions",
            "post",
        ): "createDocumentTemplateVersion",
        (
            "paths",
            "/api/document-templates/{template_id}/preview",
            "post",
        ): "previewDocumentTemplate",
        (
            "paths",
            "/api/document-templates/{template_id}/render",
            "post",
        ): "renderDocumentTemplate",
        (
            "paths",
            "/api/settings/document-templates/{template_id}/blank-print",
            "post",
        ): "printBlankDocumentTemplate",
    }
    for path, operation_id in expected_operations.items():
        current = spec
        for part in path:
            current = current[part]
        assert current["operationId"] == operation_id
    assert "DocumentTemplateSingleResponse" in spec["definitions"]
    assert "DocumentRenderRequest" in spec["definitions"]
    assert "DocumentTemplateCreate" not in spec["definitions"]


def test_helper_can_resolve_active_system_document(helper_client):
    response = helper_client.get("/api/document-templates/active/disclaimer")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["role"] == "disclaimer"
    assert data["active_version"]["published_at"] is not None

    assert (
        helper_client.get("/api/document-templates/active/custom").status_code == 404
    )


def test_draft_context_preview_renders_unsaved_repair_values(helper_client):
    template = _system_template("disclaimer")
    assert template.active_version_id is not None
    response = helper_client.post(
        f"/api/document-templates/{template.id}/preview",
        json={
            "version_id": template.active_version_id,
            "context": {
                "datum": "2026-11-26",
                "vorname": "Ada",
                "nachname": "Lovelace",
                "telefon": "12345",
                "email": "ada@example.org",
                "repair_type": "Computer",
                "geraet_art": "Laptop",
                "defekt_besch": "Startet nicht",
            },
        },
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Ada Lovelace" in html
    assert "Laptop" in html
    assert "26.11.2026" in html


def test_document_types_are_fixed_and_versions_are_sanitized(client, helper_client):
    denied = helper_client.post(
        "/api/document-templates/1/versions",
        json={"html": "<p>Hallo</p>"},
    )
    assert denied.status_code == 403

    assert helper_client.post(
        "/api/document-templates",
        json={"role": "custom", "title": "Zusatz", "html": "<p>Hallo</p>"},
    ).status_code == 405

    admin = _admin(client)
    invalid = admin.post(
        "/api/document-templates/1/versions",
        json={
            "html": "<p>{{ unknown_customer }}</p>",
        },
    )
    assert invalid.status_code == 400

    created = admin.post(
        "/api/document-templates/1/versions",
        json={
            "html": (
                '<p onclick="alert(1)">Hallo {{ customer_name }}</p>'
                "<script>alert(document.cookie)</script>"
            ),
        },
    )
    assert created.status_code == 201
    saved = created.get_json()["data"]
    html = saved["html"]
    assert "{{ customer_name }}" in html
    assert "<script" not in html
    assert "onclick" not in html

    changed = admin.put(
        f"/api/document-templates/1",
        json={"title": "Übergabedokument"},
    )
    assert changed.status_code == 200
    assert changed.get_json()["data"]["title"] == "Übergabedokument"
    assert sorted(
        template["role"]
        for template in admin.get("/api/document-templates").get_json()["data"]
    ) == ["cancellation", "disclaimer"]
    assert admin.delete("/api/document-templates/1").status_code == 405


def test_template_sanitizer_preserves_alignment_only(client):
    admin = _admin(client)
    created = admin.post(
        "/api/document-templates/1/versions",
        json={
            "html": (
                '<h2 style="text-align: center; position: fixed">Hinweis</h2>'
                '<p style="text-align: justify; background-image: url(javascript:x)">Text</p>'
            )
        },
    )

    assert created.status_code == 201
    html = created.get_json()["data"]["html"]
    assert 'style="text-align: center;"' in html
    assert 'style="text-align: justify;"' in html
    assert "position" not in html
    assert "background-image" not in html


def test_document_versions_are_immutable_and_publishable(client):
    admin = _admin(client)
    template = _system_template("disclaimer")
    created = admin.post(
        f"/api/document-templates/{template.id}/versions",
        json={"html": "<h2>Neue Version</h2><p>{{ customer_name }}</p>"},
    )
    assert created.status_code == 201
    version_id = created.get_json()["data"]["id"]
    version = db.session.get(DocumentTemplateVersion, version_id)
    version.html = "<p>Verändert</p>"
    with pytest.raises(ValueError, match="immutable"):
        db.session.commit()
    db.session.rollback()

    published = admin.post(
        f"/api/document-templates/{template.id}/versions/{version_id}/publish",
        json={},
    )
    assert published.status_code == 200
    assert published.get_json()["data"]["active_version_id"] == version_id
    assert db.session.get(DocumentTemplateVersion, version_id).published_at is not None


def test_preview_and_pdf_pin_version_and_escape_values(helper_client):
    repair_type = _repair_type()
    repair_response = helper_client.post(
        "/api/repairs",
        json=_repair_payload(
            repair_type.id,
            vorname="Erika <script>",
            nachname="Mustermann & Sohn",
        ),
    )
    repair_id = repair_response.get_json()["id"]
    template = _system_template("disclaimer")
    version = template.active_version

    preview = helper_client.post(
        f"/api/document-templates/{template.id}/preview",
        json={
            "version_id": version.id,
            "repair_id": repair_id,
            "signature": _signature(),
        },
    )
    assert preview.status_code == 200
    preview_html = preview.get_data(as_text=True)
    assert "<script>" not in preview_html
    assert "Erika &lt;script&gt; Mustermann &amp; Sohn" in preview_html
    assert "Version v1" in preview_html
    assert "data:image/png;base64," in preview_html

    rendered = helper_client.post(
        f"/api/document-templates/{template.id}/render",
        json={
            "version_id": version.id,
            "repair_id": repair_id,
            "signature": _signature(),
        },
    )
    assert rendered.status_code == 200
    assert rendered.data.startswith(b"%PDF")
    pdf = pymupdf.open(stream=rendered.data, filetype="pdf")
    text = "".join(page.get_text() for page in pdf)
    assert "Erika <script> Mustermann & Sohn" in text
    assert "Version v1" in text
    pdf.close()


def test_system_document_blank_print_returns_pdf_without_attachment(helper_client):
    admin = _admin(helper_client, "blank_print_admin")
    template = _system_template("disclaimer")
    template_id = template.id
    version_id = template.active_version_id
    assert version_id is not None
    response = helper_client.post(
        f"/api/settings/document-templates/{template_id}/blank-print",
        json={"version_id": version_id},
    )
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert RepairAttachment.query.count() == 0


def test_repair_creation_never_persists_or_returns_raw_signature(helper_client):
    repair_type = _repair_type()
    response = helper_client.post(
        "/api/repairs",
        json=_repair_payload(repair_type.id, unterschrift=_signature()),
    )
    assert response.status_code == 201
    body = response.get_json()
    assert "unterschrift" not in body["data"]
    listing = helper_client.get("/api/list").get_json()["data"]
    assert listing and "unterschrift" not in listing[0]
    repair = db.session.get(Repair, body["id"])
    assert repair.unterschrift is None
    assert repair.unterschrift_haft is True
    attachment = RepairAttachment.query.filter_by(
        repair_id=repair.id, attachment_type="disclaimer"
    ).one()
    assert attachment.template_version_id == _system_template("disclaimer").active_version_id

    download = helper_client.get(f"/api/repairs/{repair.id}/disclaimer")
    assert download.status_code == 200
    assert download.data.startswith(b"%PDF")


def test_repair_creation_rolls_back_database_and_file_on_pdf_failure(
    helper_client, monkeypatch, app
):
    repair_type = _repair_type()

    def fail_render(*_args, **_kwargs):
        raise RuntimeError("render failed")

    monkeypatch.setattr("app.api.repairs.render_document_pdf", fail_render)
    response = helper_client.post(
        "/api/repairs",
        json=_repair_payload(repair_type.id, unterschrift=_signature()),
    )
    assert response.status_code == 500
    assert Repair.query.count() == 0
    assert RepairAttachment.query.count() == 0
    attachment_dir = Path(app.config["DATA_DIR"]) / "attachments"
    assert not attachment_dir.exists() or not any(attachment_dir.rglob("*.pdf"))


def test_cancellation_uses_pinned_version_and_unified_attachment(helper_client):
    repair_type = _repair_type()
    repair = helper_client.post(
        "/api/repairs", json=_repair_payload(repair_type.id)
    ).get_json()
    template = _system_template("cancellation")
    response = helper_client.post(
        f"/api/repairs/{repair['id']}/cancellation",
        json={
            "signature": _signature(),
            "template_version_id": template.active_version_id,
        },
    )
    assert response.status_code == 201
    attachment = RepairAttachment.query.filter_by(
        repair_id=repair["id"], attachment_type="cancellation"
    ).one()
    assert attachment.template_version_id == template.active_version_id
    assert Path(helper_client.application.config["DATA_DIR"], "attachments", str(repair["id"]), attachment.stored_filename).exists()


def test_legacy_pdf_directories_are_not_runtime_storage(helper_client, app):
    repair_type = _repair_type()
    repair_id = helper_client.post(
        "/api/repairs", json=_repair_payload(repair_type.id)
    ).get_json()["id"]
    assert "SIGNED_PDF_STORAGE_PATH" not in app.config
    assert "SIGNED_CANCELLATION_STORAGE_PATH" not in app.config
    legacy_paths = []
    for directory in ("signed_disclaimers", "signed_cancellations"):
        legacy_dir = Path(app.config["DATA_DIR"]) / directory
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_pdf = legacy_dir / f"{repair_id}.pdf"
        legacy_pdf.write_bytes(b"%PDF-1.4\nlegacy\n%%EOF")
        legacy_paths.append(legacy_pdf)

    assert helper_client.get(
        f"/api/repairs/{repair_id}/disclaimer"
    ).status_code == 404
    assert helper_client.get(
        f"/api/repairs/{repair_id}/cancellation"
    ).status_code == 404
    assert all(path.exists() for path in legacy_paths)
    assert RepairAttachment.query.filter_by(repair_id=repair_id).count() == 0


def test_legacy_pdf_upload_endpoints_store_unified_attachments(helper_client):
    repair_type = _repair_type()
    repair_id = helper_client.post(
        "/api/repairs", json=_repair_payload(repair_type.id)
    ).get_json()["id"]
    pdf = b"%PDF-1.4\nuploaded\n%%EOF"

    disclaimer = helper_client.post(
        f"/api/repairs/{repair_id}/disclaimer",
        data={"file": (io.BytesIO(pdf), "disclaimer.pdf", "application/pdf")},
        content_type="multipart/form-data",
    )
    cancellation = helper_client.post(
        f"/api/repairs/{repair_id}/cancellation",
        data={"file": (io.BytesIO(pdf), "cancellation.pdf", "application/pdf")},
        content_type="multipart/form-data",
    )
    assert disclaimer.status_code == 200
    assert cancellation.status_code == 201
    types = {
        item.attachment_type
        for item in RepairAttachment.query.filter_by(repair_id=repair_id).all()
    }
    assert types == {"disclaimer", "cancellation"}
