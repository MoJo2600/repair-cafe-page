"""Add app_url key to app_config table.

Revision ID: 006
Revises: 005
Create Date: 2026-05-26
"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    op.bulk_insert(
        sa.table(
            "app_config",
            sa.column("key", sa.String),
            sa.column("value", sa.Text),
        ),
        [{"key": "app_url", "value": ""}],
    )


def downgrade():
    op.execute("DELETE FROM app_config WHERE key = 'app_url'")
