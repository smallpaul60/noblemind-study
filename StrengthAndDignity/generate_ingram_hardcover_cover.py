#!/usr/bin/env python3
"""Generate IngramSpark hardcover (dust jacket) cover PDF for Strength and Dignity.

IngramSpark specs (5.5x8.5 casebound with dust jacket, cream paper, 157 pages):
  Trim size: 5.5" x 8.5"
  Board size: 5.625" x 8.625" (trim + 0.125" on each dimension)
  Spine width: (157 / 444) + 0.08 = 0.434" (cream paper 444 PPI + board thickness)
  Flap width: 3.25" (standard dust jacket flap)
  Bleed: 0.125" on all four sides
  Turn-in: 0.625" on each flap edge
  Total width: 0.125 + 0.625 + 3.25 + 5.625 + 0.434 + 5.625 + 3.25 + 0.625 + 0.125 = 19.684"
  Total height: 0.125 + 8.625 + 0.125 = 8.875"
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Strength_and_Dignity_IngramSpark_Hardcover_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Spine calculation ---
PAGE_COUNT = 157
PPI = 444  # IngramSpark cream paper, B&W
SPINE_W = round(PAGE_COUNT / PPI + 0.08, 3)  # 0.434"

# --- Dust jacket dimensions ---
BOARD_W = 5.625     # inches (trim 5.5 + 0.125)
BOARD_H = 8.625     # inches (trim 8.5 + 0.125)
FLAP_W = 3.25       # inches (standard dust jacket flap)
TURN_IN = 0.625     # inches (turn-in at each flap edge)
BLEED = 0.125       # inches (top and bottom only)
TRIM_W = 5.5
TRIM_H = 8.5

DOC_W = (BLEED + TURN_IN + FLAP_W + BOARD_W + SPINE_W + BOARD_W + FLAP_W + TURN_IN + BLEED) * inch
DOC_H = (BLEED + BOARD_H + BLEED) * inch

# --- Colors ---
DEEP_ROSE = Color(0.235, 0.082, 0.145)   # #3C1525 deep burgundy-rose
CREAM = Color(0.957, 0.922, 0.855)        # #F4EBDA warm cream
GOLD_ACCENT = Color(0.769, 0.663, 0.306)  # #C4A94E warm gold

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
    """Fill entire document with deep burgundy-rose."""
    c.setFillColor(DEEP_ROSE)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw front cover text."""
    cx = FRONT_CENTER_X
    line_w = 1.5 * inch

    # Decorative line above title
    c.setStrokeColor(CREAM)
    c.setLineWidth(0.5)
    c.line(cx - line_w / 2, DOC_H - 2.0 * inch, cx + line_w / 2, DOC_H - 2.0 * inch)

    # Series title
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 28)
    c.drawCentredString(cx, DOC_H - 2.65 * inch, "YOUR NAME")
    c.drawCentredString(cx, DOC_H - 3.1 * inch, "MEANS EVERYTHING")

    # Decorative line between title and subtitle
    c.line(cx - line_w / 2, DOC_H - 3.45 * inch, cx + line_w / 2, DOC_H - 3.45 * inch)

    # Volume subtitle
    c.setFont("EBGaramond-Italic", 18)
    c.drawCentredString(cx, DOC_H - 3.9 * inch, "Strength and Dignity")

    # Tagline
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(cx, DOC_H - 4.6 * inch, "What the Bible Says to Young Women")
    c.drawCentredString(cx, DOC_H - 4.85 * inch, "About Character, Wisdom, and Faith")

    # Decorative line above author
    c.line(cx - line_w / 2, DOC_H - 5.35 * inch, cx + line_w / 2, DOC_H - 5.35 * inch)

    # Author name
    c.setFont("EBGaramond", 17)
    c.drawCentredString(cx, DOC_H - 5.8 * inch, "Paul & Pam Hainline")

    # Scripture near bottom
    quote_y = TRIM_BOTTOM + 1.3 * inch
    c.setStrokeColor(CREAM)
    c.line(cx - 0.3 * inch, quote_y + 0.35 * inch, cx + 0.3 * inch, quote_y + 0.35 * inch)
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, quote_y, "\u201cStrength and dignity are her clothing,")
    c.drawCentredString(cx, quote_y - 0.2 * inch, "and she smiles at the future.\u201d")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.5 * inch, "P R O V E R B S  3 1 : 2 5")


def draw_spine(c):
    """Draw spine text. At 0.434" there's room for text."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 7)
    c.drawCentredString(0, 3, "YOUR NAME MEANS EVERYTHING: STRENGTH AND DIGNITY")
    c.setFont("EBGaramond", 6)
    c.drawCentredString(0, -5, "Paul & Pam Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover blurb."""
    safe_left = BACK_COVER_LEFT + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2
    ls = 16

    c.setFillColor(CREAM)

    # Opening
    y = DOC_H - 1.8 * inch
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(cx, y, "Nobody told you this was coming.")
    y -= ls * 1.5

    c.setFont("EBGaramond", 10.5)
    lines = [
        "One day you\u2019re watching the clock in a classroom.",
        "The next, the world steps back and says \u2014",
    ]
    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= ls
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, y, "your turn.")
    y -= ls * 1.3

    body_paragraphs = [
        "The decisions are real now. And the voices competing for your attention have never been louder.",
        "Your Name Means Everything: Strength and Dignity is a straight-talk guide rooted in Scripture for young women stepping into adulthood. Through thirteen chapters, it walks through the things that matter most \u2014 identity, character, purpose, relationships, work, money, and faith \u2014 not with opinions or platitudes, but with what God\u2019s Word actually says.",
        "From Ruth\u2019s loyalty to Rahab\u2019s courage to the Proverbs 31 woman who clothed herself in strength and dignity and smiled at the future \u2014 this book shows what it looks like to build a life and a name that will outlast you.",
    ]

    c.setFont("EBGaramond", 10.5)
    for para in body_paragraphs:
        wrapped = wrap_text(c, para, "EBGaramond", 10.5, text_width)
        for line in wrapped:
            c.drawCentredString(cx, y, line)
            y -= ls
        y -= ls * 0.5

    # Scripture
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, y, "\u201cA good name is to be more desired than great wealth;")
    y -= ls
    c.drawCentredString(cx, y, "favor is better than silver and gold.\u201d")
    y -= ls
    c.setFont("EBGaramond", 9.5)
    c.drawCentredString(cx, y, "\u2014 Proverbs 22:1")

    # Author at bottom left
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

    barcode_img = str(BOOK_DIR / "barcode_978-8-9954288-3-1.png")
    c.drawImage(barcode_img, barcode_x + 0.1 * inch, barcode_y + 0.1 * inch,
                width=barcode_w - 0.2 * inch, height=barcode_h - 0.2 * inch,
                preserveAspectRatio=True, anchor='c')


def draw_front_flap(c):
    """Draw front flap text — book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(CREAM)
    y = TRIM_TOP - SAFETY
    line_height = 11

    paragraphs = [
        ("EBGaramond-Italic", 8.5,
         "Strength and Dignity is written for a young woman standing at the threshold of adulthood \u2014 facing real decisions with very little honest guidance rooted in God\u2019s Word."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "Through thirteen chapters built entirely on Scripture, Paul and Pam Hainline address the questions that will define a young woman\u2019s life: who she is, what she\u2019s worth, how she treats people, and how she builds something that lasts."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "Not with opinions. Not with trends. With what God actually says \u2014 and the examples of women in Scripture who lived it."),
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

    print('Generating IngramSpark HARDCOVER (dust jacket) cover PDF...')
    print(f'  Title: Your Name Means Everything: Strength and Dignity')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Board size: {BOARD_W}" x {BOARD_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages, cream {PPI} PPI + board)')
    print(f'  Flap width: {FLAP_W}"')
    print(f'  Bleed (top/bottom): {BLEED}"')
    print(f'  Turn-in (flap edges): {TURN_IN}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Your Name Means Everything: Strength and Dignity - IngramSpark Hardcover Dust Jacket")

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
