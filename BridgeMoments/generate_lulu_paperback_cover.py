#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'Bridge Moments'.

Lulu specs (5.5x8.5 perfect-bound paperback, 394 pages, B&W cream interior;
template values verified 2026-05-13):
  Trim: 5.5" x 8.5"
  Spine: 0.947"   (Lulu template — formula 394 * 0.0026 = 1.024" overshot
                   by 0.077"; cream rate for this stock is ~0.00240/page)
  Bleed: 0.125" outside edges only (no bleed on spine edges)
  Total document: 12.197" x 8.750"
  Safety: 0.25" inside trim for front; 0.5" for back

Design matches the published reader cover (golden-hour stone footbridge,
warm gold #B8883E accent, cream/warm typography on dark twilight sky).
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
OUTPUT = BOOK_DIR / "BridgeMoments_Lulu_Paperback_Cover.pdf"
COVER_SOURCE = BOOK_DIR / "BridgeMoments-cover-image.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (Lulu template values) ---
SPINE_W = 0.947
BLEED   = 0.125
TRIM_W  = 5.5
TRIM_H  = 8.5

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch  # 12.197"
DOC_H = (BLEED + TRIM_H + BLEED) * inch                       #  8.750"

# --- Layout positions ---
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
COVER_CENTER_Y = DOC_H / 2

SAFETY       = 0.5  * inch
FRONT_SAFETY = 0.25 * inch

# --- Colors sampled from the golden-hour bridge painting ---
DEEP_TWILIGHT = Color(0.090, 0.075, 0.055)   # #17130E near-black amber
WARM_DARK     = Color(0.180, 0.145, 0.100)   # #2E2519
CREAM         = Color(0.961, 0.910, 0.804)   # #F5E8CD
GOLD          = Color(0.722, 0.533, 0.247)   # #B8883E warm gold (book accent)
GOLD_MUTED    = Color(0.580, 0.443, 0.224)   # #94713A
SLATE         = Color(0.620, 0.580, 0.510)   # #9E9482


def _load_hires_cover():
    """Upscale the source PNG 2x with LANCZOS so the front-cover PPI clears
    Lulu's 200 PPI minimum. Source is 1024x1536 (~182 PPI at 5.625"); 2x
    yields 2048x3072 (~364 PPI), comfortably above the floor."""
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
    """Fill entire document with deep twilight amber — back-cover and spine
    base color."""
    c.setFillColor(DEEP_TWILIGHT)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    cx = FRONT_CENTER_X

    # --- Place upscaled image, clipped to front-cover region ---
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

    # --- Title block (cream over the dark sky) ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 30)
    c.drawCentredString(cx, DOC_H - 1.0 * inch, "Bridge Moments")
    check_front_safety(c, "Bridge Moments", "EBGaramond", 30, cx)

    c.setFont("EBGaramond-Italic", 13.5)
    c.drawCentredString(cx, DOC_H - 1.42 * inch, "Making the Most of Every Opportunity")
    check_front_safety(c, "Making the Most of Every Opportunity", "EBGaramond-Italic", 13.5, cx)

    # --- Bottom gradient wash so author / imprint read against the path ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    steps = 240
    band_h = 2.0 * inch
    for i in range(steps):
        alpha = 0.58 * (i / steps) ** 1.4
        c.setFillColor(Color(0.02, 0.015, 0.01, alpha))
        y = band_h * (1 - i / steps)
        h = band_h / steps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Author + imprint ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 15)
    author_y = TRIM_BOTTOM + SAFETY + 0.45 * inch
    c.drawCentredString(cx, author_y, "Paul Hainline")
    check_front_safety(c, "Paul Hainline", "EBGaramond", 15, cx)

    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, TRIM_BOTTOM + SAFETY + 0.05 * inch,
                        "N O B L E M I N D   P R E S S")


def draw_spine(c):
    """0.947" of spine — comfortable for prominent title + author + footer.
    Rotated -90° so text reads top-to-bottom on a shelf (US/UK convention)."""
    spine_safety = 0.5 * inch
    title_text   = "Bridge Moments"
    author_text  = "Paul Hainline"
    foot_text    = "NobleMind Press"

    # Title near top of spine
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_TOP - spine_safety)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 22)
    c.drawString(0, -6, title_text)
    c.restoreState()

    # Author near foot of spine
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + spine_safety + 1.6 * inch)
    c.rotate(-90)
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 12)
    c.drawString(0, -4, author_text)
    c.restoreState()

    # Imprint at very foot
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + spine_safety + 0.4 * inch)
    c.rotate(-90)
    c.setFillColor(SLATE)
    c.setFont("EBGaramond-Italic", 8.5)
    c.drawString(0, -3, foot_text)
    c.restoreState()


def draw_back_cover(c):
    cx = BACK_CENTER_X
    blurb_inset = SAFETY + 0.2 * inch
    safe_left  = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left

    # --- Opening verse (italic, gold) ---
    y = TRIM_TOP - 0.9 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    verse_lines = [
        "“Walk in wisdom toward outsiders,",
        "making the most of the opportunity.",
        "Let your speech always be with grace,",
        "as though seasoned with salt …”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 15
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— Colossians 4:5–6")
    y -= 18

    # --- Gold rule ---
    y -= 8
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body blurb ---
    c.setFillColor(CREAM)
    body = [
        "What if you don’t have to be afraid of the conversation?",
        "The Christians we admire most weren’t the ones who "
        "memorized arguments. They were the ones who knew how to "
        "listen — to a person across a table, a coworker pulled "
        "aside in the break room, a stranger on a long flight — "
        "and to recognize the moment when the conversation was "
        "ready to turn toward something more.",
        "Jesus called those moments by no name. He just walked into "
        "them. The woman at the well. Nicodemus at night. Zacchaeus "
        "in the tree. The rich young ruler stopping Him on the road. "
        "In every one, He listened first, met the person where they "
        "actually were, and let truth do its own work.",
        "Twenty chapters across four parts — twelve case studies from "
        "the Gospels, three from Acts, and five chapters on practice. "
        "Every claim from Scripture. Three appendices included for "
        "small-group use.",
    ]
    body_font, body_size, lh = "EBGaramond", 9.5, 13
    emphasis_font = "EBGaramond-Italic"
    for i, para in enumerate(body):
        is_hook = (i == 0)
        font = emphasis_font if is_hook else body_font
        size = 10.5 if is_hook else body_size
        lines = wrap_text(c, para, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= lh + (1 if is_hook else 0)
        y -= lh * 0.4

    # --- Attribution ---
    y -= lh * 0.2
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch
    print('Generating Lulu PAPERBACK cover PDF for "Bridge Moments"...')
    print(f'  Trim: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine: {SPINE_W:.3f}"  (394 pp, from Lulu template)')
    print(f'  Bleed: {BLEED}" outside edges')
    print(f'  Document: {doc_w_in:.3f}" x {doc_h_in:.3f}"')
    print('\nFront-cover safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Bridge Moments — Lulu Paperback Cover")
    draw_background(c)
    draw_back_cover(c)
    draw_front_cover(c)
    draw_spine(c)
    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
