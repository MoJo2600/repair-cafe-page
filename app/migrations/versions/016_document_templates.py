"""Add versioned document templates and link generated attachments.

Revision ID: 016
Revises: 015
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, unique=True),
        sa.Column("active_version_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "role IN ('disclaimer', 'cancellation')",
            name="ck_document_templates_role",
        ),
    )
    op.create_index(
        "ix_document_templates_role", "document_templates", ["role"], unique=True
    )
    op.create_table(
        "document_template_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("document_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("html", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "template_id",
            "version_number",
            name="uq_document_template_version_number",
        ),
    )
    op.create_index(
        "ix_document_template_versions_template_id",
        "document_template_versions",
        ["template_id"],
    )
    with op.batch_alter_table("document_templates") as batch_op:
        batch_op.create_foreign_key(
            "fk_document_templates_active_version",
            "document_template_versions",
            ["active_version_id"],
            ["id"],
            ondelete="SET NULL",
        )

    templates = sa.table(
        "document_templates",
        sa.column("id", sa.Integer),
        sa.column("title", sa.String),
        sa.column("role", sa.String),
    )
    versions = sa.table(
        "document_template_versions",
        sa.column("id", sa.Integer),
        sa.column("template_id", sa.Integer),
        sa.column("version_number", sa.Integer),
        sa.column("html", sa.Text),
        sa.column("published_at", sa.DateTime),
    )
    published_at = datetime.now()
    op.bulk_insert(
        templates,
        [
            {
                "id": 1,
                "title": "Haftungsausschluss",
                "role": "disclaimer",
            },
            {
                "id": 2,
                "title": "Reparaturabbruch",
                "role": "cancellation",
            },
        ],
    )
    op.bulk_insert(
        versions,
        [
            {
                "id": 1,
                "template_id": 1,
                "version_number": 1,
                "html": (
                    "<h1>Haftungsausschluss</h1><p>Reparaturnummer: "
                    "<strong>{{ repair_number }}</strong></p><p>Ich, "
                    "{{ customer_name }}, bestätige, dass das Gerät {{ device }} "
                    "beim Repair Café freiwillig und ohne Garantie auf Erfolg "
                    "bearbeitet wird.</p><p><strong>Fehlerbeschreibung:</strong> "
                    "{{ defect_description }}</p><p>Datum: {{ date }}</p>"
                    "<p>Unterschrift: {{ signature }}</p>"
                ),
                "published_at": published_at,
            },
            {
                "id": 2,
                "template_id": 2,
                "version_number": 1,
                "html": (
                    "<h1>Bestätigung des Reparaturabbruchs</h1>"
                    "<p>Reparaturnummer: <strong>{{ repair_number }}</strong></p>"
                    "<p>Ich, {{ customer_name }}, bestätige den Abbruch der "
                    "Reparatur von {{ device }} und nehme das Gerät wieder in "
                    "Empfang.</p><p>Fehlerbeschreibung: {{ defect_description }}"
                    "</p><p>Datum: {{ date }}</p>"
                    "<p>Unterschrift: {{ signature }}</p>"
                ),
                "published_at": published_at,
            },
        ],
    )
    op.execute("UPDATE document_templates SET active_version_id = 1 WHERE id = 1")
    op.execute("UPDATE document_templates SET active_version_id = 2 WHERE id = 2")

    with op.batch_alter_table("repair_attachments") as batch_op:
        batch_op.add_column(
            sa.Column("template_version_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_repair_attachments_template_version",
            "document_template_versions",
            ["template_version_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_repair_attachments_template_version_id",
        "repair_attachments",
        ["template_version_id"],
    )
    if op.get_bind().dialect.name == "mysql":
        op.execute(
            "ALTER TABLE repair_attachments MODIFY attachment_type "
            "ENUM('log_entry','device_photo','disclaimer','cancellation','misc') "
            "NOT NULL DEFAULT 'misc'"
        )
    # The column remains for downgrade/schema compatibility, but new workflows
    # never store signature data in it. Scrub any values retained by older builds.
    op.execute("UPDATE repairs SET unterschrift = NULL WHERE unterschrift IS NOT NULL")


def downgrade():
    if op.get_bind().dialect.name == "mysql":
        op.execute(
            "UPDATE repair_attachments SET attachment_type = 'misc' "
            "WHERE attachment_type = 'cancellation'"
        )
        op.execute(
            "ALTER TABLE repair_attachments MODIFY attachment_type "
            "ENUM('log_entry','device_photo','disclaimer','misc') "
            "NOT NULL DEFAULT 'misc'"
        )
    op.drop_index(
        "ix_repair_attachments_template_version_id",
        table_name="repair_attachments",
    )
    with op.batch_alter_table("repair_attachments") as batch_op:
        batch_op.drop_constraint(
            "fk_repair_attachments_template_version", type_="foreignkey"
        )
        batch_op.drop_column("template_version_id")
    with op.batch_alter_table("document_templates") as batch_op:
        batch_op.drop_constraint(
            "fk_document_templates_active_version", type_="foreignkey"
        )
    op.drop_index(
        "ix_document_template_versions_template_id",
        table_name="document_template_versions",
    )
    op.drop_table("document_template_versions")
    op.drop_index("ix_document_templates_role", table_name="document_templates")
    op.drop_table("document_templates")
