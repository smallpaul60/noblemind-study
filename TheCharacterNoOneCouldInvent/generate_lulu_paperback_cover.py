#!/usr/bin/env python3
"""Generate Lulu perfect-bound paperback full wraparound cover for
'The Character No One Could Invent'.

Specs from the Lulu template (172 pages, 5.5x8.5 paperback, cream
interior — confirmed against the cover template PDF Lulu generated):
  - Document size: 11.695 in x 8.75 in
  - Spine width:   0.445 in   (cream paper is thicker than the generic
                                0.002252 formula, which would predict
                                ~0.387 in; trust Lulu's value)
  - Bleed:         0.125 in on the three outside edges

Layout (left to right):
  [0.125 bleed] [5.5 back trim] [0.445 spine] [5.5 front trim] [0.125 bleed]

Design preserves the existing hardcover dust-jacket aesthetic:
  - Navy background (#091528)
  - Gold typography (#C4A94E)
  - Front: "THE CHARACTER / NO ONE COULD INVENT" + italic subtitle + author
  - Back: gold blurb (cumulative-argument paragraphs) + Haygood attribution
  - Spine: rotated gold title

Outputs:
  - The_Character_No_One_Could_Invent_Lulu_Paperback_Cover.pdf
"""

import sys
from pathlib import Path

# Register Standard-14 font overrides BEFORE constructing Canvas so the
# default Helvetica reference resolves to embedded Liberation Sans.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT_PDF = BOOK_DIR / "The_Character_No_One_Could_Invent_Lulu_Paperback_Cover.pdf"

FONT_DIR = Path.home() / ".local" / "share" / "fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (Lulu template) ---
DOC_W = 11.695 * inch
DOC_H = 8.75 * inch
SPINE_W = 0.445 * inch
BLEED = 0.125 * inch
TRIM_W = 5.5 * inch
TRIM_H = 8.5 * inch

# --- Colors (preserved from existing hardcover) ---
NAVY = Color(0.035, 0.082, 0.145)    # ~#091528
GOLD = Color(0.769, 0.663, 0.306)    # ~#C4A94E

# --- Layout anchors (PDF coords, origin bottom-left) ---
BACK_TRIM_LEFT = BLEED                         # 0.125
BACK_TRIM_RIGHT = BACK_TRIM_LEFT + TRIM_W      # 5.625
SPINE_LEFT = BACK_TRIM_RIGHT                   # 5.625
SPINE_RIGHT = SPINE_LEFT + SPINE_W             # 6.070
FRONT_TRIM_LEFT = SPINE_RIGHT                  # 6.070
FRONT_TRIM_RIGHT = FRONT_TRIM_LEFT + TRIM_W    # 11.570

TRIM_BOTTOM = BLEED                            # 0.125
TRIM_TOP = TRIM_BOTTOM + TRIM_H                # 8.625

FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2
TRIM_CY = (TRIM_TOP + TRIM_BOTTOM) / 2

SAFETY = 0.5 * inch


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    """Fill the entire document with deep navy."""
    c.setFillColor(NAVY)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Front cover typography — matches the published hardcover."""
    cx = FRONT_CENTER_X
    c.setFillColor(GOLD)

    # Title (two lines)
    c.setFont("EBGaramond", 26)
    c.drawCentredString(cx, DOC_H - 2.8 * inch, "THE CHARACTER")
    c.drawCentredString(cx, DOC_H - 3.25 * inch, "NO ONE COULD INVENT")

    # Subtitle (two italic lines)
    c.setFont("EBGaramond-Italic", 15)
    c.drawCentredString(cx, DOC_H - 4.0 * inch, "The Evidence of Jesus’ Deity")
    c.drawCentredString(cx, DOC_H - 4.35 * inch, "in the Portrait Itself")

    # Author
    c.setFont("EBGaramond", 17)
    c.drawCentredString(cx, DOC_H - 5.6 * inch, "Paul Hainline")


def draw_spine(c):
    """Spine — rotated gold title, reads top-to-bottom (US/UK convention).

    Spine width 0.445" (32pt) is comfortable for 11pt text — matches
    the hardcover's spine type size for series consistency.
    """
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_CY)
    c.rotate(270)
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 11)
    c.drawCentredString(0, -3, "THE CHARACTER NO ONE COULD INVENT")
    c.restoreState()


def draw_back_cover(c):
    """Back cover blurb — gold on navy, cumulative-argument paragraphs."""
    cx = BACK_CENTER_X
    c.setFillColor(GOLD)

    lines = [
        ("EBGaramond", 11, "What if the strongest evidence for who Jesus was"),
        ("EBGaramond", 11, "isn’t found in miracles or prophecy —"),
        ("EBGaramond", 11, "but in the man Himself?"),
        (None, 0, ""),
        ("EBGaramond", 10.5, "The four Gospels present a character so consistent,"),
        ("EBGaramond", 10.5, "so original, and so far above His biographers that"),
        ("EBGaramond", 10.5, "no human explanation accounts for Him. The men who"),
        ("EBGaramond", 10.5, "wrote about Jesus misunderstood Him, feared when He"),
        ("EBGaramond", 10.5, "was calm, and fled when He stood firm. Yet somehow"),
        ("EBGaramond", 10.5, "they produced a portrait no dramatist has ever matched."),
        (None, 0, ""),
        ("EBGaramond", 10.5, "This book examines Jesus from every angle — as a"),
        ("EBGaramond", 10.5, "literary creation, a mythological figure, a product of"),
        ("EBGaramond", 10.5, "His culture, a teacher, a reformer — and demonstrates"),
        ("EBGaramond", 10.5, "that He fails every test for human invention. He violates"),
        ("EBGaramond", 10.5, "the laws of myth. He exceeds the capacity of His authors."),
        ("EBGaramond", 10.5, "He differs from every figure who came before or after."),
        (None, 0, ""),
        ("EBGaramond", 10.5, "The argument is cumulative and the conclusion unavoidable:"),
        ("EBGaramond", 10.5, "either this character was real, or we face a miracle greater"),
        ("EBGaramond", 10.5, "than any He performed — the creation of a fiction"),
        ("EBGaramond", 10.5, "more convincing than fact."),
    ]

    y = TRIM_TOP - 0.7 * inch
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
    c.drawCentredString(
        cx, TRIM_BOTTOM + 0.7 * inch,
        "Based on The Man of Galilee by Atticus G. Haygood (1889)",
    )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("Generating Lulu paperback cover (perfect-bound)...")
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')
    print(f'  Spine:    {SPINE_W/inch:.3f}" (172 pp cream interior)')
    print(f'  Bleed:    {BLEED/inch:.3f}" on outside edges')
    print(f'  Trim:     {TRIM_W/inch:.2f}" x {TRIM_H/inch:.2f}" per panel')

    c = canvas.Canvas(str(OUTPUT_PDF), pagesize=(DOC_W, DOC_H))
    c.setTitle("The Character No One Could Invent — Lulu Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"  PDF saved to {OUTPUT_PDF}")
    print("Done.")


if __name__ == "__main__":
    main()
