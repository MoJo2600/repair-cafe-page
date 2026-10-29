"""Add OIDC subject and generic PIN code hash to users.

oidc_sub links a user to their Authentik account. pin_code_hash stores the
keyed HMAC of a user's generic PIN code.

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
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("oidc_sub", sa.String(255), nullable=True))
        batch.create_unique_constraint("uq_users_oidc_sub", ["oidc_sub"])
        batch.add_column(sa.Column("pin_code_hash", sa.String(64), nullable=True))
        batch.create_unique_constraint("uq_users_pin_code_hash", ["pin_code_hash"])
    op.create_table(
        "pin_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_pin_state_singleton"),
    )


def downgrade():
    op.drop_table("pin_state")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_pin_code_hash", type_="unique")
        batch.drop_column("pin_code_hash")
        batch.drop_constraint("uq_users_oidc_sub", type_="unique")
        batch.drop_column("oidc_sub")
