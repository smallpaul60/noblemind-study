#!/usr/bin/env python3
"""Generate a front-cover mockup for The Last Week of the Lamb.

Front cover only — Lulu/IngramSpark 5.5" x 8.5" trim with 0.125" bleed.
Uses the bloody-doorframe image as background; places title, subtitle,
author, and imprint in the dark space between the posts.

Outputs:
  - The_Last_Week_of_the_Lamb_Front_Cover_Mockup.pdf  (crisp text, for review)
  - The_Last_Week_of_the_Lamb_Front_Cover_Mockup.png  (rasterized preview)

This is a design-approval mockup. The print-ready full wraparound cover
(back + spine + front) will be generated once the design is locked and the
background image has been upscaled to 300 DPI.
"""

from pathlib import Path

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
IMAGE_FILE = BOOK_DIR / "book_cover_doorframe.png"
OUTPUT_PDF = BOOK_DIR / "The_Last_Week_of_the_Lamb_Front_Cover_Mockup.pdf"
OUTPUT_PNG = BOOK_DIR / "The_Last_Week_of_the_Lamb_Front_Cover_Mockup.png"

FONT_DIR = Path.home() / ".local" / "share" / "fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions ---
# Trim 5.5" x 8.5", bleed 0.125" on all sides
BLEED = 0.125 * inch
TRIM_W = 5.5 * inch
TRIM_H = 8.5 * inch
DOC_W = TRIM_W + 2 * BLEED     # 5.75"
DOC_H = TRIM_H + 2 * BLEED     # 8.75"

# --- Colors ---
CREAM = Color(0.96, 0.93, 0.84)    # warm cream for title
CREAM_DIM = Color(0.85, 0.80, 0.70)  # softer cream for subtitle
GOLD = Color(0.79, 0.66, 0.31)      # muted gold accent

# --- Text layout anchor ---
# The doorframe's inner dark area in the rendered cover spans roughly
# x = 0.255 (left inner post edge) to x = 0.795 (right inner post edge).
# True horizontal center of the dark well is at x = 0.525 of the cover.
# (The left post has brighter highlights, which creates a mild optical
# pull to the left — but the geometric center is the better anchor.)
# PDF coordinates: y=0 at the bottom, so we convert.
DARK_CENTER_X_FRAC = 0.525
TITLE_Y_FRAC_FROM_TOP = 0.30       # title block top (dropped for balance)
SUBTITLE_Y_FRAC_FROM_TOP = 0.435   # top of letters mirrors title baseline above rule
AUTHOR_Y_FRAC_FROM_TOP = 0.87      # pulled down near the imprint
IMPRINT_Y_FRAC_FROM_TOP = 0.93


def frac_to_pdf_y(frac_from_top):
    """Convert a top-down fraction of the cover to a PDF y coordinate."""
    return DOC_H - (frac_from_top * DOC_H)


def draw_background_image(c):
    """Draw the cover image filling the full document (with bleed)."""
    img = ImageReader(str(IMAGE_FILE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h
    target_aspect = DOC_W / DOC_H

    # Fit to height if image is wider; fit to width if image is taller
    if img_aspect > target_aspect:
        draw_h = DOC_H
        draw_w = DOC_H * img_aspect
        draw_x = (DOC_W - draw_w) / 2
        draw_y = 0
    else:
        draw_w = DOC_W
        draw_h = DOC_W / img_aspect
        draw_x = 0
        draw_y = (DOC_H - draw_h) / 2

    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h,
                preserveAspectRatio=True, mask="auto")


def draw_text(c):
    """Draw title, subtitle, author, imprint between the doorposts."""
    cx = DARK_CENTER_X_FRAC * DOC_W

    # --- Title: "The Last Week of the Lamb" ---
    # Two lines, centered, large, cream. "Last Week" gets emphasis on line 2.
    c.setFillColor(CREAM)
    title_font = "EBGaramond"

    title_line1 = "The Last Week"
    title_line2 = "of the Lamb"

    title_size = 34
    c.setFont(title_font, title_size)
    y1 = frac_to_pdf_y(TITLE_Y_FRAC_FROM_TOP)
    c.drawCentredString(cx, y1, title_line1)
    y2 = y1 - (title_size * 1.05)
    c.drawCentredString(cx, y2, title_line2)

    # --- Thin gold rule under title ---
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    rule_y = y2 - 0.28 * inch
    rule_half = 0.7 * inch
    c.line(cx - rule_half, rule_y, cx + rule_half, rule_y)

    # --- Subtitle: "The Passover Pattern Good Friday Missed" ---
    c.setFillColor(CREAM_DIM)
    subtitle_size = 14
    c.setFont("EBGaramond-Italic", subtitle_size)
    sy = frac_to_pdf_y(SUBTITLE_Y_FRAC_FROM_TOP)
    c.drawCentredString(cx, sy, "The Passover Pattern")
    c.drawCentredString(cx, sy - (subtitle_size * 1.35), "Good Friday Missed")

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 18)
    ay = frac_to_pdf_y(AUTHOR_Y_FRAC_FROM_TOP)
    c.drawCentredString(cx, ay, "Paul Hainline")

    # --- Imprint ---
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 9)
    iy = frac_to_pdf_y(IMPRINT_Y_FRAC_FROM_TOP)
    # Small caps by setting text in caps with tracking
    c.drawCentredString(cx, iy, "N O B L E M I N D   P R E S S")


def render_png_preview():
    """Rasterize the PDF to PNG via pdftoppm for a visual preview."""
    import subprocess
    tmp_prefix = BOOK_DIR / "_front_cover_preview"
    subprocess.run(
        ["pdftoppm", "-r", "150", "-png", str(OUTPUT_PDF), str(tmp_prefix)],
        check=True,
    )
    rendered = BOOK_DIR / "_front_cover_preview-1.png"
    if rendered.exists():
        rendered.rename(OUTPUT_PNG)


def main():
    print('Generating front-cover mockup for "The Last Week of the Lamb"...')
    print(f'  Trim: 5.5" x 8.5", with 0.125" bleed')
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')

    c = canvas.Canvas(str(OUTPUT_PDF), pagesize=(DOC_W, DOC_H))
    draw_background_image(c)
    draw_text(c)
    c.save()
    print(f"  PDF saved to {OUTPUT_PDF}")

    render_png_preview()
    print(f"  PNG preview saved to {OUTPUT_PNG}")
    print("Done.")


if __name__ == "__main__":
    main()
