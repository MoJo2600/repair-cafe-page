import base64
import datetime
import io
import logging

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)

# Named AcroForm field names expected in the PDF template.
# Add a text widget named "date" and an image/signature widget named "signature"
# in the template (e.g. via LibreOffice Draw > Insert > Header/Footer or Form Controls)
# to use positional field placement instead of hardcoded pixel offsets.
FIELD_SIGNATURE = "signature"
FIELD_DATE = "date"
FIELD_NAME = "name"


class PDFSigner:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        try:
            with open(pdf_path, "rb") as f:
                pass
        except FileNotFoundError:
            error_msg = f"PDF file not found at path: {pdf_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Detect whether the template has named AcroForm fields
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)

        # Log every widget found for diagnostics
        all_widgets = list(page.widgets()) if page.widgets() else []
        for w in all_widgets:
            logger.debug(
                "PDFSigner: widget — name=%r  type=%s  rect=%s",
                w.field_name,  # type: ignore[union-attr]
                w.field_type_string,  # type: ignore[union-attr]
                w.rect,  # type: ignore[union-attr]
            )
        # Also log raw annotations (catches digital-signature annots PyMuPDF may not list as widgets)
        for a in page.annots():
            logger.debug("PDFSigner: annot — type=%s  info=%s", a.type, a.info)

        self._field_names = {
            w.field_name for w in all_widgets
        }  # type: ignore[union-attr]
        # Stash widget rects for positional fallback when field_value doesn't render
        self._widget_rects: dict[str, fitz.Rect] = {
            w.field_name: w.rect  # type: ignore[union-attr]
            for w in all_widgets
            if w.field_name  # type: ignore[union-attr]
        }
        logger.debug("PDFSigner: Detected AcroForm fields: %s", self._field_names)
        doc.close()

        if FIELD_SIGNATURE in self._field_names or FIELD_DATE in self._field_names:
            logger.info("PDFSigner: using AcroForm fields %s", self._field_names)
        else:
            logger.warning(
                "PDFSigner: no AcroForm fields found, using fixed pixel positions"
            )

        logger.info("PDFSigner initialized with PDF path: %s", pdf_path)

    # ------------------------------------------------------------------
    # AcroForm-based placement (preferred when template has named fields)
    # ------------------------------------------------------------------

    def _fill_signature_field(self, page, signature):
        """Place signature image directly into the widget rect on the page."""
        rect = self._widget_rects.get(FIELD_SIGNATURE)
        if rect is None:
            logger.warning("PDFSigner: 'signature' widget rect not found")
            return
        signature_image_data = base64.b64decode(signature.split(",")[1])
        img_pixmap = fitz.Pixmap(signature_image_data)
        page.insert_image(rect, pixmap=img_pixmap, keep_proportion=True)
        logger.debug("PDFSigner: signature image inserted at %s", rect)

        # Cover the widget border by drawing the image over the whole rect;
        # no need to mutate widget flags (PDF_FLD_NO_EXPORT is not available in all PyMuPDF versions)

    def _fill_date_field(self, page, date):
        """Draw date text directly onto the page inside the widget rect."""
        if isinstance(date, (datetime.date, datetime.datetime)):
            date_str = date.strftime("%d.%m.%Y")
        else:
            parts = str(date).split("-")
            date_str = (
                f"{parts[2]}.{parts[1]}.{parts[0]}" if len(parts) == 3 else str(date)
            )
        self._fill_text_field(page, FIELD_DATE, date_str)

    def _fill_text_field(self, page, field_name: str, text: str):
        """Generic helper: draw text directly onto the page inside a named widget rect."""
        rect = self._widget_rects.get(field_name)
        if rect is None:
            logger.warning("PDFSigner: '%s' widget rect not found", field_name)
            return
        page.draw_rect(rect, color=None, fill=(1, 1, 1))
        font_size = max(8, rect.height * 0.55)
        # insert_text baseline = y coordinate; anchor to bottom-left of the widget
        # with a small inset so descenders don't get clipped
        text_point = fitz.Point(rect.x0 + 2, rect.y1 - 2)
        page.insert_text(text_point, text, fontsize=font_size, color=(0, 0, 0))
        logger.debug(
            "PDFSigner: field '%s' filled with %r at %s", field_name, text, rect
        )

    def get_signed_pdf(self, signature, date, name: str | None = None):
        try:
            doc = fitz.open(self.pdf_path)
            page = doc.load_page(0)

            if FIELD_SIGNATURE in self._field_names:
                self._fill_signature_field(page, signature)

            if FIELD_DATE in self._field_names:
                self._fill_date_field(page, date)

            if name and FIELD_NAME in self._field_names:
                self._fill_text_field(page, FIELD_NAME, name)

            output_pdf_stream = io.BytesIO()
            doc.save(output_pdf_stream, incremental=False, deflate=True, garbage=3)
            doc.close()
            output_pdf_stream.seek(0)
            return output_pdf_stream
        except Exception as e:
            logger.error("Error in get_signed_pdf: %s", e, exc_info=True)
            return None
