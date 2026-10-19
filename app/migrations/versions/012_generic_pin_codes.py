"""Generic unique PIN hashes and persisted deployment mode.

Revision ID: 012
Revises: 011
"""

import sqlalchemy as sa
from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    duplicates = connection.execute(sa.text(
        "SELECT door_code_hash FROM users WHERE door_code_hash IS NOT NULL "
        "GROUP BY door_code_hash HAVING COUNT(*) > 1"
    )).first()
    if duplicates:
        raise RuntimeError(
            "Duplicate legacy PIN hashes found. Resolve duplicate ownership "
            "in users.door_code_hash before retrying migration 012."
        )
    has_pins = connection.execute(sa.text(
        "SELECT 1 FROM users WHERE door_code_hash IS NOT NULL LIMIT 1"
    )).first() is not None
    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_door_code_hash")
        batch.alter_column("door_code_hash", new_column_name="pin_code_hash",
                           existing_type=sa.String(64))
    with op.batch_alter_table("users") as batch:
        batch.create_unique_constraint("uq_users_pin_code_hash", ["pin_code_hash"])
    state = op.create_table(
        "pin_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_pin_state_singleton"),
    )
    if has_pins:
        op.bulk_insert(state, [{"id": 1, "mode": "oidc"}])


def downgrade():
    op.drop_table("pin_state")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_pin_code_hash", type_="unique")
        batch.alter_column("pin_code_hash", new_column_name="door_code_hash",
                           existing_type=sa.String(64))
    with op.batch_alter_table("users") as batch:
        batch.create_index("ix_users_door_code_hash", ["door_code_hash"])