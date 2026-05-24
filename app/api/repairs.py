"""
Repairs API endpoints.
"""

import json
import secrets

from flask import Blueprint, Response, current_app, request, send_file

from app.extensions import db
from app.models import Customer, Repair
from app.schemas import RepairCreate, RepairCreateResponse, RepairResponse, RepairUpdate
from app.utils import pydantic_to_swagger
from app.validation import validate_request

repairs_bp = Blueprint("repairs", __name__)


@repairs_bp.route("/list", methods=["GET"])
def api_list_repairs():
    """
    Get all repairs as JSON
    ---
    operationId: listRepairs
    tags:
      - Repairs
    responses:
      200:
        description: List of all repairs
      500:
        description: Internal Server Error - database query failed
    """
    try:
        repairs = Repair.query.all()
        # Serialize using Pydantic
        repairs_list = [
            RepairResponse.model_validate(repair).model_dump(mode="json")
            for repair in repairs
        ]
        return Response(
            json.dumps(
                {"reply": "done", "data": repairs_list, "count": len(repairs_list)}
            ),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error in /api/list endpoint: {e}", exc_info=True)

        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/by-token/<token>", methods=["GET"])
def api_get_repair_by_token(token):
    """
    Get a repair record by QR token
    ---
    operationId: getRepairByQrToken
    tags:
      - Repairs
    parameters:
      - name: token
        in: path
        required: true
        type: string
        description: QR token of the repair
    responses:
      200:
        description: Repair record found
      404:
        description: Repair not found
      500:
        description: Internal server error
    """
    try:
        repair = Repair.query.filter_by(qr_token=token).first()

        if not repair:
            return Response(
                json.dumps({"reply": "error", "error": "Repair not found"}),
                status=404,
                mimetype="application/json",
            )

        return Response(
            json.dumps(
                {
                    "reply": "done",
                    "data": RepairResponse.model_validate(repair).model_dump(
                        mode="json"
                    ),
                }
            ),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error getting repair by token: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/<int:id>", methods=["PUT"])
@validate_request(RepairUpdate)
def api_update_repair(validated_data: RepairUpdate, id: int):
    """
    Update an existing repair record
    ---
    operationId: updateRepair
    tags:
      - Repairs
    parameters:
      - name: id
        in: path
        required: true
        type: integer
        description: ID of the repair to update
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/components/schemas/RepairUpdate'
    responses:
      200:
        description: Repair record updated successfully
        schema:
          type: object
          properties:
            reply:
              type: string
              example: "done"
            data:
              $ref: '#/components/schemas/RepairResponse'
      404:
        description: Repair not found
      500:
        description: Internal server error
    """
    try:
        repair = Repair.query.get_or_404(id)

        # Update fields from validated data (only non-None values,
        # except user_id=None which explicitly clears the assigned repairer)
        update_data = validated_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is None and field != "user_id":
                continue
            setattr(repair, field, value)

        db.session.commit()

        # Serialize response using Pydantic
        response_data = {
            "reply": "done",
            "data": RepairResponse.model_validate(repair).model_dump(mode="json"),
        }

        return Response(
            json.dumps(response_data), status=200, mimetype="application/json"
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating repair {id}: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/<int:id>", methods=["DELETE"])
def api_delete_repair(id: int):
    """Delete a repair record."""
    try:
        repair = Repair.query.get_or_404(id)
        db.session.delete(repair)
        db.session.commit()
        return Response(
            json.dumps({"reply": "done", "id": id}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting repair {id}: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs", methods=["POST"])
@validate_request(RepairCreate)
def api_create_repair(validated_data: RepairCreate):
    """
    Create a new repair record
    ---
    operationId: createRepair
    tags:
      - Repairs
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/components/schemas/RepairCreate'
    responses:
      201:
        description: Repair record created successfully
        schema:
          $ref: '#/components/schemas/RepairCreateResponse'
      400:
        description: Bad request - missing required fields
      500:
        description: Internal server error
    """
    try:
        # Convert Pydantic model to dict
        data = validated_data.model_dump()

        # --- Customer handling ---
        # Extract contact fields (used for customer creation; not stored on repair)
        contact_vorname = data.pop("vorname")
        contact_nachname = data.pop("nachname")
        contact_telefon = data.pop("telefon", None)
        contact_email = data.pop("email", None)
        customer_id = data.pop("customer_id", None)
        if customer_id is not None:
            # Link to existing customer
            customer = Customer.query.get(customer_id)
            if customer:
                data["customer_id"] = customer.id
        else:
            # Auto-create a new customer from the submitted contact data
            customer = Customer(
                vorname=contact_vorname,
                nachname=contact_nachname,
                telefon=contact_telefon,
                email=contact_email,
            )
            db.session.add(customer)
            db.session.flush()  # get customer.id without full commit
            data["customer_id"] = customer.id

        # Set unterschrift_haft to True if signature is provided
        if data.get("unterschrift"):
            data["unterschrift_haft"] = True

        # Generate unique QR token
        data["qr_token"] = secrets.token_hex(16)  # 32 character hex string

        # Create repair record
        repair = Repair.from_dict(data)
        db.session.add(repair)
        db.session.commit()

        current_app.logger.info(f"Created repair record with ID: {repair.id}")

        # Generate and persist the signed disclaimer PDF if a signature was provided
        if repair.unterschrift:
            try:
                pdf_service = current_app.pdf_service  # type: ignore
                saved_path = pdf_service.save_signed_pdf(
                    repair_id=repair.id,
                    signature_data=repair.unterschrift,
                    date=repair.datum,
                    name=f"{contact_vorname} {contact_nachname}".strip() or None,
                )
                if saved_path:
                    current_app.logger.info(f"Signed disclaimer saved to {saved_path}")
                else:
                    current_app.logger.warning(
                        f"Signed disclaimer could not be generated for repair {repair.id}"
                    )
            except Exception as pdf_err:
                # PDF generation failure must not block the repair from being created
                current_app.logger.error(
                    f"Error saving signed PDF for repair {repair.id}: {pdf_err}",
                    exc_info=True,
                )

        # Serialize response using Pydantic
        response_data = RepairCreateResponse(
            reply="done",
            message=None,
            error=None,
            id=repair.id,
            data=RepairResponse.model_validate(repair),
        )

        return Response(
            response_data.model_dump_json(), status=201, mimetype="application/json"
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in /api/repairs POST: {e}", exc_info=True)
        # try:
        #     loki.error({"Message": "API create repair error", "Error": str(e)})
        # except Exception:
        #     pass
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/<int:id>/update", methods=["POST"])
def legacy_update_repair(id: int):
    """Update repair (legacy POST endpoint for templates)."""
    try:
        repair = Repair.query.get_or_404(id)
        data = request.get_json()
        for key, value in data.items():
            # Protect qr_token from being overwritten
            if key == "qr_token":
                continue
            if hasattr(repair, key):
                setattr(repair, key, value)
        db.session.commit()
        return Response(
            json.dumps({"reply": "done", "id": id, "data": repair.to_dict()}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/<int:id>/<token>/update", methods=["POST"])
def legacy_update_repair_with_token(id: int, token: str):
    """Update repair with token (for QR code access)."""
    try:
        repair = Repair.query.get_or_404(id)
        if token != repair.qr_token:
            return Response(
                json.dumps({"reply": "error", "error": "invalid token"}),
                status=403,
                mimetype="application/json",
            )
        data = request.get_json()
        for key, value in data.items():
            # Protect qr_token and id from being overwritten
            if key in ("qr_token", "id"):
                continue
            if hasattr(repair, key):
                setattr(repair, key, value)
        db.session.commit()
        return Response(
            json.dumps({"reply": "done", "id": id, "data": repair.to_dict()}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/<int:id>/disclaimer", methods=["POST"])
def api_upload_disclaimer(id: int):
    """Upload a pre-signed disclaimer PDF for a repair."""
    try:
        Repair.query.get_or_404(id)

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
                json.dumps(
                    {"reply": "error", "error": "Uploaded file is not a valid PDF"}
                ),
                status=400,
                mimetype="application/json",
            )

        pdf_service = current_app.pdf_service  # type: ignore
        saved_path = pdf_service.store_uploaded_pdf(id, pdf_bytes)
        current_app.logger.info(f"Uploaded disclaimer PDF stored at {saved_path}")
        return Response(
            json.dumps({"reply": "done"}), status=200, mimetype="application/json"
        )

    except Exception as e:
        current_app.logger.error(
            f"Error uploading disclaimer for repair {id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/<int:id>/disclaimer", methods=["GET"])
def api_get_disclaimer(id: int):
    """
    Download the signed disclaimer PDF for a repair
    ---
    operationId: getRepairDisclaimer
    tags:
      - Repairs
    parameters:
      - name: id
        in: path
        required: true
        type: integer
        description: Repair ID
    responses:
      200:
        description: Signed disclaimer PDF
      404:
        description: Repair or disclaimer not found
      500:
        description: Internal server error
    """
    try:
        repair = Repair.query.get_or_404(id)
        pdf_service = current_app.pdf_service  # type: ignore
        pdf_path = pdf_service.get_stored_pdf_path(id)

        if pdf_path is not None:
            return send_file(
                str(pdf_path),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"disclaimer_{id}.pdf",
            )

        # No stored PDF yet — generate on the fly from the stored signature
        if repair.unterschrift:
            pdf_stream = pdf_service.get_signed_pdf(repair.unterschrift, repair.datum)
            if pdf_stream is None:
                return Response(
                    json.dumps(
                        {"reply": "error", "error": "Could not generate disclaimer PDF"}
                    ),
                    status=500,
                    mimetype="application/json",
                )
            return send_file(
                pdf_stream,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"disclaimer_{id}.pdf",
            )

        return Response(
            json.dumps(
                {"reply": "error", "error": "No disclaimer available for this repair"}
            ),
            status=404,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error serving disclaimer for repair {id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repairs_bp.route("/repairs/<int:id>/print-label", methods=["POST"])
def api_print_label(id: int):
    """
    Print a QR code label for a repair on a label printer.
    ---
    operationId: printRepairLabel
    tags:
      - Repairs
    parameters:
      - name: id
        in: path
        required: true
        type: integer
        description: ID of the repair to print a label for
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            base_url:
              type: string
              description: Base URL for the QR code link (defaults to request host URL)
    responses:
      200:
        description: Label printed successfully
      404:
        description: Repair not found
      503:
        description: Label printer not enabled
      500:
        description: Print error
    """
    if not current_app.config.get("LABEL_PRINTER_ENABLED", False):
        return Response(
            json.dumps({"reply": "error", "error": "Label printer is not enabled"}),
            status=503,
            mimetype="application/json",
        )
    try:
        repair = Repair.query.get_or_404(id)
        data = repair.to_dict()

        req_body = request.get_json(silent=True) or {}

        # Build base URL for the QR code link from the incoming request
        base_url = req_body.get("base_url") or request.host_url.rstrip("/")

        label_service = current_app.label_service  # type: ignore

        from app.api.config import _get_app_config

        app_cfg = _get_app_config()

        result = label_service.print_label(
            repair_data=data,
            base_url=base_url,
            org_name=app_cfg.org_name,
            org_website=app_cfg.org_website,
        )

        status_code = 200 if result.get("reply") == "done" else 500
        return Response(
            json.dumps(result),
            status=status_code,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error printing label for repair {id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )
