#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'A New and Living Way'.

Lulu specs (5.5x8.5 perfect-bound paperback, 202 pages, B&W cream interior;
template values verified 2026-05-14):
  Trim: 5.5" x 8.5"
  Spine: 0.513"  (from Lulu template — 202pp cream stock)
  Bleed: 0.125" outside edges
  Total document: 11.763" x 8.750"

Design uses the Gethsemane painting (in_the_garden.png) as the source;
the published cover_front.jpg already has baked-in title text, so we
work from the raw image and draw fresh typography on top.
"""

import sys
from io import BytesIO
from pathlib import Path

# Register Standard-14 font overrides BEFORE constructing Canvas so any
# default Helvetica reference resolves to embedded Liberation Sans.
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
OUTPUT = BOOK_DIR / "A_New_and_Living_Way_Lulu_Paperback_Cover.pdf"
COVER_SOURCE = BOOK_DIR / "in_the_garden.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (from Lulu template) ---
SPINE_W = 0.513
BLEED   = 0.125
TRIM_W  = 5.5
TRIM_H  = 8.5

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch   # 11.763"
DOC_H = (BLEED + TRIM_H + BLEED) * inch                       #  8.750"

# --- Layout ---
BACK_LEFT  = 0
BACK_RIGHT = (BLEED + TRIM_W) * inch
SPINE_LEFT   = BACK_RIGHT
SPINE_RIGHT  = SPINE_LEFT + SPINE_W * inch
FRONT_LEFT   = SPINE_RIGHT
FRONT_RIGHT  = DOC_W
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

BACK_TRIM_LEFT  = BLEED * inch
BACK_TRIM_RIGHT = BACK_RIGHT
BACK_CENTER_X   = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT  = FRONT_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X   = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

TRIM_TOP    = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch

SAFETY       = 0.5  * inch
FRONT_SAFETY = 0.25 * inch

# --- Colors (sampled from the Gethsemane painting) ---
DEEP_NIGHT  = Color(0.055, 0.075, 0.094)   # #0E1318
CREAM       = Color(0.941, 0.902, 0.800)   # #F0E6CC
COPPER      = Color(0.706, 0.314, 0.165)   # #B4502A — the cloak accent
COPPER_DARK = Color(0.545, 0.259, 0.149)   # #8B4226
SLATE       = Color(0.545, 0.529, 0.475)   # #8B8779


def _load_hires_cover():
    """2x LANCZOS upscale — 1024x1536 → 2048x3072 ≈ 364 PPI @5.625"."""
    src = Image.open(str(COVER_SOURCE)).convert("RGB")
    hires = src.resize((src.width * 2, src.height * 2), Image.LANCZOS)
    buf = BytesIO()
    hires.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return ImageReader(buf)


def check_front_safety(c, text, font_name, font_size, cx):
    w = c.stringWidth(text, font_name, font_size)
    left  = (cx - w/2 - FRONT_TRIM_LEFT) / inch
    right = (FRONT_TRIM_RIGHT - cx - w/2) / inch
    status = "OK" if min(left, right) >= 0.125 else "WARN"
    print(f'  [{status}] "{text}" {font_name} {font_size}pt: L={left:.3f}" R={right:.3f}"')


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
    target_x = FRONT_LEFT
    target_w = FRONT_RIGHT - FRONT_LEFT
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

    # --- Top dark wash so title reads cleanly against the moonlit sky ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    steps = 220
    top_band_h = 2.6 * inch
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.4
        c.setFillColor(Color(0.02, 0.025, 0.035, alpha))
        y = DOC_H - (i * top_band_h / steps)
        h = top_band_h / steps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title: italic "A New and" + bold "Living Way" ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 26)
    c.drawCentredString(cx, DOC_H - 1.0 * inch, "A New and")
    check_front_safety(c, "A New and", "EBGaramond-Italic", 26, cx)

    c.setFont("EBGaramond", 36)
    c.drawCentredString(cx, DOC_H - 1.55 * inch, "Living Way")
    check_front_safety(c, "Living Way", "EBGaramond", 36, cx)

    # --- Subtitle ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 12.5)
    c.drawCentredString(cx, DOC_H - 1.95 * inch, "What the Bible Teaches About Prayer")
    check_front_safety(c, "What the Bible Teaches About Prayer",
                       "EBGaramond-Italic", 12.5, cx)

    # --- Bottom gradient so author reads against the figure's white robe ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    bot_band_h = 1.6 * inch
    bsteps = 220
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.02, 0.025, 0.035, alpha))
        y = bot_band_h * (1 - i / bsteps)
        h = bot_band_h / bsteps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 14)
    author_y = TRIM_BOTTOM + SAFETY + 0.15 * inch
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")
    check_front_safety(c, "P A U L   H A I N L I N E", "EBGaramond", 14, cx)


def draw_spine(c):
    """0.513\" spine — comfortable for small spine text (rotated -90°,
    reads top-to-bottom when book is shelved spine-out)."""
    title_text  = "A New and Living Way"
    author_text = "Paul Hainline"

    # Title
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_TOP - 0.5 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 11)
    c.drawString(0, -3, title_text)
    c.restoreState()

    # Author near foot
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + 0.5 * inch + 1.4 * inch)
    c.rotate(-90)
    c.setFillColor(COPPER)
    c.setFont("EBGaramond", 8)
    c.drawString(0, -2.5, author_text)
    c.restoreState()


def draw_back_cover(c):
    cx = BACK_CENTER_X
    blurb_inset = SAFETY + 0.2 * inch
    safe_left  = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left

    # --- Anchor verse (italic copper) ---
    y = TRIM_TOP - 0.85 * inch
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
    y -= 18

    # --- Copper rule ---
    y -= 8
    c.setStrokeColor(COPPER)
    c.setLineWidth(0.5)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 20

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "For most of human history the door was closed.",
        "Hagar prayed in the wilderness and named the God who saw her. "
        "Abraham stood before the Lord and bargained for Sodom. Moses "
        "spoke with God face to face — but most of Israel was held back "
        "by a thick curtain that no priest dared cross more than once "
        "a year. And then, on a Friday afternoon, that curtain tore from "
        "top to bottom.",
        "This book walks the whole story — from the first cries in Eden, "
        "through the patriarchs and the tabernacle, to the cross that "
        "opened the veil, to the prayers of the early church, and into "
        "the life of prayer believers can actually live now. Twelve "
        "chapters across five parts, with every claim shown from the "
        "text.",
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
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(COPPER)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print('Generating Lulu PAPERBACK cover for "A New and Living Way"...')
    print(f'  Trim: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine: {SPINE_W:.3f}"  (202 pp cream, from Lulu template)')
    print(f'  Bleed: {BLEED}" outside edges')
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')
    print('\nFront-cover safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("A New and Living Way — Lulu Paperback Cover")
    draw_background(c)
    draw_back_cover(c)
    draw_front_cover(c)
    draw_spine(c)
    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
