"""Drop legacy reparatur_sonstiges column from repairs table.

The field was a free-text 'other repair category' that predates the
repair_type_id FK to the settings table. It is no longer used.

Revision ID: 010
Revises: 009
Create Date: 2026-07-18
"""

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("repairs", "reparatur_sonstiges")


def downgrade():
    op.add_column(
        "repairs",
        sa.Column("reparatur_sonstiges", sa.String(100), nullable=True),
    )
