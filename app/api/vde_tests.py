"""
VDE Tests API endpoints for electrical safety testing.
"""

import json

from flask import Blueprint, Response, current_app, request

from app.auth.decorators import login_required_api
from app.extensions import db
from app.models import Repair, User, VdeTest
from app.schemas import (
    VdeTestCreate,
    VdeTestCreateResponse,
    VdeTestListResponse,
    VdeTestResponse,
)
from app.services.vde_pdf_service import generate_vde_pdf
from app.validation import parse_request

vde_tests_bp = Blueprint("vde_tests", __name__)


@vde_tests_bp.route("/repairs/<int:repair_id>/vde-tests", methods=["GET"])
def api_list_vde_tests(repair_id):
    """
    Get all VDE test entries for a specific repair
    ---
    operationId: listVdeTests
    tags:
      - VDE Tests
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
        description: The repair ID
    responses:
      200:
        description: List of VDE test entries
        schema:
          $ref: '#/components/schemas/VdeTestListResponse'
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

        # Get all VDE tests for this repair
        tests = (
            VdeTest.query.filter_by(repair_id=repair_id)
            .order_by(VdeTest.created_at.desc())
            .all()
        )

        # Serialize using Pydantic
        tests_list = [
            VdeTestResponse.model_validate(test).model_dump(mode="json")
            for test in tests
        ]

        return Response(
            json.dumps({"reply": "done", "data": tests_list, "total": len(tests_list)}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error listing VDE tests: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@vde_tests_bp.route("/repairs/<int:repair_id>/vde-tests", methods=["POST"])
def api_create_vde_test(repair_id):
    """
    Create a new VDE test entry
    ---
    operationId: createVdeTest
    tags:
      - VDE Tests
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
            $ref: '#/components/schemas/VdeTestCreate'
    responses:
      201:
        description: VDE test created successfully
        schema:
          $ref: '#/components/schemas/VdeTestCreateResponse'
      400:
        description: Invalid input
      404:
        description: Repair not found
      500:
        description: Internal Server Error
    """
    body, err = parse_request(VdeTestCreate)
    if err:
        return err
    assert body is not None

    try:
        # Check if repair exists
        repair = Repair.query.get(repair_id)
        if not repair:
            return Response(
                json.dumps({"reply": "error", "error": "Repair not found"}),
                status=404,
                mimetype="application/json",
            )

        # Resolve prufer name from user FK (for backward compat with PDF/display)
        if body.prufer_user_id:
            user = User.query.get(body.prufer_user_id)
            if user:
                body.prufer = f"{user.vorname or ''} {user.nachname or ''}".strip()

        # Ensure repair_id matches the URL parameter
        body.repair_id = repair_id

        # Create the VDE test
        test_data = body.model_dump(exclude_unset=True)
        new_test = VdeTest(**test_data)

        db.session.add(new_test)

        # Update repair's din_pruef field based on test result
        repair.din_pruef = body.gesamtergebnis == "bestanden"

        db.session.commit()

        # Serialize response
        test_response = VdeTestResponse.model_validate(new_test).model_dump(mode="json")

        return Response(
            VdeTestCreateResponse(
                reply="done",
                message="VDE test created successfully",
                data=VdeTestResponse.model_validate(new_test),
                id=new_test.id,
            ).model_dump_json(),
            status=201,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating VDE test: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@vde_tests_bp.route("/repairs/<int:repair_id>/vde-tests/<int:test_id>", methods=["GET"])
def api_get_vde_test(repair_id, test_id):
    """
    Get a specific VDE test entry
    ---
    operationId: getVdeTest
    tags:
      - VDE Tests
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
        description: The repair ID
      - name: test_id
        in: path
        required: true
        schema:
          type: integer
        description: The VDE test ID
    responses:
      200:
        description: VDE test details
      404:
        description: VDE test not found
      500:
        description: Internal Server Error
    """
    try:
        test = VdeTest.query.filter_by(id=test_id, repair_id=repair_id).first()

        if not test:
            return Response(
                json.dumps({"reply": "error", "error": "VDE test not found"}),
                status=404,
                mimetype="application/json",
            )

        # Serialize using Pydantic
        test_response = VdeTestResponse.model_validate(test).model_dump(mode="json")

        return Response(
            json.dumps({"reply": "done", "data": test_response}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error getting VDE test: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@vde_tests_bp.route(
    "/repairs/<int:repair_id>/vde-tests/<int:test_id>/pdf", methods=["GET"]
)
@login_required_api
def api_get_vde_test_pdf(repair_id, test_id):
    """Download a VDE Prüfprotokoll as PDF for the given test."""
    repair = Repair.query.get(repair_id)
    if not repair:
        return Response(
            json.dumps({"reply": "error", "error": "Repair not found"}),
            status=404,
            mimetype="application/json",
        )

    test = VdeTest.query.filter_by(id=test_id, repair_id=repair_id).first()
    if not test:
        return Response(
            json.dumps({"reply": "error", "error": "VDE test not found"}),
            status=404,
            mimetype="application/json",
        )

    try:
        pdf_bytes = generate_vde_pdf(test, repair)
        filename = f"vde_pruefprotokoll_{repair_id}_{test_id}.pdf"
        return Response(
            pdf_bytes,
            status=200,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        current_app.logger.error(f"Error generating VDE PDF: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )
