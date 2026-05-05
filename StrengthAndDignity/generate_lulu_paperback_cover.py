#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for "Strength and Dignity".

Lulu specs (5.5x8.5 perfect bound paperback, cream paper, 171 pages):
  Trim size:    5.5" x 8.5"
  Spine width:  0.445" (11.3 mm) — pulled from Lulu's template tool for
                this title at 171 pages on cream paper. Do NOT use the
                generic 0.002252 formula; cream stock runs thicker, and
                Lulu's value is authoritative.
  Bleed:        0.125" on outside edges (top, bottom, left, right).
  Total size:   11.695" x 8.75"   (0.125 + 5.5 + 0.445 + 5.5 + 0.125 by 0.125 + 8.5 + 0.125)
  Fonts:        Embedded TrueType (EB Garamond + Liberation Sans, the
                latter via tools.isbn_barcode for any Standard-14 fonts
                ReportLab might fall back on).
  Layers:       Flattened (single canvas, no transparency groups).

Design mirrors the existing IngramSpark paperback cover for visual
consistency between the two retail editions. Differences are mechanical
(wider spine, slightly wider total document).

ISBN: 979-8-9954288-2-4 (paperback). The barcode is rendered from this
string at runtime via tools/isbn_barcode.py — no dependence on the older
mis-named barcode_978-... PNG that lives in this directory.
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
OUTPUT = BOOK_DIR / "Strength_and_Dignity_Lulu_Paperback_Cover.pdf"

# Register EB Garamond fonts (matches the existing SaD covers)
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- ISBN ---
ISBN = "979-8-9954288-2-4"

# --- Page count & spine (from Lulu's template tool) ---
PAGE_COUNT = 171
SPINE_W = 0.445   # Lulu template value (171 pp, cream)

# --- Document dimensions ---
BLEED = 0.125
TRIM_W = 5.5
TRIM_H = 8.5
DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H = (BLEED + TRIM_H + BLEED) * inch

# --- Colors (matched to IngramSpark cover) ---
DEEP_ROSE = Color(0.235, 0.082, 0.145)    # #3C1525 deep burgundy-rose
CREAM = Color(0.957, 0.922, 0.855)         # #F4EBDA warm cream
GOLD_ACCENT = Color(0.769, 0.663, 0.306)   # #C4A94E warm gold

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
    c.drawCentredString(cx, quote_y, "“Strength and dignity are her clothing,")
    c.drawCentredString(cx, quote_y - 0.2 * inch, "and she smiles at the future.”")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.5 * inch, "P R O V E R B S  3 1 : 2 5")


def draw_spine(c):
    """Draw spine text. The 0.445" Lulu spine has roughly 0.32" usable
    height after Lulu's recommended 0.0625" margins on each side, so a
    9pt setting reads cleanly without crowding."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(0, 0, "YOUR NAME MEANS EVERYTHING: STRENGTH AND DIGNITY")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover blurb plus ISBN barcode in the bottom-right corner."""
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
        "One day you’re watching the clock in a classroom.",
        "The next, the world steps back and says —",
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
        "young women stepping into adulthood. Through fourteen",
        "chapters, it walks through the things that matter most —",
        "identity, character, purpose, relationships, work,",
        "money, and faith — not with opinions or platitudes,",
        "but with what God’s Word actually says.",
    ]
    for line in body2:
        c.drawCentredString(cx, y, line)
        y -= ls
    y -= ls * 0.5

    body3 = [
        "From Ruth’s loyalty to Rahab’s courage to the",
        "Proverbs 31 woman who clothed herself in strength",
        "and dignity and smiled at the future — this book",
        "shows what it looks like to build a life and a name",
        "that will outlast you.",
    ]
    for line in body3:
        c.drawCentredString(cx, y, line)
        y -= ls
    y -= ls * 0.8

    # Scripture
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, y, "“A good name is to be more desired than great wealth;")
    y -= ls
    c.drawCentredString(cx, y, "favor is better than silver and gold.”")
    y -= ls
    c.setFont("EBGaramond", 9.5)
    c.drawCentredString(cx, y, "— Proverbs 22:1")

    # --- ISBN barcode (bottom-right of back cover) ---
    panel_w = 1.75 * inch
    panel_h = 1.0 * inch
    panel_x = BACK_TRIM_RIGHT - SAFETY - panel_w
    panel_y = TRIM_BOTTOM + 0.35 * inch
    draw_isbn_barcode(c, ISBN, panel_x, panel_y, panel_w=panel_w, panel_h=panel_h)


def main():
    spine_str = f"{SPINE_W:.3f}"
    doc_w_str = f"{DOC_W / inch:.3f}"
    print('Generating Lulu PAPERBACK cover PDF for "Strength and Dignity"...')
    print(f'  Trim size:   {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {spine_str}" ({PAGE_COUNT} pp, Lulu cream template)')
    print(f'  Bleed:       {BLEED}"')
    print(f'  Total size:  {doc_w_str}" x {DOC_H / inch:.3f}"')
    print(f'  ISBN:        {ISBN}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Your Name Means Everything: Strength and Dignity — Lulu Paperback Cover")
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
