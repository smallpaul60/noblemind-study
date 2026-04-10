#!/usr/bin/env python3
"""Generate IngramSpark hardcover (casebound with dust jacket) cover PDF for Through the Valley.

IngramSpark specs (5.5x8.5 casebound with dust jacket, 122 pages creme paper):
  Trim size: 5.5" x 8.5"
  Board size: 5.625" x 8.625" (trim + 0.125" on each dimension)
  Spine width: 0.438" (IngramSpark-specified for 122 pages creme paper)
  Flap width: 3.25" (standard dust jacket flap)
  Bleed: 0.125" on all four sides
  Turn-in: 0.625" on each flap edge
  Total width: 0.125 + 0.625 + 3.25 + 5.625 + 0.438 + 5.625 + 3.25 + 0.625 + 0.125 = 19.688"
  Total height: 0.125 + 8.625 + 0.125 = 8.875"
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Through_the_Valley_IngramSpark_Hardcover_Cover.pdf"
IMAGE_FILE = BOOK_DIR / "cover_image_extracted.jpg"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions ---
PAGE_COUNT = 122
SPINE_W = 0.438         # inches (IngramSpark-specified for 122 pages creme paper)
BOARD_W = 5.625         # inches (trim 5.5 + 0.125)
BOARD_H = 8.625         # inches (trim 8.5 + 0.125)
FLAP_W = 3.25           # inches (standard dust jacket flap)
TURN_IN = 0.625         # inches (turn-in at each flap edge)
BLEED = 0.125           # inches (top and bottom)

DOC_W = (BLEED + TURN_IN + FLAP_W + BOARD_W + SPINE_W + BOARD_W + FLAP_W + TURN_IN + BLEED) * inch
DOC_H = (BLEED + BOARD_H + BLEED) * inch  # 8.875"

# --- Colors ---
DEEP_GREEN = Color(0.110, 0.180, 0.110)   # #1C2E1C deep forest green
CREAM = Color(0.961, 0.941, 0.910)        # #F5F0E8 warm cream
SAGE_LIGHT = Color(0.659, 0.722, 0.620)   # #A8B89E light sage
SAGE_MUTED = Color(0.482, 0.553, 0.435)   # #7B8D6F muted sage

# --- Layout positions (from left edge of document) ---
# Layout: turn_in(0.625) + back_flap(3.25) + back_board(5.625)
#         + spine(0.35) + front_board(5.625) + front_flap(3.25) + turn_in(0.625) = 19.35"

BACK_FLAP_LEFT = (BLEED + TURN_IN) * inch
BACK_FLAP_RIGHT = BACK_FLAP_LEFT + FLAP_W * inch

BACK_COVER_LEFT = BACK_FLAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + BOARD_W * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + BOARD_W * inch

FRONT_FLAP_LEFT = FRONT_COVER_RIGHT
FRONT_FLAP_RIGHT = FRONT_FLAP_LEFT + FLAP_W * inch

# Vertical (bleed on top and bottom)
V_BLEED = BLEED * inch
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_CENTER_Y = DOC_H / 2

# Center of each cover panel
BACK_CENTER_X = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# Safety margins for text
SAFETY = 0.5 * inch

# Flap text safe areas (asymmetric: 0.25" from fold, 0.75" from turn-in)
# Front flap: left=fold, right=turn-in
FRONT_FLAP_SAFE_LEFT = FRONT_FLAP_LEFT + 0.25 * inch
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - 0.75 * inch
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT  # 2.25"

# Back flap: left=turn-in, right=fold
BACK_FLAP_SAFE_LEFT = BACK_FLAP_LEFT + 0.75 * inch
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - 0.25 * inch
BACK_FLAP_TEXT_W = BACK_FLAP_SAFE_RIGHT - BACK_FLAP_SAFE_LEFT  # 2.25"


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
    """Place the cover image on the front board area, filling it completely.

    The image already contains title, subtitle, and author name baked in.
    """
    img = ImageReader(str(IMAGE_FILE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    # Target: front board area (no separate bleed on board edges for dust jacket —
    # the image fills the entire board panel)
    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    # Scale to cover completely
    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = target_x + (target_w - draw_w) / 2
        draw_y = 0
    else:
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = target_x
        draw_y = (target_h - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()


def draw_spine(c):
    """Draw spine text on deep green background.

    At 0.35" the spine can hold small text. Reads top-to-bottom (rotated 270).
    """
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 7.5)
    c.drawCentredString(0, 2.5, "Through the Valley")
    c.setFont("EBGaramond", 6)
    c.drawCentredString(0, -5, "Paul Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover text on deep forest green background."""
    safe_left = BACK_COVER_LEFT + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
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

    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # --- Attribution (small, muted sage) ---
    y -= line_height * 0.3
    c.setFillColor(SAGE_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y, "Scripture quotations from the New American Standard Bible\u00ae (NASB).")


def draw_front_flap(c):
    """Draw front flap text — book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(CREAM)

    y = TRIM_TOP - SAFETY
    line_height = 11

    paragraphs = [
        ("EBGaramond-Italic", 8.5, "Through the Valley is written for the hardest season \u2014 when someone you love is facing the end, or when that someone is you."),
        (None, 0, ""),
        ("EBGaramond", 8, "Built on five principles \u2014 the Bible as sole authority, word-for-word accuracy, Scripture interprets Scripture, intellectual honesty, and a shared journey \u2014 each chapter walks with both the one who is departing and the one who remains."),
        (None, 0, ""),
        ("EBGaramond", 8, "This is not a book of platitudes. It acknowledges that the pain is real, the body decays, and the questions are often loud. It does not pretend the valley is not dark. It simply trusts that the Light is brighter."),
    ]

    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.5
            continue

        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            c.drawString(safe_left, y, line)
            y -= line_height
        y -= line_height * 0.2


def draw_back_flap(c):
    """Draw back flap text — About the Author."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(CREAM)

    # Heading
    y = TRIM_TOP - SAFETY
    c.setFont("EBGaramond", 10)
    c.drawString(safe_left, y, "About the Author")
    y -= 16

    line_height = 10.5

    paragraphs = [
        "Paul Hainline is a student of God\u2019s Word and the author of works rooted in the conviction that Scripture interprets Scripture. He writes from a desire to point readers back to the biblical text. He is the founder of NobleMind Press (noblemind.study).",
    ]

    for text in paragraphs:
        lines = wrap_text(c, text, "EBGaramond", 7.5, text_width)
        for line in lines:
            c.setFont("EBGaramond", 7.5)
            c.drawString(safe_left, y, line)
            y -= line_height
        y -= line_height * 0.2


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating IngramSpark HARDCOVER (dust jacket) cover PDF for "Through the Valley"...')
    print(f'  Trim size: 5.5" x 8.5"')
    print(f'  Board size: {BOARD_W}" x {BOARD_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages + board thickness)')
    print(f'  Flap width: {FLAP_W}"')
    print(f'  Bleed (top/bottom): {BLEED}"')
    print(f'  Turn-in (flap edges): {TURN_IN}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Through the Valley - IngramSpark Hardcover Dust Jacket Cover")

    draw_background(c)
    draw_front_cover_image(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
