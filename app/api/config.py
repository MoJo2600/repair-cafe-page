"""
Configuration API endpoint.
Reads dropdown data from the settings DB table (replaces dropdown_data.yaml).
"""

import json
from pathlib import Path

import fitz
from flask import Blueprint, Response, current_app, request, send_file

from app.auth.decorators import admin_required
from app.imports.pdfsigner import FIELD_DATE, FIELD_SIGNATURE
from app.models import Setting
from app.schemas import PruefgeraetResponse

config_bp = Blueprint("config", __name__)

# Where admin-uploaded disclaimer templates are persisted.
_DISCLAIMER_STORE = Path(__file__).parent.parent.parent / "data" / "disclaimer.pdf"


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
            $ref: '#/components/schemas/PruefgeraetResponse'
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
      400:
        description: Invalid file
      422:
        description: PDF is missing required AcroForm fields
    """
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
        return Response(
            json.dumps({"reply": "error", "error": f"Could not read PDF: {e}"}),
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
    _DISCLAIMER_STORE.parent.mkdir(parents=True, exist_ok=True)
    _DISCLAIMER_STORE.write_bytes(pdf_bytes)

    pdf_service = current_app.pdf_service  # type: ignore
    pdf_service.reload(str(_DISCLAIMER_STORE))
    current_app.logger.info("Disclaimer template replaced via admin upload")

    return Response(
        json.dumps({"reply": "done"}),
        status=200,
        mimetype="application/json",
    )
