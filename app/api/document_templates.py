"""Admin management and authenticated rendering of versioned documents."""

import json
from datetime import datetime

import flask_login
from flask import Blueprint, Response, make_response
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from app.auth.decorators import admin_required
from app.extensions import db
from app.models import DocumentTemplate, DocumentTemplateVersion, Repair
from app.schemas import (
    DocumentBlankPrintRequest,
    DocumentRenderRequest,
    DocumentTemplateListResponse,
    DocumentTemplateResponse,
    DocumentTemplateSingleResponse,
    DocumentTemplateUpdate,
    DocumentTemplateVersionCreate,
    DocumentTemplateVersionResponse,
    DocumentTemplateVersionSingleResponse,
)
from app.services.document_service import (
    DocumentValidationError,
    active_version_for_role,
    pinned_version,
    render_document_html,
    render_document_pdf,
    sanitize_template_html,
)
from app.validation import validate_request

document_templates_bp = Blueprint("document_templates", __name__)


def _error(message: str, status: int = 400) -> Response:
    return Response(
        json.dumps({"reply": "error", "error": message}),
        status=status,
        mimetype="application/json",
    )


def _get_template(template_id: int) -> DocumentTemplate | None:
    return (
        DocumentTemplate.query.options(
            joinedload(DocumentTemplate.active_version),
            selectinload(DocumentTemplate.versions),
        )
        .filter_by(id=template_id)
        .first()
    )


@document_templates_bp.route(
    "/document-templates/active/<string:role>", methods=["GET"]
)
def get_active_document_template(role: str):
    """Get the active published version for a fixed document role.
    ---
    operationId: getActiveDocumentTemplate
    tags: [Documents]
    parameters:
      - name: role
        in: path
        type: string
        enum: [disclaimer, cancellation]
        required: true
    responses:
      200:
        description: Active document template
        schema:
          $ref: '#/definitions/DocumentTemplateSingleResponse'
      404:
        description: Unknown role or no active version
    """
    if role not in {"disclaimer", "cancellation"}:
        return _error("Unbekannter Dokumenttyp", 404)
    try:
        version = active_version_for_role(role)
    except LookupError as exc:
        return _error(str(exc), 404)
    response = DocumentTemplateSingleResponse(
        reply="done", data=DocumentTemplateResponse.model_validate(version.template)
    )
    return Response(response.model_dump_json(), status=200, mimetype="application/json")


@document_templates_bp.route("/document-templates", methods=["GET"])
@admin_required
def list_document_templates():
    """List editable templates and all immutable versions.
    ---
    operationId: listDocumentTemplates
    tags: [Documents]
    responses:
      200:
        description: Document templates
        schema:
          $ref: '#/definitions/DocumentTemplateListResponse'
      403:
        description: Admin access required
    """
    templates = (
        DocumentTemplate.query.options(
            joinedload(DocumentTemplate.active_version),
            selectinload(DocumentTemplate.versions),
        )
        .order_by(DocumentTemplate.role)
        .all()
    )
    payload = DocumentTemplateListResponse(
        reply="done",
        data=[DocumentTemplateResponse.model_validate(item) for item in templates],
        count=len(templates),
    )
    return Response(payload.model_dump_json(), status=200, mimetype="application/json")

@document_templates_bp.route(
    "/document-templates/<int:template_id>", methods=["GET"]
)
@admin_required
def get_document_template(template_id: int):
    """Get a template and its version history.
    ---
    operationId: getDocumentTemplate
    tags: [Documents]
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Document template
        schema:
          $ref: '#/definitions/DocumentTemplateSingleResponse'
      404:
        description: Not found
    """
    template = _get_template(template_id)
    if not template:
        return _error("Dokumentvorlage nicht gefunden", 404)
    response = DocumentTemplateSingleResponse(
        reply="done", data=DocumentTemplateResponse.model_validate(template)
    )
    return Response(response.model_dump_json(), status=200, mimetype="application/json")


@document_templates_bp.route(
    "/document-templates/<int:template_id>", methods=["PUT"]
)
@admin_required
@validate_request(DocumentTemplateUpdate)
def update_document_template(validated_data: DocumentTemplateUpdate, template_id: int):
    """Update mutable template metadata; version HTML is never edited.
    ---
    operationId: updateDocumentTemplate
    tags: [Documents]
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/DocumentTemplateUpdate'
    responses:
      200:
        description: Updated metadata
        schema:
          $ref: '#/definitions/DocumentTemplateSingleResponse'
      404:
        description: Not found
    """
    template = _get_template(template_id)
    if not template:
        return _error("Dokumentvorlage nicht gefunden", 404)
    changes = validated_data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(template, field, value)
    db.session.commit()
    response = DocumentTemplateSingleResponse(
        reply="done", data=DocumentTemplateResponse.model_validate(template)
    )
    return Response(response.model_dump_json(), status=200, mimetype="application/json")

@document_templates_bp.route(
    "/document-templates/<int:template_id>/versions", methods=["POST"]
)
@admin_required
@validate_request(DocumentTemplateVersionCreate)
def create_document_template_version(
    validated_data: DocumentTemplateVersionCreate, template_id: int
):
    """Create a new immutable draft version.
    ---
    operationId: createDocumentTemplateVersion
    tags: [Documents]
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/DocumentTemplateVersionCreate'
    responses:
      201:
        description: Draft version
        schema:
          $ref: '#/definitions/DocumentTemplateVersionSingleResponse'
      400:
        description: Invalid template
      404:
        description: Template not found
    """
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        return _error("Dokumentvorlage nicht gefunden", 404)
    try:
        sanitized = sanitize_template_html(validated_data.html)
    except DocumentValidationError as exc:
        return _error(str(exc))
    next_number = (
        db.session.query(func.max(DocumentTemplateVersion.version_number))
        .filter_by(template_id=template_id)
        .scalar()
        or 0
    ) + 1
    version = DocumentTemplateVersion(
        template_id=template_id,
        version_number=next_number,
        html=sanitized,
        created_by_id=flask_login.current_user.id,
    )
    db.session.add(version)
    db.session.commit()
    response = DocumentTemplateVersionSingleResponse(
        reply="done", data=DocumentTemplateVersionResponse.model_validate(version)
    )
    return Response(response.model_dump_json(), status=201, mimetype="application/json")


@document_templates_bp.route(
    "/document-templates/<int:template_id>/versions/<int:version_id>/publish",
    methods=["POST"],
)
@admin_required
def publish_document_template_version(template_id: int, version_id: int):
    """Make an immutable version active without changing its content.
    ---
    operationId: publishDocumentTemplateVersion
    tags: [Documents]
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
      - name: version_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Active version
        schema:
          $ref: '#/definitions/DocumentTemplateSingleResponse'
      404:
        description: Template or version not found
    """
    template = _get_template(template_id)
    if not template:
        return _error("Dokumentvorlage nicht gefunden", 404)
    try:
        version = pinned_version(template_id, version_id)
    except LookupError as exc:
        return _error(str(exc), 404)
    if version.published_at is None:
        version.published_at = datetime.now()
    template.active_version_id = version.id
    db.session.commit()
    db.session.refresh(template)
    response = DocumentTemplateSingleResponse(
        reply="done", data=DocumentTemplateResponse.model_validate(template)
    )
    return Response(response.model_dump_json(), status=200, mimetype="application/json")


def _version_for_request(
    template_id: int, version_id: int, *, require_published: bool = False
) -> DocumentTemplateVersion:
    version = pinned_version(template_id, version_id)
    if require_published and version.published_at is None:
        raise LookupError("Dokumentversion ist nicht veröffentlicht")
    return version


@document_templates_bp.route(
    "/document-templates/<int:template_id>/preview", methods=["POST"]
)
@validate_request(DocumentRenderRequest)
def preview_document(validated_data: DocumentRenderRequest, template_id: int):
    """Render a signed HTML preview from a pinned version.
    ---
    operationId: previewDocumentTemplate
    tags: [Documents]
    consumes: [application/json]
    produces: [text/html]
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/DocumentRenderRequest'
    responses:
      200:
        description: Sanitized rendered preview
      400:
        description: Invalid signature or template
      404:
        description: Template, version, or repair not found
    """
    try:
        version = _version_for_request(template_id, validated_data.version_id)
        repair = (
            Repair.query.options(
                joinedload(Repair.customer), joinedload(Repair.repair_type)
            ).get(validated_data.repair_id)
            if validated_data.repair_id
            else None
        )
        if validated_data.repair_id and not repair:
            return _error("Reparatur nicht gefunden", 404)
        body = render_document_html(
            version,
            repair=repair,
            signature=validated_data.signature,
            context=(
                validated_data.context.model_dump(mode="python")
                if validated_data.context
                else None
            ),
        )
    except LookupError as exc:
        return _error(str(exc), 404)
    except DocumentValidationError as exc:
        return _error(str(exc))
    response = make_response(body)
    response.mimetype = "text/html"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; img-src data:; style-src 'unsafe-inline'; sandbox"
    )
    return response


@document_templates_bp.route(
    "/document-templates/<int:template_id>/render", methods=["POST"]
)
@validate_request(DocumentRenderRequest)
def render_document(validated_data: DocumentRenderRequest, template_id: int):
    """Render a PDF from a pinned version without storing an attachment.
    ---
    operationId: renderDocumentTemplate
    tags: [Documents]
    consumes: [application/json]
    produces: [application/pdf]
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/DocumentRenderRequest'
    responses:
      200:
        description: Rendered PDF
      400:
        description: Invalid signature or template
      404:
        description: Template, version, or repair not found
    """
    try:
        version = _version_for_request(
            template_id, validated_data.version_id, require_published=True
        )
        repair = (
            Repair.query.options(
                joinedload(Repair.customer), joinedload(Repair.repair_type)
            ).get(validated_data.repair_id)
            if validated_data.repair_id
            else None
        )
        if validated_data.repair_id and not repair:
            return _error("Reparatur nicht gefunden", 404)
        pdf = render_document_pdf(
            version,
            repair=repair,
            signature=validated_data.signature,
            context=(
                validated_data.context.model_dump(mode="python")
                if validated_data.context
                else None
            ),
        )
    except LookupError as exc:
        return _error(str(exc), 404)
    except DocumentValidationError as exc:
        return _error(str(exc))
    return Response(
        pdf,
        status=200,
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=document.pdf"},
    )


@document_templates_bp.route(
    "/settings/document-templates/<int:template_id>/blank-print", methods=["POST"]
)
@validate_request(DocumentBlankPrintRequest)
def print_blank_document(validated_data: DocumentBlankPrintRequest, template_id: int):
    """Render a blank printable PDF without creating a repair attachment.
    ---
    operationId: printBlankDocumentTemplate
    tags: [Settings, Documents]
    consumes: [application/json]
    produces: [application/pdf]
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/DocumentBlankPrintRequest'
    responses:
      200:
        description: Blank printable PDF
      400:
        description: Invalid template
      404:
        description: Template or version not found
    """
    try:
        version = _version_for_request(
            template_id, validated_data.version_id, require_published=True
        )
        pdf = render_document_pdf(version)
    except LookupError as exc:
        return _error(str(exc), 404)
    except DocumentValidationError as exc:
        return _error(str(exc))
    return Response(
        pdf,
        status=200,
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=document-blank.pdf"},
    )
