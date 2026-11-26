"""Disposable SQLite smoke test for the new reversible Alembic revision."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_document_template_migration_upgrades_and_downgrades():
    engine = sa.create_engine("sqlite://")
    migration_path = (
        Path(__file__).parents[1]
        / "migrations"
        / "versions"
        / "016_document_templates.py"
    )
    spec = importlib.util.spec_from_file_location("document_migration", migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    metadata = sa.MetaData()
    sa.Table("users", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "repairs",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("unterschrift", sa.Text),
    )
    sa.Table("repair_logs", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "repair_attachments",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("repair_id", sa.Integer),
        sa.Column("log_id", sa.Integer),
        sa.Column("attachment_type", sa.String(50), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("uploaded_at", sa.DateTime, nullable=False),
        sa.Column("uploaded_by_id", sa.Integer),
    )

    with engine.begin() as connection:
        metadata.create_all(connection)
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        inspector = sa.inspect(connection)
        assert {
            "document_templates",
            "document_template_versions",
        }.issubset(inspector.get_table_names())
        attachment_columns = {
            item["name"]
            for item in inspector.get_columns("repair_attachments")
        }
        assert "template_version_id" in attachment_columns
        roles = connection.execute(
            sa.text("SELECT role, active_version_id FROM document_templates")
        ).all()
        assert sorted(roles) == [("cancellation", 2), ("disclaimer", 1)]

        migration.downgrade()
        remaining = sa.inspect(connection).get_table_names()
        assert "document_templates" not in remaining
        assert "document_template_versions" not in remaining
        assert "template_version_id" not in {
            item["name"]
            for item in sa.inspect(connection).get_columns("repair_attachments")
        }
