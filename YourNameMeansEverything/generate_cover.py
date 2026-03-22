#!/usr/bin/env python3
"""Generate Lulu-ready dust jacket cover PDF for Your Name Means Everything: A Good Name.

Template specs (from Lulu for 5.5x8.5 hardcover with flaps, 179 pages):
  Total document size (with bleed): 19.438" x 9.25"
  Spine width: 0.688" (page count: 179)
  Book cover size (with bleed): 5.75" x 8.75"
  Book trim size: 5.5" x 8.5"
  Bleed area: 0.25"
  Safety margin: 0.5"
  Flap dimension: 3.25" x 8.5"
  Flap live area: 2.25" x 7.75"
  Flap fold width: 0.25"
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "YourNameMeansEverything_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions ---
DOC_W = 19.438 * inch
DOC_H = 9.25 * inch

# --- Colors ---
NAVY = Color(0.094, 0.125, 0.180)         # #182030 deep navy (matching original)
GOLD = Color(0.769, 0.663, 0.376)         # #C4A960 warm gold
GOLD_DIM = Color(0.620, 0.545, 0.345)     # dimmer gold for secondary text

# --- Layout positions ---
FLAP_FOLD = 0.3125 * inch   # tuned value

# Zone boundaries (from left)
BACK_FLAP_LEFT = FLAP_FOLD
BACK_FLAP_RIGHT = FLAP_FOLD + 3.25 * inch

BACK_COVER_LEFT = BACK_FLAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + 5.75 * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + 0.688 * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + 5.75 * inch

FRONT_FLAP_LEFT = FRONT_COVER_RIGHT
FRONT_FLAP_RIGHT = FRONT_FLAP_LEFT + 3.25 * inch

# Trim edges (0.125" inside bleed)
COVER_BLEED = 0.125 * inch

FRONT_TRIM_LEFT = FRONT_COVER_LEFT + COVER_BLEED
FRONT_TRIM_RIGHT = FRONT_COVER_RIGHT - COVER_BLEED
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

BACK_TRIM_LEFT = BACK_COVER_LEFT + COVER_BLEED
BACK_TRIM_RIGHT = BACK_COVER_RIGHT - COVER_BLEED
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

# Flap centers
BACK_FLAP_CENTER_X = (BACK_FLAP_LEFT + BACK_FLAP_RIGHT) / 2
FRONT_FLAP_CENTER_X = (FRONT_FLAP_LEFT + FRONT_FLAP_RIGHT) / 2

# Vertical
V_BLEED = 0.25 * inch
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

SAFETY = 0.5 * inch


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
    # Top-left
    c.line(left, top, left + s, top)
    c.line(left, top, left, top - s)
    # Top-right
    c.line(right, top, right - s, top)
    c.line(right, top, right, top - s)
    # Bottom-left
    c.line(left, bottom, left + s, bottom)
    c.line(left, bottom, left, bottom + s)
    # Bottom-right
    c.line(right, bottom, right - s, bottom)
    c.line(right, bottom, right, bottom + s)


def draw_background(c):
    """Fill entire document with deep navy."""
    c.setFillColor(NAVY)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw front cover — matching original navy/gold design with 'A Good Name' added."""
    cx = FRONT_CENTER_X
    safe_top = TRIM_TOP - SAFETY
    safe_bottom = TRIM_BOTTOM + SAFETY
    safe_left = FRONT_TRIM_LEFT + SAFETY
    safe_right = FRONT_TRIM_RIGHT - SAFETY

    # Corner brackets around the front cover safe area
    draw_corner_brackets(c, safe_left, safe_top, safe_right, safe_bottom)

    # Small cross near top
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    cross_y = DOC_H - 1.8 * inch
    c.line(cx, cross_y + 0.15 * inch, cx, cross_y - 0.15 * inch)  # vertical
    c.line(cx - 0.1 * inch, cross_y, cx + 0.1 * inch, cross_y)     # horizontal

    # "YOUR" - spaced letters
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 14)
    c.drawCentredString(cx, DOC_H - 2.55 * inch, "Y O U R")

    # "NAME" - large
    c.setFont("EBGaramond", 46)
    c.drawCentredString(cx, DOC_H - 3.2 * inch, "NAME")

    # "MEANS" - spaced letters
    c.setFont("EBGaramond", 14)
    c.drawCentredString(cx, DOC_H - 3.65 * inch, "M E A N S")

    # "EVERYTHING" - large
    c.setFont("EBGaramond", 46)
    c.drawCentredString(cx, DOC_H - 4.3 * inch, "EVERYTHING")

    # Decorative divider — line diamond line
    div_y = DOC_H - 4.75 * inch
    hw = 0.7 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - hw, div_y, cx - 0.08 * inch, div_y)
    c.line(cx + 0.08 * inch, div_y, cx + hw, div_y)
    # Small diamond
    d = 0.04 * inch
    c.setFillColor(GOLD)
    p = c.beginPath()
    p.moveTo(cx, div_y + d)
    p.lineTo(cx + d, div_y)
    p.lineTo(cx, div_y - d)
    p.lineTo(cx - d, div_y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # "A Good Name" - secondary title (NEW)
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 18)
    c.drawCentredString(cx, DOC_H - 5.2 * inch, "A Good Name")

    # Tagline
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, DOC_H - 5.75 * inch, "A Straight-Talk Guide for Young Men")
    c.drawCentredString(cx, DOC_H - 6.0 * inch, "Who Want to Matter")

    # Scripture quote near bottom
    quote_y = TRIM_BOTTOM + 1.5 * inch
    draw_short_line(c, cx, quote_y + 0.35 * inch, 0.5)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, quote_y, "\u201cThe fear of the Lord is the beginning of wisdom,")
    c.drawCentredString(cx, quote_y - 0.22 * inch,
                        "and the knowledge of the Holy One is understanding.\u201d")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.55 * inch, "P R O V E R B S  9 : 1 0")


def draw_spine(c):
    """Draw spine text."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 10)
    c.drawCentredString(0, 0, "YOUR NAME MEANS EVERYTHING: A GOOD NAME")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover blurb — matching original style."""
    cx = BACK_CENTER_X

    c.setFillColor(GOLD)

    # Short decorative line at top
    draw_short_line(c, cx, DOC_H - 2.0 * inch, 0.5)

    # Opening line — italic
    y = DOC_H - 2.5 * inch
    ls = 17  # line spacing

    c.setFont("EBGaramond-Italic", 11.5)
    c.drawCentredString(cx, y, "Nobody told you this was coming.")
    y -= ls * 1.5

    # Body text
    c.setFont("EBGaramond", 10.5)
    body_lines = [
        "You are standing at the beginning of your",
        "adult life in a world that offers everything",
        "except the truth you actually need.",
    ]
    for line in body_lines:
        c.drawCentredString(cx, y, line)
        y -= ls
    y -= ls * 0.5

    c.drawCentredString(cx, y, "This book is built on the Bible \u2014 not on")
    y -= ls
    c.drawCentredString(cx, y, "opinions, not on trends, not on what sounds")
    y -= ls
    c.drawCentredString(cx, y, "good at graduation.")
    y -= ls * 1.3

    c.drawCentredString(cx, y, "It is a straight-talk guide through the questions")
    y -= ls
    c.drawCentredString(cx, y, "that will define your life: who you are, who God")
    y -= ls
    c.drawCentredString(cx, y, "is, how you treat people, and how you build")
    y -= ls
    c.drawCentredString(cx, y, "something that lasts.")
    y -= ls * 1.5

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

    # Author at bottom
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.2 * inch,
                        "P A U L  &  P A M  H A I N L I N E")


def draw_back_flap(c):
    """Draw back flap — dedication/personal note."""
    cx = BACK_FLAP_CENTER_X

    c.setFillColor(GOLD)

    # Short decorative line
    draw_short_line(c, cx, DOC_H - 2.6 * inch, 0.4)

    y = DOC_H - 3.1 * inch
    ls = 15

    c.setFont("EBGaramond-Italic", 9.5)
    lines = [
        "This book was written by",
        "grandparents who believe the",
        "most important gift they can",
        "leave the next generation",
        "is not wealth, not comfort,",
        "and not advice \u2014 but the",
        "Word of God and the courage",
        "to build a life on it.",
    ]
    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= ls

    y -= ls * 0.8
    c.setFont("EBGaramond-Italic", 9)
    c.drawCentredString(cx, y, "\u201cA righteous man who walks")
    y -= ls
    c.drawCentredString(cx, y, "in his integrity \u2014 how blessed")
    y -= ls
    c.drawCentredString(cx, y, "are his sons after him.\u201d")
    y -= ls * 1.2

    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, y, "Proverbs 20:7")


def draw_front_flap(c):
    """Draw front flap — book description."""
    cx = FRONT_FLAP_CENTER_X

    c.setFillColor(GOLD)

    # Short decorative line
    draw_short_line(c, cx, DOC_H - 2.6 * inch, 0.4)

    y = DOC_H - 3.1 * inch
    ls = 15

    c.setFont("EBGaramond-Italic", 9.5)
    lines = [
        "Your name is the one thing",
        "you will carry for the rest",
        "of your life. It will open",
        "doors or close them. It will",
        "precede you into every room",
        "and linger after you leave.",
    ]
    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= ls

    y -= ls * 0.8
    c.setFont("EBGaramond", 9.5)
    lines2 = [
        "This book was written for the",
        "young man who wants to build",
        "something real \u2014 and is willing",
        "to hear the truth about what",
        "that requires.",
    ]
    for line in lines2:
        c.drawCentredString(cx, y, line)
        y -= ls

    y -= ls * 0.8
    c.setFont("EBGaramond-Italic", 9.5)
    c.drawCentredString(cx, y, "Grounded in Scripture.")
    y -= ls
    c.drawCentredString(cx, y, "Built for the road ahead.")


def main():
    print("Generating Lulu dust jacket cover PDF...")
    print(f'  Document size: 19.438" x 9.25"')
    print(f'  Spine width: 0.688"')
    print(f"  Page count: 179")

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Your Name Means Everything: A Good Name - Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_back_flap(c)
    draw_front_flap(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
