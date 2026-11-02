"""Track wrong PINs for per-account and global unlock limits.

Revision ID: 014
Revises: 013
"""

import sqlalchemy as sa
from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "pin_unlock_sessions", sa.Column("primary_user_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        "ix_pin_unlock_sessions_primary_user_id",
        "pin_unlock_sessions",
        ["primary_user_id"],
    )
    op.create_table(
        "pin_unlock_failures",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("primary_user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_pin_unlock_failures_created_at", "pin_unlock_failures", ["created_at"]
    )
    op.create_index(
        "ix_pin_unlock_failures_primary_user_id",
        "pin_unlock_failures",
        ["primary_user_id"],
    )


def downgrade():
    op.drop_table("pin_unlock_failures")
    op.drop_index("ix_pin_unlock_sessions_primary_user_id", "pin_unlock_sessions")
    op.drop_column("pin_unlock_sessions", "primary_user_id")
