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

# --- Palette (matches generate_cover.py exactly) ---
DEEP_BROWN  = Color(0.117, 0.082, 0.055)   # #1E1510 — back-cover background
CREAM       = Color(0.961, 0.910, 0.804)   # #F5E8CD  (245,232,205)
CREAM_SOFT  = Color(0.882, 0.824, 0.706)   # #E1D2B4  (225,210,180)
ACCENT_GOLD = Color(0.831, 0.706, 0.431)   # #D4B46E  (212,180,110)
WARM_GOLD   = ACCENT_GOLD
GOLD_DEEP   = Color(0.620, 0.529, 0.290)   # #9E874A
WARM_RED    = Color(0.769, 0.318, 0.247)   # #C4513F — back-cover verse rule
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


def _draw_centered_spaced(c, text, font_name, font_size, cx, baseline_y, char_spacing_pt):
    """Centered drawString with extra spacing between every character (no kerning)."""
    c.setFont(font_name, font_size)
    widths = [c.stringWidth(ch, font_name, font_size) for ch in text]
    total = sum(widths) + char_spacing_pt * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        c.drawString(x, baseline_y, ch)
        x += wch + char_spacing_pt


def draw_front_cover(c):
    """Front cover — typography matches generate_cover.py exactly.

    Pixel-to-point conversion: source image is 1700px tall = 8.5" trim
    (200 px/inch), so 1 Pillow_px = 0.36 pt. Pillow's draw.text anchors
    at the top of the EM box; ReportLab's drawString anchors at the
    baseline. We convert top-of-EM positions to baseline positions by
    subtracting ~0.80*font_size, which lines the visible glyphs up to
    the same place the original cover_front.jpg shows.
    """
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

    # No darkening bands — cream + the painting's wall tones carry the contrast.

    PX_TO_PT = 72.0 / 200.0
    BASELINE_FACTOR = 0.80

    def baseline_from_top_px(top_px, size_px):
        top_in = top_px / 200.0
        return TRIM_TOP - (top_in * inch) - BASELINE_FACTOR * size_px * PX_TO_PT

    def baseline_from_bottom_px(top_px_from_top, size_px):
        bot_in = (1700 - top_px_from_top) / 200.0
        return TRIM_BOTTOM + (bot_in * inch) - BASELINE_FACTOR * size_px * PX_TO_PT

    small_size  = 64 * PX_TO_PT   # ~23 pt  italic
    big_size    = 108 * PX_TO_PT  # ~39 pt  bold
    sub_size    = 34 * PX_TO_PT   # ~12 pt  italic
    author_size = 42 * PX_TO_PT   # ~15 pt  bold
    pub_size    = 20 * PX_TO_PT   # ~7  pt  italic

    # Original Pillow top-edge positions (from cover_front.jpg layout)
    small_top_px = int(1700 * 0.050)                # 85
    big_top_px   = small_top_px + int(64 * 1.15)    # 158
    sub_top_px   = big_top_px   + int(108 * 1.35)   # 304

    # --- Title block: italic "The Love God" + bold "Calls Us To" ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", small_size)
    c.drawCentredString(cx, baseline_from_top_px(small_top_px, 64), "The Love God")
    check_front_safety(c, "The Love God", "EBGaramond-Italic", small_size, cx)

    c.setFont("EBGaramond", big_size)
    c.drawCentredString(cx, baseline_from_top_px(big_top_px, 108), "Calls Us To")
    check_front_safety(c, "Calls Us To", "EBGaramond", big_size, cx)

    # --- Subtitle ---
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond-Italic", sub_size)
    c.drawCentredString(cx, baseline_from_top_px(sub_top_px, 34),
                        "Walking Out 1 Corinthians 13")
    check_front_safety(c, "Walking Out 1 Corinthians 13",
                       "EBGaramond-Italic", sub_size, cx)

    # --- Author (with original 8px letter spacing) + publisher ---
    c.setFillColor(CREAM)
    author_baseline = baseline_from_bottom_px(1560, 42)   # 140 px above bottom
    _draw_centered_spaced(c, "PAUL HAINLINE", "EBGaramond", author_size, cx,
                          author_baseline, 8 * PX_TO_PT)

    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond-Italic", pub_size)
    c.drawCentredString(cx, baseline_from_bottom_px(1625, 20), "NobleMind Press")


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
