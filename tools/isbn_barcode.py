"""Render an EAN-13 ISBN barcode with a white panel onto a ReportLab canvas.

Used by the per-book cover generators so every print-ready cover gets a
scannable barcode in a consistent style. The canvas, the dashed ISBN, and
the bottom-left corner of the desired panel are passed in; the function
draws a white rectangle, the human-readable "ISBN xxx-x-xxxxxxx-x-x" line,
and the EAN-13 bars itself.
"""

from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.colors import white, black
from reportlab.lib.pagesizes import inch


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

    # White panel (the EAN-13 quiet zone — scanners need this contrast)
    c.setFillColor(white)
    c.rect(x_left, y_bottom, panel_w, panel_h, stroke=0, fill=1)

    # Human-readable ISBN line at the top of the panel
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(
        x_left + panel_w / 2,
        y_bottom + panel_h - 0.2 * inch,
        f"ISBN {isbn_dashed}",
    )

    # Barcode itself
    barcode = Ean13BarcodeWidget(
        value=isbn_clean,
        barHeight=0.55 * inch,
        barWidth=0.0125 * inch,
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
