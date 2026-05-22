"""
Repair Logs API endpoints for tracking work sessions.
"""

import json
import mimetypes
from pathlib import Path

from flask import Blueprint, Response, current_app, request
from flask import send_file as flask_send_file
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Repair, RepairLog
from app.schemas import (
    RepairLogCreate,
    RepairLogListResponse,
    RepairLogResponse,
    RepairLogUpdate,
)
from app.validation import validate_request

_LOG_ATTACH_ROOT = (
    Path(__file__).parent.parent.parent / "data" / "repair_log_attachments"
)


repair_logs_bp = Blueprint("repair_logs", __name__)


@repair_logs_bp.route("/repairs/<int:repair_id>/logs", methods=["GET"])
def api_list_repair_logs(repair_id):
    """
    Get all log entries for a specific repair
    ---
    operationId: listRepairLogs
    tags:
      - Repair Logs
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
        description: The repair ID
    responses:
      200:
        description: List of repair log entries
        schema:
          $ref: '#/components/schemas/RepairLogListResponse'
      404:
        description: Repair not found
      500:
        description: Internal Server Error
    """
    try:
        # Check if repair exists
        repair = Repair.query.get(repair_id)
        if not repair:
            return Response(
                json.dumps({"reply": "error", "error": "Repair not found"}),
                status=404,
                mimetype="application/json",
            )

        # Get all logs for this repair
        logs = (
            RepairLog.query.filter_by(repair_id=repair_id)
            .order_by(RepairLog.created_at.desc())
            .all()
        )

        # Serialize using Pydantic
        logs_list = [
            RepairLogResponse.model_validate(log).model_dump(mode="json")
            for log in logs
        ]

        return Response(
            json.dumps({"reply": "done", "data": logs_list, "total": len(logs_list)}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error listing repair logs: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repair_logs_bp.route("/repairs/<int:repair_id>/logs", methods=["POST"])
@validate_request(RepairLogCreate)
def api_create_repair_log(validated_data, repair_id):
    """
    Create a new repair log entry
    ---
    operationId: createRepairLog
    tags:
      - Repair Logs
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
        description: The repair ID
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/RepairLogCreate'
    responses:
      201:
        description: Repair log created successfully
      400:
        description: Invalid input
      404:
        description: Repair not found
      500:
        description: Internal Server Error
    """
    try:
        # Check if repair exists
        repair = Repair.query.get(repair_id)
        if not repair:
            return Response(
                json.dumps({"reply": "error", "error": "Repair not found"}),
                status=404,
                mimetype="application/json",
            )

        # Ensure repair_id matches the URL parameter
        validated_data.repair_id = repair_id

        # Create the repair log
        log_data = validated_data.model_dump(exclude_unset=True)
        new_log = RepairLog(**log_data)

        # increment repair time in parent repair record
        increment_repair_duration(repair_id, repair, new_log)

        db.session.add(new_log)
        db.session.commit()

        # Serialize response
        log_response = RepairLogResponse.model_validate(new_log).model_dump(mode="json")

        return Response(
            json.dumps(
                {
                    "reply": "done",
                    "message": "Repair log created successfully",
                    "data": log_response,
                    "id": new_log.id,
                }
            ),
            status=201,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating repair log: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


def increment_repair_duration(repair_id, repair, new_log):
    if new_log.reparatur_dauer:
        repair.reparatur_dauer = (repair.reparatur_dauer or 0) + new_log.reparatur_dauer
        Repair.query.filter_by(id=repair_id).update(
            {"reparatur_dauer": repair.reparatur_dauer}
        )


@repair_logs_bp.route("/repairs/<int:repair_id>/logs/<int:log_id>", methods=["GET"])
def api_get_repair_log(repair_id, log_id):
    """
    Get a specific repair log entry
    ---
    operationId: getRepairLog
    tags:
      - Repair Logs
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
        description: The repair ID
      - name: log_id
        in: path
        required: true
        schema:
          type: integer
        description: The repair log ID
    responses:
      200:
        description: Repair log details
      404:
        description: Repair log not found
      500:
        description: Internal Server Error
    """
    try:
        log = RepairLog.query.filter_by(id=log_id, repair_id=repair_id).first()

        if not log:
            return Response(
                json.dumps({"reply": "error", "error": "Repair log not found"}),
                status=404,
                mimetype="application/json",
            )

        # Serialize using Pydantic
        log_response = RepairLogResponse.model_validate(log).model_dump(mode="json")

        return Response(
            json.dumps({"reply": "done", "data": log_response}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error getting repair log: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repair_logs_bp.route("/repairs/<int:repair_id>/logs/<int:log_id>", methods=["PUT"])
@validate_request(RepairLogUpdate)
def api_update_repair_log(validated_data, repair_id, log_id):
    """Update an existing repair log entry."""
    try:
        log = RepairLog.query.filter_by(id=log_id, repair_id=repair_id).first()
        if not log:
            return Response(
                json.dumps({"reply": "error", "error": "Repair log not found"}),
                status=404,
                mimetype="application/json",
            )

        old_duration = log.reparatur_dauer or 0

        update_data = validated_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_data.items():
            setattr(log, field, value)

        new_duration = validated_data.reparatur_dauer or old_duration
        if new_duration != old_duration:
            repair = Repair.query.get(repair_id)
            if repair:
                repair.reparatur_dauer = (
                    (repair.reparatur_dauer or 0) - old_duration + new_duration
                )
                Repair.query.filter_by(id=repair_id).update(
                    {"reparatur_dauer": repair.reparatur_dauer}
                )

        db.session.commit()

        log_response = RepairLogResponse.model_validate(log).model_dump(mode="json")
        return Response(
            json.dumps({"reply": "done", "data": log_response}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error updating repair log {log_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repair_logs_bp.route("/repairs/<int:repair_id>/logs/<int:log_id>", methods=["DELETE"])
def api_delete_repair_log(repair_id, log_id):
    """
    Delete a repair log entry
    ---
    operationId: deleteRepairLog
    tags:
      - Repair Logs
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
      - name: log_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Repair log deleted successfully
      404:
        description: Repair log not found
      500:
        description: Internal Server Error
    """
    try:
        log = RepairLog.query.filter_by(id=log_id, repair_id=repair_id).first()
        if not log:
            return Response(
                json.dumps({"reply": "error", "error": "Repair log not found"}),
                status=404,
                mimetype="application/json",
            )

        # Subtract this log's duration from the repair total
        if log.reparatur_dauer:
            repair = Repair.query.get(repair_id)
            if repair:
                repair.reparatur_dauer = max(
                    0, (repair.reparatur_dauer or 0) - log.reparatur_dauer
                )

        db.session.delete(log)
        db.session.commit()

        return Response(
            json.dumps({"reply": "done", "message": "Repair log deleted successfully"}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting repair log {log_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repair_logs_bp.route("/repair_logs/<int:log_id>/attachments", methods=["POST"])
def api_upload_log_attachments(log_id):
    """Upload one or more files as attachments to a repair log entry."""
    try:
        RepairLog.query.get_or_404(log_id)

        files = request.files.getlist("files")
        if not files:
            return Response(
                json.dumps({"reply": "error", "error": "No files provided"}),
                status=400,
                mimetype="application/json",
            )

        attach_dir = _LOG_ATTACH_ROOT / str(log_id)
        attach_dir.mkdir(parents=True, exist_ok=True)

        saved = []
        for f in files:
            if not f.filename:
                continue
            filename = secure_filename(f.filename)
            if not filename:
                continue
            dest = attach_dir / filename
            counter = 1
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            while dest.exists():
                dest = attach_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            f.save(str(dest))
            saved.append(dest.name)

        current_app.logger.info(f"Saved {len(saved)} attachments for log {log_id}")
        return Response(
            json.dumps({"reply": "done", "saved": saved}),
            status=201,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error uploading attachments for log {log_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repair_logs_bp.route("/repairs/<int:repair_id>/log_attachments", methods=["GET"])
def api_list_repair_log_attachments(repair_id):
    """List all attachments grouped by log_id for a repair."""
    try:
        Repair.query.get_or_404(repair_id)
        logs = RepairLog.query.filter_by(repair_id=repair_id).all()

        result: dict = {}
        for log in logs:
            attach_dir = _LOG_ATTACH_ROOT / str(log.id)
            if not attach_dir.exists():
                continue
            items = []
            for fpath in sorted(attach_dir.iterdir()):
                if not fpath.is_file():
                    continue
                ct, _ = mimetypes.guess_type(fpath.name)
                items.append(
                    {
                        "name": fpath.name,
                        "url": f"/api/repair_logs/{log.id}/attachments/{fpath.name}",
                        "content_type": ct or "application/octet-stream",
                        "size": fpath.stat().st_size,
                    }
                )
            if items:
                result[str(log.id)] = items

        return Response(
            json.dumps({"reply": "done", "data": result}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(
            f"Error listing log attachments for repair {repair_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@repair_logs_bp.route(
    "/repair_logs/<int:log_id>/attachments/<path:filename>", methods=["GET"]
)
def api_get_log_attachment(log_id, filename):
    """Serve a specific log attachment file."""
    try:
        RepairLog.query.get_or_404(log_id)
        safe_name = secure_filename(filename)
        if not safe_name:
            return Response(
                json.dumps({"reply": "error", "error": "Invalid filename"}),
                status=400,
                mimetype="application/json",
            )

        attach_dir = _LOG_ATTACH_ROOT / str(log_id)
        target = (attach_dir / safe_name).resolve()
        if not str(target).startswith(str(attach_dir.resolve())):
            return Response(
                json.dumps({"reply": "error", "error": "Invalid filename"}),
                status=400,
                mimetype="application/json",
            )

        if not target.exists():
            return Response(
                json.dumps({"reply": "error", "error": "File not found"}),
                status=404,
                mimetype="application/json",
            )

        ct, _ = mimetypes.guess_type(safe_name)
        return flask_send_file(
            str(target),
            mimetype=ct or "application/octet-stream",
            as_attachment=False,
            download_name=safe_name,
        )
    except Exception as e:
        current_app.logger.error(
            f"Error serving attachment {filename} for log {log_id}: {e}", exc_info=True
        )
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )
