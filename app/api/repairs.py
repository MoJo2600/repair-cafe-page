"""
Repairs API endpoints.
"""

import json
import secrets
from datetime import datetime, timezone

import flask_login
from flask import Blueprint, Response, current_app, request, send_file

from app.extensions import db
from app.models import Customer, Repair, Setting
from app.schemas import RepairCreate, RepairCreateResponse, RepairResponse, RepairUpdate, RepairsTimelinePoint, RepairsTimelineResponse
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
    parameters:
      - name: customer_id
        in: query
        required: false
        type: integer
        description: Filter repairs by customer ID
    responses:
      200:
        description: List of all repairs
      500:
        description: Internal Server Error - database query failed
    """
    try:
        customer_id = request.args.get("customer_id", type=int)
        query = Repair.query
        if customer_id is not None:
            query = query.filter(Repair.customer_id == customer_id)
        repairs = query.all()
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

        STATUS_TRANSITIONS: dict[str, list[str]] = {
            "Offen": ["In Bearbeitung"],
            "In Bearbeitung": ["Offen", "Repariert", "Nicht Repariert"],
            "Repariert": ["Offen", "In Bearbeitung", "Nicht Repariert"],
            "Nicht Repariert": ["Offen", "In Bearbeitung"],
        }

        update_data = validated_data.model_dump(exclude_unset=True)
        old_status = repair.status
        new_status = update_data.get("status")

        # If repair_type_id is being updated, also sync reparatur_art
        if "repair_type_id" in update_data and update_data["repair_type_id"] is not None:
            setting = Setting.query.get(update_data["repair_type_id"])
            if setting:
                update_data["reparatur_art"] = setting.name

        # 1. Validate that the status transition is allowed
        if new_status and new_status != old_status:
            allowed = STATUS_TRANSITIONS.get(old_status, [])
            if new_status not in allowed:
                return Response(
                    json.dumps(
                        {"error": f"Invalid status transition: '{old_status}' → '{new_status}'"}
                    ),
                    status=409,
                    mimetype="application/json",
                )

        # 2. Apply field updates
        for field, value in update_data.items():
            if value is None and field != "user_id":
                continue
            setattr(repair, field, value)

        # 3. Business rule validation on the post-update state
        if new_status and new_status != old_status:
            if new_status == "In Bearbeitung" and not repair.user_id:
                return Response(
                    json.dumps(
                        {"error": "Reparateur ist für diesen Statuswechsel erforderlich"}
                    ),
                    status=422,
                    mimetype="application/json",
                )
            closed_statuses = {"Repariert", "Nicht Repariert"}
            if new_status in closed_statuses and not (repair.reparatur_besch or "").strip():
                return Response(
                    json.dumps({"error": "Reparaturbeschreibung ist erforderlich"}),
                    status=422,
                    mimetype="application/json",
                )

        # 4. Side-effects: manage closed_at and user_id based on the transition
        if new_status and new_status != old_status:
            closed_statuses = {"Repariert", "Nicht Repariert"}
            if new_status in closed_statuses:
                if repair.closed_at is None:
                    repair.closed_at = datetime.now(timezone.utc)
            else:
                # Reopening (→ Offen or → In Bearbeitung from closed) clears closed_at
                repair.closed_at = None
                if new_status == "Offen":
                    repair.user_id = None

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

        # --- Repair type handling ---
        # Look up the repair type setting and auto-populate reparatur_art for backward compat
        repair_type_id = data.get("repair_type_id")
        if repair_type_id:
            setting = Setting.query.get(repair_type_id)
            if setting is None:
                return Response(
                    json.dumps({"reply": "error", "error": f"repair_type_id {repair_type_id} not found"}),
                    status=400,
                    mimetype="application/json",
                )
            data["reparatur_art"] = setting.name
        else:
            # Fallback: reparatur_art must be provided directly
            if not data.get("reparatur_art"):
                return Response(
                    json.dumps({"reply": "error", "error": "repair_type_id is required"}),
                    status=400,
                    mimetype="application/json",
                )

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

        # Record which user created this repair record
        if flask_login.current_user.is_authenticated:
            data["created_by_id"] = flask_login.current_user.id

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
          properties: {}
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

        from app.api.config import _get_app_config

        app_cfg = _get_app_config()

        # Use app_url from config; fall back to the incoming request's host URL
        app_url = app_cfg.app_url or request.host_url.rstrip("/")

        label_service = current_app.label_service  # type: ignore

        result = label_service.print_label(
            repair_data=data,
            app_url=app_url,
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


@repairs_bp.route("/repairs/stats/timeline", methods=["GET"])
def api_repairs_timeline():
    """
    Get repair counts grouped by week and status for the last 12 months.
    ---
    operationId: getRepairsTimeline
    tags:
      - Repairs
    responses:
      200:
        description: Weekly repair counts per status
        schema:
          $ref: '#/definitions/RepairsTimelineResponse'
    """
    from datetime import date, timedelta

    from sqlalchemy import func, text

    cutoff = date.today() - timedelta(days=365)

    rows = (
        db.session.query(
            func.date_format(Repair.datum, "%Y-%u").label("week"),
            Repair.status,
            func.count(Repair.id).label("count"),
        )
        .filter(Repair.datum >= cutoff)
        .group_by(text("week"), Repair.status)
        .order_by(text("week"))
        .all()
    )

    # Collect all distinct weeks in order
    weeks_ordered: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if row.week not in seen:
            weeks_ordered.append(row.week)
            seen.add(row.week)

    # Build a lookup: week -> status -> count
    data_map: dict[str, dict[str, int]] = {w: {} for w in weeks_ordered}
    for row in rows:
        data_map[row.week][row.status] = row.count

    def _week_label(yw: str) -> str:
        try:
            year, week = yw.split("-")
            return f"KW {int(week)} {year}"
        except ValueError:
            return yw

    points = [
        RepairsTimelinePoint(
            week=w,
            label=_week_label(w),
            offen=data_map[w].get("Offen", 0),
            in_bearbeitung=data_map[w].get("In Bearbeitung", 0),
            abgeschlossen=data_map[w].get("Repariert", 0),
            nicht_repariert=data_map[w].get("Nicht Repariert", 0),
        )
        for w in weeks_ordered
    ]

    return Response(
        RepairsTimelineResponse(data=points).model_dump_json(),
        status=200,
        mimetype="application/json",
    )
