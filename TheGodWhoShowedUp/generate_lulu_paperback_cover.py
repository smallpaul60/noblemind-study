#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'The God Who Showed Up'.

Lulu specs (5.5x8.5 perfect-bound paperback, 224 pages, B&W cream interior;
template values verified 2026-05-14):
  Trim: 5.5" x 8.5"
  Spine: 0.565"  (from Lulu template — matches the cream formula:
                   224 × 0.00226 + 0.057 ≈ 0.563", template = 0.565)
  Bleed: 0.125" outside edges
  Total document: 11.815" x 8.750"

Subtitle is "What His Names Reveal About Who He Is" (PLURAL — the book
covers 12 distinct names of God).

Design uses TheBurningBush.png as the raw source — cover_front.jpg
already has baked-in title text and shouldn't be reused.
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
OUTPUT = BOOK_DIR / "The_God_Who_Showed_Up_Lulu_Paperback_Cover.pdf"
COVER_SOURCE = BOOK_DIR / "TheBurningBush.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (from Lulu template) ---
SPINE_W = 0.565
BLEED   = 0.125
TRIM_W  = 5.5
TRIM_H  = 8.5

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch   # 11.815
DOC_H = (BLEED + TRIM_H + BLEED) * inch                       #  8.750

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

# --- Colors sampled from the burning-bush painting ---
DEEP_NIGHT  = Color(0.071, 0.067, 0.090)   # #121117 — night sky
CREAM       = Color(0.949, 0.910, 0.804)   # #F2E8CD
EMBER       = Color(0.890, 0.557, 0.224)   # #E38E39 — flame gold
EMBER_DEEP  = Color(0.706, 0.380, 0.122)   # #B46120 — deeper flame
EARTH       = Color(0.471, 0.341, 0.227)   # #78573A
SLATE       = Color(0.580, 0.555, 0.490)   # #948D7D


def _load_hires_cover():
    """2x LANCZOS — 1024x1536 → 2048x3072 ≈ 364 PPI @5.625"."""
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

    # --- Top wash so title reads against the upper bush flames + sky ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    steps = 220
    top_h = 2.6 * inch
    for i in range(steps):
        alpha = 0.50 * (1 - i / steps) ** 1.4
        c.setFillColor(Color(0.02, 0.02, 0.03, alpha))
        y = DOC_H - (i * top_h / steps)
        h = top_h / steps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title: italic "The God Who" + bold "Showed Up" ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 26)
    c.drawCentredString(cx, DOC_H - 0.95 * inch, "The God Who")
    check_front_safety(c, "The God Who", "EBGaramond-Italic", 26, cx)

    c.setFont("EBGaramond", 36)
    c.drawCentredString(cx, DOC_H - 1.5 * inch, "Showed Up")
    check_front_safety(c, "Showed Up", "EBGaramond", 36, cx)

    # --- Subtitle ---
    c.setFont("EBGaramond-Italic", 12.5)
    c.drawCentredString(cx, DOC_H - 1.92 * inch, "What His Names Reveal About Who He Is")
    check_front_safety(c, "What His Names Reveal About Who He Is",
                       "EBGaramond-Italic", 12.5, cx)

    # --- Bottom gradient for author ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    bot_h = 1.6 * inch
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
    c.setFont("EBGaramond", 14)
    author_y = TRIM_BOTTOM + SAFETY + 0.15 * inch
    c.drawCentredString(cx, author_y, "P A U L   &   P A M   H A I N L I N E")
    check_front_safety(c, "P A U L   &   P A M   H A I N L I N E", "EBGaramond", 14, cx)


def draw_spine(c):
    """0.565\" spine — small rotated cream title + ember author."""
    title_text  = "The God Who Showed Up"
    author_text = "Paul & Pam Hainline"

    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_TOP - 0.5 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 11)
    c.drawString(0, -3, title_text)
    c.restoreState()

    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + 0.5 * inch + 1.5 * inch)
    c.rotate(-90)
    c.setFillColor(EMBER)
    c.setFont("EBGaramond", 8.5)
    c.drawString(0, -2.5, author_text)
    c.restoreState()


def draw_back_cover(c):
    cx = BACK_CENTER_X
    blurb_inset = SAFETY + 0.2 * inch
    safe_left  = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left

    # --- Anchor verse: Exodus 3:14 (THE name God gave Himself) ---
    y = TRIM_TOP - 0.95 * inch
    c.setFillColor(EMBER)
    c.setFont("EBGaramond-Italic", 11)
    verse_lines = [
        "“God said to Moses, ‘I AM WHO I AM’;",
        "and He said, ‘Thus you shall say to the",
        "sons of Israel, I AM has sent me to you.’”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 14
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— Exodus 3:14")
    y -= 20

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
        "exactly who He is. Together, they are a portrait — not of "
        "an idea, but of the living God who keeps showing up.",
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
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(EMBER)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print('Generating Lulu PAPERBACK cover for "The God Who Showed Up"...')
    print(f'  Trim: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine: {SPINE_W:.3f}"  (224 pp cream, from Lulu template)')
    print(f'  Bleed: {BLEED}" outside edges')
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')
    print('\nFront-cover safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("The God Who Showed Up — Lulu Paperback Cover")
    draw_background(c)
    draw_back_cover(c)
    draw_front_cover(c)
    draw_spine(c)
    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
