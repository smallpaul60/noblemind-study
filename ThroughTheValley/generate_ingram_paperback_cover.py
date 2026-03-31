#!/usr/bin/env python3
"""Generate IngramSpark paperback cover PDF for Through the Valley.

IngramSpark specs (5.5x8.5 perfect bound paperback, B&W white paper, 120 pages):
  Trim size: 5.5" x 8.5"
  Spine width: 120 x 0.002252 = 0.27024" ≈ 0.27"
  Bleed: 0.125" on all outside edges (not on spine edges)
  Total document width: 0.125 + 5.5 + 0.27 + 5.5 + 0.125 = 11.52"
  Total document height: 0.125 + 8.5 + 0.125 = 8.75"
  Safety margin: 0.5" inside trim edges for text
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Through_the_Valley_IngramSpark_Paperback_Cover.pdf"
IMAGE_FILE = BOOK_DIR / "cover_image_extracted.jpg"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Spine calculation ---
PAGE_COUNT = 120
SPINE_W = 0.27  # 120 x 0.002252 = 0.27024" ≈ 0.27"

# --- Document dimensions ---
BLEED = 0.125   # inches
TRIM_W = 5.5    # inches
TRIM_H = 8.5    # inches

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch  # 11.52"
DOC_H = (BLEED + TRIM_H + BLEED) * inch                      # 8.75"

# --- Colors ---
DEEP_GREEN = Color(0.110, 0.180, 0.110)   # #1C2E1C deep forest green
CREAM = Color(0.961, 0.941, 0.910)        # #F5F0E8 warm cream
SAGE_LIGHT = Color(0.659, 0.722, 0.620)   # #A8B89E light sage
SAGE_MUTED = Color(0.482, 0.553, 0.435)   # #7B8D6F muted sage

# --- Layout positions (from left edge of document) ---
# Layout: bleed(0.125) + back_cover(5.5) + spine(0.27) + front_cover(5.5) + bleed(0.125) = 11.52"
HALF_W = (DOC_W - SPINE_W * inch) / 2  # back cover + bleed on left side

BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = HALF_W

SPINE_LEFT = HALF_W
SPINE_RIGHT = HALF_W + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

# Trim edges (0.125" inside bleed on outer edges)
BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = HALF_W  # spine edge — no bleed here
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = SPINE_RIGHT  # spine edge — no bleed here
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# Vertical
V_BLEED = BLEED * inch  # 0.125"
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_CENTER_Y = DOC_H / 2

# Safety margin: 0.5" inside trim for text
SAFETY = 0.5 * inch


def wrap_text(c, text, font_name, font_size, max_width):
    """Wrap text to fit within max_width. Returns list of lines."""
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_background(c):
    """Fill entire document with deep forest green."""
    c.setFillColor(DEEP_GREEN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover_image(c):
    """Place the cover image on the front cover area, filling it completely.

    The image already contains title, subtitle, and author name, so no text
    is drawn on top. Image is shifted up by AUTHOR_LIFT to ensure the author
    name clears IngramSpark's 0.5" type safety zone from the trim edge.
    """
    AUTHOR_LIFT = 0.25 * inch  # Shift image up to move author name into safety

    img = ImageReader(str(IMAGE_FILE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    # Target area: entire front cover panel including bleed
    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    # Scale to cover the target area completely (may crop edges)
    if img_aspect > target_aspect:
        # Image is wider — fit height, center horizontally
        draw_h = target_h + AUTHOR_LIFT  # Slightly taller to fill gap at bottom
        draw_w = draw_h * img_aspect
        draw_x = target_x + (target_w - draw_w) / 2
        draw_y = AUTHOR_LIFT  # Shift up — crops bottom of image, moves text up
    else:
        # Image is taller — fit width, center vertically
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = target_x
        draw_y = (target_h - draw_h) / 2 + AUTHOR_LIFT

    # Clip to front cover area (full bleed extent) and draw
    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()


def draw_spine(c):
    """Draw spine text on deep green background.

    At 0.27" the spine is very narrow. Text reads top-to-bottom (rotated 270).
    """
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 6.5)
    c.drawCentredString(0, 2, "Through the Valley")
    c.setFont("EBGaramond", 5.5)
    c.drawCentredString(0, -5, "Paul Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover text on deep forest green background."""
    safe_left = BACK_TRIM_LEFT + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    # --- Hook line (italic, light sage) ---
    y = TRIM_TOP - 1.0 * inch
    c.setFillColor(SAGE_LIGHT)
    c.setFont("EBGaramond-Italic", 10.5)
    hook = "This book is short enough to read in a hospital room. It is meant to be."
    lines = wrap_text(c, hook, "EBGaramond-Italic", 10.5, text_width)
    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= 14

    # --- Thin decorative line ---
    y -= 8
    line_hw = 0.6 * inch
    c.setStrokeColor(SAGE_LIGHT)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 18

    # --- Body text (cream) ---
    c.setFillColor(CREAM)
    line_height = 13.5

    body_paragraphs = [
        "Someone you love is dying. Or maybe that someone is you.",
        "Through the Valley walks with two people at once \u2014 the one whose body is failing and the one who will be left behind. It does not separate them, because they are walking through the same valley.",
        "In eight chapters anchored entirely in Scripture, this book examines what God actually says \u2014 not platitudes, not near-death stories, not clinical speculation. What does God say about His presence when He feels absent? What happens after death? And how do you grieve honestly while holding to a hope that Scripture calls certain?",
        "The valley is real. The shadow is dark. But David did not say \u2018if I walk into the valley.\u2019 He said \u2018even though I walk through.\u2019 The valley has a through. And the Shepherd is already there.",
    ]

    for i, para in enumerate(body_paragraphs):
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4  # paragraph spacing

    # --- Attribution (small, muted sage) ---
    y -= line_height * 0.3
    c.setFillColor(SAGE_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y, "Scripture quotations from the New American Standard Bible\u00ae (NASB).")

    # --- Barcode area placeholder (bottom-right of back cover) ---
    # IngramSpark places barcode here; leave empty space
    # Approximate barcode area: 2" x 1.2" at bottom-right of back cover


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating IngramSpark PAPERBACK cover PDF for "Through the Valley"...')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages, B&W white paper)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Through the Valley - IngramSpark Paperback Cover")

    draw_background(c)
    draw_front_cover_image(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
