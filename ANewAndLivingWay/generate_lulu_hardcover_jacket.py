#!/usr/bin/env python3
"""Generate Lulu LINEN-WRAP HARDCOVER DUST JACKET for 'A New and Living Way'.

Lulu specs (5.5x8.5 linen-wrap hardcover with dust jacket, 202 pages;
template verified 2026-05-14):
  Document size:     19.5" x 9.25"
  Spine width:       0.75"
  Front/back flap:   3.25" x 9.25" each
  Flap fold width:   0.25" (between cover panel and flap, each side)

Layout (left to right):
  [3.25 back flap][0.25 fold][5.875 back cover][0.75 spine]
  [5.875 front cover][0.25 fold][3.25 front flap]
  Sum: 3.25 + 0.25 + 5.875 + 0.75 + 5.875 + 0.25 + 3.25 = 19.5 ✓

Design carries the paperback palette (Gethsemane painting on the front,
deep midnight + cream + copper) onto the jacket. Cover image is the raw
in_the_garden.png — no baked-in text from cover_front.jpg.

Safety per memory note on cover clearance:
  - Flap text:       0.75" each side
  - Back cover text: 1.0" inset (visible-when-bound includes wrap)
  - Visual shift:    0.10" toward spine on flaps and back (CTBL used 0.20"
                     which the calibration memory says may over-compensate)
"""

import sys
from io import BytesIO
from pathlib import Path

# Register Standard-14 font overrides BEFORE constructing Canvas.
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
OUTPUT = BOOK_DIR / "A_New_and_Living_Way_Lulu_Hardcover_Jacket.pdf"
COVER_SOURCE = BOOK_DIR / "in_the_garden.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (Lulu template) ---
DOC_W_IN   = 19.5
DOC_H_IN   = 9.25
SPINE_W_IN = 0.75
FLAP_W_IN  = 3.25
FOLD_W_IN  = 0.25
COVER_W_IN = (DOC_W_IN - 2 * FLAP_W_IN - 2 * FOLD_W_IN - SPINE_W_IN) / 2  # 5.875

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# --- Horizontal anchors (left to right) ---
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

# --- Colors (match the paperback) ---
DEEP_NIGHT  = Color(0.055, 0.075, 0.094)   # #0E1318
CREAM       = Color(0.941, 0.902, 0.800)   # #F0E6CC
COPPER      = Color(0.706, 0.314, 0.165)   # #B4502A — cloak accent
COPPER_DARK = Color(0.545, 0.259, 0.149)   # #8B4226
SLATE       = Color(0.545, 0.529, 0.475)   # #8B8779

# --- Safety per cover-clearance memory ---
FLAP_SAFETY      = 0.75 * inch
BACK_BLURB_INSET = 1.00 * inch
COVER_SAFETY     = 0.5  * inch

# Visual shifts — text nudged toward the spine because the jacket wraps
# around the board edges. Per Paul's Lulu preview review 2026-05-14,
# the flaps needed a noticeably bigger shift than the back cover. Back
# cover looked balanced at 0.10"; flaps required ~0.25".
BACK_VISUAL_SHIFT = 0.10 * inch
FLAP_VISUAL_SHIFT = 0.25 * inch


def _load_hires_cover():
    """2x LANCZOS upscale so the front face PPI clears Lulu's 200 floor."""
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
    """Deep midnight across the whole document. The cover image overlays
    the front face; the flaps and back face will paint over this base."""
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

    # Scale-to-fill (no letterbox per cover-clearance memo)
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

    # --- Top wash so title reads against the moonlit sky ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    steps = 220
    top_h = 2.8 * inch
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.4
        c.setFillColor(Color(0.02, 0.025, 0.035, alpha))
        y = DOC_H - (i * top_h / steps)
        h = top_h / steps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title block ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 28)
    c.drawCentredString(cx, DOC_H - 1.1 * inch, "A New and")

    c.setFont("EBGaramond", 40)
    c.drawCentredString(cx, DOC_H - 1.75 * inch, "Living Way")

    c.setFont("EBGaramond-Italic", 13.5)
    c.drawCentredString(cx, DOC_H - 2.18 * inch, "What the Bible Teaches About Prayer")

    # --- Bottom wash so author reads against the figure's robe ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    bot_h = 1.8 * inch
    bsteps = 220
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.02, 0.025, 0.035, alpha))
        y = bot_h * (1 - i / bsteps)
        h = bot_h / bsteps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    c.drawCentredString(cx, COVER_SAFETY + 0.45 * inch, "P A U L   H A I N L I N E")


def draw_spine(c):
    """0.75\" spine — small rotated cream title + copper author."""
    c.saveState()
    c.translate(SPINE_CENTER_X, DOC_H - 0.5 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 14)
    c.drawString(0, -5, "A New and Living Way")
    c.restoreState()

    c.saveState()
    c.translate(SPINE_CENTER_X, 0.5 * inch + 1.6 * inch)
    c.rotate(-90)
    c.setFillColor(COPPER)
    c.setFont("EBGaramond", 10)
    c.drawString(0, -3.5, "Paul Hainline")
    c.restoreState()


def draw_back_cover(c):
    """Back cover — verse + body blurb + imprint. 1.0" inset on both
    sides; text shifted 0.10" toward spine for visible-when-bound balance."""
    safe_left  = BACK_COVER_LEFT + BACK_BLURB_INSET
    safe_right = BACK_COVER_RIGHT - BACK_BLURB_INSET
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X + BACK_VISUAL_SHIFT

    # --- Anchor verse (italic copper) ---
    y = DOC_H - 1.0 * inch
    c.setFillColor(COPPER)
    c.setFont("EBGaramond-Italic", 10.5)
    verse_lines = [
        "“Therefore, brethren, since we have",
        "confidence to enter the holy place by",
        "the blood of Jesus, by a new and living",
        "way which He inaugurated for us …",
        "let us draw near with a sincere heart",
        "in full assurance of faith.”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 14
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— Hebrews 10:19–22")
    y -= 20

    # --- Copper rule ---
    y -= 6
    c.setStrokeColor(COPPER)
    c.setLineWidth(0.5)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "For most of human history the door was closed.",
        "Hagar prayed in the wilderness and named the God who saw her. "
        "Abraham stood before the Lord and bargained for Sodom. Moses "
        "spoke with God face to face — but most of Israel was held back "
        "by a thick curtain that no priest dared cross more than once a "
        "year. And then, on a Friday afternoon, that curtain tore from "
        "top to bottom.",
        "This book walks the whole story — from the first cries in Eden "
        "through the patriarchs and the tabernacle, to the cross that "
        "opened the veil, to the prayers of the early church, and into "
        "the life of prayer believers can actually live now.",
        "If you have ever wondered whether God is really listening — or "
        "whether prayer is something more than wishful thinking — this "
        "book invites you to step through the door that Christ has "
        "already opened.",
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
    c.setFillColor(COPPER_DARK)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = COVER_SAFETY + 0.5 * inch
    c.setFillColor(COPPER)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


def draw_front_flap(c):
    """Teaser — draws the reader in. Front (right) flap: shift text LEFT
    (toward spine)."""
    safe_left  = FRONT_FLAP_LEFT + FLAP_SAFETY
    safe_right = FRONT_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (FRONT_FLAP_LEFT + FRONT_FLAP_RIGHT) / 2 - FLAP_VISUAL_SHIFT

    c.setFillColor(CREAM)
    y = DOC_H - 0.95 * inch
    line_height = 11.5

    blocks = [
        ("EBGaramond-Italic", 10,
         "On the night before His own death, the Son of God knelt in a garden and prayed."),
        ("EBGaramond", 9,
         "And in that prayer, every truth this book is trying to "
         "explain came into view: a God who hears, a Son who draws "
         "near, a door that is about to open."),
    ]
    pull = ("EBGaramond-Italic", 11.5,
            "“Let us draw near with a sincere heart in full assurance of faith.”")
    rest = [
        ("EBGaramond", 9,
         "For most of human history that nearness was unimaginable. "
         "The veil stood. Most of Israel never crossed it. And yet "
         "Scripture is full of prayer — Hagar at the well, Abraham "
         "before the Lord, Hannah at Shiloh, David in his songs, "
         "Daniel in his window."),
        ("EBGaramond", 9,
         "How did they pray before the veil was torn? And how do we pray now that it has been?"),
        ("EBGaramond", 9,
         "Twelve chapters across five parts, walking from the first "
         "cries in Eden to the prayers of the early church, with "
         "every claim shown from the text."),
        ("EBGaramond-Italic", 9.5,
         "The door has been open for two thousand years. It was opened at tremendous cost. And far too many of us have been standing just outside it, praying like the veil still stands."),
    ]

    for font, size, text in blocks:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.45

    # Pull quote (copper)
    y -= line_height * 0.2
    c.setFillColor(COPPER)
    c.setFont(pull[0], pull[1])
    lines = wrap_text(c, pull[2], pull[0], pull[1], text_width)
    for line in lines:
        c.drawCentredString(flap_cx, y, line)
        y -= line_height + 1
    c.setFont("EBGaramond", 9)
    c.drawCentredString(flap_cx, y, "— Hebrews 10:22")
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
    """About the Author. Back (left) flap: shift text RIGHT (toward spine)."""
    safe_left  = BACK_FLAP_LEFT + FLAP_SAFETY
    safe_right = BACK_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (BACK_FLAP_LEFT + BACK_FLAP_RIGHT) / 2 + FLAP_VISUAL_SHIFT

    c.setFillColor(COPPER)
    y = DOC_H - 0.95 * inch
    c.setFont("EBGaramond-Italic", 12.5)
    c.drawCentredString(flap_cx, y, "About the Author")
    y -= 10

    c.setStrokeColor(COPPER)
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
         "and Christian living, including From the Beginning, Change the "
         "Mind Change the Man, The Character No One Could Invent, Why "
         "Do You Delay, Bridge Moments, The Last Week of the Lamb, and "
         "Can These Bones Live?"),
        ("EBGaramond", 9.5,
         "He writes with his wife Pam on books for teenagers, including "
         "Your Name Means Everything: A Good Name and Strength and Dignity."),
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
    c.setFillColor(COPPER)
    c.setFont("EBGaramond-Italic", 10.5)
    c.drawCentredString(flap_cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(flap_cx, mark_y - 12, "noblemind.study")


def main():
    print('Generating Lulu LINEN-WRAP DUST JACKET for "A New and Living Way"...')
    print(f'  Document size:  {DOC_W_IN}" x {DOC_H_IN}"')
    print(f'  Spine:          {SPINE_W_IN}"')
    print(f'  Cover panel:    {COVER_W_IN}" x {DOC_H_IN}" each')
    print(f'  Flap:           {FLAP_W_IN}" x {DOC_H_IN}"   Fold: {FOLD_W_IN}"')
    print()
    print('  Panel x-positions (inches):')
    print(f'    back flap   : {BACK_FLAP_LEFT/inch:.3f} .. {BACK_FLAP_RIGHT/inch:.3f}')
    print(f'    back cover  : {BACK_COVER_LEFT/inch:.3f} .. {BACK_COVER_RIGHT/inch:.3f}')
    print(f'    spine       : {SPINE_LEFT/inch:.3f} .. {SPINE_RIGHT/inch:.3f}')
    print(f'    front cover : {FRONT_COVER_LEFT/inch:.3f} .. {FRONT_COVER_RIGHT/inch:.3f}')
    print(f'    front flap  : {FRONT_FLAP_LEFT/inch:.3f} .. {FRONT_FLAP_RIGHT/inch:.3f}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("A New and Living Way — Lulu Hardcover Dust Jacket")

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
