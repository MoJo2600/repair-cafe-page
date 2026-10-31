"""
Repair Logs API endpoints for tracking work sessions.
"""

import json

from flask import Blueprint, Response, current_app

from app.extensions import db
from app.models import Repair, RepairLog
from app.schemas import (
    RepairLogCreate,
    RepairLogListResponse,
    RepairLogResponse,
    RepairLogUpdate,
)
from app.validation import validate_request


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

