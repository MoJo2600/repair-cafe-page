"""Add app_config table for organisation name and website.

Revision ID: 002
Revises: 001
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Seed default values
    op.bulk_insert(
        sa.table(
            "app_config",
            sa.column("key", sa.String),
            sa.column("value", sa.Text),
        ),
        [
            {"key": "org_name", "value": "Repair Café"},
            {"key": "org_website", "value": ""},
        ],
    )


def downgrade():
    op.drop_table("app_config")
