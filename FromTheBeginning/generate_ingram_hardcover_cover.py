#!/usr/bin/env python3
"""Generate IngramSpark hardcover (casebound with dust jacket) cover PDF for From the Beginning.

IngramSpark specs (5.5x8.5 casebound with dust jacket, 154 pages):
  Trim size: 5.5" x 8.5"
  Board size: 5.625" x 8.625" (trim + 0.125" on each dimension)
  Spine width: 154 x 0.002252 + 0.08 = 0.427" (includes board thickness)
  Flap width: 3.25" (standard dust jacket flap)
  Bleed: 0.125" on all four sides
  Turn-in: 0.625" on each flap edge
  Total width: 0.125 + 0.625 + 3.25 + 5.625 + 0.427 + 5.625 + 3.25 + 0.625 + 0.125 = 19.677"
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
OUTPUT = BOOK_DIR / "FromTheBeginning_IngramSpark_Hardcover_Cover.pdf"
IMAGE_FILE = BOOK_DIR / "FromTheBeginning_Portrait.png"

# Register fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions ---
PAGE_COUNT = 154
SPINE_W = round(PAGE_COUNT * 0.002252 + 0.08, 3)  # 0.427"
BOARD_W = 5.625         # inches (trim 5.5 + 0.125)
BOARD_H = 8.625         # inches (trim 8.5 + 0.125)
FLAP_W = 3.25           # inches (standard dust jacket flap)
TURN_IN = 0.625         # inches (turn-in at each flap edge)
BLEED = 0.125           # inches (top and bottom)

DOC_W = (BLEED + TURN_IN + FLAP_W + BOARD_W + SPINE_W + BOARD_W + FLAP_W + TURN_IN + BLEED) * inch
DOC_H = (BLEED + BOARD_H + BLEED) * inch

# --- Colors ---
DEEP_BLUE = Color(0.067, 0.118, 0.216)     # #112138 deep midnight blue
CREAM = Color(0.961, 0.902, 0.784)         # #F5E6C8 warm cream
GOLD_LIGHT = Color(0.831, 0.659, 0.282)    # #D4A848 warm gold
GOLD_MUTED = Color(0.631, 0.529, 0.322)    # #A18752 muted gold

# --- Layout positions (from left edge of document) ---
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

# Vertical
V_BLEED = BLEED * inch
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_CENTER_Y = DOC_H / 2

# Centers
BACK_CENTER_X = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# Safety margins
SAFETY = 0.5 * inch          # Cover panels
FRONT_SAFETY = 0.5 * inch    # Front cover (dust jacket requires 0.5" from trim)

# Flap text safe areas (asymmetric: 0.25" from fold, 0.75" from turn-in)
# Front flap: left=fold, right=turn-in
FRONT_FLAP_SAFE_LEFT = FRONT_FLAP_LEFT + 0.25 * inch
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - 0.75 * inch
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT

# Back flap: left=turn-in, right=fold
BACK_FLAP_SAFE_LEFT = BACK_FLAP_LEFT + 0.75 * inch
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - 0.25 * inch
BACK_FLAP_TEXT_W = BACK_FLAP_SAFE_RIGHT - BACK_FLAP_SAFE_LEFT


def wrap_text(c, text, font_name, font_size, max_width):
    """Wrap text to fit within max_width."""
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
    """Fill entire document with deep midnight blue."""
    c.setFillColor(DEEP_BLUE)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Place cover image on front board area with title overlay."""
    cx = FRONT_CENTER_X

    # --- Place background image ---
    img = ImageReader(str(IMAGE_FILE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = cx - draw_w / 2
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

    # --- Top gradient overlay for title ---
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_COVER_LEFT, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)

    steps = 40
    grad_height = 4.0 * inch
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.5
        c.setFillColor(Color(0.06, 0.08, 0.14, alpha))
        y = DOC_H - (i * grad_height / steps)
        h = grad_height / steps + 1
        c.rect(FRONT_COVER_LEFT, y - h, target_w, h, fill=1, stroke=0)

    c.restoreState()

    # --- Title ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 22)
    c.drawCentredString(cx, DOC_H - 1.5 * inch, "From the")

    c.setFont("EBGaramond", 48)
    c.drawCentredString(cx, DOC_H - 2.2 * inch, "Beginning")

    # --- Subtitle (dark blue for contrast against bright horizon) ---
    c.setFillColor(DEEP_BLUE)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, DOC_H - 2.85 * inch, "The Gospel from the Ground Up")

    # --- Bottom gradient overlay for author ---
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_COVER_LEFT, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)

    bottom_grad_height = 2.0 * inch
    for i in range(steps):
        alpha = 0.5 * (i / steps) ** 1.5
        c.setFillColor(Color(0.06, 0.08, 0.14, alpha))
        y = bottom_grad_height * (1 - i / steps)
        h = bottom_grad_height / steps + 1
        c.rect(FRONT_COVER_LEFT, y - h, target_w, h, fill=1, stroke=0)

    c.restoreState()

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    author_y = TRIM_BOTTOM + SAFETY + 0.2 * inch
    c.drawCentredString(cx, author_y, "P A U L   &   P A M   H A I N L I N E")


def draw_spine(c):
    """Draw spine text. At 0.427" we have room for text."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(0, 3, "From the Beginning")
    c.setFont("EBGaramond", 6.5)
    c.drawCentredString(0, -5.5, "Paul & Pam Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover text on deep midnight blue."""
    safe_left = BACK_COVER_LEFT + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    # --- Opening verse ---
    y = TRIM_TOP - 1.0 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 10)
    verse = "\u201cIn the beginning God created the heavens and the earth.\u201d"
    c.drawCentredString(cx, y, verse)
    y -= 14
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, y, "\u2014 Genesis 1:1")
    y -= 10

    # --- Decorative line ---
    y -= 8
    line_hw = 0.6 * inch
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 20

    # --- Body text ---
    c.setFillColor(CREAM)
    line_height = 13.5

    body_paragraphs = [
        "You don\u2019t need a church background to read this book. You don\u2019t need to know anything about the Bible. You just need to be willing to look.",
        "From the Beginning starts where the Bible starts \u2014 with a God who created you on purpose, who knew you before you were born, and who had a plan for your rescue before the world began. In ten chapters, it walks you through the whole story: who God is, what went wrong, the long thread of promise that runs through Scripture, and the Christ who fulfilled every word of it.",
        "This is not a book of opinions. Every claim is anchored in Scripture. Every chapter builds on the last. And by the end, you\u2019ll understand not just what God did \u2014 but what He asks you to do about it.",
        "If you\u2019ve been looking for the starting line, this is it.",
    ]

    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # --- Attribution ---
    y -= line_height * 0.3
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y, "Scripture quotations from the New American Standard Bible\u00ae (NASB).")


def draw_front_flap(c):
    """Draw front flap text -- book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(CREAM)
    y = TRIM_TOP - SAFETY
    line_height = 11

    paragraphs = [
        ("EBGaramond-Italic", 8.5,
         "From the Beginning is written for two generations \u2014 parents who drifted from faith and stopped reading Scripture, and their children who grew up with little to no knowledge of God."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "Starting from creation and building toward the resurrection, each chapter follows the thread of promise that God wove through centuries of history. No assumptions. No church jargon. Just the story the Bible tells \u2014 told the way Paul told it in Athens, starting from the ground up."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "The tone is conversational \u2014 like sitting across from someone at a coffee shop. The evidence is scriptural. And the invitation is open to anyone willing to look."),
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
    """Draw back flap text -- About the Authors."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(CREAM)

    y = TRIM_TOP - SAFETY
    c.setFont("EBGaramond", 10)
    c.drawString(safe_left, y, "About the Authors")
    y -= 16

    line_height = 10.5

    paragraphs = [
        "Paul and Pam Hainline are students of God\u2019s Word who write from the conviction that Scripture interprets Scripture. Their work is rooted in a desire to point readers back to the biblical text \u2014 not to opinions, traditions, or denominational systems. They are the founders of NobleMind Press (noblemind.study).",
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

    print('Generating IngramSpark HARDCOVER (dust jacket) cover PDF for "From the Beginning"...')
    print(f'  Trim size: 5.5" x 8.5"')
    print(f'  Board size: {BOARD_W}" x {BOARD_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages + board thickness)')
    print(f'  Flap width: {FLAP_W}"')
    print(f'  Bleed (top/bottom): {BLEED}"')
    print(f'  Turn-in (flap edges): {TURN_IN}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("From the Beginning - IngramSpark Hardcover Dust Jacket Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
