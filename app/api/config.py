"""
Configuration API endpoint.
Reads dropdown data from the settings DB table (replaces dropdown_data.yaml).
"""

import io
import json
from pathlib import Path

import fitz
from flask import Blueprint, Response, current_app, request, send_file
from PIL import Image, UnidentifiedImageError

from app.auth.decorators import admin_required, public_endpoint
from app.extensions import db
from app.imports.pdfsigner import FIELD_DATE, FIELD_SIGNATURE
from app.models import AppConfig, Setting
from app.schemas import (
    AppConfigResponse,
    AppConfigUpdate,
    FeaturesResponse,
    PruefgeraetResponse,
)
from app.validation import parse_request

config_bp = Blueprint("config", __name__)

_LOGO_DEFAULT = Path(__file__).parent.parent / "static" / "logo.jpg"


def _get_disclaimer_store() -> Path:
    return Path(current_app.config["DATA_DIR"]) / "disclaimer.pdf"


def _get_cancellation_store() -> Path:
    return Path(current_app.config["DATA_DIR"]) / "cancellation.pdf"


def _get_logo_store() -> Path:
    return Path(current_app.config["DATA_DIR"]) / "logo.png"


_CELEBRATION_SOUND_DEFAULT = Path(__file__).parent.parent / "static" / "fanfare.mp3"
CELEBRATION_SOUND_MAX_BYTES = 2 * 1024 * 1024


def _get_celebration_sound_store() -> Path:
    return Path(current_app.config["DATA_DIR"]) / "celebration.mp3"


def _is_mp3(head: bytes) -> bool:
    """MP3 with an ID3 tag, or starting directly with an MPEG audio frame header."""
    if head.startswith(b"ID3"):
        return True
    return len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0


@config_bp.route("/config/dropdowns", methods=["GET"])
def get_dropdown_config():
    """
    Get dropdown configuration data from DB.
    ---
    operationId: getDropdownConfig
    tags:
      - Configuration
    responses:
      200:
        description: Dropdown configuration data keyed by English category name
        schema:
          $ref: '#/definitions/DropdownConfigResponse'
    """
    repair_types = (
        Setting.query.filter_by(category="repair_type", is_active=True)
        .order_by(Setting.sort_order, Setting.name)
        .all()
    )
    result = {
        "repair_type": [{"id": s.id, "name": s.name} for s in repair_types],
    }
    return Response(json.dumps(result), status=200, mimetype="application/json")


@config_bp.route("/config/pruefgeraete", methods=["GET"])
def get_pruefgeraete():
    """
    Get list of testing devices (Prüfgeräte) from DB.
    ---
    operationId: getPruefgeraete
    tags:
      - Configuration
    responses:
      200:
        description: List of testing devices with name and serial_number
        schema:
          type: array
          items:
            $ref: '#/definitions/PruefgeraetResponse'
    """
    devices = (
        Setting.query.filter_by(category="test_device", is_active=True)
        .order_by(Setting.sort_order, Setting.name)
        .all()
    )
    result = [
        PruefgeraetResponse.model_validate(s).model_dump(mode="json") for s in devices
    ]
    return Response(json.dumps(result), status=200, mimetype="application/json")


@config_bp.route("/config/disclaimer", methods=["GET"])
def get_disclaimer_template():
    """
    Serve the active disclaimer PDF template for inline display.
    ---
    operationId: getDisclaimerTemplate
    tags:
      - Configuration
    responses:
      200:
        description: Active disclaimer PDF
      404:
        description: No disclaimer configured
    """
    pdf_service = current_app.pdf_service  # type: ignore
    path = Path(pdf_service.pdf_path)
    if not path.exists():
        return Response(
            json.dumps({"reply": "error", "error": "No disclaimer PDF configured"}),
            status=404,
            mimetype="application/json",
        )
    return send_file(str(path), mimetype="application/pdf")


def _handle_pdf_template_upload(store_path: Path, pdf_service, label: str) -> Response:
    """Validate an uploaded PDF template for AcroForm fields, persist it, and reload the PDFService."""
    if "file" not in request.files:
        return Response(
            json.dumps({"reply": "error", "error": "No file provided"}),
            status=400,
            mimetype="application/json",
        )

    uploaded_file = request.files["file"]
    if not uploaded_file.filename or not uploaded_file.filename.lower().endswith(
        ".pdf"
    ):
        return Response(
            json.dumps({"reply": "error", "error": "Only PDF files are accepted"}),
            status=400,
            mimetype="application/json",
        )

    pdf_bytes = uploaded_file.read()
    if len(pdf_bytes) < 4 or pdf_bytes[:4] != b"%PDF":
        return Response(
            json.dumps({"reply": "error", "error": "Uploaded file is not a valid PDF"}),
            status=400,
            mimetype="application/json",
        )

    # Validate required AcroForm fields
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(0)
        field_names = {w.field_name for w in (page.widgets() or [])}
        doc.close()
    except Exception as e:
        current_app.logger.warning("Uploaded PDF template could not be read: %s", e)
        return Response(
            json.dumps({"reply": "error", "error": "Could not read PDF"}),
            status=400,
            mimetype="application/json",
        )

    missing = [f for f in (FIELD_DATE, FIELD_SIGNATURE) if f not in field_names]
    if missing:
        found = ", ".join(sorted(field_names)) or "none"
        return Response(
            json.dumps(
                {
                    "reply": "error",
                    "error": (
                        f"PDF is missing required AcroForm fields: {', '.join(missing)}. "
                        f"Fields found in PDF: {found}"
                    ),
                }
            ),
            status=422,
            mimetype="application/json",
        )

    # Persist and hot-reload
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_bytes(pdf_bytes)

    pdf_service.reload(str(store_path))
    current_app.logger.info("%s template replaced via admin upload", label)

    return Response(
        json.dumps({"reply": "done"}),
        status=200,
        mimetype="application/json",
    )


@config_bp.route("/config/disclaimer", methods=["POST"])
@admin_required
def upload_disclaimer_template():
    """
    Upload and activate a new disclaimer PDF template (admin only).
    The PDF must contain AcroForm fields named 'date' and 'signature'.
    Takes effect immediately without a server restart.
    ---
    operationId: uploadDisclaimerTemplate
    tags:
      - Configuration
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: PDF file with required AcroForm fields
    responses:
      200:
        description: Template replaced successfully
        schema:
          $ref: '#/definitions/APIResponse'
      400:
        description: Invalid file
      422:
        description: PDF is missing required AcroForm fields
    """
    return _handle_pdf_template_upload(
        _get_disclaimer_store(),
        current_app.pdf_service,  # type: ignore[attr-defined]
        "Disclaimer",
    )


@config_bp.route("/config/cancellation", methods=["GET"])
def get_cancellation_template():
    """
    Serve the active cancellation PDF template for inline display.
    ---
    operationId: getCancellationTemplate
    tags:
      - Configuration
    responses:
      200:
        description: Active cancellation PDF
      404:
        description: No cancellation template configured
    """
    cancellation_service = current_app.cancellation_pdf_service  # type: ignore[attr-defined]
    path = Path(cancellation_service.pdf_path)
    if not path.exists():
        return Response(
            json.dumps({"reply": "error", "error": "No cancellation PDF configured"}),
            status=404,
            mimetype="application/json",
        )
    return send_file(str(path), mimetype="application/pdf")


@config_bp.route("/config/cancellation", methods=["POST"])
@admin_required
def upload_cancellation_template():
    """
    Upload and activate a new cancellation PDF template (admin only).
    The PDF must contain AcroForm fields named 'date' and 'signature'.
    Takes effect immediately without a server restart.
    ---
    operationId: uploadCancellationTemplate
    tags:
      - Configuration
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: PDF file with required AcroForm fields
    responses:
      200:
        description: Template replaced successfully
        schema:
          $ref: '#/definitions/APIResponse'
      400:
        description: Invalid file
      422:
        description: PDF is missing required AcroForm fields
    """
    return _handle_pdf_template_upload(
        _get_cancellation_store(),
        current_app.cancellation_pdf_service,  # type: ignore[attr-defined]
        "Cancellation",
    )


@config_bp.route("/config/logo", methods=["GET"])
@public_endpoint
def get_logo():
    """
    Serve the active logo image.
    Falls back to the bundled default when no custom logo has been uploaded.
    ---
    operationId: getLogo
    tags:
      - Configuration
    produces:
      - image/png
      - image/jpeg
    responses:
      200:
        description: Logo image
      404:
        description: No logo available
    """
    logo_store = _get_logo_store()
    if logo_store.exists():
        return send_file(str(logo_store), mimetype="image/png")
    if _LOGO_DEFAULT.exists():
        return send_file(str(_LOGO_DEFAULT), mimetype="image/jpeg")
    return Response(
        json.dumps({"reply": "error", "error": "No logo configured"}),
        status=404,
        mimetype="application/json",
    )


@config_bp.route("/config/logo", methods=["POST"])
@admin_required
def upload_logo():
    """
    Upload and activate a new logo image (admin only).
    Accepts PNG or JPEG. The image is validated and stored as PNG.
    Takes effect immediately without a server restart.
    ---
    operationId: uploadLogo
    tags:
      - Configuration
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: PNG or JPEG image file
    responses:
      200:
        description: Logo replaced successfully
        schema:
          $ref: '#/definitions/APIResponse'
      400:
        description: Invalid or missing file
    """
    if "file" not in request.files:
        return Response(
            json.dumps({"reply": "error", "error": "No file provided"}),
            status=400,
            mimetype="application/json",
        )

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return Response(
            json.dumps({"reply": "error", "error": "No filename provided"}),
            status=400,
            mimetype="application/json",
        )

    allowed_extensions = {".png", ".jpg", ".jpeg"}
    suffix = Path(uploaded_file.filename).suffix.lower()
    if suffix not in allowed_extensions:
        return Response(
            json.dumps(
                {
                    "reply": "error",
                    "error": "Only PNG and JPEG images are accepted",
                }
            ),
            status=400,
            mimetype="application/json",
        )

    image_bytes = uploaded_file.read()

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # Raises on invalid/truncated image data
    except (UnidentifiedImageError, Exception):
        return Response(
            json.dumps(
                {"reply": "error", "error": "Uploaded file is not a valid image"}
            ),
            status=400,
            mimetype="application/json",
        )

    # Re-open after verify() (verify() exhausts the stream/resets internal state)
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    # Convert to RGB before saving as PNG (RGBA is fine for PNG, but avoids
    # issues if someone later tries to use it in a JPEG context)
    out = io.BytesIO()
    img.save(out, format="PNG")

    logo_store = _get_logo_store()
    logo_store.parent.mkdir(parents=True, exist_ok=True)
    logo_store.write_bytes(out.getvalue())
    current_app.logger.info("Logo replaced via admin upload")

    return Response(
        json.dumps({"reply": "done"}),
        status=200,
        mimetype="application/json",
    )


# ── Celebration sound ──────────────────────────────────────────────────────


@config_bp.route("/config/celebration-sound", methods=["GET"])
@public_endpoint
def get_celebration_sound():
    """
    Serve the MP3 played when a repair succeeds.
    Public because the lock screen dashboard celebrates too.
    Falls back to the bundled fanfare when no custom sound has been uploaded.
    ---
    operationId: getCelebrationSound
    tags:
      - Configuration
    produces:
      - audio/mpeg
    responses:
      200:
        description: MP3 audio
    """
    store = _get_celebration_sound_store()
    path = store if store.exists() else _CELEBRATION_SOUND_DEFAULT
    response = send_file(str(path), mimetype="audio/mpeg")
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@config_bp.route("/config/celebration-sound", methods=["POST"])
@admin_required
def upload_celebration_sound():
    """
    Upload and activate a custom celebration sound (admin only).
    Accepts an MP3 file of at most 2 MB. Takes effect on the next page load.
    ---
    operationId: uploadCelebrationSound
    tags:
      - Configuration
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: MP3 file (max. 2 MB)
    responses:
      200:
        description: Sound replaced successfully
        schema:
          $ref: '#/definitions/APIResponse'
      400:
        description: Invalid or missing file
    """
    uploaded_file = request.files.get("file")
    if uploaded_file is None or not uploaded_file.filename:
        return Response(
            json.dumps({"reply": "error", "error": "No file provided"}),
            status=400,
            mimetype="application/json",
        )

    data = uploaded_file.read(CELEBRATION_SOUND_MAX_BYTES + 1)
    if len(data) > CELEBRATION_SOUND_MAX_BYTES:
        return Response(
            json.dumps({"reply": "error", "error": "The file is larger than 2 MB"}),
            status=400,
            mimetype="application/json",
        )
    if not _is_mp3(data[:4]):
        return Response(
            json.dumps({"reply": "error", "error": "Only MP3 files are accepted"}),
            status=400,
            mimetype="application/json",
        )

    store = _get_celebration_sound_store()
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_bytes(data)
    current_app.logger.info("Celebration sound replaced via admin upload")
    return Response(
        json.dumps({"reply": "done"}), status=200, mimetype="application/json"
    )


@config_bp.route("/config/celebration-sound", methods=["DELETE"])
@admin_required
def reset_celebration_sound():
    """
    Remove the custom celebration sound and go back to the bundled fanfare (admin only).
    ---
    operationId: resetCelebrationSound
    tags:
      - Configuration
    responses:
      200:
        description: Default sound active again
        schema:
          $ref: '#/definitions/APIResponse'
    """
    _get_celebration_sound_store().unlink(missing_ok=True)
    current_app.logger.info("Celebration sound reset to the default")
    return Response(
        json.dumps({"reply": "done"}), status=200, mimetype="application/json"
    )


# ── App-level configuration (org name, website) ────────────────────────────


def _get_app_config() -> AppConfigResponse:
    """Read org_name, org_website and app_url from the DB, falling back to defaults."""
    defaults = AppConfigResponse()
    org_name_row = db.session.get(AppConfig, "org_name")
    org_website_row = db.session.get(AppConfig, "org_website")
    app_url_row = db.session.get(AppConfig, "app_url")
    return AppConfigResponse(
        org_name=org_name_row.value if org_name_row else defaults.org_name,
        org_website=org_website_row.value if org_website_row else defaults.org_website,
        app_url=app_url_row.value if app_url_row else defaults.app_url,
    )


@config_bp.route("/config/app-config", methods=["GET"])
def get_app_config():
    """
    Get application-level configuration (organisation name and website).
    ---
    operationId: getAppConfig
    tags:
      - Configuration
    responses:
      200:
        description: Current application configuration
        schema:
          $ref: '#/definitions/AppConfigResponse'
    """
    return Response(
        json.dumps(_get_app_config().model_dump()),
        status=200,
        mimetype="application/json",
    )


@config_bp.route("/config/app-config", methods=["PUT"])
@admin_required
def update_app_config():
    """
    Update application-level configuration (admin only).
    ---
    operationId: updateAppConfig
    tags:
      - Configuration
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            org_name:
              type: string
            org_website:
              type: string
            app_url:
              type: string
              description: Application base URL for QR code links on printed labels
    responses:
      200:
        description: Updated configuration
        schema:
          $ref: '#/definitions/AppConfigResponse'
      400:
        description: Invalid request body
    """
    body, err = parse_request(AppConfigUpdate)
    if err:
        return err
    assert body is not None

    from datetime import datetime

    now = datetime.utcnow()

    if body.org_name is not None:
        row = db.session.get(AppConfig, "org_name")
        if row:
            row.value = body.org_name
            row.updated_at = now
        else:
            db.session.add(
                AppConfig(key="org_name", value=body.org_name, updated_at=now)
            )

    if body.org_website is not None:
        row = db.session.get(AppConfig, "org_website")
        if row:
            row.value = body.org_website
            row.updated_at = now
        else:
            db.session.add(
                AppConfig(key="org_website", value=body.org_website, updated_at=now)
            )

    if body.app_url is not None:
        row = db.session.get(AppConfig, "app_url")
        if row:
            row.value = body.app_url
            row.updated_at = now
        else:
            db.session.add(
                AppConfig(key="app_url", value=body.app_url, updated_at=now)
            )

    db.session.commit()

    return Response(
        json.dumps(_get_app_config().model_dump()),
        status=200,
        mimetype="application/json",
    )


@config_bp.route("/config/features", methods=["GET"])
def get_features():
    """
    Return server-side feature flags derived from environment variables.
    ---
    operationId: getFeatures
    tags:
      - Configuration
    responses:
      200:
        description: Feature flags
        schema:
          $ref: '#/definitions/FeaturesResponse'
    """
    return Response(
        json.dumps(
            FeaturesResponse(
                label_printer=bool(
                    current_app.config.get("LABEL_PRINTER_ENABLED", False)
                )
            ).model_dump()
        ),
        status=200,
        mimetype="application/json",
    )
