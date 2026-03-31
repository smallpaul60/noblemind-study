#!/usr/bin/env python3
"""Generate IngramSpark paperback cover PDF for Is Baptism Really Necessary?

IngramSpark specs (5x8 perfect bound paperback, B&W white paper, 30 pages):
  Trim size: 5" x 8"
  Spine width: 30 x 0.002252 = 0.06756" ≈ 0.068"
  Bleed: 0.125" on all outside edges (not on spine edges)
  Total document width: 0.125 + 5 + 0.068 + 5 + 0.125 = 10.318"
  Total document height: 0.125 + 8 + 0.125 = 8.25"
  Safety margin: 0.5" inside trim edges for text
  Spine too narrow for text — left blank
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Is_Baptism_Really_Necessary_IngramSpark_Paperback_Cover.pdf"
COVER_IMAGE = BOOK_DIR / "Is_Baptism_Really_Necessary_Cover.png"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Spine calculation ---
PAGE_COUNT = 38
SPINE_W = round(PAGE_COUNT * 0.002252, 4)  # 0.0856"

# --- Document dimensions ---
BLEED = 0.125   # inches
TRIM_W = 5.0    # inches
TRIM_H = 8.0    # inches

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H = (BLEED + TRIM_H + BLEED) * inch

# --- Colors ---
# Dark background matching the cover image gradient
DARK_BG = Color(0.020, 0.024, 0.032)       # Very dark blue-black
TEXT_PRIMARY = Color(0.961, 0.941, 0.902)   # #F5F0E6 warm cream
TEXT_SECONDARY = Color(0.824, 0.804, 0.765) # Muted cream
TEXT_MUTED = Color(0.600, 0.580, 0.545)     # Muted for attribution
ACCENT = Color(0.369, 0.898, 1.0)           # #5EE5FF cyan accent (from site)

# --- Layout positions ---
HALF_W = (DOC_W - SPINE_W * inch) / 2

BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = HALF_W

SPINE_LEFT = HALF_W
SPINE_RIGHT = HALF_W + SPINE_W * inch

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

# Trim edges
BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = HALF_W
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = SPINE_RIGHT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# Vertical
V_BLEED = BLEED * inch
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED

# Safety margin
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
    """Fill entire document with dark background."""
    c.setFillColor(DARK_BG)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover_image(c):
    """Place the cover image on the front cover area."""
    img = ImageReader(str(COVER_IMAGE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    # Target area: entire front cover panel including bleed
    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    # Center image on TRIM area (not full panel) so content appears visually centered.
    # The panel includes bleed on the right side only, which shifts the panel center
    # right of the visual trim center by BLEED/2. Correct for this.
    trim_center_x = FRONT_TRIM_LEFT + (TRIM_W * inch) / 2

    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = trim_center_x - draw_w / 2
        draw_y = 0
    else:
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = trim_center_x - draw_w / 2
        draw_y = (target_h - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()


def draw_back_cover(c):
    """Draw back cover text on dark background."""
    safe_left = BACK_TRIM_LEFT + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    # --- Hook line (italic, accent) ---
    y = TRIM_TOP - 1.2 * inch
    c.setFillColor(ACCENT)
    c.setFont("EBGaramond-Italic", 11)
    hook = "What if everything you were taught about baptism wasn\u2019t what the Bible actually says?"
    lines = wrap_text(c, hook, "EBGaramond-Italic", 11, text_width)
    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= 15

    # --- Thin decorative line ---
    y -= 12
    line_hw = 0.6 * inch
    c.setStrokeColor(TEXT_MUTED)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 22

    # --- Body text ---
    c.setFillColor(TEXT_PRIMARY)
    line_height = 13.5

    body_paragraphs = [
        "This study asks one thing of you: set aside what men have taught, and look at what the Scriptures say for yourself.",
        "Inside you will find every command Jesus gave concerning baptism. Every passage the apostles wrote about it. Every conversion recorded in the book of Acts \u2014 nine in all \u2014 and what happened in every single one.",
        "You will also find honest answers to every common objection: salvation by grace alone, faith alone, the thief on the cross, and more.",
        "No opinion. No denomination. Just the text.",
        "Check every verse. Follow wherever it leads.",
    ]

    for i, para in enumerate(body_paragraphs):
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # --- Website ---
    y -= line_height * 0.5
    c.setFillColor(ACCENT)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y, "noblemind.study")

    # --- Attribution (small, muted) ---
    y -= line_height * 1.5
    c.setFillColor(TEXT_MUTED)
    c.setFont("EBGaramond-Italic", 7.5)
    c.drawCentredString(cx, y, "Scripture quotations from the")
    y -= 11
    c.drawCentredString(cx, y, "New American Standard Bible\u00ae (NASB).")

    # --- Barcode area placeholder ---
    # IngramSpark places barcode at bottom-right of back cover
    # Leave ~2" x 1.2" empty space there


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating IngramSpark PAPERBACK cover PDF...')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages, B&W white paper)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Is Baptism Really Necessary? - IngramSpark Paperback Cover")

    draw_background(c)
    draw_front_cover_image(c)
    draw_back_cover(c)
    # No spine text — too narrow at 0.068"

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
