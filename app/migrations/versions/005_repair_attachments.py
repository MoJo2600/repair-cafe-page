"""Add unified repair_attachments table.

Revision ID: 005
Revises: 004
Create Date: 2026-05-26
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

VALID_TYPES = ("log_entry", "device_photo", "disclaimer", "misc")


def upgrade():
    op.create_table(
        "repair_attachments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "repair_id",
            sa.Integer,
            sa.ForeignKey("repairs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "log_id",
            sa.Integer,
            sa.ForeignKey("repair_logs.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "attachment_type",
            sa.Enum(*VALID_TYPES, name="attachment_type_enum"),
            nullable=False,
            server_default="misc",
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False, unique=True),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "uploaded_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_table("repair_attachments")
    # Drop the enum type (required for PostgreSQL; no-op on MariaDB)
    try:
        sa.Enum(name="attachment_type_enum").drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
