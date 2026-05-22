"""
Generate a VDE Prüfprotokoll (DIN VDE 0701/0702) PDF from a VdeTest + Repair.

Returns raw PDF bytes — no template file required.
"""

import io
from datetime import datetime, timezone

import fitz  # PyMuPDF

# DejaVu Sans – free font, ships with Debian; full Unicode (✓ ✕ ≤ ≥ Umlauts…)
_FONT_DIR = "/usr/share/fonts/truetype/dejavu"
_FONT_REGULAR = f"{_FONT_DIR}/DejaVuSans.ttf"
_FONT_BOLD = f"{_FONT_DIR}/DejaVuSans-Bold.ttf"

# Short aliases used as PDF resource names
F_REGULAR = "dvu"
F_BOLD = "dvub"


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COL_DARK = (0.15, 0.15, 0.15)
COL_SECTION_BG = (0.88, 0.92, 0.96)
COL_SECTION_TEXT = (0.1, 0.2, 0.4)
COL_PASS_BG = (0.18, 0.65, 0.35)
COL_FAIL_BG = (0.85, 0.18, 0.18)
COL_RESULT_TEXT = (1.0, 1.0, 1.0)
COL_BORDER = (0.6, 0.6, 0.6)
COL_IO = (0.2, 0.6, 0.2)
COL_NIO = (0.8, 0.1, 0.1)
COL_NA = (0.5, 0.5, 0.5)
COL_LIGHT_LINE = (0.8, 0.8, 0.8)


# ---------------------------------------------------------------------------
# Low-level drawing helpers
# ---------------------------------------------------------------------------


def _filled_rect(page, rect, fill_color, border_color=None):
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(fill=fill_color, color=border_color, width=0.5 if border_color else 0)
    shape.commit()


def _line(page, p1, p2, color=COL_LIGHT_LINE, width=0.5):
    shape = page.new_shape()
    shape.draw_line(p1, p2)
    shape.finish(color=color, width=width)
    shape.commit()


def _text(page, point, text, fontsize=9, color=COL_DARK, fontname=F_REGULAR, align=0):
    page.insert_text(point, text, fontsize=fontsize, color=color, fontname=fontname)


def _section_header(page, y, title, left=40, right=555):
    rect = fitz.Rect(left, y, right, y + 16)
    _filled_rect(page, rect, COL_SECTION_BG)
    page.insert_text(
        (left + 6, y + 12), title, fontsize=9, color=COL_SECTION_TEXT, fontname=F_BOLD
    )
    return y + 20  # next y


def _field_row(page, y, label, value, lx=40, vx=220, right=555, row_h=17):
    """Draw one label/value row; returns next y."""
    page.insert_text(
        (lx, y + 12), label, fontsize=8, color=(0.4, 0.4, 0.4), fontname=F_REGULAR
    )
    page.insert_text(
        (vx, y + 12), value or "—", fontsize=9, color=COL_DARK, fontname=F_REGULAR
    )
    _line(page, (lx, y + row_h), (right, y + row_h))
    return y + row_h


def _check_symbol(page, x, y, state, label, box_size=10):
    """
    Draw a labelled checkbox symbol.
    state: True  → green tick (i.O. / bestanden)
           False → red cross (n.i.O. / nicht bestanden)
           None  → grey dash (not checked / n.a.)
    """
    rect = fitz.Rect(x, y + 1, x + box_size, y + 1 + box_size)
    if state is True:
        _filled_rect(page, rect, COL_IO, COL_IO)
        page.insert_text(
            (x + 1, y + 10), "\u2713", fontsize=8, color=(1, 1, 1), fontname=F_BOLD
        )
    elif state is False:
        _filled_rect(page, rect, COL_NIO, COL_NIO)
        page.insert_text(
            (x + 1, y + 10), "\u2715", fontsize=8, color=(1, 1, 1), fontname=F_BOLD
        )
    else:
        _filled_rect(page, rect, (0.85, 0.85, 0.85), COL_BORDER)
        page.insert_text((x + 3, y + 10), "\u2013", fontsize=8, color=COL_NA)

    page.insert_text(
        (x + box_size + 4, y + 10),
        label,
        fontsize=8,
        color=COL_DARK,
        fontname=F_REGULAR,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_vde_pdf(vde_test, repair) -> bytes:
    """
    Build and return a PDF Prüfprotokoll for *vde_test* / *repair*.

    Parameters
    ----------
    vde_test : VdeTest model instance
    repair   : Repair model instance (for Laufzettel-Nr and device info)
    """

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Register fonts once so all insert_text calls on this page can use them
    page.insert_font(fontname=F_REGULAR, fontfile=_FONT_REGULAR)
    page.insert_font(fontname=F_BOLD, fontfile=_FONT_BOLD)

    LEFT = 40
    RIGHT = 555
    WIDTH = RIGHT - LEFT
    y = 30

    # -----------------------------------------------------------------------
    # Page title
    # -----------------------------------------------------------------------
    page.insert_text(
        (LEFT, y + 14),
        "Prüfprotokoll – Elektrische Sicherheitsprüfung",
        fontsize=14,
        color=COL_SECTION_TEXT,
        fontname=F_BOLD,
    )
    y += 20
    page.insert_text(
        (LEFT, y + 11),
        "gemäß DIN VDE 0701-0702",
        fontsize=9,
        color=(0.5, 0.5, 0.5),
        fontname=F_REGULAR,
    )
    y += 16
    _line(page, (LEFT, y), (RIGHT, y), color=(0.3, 0.3, 0.3), width=1.0)
    y += 10

    # -----------------------------------------------------------------------
    # Section 1 – Allgemeine Angaben
    # -----------------------------------------------------------------------
    y = _section_header(page, y, "Allgemeine Angaben")

    pruef_datum = ""
    if vde_test.created_at:
        pruef_datum = vde_test.created_at.strftime("%d.%m.%Y %H:%M")

    prufer_name = ""
    if vde_test.prufer_user:
        prufer_name = (
            f"{vde_test.prufer_user.vorname} {vde_test.prufer_user.nachname}".strip()
        )
    elif vde_test.prufer:
        prufer_name = vde_test.prufer

    # Two-column row helper
    def _two_col(y, l1, v1, l2, v2):
        mid = LEFT + WIDTH // 2
        page.insert_text(
            (LEFT, y + 12), l1, fontsize=8, color=(0.4, 0.4, 0.4), fontname=F_REGULAR
        )
        page.insert_text(
            (LEFT + 90, y + 12),
            v1 or "—",
            fontsize=9,
            color=COL_DARK,
            fontname=F_REGULAR,
        )
        page.insert_text(
            (mid + 4, y + 12), l2, fontsize=8, color=(0.4, 0.4, 0.4), fontname=F_REGULAR
        )
        page.insert_text(
            (mid + 90, y + 12),
            v2 or "—",
            fontsize=9,
            color=COL_DARK,
            fontname=F_REGULAR,
        )
        _line(page, (LEFT, y + 17), (RIGHT, y + 17))
        return y + 17

    y = _two_col(y, "Laufzettel-Nr.:", str(repair.id), "Prüfdatum:", pruef_datum)
    y = _two_col(
        y,
        "Geräteart:",
        repair.geraet_art or "—",
        "Schutzklasse:",
        vde_test.schutzklasse or "—",
    )
    y = _two_col(
        y, "Prüfer:", prufer_name, "Elektrofachkraft:", vde_test.electrician or "—"
    )
    y = _two_col(
        y,
        "Prüfgerät:",
        vde_test.pruefgeraet_name or "—",
        "Seriennummer:",
        vde_test.pruefgeraet_serial or "—",
    )
    y += 8

    # -----------------------------------------------------------------------
    # Section 2 – Sichtprüfung
    # -----------------------------------------------------------------------
    y = _section_header(page, y, "Sichtprüfung")

    sicht_items = [
        ("Gehäuse / Mechanische Unversehrtheit", vde_test.sichtpruefung_gehaeuse),
        ("Anschlussleitung / Kabel", vde_test.sichtpruefung_kabel),
        ("Stecker / Kupplung", vde_test.sichtpruefung_stecker),
        ("Zugentlastung / Knickschutz", vde_test.sichtpruefung_zugentlastung),
        ("Sicherheitseinrichtungen", vde_test.sichtpruefung_sicherheit),
    ]

    for label, state in sicht_items:
        page.insert_text(
            (LEFT + 4, y + 11), label, fontsize=9, color=COL_DARK, fontname=F_REGULAR
        )
        _check_symbol(
            page, RIGHT - 130, y, True if state is True else None, "i.O.", box_size=10
        )
        _check_symbol(
            page,
            RIGHT - 85,
            y,
            False if state is False else None,
            "n.i.O.",
            box_size=10,
        )
        _line(page, (LEFT, y + 16), (RIGHT, y + 16))
        y += 16

    y += 6

    # -----------------------------------------------------------------------
    # Section 3 – Elektrische Prüfungen
    # -----------------------------------------------------------------------
    y = _section_header(page, y, "Elektrische Prüfungen")

    el_items = [
        ("Schutzleiterwiderstandsmessung (≤ 0,3 Ω)", vde_test.schutzleiter_pruefung),
        ("Isolationswiderstandsmessung (≥ 1 MΩ)", vde_test.isolationspruefung),
        (
            "Ableitstrommessung / Ersatzableitstrommessung",
            vde_test.ableitstrom_pruefung,
        ),
    ]

    for label, result in el_items:
        page.insert_text(
            (LEFT + 4, y + 11), label, fontsize=9, color=COL_DARK, fontname=F_REGULAR
        )
        _check_symbol(
            page, RIGHT - 130, y, True if result is True else None, "i.O.", box_size=10
        )
        _check_symbol(
            page,
            RIGHT - 85,
            y,
            False if result is False else None,
            "n.i.O.",
            box_size=10,
        )
        if result is None:
            _check_symbol(page, RIGHT - 40, y, True, "n.a.", box_size=10)
        else:
            _check_symbol(page, RIGHT - 40, y, None, "n.a.", box_size=10)
        _line(page, (LEFT, y + 16), (RIGHT, y + 16))
        y += 16

    y += 8

    # -----------------------------------------------------------------------
    # Section 4 – Gesamtergebnis
    # -----------------------------------------------------------------------
    y = _section_header(page, y, "Gesamtergebnis")
    y += 4

    bestanden = vde_test.gesamtergebnis is True
    result_color = COL_PASS_BG if bestanden else COL_FAIL_BG
    result_text = "BESTANDEN" if bestanden else "NICHT BESTANDEN"
    result_icon = "\u2713" if bestanden else "\u2715"

    result_rect = fitz.Rect(LEFT, y, RIGHT, y + 30)
    _filled_rect(page, result_rect, result_color)
    page.insert_text(
        (LEFT + 16, y + 21),
        f"{result_icon}  {result_text}",
        fontsize=14,
        color=COL_RESULT_TEXT,
        fontname=F_BOLD,
    )
    y += 36

    # -----------------------------------------------------------------------
    # Section 5 – Bemerkungen
    # -----------------------------------------------------------------------
    if vde_test.bemerkungen:
        y += 4
        y = _section_header(page, y, "Bemerkungen / Mängel")
        bemerkungen_text = vde_test.bemerkungen or ""
        # Wrap long text into lines of ~85 chars
        lines = _wrap_text(bemerkungen_text, 85)
        for line in lines[:8]:  # max 8 lines
            page.insert_text(
                (LEFT + 4, y + 11), line, fontsize=9, color=COL_DARK, fontname=F_REGULAR
            )
            y += 13
        y += 4

    # -----------------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------------
    footer_y = 815
    _line(page, (LEFT, footer_y), (RIGHT, footer_y), color=(0.7, 0.7, 0.7), width=0.5)
    generated_at = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
    page.insert_text(
        (LEFT, footer_y + 12),
        f"Erstellt am {generated_at} UTC  ·  Repair Café Prüfsystem",
        fontsize=7,
        color=(0.6, 0.6, 0.6),
        fontname=F_REGULAR,
    )
    page.insert_text(
        (RIGHT - 80, footer_y + 12),
        f"Laufzettel #{repair.id}",
        fontsize=7,
        color=(0.6, 0.6, 0.6),
        fontname=F_REGULAR,
    )

    # -----------------------------------------------------------------------
    # Serialise
    # -----------------------------------------------------------------------
    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wrap_text(text: str, max_chars: int) -> list:
    """Simple word-wrap to max_chars per line."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
