"""Per-session switch for the idle auto-lock (off on personal devices).

Revision ID: 015
Revises: 014
"""

import sqlalchemy as sa
from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "pin_unlock_sessions",
        sa.Column("auto_lock_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade():
    op.drop_column("pin_unlock_sessions", "auto_lock_enabled")
