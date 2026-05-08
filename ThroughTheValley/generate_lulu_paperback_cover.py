#!/usr/bin/env python3
"""Generate Lulu paperback cover for Through the Valley.

Lulu specs (from lulu-paperback-cover-template.pdf, page count 120,
cream paper):
  Document size:   11.58" x 8.75"  (with 0.125" bleed all sides)
  Book trim size:  5.5" x 8.5"
  Spine width:     0.33"
  Safety margin:   0.5" from trim edge
  Barcode area:    3.622" x 1.26"  (panel for ISBN barcode)
                    positioned 0.5" from bleed edge

Layout (left to right):
  [0.125 bleed][5.5 back cover trim][0.33 spine][5.5 front cover trim][0.125 bleed]
  Heights: 0.125 bleed top + 8.5 trim + 0.125 bleed bottom = 8.75

Design matches the v6 hardcover jacket so paperback and hardcover read
as the same edition: deep green field, framed sunset image, Paul & Pam
byline, Psalm 23:4 + dedication on the back, NobleMind imprint, ISBN
barcode at lower-LEFT of back panel (opposite the spine).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import isbn_barcode  # noqa: F401  -- registers Standard 14 font aliases

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Through_the_Valley_Lulu_Paperback_Cover.pdf"
COVER_IMAGE = BOOK_DIR / "new-cover-image-upscaled.png"
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-7-9.png"   # paperback ISBN

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions ---
DOC_W_IN = 11.58
DOC_H_IN = 8.75
SPINE_W_IN = 0.33
TRIM_W_IN = 5.5
TRIM_H_IN = 8.5
BLEED_IN = 0.125

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# --- Horizontal layout anchors (in pts) ---
BACK_PANEL_LEFT = 0
BACK_PANEL_RIGHT = (BLEED_IN + TRIM_W_IN) * inch       # 5.625
SPINE_LEFT = BACK_PANEL_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W_IN * inch            # 5.955
FRONT_PANEL_LEFT = SPINE_RIGHT
FRONT_PANEL_RIGHT = DOC_W                               # 11.58

# Visible (post-trim) cover faces
BACK_VISIBLE_LEFT = BLEED_IN * inch                     # 0.125
BACK_VISIBLE_RIGHT = BACK_PANEL_RIGHT                   # 5.625
FRONT_VISIBLE_LEFT = FRONT_PANEL_LEFT                   # 5.955
FRONT_VISIBLE_RIGHT = (DOC_W_IN - BLEED_IN) * inch      # 11.455
VISIBLE_TOP = (DOC_H_IN - BLEED_IN) * inch              # 8.625
VISIBLE_BOTTOM = BLEED_IN * inch                        # 0.125

BACK_VISIBLE_CENTER = (BACK_VISIBLE_LEFT + BACK_VISIBLE_RIGHT) / 2
FRONT_VISIBLE_CENTER = (FRONT_VISIBLE_LEFT + FRONT_VISIBLE_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

# --- Colors (match the hardcover jacket palette) ---
DEEP_GREEN = Color(0.110, 0.180, 0.110)
CREAM      = Color(0.961, 0.941, 0.910)
GOLD       = Color(0.788, 0.659, 0.306)
GOLD_MUTED = Color(0.580, 0.475, 0.220)
DARK_INK   = Color(0.090, 0.130, 0.090)
SLATE      = Color(0.608, 0.580, 0.525)
WHITE      = Color(1, 1, 1)

# --- Padding ---
SAFETY_IN = 0.5             # Lulu's stated safety margin (from trim edge)
BACK_TEXT_INSET = 0.75      # each side, from trim edge — generous
COVER_FRAME_IN = 0.2        # dark-green frame around front image


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for w in words:
        test = f"{current} {w}".strip() if current else w
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_background(c):
    """Fill the entire cover with deep green."""
    c.setFillColor(DEEP_GREEN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Front panel: image inset with dark-green frame; title + subtitle +
    byline overlaid. Centered on the visible front face midpoint."""
    cx = FRONT_VISIBLE_CENTER

    # Image inset rectangle (inside the visible cover, framed by green)
    img_x = FRONT_VISIBLE_LEFT + COVER_FRAME_IN * inch
    img_y = VISIBLE_BOTTOM + COVER_FRAME_IN * inch
    img_w = (FRONT_VISIBLE_RIGHT - FRONT_VISIBLE_LEFT) - 2 * COVER_FRAME_IN * inch
    img_h = (VISIBLE_TOP - VISIBLE_BOTTOM) - 2 * COVER_FRAME_IN * inch

    img = ImageReader(str(COVER_IMAGE))
    src_w, src_h = img.getSize()
    src_aspect = src_w / src_h
    target_aspect = img_w / img_h

    if src_aspect > target_aspect:
        draw_h = img_h
        draw_w = img_h * src_aspect
        draw_x = img_x + (img_w - draw_w) / 2
        draw_y = img_y
    else:
        draw_w = img_w
        draw_h = img_w / src_aspect
        draw_x = img_x
        draw_y = img_y + (img_h - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(img_x, img_y, img_w, img_h)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # Title — two-line italic serif, near-equal sizes (matches hardcover).
    # Slightly smaller than the jacket because the paperback face is
    # 5.5" vs the jacket's 5.75" visible width.
    title_top_y = VISIBLE_TOP - 0.95 * inch
    c.setFillColor(DARK_INK)
    c.setFont("EBGaramond-Italic", 44)
    c.drawCentredString(cx, title_top_y, "Through the")

    title_main_y = title_top_y - 0.66 * inch
    c.setFont("EBGaramond-Italic", 48)
    c.drawCentredString(cx, title_main_y, "Valley")

    rule_y = title_main_y - 0.38 * inch
    rule_hw = 0.55 * inch
    c.setStrokeColor(DARK_INK)
    c.setLineWidth(0.6)
    c.line(cx - rule_hw, rule_y, cx + rule_hw, rule_y)

    c.setFont("EBGaramond-Italic", 14)
    sub_y = rule_y - 0.28 * inch
    c.drawCentredString(cx, sub_y, "What God Says When the Shadow Is Real")

    # Soft dark gradient at the bottom of the front image so the byline
    # reads cleanly regardless of what part of the painted scene sits
    # under it.
    c.saveState()
    grad_path = c.beginPath()
    grad_path.rect(img_x, img_y, img_w, img_h)
    grad_path.close()
    c.clipPath(grad_path, stroke=0)
    grad_h = 1.5 * inch
    bsteps = 240
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.04, 0.07, 0.04, alpha))
        y_band = grad_h * (1 - i / bsteps) + img_y
        h_band = grad_h / bsteps + 1
        c.rect(img_x, y_band - h_band, img_w, h_band, fill=1, stroke=0)
    c.restoreState()

    # Byline in cream over the gradient
    byline_y = VISIBLE_BOTTOM + 0.55 * inch
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 15)
    c.drawCentredString(cx, byline_y, "P A U L  &  P A M   H A I N L I N E")


def draw_spine(c):
    """Vertical title only on the 0.33" spine (tighter than the
    hardcover's 0.5" — author/imprint omitted to stay safely centered)."""
    c.saveState()
    c.translate(SPINE_CENTER_X, DOC_H / 2)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(0, -4, "Through the Valley")
    c.restoreState()


def draw_back_cover(c):
    """Back panel: Psalm 23:4 pull, dedication, NobleMind imprint,
    ISBN barcode at lower-LEFT of back cover (opposite the spine)."""
    cx = BACK_VISIBLE_CENTER

    # Psalm 23:4 pull (gold italic, upper third)
    y = VISIBLE_TOP - 1.0 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 13)
    psalm_lines = [
        "“Even though I walk through the valley",
        "of the shadow of death,",
        "I fear no evil, for You are with me…”",
    ]
    line_height = 19
    for line in psalm_lines:
        c.drawCentredString(cx, y, line)
        y -= line_height

    y -= 6
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond", 10)
    c.drawCentredString(cx, y, "— Psalm 23:4")
    y -= 22

    # Thin gold rule
    rule_hw = 0.7 * inch
    c.setStrokeColor(GOLD_MUTED)
    c.setLineWidth(0.5)
    c.line(cx - rule_hw, y, cx + rule_hw, y)
    y -= 28

    # Dedication (cream italic)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, y, "To all those who are going")
    y -= 19
    c.drawCentredString(cx, y, "through the valley.")

    # Imprint — placed above the lower-left barcode area so they don't
    # collide. Centered on the back cover, mid-low.
    mark_y = 2.0 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")

    # ISBN barcode in lower-LEFT of back cover, on a white panel.
    # 0.5" from the bleed edge (left and bottom) per Lulu's barcode area
    # guidance; sized to comfortably fit a standard EAN-13.
    bc_w = 1.85 * inch
    bc_h = bc_w * 280 / 523
    pad = 0.08 * inch
    box_w = bc_w + 2 * pad
    box_h = bc_h + 2 * pad
    box_x = 0.5 * inch
    box_y = 0.5 * inch
    c.setFillColor(WHITE)
    c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)
    bc_img = ImageReader(str(BARCODE_IMAGE))
    c.drawImage(bc_img, box_x + pad, box_y + pad, width=bc_w, height=bc_h)


def main():
    print('Generating Lulu PAPERBACK COVER PDF for "Through the Valley"...')
    print(f'  Document size:  {DOC_W_IN}" x {DOC_H_IN}"')
    print(f'  Spine:          {SPINE_W_IN}"')
    print(f'  Trim per cover: {TRIM_W_IN}" x {TRIM_H_IN}"')
    print()
    print(f'  Panel x-positions (inches):')
    print(f'    back panel  : {BACK_PANEL_LEFT/inch:.3f} .. {BACK_PANEL_RIGHT/inch:.3f}')
    print(f'    spine       : {SPINE_LEFT/inch:.3f} .. {SPINE_RIGHT/inch:.3f}')
    print(f'    front panel : {FRONT_PANEL_LEFT/inch:.3f} .. {FRONT_PANEL_RIGHT/inch:.3f}')
    print(f'    back visible: {BACK_VISIBLE_LEFT/inch:.3f} .. {BACK_VISIBLE_RIGHT/inch:.3f}')
    print(f'    front visible: {FRONT_VISIBLE_LEFT/inch:.3f} .. {FRONT_VISIBLE_RIGHT/inch:.3f}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Through the Valley — Lulu Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nPaperback cover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
