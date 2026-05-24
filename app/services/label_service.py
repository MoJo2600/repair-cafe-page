"""
Label printing service for generating and printing QR code labels on a SLP 650 label printer.
"""
import logging
import os
import subprocess
from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# SLP 650 native resolution: 203 DPI, label size 51mm x 28mm = 406 x 224 pixels
LABEL_WIDTH = 406
LABEL_HEIGHT = 224

_FONT_PATH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _load_fonts():
    try:
        return (
            ImageFont.truetype(_FONT_PATH_BOLD, 26),
            ImageFont.truetype(_FONT_PATH, 18),
            ImageFont.truetype(_FONT_PATH, 14),
        )
    except OSError:
        default = ImageFont.load_default()
        return default, default, default


def generate_label_image(repair_data: dict, base_url: str = "") -> Image.Image:
    """
    Generate a label image for the SLP 650 printer.

    Args:
        repair_data: Dict with repair fields (id, qr_token, datum, vorname, nachname, geraet_art).
        base_url: Base URL used as the root for the QR code link (e.g. "http://repaircafe/").

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
        max_text_width = LABEL_WIDTH - 160  # leave room for the QR code on the right
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

        y = 35
        for line in lines[:3]:
            draw.text((0, y), line, fill="black", font=font_large)
            y += 30

    # Device type — below name
    device = repair_data.get("geraet_art", "")
    if device:
        device_y = 40 + len(lines[:3]) * 30 if name else 70
        draw.text((0, device_y), device[:25], fill="black", font=font_medium)

    # QR code — right side
    qr_token = repair_data.get("qr_token", "")
    qr_url = f"{base_url.rstrip('/')}/edit/{qr_token}" if qr_token else "unknown"
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((140, 140))
    qr_x = LABEL_WIDTH - 140
    img.paste(qr_img, (qr_x, 0))

    # Repair ID — centered below QR code
    id_text = f"#{repair_data.get('id', '?')}"
    bbox = draw.textbbox((0, 0), id_text, font=font_large)
    id_x = qr_x + (140 - (bbox[2] - bbox[0])) // 2
    draw.text((id_x, 170), id_text, fill="black", font=font_large)

    # Logo — bottom left
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "logo.jpg")
    try:
        logo = Image.open(logo_path).resize((64, 64))
        img.paste(logo, (0, LABEL_HEIGHT - 64))
        draw.text((69, LABEL_HEIGHT - 38), "Tangrintel Repair Café e.V.", fill="black", font=font_small)
        draw.text((69, LABEL_HEIGHT - 18), "tangrintel-repaircafe.de", fill="black", font=font_small)
    except Exception as exc:
        logger.warning("Could not load logo for label: %s", exc)

    return img


def _escpos_commands(image: Image.Image) -> bytes:
    """Generate ESC/POS byte stream for the given PIL image."""
    from escpos import printer as escpos_printer

    output = BytesIO()
    try:
        p = escpos_printer.File(output)
        p._raw(b"\x1B\x40")  # ESC @ — initialize
        p.image(image)
        p.text("\n\n")
        p._raw(b"\x1B\x69")  # ESC i — partial cut
        return output.getvalue()
    except Exception as exc:
        logger.error("Error generating ESC/POS commands: %s", exc)
        return b"\x1B\x40"  # fall back to init-only


class LabelService:
    """Service for printing QR code labels."""

    def __init__(
        self,
        default_device: str = "/dev/usb/lp0",
        default_method: str = "file",
        default_cups_name: str = "SLP650",
        default_network_ip: str | None = None,
        default_network_port: int = 9100,
    ):
        self.default_device = default_device
        self.default_method = default_method
        self.default_cups_name = default_cups_name
        self.default_network_ip = default_network_ip
        self.default_network_port = default_network_port

    def print_label(
        self,
        repair_data: dict,
        base_url: str = "",
        method: str | None = None,
        printer_device: str | None = None,
        printer_name: str | None = None,
        printer_ip: str | None = None,
        printer_port: int | None = None,
    ) -> dict:
        """
        Generate and print a label for the given repair.

        Returns a dict with keys ``reply`` ("done" or "error") and ``message``/``error``.
        """
        repair_id = repair_data.get("id", "?")
        method = method or self.default_method
        printer_device = printer_device or self.default_device
        printer_name = printer_name or self.default_cups_name
        printer_ip = printer_ip or self.default_network_ip
        printer_port = printer_port or self.default_network_port

        label_image = generate_label_image(repair_data, base_url=base_url)

        if method in ("usb", "file"):
            return self._print_file(label_image, printer_device, repair_id)
        elif method == "cups":
            return self._print_cups(label_image, printer_name, repair_id)
        elif method == "network":
            if not printer_ip:
                return {"reply": "error", "error": "Printer IP address required for network printing"}
            return self._print_network(label_image, printer_ip, printer_port, repair_id)
        else:
            return {"reply": "error", "error": f"Unknown print method: {method}"}

    # ------------------------------------------------------------------
    # Private printing helpers
    # ------------------------------------------------------------------

    def _print_file(self, image: Image.Image, device: str, repair_id) -> dict:
        try:
            commands = _escpos_commands(image)
            with open(device, "wb") as f:
                f.write(commands)
            logger.info("Label printed for repair %s via USB/file (%s)", repair_id, device)
            return {"reply": "done", "message": f"Label printed for repair #{repair_id}"}
        except PermissionError:
            return {
                "reply": "error",
                "error": f"Permission denied: {device}. Run: sudo chmod 666 {device}",
            }
        except FileNotFoundError:
            return {
                "reply": "error",
                "error": f"Printer device not found: {device}. Check USB connection.",
            }

    def _print_cups(self, image: Image.Image, printer_name: str, repair_id) -> dict:
        tmp = f"/tmp/label_{repair_id}.png"
        try:
            image.save(tmp, format="PNG")
            proc = subprocess.Popen(
                ["lpr", "-P", printer_name, tmp],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"lpr failed: {stderr.decode()}")
            logger.info("Label printed for repair %s via CUPS (%s)", repair_id, printer_name)
            return {"reply": "done", "message": f"Label printed for repair #{repair_id}"}
        except FileNotFoundError:
            return {"reply": "error", "error": "CUPS not installed. Install with: sudo apt-get install cups"}
        except Exception as exc:
            return {"reply": "error", "error": str(exc)}
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass

    def _print_network(self, image: Image.Image, ip: str, port: int, repair_id) -> dict:
        import socket

        try:
            commands = _escpos_commands(image)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.sendall(commands)
            sock.close()
            logger.info("Label printed for repair %s via network (%s:%s)", repair_id, ip, port)
            return {"reply": "done", "message": f"Label printed for repair #{repair_id}"}
        except Exception as exc:
            return {"reply": "error", "error": f"Network print failed: {exc}"}
