"""Add OIDC subject and door code hash to users.

oidc_sub links a user to their Authentik account; door_code_hash stores a
keyed HMAC of the member's door code, used as the quick-unlock PIN.

Revision ID: 011
Revises: 010
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("oidc_sub", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_users_oidc_sub", "users", ["oidc_sub"])
    op.add_column("users", sa.Column("door_code_hash", sa.String(64), nullable=True))
    op.create_index("ix_users_door_code_hash", "users", ["door_code_hash"])


def downgrade():
    op.drop_index("ix_users_door_code_hash", table_name="users")
    op.drop_column("users", "door_code_hash")
    op.drop_constraint("uq_users_oidc_sub", "users", type_="unique")
    op.drop_column("users", "oidc_sub")
