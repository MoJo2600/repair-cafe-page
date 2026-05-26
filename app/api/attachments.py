"""
Unified Repair Attachments API.

Storage layout: data/attachments/{repair_id}/{stored_filename}
where stored_filename is a UUID + original extension (guaranteed unique).
"""

import json
import mimetypes
import os
import uuid
from pathlib import Path

from flask import Blueprint, Response, current_app, request
from flask import send_file as flask_send_file
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import ATTACHMENT_TYPES, Repair, RepairAttachment, RepairLog
from app.schemas import RepairAttachmentListResponse, RepairAttachmentResponse

attachments_bp = Blueprint("attachments", __name__)

_ATTACH_ROOT = Path(__file__).parent.parent.parent / "data" / "attachments"

# Allowed MIME types — extend as needed
_ALLOWED_MIME_PREFIXES = ("image/", "application/pdf", "video/")
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB per file


def _attachment_dir(repair_id: int) -> Path:
    return _ATTACH_ROOT / str(repair_id)


def _make_stored_filename(original: str) -> str:
    """Return a UUID-based filename with the original extension."""
    ext = Path(secure_filename(original)).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def _is_allowed_mime(content_type: str) -> bool:
    return any(content_type.startswith(p) for p in _ALLOWED_MIME_PREFIXES)


# ---------------------------------------------------------------------------
# List attachments  GET /api/repairs/{repair_id}/attachments
# ---------------------------------------------------------------------------


@attachments_bp.route("/repairs/<int:repair_id>/attachments", methods=["GET"])
def api_list_repair_attachments(repair_id):
    """
    List all attachments for a repair
    ---
    operationId: listRepairAttachments
    tags:
      - Attachments
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
      - name: attachment_type
        in: query
        required: false
        schema:
          type: string
          enum: [log_entry, device_photo, disclaimer, misc]
      - name: log_id
        in: query
        required: false
        schema:
          type: integer
    responses:
      200:
        description: List of attachments
        schema:
          $ref: '#/definitions/RepairAttachmentListResponse'
      404:
        description: Repair not found
      500:
        description: Internal Server Error
    """
    try:
        repair = Repair.query.get(repair_id)
        if not repair:
            return Response(
                json.dumps({"reply": "error", "error": "Repair not found"}),
                status=404,
                mimetype="application/json",
            )

        query = RepairAttachment.query.filter_by(repair_id=repair_id)

        attachment_type = request.args.get("attachment_type")
        if attachment_type:
            if attachment_type not in ATTACHMENT_TYPES:
                return Response(
                    json.dumps({"reply": "error", "error": f"Invalid attachment_type. Must be one of: {', '.join(ATTACHMENT_TYPES)}"}),
                    status=400,
                    mimetype="application/json",
                )
            query = query.filter_by(attachment_type=attachment_type)

        log_id = request.args.get("log_id", type=int)
        if log_id is not None:
            query = query.filter_by(log_id=log_id)

        attachments = query.order_by(RepairAttachment.uploaded_at.asc()).all()

        data = [
            RepairAttachmentResponse.model_validate(a).model_dump(mode="json")
            for a in attachments
        ]
        return Response(
            json.dumps({"reply": "done", "data": data, "total": len(data)}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        current_app.logger.error(f"Error listing attachments: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


# ---------------------------------------------------------------------------
# Upload attachments  POST /api/repairs/{repair_id}/attachments
# ---------------------------------------------------------------------------


@attachments_bp.route("/repairs/<int:repair_id>/attachments", methods=["POST"])
def api_upload_repair_attachments(repair_id):
    """
    Upload one or more files to a repair
    ---
    operationId: uploadRepairAttachments
    tags:
      - Attachments
    consumes:
      - multipart/form-data
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
      - name: files
        in: formData
        type: array
        items:
          type: file
        required: true
        description: One or more files to upload
      - name: attachment_type
        in: formData
        type: string
        required: false
        description: "Attachment type: log_entry, device_photo, disclaimer, misc (default: misc)"
      - name: log_id
        in: formData
        type: integer
        required: false
        description: Link to a repair log entry
      - name: uploaded_by_id
        in: formData
        type: integer
        required: false
        description: User ID of the uploader
    responses:
      201:
        description: Attachments uploaded successfully
        schema:
          $ref: '#/definitions/RepairAttachmentListResponse'
      400:
        description: Validation error
      404:
        description: Repair not found
      500:
        description: Internal Server Error
    """
    try:
        repair = Repair.query.get(repair_id)
        if not repair:
            return Response(
                json.dumps({"reply": "error", "error": "Repair not found"}),
                status=404,
                mimetype="application/json",
            )

        files = request.files.getlist("files")
        if not files or all(f.filename == "" for f in files):
            return Response(
                json.dumps({"reply": "error", "error": "No files provided"}),
                status=400,
                mimetype="application/json",
            )

        attachment_type = request.form.get("attachment_type", "misc")
        if attachment_type not in ATTACHMENT_TYPES:
            return Response(
                json.dumps({"reply": "error", "error": f"Invalid attachment_type. Must be one of: {', '.join(ATTACHMENT_TYPES)}"}),
                status=400,
                mimetype="application/json",
            )

        log_id_raw = request.form.get("log_id")
        log_id: int | None = None
        if log_id_raw:
            log_id = int(log_id_raw)
            log = RepairLog.query.get(log_id)
            if not log or log.repair_id != repair_id:
                return Response(
                    json.dumps({"reply": "error", "error": "Log entry not found for this repair"}),
                    status=404,
                    mimetype="application/json",
                )

        uploaded_by_id_raw = request.form.get("uploaded_by_id")
        uploaded_by_id: int | None = None
        if uploaded_by_id_raw:
            uploaded_by_id = int(uploaded_by_id_raw)

        dest_dir = _attachment_dir(repair_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        created = []
        for f in files:
            if f.filename == "":
                continue

            # Detect content type — fall back to stream sniff if absent
            ct = f.content_type or mimetypes.guess_type(f.filename)[0] or "application/octet-stream"
            if not _is_allowed_mime(ct):
                return Response(
                    json.dumps({"reply": "error", "error": f"File type not allowed: {ct}"}),
                    status=400,
                    mimetype="application/json",
                )

            original = secure_filename(f.filename)
            stored = _make_stored_filename(original)
            dest_path = dest_dir / stored

            f.save(str(dest_path))
            size = dest_path.stat().st_size

            if size > _MAX_FILE_SIZE:
                dest_path.unlink(missing_ok=True)
                return Response(
                    json.dumps({"reply": "error", "error": f"File too large (max {_MAX_FILE_SIZE // (1024*1024)} MB)"}),
                    status=400,
                    mimetype="application/json",
                )

            attachment = RepairAttachment(
                repair_id=repair_id,
                log_id=log_id,
                attachment_type=attachment_type,
                original_filename=original,
                stored_filename=stored,
                content_type=ct,
                size=size,
                uploaded_by_id=uploaded_by_id,
            )
            db.session.add(attachment)
            created.append(attachment)

        db.session.commit()

        data = [
            RepairAttachmentResponse.model_validate(a).model_dump(mode="json")
            for a in created
        ]
        return Response(
            json.dumps({"reply": "done", "data": data, "total": len(data)}),
            status=201,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading attachments: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


# ---------------------------------------------------------------------------
# Serve attachment  GET /api/repairs/{repair_id}/attachments/{attachment_id}
# ---------------------------------------------------------------------------


@attachments_bp.route(
    "/repairs/<int:repair_id>/attachments/<int:attachment_id>", methods=["GET"]
)
def api_get_repair_attachment(repair_id, attachment_id):
    """
    Download / serve a single attachment file
    ---
    operationId: getRepairAttachment
    tags:
      - Attachments
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
      - name: attachment_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: File contents
      404:
        description: Attachment not found
      500:
        description: Internal Server Error
    """
    try:
        attachment = RepairAttachment.query.filter_by(
            id=attachment_id, repair_id=repair_id
        ).first()
        if not attachment:
            return Response(
                json.dumps({"reply": "error", "error": "Attachment not found"}),
                status=404,
                mimetype="application/json",
            )

        file_path = _attachment_dir(repair_id) / attachment.stored_filename
        if not file_path.exists():
            return Response(
                json.dumps({"reply": "error", "error": "File not found on disk"}),
                status=404,
                mimetype="application/json",
            )

        return flask_send_file(
            str(file_path),
            mimetype=attachment.content_type,
            as_attachment=False,
            download_name=attachment.original_filename,
        )
    except Exception as e:
        current_app.logger.error(f"Error serving attachment: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


# ---------------------------------------------------------------------------
# Delete attachment  DELETE /api/repairs/{repair_id}/attachments/{attachment_id}
# ---------------------------------------------------------------------------


@attachments_bp.route(
    "/repairs/<int:repair_id>/attachments/<int:attachment_id>", methods=["DELETE"]
)
def api_delete_repair_attachment(repair_id, attachment_id):
    """
    Delete a repair attachment (record + file on disk)
    ---
    operationId: deleteRepairAttachment
    tags:
      - Attachments
    parameters:
      - name: repair_id
        in: path
        required: true
        schema:
          type: integer
      - name: attachment_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Attachment deleted
      404:
        description: Attachment not found
      500:
        description: Internal Server Error
    """
    try:
        attachment = RepairAttachment.query.filter_by(
            id=attachment_id, repair_id=repair_id
        ).first()
        if not attachment:
            return Response(
                json.dumps({"reply": "error", "error": "Attachment not found"}),
                status=404,
                mimetype="application/json",
            )

        file_path = _attachment_dir(repair_id) / attachment.stored_filename
        try:
            file_path.unlink(missing_ok=True)
        except OSError as oe:
            current_app.logger.warning(f"Could not delete file {file_path}: {oe}")

        db.session.delete(attachment)
        db.session.commit()

        return Response(
            json.dumps({"reply": "done", "message": "Attachment deleted"}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting attachment: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )
