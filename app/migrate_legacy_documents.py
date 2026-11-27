"""Copy legacy signed PDFs into the unified repair attachment store."""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path

import sqlalchemy as sa


class LegacyDocumentMigrationError(RuntimeError):
    """Raised when legacy documents cannot be migrated safely."""


_PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _database_url() -> str:
    if database_url := os.environ.get("DATABASE_URL"):
        return database_url
    host = os.environ.get("MYSQL_HOST", "db")
    database = os.environ.get("MYSQL_DATABASE", "repaircafepage")
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "mariadb")
    port = os.environ.get("MYSQL_PORT", "3306")
    return (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    )


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_pdf(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open("rb") as pdf:
        return pdf.read(5).startswith(b"%PDF-")


def _copy_verified(source: Path, destination: Path, digest: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if _file_digest(destination) != digest:
            raise LegacyDocumentMigrationError(
                f"Existing destination has unexpected content: {destination}"
            )
        return

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            with source.open("rb") as source_file:
                shutil.copyfileobj(source_file, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
        if _file_digest(temporary_path) != digest:
            raise LegacyDocumentMigrationError(
                f"Source changed while it was being copied: {source}"
            )
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_source(source: Path) -> tuple[int, int, str]:
    try:
        repair_id = int(source.stem)
    except ValueError as exc:
        raise LegacyDocumentMigrationError(
            f"Legacy PDF filename does not contain a repair ID: {source}"
        ) from exc
    if not _is_pdf(source):
        raise LegacyDocumentMigrationError(
            f"Legacy file is not a PDF: {source}"
        )
    size = source.stat().st_size
    return repair_id, size, _file_digest(source)


def _migrate_document(
    connection,
    data_dir: Path,
    attachment_type: str,
    source: Path,
) -> bool:
    repair_id, size, digest = _validate_source(source)
    repair_exists = connection.execute(
        sa.text("SELECT id FROM repairs WHERE id = :repair_id"),
        {"repair_id": repair_id},
    ).scalar_one_or_none()
    if repair_exists is None:
        raise LegacyDocumentMigrationError(
            f"No repair exists for legacy {attachment_type} PDF: {source}"
        )

    attachment_dir = data_dir / "attachments" / str(repair_id)
    attachments = connection.execute(
        sa.text(
            """
            SELECT id, stored_filename
            FROM repair_attachments
            WHERE repair_id = :repair_id AND attachment_type = :attachment_type
            ORDER BY id DESC
            """
        ),
        {"repair_id": repair_id, "attachment_type": attachment_type},
    ).mappings().all()
    if attachments:
        current_path = attachment_dir / attachments[0]["stored_filename"]
        if _is_pdf(current_path):
            return False

    filename = (
        f"legacy-{attachment_type}-{repair_id}-{digest[:16]}.pdf"
    )
    destination = attachment_dir / filename
    _copy_verified(source, destination, digest)

    values = {
        "repair_id": repair_id,
        "attachment_type": attachment_type,
        "original_filename": source.name,
        "stored_filename": filename,
        "content_type": "application/pdf",
        "size": size,
    }
    if attachments:
        values["id"] = attachments[0]["id"]
        connection.execute(
            sa.text(
                """
                UPDATE repair_attachments
                SET original_filename = :original_filename,
                    stored_filename = :stored_filename,
                    content_type = :content_type,
                    size = :size,
                    uploaded_by_id = NULL,
                    template_version_id = NULL
                WHERE id = :id
                """
            ),
            values,
        )
    else:
        connection.execute(
            sa.text(
                """
                INSERT INTO repair_attachments (
                    repair_id, attachment_type, original_filename,
                    stored_filename, content_type, size,
                    uploaded_by_id, template_version_id
                ) VALUES (
                    :repair_id, :attachment_type, :original_filename,
                    :stored_filename, :content_type, :size, NULL, NULL
                )
                """
            ),
            values,
        )
    return True


def migrate_legacy_documents(
    engine: sa.Engine,
    data_dir: Path,
    signed_pdf_dir: Path,
    signed_cancellation_dir: Path,
) -> dict[str, int]:
    """Copy all legacy PDFs and record them as unified attachments."""
    summary = {"disclaimer": 0, "cancellation": 0}
    sources = (
        ("disclaimer", signed_pdf_dir),
        ("cancellation", signed_cancellation_dir),
    )
    with engine.begin() as connection:
        for attachment_type, source_dir in sources:
            if not source_dir.is_dir():
                continue
            for source in sorted(source_dir.glob("*.pdf")):
                if _migrate_document(
                    connection, data_dir, attachment_type, source
                ):
                    summary[attachment_type] += 1
    return summary


def main() -> None:
    data_dir = Path(
        os.environ.get("DATA_DIR", str(_PROJECT_ROOT / "data"))
    ).resolve()
    signed_pdf_dir = Path(
        os.environ.get("SIGNED_PDF_STORAGE_PATH")
        or str(data_dir / "signed_disclaimers")
    ).resolve()
    signed_cancellation_dir = Path(
        os.environ.get("SIGNED_CANCELLATION_STORAGE_PATH")
        or str(data_dir / "signed_cancellations")
    ).resolve()
    engine = sa.create_engine(_database_url())
    try:
        summary = migrate_legacy_documents(
            engine,
            data_dir,
            signed_pdf_dir,
            signed_cancellation_dir,
        )
    finally:
        engine.dispose()
    print(
        "Legacy document migration complete: "
        f"{summary['disclaimer']} disclaimer(s), "
        f"{summary['cancellation']} cancellation(s)"
    )


if __name__ == "__main__":
    main()
