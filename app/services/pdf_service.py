"""
PDF service for generating and signing disclaimer PDFs.
"""

import os
from pathlib import Path

from app.imports.pdfsigner import PDFSigner

_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Active disclaimer stored in data/ (written by seed or admin upload).
# Falls back to the bundled sample when no custom file exists.
_DISCLAIMER_ACTIVE = _PROJECT_ROOT / "data" / "disclaimer.pdf"
_DISCLAIMER_SAMPLE = _PROJECT_ROOT / "config" / "Disclaimer_sample.pdf"


class PDFService:
    """Service for handling PDF operations."""

    def __init__(self, pdf_path=None, storage_dir=None):
        if pdf_path is None:
            pdf_path = os.environ.get("PDF_PATH") or (
                str(_DISCLAIMER_ACTIVE)
                if _DISCLAIMER_ACTIVE.exists()
                else str(_DISCLAIMER_SAMPLE)
            )
        if storage_dir is None:
            storage_dir = os.environ.get(
                "SIGNED_PDF_STORAGE_PATH",
                str(_PROJECT_ROOT / "data" / "signed_disclaimers"),
            )

        self.pdf_path = pdf_path
        self.storage_dir = Path(storage_dir)
        self._signer = None

    @property
    def signer(self):
        """Get or initialize the PDFSigner instance (lazy loading)."""
        if self._signer is None:
            self._signer = PDFSigner(self.pdf_path)
        return self._signer

    def reload(self, new_path: str) -> None:
        """Hot-swap the PDF template. Clears the cached signer so the next
        call to ``signer`` picks up the new file."""
        self.pdf_path = new_path
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
        Persist raw PDF bytes as the disclaimer for the given repair.
        Returns the Path of the saved file.
        """
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        dest = self.storage_dir / f"{repair_id}.pdf"
        dest.write_bytes(pdf_bytes)
        return dest

    def get_stored_pdf_path(self, repair_id: int) -> Path | None:
        """
        Return the Path to the stored signed disclaimer PDF, or None if it
        does not exist yet.
        """
        path = self.storage_dir / f"{repair_id}.pdf"
        return path if path.exists() else None
