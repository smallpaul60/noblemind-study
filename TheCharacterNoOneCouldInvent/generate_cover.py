#!/usr/bin/env python3
"""Generate Lulu-ready cover PDF for The Character No One Could Invent.

Template specs (from Lulu template for 5.5x8.5 hardcover with flaps, 164 pages):
  Total document size (with bleed): 19.375" x 9.25"
  Book cover size (with bleed): 5.75" x 8.75"
  Book trim size: 5.5" x 8.5"
  Spine width: 0.625" (page count: 164)
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
OUTPUT = BOOK_DIR / "The_Character_No_One_Could_Invent_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (from Lulu's actual requirements) ---
DOC_W = 19.438 * inch
DOC_H = 9.25 * inch

# --- Colors ---
NAVY = Color(0.035, 0.082, 0.145)    # ~#091528 deep navy
GOLD = Color(0.769, 0.663, 0.306)    # ~#C4A94E warm gold

# --- Layout positions (from left edge of document) ---
# Layout: flap_fold(0.25) + flap(3.25) + back_cover_w_bleed + spine(0.688) + front_cover_w_bleed + flap(3.25) + flap_fold(0.25)
# Back/front cover with bleed = (19.438 - 0.25*2 - 3.25*2 - 0.688) / 2 = 5.75"
FLAP_FOLD = 0.3125 * inch

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
COVER_HEIGHT = TRIM_TOP - TRIM_BOTTOM  # 8.75"
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

# Safety margin: 0.5" inside trim
SAFETY = 0.5 * inch


def draw_background(c):
    """Fill entire document with dark navy."""
    c.setFillColor(NAVY)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw front cover text."""
    # Center of the front cover trim area (between trim edges, not bleed)
    cx = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

    # Title - "THE CHARACTER"
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 26)
    c.drawCentredString(cx, DOC_H - 2.8 * inch, "THE CHARACTER")

    # Title line 2 - "NO ONE COULD INVENT"
    c.setFont("EBGaramond", 26)
    c.drawCentredString(cx, DOC_H - 3.25 * inch, "NO ONE COULD INVENT")

    # Subtitle line 1
    c.setFont("EBGaramond-Italic", 15)
    c.drawCentredString(cx, DOC_H - 4.0 * inch, "The Evidence of Jesus\u2019 Deity")

    # Subtitle line 2
    c.setFont("EBGaramond-Italic", 15)
    c.drawCentredString(cx, DOC_H - 4.35 * inch, "in the Portrait Itself")

    # Author name
    c.setFont("EBGaramond", 17)
    c.drawCentredString(cx, DOC_H - 5.6 * inch, "Paul Hainline")


def draw_spine(c):
    """Draw spine text (rotated, reading top to bottom when book is upright)."""
    c.saveState()
    # Spine text reads from top to bottom (rotate -90 / 270 degrees)
    # Position at spine center
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)  # Rotates so text reads top-to-bottom (standard for spines)

    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 11)
    c.drawCentredString(0, 0, "THE CHARACTER NO ONE COULD INVENT")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover text."""
    cx = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2
    safe_left = BACK_TRIM_LEFT + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left

    c.setFillColor(GOLD)

    # Back cover blurb - centered paragraphs
    lines = [
        ("EBGaramond", 11, "What if the strongest evidence for who Jesus was"),
        ("EBGaramond", 11, "isn\u2019t found in miracles or prophecy \u2014"),
        ("EBGaramond", 11, "but in the man Himself?"),
        (None, 0, ""),  # spacer
        ("EBGaramond", 10.5, "The four Gospels present a character so consistent,"),
        ("EBGaramond", 10.5, "so original, and so far above His biographers that"),
        ("EBGaramond", 10.5, "no human explanation accounts for Him. The men who"),
        ("EBGaramond", 10.5, "wrote about Jesus misunderstood Him, feared when He"),
        ("EBGaramond", 10.5, "was calm, and fled when He stood firm. Yet somehow"),
        ("EBGaramond", 10.5, "they produced a portrait no dramatist has ever matched."),
        (None, 0, ""),  # spacer
        ("EBGaramond", 10.5, "This book examines Jesus from every angle \u2014 as a"),
        ("EBGaramond", 10.5, "literary creation, a mythological figure, a product of"),
        ("EBGaramond", 10.5, "His culture, a teacher, a reformer \u2014 and demonstrates"),
        ("EBGaramond", 10.5, "that He fails every test for human invention. He violates"),
        ("EBGaramond", 10.5, "the laws of myth. He exceeds the capacity of His authors."),
        ("EBGaramond", 10.5, "He differs from every figure who came before or after."),
        (None, 0, ""),  # spacer
        ("EBGaramond", 10.5, "The argument is cumulative and the conclusion unavoidable:"),
        ("EBGaramond", 10.5, "either this character was real, or we face a miracle greater"),
        ("EBGaramond", 10.5, "than any He performed \u2014 the creation of a fiction"),
        ("EBGaramond", 10.5, "more convincing than fact."),
    ]

    y = DOC_H - 2.2 * inch
    line_spacing = 16

    for font, size, text in lines:
        if font is None:
            y -= line_spacing * 0.8
            continue
        c.setFont(font, size)
        c.drawCentredString(cx, y, text)
        y -= line_spacing

    # Attribution at bottom of back cover
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.2 * inch,
                        "Based on The Man of Galilee by Atticus G. Haygood (1889)")


def main():
    print("Generating Lulu cover PDF...")
    print(f"  Document size: 19.438\" x 9.25\"")
    print(f"  Spine width: 0.688\"")

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
