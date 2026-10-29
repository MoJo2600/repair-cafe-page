"""
PDF service for generating and signing disclaimer and cancellation PDFs.
"""

import os
from pathlib import Path

from app.imports.pdfsigner import PDFSigner

_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()


class PDFService:
    """Service for handling template-based PDF signing and storage operations."""

    def __init__(
        self,
        pdf_path: str | Path | None = None,
        storage_dir: str | Path | None = None,
        data_dir: str | Path | None = None,
        config_dir: str | Path | None = None,
        active_filename: str = "disclaimer.pdf",
        sample_filename: str = "Disclaimer_sample.pdf",
        storage_subdir: str = "signed_disclaimers",
    ):
        resolved_data_dir = Path(
            data_dir or os.environ.get("DATA_DIR", str(_PROJECT_ROOT / "data"))
        ).resolve()
        resolved_config_dir = Path(
            config_dir or os.environ.get("CONFIG_DIR", str(_PROJECT_ROOT / "config"))
        ).resolve()

        self.data_dir = resolved_data_dir
        self.config_dir = resolved_config_dir
        self.active_template_path = resolved_data_dir / active_filename
        self.sample_template_path = resolved_config_dir / sample_filename

        if pdf_path is None:
            if active_filename == "disclaimer.pdf" and os.environ.get("PDF_PATH"):
                pdf_path = os.environ["PDF_PATH"]
            elif self.active_template_path.exists():
                pdf_path = str(self.active_template_path)
            else:
                pdf_path = str(self.sample_template_path)

        if storage_dir is None:
            if storage_subdir == "signed_disclaimers" and os.environ.get(
                "SIGNED_PDF_STORAGE_PATH"
            ):
                storage_dir = os.environ["SIGNED_PDF_STORAGE_PATH"]
            elif storage_subdir == "signed_cancellations" and os.environ.get(
                "SIGNED_CANCELLATION_STORAGE_PATH"
            ):
                storage_dir = os.environ["SIGNED_CANCELLATION_STORAGE_PATH"]
            else:
                storage_dir = str(resolved_data_dir / storage_subdir)

        self.pdf_path = str(pdf_path)
        self.storage_dir = Path(storage_dir)
        self._signer: PDFSigner | None = None

    @property
    def signer(self) -> PDFSigner:
        """Get or initialize the PDFSigner instance (lazy loading)."""
        if self._signer is None:
            # Re-check whether an active template now exists in data_dir
            if (
                not Path(self.pdf_path).exists()
                and self.active_template_path.exists()
            ):
                self.pdf_path = str(self.active_template_path)
            self._signer = PDFSigner(self.pdf_path)
        return self._signer

    def reload(self, new_path: str | Path) -> None:
        """Hot-swap the PDF template. Clears the cached signer so the next
        call to ``signer`` picks up the new file."""
        self.pdf_path = str(new_path)
        self._signer = None

    def get_signed_pdf(self, signature_data, date, name: str | None = None):
        """
        Return a signed PDF as a BytesIO stream without persisting it.
        """
        return self.signer.get_signed_pdf(signature_data, date, name=name)

    def save_signed_pdf(
        self,
        repair_id: int,
        signature_data: str,
        date,
        name: str | None = None,
    ) -> Path | None:
        """
        Generate a signed PDF for the repair and persist it to
        <storage_dir>/<repair_id>.pdf.

        Returns the Path of the saved file, or None if generation failed.
        """
        pdf_stream = self.signer.get_signed_pdf(signature_data, date, name=name)
        if pdf_stream is None:
            return None

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        dest = self.storage_dir / f"{repair_id}.pdf"
        dest.write_bytes(pdf_stream.read())
        return dest

    def store_uploaded_pdf(self, repair_id: int, pdf_bytes: bytes) -> Path:
        """
        Persist raw PDF bytes for the given repair.
        Returns the Path of the saved file.
        """
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        dest = self.storage_dir / f"{repair_id}.pdf"
        dest.write_bytes(pdf_bytes)
        return dest

    def get_stored_pdf_path(self, repair_id: int) -> Path | None:
        """
        Return the Path to the stored signed PDF, or None if it does not exist yet.
        """
        path = self.storage_dir / f"{repair_id}.pdf"
        return path if path.exists() else None

    def delete_stored_pdf(self, repair_id: int) -> None:
        """Delete the stored signed PDF for the given repair if present."""
        path = self.storage_dir / f"{repair_id}.pdf"
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
