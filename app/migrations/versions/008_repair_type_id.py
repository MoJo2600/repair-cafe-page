"""Add repair_type_id FK to repairs table.

Replaces the free-text reparatur_art field with a FK to the settings table
(category='repair_type'). reparatur_art is kept for backward-compatibility.

Revision ID: 008
Revises: 007
Create Date: 2026-07-14
"""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "repairs",
        sa.Column("repair_type_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_repairs_repair_type_id",
        "repairs",
        "settings",
        ["repair_type_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_repairs_repair_type_id", "repairs", type_="foreignkey")
    op.drop_column("repairs", "repair_type_id")
