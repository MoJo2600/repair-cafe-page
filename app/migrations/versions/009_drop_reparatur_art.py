"""Drop legacy reparatur_art column from repairs table.

All data has been migrated to repair_type_id (FK to settings).

Revision ID: 009
Revises: 008
Create Date: 2026-07-16
"""

import sqlalchemy as sa
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("repairs", "reparatur_art")


def downgrade():
    op.add_column(
        "repairs",
        sa.Column("reparatur_art", sa.String(100), nullable=False, server_default=""),
    )
