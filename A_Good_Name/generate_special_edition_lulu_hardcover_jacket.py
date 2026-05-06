#!/usr/bin/env python3
"""Generate Lulu linen-hardcover DUST JACKET for the SPECIAL EDITION
of "A Good Name" — personalized gift printings for the grandchildren.

Identical to the public AGN Lulu hardcover jacket in every respect
except one: a small gold "SPECIAL EDITION" line on the front cover,
just below the author name. Spine, back cover, and both flaps remain
verbatim to the public jacket. The jacket is recipient-agnostic — the
named dedication is in the interior — so this same jacket file can be
reused for every grandchild's printing.

Lulu specs (same template as the public AGN hardcover):
  Document size:    19.5" x 9.25"
  Spine width:      0.75"
  Front/back flap:  3.25" x 9.25"
  Flap fold width:  0.25"
  Cover panel:      5.875" wide (5.5" trim + 0.375" wrap)
  Height:           9.25" (8.5" trim + 0.375" wrap top + 0.375" wrap bottom)
  Fonts:            Embedded TrueType
  Layers:           Flattened

Hardcover ISBN: 979-8-9954288-1-7 (same as public; Lulu treats this
as a private printing of the same title).

Output is gitignored and rsync-excluded — private gift, never deployed.
"""

from pathlib import Path
import sys

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Importing tools.isbn_barcode at module load registers the embedded
# Standard-14 font overrides so Lulu's preflight accepts the cover.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.isbn_barcode import draw_isbn_barcode  # noqa: E402

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "YourNameMeansEverything_Special_Edition_Lulu_Hardcover_Jacket.pdf"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- ISBN ---
ISBN = "979-8-9954288-1-7"

# ============================================================================
# DOCUMENT DIMENSIONS — from Lulu's downloaded hardcover jacket template
# ============================================================================
DOC_H_IN   = 9.25
FLAP_W_IN  = 3.25
FOLD_W_IN  = 0.25
COVER_W_IN = 5.875
SPINE_W_IN = 0.75
DOC_W_IN   = 2*FLAP_W_IN + 2*FOLD_W_IN + 2*COVER_W_IN + SPINE_W_IN  # 19.5"

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# Horizontal layout anchors
BACK_FLAP_LEFT    = 0
BACK_FLAP_RIGHT   = FLAP_W_IN * inch
BACK_FOLD_LEFT    = BACK_FLAP_RIGHT
BACK_FOLD_RIGHT   = BACK_FOLD_LEFT + FOLD_W_IN * inch
BACK_COVER_LEFT   = BACK_FOLD_RIGHT
BACK_COVER_RIGHT  = BACK_COVER_LEFT + COVER_W_IN * inch
SPINE_LEFT        = BACK_COVER_RIGHT
SPINE_RIGHT       = SPINE_LEFT + SPINE_W_IN * inch
FRONT_COVER_LEFT  = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W_IN * inch
FRONT_FOLD_LEFT   = FRONT_COVER_RIGHT
FRONT_FOLD_RIGHT  = FRONT_FOLD_LEFT + FOLD_W_IN * inch
FRONT_FLAP_LEFT   = FRONT_FOLD_RIGHT
FRONT_FLAP_RIGHT  = DOC_W

BACK_CENTER_X  = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

COVER_CENTER_Y = DOC_H / 2

# Wrap (analogous to paperback bleed)
WRAP = 0.375 * inch
TRIM_TOP    = DOC_H - WRAP
TRIM_BOTTOM = WRAP

# Safety margins
COVER_SAFETY = 0.5 * inch
FLAP_SAFETY  = 0.5 * inch

# Visual-centering shifts. The outer 0.375" of each flap and each cover
# panel disappears into the case wrap — the visible center is offset
# from the geometric center toward the spine. Without these the text
# reads as pushed toward the outer edges. The barcode panel on the back
# cover is anchored to the trim-right of the panel and is unaffected.
FLAP_VISUAL_SHIFT = 0.19 * inch
FRONT_COVER_VISUAL_SHIFT = 0.19 * inch
BACK_COVER_VISUAL_SHIFT  = 0.19 * inch

# ============================================================================
# COLORS — matched to the AGN paperback cover
# ============================================================================
NAVY     = Color(0.094, 0.125, 0.180)   # #182030 deep navy
GOLD     = Color(0.769, 0.663, 0.376)   # #C4A960 warm gold
GOLD_DIM = Color(0.620, 0.545, 0.345)   # dimmer gold for secondary text


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for w in words:
        test = f"{current} {w}".strip() if current else w
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_short_line(c, cx, y, width=0.6):
    hw = width * inch / 2
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - hw, y, cx + hw, y)


# ============================================================================
# PANELS
# ============================================================================

def draw_background(c):
    """Fill the entire jacket with deep navy."""
    c.setFillColor(NAVY)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Mirrors the AGN paperback front cover, shifted to land in the
    8.5" trim area between top wrap (0.375") and bottom wrap (0.375").
    Horizontally pulled toward the spine to compensate for the outer
    wrap that disappears around the case board edge."""
    cx = FRONT_CENTER_X - FRONT_COVER_VISUAL_SHIFT

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

    # Author near bottom-mid
    c.setFont("EBGaramond", 13)
    c.drawCentredString(cx, DOC_H - 6.4 * inch, "Paul & Pam Hainline")

    # Special Edition mark — small gold line, letterspaced, italic.
    # Sits between author and Scripture quote so it reads as a quiet
    # "this is something more than the public copy" without drawing
    # focus away from the title hero above.
    c.setFont("EBGaramond-Italic", 9)
    c.drawCentredString(cx, DOC_H - 6.85 * inch,
                        "S P E C I A L   E D I T I O N")

    # Scripture quote near bottom
    quote_y = TRIM_BOTTOM + 1.4 * inch
    draw_short_line(c, cx, quote_y + 0.4 * inch, 0.5)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, quote_y, "“The fear of the Lord is the beginning of wisdom,")
    c.drawCentredString(cx, quote_y - 0.22 * inch,
                        "and the knowledge of the Holy One is understanding.”")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.55 * inch, "P R O V E R B S  9 : 1 0")


def draw_spine(c):
    """Spine reads cleanly on navy at 13pt — wider here than the
    paperback spine (0.75" vs 0.508"), so size up.

    The y offset before drawCentredString shifts the baseline so the
    cap-height middle (not the baseline) lands on the spine centerline."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(GOLD)
    font_size = 13
    c.setFont("EBGaramond", font_size)
    c.drawCentredString(0, -font_size * 0.30,
                        "YOUR NAME MEANS EVERYTHING: A GOOD NAME")

    c.restoreState()


def draw_back_cover(c):
    """Back cover blurb — mirrors the AGN paperback back, with the ISBN
    barcode tucked into the bottom-right corner of the safe area. Body
    text shifts toward the spine to compensate for the outer wrap; the
    barcode is anchored to the trim-right and stays put."""
    cx = BACK_CENTER_X + BACK_COVER_VISUAL_SHIFT
    ls = 17

    c.setFillColor(GOLD)
    draw_short_line(c, cx, DOC_H - 1.8 * inch, 0.5)

    # Opening line — italic
    y = DOC_H - 2.3 * inch
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

    c.setFont("EBGaramond-Italic", 11.5)
    c.drawCentredString(cx, y, "Fourteen chapters. One Foundation.")
    y -= ls * 1.7

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

    # --- ISBN barcode (bottom-right of back cover, inside safe area) ---
    panel_w = 1.75 * inch
    panel_h = 1.0 * inch
    panel_x = BACK_COVER_RIGHT - COVER_SAFETY - panel_w
    panel_y = TRIM_BOTTOM + 0.35 * inch
    draw_isbn_barcode(c, ISBN, panel_x, panel_y, panel_w=panel_w, panel_h=panel_h)


def draw_front_flap(c):
    """Front flap — book description. Text is identical to the AGN
    IngramSpark hardcover jacket, with the single mechanical update
    'thirteen' → 'fourteen' to reflect the new chapter count."""
    safe_left  = FRONT_FLAP_LEFT + FLAP_SAFETY
    safe_right = FRONT_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (FRONT_FLAP_LEFT + FRONT_FLAP_RIGHT) / 2 - FLAP_VISUAL_SHIFT

    c.setFillColor(GOLD)
    y = DOC_H - 1.0 * inch
    line_height = 12

    paragraphs = [
        ("EBGaramond-Italic", 10.5,
            "Your Name Means Everything: A Good Name is a "
            "straight-talk guide for young men navigating the "
            "years that will shape the rest of their lives."),
        ("EBGaramond", 10,
            "In fourteen chapters anchored entirely in Scripture, "
            "Paul and Pam Hainline address the questions no one "
            "else is answering honestly: identity, integrity, "
            "purity, friendship, money, marriage, and what it "
            "means to build a life on the only foundation that "
            "lasts."),
        ("EBGaramond", 10,
            "This is not a book of opinions. It is a book of "
            "Scripture — letting God's Word speak for itself to a "
            "generation that has rarely heard it."),
    ]

    for font, size, text in paragraphs:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.6


def draw_back_flap(c):
    """Back flap — About the Authors. Text is identical to the AGN
    IngramSpark hardcover jacket."""
    safe_left  = BACK_FLAP_LEFT + FLAP_SAFETY
    safe_right = BACK_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (BACK_FLAP_LEFT + BACK_FLAP_RIGHT) / 2 + FLAP_VISUAL_SHIFT

    c.setFillColor(GOLD)
    y = DOC_H - 1.0 * inch
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(flap_cx, y, "About the Authors")
    y -= 10

    c.setStrokeColor(GOLD)
    c.setLineWidth(0.4)
    rule_hw = 0.4 * inch
    c.line(flap_cx - rule_hw, y, flap_cx + rule_hw, y)
    y -= 22

    c.setFillColor(GOLD)
    line_height = 12
    paragraphs = [
        ("EBGaramond", 10,
            "Paul and Pam Hainline are students of God's Word who "
            "write from the conviction that Scripture interprets "
            "Scripture. Their work is rooted in a desire to point "
            "readers back to the biblical text — not to opinions, "
            "traditions, or denominational systems. They are the "
            "founders of NobleMind Press (noblemind.study)."),
    ]
    for font, size, text in paragraphs:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.45

    # Imprint
    mark_y = TRIM_BOTTOM + 0.7 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(flap_cx, mark_y, "NobleMind Press")
    c.setFillColor(GOLD_DIM)
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(flap_cx, mark_y - 14, "noblemind.study")


def main():
    print('Generating SPECIAL EDITION Lulu HARDCOVER JACKET PDF for "A Good Name"...')
    print(f'  Document size:  {DOC_W_IN:.3f}" x {DOC_H_IN}"')
    print(f'  Spine:          {SPINE_W_IN}" (Lulu hardcover template)')
    print(f'  Cover panel:    {COVER_W_IN}" x {DOC_H_IN}" each')
    print(f'  Flap:           {FLAP_W_IN}" x {DOC_H_IN}"   Fold: {FOLD_W_IN}"')
    print(f'  ISBN:           {ISBN}')
    print()
    print('  Panel x-positions (inches):')
    print(f'    back flap  : {BACK_FLAP_LEFT/inch:.3f} .. {BACK_FLAP_RIGHT/inch:.3f}')
    print(f'    back cover : {BACK_COVER_LEFT/inch:.3f} .. {BACK_COVER_RIGHT/inch:.3f}')
    print(f'    spine      : {SPINE_LEFT/inch:.3f} .. {SPINE_RIGHT/inch:.3f}')
    print(f'    front cover: {FRONT_COVER_LEFT/inch:.3f} .. {FRONT_COVER_RIGHT/inch:.3f}')
    print(f'    front flap : {FRONT_FLAP_LEFT/inch:.3f} .. {FRONT_FLAP_RIGHT/inch:.3f}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Your Name Means Everything: A Good Name — Lulu Hardcover Jacket")
    c.setAuthor("Paul & Pam Hainline")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\nJacket saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
