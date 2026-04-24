#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'Why Do You Delay?'.

Lulu specs (5.5x8.5 perfect bound paperback, B&W white paper):
  Trim size: 5.5" x 8.5"
  Spine width: PAGE_COUNT * 0.002252" (B&W white paper).
               Update with Lulu's exact value from their template tool
               before final upload.
  Bleed: 0.125" on all outside edges (not on spine edges)
  Total document width:  0.125 + 5.5 + spine + 5.5 + 0.125
  Total document height: 0.125 + 8.5 + 0.125 = 8.75"
  Safety margin: 0.25" inside trim edges for front cover text
  Safety margin: 0.5"  inside trim edges for back cover text
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_Do_You_Delay_Lulu_Paperback_Cover.pdf"
BG_IMAGE = BOOK_DIR / "why-do-you-delay-cover-image.png"

# Fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Page count & spine width ---
# Update PAGE_COUNT after running generate_lulu_interior.py and use
# Lulu's template tool value for SPINE_W before final upload.
PAGE_COUNT = 84
SPINE_W    = PAGE_COUNT * 0.002252   # Lulu B&W white paper formula

# --- Document dimensions ---
BLEED  = 0.125
TRIM_W = 5.5
TRIM_H = 8.5
DOC_W  = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H  = (BLEED + TRIM_H + BLEED) * inch

# --- Colors sampled from the Rockwell-style river baptism painting ---
DEEP_SHADOW = Color(0.075, 0.086, 0.059)   # #13160F near-black water
DARK_WATER  = Color(0.105, 0.131, 0.105)   # #1B211B shaded water
CANOPY_DARK = Color(0.165, 0.188, 0.110)   # #2A301C deep canopy
CREAM       = Color(0.961, 0.910, 0.804)   # #F5E8CD text cream
GOLD        = Color(0.776, 0.608, 0.337)   # #C69B56 warm gold accent
MUTED_GOLD  = Color(0.616, 0.490, 0.278)   # #9D7D47 subtle gold
SLATE       = Color(0.582, 0.561, 0.494)   # #948F7E muted stone

# --- Layout positions ---
BACK_COVER_LEFT  = 0
BACK_COVER_RIGHT = (BLEED + TRIM_W) * inch

SPINE_LEFT   = BACK_COVER_RIGHT
SPINE_RIGHT  = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT  = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

BACK_TRIM_LEFT   = BLEED * inch
BACK_TRIM_RIGHT  = BACK_COVER_RIGHT
BACK_CENTER_X    = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT  = FRONT_COVER_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X   = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

TRIM_TOP       = DOC_H - BLEED * inch
TRIM_BOTTOM    = BLEED * inch
COVER_CENTER_Y = DOC_H / 2

SAFETY       = 0.5 * inch
FRONT_SAFETY = 0.25 * inch


def check_front_safety(c, text, font_name, font_size, cx):
    w = c.stringWidth(text, font_name, font_size)
    half_w = w / 2
    left_edge = cx - half_w
    right_edge = cx + half_w
    left_margin  = (left_edge - FRONT_TRIM_LEFT) / inch
    right_margin = (FRONT_TRIM_RIGHT - right_edge) / inch
    status = "OK" if min(left_margin, right_margin) >= 0.125 else "WARN"
    print(f'  [{status}] "{text}" ({font_name} {font_size}pt): '
          f'L={left_margin:.3f}" R={right_margin:.3f}"')


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for w in words:
        test = f"{current} {w}".strip() if current else w
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_background(c):
    """Fill the full document with a dark water brown — the back-cover
    and spine base color."""
    c.setFillColor(DEEP_SHADOW)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    cx = FRONT_CENTER_X

    # --- Background image, clipped to front cover area ---
    img = ImageReader(str(BG_IMAGE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

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
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # --- Top darkening wash so title reads ---
    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    top_band_h = 2.2 * inch
    tsteps = 220
    for i in range(tsteps):
        alpha = 0.58 * (1 - i / tsteps) ** 1.4
        c.setFillColor(Color(0.03, 0.05, 0.03, alpha))
        y = DOC_H - (top_band_h * i / tsteps) - 1
        h = top_band_h / tsteps + 1
        c.rect(target_x, y, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title: "Why Do You" (italic) ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 24)
    c.drawCentredString(cx, DOC_H - 1.0 * inch, "Why Do You")
    check_front_safety(c, "Why Do You", "EBGaramond-Italic", 24, cx)

    # --- Title: "Delay?" (bold) ---
    c.setFont("EBGaramond", 46)
    c.drawCentredString(cx, DOC_H - 1.7 * inch, "Delay?")
    check_front_safety(c, "Delay?", "EBGaramond", 46, cx)

    # --- Bottom wash so subtitle + author read ---
    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    bot_band_h = 2.4 * inch
    bsteps = 260
    for i in range(bsteps):
        alpha = 0.62 * (i / bsteps) ** 1.3
        c.setFillColor(Color(0.02, 0.04, 0.03, alpha))
        y = bot_band_h * (1 - i / bsteps)
        h = bot_band_h / bsteps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Subtitle (two italic lines, above author) ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 12.5)
    sub1_y = TRIM_BOTTOM + SAFETY + 0.95 * inch
    sub2_y = sub1_y - 0.26 * inch
    c.drawCentredString(cx, sub1_y, "Baptism, Salvation,")
    c.drawCentredString(cx, sub2_y, "and What the Bible Actually Says")
    check_front_safety(c, "and What the Bible Actually Says",
                       "EBGaramond-Italic", 12.5, cx)

    # --- Decorative rule between subtitle and author ---
    rule_y = TRIM_BOTTOM + SAFETY + 0.45 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    rule_hw = 0.55 * inch
    c.line(cx - rule_hw, rule_y, cx + rule_hw, rule_y)

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 15)
    author_y = TRIM_BOTTOM + SAFETY + 0.1 * inch
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")
    check_front_safety(c, "P A U L   H A I N L I N E", "EBGaramond", 15, cx)


def draw_spine(c):
    # 0.189" is too narrow for legible vertical text per Lulu guidance.
    # We fill with a deeper earth brown so the spine reads as a clean
    # edge between front and back — no typography.
    c.setFillColor(CANOPY_DARK)
    c.rect(SPINE_LEFT, 0, SPINE_W * inch, DOC_H, fill=1, stroke=0)


def draw_back_cover(c):
    blurb_inset = SAFETY + 0.2 * inch
    safe_left = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X

    # --- Opening verse (italic, gold) ---
    y = TRIM_TOP - 0.95 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, y,      "“Now why do you delay? Get up and be")
    y -= 15
    c.drawCentredString(cx, y,      "baptized, and wash away your sins,")
    y -= 15
    c.drawCentredString(cx, y,      "calling on His name.”")
    y -= 16
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y, "— Acts 22:16")
    y -= 12

    # --- Thin rule ---
    y -= 8
    line_hw = 0.55 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 22

    # --- Body blurb ---
    c.setFillColor(CREAM)
    line_height = 13

    body_paragraphs = [
        "Is baptism really necessary?",
        "The question has been asked in churches, Bible studies, and living "
        "room conversations for generations. Every answer turns on what the "
        "Scriptures actually say.",
        "This book opens the New Testament and lets it speak. What the Lord "
        "and His apostles taught. What the early church did on the day of "
        "Pentecost and in every conversion after. The common objections, "
        "answered from the text rather than from tradition.",
        "Thirteen chapters across three parts, ending at the question "
        "Ananias asked Saul of Tarsus two thousand years ago — the "
        "same question that echoes through every page of the New Testament:",
        "“Why do you delay?”",
    ]
    for i, para in enumerate(body_paragraphs):
        lines = wrap_text(c, para, "EBGaramond", 9.5, text_width)
        is_emphasis = (i == 0 or i == len(body_paragraphs) - 1)
        if is_emphasis:
            c.setFont("EBGaramond-Italic", 10)
        else:
            c.setFont("EBGaramond", 9.5)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.35

    # --- Attribution ---
    y -= line_height * 0.2
    c.setFillColor(MUTED_GOLD)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(
        cx, y,
        "Scripture quotations from the New American Standard Bible® (NASB).",
    )

    # --- Imprint (no ISBN) ---
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating Lulu PAPERBACK cover PDF for "Why Do You Delay?"...')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {SPINE_W:.3f}" '
          f'({PAGE_COUNT} pages, Lulu B&W white paper estimate)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')
    print(f'\nFront cover text safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Why Do You Delay? — Lulu Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
