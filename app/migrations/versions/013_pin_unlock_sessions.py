"""Store PIN-switch eligibility and lock state per authenticated session.

Revision ID: 013
Revises: 011
"""

import sqlalchemy as sa
from alembic import op

revision = "013"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pin_unlock_sessions",
        sa.Column("session_id", sa.String(64), primary_key=True),
        sa.Column(
            "active_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "last_activity_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cooldown_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("pin_unlock_sessions")
