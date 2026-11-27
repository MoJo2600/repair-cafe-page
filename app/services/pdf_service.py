"""PDF template and signing service."""

import os
from pathlib import Path

from app.imports.pdfsigner import PDFSigner

_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()


class PDFService:
    """Service for handling template-based PDF signing and storage operations."""

    def __init__(
        self,
        pdf_path: str | Path | None = None,
        data_dir: str | Path | None = None,
        config_dir: str | Path | None = None,
        active_filename: str = "disclaimer.pdf",
        sample_filename: str = "Disclaimer_sample.pdf",
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

        self.pdf_path = str(pdf_path)
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
