"""Initial schema: create all tables for first release.

Revision ID: 001
Revises:
Create Date: 2026-05-17

Tables created:
  users, settings, customers, repairs, repair_logs, vde_tests

Includes seed data for the settings table (repair_type and test_device categories).
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Seed data for the settings table
# ---------------------------------------------------------------------------

_SETTINGS_SEED = [
    # repair_type -------------------------------------------------------
    {
        "category": "repair_type",
        "name": "Audio",
        "serial_number": None,
        "sort_order": 0,
    },
    {
        "category": "repair_type",
        "name": "Elektro",
        "serial_number": None,
        "sort_order": 1,
    },
    {
        "category": "repair_type",
        "name": "Fahrrad",
        "serial_number": None,
        "sort_order": 2,
    },
    {
        "category": "repair_type",
        "name": "Möbel",
        "serial_number": None,
        "sort_order": 3,
    },
    {"category": "repair_type", "name": "PC", "serial_number": None, "sort_order": 4},
    {
        "category": "repair_type",
        "name": "Spielzeug",
        "serial_number": None,
        "sort_order": 5,
    },
    {
        "category": "repair_type",
        "name": "Schleifarbeiten",
        "serial_number": None,
        "sort_order": 6,
    },
    {
        "category": "repair_type",
        "name": "Telekom",
        "serial_number": None,
        "sort_order": 7,
    },
    {
        "category": "repair_type",
        "name": "Textil",
        "serial_number": None,
        "sort_order": 8,
    },
    {
        "category": "repair_type",
        "name": "Video",
        "serial_number": None,
        "sort_order": 9,
    },
    {
        "category": "repair_type",
        "name": "Sonstiges",
        "serial_number": None,
        "sort_order": 10,
    },
    # test_device -------------------------------------------------------
    {
        "category": "test_device",
        "name": "Benning ST 750",
        "serial_number": "SN-2024-001",
        "sort_order": 0,
    },
    {
        "category": "test_device",
        "name": "Gossen Metrawatt Secutest",
        "serial_number": "SN-2024-002",
        "sort_order": 1,
    },
    {
        "category": "test_device",
        "name": "Fluke 1664 FC",
        "serial_number": "SN-2024-003",
        "sort_order": 2,
    },
]


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


def upgrade():
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("vorname", sa.String(100), nullable=True),
        sa.Column("nachname", sa.String(100), nullable=True),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    # ------------------------------------------------------------------
    # settings
    # ------------------------------------------------------------------
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_settings_category", "settings", ["category"])
    op.create_unique_constraint(
        "uq_settings_category_name", "settings", ["category", "name"]
    )

    # Seed settings
    conn = op.get_bind()
    now = datetime.utcnow()
    settings_tbl = sa.table(
        "settings",
        sa.column("category", sa.String),
        sa.column("name", sa.String),
        sa.column("serial_number", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    conn.execute(
        settings_tbl.insert(),
        [
            {**row, "is_active": True, "created_at": now, "updated_at": now}
            for row in _SETTINGS_SEED
        ],
    )

    # ------------------------------------------------------------------
    # customers
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vorname", sa.String(100), nullable=False),
        sa.Column("nachname", sa.String(100), nullable=False),
        sa.Column("telefon", sa.String(40), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # repairs
    # ------------------------------------------------------------------
    op.create_table(
        "repairs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("datum", sa.Date(), nullable=False),
        sa.Column("reparatur_art", sa.String(100), nullable=False),
        sa.Column("reparatur_sonstiges", sa.String(100), nullable=True),
        sa.Column("geraet_art", sa.String(100), nullable=False),
        sa.Column("defekt_besch", sa.String(400), nullable=True),
        sa.Column("unterschrift_haft", sa.Boolean(), nullable=True),
        sa.Column("unterschrift", sa.Text(), nullable=True),
        sa.Column("din_pruef", sa.Boolean(), nullable=True),
        sa.Column("status_detail", sa.String(100), nullable=True),
        sa.Column("reparatur_besch", sa.String(400), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("reparatur_dauer", sa.SmallInteger(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="Offen"),
        sa.Column("qr_token", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("qr_token"),
    )

    # ------------------------------------------------------------------
    # repair_logs
    # ------------------------------------------------------------------
    op.create_table(
        "repair_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("repair_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("reparatur_dauer", sa.SmallInteger(), nullable=False),
        sa.Column("reparatur_besch", sa.String(400), nullable=False),
        sa.Column("log_type", sa.String(20), nullable=False, server_default="work"),
        sa.Column("status_from", sa.String(20), nullable=True),
        sa.Column("status_to", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["repair_id"], ["repairs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # vde_tests
    # ------------------------------------------------------------------
    op.create_table(
        "vde_tests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("repair_id", sa.Integer(), nullable=False),
        sa.Column("prufer", sa.String(100), nullable=True),
        sa.Column("prufer_user_id", sa.Integer(), nullable=True),
        sa.Column("electrician", sa.String(100), nullable=True),
        sa.Column("pruefgeraet_name", sa.String(100), nullable=True),
        sa.Column("pruefgeraet_serial", sa.String(100), nullable=True),
        sa.Column("sichtpruefung_gehaeuse", sa.Boolean(), nullable=True),
        sa.Column("sichtpruefung_kabel", sa.Boolean(), nullable=True),
        sa.Column("sichtpruefung_stecker", sa.Boolean(), nullable=True),
        sa.Column("sichtpruefung_zugentlastung", sa.Boolean(), nullable=True),
        sa.Column("sichtpruefung_sicherheit", sa.Boolean(), nullable=True),
        sa.Column("schutzklasse", sa.String(50), nullable=True),
        sa.Column("schutzleiter_pruefung", sa.Boolean(), nullable=True),
        sa.Column("isolationspruefung", sa.Boolean(), nullable=True),
        sa.Column("ableitstrom_pruefung", sa.Boolean(), nullable=True),
        sa.Column("gesamtergebnis", sa.Boolean(), nullable=False),
        sa.Column("bemerkungen", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["repair_id"], ["repairs.id"]),
        sa.ForeignKeyConstraint(["prufer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("vde_tests")
    op.drop_table("repair_logs")
    op.drop_table("repairs")
    op.drop_table("customers")
    op.drop_table("settings")
    op.drop_table("users")
