"""Add closed_at to repairs table.

Revision ID: 004
Revises: 003
Create Date: 2026-05-26
"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "repairs",
        sa.Column("closed_at", sa.DateTime, nullable=True),
    )


def downgrade():
    op.drop_column("repairs", "closed_at")
