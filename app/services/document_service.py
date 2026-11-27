"""Sanitize, render, and persist versioned customer documents."""

import base64
import binascii
import html
import io
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from bleach.css_sanitizer import CSSSanitizer
from bleach.sanitizer import Cleaner
from flask import current_app
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import joinedload
from weasyprint import HTML

from app.extensions import db
from app.models import (
    DocumentTemplate,
    DocumentTemplateVersion,
    Repair,
    RepairAttachment,
)

ALLOWED_PLACEHOLDERS = frozenset(
    {
        "customer_name",
        "customer_first_name",
        "customer_last_name",
        "customer_phone",
        "customer_email",
        "date",
        "repair_number",
        "repair_type",
        "device",
        "defect_description",
        "signature",
        "template_version",
    }
)

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
_MAX_SIGNATURE_BYTES = 1_000_000
_CLEANER = Cleaner(
    tags=frozenset(
        {
            "p",
            "div",
            "span",
            "br",
            "strong",
            "b",
            "em",
            "i",
            "u",
            "ul",
            "ol",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "blockquote",
            "hr",
        }
    ),
    attributes={"*": ["class", "style"]},
    css_sanitizer=CSSSanitizer(allowed_css_properties=frozenset({"text-align"})),
    protocols=frozenset(),
    strip=True,
)

_SYSTEM_TEMPLATES = {
    "disclaimer": {
        "title": "Haftungsausschluss",
        "html": """
<h1>Haftungsausschluss</h1>
<p>Reparaturnummer: <strong>{{ repair_number }}</strong></p>
<p>Ich, {{ customer_name }}, bestätige, dass das Gerät {{ device }}
beim Repair Café freiwillig und ohne Garantie auf Erfolg bearbeitet wird.</p>
<p><strong>Fehlerbeschreibung:</strong> {{ defect_description }}</p>
<p>Datum: {{ date }}</p>
<p>Unterschrift: {{ signature }}</p>
""",
    },
    "cancellation": {
        "title": "Reparaturabbruch",
        "html": """
<h1>Bestätigung des Reparaturabbruchs</h1>
<p>Reparaturnummer: <strong>{{ repair_number }}</strong></p>
<p>Ich, {{ customer_name }}, bestätige den Abbruch der Reparatur
von {{ device }} und nehme das Gerät wieder in Empfang.</p>
<p>Fehlerbeschreibung: {{ defect_description }}</p>
<p>Datum: {{ date }}</p>
<p>Unterschrift: {{ signature }}</p>
""",
    },
}


class DocumentValidationError(ValueError):
    """The stored HTML cannot safely be used as a document template."""


def validate_placeholders(raw_html: str) -> None:
    """Reject unknown or malformed placeholder syntax."""
    tokens = _PLACEHOLDER_RE.findall(raw_html)
    unknown = sorted(set(tokens) - ALLOWED_PLACEHOLDERS)
    if unknown:
        raise DocumentValidationError(
            "Unbekannte Platzhalter: " + ", ".join(unknown)
        )
    remainder = _PLACEHOLDER_RE.sub("", raw_html)
    if "{{" in remainder or "}}" in remainder:
        raise DocumentValidationError("Platzhalter müssen die Form {{ name }} haben")


def sanitize_template_html(raw_html: str) -> str:
    """Sanitize WYSIWYG HTML while preserving validated placeholders."""
    validate_placeholders(raw_html)
    sanitized = _CLEANER.clean(raw_html).strip()
    if not sanitized:
        raise DocumentValidationError("Das Dokument darf nicht leer sein")
    validate_placeholders(sanitized)
    return sanitized


def _signature_markup(signature: str | None) -> str:
    if not signature:
        return (
            '<span class="document-signature document-signature--blank" '
            'aria-label="Unterschriftsfeld">&nbsp;</span>'
        )
    try:
        header, encoded = signature.split(",", 1)
        if header not in ("data:image/png;base64", "data:image/jpeg;base64"):
            raise DocumentValidationError("Unterschrift muss PNG oder JPEG sein")
        payload = base64.b64decode(encoded, validate=True)
        if len(payload) > _MAX_SIGNATURE_BYTES:
            raise DocumentValidationError("Unterschrift ist zu groß")
        image = Image.open(io.BytesIO(payload))
        image.verify()
    except (ValueError, binascii.Error, UnidentifiedImageError, OSError) as exc:
        raise DocumentValidationError("Ungültige Unterschrift") from exc
    mime = "image/png" if header.endswith("png;base64") else "image/jpeg"
    return (
        f'<img src="data:{mime};base64,{encoded}" '
        'alt="Unterschrift" class="document-signature">'
    )


def _template_context(
    version: DocumentTemplateVersion,
    repair: Repair | None,
    signature: str | None,
    document_date: date | datetime | None,
    context: Mapping[str, Any] | None,
) -> dict[str, str]:
    customer = repair.customer if repair else None
    if document_date is None:
        document_date = repair.datum if repair else datetime.now().date()
    if isinstance(document_date, datetime):
        document_date = document_date.date()
    first_name = customer.vorname if customer else ""
    last_name = customer.nachname if customer else ""
    if context:
        first_name = str(context.get("vorname") or "")
        last_name = str(context.get("nachname") or "")
        document_date = context.get("datum") or document_date
    if isinstance(document_date, datetime):
        document_date = document_date.date()
    return {
        "customer_name": f"{first_name} {last_name}".strip(),
        "customer_first_name": first_name,
        "customer_last_name": last_name,
        "customer_phone": (
            str(context.get("telefon") or "")
            if context
            else (customer.telefon or "" if customer else "")
        ),
        "customer_email": (
            str(context.get("email") or "")
            if context
            else (customer.email or "" if customer else "")
        ),
        "date": document_date.strftime("%d.%m.%Y"),
        "repair_number": (
            str(context.get("repair_number") or "")
            if context
            else (str(repair.id) if repair else "")
        ),
        "repair_type": (
            str(context.get("repair_type") or "")
            if context
            else (repair.repair_type.name if repair and repair.repair_type else "")
        ),
        "device": (
            str(context.get("geraet_art") or "")
            if context
            else (repair.geraet_art if repair else "")
        ),
        "defect_description": (
            str(context.get("defekt_besch") or "")
            if context
            else (repair.defekt_besch or "" if repair else "")
        ),
        "signature": _signature_markup(signature),
        "template_version": str(version.version_number),
    }


def render_document_html(
    version: DocumentTemplateVersion,
    *,
    repair: Repair | None = None,
    signature: str | None = None,
    document_date: date | datetime | None = None,
    context: Mapping[str, Any] | None = None,
) -> str:
    """Render sanitized, escaped HTML plus the server-controlled footer."""
    template = version.template
    if not template:
        raise DocumentValidationError("Dokumentvorlage nicht gefunden")
    values = _template_context(version, repair, signature, document_date, context)

    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token == "signature":
            return values[token]
        return html.escape(values[token], quote=True)

    body = _PLACEHOLDER_RE.sub(replace, version.html)
    title = html.escape(template.title, quote=True)
    footer_version = f"v{version.version_number}"
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>{title}</title>
<style>
@page {{ size: A4; margin: 18mm 18mm 22mm; }}
html, body {{ font-family: DejaVu Sans, sans-serif; color: #111; font-size: 11pt; line-height: 1.45; }}
h1, h2, h3, h4, h5, h6 {{ color: #183a37; }}
.document-signature {{ max-width: 70mm; max-height: 25mm; vertical-align: middle; }}
.document-signature--blank {{ display: inline-block; width: 65mm; height: 12mm; border-bottom: 0.3mm solid #333; }}
.server-document-footer {{ position: fixed; left: 0; right: 0; bottom: -13mm; border-top: 0.3mm solid #777; padding-top: 2mm; font-size: 8pt; color: #555; display: flex; justify-content: space-between; }}
</style></head><body>{body}
<footer class="server-document-footer"><span>{title}</span><span>Version {footer_version}</span></footer>
</body></html>"""


def render_document_pdf(
    version: DocumentTemplateVersion,
    *,
    repair: Repair | None = None,
    signature: str | None = None,
    document_date: date | datetime | None = None,
    context: Mapping[str, Any] | None = None,
) -> bytes:
    """Use the exact same HTML renderer for previews and stored PDFs."""
    rendered = render_document_html(
        version,
        repair=repair,
        signature=signature,
        document_date=document_date,
        context=context,
    )
    return HTML(string=rendered).write_pdf()


def active_version_for_role(role: str) -> DocumentTemplateVersion:
    """Resolve a role's current published version."""
    template = (
        DocumentTemplate.query.options(joinedload(DocumentTemplate.active_version))
        .filter_by(role=role)
        .first()
    )
    if not template or not template.active_version:
        raise LookupError(f"Keine aktive Dokumentvorlage für '{role}'")
    if template.active_version.published_at is None:
        raise LookupError("Aktive Dokumentversion ist nicht veröffentlicht")
    if template.active_version.template_id != template.id:
        raise LookupError("Aktive Dokumentversion gehört nicht zur Vorlage")
    return template.active_version


def pinned_version_for_role(
    role: str, version_id: int | None
) -> DocumentTemplateVersion:
    """Pin a supplied version for a system role, or pin its current active version."""
    if version_id is None:
        return active_version_for_role(role)
    version = (
        DocumentTemplateVersion.query.options(
            joinedload(DocumentTemplateVersion.template)
        )
        .join(
            DocumentTemplate,
            DocumentTemplate.id == DocumentTemplateVersion.template_id,
        )
        .filter(
            DocumentTemplateVersion.id == version_id,
            DocumentTemplate.role == role,
        )
        .first()
    )
    if not version:
        raise LookupError("Version gehört nicht zur angeforderten Systemvorlage")
    if version.published_at is None:
        raise LookupError("Dokumentversion ist nicht veröffentlicht")
    return version


def pinned_version(template_id: int, version_id: int) -> DocumentTemplateVersion:
    version = (
        DocumentTemplateVersion.query.options(
            joinedload(DocumentTemplateVersion.template)
        )
        .filter_by(id=version_id, template_id=template_id)
        .first()
    )
    if not version:
        raise LookupError("Dokumentversion nicht gefunden")
    return version


def ensure_system_document_templates() -> None:
    """Idempotently seed the two built-in editable document families."""
    changed = False
    for role, defaults in _SYSTEM_TEMPLATES.items():
        template = DocumentTemplate.query.filter_by(role=role).first()
        if template:
            continue
        template = DocumentTemplate(
            role=role,
            title=defaults["title"],
        )
        db.session.add(template)
        db.session.flush()
        version = DocumentTemplateVersion(
            template_id=template.id,
            version_number=1,
            html=sanitize_template_html(defaults["html"]),
            published_at=datetime.now(),
        )
        db.session.add(version)
        db.session.flush()
        template.active_version_id = version.id
        changed = True
    if changed:
        db.session.commit()


def store_document_attachment(
    *,
    repair: Repair,
    attachment_type: str,
    pdf_bytes: bytes,
    version: DocumentTemplateVersion | None,
    uploaded_by_id: int | None,
    original_filename: str | None = None,
    replace_existing: bool = True,
) -> tuple[RepairAttachment, Path, list[tuple[Path, int]]]:
    """Stage a PDF under attachments and return commit cleanup information."""
    if not pdf_bytes.startswith(b"%PDF-"):
        raise DocumentValidationError("Generiertes Dokument ist keine gültige PDF-Datei")
    destination = (
        Path(current_app.config["DATA_DIR"])
        / "attachments"
        / str(repair.id)
    )
    destination.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.pdf"
    path = destination / stored_filename
    path.write_bytes(pdf_bytes)

    replaced = []
    if replace_existing:
        existing = RepairAttachment.query.filter_by(
            repair_id=repair.id, attachment_type=attachment_type
        ).all()
        for attachment in existing:
            replaced.append((destination / attachment.stored_filename, attachment.id))
            db.session.delete(attachment)

    attachment = RepairAttachment(
        repair_id=repair.id,
        attachment_type=attachment_type,
        original_filename=original_filename or f"{attachment_type}_{repair.id}.pdf",
        stored_filename=stored_filename,
        content_type="application/pdf",
        size=len(pdf_bytes),
        uploaded_by_id=uploaded_by_id,
        template_version_id=version.id if version else None,
    )
    db.session.add(attachment)
    db.session.flush()
    return attachment, path, replaced


def attachment_path(repair_id: int, attachment: RepairAttachment) -> Path:
    return (
        Path(current_app.config["DATA_DIR"])
        / "attachments"
        / str(repair_id)
        / attachment.stored_filename
    )


def cleanup_replaced_document_files(replaced: list[tuple[Path, int]]) -> None:
    """Remove superseded files after a committed attachment replacement."""
    for path, _attachment_id in replaced:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            current_app.logger.warning(
                "Could not remove superseded document %s: %s", path, exc
            )


def latest_document_attachment(
    repair_id: int, attachment_type: str
) -> RepairAttachment | None:
    return (
        RepairAttachment.query.filter_by(
            repair_id=repair_id, attachment_type=attachment_type
        )
        .order_by(RepairAttachment.id.desc())
        .first()
    )
