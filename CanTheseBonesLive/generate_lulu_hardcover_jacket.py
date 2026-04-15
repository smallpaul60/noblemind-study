#!/usr/bin/env python3
"""Generate Lulu linen-hardcover DUST JACKET for Can These Bones Live?

Lulu specs (from upload page for 148-page 5.5x8.5 linen hardcover w/ jacket):
  Document size:     19.375" x 9.25"
  Spine width:       0.625"
  Front/back flap:   3.25" x 9.25" each
  Flap fold width:   0.25" (between cover panel and flap, each side)

Layout (left to right):
  [3.25 back flap][0.25 fold][5.875 back cover][0.625 spine]
  [5.875 front cover][0.25 fold][3.25 front flap]
  Sum: 3.25 + 0.25 + 5.875 + 0.625 + 5.875 + 0.25 + 3.25 = 19.375 ✓

Design matches the approved paperback cover — same image, black title and
subtitle, cream author block at the bottom. Flaps carry a teaser (front)
and the author bio (back). Spine is intentionally blank.
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "CanTheseBonesLive_Lulu_Hardcover_Jacket.pdf"
BG_IMAGE = BOOK_DIR / "CanTheseBonesLive_image_Hires.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (Lulu spec) ---
DOC_W_IN = 19.375
DOC_H_IN = 9.25
SPINE_W_IN = 0.625
FLAP_W_IN = 3.25
FOLD_W_IN = 0.25
COVER_W_IN = (DOC_W_IN - 2 * FLAP_W_IN - 2 * FOLD_W_IN - SPINE_W_IN) / 2  # 5.875

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# --- Horizontal layout anchors ---
BACK_FLAP_LEFT = 0
BACK_FLAP_RIGHT = FLAP_W_IN * inch
BACK_FOLD_LEFT = BACK_FLAP_RIGHT
BACK_FOLD_RIGHT = BACK_FOLD_LEFT + FOLD_W_IN * inch
BACK_COVER_LEFT = BACK_FOLD_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W_IN * inch
SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W_IN * inch
FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W_IN * inch
FRONT_FOLD_LEFT = FRONT_COVER_RIGHT
FRONT_FOLD_RIGHT = FRONT_FOLD_LEFT + FOLD_W_IN * inch
FRONT_FLAP_LEFT = FRONT_FOLD_RIGHT
FRONT_FLAP_RIGHT = DOC_W

BACK_CENTER_X = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

# --- Colors (match paperback palette) ---
DEEP_BROWN = Color(0.180, 0.145, 0.118)
WARM_BROWN = Color(0.310, 0.235, 0.180)
CREAM      = Color(0.949, 0.902, 0.820)
GOLD_LIGHT = Color(0.776, 0.608, 0.337)
GOLD_MUTED = Color(0.600, 0.478, 0.302)
SLATE      = Color(0.608, 0.580, 0.525)
BLACK      = Color(0, 0, 0)

# --- Safety margins ---
# Text must stay at least 0.5" from any trim/fold edge on flaps and back
# cover; front cover uses 0.25" on top/sides because title typography is
# already generously inset.
COVER_SAFETY = 0.5 * inch
FLAP_SAFETY = 0.5 * inch
BACK_BLURB_INSET = 0.75 * inch   # extra breathing room inside back cover

# Visual-balance shifts (nudge text toward the spine). The geometric
# panel centers are mathematically symmetric, but the Lulu preview reads
# flap text as pulled toward the outer edges, so we pre-shift it inward.
FLAP_VISUAL_SHIFT = 0.20 * inch
BACK_VISUAL_SHIFT = 0.10 * inch


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


def draw_background(c):
    """Fill the entire document with deep brown — this is what shows on the
    flaps and spine, and behind any letterboxing on the covers."""
    c.setFillColor(DEEP_BROWN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    cx = FRONT_CENTER_X

    img = ImageReader(str(BG_IMAGE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    # Scale-to-fill
    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = cx - draw_w / 2
        draw_y = 0
    else:
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = target_x
        draw_y = (target_h - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # Title "Can These" (italic)
    c.setFillColor(BLACK)
    c.setFont("EBGaramond-Italic", 22)
    c.drawCentredString(cx, DOC_H - 1.2 * inch, "Can These")

    # Title "Bones Live?" (bold)
    c.setFont("EBGaramond", 44)
    c.drawCentredString(cx, DOC_H - 1.95 * inch, "Bones Live?")

    # Decorative rule
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    rule_hw = 0.6 * inch
    c.line(cx - rule_hw, DOC_H - 2.25 * inch, cx + rule_hw, DOC_H - 2.25 * inch)

    # Subtitle
    c.setFillColor(BLACK)
    c.setFont("EBGaramond-Italic", 12.5)
    c.drawCentredString(cx, DOC_H - 2.55 * inch, "How God Has Always Made")
    c.drawCentredString(cx, DOC_H - 2.82 * inch, "Dead Things Live")

    # Bottom gradient for author readability
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_COVER_LEFT, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    bottom_grad_height = 1.8 * inch
    bsteps = 280
    for i in range(bsteps):
        alpha = 0.6 * (i / bsteps) ** 1.5
        c.setFillColor(Color(0.10, 0.07, 0.05, alpha))
        y = bottom_grad_height * (1 - i / bsteps)
        h = bottom_grad_height / bsteps + 1
        c.rect(FRONT_COVER_LEFT, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # Author
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    author_y = COVER_SAFETY + 0.45 * inch
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")


def draw_spine(c):
    # Blank — 0.625" is narrow enough that we keep it clean like the paperback.
    pass


def draw_back_cover(c):
    safe_left = BACK_COVER_LEFT + BACK_BLURB_INSET
    safe_right = BACK_COVER_RIGHT - BACK_BLURB_INSET
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X + BACK_VISUAL_SHIFT

    # Opening verse (italic, gold)
    y = DOC_H - 1.0 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, y, "\u201cSon of man, can these bones live?\u201d")
    y -= 16
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y, "\u2014 Ezekiel 37:3")
    y -= 12

    # Thin rule
    y -= 8
    line_hw = 0.6 * inch
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 22

    # Body
    c.setFillColor(CREAM)
    line_height = 13.5
    body_paragraphs = [
        "God showed Ezekiel a valley of dry bones and asked the one question only God can answer: can these live?",
        "The answer, then and now, is the same \u2014 and it comes by the same means. The word of God gives form. The Spirit of God gives life. Together, and only together, they make dead things stand.",
        "This book traces that single pattern through the whole Bible, from the dust of Eden to the rushing wind of Pentecost, from the valley of bones to the seven letters Christ dictated to His own church. At every scale \u2014 creation, restoration, new birth, conversion \u2014 the mechanism is the same. Where the word goes silent or the breath is withheld, the bones dry out. Where both are present, the dead rise.",
        "Eleven chapters. One question. One pattern. One God who has been doing this from the beginning.",
    ]
    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # Attribution
    y -= line_height * 0.3
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(
        cx, y,
        "Scripture quotations from the New American Standard Bible\u00ae (NASB)."
    )

    # Imprint
    mark_y = COVER_SAFETY + 0.5 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")


def draw_front_flap(c):
    """Teaser / hook — draws the reader into the book."""
    safe_left = FRONT_FLAP_LEFT + FLAP_SAFETY
    safe_right = FRONT_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    # Pull text toward the spine (shift left for the right-hand flap)
    flap_cx = (FRONT_FLAP_LEFT + FRONT_FLAP_RIGHT) / 2 - FLAP_VISUAL_SHIFT

    c.setFillColor(CREAM)
    y = DOC_H - 0.85 * inch
    line_height = 11

    opening = ("EBGaramond-Italic", 9.5,
        "The valley is silent. There is no wind. No birds. The ground is "
        "covered with bones \u2014 human bones, bleached and dry, as far "
        "as a man can see.")

    second = ("EBGaramond", 9,
        "This is where God brought His prophet. And then He asked him a "
        "question only God would dare ask.")

    pull_font, pull_size, pull_text = ("EBGaramond-Italic", 11,
        "Son of man, can these bones live?")

    rest = [
        ("EBGaramond", 9,
            "That question hangs over every generation that has watched "
            "the life of God depart from a people. It hangs over the "
            "Church today."),
        ("EBGaramond", 9,
            "Scripture answers it \u2014 not with a platitude, but with a "
            "pattern. The word of God gives form. The Spirit of God gives "
            "life. Together, and only together, they make dead things stand."),
        ("EBGaramond", 9,
            "From the dust of Eden to the rushing wind of Pentecost, from "
            "the valley of bones to the seven letters Christ dictated to "
            "His own church, the mechanism is the same. And it still works."),
    ]

    for font, size, text in [opening, second]:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.5

    # Pull quote (gold)
    y -= line_height * 0.3
    c.setFillColor(GOLD_LIGHT)
    c.setFont(pull_font, pull_size)
    c.drawCentredString(flap_cx, y, "\u201c" + pull_text + "\u201d")
    y -= line_height * 1.6
    c.setFillColor(CREAM)

    for font, size, text in rest:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.4


def draw_back_flap(c):
    """About the Author."""
    safe_left = BACK_FLAP_LEFT + FLAP_SAFETY
    safe_right = BACK_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    # Pull text toward the spine (shift right for the left-hand flap)
    flap_cx = (BACK_FLAP_LEFT + BACK_FLAP_RIGHT) / 2 + FLAP_VISUAL_SHIFT

    c.setFillColor(GOLD_LIGHT)
    y = DOC_H - 0.85 * inch
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(flap_cx, y, "About the Author")
    y -= 8

    # Thin rule (centered)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.4)
    rule_hw = 0.4 * inch
    c.line(flap_cx - rule_hw, y, flap_cx + rule_hw, y)
    y -= 20

    c.setFillColor(CREAM)
    line_height = 11.5
    paragraphs = [
        ("EBGaramond", 9,
            "Paul Hainline is a student of God\u2019s Word, writing with "
            "the conviction that Scripture interprets Scripture. Together "
            "with his wife Pam, he publishes books grounded in careful "
            "attention to the biblical text \u2014 books written to point "
            "readers back to the Scriptures themselves."),
        ("EBGaramond", 9,
            "He is the founder of NobleMind Press."),
    ]
    for font, size, text in paragraphs:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # Imprint block at bottom of flap
    mark_y = COVER_SAFETY + 0.6 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(flap_cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(flap_cx, mark_y - 12, "noblemind.study")


def main():
    print('Generating Lulu HARDCOVER JACKET PDF for "Can These Bones Live?"...')
    print(f'  Document size:  {DOC_W_IN}" x {DOC_H_IN}"')
    print(f'  Spine:          {SPINE_W_IN}"')
    print(f'  Cover panel:    {COVER_W_IN}" x {DOC_H_IN}" each')
    print(f'  Flap:           {FLAP_W_IN}" x {DOC_H_IN}"   Fold: {FOLD_W_IN}"')
    print()
    print(f'  Panel x-positions (inches):')
    print(f'    back flap  : {BACK_FLAP_LEFT/inch:.3f} .. {BACK_FLAP_RIGHT/inch:.3f}')
    print(f'    back cover : {BACK_COVER_LEFT/inch:.3f} .. {BACK_COVER_RIGHT/inch:.3f}')
    print(f'    spine      : {SPINE_LEFT/inch:.3f} .. {SPINE_RIGHT/inch:.3f}')
    print(f'    front cover: {FRONT_COVER_LEFT/inch:.3f} .. {FRONT_COVER_RIGHT/inch:.3f}')
    print(f'    front flap : {FRONT_FLAP_LEFT/inch:.3f} .. {FRONT_FLAP_RIGHT/inch:.3f}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Can These Bones Live? \u2014 Lulu Hardcover Jacket")

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
