"""
Label printing service for generating and printing QR code labels on a SLP 650 label printer.
"""

import logging
import os
import subprocess

import qrcode
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# SLP 650 native resolution: 300 DPI, label size 51mm x 28mm = 602 x 330 pixels
LABEL_WIDTH = 602
LABEL_HEIGHT = 330

_FONT_PATH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _load_fonts():
    try:
        return (
            ImageFont.truetype(_FONT_PATH_BOLD, 38),
            ImageFont.truetype(_FONT_PATH, 27),
            ImageFont.truetype(_FONT_PATH, 25),
        )
    except OSError:
        default = ImageFont.load_default()
        return default, default, default


def generate_label_image(
    repair_data: dict,
    app_url: str = "",
    org_name: str = "Repair Café",
    org_website: str = "",
) -> Image.Image:
    """
    Generate a label image for the SLP 650 printer.

    Args:
        repair_data: Dict with repair fields (id, qr_token, datum, vorname, nachname, geraet_art).
        app_url: Base URL of the application used for the QR code link (e.g. "https://repaircafe.example.org").
        org_name: Organisation name printed at the bottom of the label.
        org_website: Organisation website printed at the bottom of the label (can differ from app_url).

    Returns:
        PIL Image object ready for printing.
    """
    font_large, font_medium, font_small = _load_fonts()

    img = Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    # Date — top left
    datum = repair_data.get("datum", "")
    if datum:
        # Shorten to date only if it's a full ISO datetime string
        datum_display = str(datum)[:10]
        draw.text((0, 0), datum_display, fill="black", font=font_medium)

    # Name — left side, below date
    name = f"{repair_data.get('vorname', '')} {repair_data.get('nachname', '')}".strip()
    lines: list[str] = []
    if name:
        max_text_width = LABEL_WIDTH - 237  # leave room for the QR code on the right
        words = name.split()
        current_line: list[str] = []
        for word in words:
            test = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test, font=font_large)
            if bbox[2] - bbox[0] <= max_text_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        y = 52
        for line in lines[:3]:
            draw.text((0, y), line, fill="black", font=font_large)
            y += 44

    # Device type — below name
    device = repair_data.get("geraet_art", "")
    if device:
        device_y = 59 + len(lines[:3]) * 44 if name else 104
        draw.text((0, device_y), device[:25], fill="black", font=font_medium)

    # QR code — right side
    qr_token = repair_data.get("qr_token", "")
    qr_url = f"{app_url.rstrip('/')}/edit/{qr_token}" if qr_token else "unknown"
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((207, 207))
    qr_x = LABEL_WIDTH - 207
    img.paste(qr_img, (qr_x, 0))

    # Repair ID — centered below QR code
    id_text = f"#{repair_data.get('id', '?')}"
    bbox = draw.textbbox((0, 0), id_text, font=font_large)
    id_x = qr_x + (207 - (bbox[2] - bbox[0])) // 2
    draw.text((id_x, 251), id_text, fill="black", font=font_large)

    # Logo — bottom left
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "static", "logo.jpg"
    )
    try:
        logo = Image.open(logo_path).resize((95, 95))
        img.paste(logo, (0, LABEL_HEIGHT - 95))
        if org_name:
            draw.text((102, LABEL_HEIGHT - 80), org_name, fill="black", font=font_small)
        if org_website:
            draw.text(
                (102, LABEL_HEIGHT - 38), org_website, fill="black", font=font_small
            )
    except Exception as exc:
        logger.warning("Could not load logo for label: %s", exc)

    return img


class LabelService:
    """Service for printing QR code labels via CUPS (Unix socket)."""

    def __init__(self, printer_name: str = "SLP650"):
        self.printer_name = printer_name

    def print_label(
        self,
        repair_data: dict,
        app_url: str = "",
        org_name: str = "Repair Café",
        org_website: str = "",
    ) -> dict:
        """
        Generate and print a label for the given repair via CUPS.

        Returns a dict with keys ``reply`` ("done" or "error") and ``message``/``error``.
        """
        repair_id = repair_data.get("id", "?")
        label_image = generate_label_image(
            repair_data, app_url=app_url, org_name=org_name, org_website=org_website
        )
        return self._print_cups(label_image, repair_id)

    def _print_cups(self, image: Image.Image, repair_id) -> dict:
        tmp = f"/tmp/label_{repair_id}.png"
        try:
            image.save(tmp, format="PNG")
            proc = subprocess.Popen(
                ["lp", "-d", self.printer_name, tmp],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(stderr.decode().strip())
            logger.info("Label printed for repair %s on %s", repair_id, self.printer_name)
            return {"reply": "done", "message": f"Label printed for repair #{repair_id}"}
        except FileNotFoundError:
            return {"reply": "error", "error": "lp not found — install cups-client: sudo apt-get install cups-client"}
        except Exception as exc:
            return {"reply": "error", "error": str(exc)}
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
