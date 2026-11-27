from pathlib import Path

import pytest
import sqlalchemy as sa

from app.migrate_legacy_documents import (
    LegacyDocumentMigrationError,
    migrate_legacy_documents,
)


def _database() -> sa.Engine:
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    sa.Table("repairs", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "repair_attachments",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repair_id", sa.Integer, nullable=False),
        sa.Column("attachment_type", sa.String(50), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False, unique=True),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("uploaded_by_id", sa.Integer),
        sa.Column("template_version_id", sa.Integer),
    )
    metadata.create_all(engine)
    return engine


def _add_repairs(engine: sa.Engine, *repair_ids: int) -> None:
    with engine.begin() as connection:
        connection.execute(
            sa.text("INSERT INTO repairs (id) VALUES (:id)"),
            [{"id": repair_id} for repair_id in repair_ids],
        )


def _write_pdf(directory: Path, repair_id: int, content: bytes) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{repair_id}.pdf"
    path.write_bytes(content)
    return path


def _attachment_rows(engine: sa.Engine) -> list[dict]:
    with engine.connect() as connection:
        return list(
            connection.execute(
                sa.text(
                    """
                    SELECT repair_id, attachment_type, stored_filename, size
                    FROM repair_attachments
                    ORDER BY attachment_type
                    """
                )
            ).mappings()
        )


def test_migration_copies_both_types_and_is_idempotent(tmp_path):
    engine = _database()
    _add_repairs(engine, 1, 2)
    data_dir = tmp_path / "data"
    disclaimer_dir = tmp_path / "legacy-disclaimers"
    cancellation_dir = tmp_path / "legacy-cancellations"
    disclaimer = _write_pdf(disclaimer_dir, 1, b"%PDF-1.4\ndisclaimer\n%%EOF")
    cancellation = _write_pdf(
        cancellation_dir, 2, b"%PDF-1.4\ncancellation\n%%EOF"
    )

    first = migrate_legacy_documents(
        engine, data_dir, disclaimer_dir, cancellation_dir
    )
    second = migrate_legacy_documents(
        engine, data_dir, disclaimer_dir, cancellation_dir
    )

    assert first == {"disclaimer": 1, "cancellation": 1}
    assert second == {"disclaimer": 0, "cancellation": 0}
    assert disclaimer.exists()
    assert cancellation.exists()
    rows = _attachment_rows(engine)
    assert {(row["repair_id"], row["attachment_type"]) for row in rows} == {
        (1, "disclaimer"),
        (2, "cancellation"),
    }
    for row in rows:
        stored = (
            data_dir
            / "attachments"
            / str(row["repair_id"])
            / row["stored_filename"]
        )
        assert stored.read_bytes().startswith(b"%PDF-")
        assert stored.stat().st_size == row["size"]


def test_migration_does_not_replace_healthy_unified_attachment(tmp_path):
    engine = _database()
    _add_repairs(engine, 7)
    data_dir = tmp_path / "data"
    existing_dir = data_dir / "attachments" / "7"
    existing_dir.mkdir(parents=True)
    existing = existing_dir / "current.pdf"
    existing.write_bytes(b"%PDF-1.4\ncurrent\n%%EOF")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                INSERT INTO repair_attachments (
                    repair_id, attachment_type, original_filename,
                    stored_filename, content_type, size
                ) VALUES (7, 'disclaimer', 'current.pdf', 'current.pdf',
                          'application/pdf', :size)
                """
            ),
            {"size": existing.stat().st_size},
        )
    legacy_dir = tmp_path / "legacy"
    legacy = _write_pdf(legacy_dir, 7, b"%PDF-1.4\nlegacy\n%%EOF")

    summary = migrate_legacy_documents(
        engine, data_dir, legacy_dir, tmp_path / "missing"
    )

    assert summary == {"disclaimer": 0, "cancellation": 0}
    assert existing.read_bytes() == b"%PDF-1.4\ncurrent\n%%EOF"
    assert legacy.exists()
    assert len(_attachment_rows(engine)) == 1


@pytest.mark.parametrize(
    ("repair_id", "content", "expected"),
    [
        (99, b"%PDF-1.4\norphan\n%%EOF", "No repair exists"),
        (1, b"not a PDF", "not a PDF"),
    ],
)
def test_migration_fails_without_removing_source(
    tmp_path, repair_id, content, expected
):
    engine = _database()
    _add_repairs(engine, 1)
    legacy_dir = tmp_path / "legacy"
    legacy = _write_pdf(legacy_dir, repair_id, content)

    with pytest.raises(LegacyDocumentMigrationError, match=expected):
        migrate_legacy_documents(
            engine, tmp_path / "data", legacy_dir, tmp_path / "missing"
        )

    assert legacy.exists()
    assert _attachment_rows(engine) == []


def test_database_failure_rolls_back_rows_and_is_retryable(tmp_path):
    engine = _database()
    _add_repairs(engine, 1)
    legacy_dir = tmp_path / "legacy"
    source = _write_pdf(legacy_dir, 1, b"%PDF-1.4\nretry\n%%EOF")
    data_dir = tmp_path / "data"

    def fail_insert(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().startswith("INSERT INTO repair_attachments"):
            raise RuntimeError("simulated database failure")

    sa.event.listen(engine, "before_cursor_execute", fail_insert)
    with pytest.raises(RuntimeError, match="simulated database failure"):
        migrate_legacy_documents(
            engine, data_dir, legacy_dir, tmp_path / "missing"
        )
    sa.event.remove(engine, "before_cursor_execute", fail_insert)

    assert _attachment_rows(engine) == []
    assert source.exists()
    assert len(list((data_dir / "attachments").rglob("*.pdf"))) == 1

    summary = migrate_legacy_documents(
        engine, data_dir, legacy_dir, tmp_path / "missing"
    )
    assert summary == {"disclaimer": 1, "cancellation": 0}
    assert len(_attachment_rows(engine)) == 1
    assert source.exists()


def test_main_honors_custom_legacy_directory_overrides(
    tmp_path, monkeypatch, capsys
):
    database_path = tmp_path / "migration.sqlite"
    engine = sa.create_engine(f"sqlite:///{database_path}")
    metadata = sa.MetaData()
    sa.Table("repairs", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "repair_attachments",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repair_id", sa.Integer, nullable=False),
        sa.Column("attachment_type", sa.String(50), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False, unique=True),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("uploaded_by_id", sa.Integer),
        sa.Column("template_version_id", sa.Integer),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(sa.text("INSERT INTO repairs (id) VALUES (4)"))
    engine.dispose()

    data_dir = tmp_path / "data"
    custom_dir = tmp_path / "custom-legacy"
    source = _write_pdf(custom_dir, 4, b"%PDF-1.4\ncustom\n%%EOF")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("SIGNED_PDF_STORAGE_PATH", str(custom_dir))
    monkeypatch.setenv(
        "SIGNED_CANCELLATION_STORAGE_PATH", str(tmp_path / "missing-cancellations")
    )

    from app.migrate_legacy_documents import main

    main()

    assert "1 disclaimer(s), 0 cancellation(s)" in capsys.readouterr().out
    assert source.exists()
    with sa.create_engine(f"sqlite:///{database_path}").connect() as connection:
        assert connection.execute(
            sa.text("SELECT COUNT(*) FROM repair_attachments")
        ).scalar_one() == 1
