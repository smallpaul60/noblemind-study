#!/usr/bin/env python3
"""Generate Lulu-ready dust jacket cover PDF for Strength and Dignity.

Template specs (from Lulu template for 5.5x8.5 hardcover with flaps, 157 pages):
  Total document size (with bleed): 19.375" x 9.25"
  Book cover size (with bleed): 5.75" x 8.75"
  Book trim size: 5.5" x 8.5"
  Spine width: 0.625" (page count: 157)
  Bleed area: 0.25"
  Safety margin: 0.5"
  Flap dimension: 3.25" x 8.5"
  Flap live area: 2.25" x 7.75"
  Fold safety margin: 0.25"
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Strength_and_Dignity_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions ---
DOC_W = 19.375 * inch
DOC_H = 9.25 * inch

# --- Colors ---
DEEP_ROSE = Color(0.235, 0.082, 0.145)   # #3C1525 deep burgundy-rose
CREAM = Color(0.957, 0.922, 0.855)        # #F4EBDA warm cream
GOLD_ACCENT = Color(0.769, 0.663, 0.306)  # #C4A94E warm gold (for subtle accents)

# --- Layout positions (from left edge of document) ---
FLAP_FOLD = 0.3125 * inch   # tuned value (same as Character book)

# Zone boundaries (from left)
BACK_FLAP_LEFT = FLAP_FOLD
BACK_FLAP_RIGHT = FLAP_FOLD + 3.25 * inch

BACK_COVER_LEFT = BACK_FLAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + 5.75 * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + 0.625 * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + 5.75 * inch

FRONT_FLAP_LEFT = FRONT_COVER_RIGHT
FRONT_FLAP_RIGHT = FRONT_FLAP_LEFT + 3.25 * inch

# Trim edges (0.125" inside bleed on each side of cover panels)
COVER_BLEED = 0.125 * inch

FRONT_TRIM_LEFT = FRONT_COVER_LEFT + COVER_BLEED
FRONT_TRIM_RIGHT = FRONT_COVER_RIGHT - COVER_BLEED
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

BACK_TRIM_LEFT = BACK_COVER_LEFT + COVER_BLEED
BACK_TRIM_RIGHT = BACK_COVER_RIGHT - COVER_BLEED
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

# Vertical (bleed is 0.25" top and bottom)
V_BLEED = 0.25 * inch
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_HEIGHT = TRIM_TOP - TRIM_BOTTOM
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

# Safety margin: 0.5" inside trim
SAFETY = 0.5 * inch


def draw_background(c):
    """Fill entire document with deep burgundy-rose."""
    c.setFillColor(DEEP_ROSE)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw front cover text."""
    cx = FRONT_CENTER_X

    # Decorative line above title
    c.setStrokeColor(CREAM)
    c.setLineWidth(0.5)
    line_w = 1.5 * inch
    c.line(cx - line_w / 2, DOC_H - 2.2 * inch, cx + line_w / 2, DOC_H - 2.2 * inch)

    # Series title - "YOUR NAME"
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 28)
    c.drawCentredString(cx, DOC_H - 2.85 * inch, "YOUR NAME")

    # Series title line 2 - "MEANS EVERYTHING"
    c.setFont("EBGaramond", 28)
    c.drawCentredString(cx, DOC_H - 3.3 * inch, "MEANS EVERYTHING")

    # Decorative line between title and subtitle
    c.setStrokeColor(CREAM)
    c.setLineWidth(0.5)
    c.line(cx - line_w / 2, DOC_H - 3.65 * inch, cx + line_w / 2, DOC_H - 3.65 * inch)

    # Volume subtitle - "Strength and Dignity"
    c.setFont("EBGaramond-Italic", 18)
    c.drawCentredString(cx, DOC_H - 4.1 * inch, "Strength and Dignity")

    # Tagline line 1
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(cx, DOC_H - 4.8 * inch, "What the Bible Says to Young Women")

    # Tagline line 2
    c.drawCentredString(cx, DOC_H - 5.05 * inch, "About Character, Wisdom, and Faith")

    # Decorative line above author
    c.line(cx - line_w / 2, DOC_H - 5.55 * inch, cx + line_w / 2, DOC_H - 5.55 * inch)

    # Author name
    c.setFont("EBGaramond", 17)
    c.drawCentredString(cx, DOC_H - 6.0 * inch, "Paul & Pam Hainline")


def draw_spine(c):
    """Draw spine text (rotated, reading top to bottom when book is upright)."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(0, 0, "YOUR NAME MEANS EVERYTHING: STRENGTH AND DIGNITY")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover blurb."""
    cx = BACK_CENTER_X
    safe_left = BACK_TRIM_LEFT + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY

    c.setFillColor(CREAM)

    lines = [
        ("EBGaramond-Italic", 12, "Nobody told you this was coming."),
        (None, 0, ""),
        ("EBGaramond", 10.5, "One day you\u2019re watching the clock in a classroom."),
        ("EBGaramond", 10.5, "The next, the world steps back and says \u2014"),
        ("EBGaramond-Italic", 10.5, "your turn."),
        (None, 0, ""),
        ("EBGaramond", 10.5, "The decisions are real now. And the voices competing"),
        ("EBGaramond", 10.5, "for your attention have never been louder."),
        (None, 0, ""),
        ("EBGaramond", 10.5, "Your Name Means Everything: Strength and Dignity"),
        ("EBGaramond", 10.5, "is a straight-talk guide rooted in Scripture for"),
        ("EBGaramond", 10.5, "young women stepping into adulthood. Through thirteen"),
        ("EBGaramond", 10.5, "chapters, it walks through the things that matter most \u2014"),
        ("EBGaramond", 10.5, "identity, character, purpose, relationships, work,"),
        ("EBGaramond", 10.5, "money, and faith \u2014 not with opinions or platitudes,"),
        ("EBGaramond", 10.5, "but with what God\u2019s Word actually says."),
        (None, 0, ""),
        ("EBGaramond", 10.5, "From Ruth\u2019s loyalty to Rahab\u2019s courage to the"),
        ("EBGaramond", 10.5, "Proverbs 31 woman who clothed herself in strength"),
        ("EBGaramond", 10.5, "and dignity and smiled at the future \u2014 this book"),
        ("EBGaramond", 10.5, "shows what it looks like to build a life and a name"),
        ("EBGaramond", 10.5, "that will outlast you."),
    ]

    y = DOC_H - 2.0 * inch
    line_spacing = 16

    for font, size, text in lines:
        if font is None:
            y -= line_spacing * 0.7
            continue
        c.setFont(font, size)
        c.drawCentredString(cx, y, text)
        y -= line_spacing

    # Scripture quote near bottom
    y -= line_spacing * 0.5
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, y, "\u201cA good name is to be more desired than great wealth;")
    y -= line_spacing
    c.drawCentredString(cx, y, "favor is better than silver and gold.\u201d")
    y -= line_spacing
    c.setFont("EBGaramond", 9.5)
    c.drawCentredString(cx, y, "\u2014 Proverbs 22:1")


def main():
    print("Generating Lulu dust jacket cover PDF...")
    print(f'  Document size: 19.375" x 9.25"')
    print(f'  Spine width: 0.625"')
    print(f"  Page count: 157")

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
