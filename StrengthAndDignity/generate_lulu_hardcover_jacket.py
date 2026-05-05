#!/usr/bin/env python3
"""Generate Lulu linen-hardcover DUST JACKET for "Strength and Dignity".

Lulu specs (pulled from Lulu's downloaded template for this title):
  Document size:    19.438" x 9.25"   (493.73mm x 234.95mm)
  Spine width:      0.688" (17.48mm)
  Front/back flap:  3.25" x 9.25"
  Flap fold width:  0.25" (between cover panel and flap, each side)
  Cover panel:      5.875" wide (5.5" trim + 0.375" wrap)
  Height:           9.25" (8.5" trim + 0.375" wrap top + 0.375" wrap bottom)
  Fonts:            Embedded TrueType (EB Garamond + Liberation Sans via
                    tools.isbn_barcode for any Standard-14 fallbacks)
  Layers:           Flattened

Layout (left to right):
  [3.25 back flap][0.25 fold][5.875 back cover][0.688 spine]
  [5.875 front cover][0.25 fold][3.25 front flap]
  Total: 3.25 + 0.25 + 5.875 + 0.688 + 5.875 + 0.25 + 3.25 = 19.438"

Design mirrors the SaD paperback covers (deep burgundy-rose background,
cream typography, warm-gold accents) for visual consistency between the
paperback and hardcover editions.

Hardcover ISBN: 979-8-9954288-3-1.
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
OUTPUT = BOOK_DIR / "Strength_and_Dignity_Lulu_Hardcover_Jacket.pdf"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- ISBN ---
ISBN = "979-8-9954288-3-1"

# ============================================================================
# DOCUMENT DIMENSIONS — from Lulu's downloaded hardcover jacket template
# ============================================================================
DOC_H_IN   = 9.25
FLAP_W_IN  = 3.25
FOLD_W_IN  = 0.25
COVER_W_IN = 5.875
SPINE_W_IN = 0.688
DOC_W_IN   = 2*FLAP_W_IN + 2*FOLD_W_IN + 2*COVER_W_IN + SPINE_W_IN  # 19.438"

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
# panel disappears into the case wrap — the visible center is offset from
# the geometric center toward the spine. Without these the text reads as
# pushed toward the outer edges. The barcode panel on the back cover is
# anchored to the trim-right of the panel and is unaffected.
FLAP_VISUAL_SHIFT = 0.19 * inch        # both flaps shift toward doc center
FRONT_COVER_VISUAL_SHIFT = 0.19 * inch  # front cover shifts toward spine (left)
BACK_COVER_VISUAL_SHIFT = 0.19 * inch   # back cover body shifts toward spine (right)

# ============================================================================
# COLORS — matched to the SaD paperback cover
# ============================================================================
DEEP_ROSE   = Color(0.235, 0.082, 0.145)   # #3C1525 deep burgundy-rose
CREAM       = Color(0.957, 0.922, 0.855)   # #F4EBDA warm cream
GOLD_ACCENT = Color(0.769, 0.663, 0.306)   # #C4A94E warm gold
MUTED_GOLD  = Color(0.616, 0.490, 0.278)   # #9D7D47


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


# ============================================================================
# PANELS
# ============================================================================

def draw_background(c):
    """Fill the entire jacket with deep burgundy-rose."""
    c.setFillColor(DEEP_ROSE)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Mirrors the SaD paperback front cover, shifted to land in the
    8.5" trim area between top wrap (0.375") and bottom wrap (0.375").
    Horizontally pulled toward the spine to compensate for the outer
    wrap that disappears around the case board edge."""
    cx = FRONT_CENTER_X - FRONT_COVER_VISUAL_SHIFT
    line_w = 1.5 * inch

    # Decorative line above title
    c.setStrokeColor(CREAM)
    c.setLineWidth(0.5)
    c.line(cx - line_w / 2, DOC_H - 2.25 * inch, cx + line_w / 2, DOC_H - 2.25 * inch)

    # Series title - "YOUR NAME"
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 28)
    c.drawCentredString(cx, DOC_H - 2.9 * inch, "YOUR NAME")

    # Series title line 2 - "MEANS EVERYTHING"
    c.setFont("EBGaramond", 28)
    c.drawCentredString(cx, DOC_H - 3.35 * inch, "MEANS EVERYTHING")

    # Decorative line between title and subtitle
    c.line(cx - line_w / 2, DOC_H - 3.7 * inch, cx + line_w / 2, DOC_H - 3.7 * inch)

    # Volume subtitle - "Strength and Dignity"
    c.setFont("EBGaramond-Italic", 18)
    c.drawCentredString(cx, DOC_H - 4.15 * inch, "Strength and Dignity")

    # Tagline
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(cx, DOC_H - 4.85 * inch, "What the Bible Says to Young Women")
    c.drawCentredString(cx, DOC_H - 5.10 * inch, "About Character, Wisdom, and Faith")

    # Decorative line above author
    c.line(cx - line_w / 2, DOC_H - 5.6 * inch, cx + line_w / 2, DOC_H - 5.6 * inch)

    # Author name
    c.setFont("EBGaramond", 17)
    c.drawCentredString(cx, DOC_H - 6.05 * inch, "Paul & Pam Hainline")

    # Scripture near bottom
    quote_y = TRIM_BOTTOM + 1.3 * inch
    c.line(cx - 0.3 * inch, quote_y + 0.35 * inch, cx + 0.3 * inch, quote_y + 0.35 * inch)
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(cx, quote_y, "“Strength and dignity are her clothing,")
    c.drawCentredString(cx, quote_y - 0.2 * inch, "and she smiles at the future.”")
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, quote_y - 0.5 * inch, "P R O V E R B S  3 1 : 2 5")


def draw_spine(c):
    """Spine reads cleanly on cream at 12pt — wider here than the
    paperback spine (0.688" vs 0.445"), so size up slightly.

    The y offset before drawCentredString shifts the baseline so the
    cap-height middle (not the baseline) lands on the spine centerline.
    Without it the text reads ~3–4pt off-center toward the front cover."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    font_size = 12
    c.setFont("EBGaramond", font_size)
    c.drawCentredString(0, -font_size * 0.30,
                        "YOUR NAME MEANS EVERYTHING: STRENGTH AND DIGNITY")

    c.restoreState()


def draw_back_cover(c):
    """Back cover blurb — mirrors the SaD paperback back, with the ISBN
    barcode tucked into the bottom-right corner of the safe area. Body
    text shifts toward the spine to compensate for the outer wrap; the
    barcode is anchored to the trim-right and stays put."""
    cx = BACK_CENTER_X + BACK_COVER_VISUAL_SHIFT
    ls = 16

    c.setFillColor(CREAM)

    # Opening
    y = DOC_H - 1.95 * inch
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

    # --- ISBN barcode (bottom-right of back cover, inside safe area) ---
    panel_w = 1.75 * inch
    panel_h = 1.0 * inch
    panel_x = BACK_COVER_RIGHT - COVER_SAFETY - panel_w
    panel_y = TRIM_BOTTOM + 0.35 * inch
    draw_isbn_barcode(c, ISBN, panel_x, panel_y, panel_w=panel_w, panel_h=panel_h)


def draw_front_flap(c):
    """Front flap — teaser pulling the reader into the book."""
    safe_left  = FRONT_FLAP_LEFT + FLAP_SAFETY
    safe_right = FRONT_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (FRONT_FLAP_LEFT + FRONT_FLAP_RIGHT) / 2 - FLAP_VISUAL_SHIFT

    c.setFillColor(CREAM)
    y = DOC_H - 1.0 * inch
    line_height = 12

    opening = ("EBGaramond-Italic", 10,
        "There is a moment, somewhere between the last day of school "
        "and the first real decision of adulthood, when a young woman "
        "realizes she is not a girl anymore. The world hands her the "
        "pen and waits.")

    second = ("EBGaramond", 9.5,
        "What does she write? Whose voice does she trust? What kind "
        "of name does she build, and what kind of woman does she "
        "become?")

    third = ("EBGaramond", 9.5,
        "Strength and Dignity is the second volume of Your Name Means "
        "Everything — a Bible-based guide written for the young woman "
        "stepping into the years that will set the trajectory for the "
        "rest of her life. Fourteen straight-talk chapters across four "
        "parts examine identity, character, purpose, relationships, "
        "work, money, and faith — not with opinions, but with what "
        "Scripture actually says.")

    pull = ("EBGaramond-Italic", 11,
        "“Strength and dignity are her clothing, and she smiles at the future.”")

    closing = ("EBGaramond", 9.5,
        "This is a book about becoming that woman — clothed in "
        "strength, walking in dignity, and unafraid of what comes next.")

    for font, size, text in [opening, second, third]:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.5

    # Pull quote in gold
    y -= line_height * 0.2
    c.setFillColor(GOLD_ACCENT)
    pull_lines = wrap_text(c, pull[2], pull[0], pull[1], text_width)
    c.setFont(pull[0], pull[1])
    for line in pull_lines:
        c.drawCentredString(flap_cx, y, line)
        y -= line_height + 1
    y -= line_height * 0.4
    c.setFillColor(CREAM)

    lines = wrap_text(c, closing[2], closing[0], closing[1], text_width)
    c.setFont(closing[0], closing[1])
    for line in lines:
        c.drawCentredString(flap_cx, y, line)
        y -= line_height


def draw_back_flap(c):
    """Back flap — About the Authors (Paul & Pam) + imprint."""
    safe_left  = BACK_FLAP_LEFT + FLAP_SAFETY
    safe_right = BACK_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (BACK_FLAP_LEFT + BACK_FLAP_RIGHT) / 2 + FLAP_VISUAL_SHIFT

    c.setFillColor(GOLD_ACCENT)
    y = DOC_H - 1.0 * inch
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(flap_cx, y, "About the Authors")
    y -= 10

    c.setStrokeColor(GOLD_ACCENT)
    c.setLineWidth(0.4)
    rule_hw = 0.4 * inch
    c.line(flap_cx - rule_hw, y, flap_cx + rule_hw, y)
    y -= 22

    c.setFillColor(CREAM)
    line_height = 12
    paragraphs = [
        ("EBGaramond", 9.5,
            "Paul and Pam Hainline write together from the conviction "
            "that the Scriptures, rightly read, are clear enough to "
            "settle every essential question of life — and that young "
            "women in particular deserve to be told the truth without "
            "flattery and without compromise."),
        ("EBGaramond", 9.5,
            "Their books are grounded in careful attention to the "
            "biblical text and shaped by decades of living the questions "
            "they write about. Strength and Dignity is the second volume "
            "in their Your Name Means Everything series, written for "
            "their daughters, granddaughters, and every young woman "
            "who is ready to hear what God has actually said."),
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
    c.setFillColor(GOLD_ACCENT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(flap_cx, mark_y, "NobleMind Press")
    c.setFillColor(MUTED_GOLD)
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(flap_cx, mark_y - 14, "noblemind.study")


def main():
    print('Generating Lulu HARDCOVER JACKET PDF for "Strength and Dignity"...')
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
    c.setTitle("Your Name Means Everything: Strength and Dignity — Lulu Hardcover Jacket")
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
