"""
Unified Repair Attachments API.

Storage layout: data/attachments/{repair_id}/{stored_filename}
where stored_filename is a UUID + original extension (guaranteed unique).
"""

import json
import shutil
import uuid
from pathlib import Path

import flask_login
from flask import Blueprint, Response, current_app, request
from flask import send_file as flask_send_file
from werkzeug.utils import secure_filename

from app.auth.decorators import forbidden, may_delete
from app.extensions import db
from app.models import ATTACHMENT_TYPES, Repair, RepairAttachment, RepairLog
from app.schemas import RepairAttachmentListResponse, RepairAttachmentResponse

attachments_bp = Blueprint("attachments", __name__)

# Allowed types with the extension used on disk. The type is detected from the
# file content; the client's Content-Type and file name are not trusted.
_ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "application/pdf": ".pdf",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}
# Served inline; everything else is sent as a download.
_INLINE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_HEIC_BRANDS = {b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1"}
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB per file


def _attachment_dir(repair_id: int) -> Path:
    data_dir = Path(current_app.config["DATA_DIR"])
    return data_dir / "attachments" / str(repair_id)


def cleanup_repair_attachments(repair_id: int) -> None:
    """Remove all stored attachment files on disk for a repair."""
    attach_dir = _attachment_dir(repair_id)
    if attach_dir.exists():
        try:
            shutil.rmtree(attach_dir)
        except OSError as oe:
            current_app.logger.warning(
                "Could not remove attachment directory %s: %s", attach_dir, oe
            )


def _make_stored_filename(content_type: str) -> str:
    """Return a UUID-based filename with the extension of the detected type."""
    return f"{uuid.uuid4().hex}{_ALLOWED_TYPES[content_type]}"


def _detect_type(head: bytes) -> str | None:
    """Return the allowed MIME type matching the file's magic bytes, or None."""
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head.startswith(b"%PDF-"):
        return "application/pdf"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in _HEIC_BRANDS:
            return "image/heic"
        if brand == b"qt  ":
            return "video/quicktime"
        if not brand.startswith(b"M4A") and not brand.startswith(b"M4B"):
            return "video/mp4"
    return None


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
            json.dumps({"reply": "error", "error": "Internal Server Error"}),
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

        uploaded_by_id: int | None = None
        if flask_login.current_user.is_authenticated:
            uploaded_by_id = flask_login.current_user.id
        else:
            uploaded_by_id_raw = request.form.get("uploaded_by_id")
            if uploaded_by_id_raw:
                uploaded_by_id = int(uploaded_by_id_raw)

        dest_dir = _attachment_dir(repair_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Check every file before saving any, so a rejected upload stores nothing.
        uploads = []
        for f in files:
            if f.filename == "":
                continue
            ct = _detect_type(f.stream.read(16))
            f.stream.seek(0)
            if ct is None:
                return Response(
                    json.dumps({
                        "reply": "error",
                        "error": "File type not allowed (JPEG, PNG, WebP, HEIC, PDF, MP4, MOV, WebM)",
                    }),
                    status=400,
                    mimetype="application/json",
                )
            uploads.append((f, ct))

        created = []
        saved_paths = []
        for f, ct in uploads:
            original = secure_filename(f.filename)
            stored = _make_stored_filename(ct)
            dest_path = dest_dir / stored

            f.save(str(dest_path))
            saved_paths.append(dest_path)
            size = dest_path.stat().st_size

            if size > _MAX_FILE_SIZE:
                db.session.rollback()
                for path in saved_paths:
                    path.unlink(missing_ok=True)
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
            json.dumps({"reply": "error", "error": "Internal Server Error"}),
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
        type: integer
      - name: attachment_id
        in: path
        required: true
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

        # Older rows hold the client-supplied type; serve anything unexpected
        # as an opaque download.
        content_type = attachment.content_type
        if content_type not in _ALLOWED_TYPES:
            content_type = "application/octet-stream"
        response = flask_send_file(
            str(file_path),
            mimetype=content_type,
            as_attachment=content_type not in _INLINE_TYPES,
            download_name=attachment.original_filename,
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "sandbox"
        return response
    except Exception as e:
        current_app.logger.error(f"Error serving attachment: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": "Internal Server Error"}),
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
        type: integer
      - name: attachment_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Attachment deleted
        schema:
          $ref: '#/definitions/APIResponse'
      403:
        description: Not an admin and not the creator
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
        if not may_delete(attachment.uploaded_by_id):
            return forbidden("Only admins can delete other users' attachments")

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
            json.dumps({"reply": "error", "error": "Internal Server Error"}),
            status=500,
            mimetype="application/json",
        )
