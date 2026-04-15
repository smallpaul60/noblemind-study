#!/usr/bin/env python3
"""Generate IngramSpark hardcover dust jacket PDF for Your Name Means Everything: A Good Name.

This script overlays book artwork onto IngramSpark's official Cover Generator
template (downloaded by ISBN). The template defines the exact 24" x 12.5"
document size, trim/fold marks, and bleed area that IngramSpark's automated
checker requires. Our artwork is drawn into the bleed area only, then merged
onto the template so the outer-margin marks remain unaltered.

Specs (IngramSpark template, ISBN 979-8-9954288-1-7):
  Document size:    24.000" x 12.500"
  Bleed area:       19.6875" x  9.000"  at (3.3125", 3.000")
  Trim size:         5.500"  x  8.500"
  Cover panel:       5.938"  x  8.750"  (each)
  Spine:             0.5625"            (180 pages, B&W creme paper)
  Flap:              3.250"             (each)
  Wrap:              0.250"             (between cover and flap)
  Bleed:             0.125"             (all four edges of bleed area)
  Page count:        180
"""

from pathlib import Path
import pypdf
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
TEMPLATE_FILE = BOOK_DIR / "9798995428817-Jacket.pdf"
ARTWORK_TMP = BOOK_DIR / "_hc_artwork_overlay.pdf"
OUTPUT = BOOK_DIR / "YourNameMeansEverything_IngramSpark_Hardcover_Cover.pdf"
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-1-7.png"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (must match IngramSpark template exactly) ---
PAGE_COUNT  = 180
DOC_W_IN    = 24.000
DOC_H_IN    = 12.500
DOC_W       = DOC_W_IN * inch
DOC_H       = DOC_H_IN * inch

# Bleed artwork area — exact position and size measured from template
BLEED_AREA_W_IN = 19.6875   # = 19 11/16"
BLEED_AREA_H_IN =  9.0000
BLEED_LEFT_IN   =  3.3125   # = 3 5/16"
BLEED_BOTTOM_IN =  3.0000
BLEED_RIGHT_IN  = BLEED_LEFT_IN  + BLEED_AREA_W_IN    # 23.0000"
BLEED_TOP_IN    = BLEED_BOTTOM_IN + BLEED_AREA_H_IN   # 12.0000"

BLEED_LEFT   = BLEED_LEFT_IN   * inch
BLEED_RIGHT  = BLEED_RIGHT_IN  * inch
BLEED_BOTTOM = BLEED_BOTTOM_IN * inch
BLEED_TOP    = BLEED_TOP_IN    * inch

# Panel widths (from template — exact 16ths)
BLEED_W   = 0.1250
FLAP_W    = 3.2500
WRAP_W    = 0.2500
COVER_W   = 5.9375     # = 95/16"
SPINE_W   = 0.5625     # = 9/16"  (180 pages creme)
COVER_H   = 8.7500
TRIM_W    = 5.5
TRIM_H    = 8.5

# Trim edges (just inside the bleed margins)
TRIM_LEFT_IN   = BLEED_LEFT_IN   + BLEED_W   # 3.4375"
TRIM_RIGHT_IN  = BLEED_RIGHT_IN  - BLEED_W   # 22.8750"
TRIM_BOTTOM_IN = BLEED_BOTTOM_IN + BLEED_W   # 3.1250"
TRIM_TOP_IN    = BLEED_TOP_IN    - BLEED_W   # 11.8750"

# --- Colors ---
NAVY = Color(0.094, 0.125, 0.180)         # #182030 deep navy
GOLD = Color(0.769, 0.663, 0.376)         # #C4A960 warm gold
GOLD_DIM = Color(0.620, 0.545, 0.345)     # dimmer gold for secondary text

# --- Panel x-positions (from left edge of document, in points) ---
BACK_FLAP_LEFT   = TRIM_LEFT_IN * inch
BACK_FLAP_RIGHT  = BACK_FLAP_LEFT + FLAP_W * inch
BACK_WRAP_LEFT   = BACK_FLAP_RIGHT
BACK_WRAP_RIGHT  = BACK_WRAP_LEFT + WRAP_W * inch
BACK_COVER_LEFT  = BACK_WRAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W * inch

SPINE_LEFT      = BACK_COVER_RIGHT
SPINE_RIGHT     = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X  = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT  = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W * inch
FRONT_WRAP_LEFT   = FRONT_COVER_RIGHT
FRONT_WRAP_RIGHT  = FRONT_WRAP_LEFT + WRAP_W * inch
FRONT_FLAP_LEFT   = FRONT_WRAP_RIGHT
FRONT_FLAP_RIGHT  = FRONT_FLAP_LEFT + FLAP_W * inch

# Vertical
TRIM_TOP       = TRIM_TOP_IN    * inch
TRIM_BOTTOM    = TRIM_BOTTOM_IN * inch
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

# Centers of each panel
BACK_CENTER_X  = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# Safety margins
# IngramSpark's absolute minimum is 0.125" from any trim or fold line, but
# their automated checker has rejected prior submissions at ~0.25", so we
# aim for 0.5" on every panel, every edge. Flap text width stays 2.25".
SAFETY = 0.5 * inch             # Back cover, cover panels
FRONT_SAFETY = 0.5 * inch       # Front cover
FLAP_FOLD_SAFETY = 0.5 * inch   # Flap fold line (toward board)
FLAP_TRIM_SAFETY = 0.5 * inch   # Flap turn-in edge (paper trim side)
TOP_HEAD_PAD = 0.625 * inch     # Extra headroom for first-line ascenders

FRONT_FLAP_SAFE_LEFT = FRONT_FLAP_LEFT + FLAP_FOLD_SAFETY
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - FLAP_TRIM_SAFETY
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT

BACK_FLAP_SAFE_LEFT = BACK_FLAP_LEFT + FLAP_TRIM_SAFETY
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - FLAP_FOLD_SAFETY
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


# --- Element-level safety auditing -----------------------------------
# Every draw call for text, lines, and images records its bbox here.
# At the end of the run we walk the list and flag anything tighter than
# SAFETY_WARN_THRESHOLD inches from any trim or fold edge.

SAFETY_WARN_THRESHOLD = 0.375  # inches

_drawn_elements = []  # (panel, label, left, right, top, bottom)
_canvas = None        # set in main() so record_text can call stringWidth

_FONT_ASC = 0.73
_FONT_DES = 0.22


def _panel_for_x(x):
    """Identify which panel an x coordinate sits in. Returns
    (name, left_pt, right_pt, left_is_fold, right_is_fold)."""
    if BACK_FLAP_LEFT <= x < BACK_FLAP_RIGHT:
        return ("back_flap", BACK_FLAP_LEFT, BACK_FLAP_RIGHT, False, True)
    if BACK_WRAP_LEFT <= x < BACK_WRAP_RIGHT:
        return ("back_wrap", BACK_WRAP_LEFT, BACK_WRAP_RIGHT, True, True)
    if BACK_COVER_LEFT <= x < BACK_COVER_RIGHT:
        return ("back_cover", BACK_COVER_LEFT, BACK_COVER_RIGHT, True, True)
    if SPINE_LEFT <= x < SPINE_RIGHT:
        return ("spine", SPINE_LEFT, SPINE_RIGHT, True, True)
    if FRONT_COVER_LEFT <= x < FRONT_COVER_RIGHT:
        return ("front_cover", FRONT_COVER_LEFT, FRONT_COVER_RIGHT, True, True)
    if FRONT_WRAP_LEFT <= x < FRONT_WRAP_RIGHT:
        return ("front_wrap", FRONT_WRAP_LEFT, FRONT_WRAP_RIGHT, True, True)
    if FRONT_FLAP_LEFT <= x < FRONT_FLAP_RIGHT:
        return ("front_flap", FRONT_FLAP_LEFT, FRONT_FLAP_RIGHT, True, False)
    return ("unknown", 0, DOC_W, False, False)


def record_text(text, font, size, x_anchor, baseline, centered=True):
    w = _canvas.stringWidth(text, font, size)
    if centered:
        left = x_anchor - w / 2
        right = x_anchor + w / 2
    else:
        left = x_anchor
        right = x_anchor + w
    top = baseline + _FONT_ASC * size
    bottom = baseline - _FONT_DES * size
    panel = _panel_for_x((left + right) / 2)[0]
    _drawn_elements.append((panel, f"{font} {size}pt '{text[:44]}'", left, right, top, bottom))


def record_rect(label, x, y, w, h):
    panel = _panel_for_x(x + w / 2)[0]
    _drawn_elements.append((panel, label, x, x + w, y + h, y))


def run_safety_audit():
    print(f"\n=== Safety audit (warn threshold: {SAFETY_WARN_THRESHOLD}\") ===")
    warnings = 0
    worst_by_panel = {}
    for panel, label, left, right, top, bottom in _drawn_elements:
        if panel == "spine":
            continue
        _, L, R, fold_l, fold_r = _panel_for_x((left + right) / 2)
        edges = [
            ("left",   (left - L) / 72,             fold_l),
            ("right",  (R - right) / 72,            fold_r),
            ("top",    (TRIM_TOP - top) / 72,       False),
            ("bottom", (bottom - TRIM_BOTTOM) / 72, False),
        ]
        side, dist, is_fold = min(edges, key=lambda e: e[1])
        cur = worst_by_panel.get(panel)
        if cur is None or dist < cur[0]:
            worst_by_panel[panel] = (dist, label, side, is_fold)
        if dist < SAFETY_WARN_THRESHOLD:
            kind = "fold" if is_fold else "trim"
            tag = "VIOLATION" if dist < 0.125 else "TIGHT"
            print(f"  [{tag}] {panel} {label}: {side}={dist:+.3f}\" ({kind})")
            warnings += 1
    print("\n  Worst clearance per panel:")
    for panel, (dist, label, side, is_fold) in sorted(worst_by_panel.items()):
        kind = "fold" if is_fold else "trim"
        print(f"    {panel:12} {side:6} = {dist:+.3f}\" ({kind})  [{label[:60]}]")
    if warnings == 0:
        print(f"\n  ALL CLEAR — every element is at least "
              f"{SAFETY_WARN_THRESHOLD}\" from every edge.")
    else:
        print(f"\n  {warnings} element(s) below warn threshold.")
# ---------------------------------------------------------------------


def draw_background(c):
    """Fill the bleed area only with deep navy.

    Clipped to the bleed area so the IngramSpark template's trim/fold marks
    in the white outer margins remain visible after merging.
    """
    c.saveState()
    clip = c.beginPath()
    clip.rect(BLEED_LEFT, BLEED_BOTTOM,
              BLEED_RIGHT - BLEED_LEFT, BLEED_TOP - BLEED_BOTTOM)
    clip.close()
    c.clipPath(clip, stroke=0)
    c.setFillColor(NAVY)
    c.rect(BLEED_LEFT, BLEED_BOTTOM,
           BLEED_RIGHT - BLEED_LEFT, BLEED_TOP - BLEED_BOTTOM,
           fill=1, stroke=0)
    c.restoreState()


def draw_front_cover(c):
    """Draw front cover — navy/gold design."""
    cx = FRONT_CENTER_X
    safe_top = TRIM_TOP - FRONT_SAFETY
    safe_bottom = TRIM_BOTTOM + FRONT_SAFETY
    safe_left = FRONT_COVER_LEFT + FRONT_SAFETY
    safe_right = FRONT_COVER_RIGHT - FRONT_SAFETY

    def centered(text, font, size, baseline):
        c.setFont(font, size)
        c.drawCentredString(cx, baseline, text)
        record_text(text, font, size, cx, baseline, centered=True)

    # Corner brackets — start AT the safe corners, extend inward
    draw_corner_brackets(c, safe_left, safe_top, safe_right, safe_bottom)
    # The bracket arms are at exactly safe_left/safe_right/safe_top/safe_bottom
    # — record them as zero-area points on those edges so the audit
    # catches any future change to bracket placement.
    record_rect("bracket TL", safe_left, safe_top - 0.5, 0.5, 0.5)
    record_rect("bracket BR", safe_right - 0.5, safe_bottom, 0.5, 0.5)

    # Small cross near top
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    cross_y = BLEED_TOP - 1.6 * inch
    c.line(cx, cross_y + 0.15 * inch, cx, cross_y - 0.15 * inch)
    c.line(cx - 0.1 * inch, cross_y, cx + 0.1 * inch, cross_y)
    record_rect("cross", cx - 0.1 * inch, cross_y - 0.15 * inch,
                0.2 * inch, 0.3 * inch)

    c.setFillColor(GOLD)
    centered("Y O U R",    "EBGaramond", 14, BLEED_TOP - 2.35 * inch)
    centered("NAME",       "EBGaramond", 46, BLEED_TOP - 3.0  * inch)
    centered("M E A N S",  "EBGaramond", 14, BLEED_TOP - 3.45 * inch)
    centered("EVERYTHING", "EBGaramond", 46, BLEED_TOP - 4.1  * inch)

    # Decorative divider — line diamond line
    div_y = BLEED_TOP - 4.55 * inch
    hw = 0.7 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - hw, div_y, cx - 0.08 * inch, div_y)
    c.line(cx + 0.08 * inch, div_y, cx + hw, div_y)
    record_rect("divider", cx - hw, div_y - 0.03, 2 * hw, 0.06)
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
    centered("A Good Name", "EBGaramond-Italic", 18, BLEED_TOP - 5.0 * inch)

    # Tagline
    centered("A Straight-Talk Guide for Young Men", "EBGaramond-Italic", 13, BLEED_TOP - 5.55 * inch)
    centered("Who Want to Matter",                  "EBGaramond-Italic", 13, BLEED_TOP - 5.8  * inch)

    # Scripture quote near bottom
    quote_y = TRIM_BOTTOM + 1.4 * inch
    draw_short_line(c, cx, quote_y + 0.35 * inch, 0.5)
    record_rect("quote decor line",
                cx - 0.25 * inch, quote_y + 0.35 * inch - 0.3,
                0.5 * inch, 0.6)
    centered("\u201cThe fear of the Lord is the beginning of wisdom,",
             "EBGaramond-Italic", 11, quote_y)
    centered("and the knowledge of the Holy One is understanding.\u201d",
             "EBGaramond-Italic", 11, quote_y - 0.22 * inch)
    centered("P R O V E R B S  9 : 1 0",
             "EBGaramond", 8.5, quote_y - 0.55 * inch)


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

    def centered(text, font, size, baseline):
        c.setFont(font, size)
        c.drawCentredString(cx, baseline, text)
        record_text(text, font, size, cx, baseline, centered=True)

    c.setFillColor(GOLD)

    # Short decorative line at top
    draw_short_line(c, cx, BLEED_TOP - 1.8 * inch, 0.5)
    record_rect("back decor top",
                cx - 0.25 * inch, BLEED_TOP - 1.8 * inch - 0.25,
                0.5 * inch, 0.5)

    # Opening line — italic
    y = BLEED_TOP - 2.3 * inch
    ls = 17

    centered("Nobody told you this was coming.", "EBGaramond-Italic", 11.5, y)
    y -= ls * 1.5

    # Body text
    body_paragraphs = [
        "You are standing at the beginning of your adult life in a world that offers everything except the truth you actually need.",
        "This book is built on the Bible \u2014 not on opinions, not on trends, not on what sounds good at graduation.",
        "It is a straight-talk guide through the questions that will define your life: who you are, who God is, how you treat people, and how you build something that lasts.",
    ]

    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10.5, text_width)
        for line in lines:
            centered(line, "EBGaramond", 10.5, y)
            y -= ls
        y -= ls * 0.5

    # Bold tagline
    centered("Thirteen chapters. One Foundation.", "EBGaramond-Italic", 11.5, y)
    y -= ls * 1.8

    # Decorative line
    draw_short_line(c, cx, y + 0.1 * inch, 0.35)
    record_rect("back decor mid",
                cx - 0.175 * inch, y + 0.1 * inch - 0.25,
                0.35 * inch, 0.5)
    y -= ls * 0.8

    # Scripture quote
    centered("\u201cChoose for yourselves today",  "EBGaramond-Italic", 10.5, y); y -= ls
    centered("whom you will serve . . .",           "EBGaramond-Italic", 10.5, y); y -= ls
    centered("but as for me and my house,",        "EBGaramond-Italic", 10.5, y); y -= ls
    centered("we will serve the Lord.\u201d",       "EBGaramond-Italic", 10.5, y); y -= ls * 1.2
    centered("J O S H U A  2 4 : 1 5",              "EBGaramond", 8.5, y)

    # Author at bottom (left side, leaving room for barcode on right)
    author_text = "P A U L  &  P A M  H A I N L I N E"
    author_baseline = TRIM_BOTTOM + SAFETY
    c.setFont("EBGaramond", 9)
    c.drawString(safe_left, author_baseline, author_text)
    record_text(author_text, "EBGaramond", 9, safe_left, author_baseline, centered=False)

    # --- ISBN Barcode (bottom-right of back cover) ---
    # Previous revision nudged this -0.15" below the safety line — remove
    # that nudge so the barcode sits flush with the 0.5" safety margin.
    barcode_w = 2.0 * inch
    barcode_h = 1.2 * inch
    barcode_x = safe_right - barcode_w
    barcode_y = TRIM_BOTTOM + SAFETY

    c.setFillColor(white)
    c.rect(barcode_x, barcode_y, barcode_w, barcode_h, fill=1, stroke=0)
    record_rect("ISBN barcode box", barcode_x, barcode_y, barcode_w, barcode_h)

    barcode_img = str(BOOK_DIR / "barcode_978-8-9954288-1-7.png")
    c.drawImage(barcode_img, barcode_x + 0.1 * inch, barcode_y + 0.1 * inch,
                width=barcode_w - 0.2 * inch, height=barcode_h - 0.2 * inch,
                preserveAspectRatio=True, anchor='c')


def draw_front_flap(c):
    """Draw front flap text — book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(GOLD)

    y = TRIM_TOP - TOP_HEAD_PAD
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
            record_text(line, font, size, safe_left, y, centered=False)
            y -= line_height
        y -= line_height * 0.2


def draw_back_flap(c):
    """Draw back flap text — About the Authors."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(GOLD)

    y = TRIM_TOP - TOP_HEAD_PAD
    header = "About the Authors"
    c.setFont("EBGaramond", 10)
    c.drawString(safe_left, y, header)
    record_text(header, "EBGaramond", 10, safe_left, y, centered=False)
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
            record_text(line, "EBGaramond", 7.5, safe_left, y, centered=False)
            y -= line_height
        y -= line_height * 0.2


def main():
    if not TEMPLATE_FILE.exists():
        raise SystemExit(f"ERROR: IngramSpark template not found at {TEMPLATE_FILE}")

    print('Generating IngramSpark HARDCOVER (dust jacket) cover PDF...')
    print(f'  Title: Your Name Means Everything: A Good Name')
    print(f'  Document size:   {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}" (per IngramSpark template)')
    print(f'  Bleed area:      {BLEED_AREA_W_IN:.4f}" x {BLEED_AREA_H_IN:.4f}" '
          f'at ({BLEED_LEFT_IN:.4f}", {BLEED_BOTTOM_IN:.4f}")')
    print(f'  Trim size:       {TRIM_W}" x {TRIM_H}"')
    print(f'  Cover panel:     {COVER_W}" x {COVER_H}"')
    print(f'  Spine:           {SPINE_W}" ({PAGE_COUNT} pages, creme paper)')
    print(f'  Flap:            {FLAP_W}"   Wrap: {WRAP_W}"   Bleed: {BLEED_W}"')

    # --- Step 1: render artwork to intermediate PDF at 24x12.5 ------------
    global _canvas
    c = canvas.Canvas(str(ARTWORK_TMP), pagesize=(DOC_W, DOC_H))
    _canvas = c  # so record_text() can call stringWidth
    c.setTitle("Your Name Means Everything: A Good Name - IngramSpark Hardcover Dust Jacket")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\n  Artwork overlay rendered: {ARTWORK_TMP.name}")

    # --- Step 2: overlay artwork onto IngramSpark template ----------------
    template_reader = pypdf.PdfReader(str(TEMPLATE_FILE))
    artwork_reader  = pypdf.PdfReader(str(ARTWORK_TMP))

    base_page    = template_reader.pages[0]
    overlay_page = artwork_reader.pages[0]

    bw = float(base_page.mediabox.width)
    bh = float(base_page.mediabox.height)
    ow = float(overlay_page.mediabox.width)
    oh = float(overlay_page.mediabox.height)
    if abs(bw - ow) > 0.5 or abs(bh - oh) > 0.5:
        raise SystemExit(
            f"ERROR: page size mismatch. template={bw}x{bh}pt, "
            f"artwork={ow}x{oh}pt")

    base_page.merge_page(overlay_page)

    writer = pypdf.PdfWriter()
    writer.add_page(base_page)
    with open(OUTPUT, "wb") as f:
        writer.write(f)

    try:
        ARTWORK_TMP.unlink()
    except OSError:
        pass

    print(f"\nFinal cover saved to {OUTPUT}")
    print(f"  Document size:   {bw/72:.3f}\" x {bh/72:.3f}\"  (matches template)")

    run_safety_audit()
    print("Done.")


if __name__ == "__main__":
    main()
