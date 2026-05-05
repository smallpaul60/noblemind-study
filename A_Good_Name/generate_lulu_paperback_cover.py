#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for "Your Name Means Everything: A Good Name".

Lulu specs (5.5x8.5 perfect bound paperback, cream paper, 14-chapter
edition — pulled from Lulu's downloaded paperback cover template):
  Trim size:    5.5" x 8.5"
  Spine width:  0.508" (12.9 mm) — Lulu template value for this title.
                Do NOT use the generic 0.002252 formula; cream stock
                runs thicker and Lulu's value is authoritative.
  Bleed:        0.125" on outside edges (top, bottom, left, right).
  Total size:   11.758" x 8.75"   (0.125 + 5.5 + 0.508 + 5.5 + 0.125 by 0.125 + 8.5 + 0.125)
  Fonts:        Embedded TrueType (EB Garamond + Liberation Sans, the
                latter via tools.isbn_barcode for any Standard-14 fonts
                ReportLab might fall back on).
  Layers:       Flattened (single canvas, no transparency groups).

Design mirrors the existing IngramSpark paperback cover for visual
consistency between the two retail editions. Differences are mechanical
(wider spine, slightly wider total document, runtime barcode instead of
PNG image).

ISBN: 979-8-9954288-0-0 (paperback). The barcode is rendered from this
string at runtime via tools/isbn_barcode.py.
"""

from pathlib import Path
import sys

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Importing tools.isbn_barcode at module load registers the embedded
# Standard-14 font overrides (Helvetica, Times) so Lulu's preflight
# accepts the cover. It also exposes draw_isbn_barcode() below.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.isbn_barcode import draw_isbn_barcode  # noqa: E402

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "YourNameMeansEverything_Lulu_Paperback_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- ISBN ---
ISBN = "979-8-9954288-0-0"

# --- Spine (from Lulu template) ---
SPINE_W = 0.508

# --- Document dimensions ---
BLEED = 0.125
TRIM_W = 5.5
TRIM_H = 8.5
DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H = (BLEED + TRIM_H + BLEED) * inch

# --- Colors (matched to IngramSpark cover) ---
NAVY     = Color(0.094, 0.125, 0.180)   # #182030 deep navy
GOLD     = Color(0.769, 0.663, 0.376)   # #C4A960 warm gold
GOLD_DIM = Color(0.620, 0.545, 0.345)   # dimmer gold for secondary text

# --- Layout positions (from left edge of document) ---
BACK_COVER_LEFT  = 0
BACK_COVER_RIGHT = (BLEED + TRIM_W) * inch

SPINE_LEFT     = BACK_COVER_RIGHT
SPINE_RIGHT    = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT  = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

# Trim edges
BACK_TRIM_LEFT  = BLEED * inch
BACK_TRIM_RIGHT = BACK_COVER_RIGHT
BACK_CENTER_X   = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT  = FRONT_COVER_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X   = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# Vertical
TRIM_TOP    = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch
COVER_CENTER_Y = DOC_H / 2

# Safety margin
SAFETY = 0.25 * inch


def draw_short_line(c, cx, y, width=0.6):
    hw = width * inch / 2
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - hw, y, cx + hw, y)


def draw_corner_brackets(c, left, top, right, bottom, size=0.3):
    s = size * inch
    c.setStrokeColor(GOLD_DIM)
    c.setLineWidth(0.4)
    c.line(left, top,    left + s, top)
    c.line(left, top,    left,     top - s)
    c.line(right, top,   right - s, top)
    c.line(right, top,   right,     top - s)
    c.line(left, bottom, left + s, bottom)
    c.line(left, bottom, left,     bottom + s)
    c.line(right, bottom, right - s, bottom)
    c.line(right, bottom, right,     bottom + s)


def draw_background(c):
    """Fill entire document with deep navy."""
    c.setFillColor(NAVY)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    cx = FRONT_CENTER_X
    safe_top    = TRIM_TOP - SAFETY
    safe_bottom = TRIM_BOTTOM + SAFETY
    safe_left   = FRONT_TRIM_LEFT + SAFETY
    safe_right  = FRONT_TRIM_RIGHT - SAFETY

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
    c.drawCentredString(cx, quote_y, "“The fear of the Lord is the beginning of wisdom,")
    c.drawCentredString(cx, quote_y - 0.22 * inch,
                        "and the knowledge of the Holy One is understanding.”")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.55 * inch, "P R O V E R B S  9 : 1 0")


def draw_spine(c):
    """Draw spine text. The 0.508" Lulu spine has roughly 0.38" usable
    height after recommended 0.0625" margins each side, so a 10pt
    setting reads cleanly without crowding. Baseline offset by
    font_size * 0.30 so the cap-height middle (not the baseline) lands
    on the spine centerline."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(GOLD)
    font_size = 10
    c.setFont("EBGaramond", font_size)
    c.drawCentredString(0, -font_size * 0.30,
                        "YOUR NAME MEANS EVERYTHING: A GOOD NAME")

    c.restoreState()


def draw_back_cover(c):
    """Back cover blurb plus ISBN barcode in the bottom-right corner.
    Updated for the 14-chapter edition."""
    cx = BACK_CENTER_X

    c.setFillColor(GOLD)
    draw_short_line(c, cx, DOC_H - 1.8 * inch, 0.5)

    # Opening line — italic
    y = DOC_H - 2.3 * inch
    ls = 17

    c.setFont("EBGaramond-Italic", 11.5)
    c.drawCentredString(cx, y, "Nobody told you this was coming.")
    y -= ls * 1.5

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

    c.drawCentredString(cx, y, "This book is built on the Bible — not on")
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

    # Tagline — bumped to fourteen for the new edition
    c.setFont("EBGaramond-Italic", 11.5)
    c.drawCentredString(cx, y, "Fourteen chapters. One Foundation.")
    y -= ls * 1.8

    draw_short_line(c, cx, y + 0.1 * inch, 0.35)
    y -= ls * 0.8

    # Scripture quote
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, y, "“Choose for yourselves today")
    y -= ls
    c.drawCentredString(cx, y, "whom you will serve . . .")
    y -= ls
    c.drawCentredString(cx, y, "but as for me and my house,")
    y -= ls
    c.drawCentredString(cx, y, "we will serve the Lord.”")
    y -= ls * 1.2

    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, y, "J O S H U A  2 4 : 1 5")

    # Author at bottom (left side; barcode goes on the right)
    c.setFont("EBGaramond", 9)
    c.drawString(BACK_TRIM_LEFT + SAFETY, TRIM_BOTTOM + 0.5 * inch,
                 "P A U L  &  P A M  H A I N L I N E")

    # --- ISBN barcode (bottom-right of back cover) ---
    panel_w = 1.75 * inch
    panel_h = 1.0 * inch
    panel_x = BACK_TRIM_RIGHT - SAFETY - panel_w
    panel_y = TRIM_BOTTOM + 0.35 * inch
    draw_isbn_barcode(c, ISBN, panel_x, panel_y, panel_w=panel_w, panel_h=panel_h)


def main():
    spine_str = f"{SPINE_W:.3f}"
    doc_w_str = f"{DOC_W / inch:.3f}"
    print('Generating Lulu PAPERBACK cover PDF for "A Good Name"...')
    print(f'  Trim size:   {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {spine_str}" (Lulu template value)')
    print(f'  Bleed:       {BLEED}"')
    print(f'  Total size:  {doc_w_str}" x {DOC_H / inch:.3f}"')
    print(f'  ISBN:        {ISBN}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Your Name Means Everything: A Good Name — Lulu Paperback Cover")
    c.setAuthor("Paul & Pam Hainline")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
