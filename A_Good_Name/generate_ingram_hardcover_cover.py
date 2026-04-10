#!/usr/bin/env python3
"""Generate IngramSpark hardcover (dust jacket) cover PDF for Your Name Means Everything: A Good Name.

IngramSpark specs (5.5x8.5 casebound with dust jacket, cream paper, 179 pages):
  Trim size: 5.5" x 8.5"
  Board size: 5.625" x 8.625" (trim + 0.125" on each dimension)
  Spine width: (179 / 444) + 0.08 = 0.483" (cream paper 444 PPI + board thickness)
  Flap width: 3.25" (standard dust jacket flap)
  Bleed: 0.125" on all four sides
  Turn-in: 0.625" on each flap edge
  Total width: 0.125 + 0.625 + 3.25 + 5.625 + 0.483 + 5.625 + 3.25 + 0.625 + 0.125 = 19.733"
  Total height: 0.125 + 8.625 + 0.125 = 8.875"
  Safety margin: 0.25" inside trim for front cover, 0.5" for back cover and flaps
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "YourNameMeansEverything_IngramSpark_Hardcover_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Spine calculation ---
PAGE_COUNT = 179
PPI = 444  # IngramSpark cream paper, B&W
SPINE_W = round(PAGE_COUNT / PPI + 0.08, 3)  # 0.483" (interior + board thickness)

# --- Dust jacket dimensions ---
BOARD_W = 5.625     # inches (trim 5.5 + 0.125)
BOARD_H = 8.625     # inches (trim 8.5 + 0.125)
FLAP_W = 3.25       # inches (standard dust jacket flap)
TURN_IN = 0.625     # inches (turn-in at each flap edge)
BLEED = 0.125       # inches (top and bottom only)
TRIM_W = 5.5        # inches (for reference)
TRIM_H = 8.5        # inches (for reference)

DOC_W = (BLEED + TURN_IN + FLAP_W + BOARD_W + SPINE_W + BOARD_W + FLAP_W + TURN_IN + BLEED) * inch
DOC_H = (BLEED + BOARD_H + BLEED) * inch

# --- Colors ---
NAVY = Color(0.094, 0.125, 0.180)         # #182030 deep navy
GOLD = Color(0.769, 0.663, 0.376)         # #C4A960 warm gold
GOLD_DIM = Color(0.620, 0.545, 0.345)     # dimmer gold for secondary text

# --- Layout positions (from left edge of document) ---
# Layout: turn_in + back_flap + back_board + spine + front_board + front_flap + turn_in

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

# Centers of each panel
BACK_CENTER_X = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# Safety margins
SAFETY = 0.5 * inch          # Back cover, cover panels
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


def draw_short_line(c, cx, y, width=0.6):
    """Draw a small decorative horizontal line."""
    hw = width * inch / 2
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - hw, y, cx + hw, y)


def draw_corner_brackets(c, left, top, right, bottom, size=0.3):
    """Draw thin corner bracket marks."""
    s = size * inch
    c.setStrokeColor(GOLD_DIM)
    c.setLineWidth(0.4)
    c.line(left, top, left + s, top)
    c.line(left, top, left, top - s)
    c.line(right, top, right - s, top)
    c.line(right, top, right, top - s)
    c.line(left, bottom, left + s, bottom)
    c.line(left, bottom, left, bottom + s)
    c.line(right, bottom, right - s, bottom)
    c.line(right, bottom, right, bottom + s)


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
    """Fill entire document with deep navy."""
    c.setFillColor(NAVY)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw front cover — navy/gold design."""
    cx = FRONT_CENTER_X
    safe_top = TRIM_TOP - FRONT_SAFETY
    safe_bottom = TRIM_BOTTOM + FRONT_SAFETY
    safe_left = FRONT_COVER_LEFT + FRONT_SAFETY
    safe_right = FRONT_COVER_RIGHT - FRONT_SAFETY

    # Corner brackets
    draw_corner_brackets(c, safe_left, safe_top, safe_right, safe_bottom)

    # Small cross near top
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    cross_y = DOC_H - 1.6 * inch
    c.line(cx, cross_y + 0.15 * inch, cx, cross_y - 0.15 * inch)
    c.line(cx - 0.1 * inch, cross_y, cx + 0.1 * inch, cross_y)

    # "YOUR" - spaced letters
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 14)
    c.drawCentredString(cx, DOC_H - 2.35 * inch, "Y O U R")

    # "NAME" - large
    c.setFont("EBGaramond", 46)
    c.drawCentredString(cx, DOC_H - 3.0 * inch, "NAME")

    # "MEANS" - spaced letters
    c.setFont("EBGaramond", 14)
    c.drawCentredString(cx, DOC_H - 3.45 * inch, "M E A N S")

    # "EVERYTHING" - large
    c.setFont("EBGaramond", 46)
    c.drawCentredString(cx, DOC_H - 4.1 * inch, "EVERYTHING")

    # Decorative divider — line diamond line
    div_y = DOC_H - 4.55 * inch
    hw = 0.7 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - hw, div_y, cx - 0.08 * inch, div_y)
    c.line(cx + 0.08 * inch, div_y, cx + hw, div_y)
    d = 0.04 * inch
    c.setFillColor(GOLD)
    p = c.beginPath()
    p.moveTo(cx, div_y + d)
    p.lineTo(cx + d, div_y)
    p.lineTo(cx, div_y - d)
    p.lineTo(cx - d, div_y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # "A Good Name" - secondary title
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 18)
    c.drawCentredString(cx, DOC_H - 5.0 * inch, "A Good Name")

    # Tagline
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, DOC_H - 5.55 * inch, "A Straight-Talk Guide for Young Men")
    c.drawCentredString(cx, DOC_H - 5.8 * inch, "Who Want to Matter")

    # Scripture quote near bottom
    quote_y = TRIM_BOTTOM + 1.4 * inch
    draw_short_line(c, cx, quote_y + 0.35 * inch, 0.5)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, quote_y, "\u201cThe fear of the Lord is the beginning of wisdom,")
    c.drawCentredString(cx, quote_y - 0.22 * inch,
                        "and the knowledge of the Holy One is understanding.\u201d")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.55 * inch, "P R O V E R B S  9 : 1 0")


def draw_spine(c):
    """Draw spine text. At 0.483" there's room for text."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 7.5)
    c.drawCentredString(0, 3, "YOUR NAME MEANS EVERYTHING: A GOOD NAME")
    c.setFont("EBGaramond", 6)
    c.drawCentredString(0, -5.5, "Paul & Pam Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover blurb."""
    safe_left = BACK_COVER_LEFT + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    c.setFillColor(GOLD)

    # Short decorative line at top
    draw_short_line(c, cx, DOC_H - 1.8 * inch, 0.5)

    # Opening line — italic
    y = DOC_H - 2.3 * inch
    ls = 17

    c.setFont("EBGaramond-Italic", 11.5)
    c.drawCentredString(cx, y, "Nobody told you this was coming.")
    y -= ls * 1.5

    # Body text
    body_paragraphs = [
        "You are standing at the beginning of your adult life in a world that offers everything except the truth you actually need.",
        "This book is built on the Bible \u2014 not on opinions, not on trends, not on what sounds good at graduation.",
        "It is a straight-talk guide through the questions that will define your life: who you are, who God is, how you treat people, and how you build something that lasts.",
    ]

    c.setFont("EBGaramond", 10.5)
    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10.5, text_width)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= ls
        y -= ls * 0.5

    # Bold tagline
    c.setFont("EBGaramond-Italic", 11.5)
    c.drawCentredString(cx, y, "Thirteen chapters. One Foundation.")
    y -= ls * 1.8

    # Decorative line
    draw_short_line(c, cx, y + 0.1 * inch, 0.35)
    y -= ls * 0.8

    # Scripture quote
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, y, "\u201cChoose for yourselves today")
    y -= ls
    c.drawCentredString(cx, y, "whom you will serve . . .")
    y -= ls
    c.drawCentredString(cx, y, "but as for me and my house,")
    y -= ls
    c.drawCentredString(cx, y, "we will serve the Lord.\u201d")
    y -= ls * 1.2

    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, y, "J O S H U A  2 4 : 1 5")

    # Author at bottom (left side, leaving room for barcode on right)
    c.setFont("EBGaramond", 9)
    c.drawString(safe_left, TRIM_BOTTOM + SAFETY,
                 "P A U L  &  P A M  H A I N L I N E")

    # --- ISBN Barcode (bottom-right of back cover) ---
    barcode_w = 2.0 * inch
    barcode_h = 1.2 * inch
    barcode_x = safe_right - barcode_w
    barcode_y = TRIM_BOTTOM + SAFETY - 0.15 * inch

    c.setFillColor(white)
    c.rect(barcode_x, barcode_y, barcode_w, barcode_h, fill=1, stroke=0)

    barcode_img = str(BOOK_DIR / "barcode_978-8-9954288-1-7.png")
    c.drawImage(barcode_img, barcode_x + 0.1 * inch, barcode_y + 0.1 * inch,
                width=barcode_w - 0.2 * inch, height=barcode_h - 0.2 * inch,
                preserveAspectRatio=True, anchor='c')


def draw_front_flap(c):
    """Draw front flap text — book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(GOLD)

    y = TRIM_TOP - SAFETY
    line_height = 11

    paragraphs = [
        ("EBGaramond-Italic", 8.5,
         "Your Name Means Everything: A Good Name is a straight-talk guide for young men navigating the years that will shape the rest of their lives."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "In thirteen chapters anchored entirely in Scripture, Paul and Pam Hainline address the questions no one else is answering honestly: identity, integrity, purity, friendship, money, marriage, and what it means to build a life on the only foundation that lasts."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "This is not a book of opinions. It is a book of Scripture \u2014 letting God\u2019s Word speak for itself to a generation that has rarely heard it."),
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
    """Draw back flap text — About the Authors."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(GOLD)

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

    print('Generating IngramSpark HARDCOVER (dust jacket) cover PDF...')
    print(f'  Title: Your Name Means Everything: A Good Name')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Board size: {BOARD_W}" x {BOARD_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages, cream {PPI} PPI + board)')
    print(f'  Flap width: {FLAP_W}"')
    print(f'  Bleed (top/bottom): {BLEED}"')
    print(f'  Turn-in (flap edges): {TURN_IN}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Your Name Means Everything: A Good Name - IngramSpark Hardcover Dust Jacket")

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
