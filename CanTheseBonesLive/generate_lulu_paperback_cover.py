#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for Can These Bones Live?

Lulu specs (5.5x8.5 perfect bound paperback, B&W white paper):
  Trim size: 5.5" x 8.5"
  Spine width: PAGE_COUNT * 0.00264" (approximate for Lulu B&W white paper).
               Update with Lulu's exact value from their template tool before
               final upload.
  Bleed: 0.125" on all outside edges (not on spine edges)
  Total document width:  0.125 + 5.5 + spine + 5.5 + 0.125
  Total document height: 0.125 + 8.5 + 0.125 = 8.75"
  Safety margin: 0.25" inside trim edges for front cover text
  Safety margin: 0.5"  inside trim edges for back cover text
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "CanTheseBonesLive_Lulu_Paperback_Cover.pdf"
BG_IMAGE = BOOK_DIR / "CanTheseBonesLive_image_Hires.png"

# Fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Spine (Lulu's exact value from upload tool) ---
PAGE_COUNT = 148
SPINE_W = 0.393   # Lulu spec for 148-page B&W paperback

# --- Document dimensions ---
BLEED = 0.125
TRIM_W = 5.5
TRIM_H = 8.5
DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H = (BLEED + TRIM_H + BLEED) * inch

# --- Colors (drawn from the cover image — warm earth/bone palette) ---
DEEP_BROWN = Color(0.180, 0.145, 0.118)   # #2E2520 shadow
WARM_BROWN = Color(0.310, 0.235, 0.180)   # #4F3C2E earth
CREAM      = Color(0.949, 0.902, 0.820)   # #F2E6D1 bone
GOLD_LIGHT = Color(0.776, 0.608, 0.337)   # #C69B56 warm gold
GOLD_MUTED = Color(0.600, 0.478, 0.302)   # #997A4D muted gold
SLATE      = Color(0.608, 0.580, 0.525)   # #9B9486 stone

# --- Layout positions ---
BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = (BLEED + TRIM_W) * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = BACK_COVER_RIGHT
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = FRONT_COVER_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

TRIM_TOP = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch
COVER_CENTER_Y = DOC_H / 2

SAFETY = 0.5 * inch
FRONT_SAFETY = 0.25 * inch

FRONT_SAFE_LEFT = FRONT_TRIM_LEFT + FRONT_SAFETY
FRONT_SAFE_RIGHT = FRONT_TRIM_RIGHT - FRONT_SAFETY
FRONT_SAFE_WIDTH = FRONT_SAFE_RIGHT - FRONT_SAFE_LEFT


def check_front_safety(c, text, font_name, font_size, cx):
    w = c.stringWidth(text, font_name, font_size)
    half_w = w / 2
    left_edge = cx - half_w
    right_edge = cx + half_w
    left_margin = (left_edge - FRONT_TRIM_LEFT) / inch
    right_margin = (FRONT_TRIM_RIGHT - right_edge) / inch
    status = "OK" if min(left_margin, right_margin) >= 0.125 else "WARN"
    print(f'  [{status}] "{text}" ({font_name} {font_size}pt): '
          f'L={left_margin:.3f}" R={right_margin:.3f}"')


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
    """Fill the full document with a dark earth brown."""
    c.setFillColor(DEEP_BROWN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    cx = FRONT_CENTER_X

    # --- Background image (clipped to front cover area) ---
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

    # --- Title: "Can These" (italic, smaller) ---
    c.setFillColor(Color(0, 0, 0))
    c.setFont("EBGaramond-Italic", 22)
    c.drawCentredString(cx, DOC_H - 1.2 * inch, "Can These")
    check_front_safety(c, "Can These", "EBGaramond-Italic", 22, cx)

    # --- Title: "Bones Live?" (large, bold) ---
    c.setFont("EBGaramond", 44)
    c.drawCentredString(cx, DOC_H - 1.95 * inch, "Bones Live?")
    check_front_safety(c, "Bones Live?", "EBGaramond", 44, cx)

    # --- Decorative rule ---
    c.setStrokeColor(Color(0, 0, 0))
    c.setLineWidth(0.5)
    rule_hw = 0.6 * inch
    c.line(cx - rule_hw, DOC_H - 2.25 * inch, cx + rule_hw, DOC_H - 2.25 * inch)

    # --- Subtitle ---
    c.setFillColor(Color(0, 0, 0))
    c.setFont("EBGaramond-Italic", 12.5)
    c.drawCentredString(cx, DOC_H - 2.55 * inch, "How the Word and the Spirit")
    c.drawCentredString(cx, DOC_H - 2.82 * inch, "Make Dead Things Live")
    check_front_safety(c, "How the Word and the Spirit", "EBGaramond-Italic", 12, cx)
    check_front_safety(c, "Make Dead Things Live", "EBGaramond-Italic", 12, cx)

    # --- Bottom gradient for author readability ---
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

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    author_y = TRIM_BOTTOM + SAFETY + 0.2 * inch
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")
    check_front_safety(c, "P A U L   H A I N L I N E", "EBGaramond", 16, cx)


def draw_spine(c):
    # Spine intentionally left blank — 0.393" is too narrow for legible text.
    pass


def draw_back_cover(c):
    # Extra 0.25" inset beyond the Lulu safety margin so the blurb breathes
    # and doesn't crowd the trim edges.
    blurb_inset = SAFETY + 0.25 * inch
    safe_left = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X

    # --- Opening verse (italic, gold) ---
    y = TRIM_TOP - 1.0 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, y, "\u201cSon of man, can these bones live?\u201d")
    y -= 16
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y, "\u2014 Ezekiel 37:3")
    y -= 12

    # --- Thin rule ---
    y -= 8
    line_hw = 0.6 * inch
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 22

    # --- Body ---
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

    # --- Attribution ---
    y -= line_height * 0.3
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(
        cx, y,
        "Scripture quotations from the New American Standard Bible\u00ae (NASB)."
    )

    # --- Imprint (no ISBN for this printing) ---
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating Lulu PAPERBACK cover PDF for "Can These Bones Live?"...')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages, Lulu B&W white paper estimate)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')
    print(f'  Front cover safe text width: {FRONT_SAFE_WIDTH/inch:.2f}"')
    print(f'\nFront cover text safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Can These Bones Live? \u2014 Lulu Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
