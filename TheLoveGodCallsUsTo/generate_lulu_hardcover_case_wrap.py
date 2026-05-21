#!/usr/bin/env python3
"""Generate Lulu CASE-WRAP hardcover cover for 'The Love God Calls Us To'.

Design mirrors the published paperback (footwashing painting + cream
typography + warm gold). No darkening bands — the cream type carries
against the painting's warm wall and the deep floor.

Lulu specs (5.5x8.5 hardcover case-wrap, 224 pp cream interior;
spine width from Lulu's downloaded template):
  Total document:  13.563" x 10.250"
  Panel face:      5.75"   x 9.000"    (board extends 0.125" past trim
                                        on top, bottom, and outside)
  Spine width:     0.813"  (paperback 0.565" + ~0.248" board overhead)
  Wrap area:       0.625"  past board edge, all four sides
  Safety margin:   0.625"  inside board edge
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
OUTPUT = BOOK_DIR / "The_Love_God_Calls_Us_To_Lulu_Hardcover_CaseWrap.pdf"
COVER_SOURCE = BOOK_DIR / "washing_feet_cover.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# ============================================================================
# DOCUMENT DIMENSIONS
# ============================================================================
PAGE_COUNT  = 224
SPINE_W_IN  = 0.813   # Lulu template (paperback 0.565 + 0.248 board overhead)

PANEL_W_IN  = 5.75
PANEL_H_IN  = 9.00
WRAP_IN     = 0.625
SAFETY_IN   = 0.625

DOC_W_IN    = PANEL_W_IN * 2 + SPINE_W_IN + WRAP_IN * 2   # 13.563
DOC_H_IN    = PANEL_H_IN + WRAP_IN * 2                    # 10.250
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

# Safety-inset bounds
FRONT_SAFE_LEFT   = FRONT_FACE_LEFT + SAFETY_IN * inch
FRONT_SAFE_RIGHT  = FRONT_FACE_RIGHT - SAFETY_IN * inch
FRONT_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
FRONT_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch

BACK_SAFE_LEFT   = BACK_FACE_LEFT + SAFETY_IN * inch
BACK_SAFE_RIGHT  = BACK_FACE_RIGHT - SAFETY_IN * inch
BACK_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
BACK_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch
BACK_TEXT_WIDTH  = BACK_SAFE_RIGHT - BACK_SAFE_LEFT

# --- Palette (matches the paperback) ---
DEEP_BROWN  = Color(0.117, 0.082, 0.055)   # #1E1510 — back panel + spine
CREAM       = Color(0.961, 0.910, 0.804)   # #F5E8CD
CREAM_SOFT  = Color(0.882, 0.824, 0.706)   # #E1D2B4
ACCENT_GOLD = Color(0.831, 0.706, 0.431)   # #D4B46E
WARM_GOLD   = ACCENT_GOLD
GOLD_DEEP   = Color(0.620, 0.529, 0.290)   # #9E874A
WARM_RED    = Color(0.769, 0.318, 0.247)   # #C4513F — verse rule
SLATE       = Color(0.604, 0.561, 0.494)   # #9A8F7E


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _load_hires_cover():
    """2x LANCZOS upscale → ~340 PPI across the 5.75\" face."""
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


def check_front_safety(c, text, font_name, font_size, cx):
    w = c.stringWidth(text, font_name, font_size)
    left  = (cx - w/2 - FRONT_FACE_LEFT) / inch
    right = (FRONT_FACE_RIGHT - cx - w/2) / inch
    status = "OK" if min(left, right) >= 0.25 else "WARN"
    print(f'  [{status}] "{text}" {font_name} {font_size:.2f}pt: '
          f'L={left:.3f}" R={right:.3f}"')


def _draw_centered_spaced(c, text, font_name, font_size, cx, baseline_y,
                          char_spacing_pt):
    """Centered drawString with extra spacing between every character."""
    c.setFont(font_name, font_size)
    widths = [c.stringWidth(ch, font_name, font_size) for ch in text]
    total = sum(widths) + char_spacing_pt * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        c.drawString(x, baseline_y, ch)
        x += wch + char_spacing_pt


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    """Deep brown across the whole document — covers the back panel,
    the spine, and the wrap areas that fold to the inside of the boards."""
    c.setFillColor(DEEP_BROWN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_face_image(c):
    """Place the footwashing painting, filling the full 5.75 x 9.00 face."""
    img = _load_hires_cover()
    iw, ih = img.getSize()
    img_aspect = iw / ih
    target_w = PANEL_W_IN * inch
    target_h = PANEL_H_IN * inch
    target_aspect = target_w / target_h

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


def draw_front_face_text(c):
    """Title / subtitle / author — same proportional layout as the
    paperback front, scaled to the 9.0\" face height. No darkening bands;
    cream reads against the warm wall and the dark floor."""
    cx = FRONT_CENTER_X

    # Paperback typography was tuned at trim_h=8.5"; scale up to 9.0".
    SCALE = PANEL_H_IN / 8.5         # 1.0588
    PX_TO_PT = 72.0 / 200.0
    BASELINE_FACTOR = 0.80

    # Source positions in Pillow pixels (1700 = 8.5")
    small_top_px = int(1700 * 0.050)                # 85
    big_top_px   = small_top_px + int(64 * 1.15)    # 158
    sub_top_px   = big_top_px   + int(108 * 1.35)   # 304

    def baseline_from_top_px(top_px, size_px):
        # convert "top px of EM box" → baseline_y in PDF coords (from FACE_TOP)
        top_in   = (top_px / 200.0) * SCALE          # inches from face top
        baseline = FACE_TOP - top_in * inch - BASELINE_FACTOR * size_px * PX_TO_PT * SCALE
        return baseline

    def baseline_from_bottom_px(top_px_from_top, size_px):
        bot_in   = ((1700 - top_px_from_top) / 200.0) * SCALE
        baseline = FACE_BOTTOM + bot_in * inch - BASELINE_FACTOR * size_px * PX_TO_PT * SCALE
        return baseline

    small_size  = 64  * PX_TO_PT * SCALE   # ~24 pt italic
    big_size    = 108 * PX_TO_PT * SCALE   # ~41 pt bold
    sub_size    = 34  * PX_TO_PT * SCALE   # ~13 pt italic
    author_size = 42  * PX_TO_PT * SCALE   # ~16 pt bold
    pub_size    = 20  * PX_TO_PT * SCALE   # ~7.6 pt italic

    # Title block
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", small_size)
    c.drawCentredString(cx, baseline_from_top_px(small_top_px, 64), "The Love God")
    check_front_safety(c, "The Love God", "EBGaramond-Italic", small_size, cx)

    c.setFont("EBGaramond", big_size)
    c.drawCentredString(cx, baseline_from_top_px(big_top_px, 108), "Calls Us To")
    check_front_safety(c, "Calls Us To", "EBGaramond", big_size, cx)

    # Subtitle
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond-Italic", sub_size)
    c.drawCentredString(cx, baseline_from_top_px(sub_top_px, 34),
                        "Walking Out 1 Corinthians 13")
    check_front_safety(c, "Walking Out 1 Corinthians 13",
                       "EBGaramond-Italic", sub_size, cx)

    # Author (8px letter-spacing from the paperback) + publisher
    c.setFillColor(CREAM)
    author_baseline = baseline_from_bottom_px(1560, 42)   # 140 px above bottom
    _draw_centered_spaced(c, "PAUL HAINLINE", "EBGaramond", author_size, cx,
                          author_baseline, 8 * PX_TO_PT * SCALE)

    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond-Italic", pub_size)
    c.drawCentredString(cx, baseline_from_bottom_px(1625, 20), "NobleMind Press")


def draw_spine(c):
    """0.813\" spine — comfortable for a 14pt title + 10pt author block."""
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_CY)
    c.rotate(270)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 14)
    c.drawCentredString(0, 4, "The Love God Calls Us To")
    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond", 11)
    c.drawCentredString(0, -14, "PAUL HAINLINE")
    c.restoreState()


def draw_back_face(c):
    """Back face — 1 Cor 13:13 anchor verse + body blurb + Scripture
    attribution + NobleMind Press imprint. Mirrors the paperback back."""
    cx = BACK_CENTER_X

    # --- Anchor verse ---
    y = FACE_TOP - 1.05 * inch
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

    # --- Warm-red rule ---
    y -= 4
    c.setStrokeColor(WARM_RED)
    c.setLineWidth(0.7)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "The world has heard this chapter a thousand times at weddings and read it carefully almost nowhere else.",
        "Paul did not write 1 Corinthians 13 as wedding poetry. He wrote it to a fractured first-century church that had collected impressive spiritual gifts and lost the one thing that made the gifts mean anything. Fifteen attributes of love, addressed across fourteen chapters, with the Greek named where it helps and the Corinthian failures named where they sharpen what we are now being asked to do.",
        "Written for junior-high and high-school students. Useful for any believer who wants to walk out what this chapter actually demands.",
        "The love described here is the eternal nature of God Himself, and you have been invited to learn what it looks like — and to begin practicing it now.",
    ]
    for i, para in enumerate(body):
        is_hook = (i == 0)
        font = "EBGaramond-Italic" if is_hook else "EBGaramond"
        size = 10.5 if is_hook else 9.5
        lh = 13.5 if is_hook else 13
        lines = wrap_text(c, para, font, size, BACK_TEXT_WIDTH)
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
    mark_y = BACK_SAFE_BOTTOM + 0.25 * inch
    c.setFillColor(WARM_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print('Generating Lulu HARDCOVER case-wrap for "The Love God Calls Us To"...')
    print(f'  Page count:     {PAGE_COUNT}')
    print(f'  Document size:  {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}"')
    print(f'  Panel face:     {PANEL_W_IN}" x {PANEL_H_IN}"')
    print(f'  Spine width:    {SPINE_W_IN:.3f}"  (Lulu template)')
    print(f'  Wrap:           {WRAP_IN}" past board edge')
    print(f'  Safety:         {SAFETY_IN}" inside board edge')
    print('\nFront-face safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("The Love God Calls Us To — Lulu Hardcover Case-Wrap")

    draw_background(c)
    draw_front_face_image(c)
    draw_front_face_text(c)
    draw_back_face(c)
    draw_spine(c)

    c.save()
    print(f"\nCase-wrap saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
