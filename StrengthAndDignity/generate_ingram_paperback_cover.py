#!/usr/bin/env python3
"""Generate IngramSpark paperback cover PDF for Strength and Dignity.

IngramSpark specs (5.5x8.5 paperback, cream paper, 157 pages):
  Trim size: 5.5" x 8.5"
  Spine width: 157 / 444 = 0.354" (B&W on cream 444 PPI)
  Bleed: 0.125" on all sides
  Total document size: 11.604" x 8.75"
  Safety margin: 0.25" inside trim on all sides
  Barcode area: ~2" x 1.2" bottom-right of back cover (placeholder until ISBN assigned)
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Strength_and_Dignity_IngramSpark_Paperback_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Spine calculation ---
PAGE_COUNT = 157
PPI = 444  # IngramSpark cream paper, B&W
SPINE_W = PAGE_COUNT / PPI  # 0.3536 inches

# --- Document dimensions ---
BLEED = 0.125  # inches
TRIM_W = 5.5   # inches
TRIM_H = 8.5   # inches

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H = (BLEED + TRIM_H + BLEED) * inch

# --- Colors ---
DEEP_ROSE = Color(0.235, 0.082, 0.145)   # #3C1525 deep burgundy-rose
CREAM = Color(0.957, 0.922, 0.855)        # #F4EBDA warm cream
GOLD_ACCENT = Color(0.769, 0.663, 0.306)  # #C4A94E warm gold

# --- Layout positions (from left edge of document) ---
BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = (BLEED + TRIM_W) * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

# Trim edges
BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = BACK_COVER_RIGHT
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = FRONT_COVER_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# Vertical
TRIM_TOP = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch
COVER_CENTER_Y = DOC_H / 2

# Safety margin
SAFETY = 0.25 * inch


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

    # Series title - "YOUR NAME"
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 28)
    c.drawCentredString(cx, DOC_H - 2.65 * inch, "YOUR NAME")

    # Series title line 2 - "MEANS EVERYTHING"
    c.setFont("EBGaramond", 28)
    c.drawCentredString(cx, DOC_H - 3.1 * inch, "MEANS EVERYTHING")

    # Decorative line between title and subtitle
    c.setStrokeColor(CREAM)
    c.setLineWidth(0.5)
    c.line(cx - line_w / 2, DOC_H - 3.45 * inch, cx + line_w / 2, DOC_H - 3.45 * inch)

    # Volume subtitle - "Strength and Dignity"
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
    c.setLineWidth(0.5)
    c.line(cx - 0.3 * inch, quote_y + 0.35 * inch, cx + 0.3 * inch, quote_y + 0.35 * inch)
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, quote_y, "\u201cStrength and dignity are her clothing,")
    c.drawCentredString(cx, quote_y - 0.2 * inch, "and she smiles at the future.\u201d")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.5 * inch, "P R O V E R B S  3 1 : 2 5")


def draw_spine(c):
    """Draw spine text."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 7.5)
    c.drawCentredString(0, 0, "YOUR NAME MEANS EVERYTHING: STRENGTH AND DIGNITY")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover blurb with barcode placeholder."""
    cx = BACK_CENTER_X
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

    c.setFont("EBGaramond", 10.5)
    body = [
        "The decisions are real now. And the voices competing",
        "for your attention have never been louder.",
    ]
    for line in body:
        c.drawCentredString(cx, y, line)
        y -= ls
    y -= ls * 0.5

    body2 = [
        "Your Name Means Everything: Strength and Dignity",
        "is a straight-talk guide rooted in Scripture for",
        "young women stepping into adulthood. Through thirteen",
        "chapters, it walks through the things that matter most \u2014",
        "identity, character, purpose, relationships, work,",
        "money, and faith \u2014 not with opinions or platitudes,",
        "but with what God\u2019s Word actually says.",
    ]
    for line in body2:
        c.drawCentredString(cx, y, line)
        y -= ls
    y -= ls * 0.5

    body3 = [
        "From Ruth\u2019s loyalty to Rahab\u2019s courage to the",
        "Proverbs 31 woman who clothed herself in strength",
        "and dignity and smiled at the future \u2014 this book",
        "shows what it looks like to build a life and a name",
        "that will outlast you.",
    ]
    for line in body3:
        c.drawCentredString(cx, y, line)
        y -= ls
    y -= ls * 0.8

    # Scripture
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, y, "\u201cA good name is to be more desired than great wealth;")
    y -= ls
    c.drawCentredString(cx, y, "favor is better than silver and gold.\u201d")
    y -= ls
    c.setFont("EBGaramond", 9.5)
    c.drawCentredString(cx, y, "\u2014 Proverbs 22:1")

    # --- ISBN Barcode (bottom-right of back cover) ---
    barcode_w = 2.0 * inch
    barcode_h = 1.2 * inch
    barcode_x = BACK_TRIM_RIGHT - SAFETY - barcode_w
    barcode_y = TRIM_BOTTOM + 0.35 * inch

    # White background behind barcode
    c.setFillColor(white)
    c.rect(barcode_x, barcode_y, barcode_w, barcode_h, fill=1, stroke=0)

    # Draw barcode image
    barcode_img = str(BOOK_DIR / "barcode_978-8-9954288-2-4.png")
    c.drawImage(barcode_img, barcode_x + 0.1 * inch, barcode_y + 0.1 * inch,
                width=barcode_w - 0.2 * inch, height=barcode_h - 0.2 * inch,
                preserveAspectRatio=True, anchor='c')


def main():
    spine_str = f"{SPINE_W:.3f}"
    doc_w_str = f"{DOC_W / inch:.3f}"
    print("Generating IngramSpark paperback cover PDF...")
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {spine_str}" ({PAGE_COUNT} pages, cream {PPI} PPI)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_str}" x {DOC_H / inch:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Your Name Means Everything: Strength and Dignity - IngramSpark Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
