"""Render an EAN-13 ISBN barcode with a white panel onto a ReportLab canvas.

Used by the per-book cover generators so every print-ready cover gets a
scannable barcode in a consistent style. The canvas, the dashed ISBN, and
the bottom-left corner of the desired panel are passed in; the function
draws a white rectangle, the human-readable "ISBN xxx-x-xxxxxxx-x-x" line,
and the EAN-13 bars itself.

All fonts used here are embedded TrueType (Liberation Sans, a metrically
equivalent Helvetica replacement). Lulu and IngramSpark reject covers
that rely on the PDF Standard 14 fonts because those aren't embedded by
default in ReportLab output.
"""

from pathlib import Path

from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.colors import white, black
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Embedded sans-serif fonts (Helvetica-equivalent, but actually embedded in
# the output PDF so Lulu/IngramSpark accept the cover). Liberation Sans is
# the standard Ubuntu-shipped metric clone.
_LIBSANS_REG = "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
_LIBSANS_BOLD = "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
_LIBSERIF_REG = "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"

_BARCODE_FONT_REGULAR = "ISBNBarcodeSans"
_BARCODE_FONT_BOLD = "ISBNBarcodeSans-Bold"

# Standard 14 PDF fonts we override globally so any default ReportLab
# reference resolves to an embedded TTF. Without this Lulu/IngramSpark
# reject the cover with "Incorrect Fonts: not embedded."
_STANDARD_14_OVERRIDES = {
    "Helvetica": _LIBSANS_REG,
    "Helvetica-Bold": _LIBSANS_BOLD,
    "Helvetica-Oblique": _LIBSANS_REG,
    "Helvetica-BoldOblique": _LIBSANS_BOLD,
    "Times-Roman": _LIBSERIF_REG,
    "Times-Bold": _LIBSERIF_REG,
    "Times-Italic": _LIBSERIF_REG,
    "Times-BoldItalic": _LIBSERIF_REG,
}


def _ensure_fonts_registered():
    """Register the embedded sans-serif fonts and Standard 14 overrides.

    Idempotent — safe to call from multiple cover generators in the same run.
    Run at module import so the overrides are in place BEFORE any
    ReportLab Canvas is constructed (the canvas registers Helvetica as a
    default at construction time).
    """
    registered = pdfmetrics.getRegisteredFontNames()
    if _BARCODE_FONT_REGULAR not in registered:
        if not Path(_LIBSANS_REG).exists():
            raise FileNotFoundError(
                f"Liberation Sans Regular not found at {_LIBSANS_REG}. "
                "Install with: sudo apt install fonts-liberation2"
            )
        pdfmetrics.registerFont(TTFont(_BARCODE_FONT_REGULAR, _LIBSANS_REG))
    if _BARCODE_FONT_BOLD not in registered:
        if not Path(_LIBSANS_BOLD).exists():
            raise FileNotFoundError(
                f"Liberation Sans Bold not found at {_LIBSANS_BOLD}. "
                "Install with: sudo apt install fonts-liberation2"
            )
        pdfmetrics.registerFont(TTFont(_BARCODE_FONT_BOLD, _LIBSANS_BOLD))
    for alias, path in _STANDARD_14_OVERRIDES.items():
        if alias not in registered and Path(path).exists():
            pdfmetrics.registerFont(TTFont(alias, path))


# Register at import time so cover scripts that `from isbn_barcode import ...`
# pick up the Standard 14 overrides before they construct their Canvas.
_ensure_fonts_registered()


def draw_isbn_barcode(c, isbn_dashed, x_left, y_bottom,
                      panel_w=1.75 * inch, panel_h=1.0 * inch):
    """Draw a white-paneled ISBN barcode block on canvas `c`.

    Args:
        c: ReportLab canvas.
        isbn_dashed: ISBN-13 with dashes, e.g. "979-8-9954288-4-8".
        x_left, y_bottom: bottom-left corner of the white panel (in points).
        panel_w, panel_h: panel size; defaults give a Lulu-friendly
            1.75" x 1.0" block (barcode + ISBN line, with quiet zone).
    """
    isbn_clean = isbn_dashed.replace("-", "").replace(" ", "")
    if len(isbn_clean) != 13:
        raise ValueError(f"Expected 13-digit ISBN; got {isbn_clean!r}")

    _ensure_fonts_registered()

    # White panel (the EAN-13 quiet zone — scanners need this contrast)
    c.setFillColor(white)
    c.rect(x_left, y_bottom, panel_w, panel_h, stroke=0, fill=1)

    # Human-readable ISBN line at the top of the panel
    c.setFillColor(black)
    c.setFont(_BARCODE_FONT_BOLD, 9)
    c.drawCentredString(
        x_left + panel_w / 2,
        y_bottom + panel_h - 0.2 * inch,
        f"ISBN {isbn_dashed}",
    )

    # Barcode itself — fontName forces the digit line under the bars to use
    # an embedded font instead of the default Helvetica.
    barcode = Ean13BarcodeWidget(
        value=isbn_clean,
        barHeight=0.55 * inch,
        barWidth=0.0125 * inch,
        fontName=_BARCODE_FONT_REGULAR,
        fontSize=7,
        humanReadable=True,
    )
    bounds = barcode.getBounds()
    bw = bounds[2] - bounds[0]
    bh = bounds[3] - bounds[1]

    drawing = Drawing(bw, bh)
    barcode.x = -bounds[0]
    barcode.y = -bounds[1]
    drawing.add(barcode)

    # Center barcode horizontally in the panel; sit it just above the
    # bottom of the panel so the ISBN line and barcode have breathing room.
    bc_x = x_left + (panel_w - bw) / 2
    bc_y = y_bottom + 0.05 * inch
    renderPDF.draw(drawing, c, bc_x, bc_y)
