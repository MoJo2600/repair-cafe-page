"""Add repair handover tracking.

Revision ID: 018
Revises: 017
"""

import sqlalchemy as sa
from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade():
    op.bulk_insert(
        sa.table(
            "app_config",
            sa.column("key", sa.String),
            sa.column("value", sa.Text),
        ),
        [{"key": "repair_handover_enabled", "value": "false"}],
    )

    with op.batch_alter_table("repairs") as batch_op:
        batch_op.add_column(sa.Column("handed_over_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("handed_over_by_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_repairs_handed_over_by_id_users",
            "users",
            ["handed_over_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
        UPDATE repairs
        SET handed_over_at = COALESCE(closed_at, CURRENT_TIMESTAMP)
        WHERE status IN ('Repariert', 'Nicht Repariert')
        """
    )
    op.execute(
        """
        UPDATE repairs
        SET status_detail = NULL
        WHERE status = 'In Bearbeitung'
          AND status_detail = 'Ersatzteilbesorgung'
        """
    )


def downgrade():
    with op.batch_alter_table("repairs") as batch_op:
        batch_op.drop_constraint(
            "fk_repairs_handed_over_by_id_users", type_="foreignkey"
        )
        batch_op.drop_column("handed_over_by_id")
        batch_op.drop_column("handed_over_at")
    op.execute("DELETE FROM app_config WHERE key = 'repair_handover_enabled'")
