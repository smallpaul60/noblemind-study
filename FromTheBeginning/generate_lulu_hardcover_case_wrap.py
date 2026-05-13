#!/usr/bin/env python3
"""Generate Lulu CASE-WRAP hardcover cover for 'From the Beginning'.

Design mirrors the published paperback (sunrise portrait + deep midnight
blue + cream + gold). The hardcover spine is wider because the case
binds around boards.

Lulu specs (5.5x8.5 hardcover case-wrap):
  Total document size:  PANEL_W*2 + SPINE_W + WRAP*2  by
                        PANEL_H + WRAP*2
  Panel face (board):   5.75" x 9.00"  (board extends 0.125" past trim
                                         on top/bottom/outside)
  Wrap area:            0.625" past board edge, all four sides
  Safety margin:        0.625" inside board edge

SPINE WIDTH IS AN ESTIMATE until verified against Lulu's downloaded
case-wrap template. From other titles on the same paper stock, the
hardcover spine sits ~0.243" wider than the paperback spine (board
thickness). Paperback spine = 0.407" (Lulu template), so hardcover
spine ≈ 0.650". Update SPINE_W_IN when the real template is in hand.
"""

import sys
from pathlib import Path

# Register Standard-14 font overrides (Helvetica → embedded Liberation Sans)
# BEFORE constructing the Canvas. Without this Lulu preflight reports
# unembedded Helvetica and rejects the cover.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "FromTheBeginning_Lulu_Hardcover_CaseWrap.pdf"
BG_IMAGE = BOOK_DIR / "FromTheBeginning_Portrait_Hires.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# ============================================================================
# DOCUMENT DIMENSIONS — Lulu hardcover case-wrap for 5.5x8.5 interior
# (154 B&W white pages). UPDATE SPINE_W_IN with Lulu's template value
# before final upload.
# ============================================================================
PAGE_COUNT  = 154
SPINE_W_IN  = 0.650   # ESTIMATE (paperback 0.407 + ~0.243 board overhead)

PANEL_W_IN  = 5.75
PANEL_H_IN  = 9.00
WRAP_IN     = 0.625
SAFETY_IN   = 0.625

DOC_W_IN    = PANEL_W_IN * 2 + SPINE_W_IN + WRAP_IN * 2
DOC_H_IN    = PANEL_H_IN + WRAP_IN * 2
DOC_W       = DOC_W_IN * inch
DOC_H       = DOC_H_IN * inch

# Horizontal anchors
WRAP_LEFT_RIGHT  = WRAP_IN * inch
BACK_FACE_LEFT   = WRAP_LEFT_RIGHT
BACK_FACE_RIGHT  = BACK_FACE_LEFT + PANEL_W_IN * inch
SPINE_LEFT       = BACK_FACE_RIGHT
SPINE_RIGHT      = SPINE_LEFT + SPINE_W_IN * inch
FRONT_FACE_LEFT  = SPINE_RIGHT
FRONT_FACE_RIGHT = FRONT_FACE_LEFT + PANEL_W_IN * inch

# Vertical anchors
FACE_BOTTOM = WRAP_IN * inch
FACE_TOP    = FACE_BOTTOM + PANEL_H_IN * inch
FACE_CY     = (FACE_BOTTOM + FACE_TOP) / 2

BACK_CENTER_X  = (BACK_FACE_LEFT + BACK_FACE_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2
FRONT_CENTER_X = (FRONT_FACE_LEFT + FRONT_FACE_RIGHT) / 2

# Safety-inset bounds (text/critical art must stay inside)
FRONT_SAFE_LEFT   = FRONT_FACE_LEFT + SAFETY_IN * inch
FRONT_SAFE_RIGHT  = FRONT_FACE_RIGHT - SAFETY_IN * inch
FRONT_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
FRONT_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch

BACK_SAFE_LEFT   = BACK_FACE_LEFT + SAFETY_IN * inch
BACK_SAFE_RIGHT  = BACK_FACE_RIGHT - SAFETY_IN * inch
BACK_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
BACK_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch
BACK_TEXT_WIDTH  = BACK_SAFE_RIGHT - BACK_SAFE_LEFT

# --- Colors (matched to the paperback) ---
DEEP_BLUE  = Color(0.067, 0.118, 0.216)   # #112138
CREAM      = Color(0.961, 0.902, 0.784)   # #F5E6C8
GOLD_LIGHT = Color(0.831, 0.659, 0.282)   # #D4A848
GOLD_MUTED = Color(0.631, 0.529, 0.322)   # #A18752
SLATE      = Color(0.580, 0.631, 0.706)   # #94A1B4


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip() if current else word
        if c.stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    """Solid deep midnight blue across the whole document (wraps + spine
    + panels). The front face will be overlaid with the sunrise image."""
    c.setFillColor(DEEP_BLUE)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_face_image(c):
    """Place the sunrise portrait, sized to fill the full front face
    (5.75 x 9.0). The wrap area on the front side stays deep blue and
    folds around the board to the inside — invisible after binding."""
    img = ImageReader(str(BG_IMAGE))
    iw, ih = img.getSize()
    img_aspect = iw / ih
    target_w = PANEL_W_IN * inch
    target_h = PANEL_H_IN * inch
    target_aspect = target_w / target_h

    # Cover the full face area, cropping the longer dimension
    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = FRONT_CENTER_X - draw_w / 2
        draw_y = FACE_BOTTOM
    else:
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = FRONT_FACE_LEFT
        draw_y = FACE_CY - draw_h / 2

    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, target_h)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()


def draw_front_face_overlays(c):
    """Top and bottom dark gradients so the cream title and author read
    against the brightest parts of the sunrise."""
    target_w = PANEL_W_IN * inch
    steps = 40

    # Top gradient — for title block
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, PANEL_H_IN * inch)
    path.close()
    c.clipPath(path, stroke=0)
    top_h = 4.0 * inch
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.5
        c.setFillColor(Color(0.06, 0.08, 0.14, alpha))
        y = FACE_TOP - (i * top_h / steps)
        h = top_h / steps + 1
        c.rect(FRONT_FACE_LEFT, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # Bottom gradient — for author block
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, PANEL_H_IN * inch)
    path.close()
    c.clipPath(path, stroke=0)
    bot_h = 2.0 * inch
    for i in range(steps):
        alpha = 0.5 * (i / steps) ** 1.5
        c.setFillColor(Color(0.06, 0.08, 0.14, alpha))
        y = FACE_BOTTOM + bot_h * (1 - i / steps)
        h = bot_h / steps + 1
        c.rect(FRONT_FACE_LEFT, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()


def draw_front_face_text(c):
    """Title / subtitle / author — matches the paperback typography."""
    cx = FRONT_CENTER_X

    # Title — italic "From the"
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 22)
    c.drawCentredString(cx, FACE_TOP - 1.5 * inch, "From the")

    # Title — large "Beginning"
    c.setFont("EBGaramond", 48)
    c.drawCentredString(cx, FACE_TOP - 2.2 * inch, "Beginning")

    # Subtitle — deep blue against the bright horizon
    c.setFillColor(DEEP_BLUE)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, FACE_TOP - 2.85 * inch, "The Gospel from the Ground Up")

    # Author — cream, in the bottom gradient
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    author_y = FACE_BOTTOM + SAFETY_IN * inch + 0.2 * inch
    c.drawCentredString(cx, author_y, "P A U L   &   P A M   H A I N L I N E")


def draw_spine(c):
    """Rotated spine — cream title + author. Spine width ~0.650" is
    comfortable for legible text."""
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_CY)
    c.rotate(270)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 13)
    c.drawCentredString(0, 4, "From the Beginning")
    c.setFont("EBGaramond", 10)
    c.drawCentredString(0, -10, "Paul & Pam Hainline")
    c.restoreState()


def draw_back_face(c):
    """Back face — Genesis 1:1 verse + body blurb + Scripture attribution
    + NobleMind Press imprint. Same copy as the paperback back cover."""
    cx = BACK_CENTER_X

    # Opening verse (italic, gold)
    y = FACE_TOP - 1.0 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(cx, y, "“In the beginning God created the heavens and the earth.”")
    y -= 14
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, y, "— Genesis 1:1")
    y -= 10

    # Decorative line
    y -= 8
    line_hw = 0.6 * inch
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 20

    # Body (cream)
    c.setFillColor(CREAM)
    line_height = 13.5
    body_paragraphs = [
        "You don’t need a church background to read this book. You don’t need to know anything about the Bible. You just need to be willing to look.",
        "From the Beginning starts where the Bible starts — with a God who created you on purpose, who knew you before you were born, and who had a plan for your rescue before the world began. In ten chapters, it walks you through the whole story: who God is, what went wrong, the long thread of promise that runs through Scripture, and the Christ who fulfilled every word of it.",
        "This is not a book of opinions. Every claim is anchored in Scripture. Every chapter builds on the last. And by the end, you’ll understand not just what God did — but what He asks you to do about it.",
        "If you’ve been looking for the starting line, this is it.",
    ]
    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10, BACK_TEXT_WIDTH)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # Scripture attribution
    y -= line_height * 0.3
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y, "Scripture quotations from the New American Standard Bible® (NASB).")

    # Imprint (no ISBN yet)
    mark_y = BACK_SAFE_BOTTOM + 0.25 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print('Generating Lulu HARDCOVER case-wrap PDF for "From the Beginning"...')
    print(f'  Document size: {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}"')
    print(f'  Panel face size: {PANEL_W_IN}" x {PANEL_H_IN}"')
    print(f'  Spine width: {SPINE_W_IN:.3f}"  (ESTIMATE — verify against Lulu template)')
    print(f'  Wrap: {WRAP_IN}" past board edge')
    print(f'  Safety: {SAFETY_IN}" inside board edge')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("From the Beginning — Lulu Hardcover Case-Wrap")

    draw_background(c)
    draw_front_face_image(c)
    draw_front_face_overlays(c)
    draw_front_face_text(c)
    draw_back_face(c)
    draw_spine(c)

    c.save()
    print(f"\nCase-wrap saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
