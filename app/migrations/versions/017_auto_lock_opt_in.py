"""Make PIN session auto-lock opt-in.

Revision ID: 017
Revises: 016
"""

import sqlalchemy as sa
from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("pin_unlock_sessions") as batch_op:
        batch_op.alter_column(
            "auto_lock_enabled",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.false(),
        )


def downgrade():
    with op.batch_alter_table("pin_unlock_sessions") as batch_op:
        batch_op.alter_column(
            "auto_lock_enabled",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.true(),
        )
