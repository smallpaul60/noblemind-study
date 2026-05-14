#!/usr/bin/env python3
"""Generate Lulu LINEN-WRAP HARDCOVER DUST JACKET for 'The God Who Showed Up'.

Lulu specs (5.5x8.5 linen-wrap hardcover with dust jacket, 224 pages;
template verified 2026-05-14):
  Document size:     19.563" x 9.25"
  Spine width:       0.813"   (paperback 0.565" + ~0.248" board overhead;
                                the 0.243"±0.005 rule held across BM, FTB,
                                ANLW, and now TGWSU jackets)
  Front/back flap:   3.25" x 9.25" each
  Flap fold width:   0.25"
  Cover panel:       5.875" each side

Design carries the paperback palette (burning-bush front, deep night
+ cream + ember/flame gold) onto the jacket. Cover image is the raw
TheBurningBush.png — no baked-in text.

Visual shifts per ANLW calibration (2026-05-14):
  - Flap text:       0.25" toward spine
  - Back cover text: 0.10" toward spine
"""

import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401

from PIL import Image
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "The_God_Who_Showed_Up_Lulu_Hardcover_Jacket.pdf"
COVER_SOURCE = BOOK_DIR / "TheBurningBush.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (Lulu template) ---
DOC_W_IN   = 19.563
DOC_H_IN   = 9.25
SPINE_W_IN = 0.813
FLAP_W_IN  = 3.25
FOLD_W_IN  = 0.25
COVER_W_IN = (DOC_W_IN - 2 * FLAP_W_IN - 2 * FOLD_W_IN - SPINE_W_IN) / 2  # 5.875

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# --- Horizontal anchors ---
BACK_FLAP_LEFT   = 0
BACK_FLAP_RIGHT  = FLAP_W_IN * inch
BACK_FOLD_LEFT   = BACK_FLAP_RIGHT
BACK_FOLD_RIGHT  = BACK_FOLD_LEFT + FOLD_W_IN * inch
BACK_COVER_LEFT  = BACK_FOLD_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W_IN * inch
SPINE_LEFT       = BACK_COVER_RIGHT
SPINE_RIGHT      = SPINE_LEFT + SPINE_W_IN * inch
FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W_IN * inch
FRONT_FOLD_LEFT  = FRONT_COVER_RIGHT
FRONT_FOLD_RIGHT = FRONT_FOLD_LEFT + FOLD_W_IN * inch
FRONT_FLAP_LEFT  = FRONT_FOLD_RIGHT
FRONT_FLAP_RIGHT = DOC_W

BACK_CENTER_X  = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

# --- Colors (match the paperback palette) ---
DEEP_NIGHT  = Color(0.071, 0.067, 0.090)   # #121117
CREAM       = Color(0.949, 0.910, 0.804)   # #F2E8CD
EMBER       = Color(0.890, 0.557, 0.224)   # #E38E39 — flame gold
EMBER_DEEP  = Color(0.706, 0.380, 0.122)   # #B46120
SLATE       = Color(0.580, 0.555, 0.490)   # #948D7D

# --- Safety per cover-clearance memory ---
FLAP_SAFETY      = 0.75 * inch
BACK_BLURB_INSET = 1.00 * inch
COVER_SAFETY     = 0.5  * inch
BACK_VISUAL_SHIFT = 0.10 * inch
FLAP_VISUAL_SHIFT = 0.25 * inch


def _load_hires_cover():
    src = Image.open(str(COVER_SOURCE)).convert("RGB")
    hires = src.resize((src.width * 2, src.height * 2), Image.LANCZOS)
    buf = BytesIO()
    hires.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return ImageReader(buf)


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for w in words:
        trial = f"{current} {w}".strip() if current else w
        if c.stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    c.setFillColor(DEEP_NIGHT)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    cx = FRONT_CENTER_X
    img = _load_hires_cover()
    iw, ih = img.getSize()
    img_aspect = iw / ih
    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

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
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # --- Top wash so title reads against the flame + sky ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    steps = 220
    top_h = 2.8 * inch
    for i in range(steps):
        alpha = 0.50 * (1 - i / steps) ** 1.4
        c.setFillColor(Color(0.02, 0.02, 0.03, alpha))
        y = DOC_H - (i * top_h / steps)
        h = top_h / steps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title block ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 28)
    c.drawCentredString(cx, DOC_H - 1.05 * inch, "The God Who")

    c.setFont("EBGaramond", 40)
    c.drawCentredString(cx, DOC_H - 1.7 * inch, "Showed Up")

    c.setFont("EBGaramond-Italic", 13.5)
    c.drawCentredString(cx, DOC_H - 2.13 * inch, "What His Names Reveal About Who He Is")

    # --- Bottom wash so author reads against the figure's robe ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    bot_h = 1.8 * inch
    bsteps = 220
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.02, 0.02, 0.03, alpha))
        y = bot_h * (1 - i / bsteps)
        h = bot_h / bsteps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Authors (co-authored) ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    c.drawCentredString(cx, COVER_SAFETY + 0.45 * inch, "P A U L   &   P A M   H A I N L I N E")


def draw_spine(c):
    """0.813\" spine — rotated cream title + ember author."""
    c.saveState()
    c.translate(SPINE_CENTER_X, DOC_H - 0.5 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 15)
    c.drawString(0, -5.5, "The God Who Showed Up")
    c.restoreState()

    c.saveState()
    c.translate(SPINE_CENTER_X, 0.5 * inch + 1.7 * inch)
    c.rotate(-90)
    c.setFillColor(EMBER)
    c.setFont("EBGaramond", 11)
    c.drawString(0, -4, "Paul & Pam Hainline")
    c.restoreState()


def draw_back_cover(c):
    safe_left  = BACK_COVER_LEFT + BACK_BLURB_INSET
    safe_right = BACK_COVER_RIGHT - BACK_BLURB_INSET
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X + BACK_VISUAL_SHIFT

    # --- Anchor verse: Exodus 3:14 ---
    y = DOC_H - 1.0 * inch
    c.setFillColor(EMBER)
    c.setFont("EBGaramond-Italic", 11)
    verse_lines = [
        "“God said to Moses, ‘I AM WHO I AM’;",
        "and He said, ‘Thus you shall say to the",
        "sons of Israel, I AM has sent me to you.’”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 15
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— Exodus 3:14")
    y -= 22

    # --- Ember rule ---
    y -= 6
    c.setStrokeColor(EMBER)
    c.setLineWidth(0.5)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "God did not just send His word into history. He showed up — by name.",
        "He met Hagar in the wilderness and let her name Him El Roi, "
        "the God Who Sees. He told Abraham He was El Shaddai. He gave "
        "Moses a personal name from a burning bush. He provided on "
        "Mount Moriah, healed at Marah, gave peace at the threshing "
        "floor, shepherded His people in Psalm 23, and finally came in "
        "person as Immanuel — God With Us.",
        "Twelve chapters, twelve names. Each one is a moment when God "
        "stepped into the story and let a specific human being know "
        "exactly who He is. Together, they form a portrait — not of an "
        "idea, but of the living God who keeps showing up.",
        "If you have ever wished you could meet Him for yourself, this book is the introduction.",
    ]
    for i, para in enumerate(body):
        is_hook = (i == 0)
        font = "EBGaramond-Italic" if is_hook else "EBGaramond"
        size = 10.5 if is_hook else 9.5
        lh = 13.5 if is_hook else 13
        lines = wrap_text(c, para, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= lh
        y -= lh * 0.4

    # --- Attribution ---
    y -= 5
    c.setFillColor(EMBER_DEEP)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = COVER_SAFETY + 0.5 * inch
    c.setFillColor(EMBER)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


def draw_front_flap(c):
    """Teaser — Front (right) flap: shift text LEFT toward spine."""
    safe_left  = FRONT_FLAP_LEFT + FLAP_SAFETY
    safe_right = FRONT_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (FRONT_FLAP_LEFT + FRONT_FLAP_RIGHT) / 2 - FLAP_VISUAL_SHIFT

    c.setFillColor(CREAM)
    y = DOC_H - 0.95 * inch
    line_height = 11.5

    blocks = [
        ("EBGaramond-Italic", 10,
         "A name was never just a label. In Scripture it was a revelation."),
        ("EBGaramond", 9,
         "And the God of the Bible kept giving Himself new ones — each one tied "
         "to a moment when a human being needed to know that particular truth "
         "about Him."),
    ]
    pull = ("EBGaramond-Italic", 11.5,
            "“I AM WHO I AM.”")
    rest = [
        ("EBGaramond", 9,
         "Hagar called Him El Roi from the desert. Abraham learned He was El "
         "Shaddai before the covenant. Moses heard YAHWEH from a burning bush. "
         "Gideon found Him as Jehovah Shalom under an oak tree. David sang of "
         "Him as Jehovah Rohi."),
        ("EBGaramond", 9,
         "And then, in Matthew 1, a child was born and an angel told Joseph "
         "exactly what to call Him: Immanuel — God With Us."),
        ("EBGaramond", 9,
         "Twelve chapters, twelve names, walking through the Bible in the order "
         "God revealed them. Every name drawn directly from the text."),
        ("EBGaramond-Italic", 9.5,
         "Each one is a moment when God showed up. Together they form a portrait of the living God."),
    ]

    for font, size, text in blocks:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.45

    # Pull quote (ember)
    y -= line_height * 0.2
    c.setFillColor(EMBER)
    c.setFont(pull[0], pull[1])
    c.drawCentredString(flap_cx, y, pull[2])
    y -= line_height + 1
    c.setFont("EBGaramond", 9)
    c.drawCentredString(flap_cx, y, "— Exodus 3:14")
    y -= line_height * 1.4

    c.setFillColor(CREAM)
    for font, size, text in rest:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.4


def draw_back_flap(c):
    """About the Authors. Back (left) flap: shift text RIGHT toward spine."""
    safe_left  = BACK_FLAP_LEFT + FLAP_SAFETY
    safe_right = BACK_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (BACK_FLAP_LEFT + BACK_FLAP_RIGHT) / 2 + FLAP_VISUAL_SHIFT

    c.setFillColor(EMBER)
    y = DOC_H - 0.95 * inch
    c.setFont("EBGaramond-Italic", 12.5)
    c.drawCentredString(flap_cx, y, "About the Authors")
    y -= 10

    c.setStrokeColor(EMBER)
    c.setLineWidth(0.4)
    rule_hw = 0.45 * inch
    c.line(flap_cx - rule_hw, y, flap_cx + rule_hw, y)
    y -= 22

    c.setFillColor(CREAM)
    line_height = 12
    paragraphs = [
        ("EBGaramond", 9.5,
         "Paul Hainline writes using the Berean approach of examining "
         "the Scriptures daily to see whether these things are so "
         "(Acts 17:11), and letting Scripture interpret Scripture."),
        ("EBGaramond", 9.5,
         "He is the author of multiple books on Bible study, evangelism, "
         "and Christian living, including A New and Living Way, From the "
         "Beginning, Change the Mind Change the Man, The Character No One "
         "Could Invent, Why Do You Delay, Bridge Moments, The Last Week "
         "of the Lamb, and Can These Bones Live?"),
        ("EBGaramond", 9.5,
         "He co-authored The God Who Showed Up with his wife Pam, and they "
         "write together for teen readers in Your Name Means Everything: "
         "A Good Name and Strength and Dignity."),
    ]
    for font, size, text in paragraphs:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # --- Imprint at foot of flap ---
    mark_y = COVER_SAFETY + 0.6 * inch
    c.setFillColor(EMBER)
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(flap_cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(flap_cx, mark_y - 12, "noblemind.study")


def main():
    print('Generating Lulu DUST JACKET for "The God Who Showed Up"...')
    print(f'  Document size:  {DOC_W_IN}" x {DOC_H_IN}"')
    print(f'  Spine:          {SPINE_W_IN}"')
    print(f'  Cover panel:    {COVER_W_IN}" x {DOC_H_IN}" each')
    print(f'  Flap:           {FLAP_W_IN}" x {DOC_H_IN}"   Fold: {FOLD_W_IN}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("The God Who Showed Up — Lulu Hardcover Dust Jacket")

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
