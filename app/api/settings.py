"""
Settings API — DB-backed configuration replacing dropdown_data.yaml.

Categories:
  repair_type   — Reparaturarten
  repairer      — Reparateure
  test_device   — Prüfgeräte (with optional serial_number)
"""

import json
from datetime import datetime

from flask import Blueprint, Response

from app.auth.decorators import admin_required
from app.extensions import db
from app.models import Setting
from app.schemas import SettingCreate, SettingResponse, SettingUpdate
from app.validation import parse_request

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET"])
def api_list_settings():
    """
    List all active settings grouped by category.
    ---
    tags:
      - Settings
    operationId: listSettings
    responses:
      200:
        description: Settings grouped by category
    """
    rows = (
        Setting.query.filter_by(is_active=True)
        .order_by(Setting.category, Setting.sort_order, Setting.name)
        .all()
    )
    grouped: dict = {}
    for s in rows:
        if s.category not in grouped:
            grouped[s.category] = []
        item: dict = {"id": s.id, "name": s.name}
        if s.serial_number:
            item["serial_number"] = s.serial_number
        grouped[s.category].append(item)
    return Response(json.dumps(grouped), status=200, mimetype="application/json")


@settings_bp.route("/settings/all", methods=["GET"])
@admin_required
def api_list_all_settings():
    """
    List all settings (including inactive) for admin management.
    ---
    tags:
      - Settings
    operationId: listAllSettings
    responses:
      200:
        description: All settings
        schema:
          type: object
          properties:
            reply:
              type: string
            data:
              type: array
              items:
                $ref: '#/definitions/SettingResponse'
    """
    rows = Setting.query.order_by(
        Setting.category, Setting.sort_order, Setting.name
    ).all()
    data = [SettingResponse.model_validate(s).model_dump(mode="json") for s in rows]
    return Response(
        json.dumps({"reply": "done", "data": data}),
        status=200,
        mimetype="application/json",
    )


@settings_bp.route("/settings", methods=["POST"])
@admin_required
def api_create_setting():
    """
    Create a new setting entry.
    ---
    tags:
      - Settings
    operationId: createSetting
    responses:
      201:
        description: Created
        schema:
          $ref: '#/definitions/SettingResponse'
      409:
        description: Duplicate name in category
    """
    body, err = parse_request(SettingCreate)
    if err:
        return err
    assert body is not None

    conflict = Setting.query.filter_by(category=body.category, name=body.name).first()
    if conflict:
        return Response(
            json.dumps(
                {
                    "reply": "error",
                    "error": "Eintrag mit diesem Namen existiert bereits",
                }
            ),
            status=409,
            mimetype="application/json",
        )

    now = datetime.utcnow()
    setting = Setting(
        category=body.category,
        name=body.name,
        serial_number=body.serial_number,
        sort_order=body.sort_order,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.session.add(setting)
    db.session.commit()
    result = SettingResponse.model_validate(setting).model_dump(mode="json")
    return Response(
        json.dumps({"reply": "done", "data": result}),
        status=201,
        mimetype="application/json",
    )


@settings_bp.route("/settings/<int:setting_id>", methods=["PUT"])
@admin_required
def api_update_setting(setting_id):
    """
    Update a setting entry.
    ---
    tags:
      - Settings
    operationId: updateSetting
    parameters:
      - name: setting_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Updated
        schema:
          $ref: '#/definitions/SettingResponse'
      404:
        description: Not found
      409:
        description: Duplicate name in category
    """
    setting = db.session.get(Setting, setting_id)
    if not setting:
        return Response(
            json.dumps({"reply": "error", "error": "Not found"}),
            status=404,
            mimetype="application/json",
        )

    body, err = parse_request(SettingUpdate)
    if err:
        return err
    assert body is not None

    if body.name is not None:
        conflict = Setting.query.filter(
            Setting.category == setting.category,
            Setting.name == body.name,
            Setting.id != setting_id,
        ).first()
        if conflict:
            return Response(
                json.dumps(
                    {
                        "reply": "error",
                        "error": "Eintrag mit diesem Namen existiert bereits",
                    }
                ),
                status=409,
                mimetype="application/json",
            )
        setting.name = body.name

    if body.serial_number is not None:
        setting.serial_number = body.serial_number
    if body.sort_order is not None:
        setting.sort_order = body.sort_order
    if body.is_active is not None:
        setting.is_active = body.is_active

    setting.updated_at = datetime.utcnow()
    db.session.commit()
    result = SettingResponse.model_validate(setting).model_dump(mode="json")
    return Response(
        json.dumps({"reply": "done", "data": result}),
        status=200,
        mimetype="application/json",
    )


@settings_bp.route("/settings/<int:setting_id>", methods=["DELETE"])
@admin_required
def api_delete_setting(setting_id):
    """
    Delete a setting entry.
    ---
    tags:
      - Settings
    operationId: deleteSetting
    parameters:
      - name: setting_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Deleted
      404:
        description: Not found
    """
    setting = db.session.get(Setting, setting_id)
    if not setting:
        return Response(
            json.dumps({"reply": "error", "error": "Not found"}),
            status=404,
            mimetype="application/json",
        )
    db.session.delete(setting)
    db.session.commit()
    return Response(
        json.dumps({"reply": "done"}), status=200, mimetype="application/json"
    )
