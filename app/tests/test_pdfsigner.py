"""
Unit tests for PDFSigner.

Run from the project root:
    python -m pytest app/tests/test_pdfsigner.py -v

Or run a single test:
    python -m pytest app/tests/test_pdfsigner.py::TestPDFSignerWithFields::test_date_text_appears -v -s
"""

import base64
import datetime
import io
import sys
import unittest
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw

# Make sure the app package is importable when running from project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.imports.pdfsigner import FIELD_DATE, FIELD_NAME, FIELD_SIGNATURE, PDFSigner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PDF_SAMPLE = (
    Path(__file__).parent.parent.parent / "config" / "Disclaimer_sample.pdf"
)

TEMPLATE_PATH: Path | None = PDF_SAMPLE if PDF_SAMPLE.exists() else None


def _make_minimal_pdf(with_fields: bool = True) -> Path:
    """Create a minimal in-memory PDF with optional AcroForm text fields."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    if with_fields:
        # date: plain text field
        date_rect = fitz.Rect(100, 700, 300, 730)
        date_widget = fitz.Widget()
        date_widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        date_widget.field_name = FIELD_DATE
        date_widget.rect = date_rect
        date_widget.field_value = ""
        page.add_widget(date_widget)

        # name: plain text field
        name_rect = fitz.Rect(100, 750, 400, 780)
        name_widget = fitz.Widget()
        name_widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        name_widget.field_name = FIELD_NAME
        name_widget.rect = name_rect
        name_widget.field_value = ""
        page.add_widget(name_widget)

        # signature: push-button used as image placeholder
        sig_rect = fitz.Rect(100, 580, 400, 680)
        sig_widget = fitz.Widget()
        sig_widget.field_type = fitz.PDF_WIDGET_TYPE_BUTTON
        sig_widget.field_name = FIELD_SIGNATURE
        sig_widget.rect = sig_rect
        page.add_widget(sig_widget)

    tmp = Path(
        fitz.get_pdf_str(doc) if False else "/tmp/test_template.pdf"
    )  # noqa: F821
    path = Path(
        "/tmp/test_template_fields.pdf"
        if with_fields
        else "/tmp/test_template_plain.pdf"
    )
    doc.save(str(path))
    doc.close()
    return path


def _make_signature_b64() -> str:
    """Return a tiny base64-encoded PNG that looks like a signature squiggle."""
    img = Image.new("RGBA", (200, 60), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.line(
        [(10, 30), (50, 10), (100, 50), (150, 20), (190, 40)], fill="black", width=3
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


# ---------------------------------------------------------------------------
# Tests using a generated minimal PDF (no dependency on real template)
# ---------------------------------------------------------------------------


class TestPDFSignerWithFields(unittest.TestCase):
    """Tests using a generated PDF that has both AcroForm fields."""

    @classmethod
    def setUpClass(cls):
        cls.pdf_path = _make_minimal_pdf(with_fields=True)
        cls.signer = PDFSigner(str(cls.pdf_path))
        cls.signature = _make_signature_b64()
        cls.test_date = datetime.date(2026, 5, 14)

    def test_name_field_detected(self):
        self.assertIn(FIELD_NAME, self.signer._field_names)

    def test_name_text_appears(self):
        """Full name must appear in the rendered page text."""
        result = self.signer.get_signed_pdf(
            self.signature, self.test_date, name="Max Mustermann"
        )
        doc = fitz.open(stream=result.read(), filetype="pdf")
        text = doc.load_page(0).get_text()
        doc.close()
        self.assertIn("Max Mustermann", text, f"Name not found in PDF text:\n{text}")

    def test_name_none_does_not_crash(self):
        """Passing name=None must still produce a valid PDF."""
        result = self.signer.get_signed_pdf(self.signature, self.test_date, name=None)
        self.assertIsNotNone(result)
        data = result.read()
        self.assertTrue(data.startswith(b"%PDF"))

    def test_fields_detected(self):
        self.assertIn(FIELD_DATE, self.signer._field_names)
        self.assertIn(FIELD_SIGNATURE, self.signer._field_names)

    def test_widget_rects_stashed(self):
        self.assertIn(FIELD_DATE, self.signer._widget_rects)
        self.assertIn(FIELD_SIGNATURE, self.signer._widget_rects)

    def test_get_signed_pdf_returns_bytes(self):
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, io.BytesIO)

    def test_output_is_valid_pdf(self):
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        data = result.read()
        self.assertTrue(
            data.startswith(b"%PDF"), "Output does not start with %PDF header"
        )

    def test_date_text_appears(self):
        """The date string '14.05.2026' must appear in the rendered page text."""
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        doc = fitz.open(stream=result.read(), filetype="pdf")
        text = doc.load_page(0).get_text()
        doc.close()
        self.assertIn(
            "14.05.2026", text, f"Date not found in PDF text. Full text:\n{text}"
        )

    def test_date_string_input(self):
        """Accept date as ISO string '2026-05-14'."""
        result = self.signer.get_signed_pdf(self.signature, "2026-05-14")
        doc = fitz.open(stream=result.read(), filetype="pdf")
        text = doc.load_page(0).get_text()
        doc.close()
        self.assertIn("14.05.2026", text)

    def test_date_datetime_input(self):
        """Accept date as datetime object."""
        result = self.signer.get_signed_pdf(
            self.signature, datetime.datetime(2026, 5, 14, 10, 30)
        )
        doc = fitz.open(stream=result.read(), filetype="pdf")
        text = doc.load_page(0).get_text()
        doc.close()
        self.assertIn("14.05.2026", text)

    def test_signature_image_embedded(self):
        """The output PDF must contain at least one embedded image."""
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        doc = fitz.open(stream=result.read(), filetype="pdf")
        images = doc.load_page(0).get_images(full=True)
        doc.close()
        self.assertGreater(len(images), 0, "No images found in signed PDF")

    def test_invalid_signature_raises(self):
        """Malformed base64 signature must not crash silently — get_signed_pdf returns None."""
        result = self.signer.get_signed_pdf(
            "data:image/png;base64,NOT_VALID_BASE64!!!!", self.test_date
        )
        self.assertIsNone(result)


class TestPDFSignerWithoutFields(unittest.TestCase):
    """Tests using a plain PDF without AcroForm fields (pixel-offset fallback path)."""

    @classmethod
    def setUpClass(cls):
        cls.pdf_path = _make_minimal_pdf(with_fields=False)
        cls.signer = PDFSigner(str(cls.pdf_path))
        cls.signature = _make_signature_b64()
        cls.test_date = datetime.date(2026, 5, 14)

    def test_no_fields_detected(self):
        self.assertNotIn(FIELD_DATE, self.signer._field_names)
        self.assertNotIn(FIELD_SIGNATURE, self.signer._field_names)

    def test_get_signed_pdf_still_returns_pdf(self):
        """Even without fields the PDF is returned (fields simply skipped)."""
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        self.assertIsNotNone(result)
        data = result.read()
        self.assertTrue(data.startswith(b"%PDF"))


class TestPDFSignerMissingFile(unittest.TestCase):
    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            PDFSigner("/nonexistent/path/to/template.pdf")


# ---------------------------------------------------------------------------
# Optional: tests against the real Disclaimer_sample.pdf template
# ---------------------------------------------------------------------------


@unittest.skipUnless(
    TEMPLATE_PATH is not None, f"Real template not found at {PDF_SAMPLE}"
)
class TestRealTemplate(unittest.TestCase):
    """Integration tests against the actual PDF template.

    These tell you immediately whether the real file has the expected fields
    and whether the output renders correctly.
    """

    @classmethod
    def setUpClass(cls):
        cls.signer = PDFSigner(str(TEMPLATE_PATH))
        cls.signature = _make_signature_b64()
        cls.test_date = datetime.date(2026, 5, 14)

    def test_date_field_present(self):
        self.assertIn(
            FIELD_DATE,
            self.signer._field_names,
            f"'date' field missing. Fields found: {self.signer._field_names}",
        )

    def test_signature_field_present(self):
        self.assertIn(
            FIELD_SIGNATURE,
            self.signer._field_names,
            f"'signature' field missing. Fields found: {self.signer._field_names}",
        )

    def test_all_detected_fields(self):
        """Print all fields for quick diagnostics (always passes)."""
        print(f"\nReal template fields: {self.signer._field_names}")
        print(f"Widget rects: {self.signer._widget_rects}")

    def test_signed_pdf_date_rendered(self):
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        self.assertIsNotNone(result, "get_signed_pdf returned None")
        doc = fitz.open(stream=result.read(), filetype="pdf")
        text = doc.load_page(0).get_text()
        doc.close()
        self.assertIn("14.05.2026", text, f"Date not in PDF. Text found:\n{text}")

    def test_signed_pdf_has_image(self):
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        doc = fitz.open(stream=result.read(), filetype="pdf")
        images = doc.load_page(0).get_images(full=True)
        doc.close()
        self.assertGreater(len(images), 0, "No signature image in signed PDF")

    def test_save_output_file(self):
        """Write the signed PDF to /tmp/signed_test.pdf for visual inspection."""
        result = self.signer.get_signed_pdf(self.signature, self.test_date)
        out = Path("/tmp/signed_test.pdf")
        out.write_bytes(result.read())
        print(f"\nSigned PDF saved to {out} — open it to check visually")


if __name__ == "__main__":
    unittest.main(verbosity=2)
