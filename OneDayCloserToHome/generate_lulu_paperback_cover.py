#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'One Day Closer to Home'.

Lulu specs (5.5x8.5 perfect-bound paperback, 142 pages, B&W cream interior;
template values verified 2026-05-14):
  Trim: 5.5" x 8.5"
  Spine: 0.378"  (from Lulu template; matches cream formula:
                   141 × 0.00226 + 0.057 ≈ 0.376", template 0.378)
  Bleed: 0.125" outside edges
  Total document: 11.628" x 8.750"

Source image is the raw "One Day Closer to Home.png" — cover_front.jpg
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
OUTPUT = BOOK_DIR / "One_Day_Closer_to_Home_Lulu_Paperback_Cover.pdf"
COVER_SOURCE = BOOK_DIR / "One Day Closer to Home.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (from Lulu template) ---
SPINE_W = 0.378
BLEED   = 0.125
TRIM_W  = 5.5
TRIM_H  = 8.5

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch   # 11.628
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

# --- Colors sampled from the sunset porch painting ---
DEEP_BROWN   = Color(0.137, 0.090, 0.063)   # #231710 — warm dark wood
CREAM        = Color(0.953, 0.910, 0.792)   # #F3E8CA
SUNRISE_GOLD = Color(0.886, 0.624, 0.275)   # #E29F46 — sunset amber accent
GOLD_DEEP    = Color(0.706, 0.467, 0.180)   # #B4772E
WHEAT        = Color(0.804, 0.690, 0.490)   # #CDB07D
SLATE        = Color(0.604, 0.561, 0.494)   # #9A8F7E


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
    c.setFillColor(DEEP_BROWN)
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

    # --- Top wash so title reads against the porch ceiling + sunset ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    steps = 220
    top_h = 2.4 * inch
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.4
        c.setFillColor(Color(0.08, 0.05, 0.03, alpha))
        y = DOC_H - (i * top_h / steps)
        h = top_h / steps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title: italic "One Day Closer" + bold "to Home" ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 24)
    c.drawCentredString(cx, DOC_H - 0.85 * inch, "One Day Closer")
    check_front_safety(c, "One Day Closer", "EBGaramond-Italic", 24, cx)

    c.setFont("EBGaramond", 36)
    c.drawCentredString(cx, DOC_H - 1.4 * inch, "to Home")
    check_front_safety(c, "to Home", "EBGaramond", 36, cx)

    # --- Subtitle ---
    c.setFont("EBGaramond-Italic", 12.5)
    c.drawCentredString(cx, DOC_H - 1.82 * inch, "A Book of Hope for Those")
    c.drawCentredString(cx, DOC_H - 2.06 * inch, "in the Final Chapters")
    check_front_safety(c, "A Book of Hope for Those", "EBGaramond-Italic", 12.5, cx)

    # --- Bottom gradient for author ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    bot_h = 1.5 * inch
    bsteps = 220
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.08, 0.05, 0.03, alpha))
        y = bot_h * (1 - i / bsteps)
        h = bot_h / bsteps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 14)
    author_y = TRIM_BOTTOM + SAFETY + 0.15 * inch
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")
    check_front_safety(c, "P A U L   H A I N L I N E", "EBGaramond", 14, cx)


def draw_spine(c):
    """0.378\" spine — narrow but workable for small title + author."""
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_TOP - 0.4 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 9)
    c.drawString(0, -2.5, "One Day Closer to Home")
    c.restoreState()

    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + 0.4 * inch + 1.2 * inch)
    c.rotate(-90)
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond", 7.5)
    c.drawString(0, -2, "Paul Hainline")
    c.restoreState()


def draw_back_cover(c):
    cx = BACK_CENTER_X
    blurb_inset = SAFETY + 0.2 * inch
    safe_left  = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left

    # --- Anchor verse: 2 Corinthians 4:16-17 ---
    y = TRIM_TOP - 0.95 * inch
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    verse_lines = [
        "“Therefore we do not lose heart, but",
        "though our outer man is decaying,",
        "yet our inner man is being renewed",
        "day by day.”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 15
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— 2 Corinthians 4:16")
    y -= 22

    # --- Gold rule ---
    y -= 6
    c.setStrokeColor(SUNRISE_GOLD)
    c.setLineWidth(0.5)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "Aging is not the long ending of a good story. It is the long approach to a better one.",
        "Scripture does not flinch from the body that is breaking down — but it never lets that "
        "be the whole picture. Simeon held the Christ child and was ready to depart in peace. "
        "Anna never left the temple. Caleb at eighty-five asked God for one more mountain. Paul, "
        "in prison and old, called his suffering a momentary light affliction next to what was "
        "coming.",
        "Thirteen chapters across three parts walk through the examples, the theology, and the "
        "crescendo of biblical hope for those nearing the end. Every claim is shown from the "
        "text — not as platitude, but as the actual answer Scripture gives.",
        "If you are walking the final mile, or walking it with someone you love, this book is for you.",
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
    c.setFillColor(GOLD_DEEP)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


def main():
    print('Generating Lulu PAPERBACK cover for "One Day Closer to Home"...')
    print(f'  Trim: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine: {SPINE_W:.3f}"  (142 pp cream, from Lulu template)')
    print(f'  Bleed: {BLEED}" outside edges')
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')
    print('\nFront-cover safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("One Day Closer to Home — Lulu Paperback Cover")
    draw_background(c)
    draw_back_cover(c)
    draw_front_cover(c)
    draw_spine(c)
    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
