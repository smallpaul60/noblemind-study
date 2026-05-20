#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'The Love God Calls Us To'.

Lulu specs (5.5x8.5 perfect-bound paperback, 224 pages, B&W cream
interior; spine width from Lulu template):
  Trim: 5.5" x 8.5"
  Spine: 0.565"  (Lulu template; 224 × 0.00226 + 0.057 ≈ 0.563", template 0.565)
  Bleed: 0.125" outside edges
  Total document: 11.815" x 8.750"

Source image: washing_feet_cover.png (Christ kneeling, washing the feet
of a disciple). The composed cover_front.jpg has the title typography
baked in — we don't reuse it here. We start fresh on the wraparound
spread, redraw the title at print resolution, and let ReportLab embed
all fonts so Lulu's preflight accepts the cover.
"""

import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401  (registers Standard-14 font aliases)

from PIL import Image
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "The_Love_God_Calls_Us_To_Lulu_Paperback_Cover.pdf"
COVER_SOURCE = BOOK_DIR / "washing_feet_cover.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (from Lulu template) ---
SPINE_W = 0.565
BLEED = 0.125
TRIM_W = 5.5
TRIM_H = 8.5

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch   # 11.815
DOC_H = (BLEED + TRIM_H + BLEED) * inch                       #  8.750

# --- Layout anchors ---
BACK_LEFT = 0
BACK_RIGHT = (BLEED + TRIM_W) * inch
SPINE_LEFT = BACK_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
FRONT_LEFT = SPINE_RIGHT
FRONT_RIGHT = DOC_W
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = BACK_RIGHT
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = FRONT_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

TRIM_TOP = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch

SAFETY = 0.5 * inch
FRONT_SAFETY = 0.25 * inch

# --- Palette (sampled from the footwashing painting) ---
DEEP_BROWN  = Color(0.117, 0.082, 0.055)   # #1E1510 — deep warm wall shadow
CREAM       = Color(0.961, 0.929, 0.890)   # #F5EDE3
CREAM_SOFT  = Color(0.882, 0.823, 0.706)   # #E1D2B4
WARM_GOLD   = Color(0.769, 0.659, 0.392)   # #C4A864 — oil-lamp glow
GOLD_DEEP   = Color(0.620, 0.529, 0.290)   # #9E874A
WARM_RED    = Color(0.769, 0.318, 0.247)   # #C4513F — accent for verse rule
SLATE       = Color(0.604, 0.561, 0.494)   # #9A8F7E


def _load_hires_cover():
    """2x LANCZOS — 1023x1537 → 2046x3074 ≈ 340 PPI at 6"-wide print."""
    src = Image.open(str(COVER_SOURCE)).convert("RGB")
    hires = src.resize((src.width * 2, src.height * 2), Image.LANCZOS)
    buf = BytesIO()
    hires.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return ImageReader(buf)


def check_front_safety(c, text, font_name, font_size, cx):
    w = c.stringWidth(text, font_name, font_size)
    left = (cx - w/2 - FRONT_TRIM_LEFT) / inch
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

    # --- Top darkening band so cream title reads on the warm wall ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    top_h = 2.2 * inch
    steps = 220
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.4
        c.setFillColor(Color(0.04, 0.025, 0.015, alpha))
        y = DOC_H - (i * top_h / steps)
        h = top_h / steps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title: italic "The Love God" + bold "Calls Us To" ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 26)
    c.drawCentredString(cx, DOC_H - 0.70 * inch, "The Love God")
    check_front_safety(c, "The Love God", "EBGaramond-Italic", 26, cx)

    c.setFont("EBGaramond", 44)
    c.drawCentredString(cx, DOC_H - 1.30 * inch, "Calls Us To")
    check_front_safety(c, "Calls Us To", "EBGaramond", 44, cx)

    # --- Subtitle ---
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, DOC_H - 1.75 * inch, "Walking Out 1 Corinthians 13")
    check_front_safety(c, "Walking Out 1 Corinthians 13", "EBGaramond-Italic", 13, cx)

    # --- Bottom darkening band for author + publisher ---
    c.saveState()
    p = c.beginPath(); p.rect(target_x, 0, target_w, DOC_H); p.close()
    c.clipPath(p, stroke=0)
    bot_h = 1.5 * inch
    bsteps = 220
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.04, 0.025, 0.015, alpha))
        y = bot_h * (1 - i / bsteps)
        h = bot_h / bsteps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Author + publisher ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 15)
    author_y = TRIM_BOTTOM + SAFETY + 0.35 * inch
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")
    check_front_safety(c, "P A U L   H A I N L I N E", "EBGaramond", 15, cx)

    c.setFillColor(WARM_GOLD)
    c.setFont("EBGaramond-Italic", 9)
    c.drawCentredString(cx, TRIM_BOTTOM + SAFETY - 0.05 * inch, "NobleMind Press")


def draw_spine(c):
    """0.565\" spine — comfortable for the title and the author."""
    # Spine title: top-anchored, reads top-to-bottom on shelf
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_TOP - 0.6 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 12)
    c.drawString(0, -3.5, "The Love God Calls Us To")
    c.restoreState()

    # Spine author: bottom-anchored, reads top-to-bottom on shelf
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + 1.4 * inch)
    c.rotate(-90)
    c.setFillColor(WARM_GOLD)
    c.setFont("EBGaramond", 10)
    c.drawString(0, -3, "PAUL HAINLINE")
    c.restoreState()


def draw_back_cover(c):
    cx = BACK_CENTER_X
    blurb_inset = SAFETY + 0.2 * inch
    safe_left = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left

    # --- Anchor verse: 1 Corinthians 13:13 ---
    y = TRIM_TOP - 0.95 * inch
    c.setFillColor(WARM_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    verse_lines = [
        "“But now faith, hope, love,",
        "abide these three;",
        "but the greatest of these is love.”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 15
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— 1 Corinthians 13:13")
    y -= 22

    # --- Warm-red rule (echoes the scripture-border accent inside the book) ---
    y -= 4
    c.setStrokeColor(WARM_RED)
    c.setLineWidth(0.7)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "The world has heard this chapter a thousand times at weddings and read it carefully almost nowhere else.",
        "Paul did not write 1 Corinthians 13 as wedding poetry. He wrote it to a fractured first-century church that had collected impressive spiritual gifts and lost the one thing that made the gifts mean anything. Fifteen attributes of love, addressed one chapter at a time, with the Greek named where it helps and the Corinthian failures named where they sharpen what we are now being asked to do.",
        "Written for junior-high and high-school students. Useful for any believer who wants to walk out what this chapter actually demands.",
        "The love described here is the eternal nature of God Himself, and you have been invited to learn what it looks like — and to begin practicing it now.",
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

    # --- Scripture attribution ---
    y -= 5
    c.setFillColor(GOLD_DEEP)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(WARM_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


def main():
    print('Generating Lulu PAPERBACK cover for "The Love God Calls Us To"...')
    print(f'  Trim: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine: {SPINE_W:.3f}"  (224 pp cream, from Lulu template)')
    print(f'  Bleed: {BLEED}" outside edges')
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')
    print('\nFront-cover safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("The Love God Calls Us To — Lulu Paperback Cover")
    draw_background(c)
    draw_back_cover(c)
    draw_front_cover(c)
    draw_spine(c)
    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
