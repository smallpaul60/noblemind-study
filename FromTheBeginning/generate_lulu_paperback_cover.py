#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for From the Beginning.

Lulu specs (from the cover template — 5.5x8.5 perfect bound paperback,
B&W white paper, 154 pages):
  Trim size: 5.5" x 8.5"
  Spine width: 0.407" (Lulu calculates at ~0.00264"/page, wider than
               IngramSpark's 0.00225"/page)
  Bleed: 0.125" on all outside edges (not on spine edges)
  Total document width:  0.125 + 5.5 + 0.407 + 5.5 + 0.125 = 11.657"
  Total document height: 0.125 + 8.5 + 0.125 = 8.75"
  Safety margin: 0.25" inside trim edges for front cover text
  Safety margin: 0.5"  inside trim edges for back cover text

Design is identical to the IngramSpark paperback cover; only the spine
width and the resulting document width differ.
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "FromTheBeginning_Lulu_Paperback_Cover.pdf"
# 2x LANCZOS upscale of the original Portrait — needed to clear Lulu's
# 200 DPI minimum. Effective ~350 DPI when drawn on the front cover.
BG_IMAGE = BOOK_DIR / "FromTheBeginning_Portrait_Hires.png"

# Register fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Spine (from Lulu template, NOT computed from page count) ---
PAGE_COUNT = 154
SPINE_W = 0.407   # inches — as given by Lulu for 154 pages on B&W white paper

# --- Document dimensions ---
BLEED = 0.125   # inches
TRIM_W = 5.5    # inches
TRIM_H = 8.5    # inches

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch  # 11.657"
DOC_H = (BLEED + TRIM_H + BLEED) * inch                      #  8.75"

# --- Colors ---
DEEP_BLUE = Color(0.067, 0.118, 0.216)     # #112138 deep midnight blue
CREAM = Color(0.961, 0.902, 0.784)         # #F5E6C8 warm cream
GOLD_LIGHT = Color(0.831, 0.659, 0.282)    # #D4A848 warm gold
GOLD_MUTED = Color(0.631, 0.529, 0.322)    # #A18752 muted gold
SLATE = Color(0.580, 0.631, 0.706)         # #94A1B4 light slate

# --- Layout positions (from left edge of document) ---
BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = (BLEED + TRIM_W) * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

# Trim edges (what the reader sees after cutting)
BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = BACK_COVER_RIGHT
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = FRONT_COVER_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# Vertical
TRIM_TOP = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch
COVER_CENTER_Y = DOC_H / 2

# Safety margins
SAFETY = 0.5 * inch
FRONT_SAFETY = 0.25 * inch

FRONT_SAFE_LEFT = FRONT_TRIM_LEFT + FRONT_SAFETY
FRONT_SAFE_RIGHT = FRONT_TRIM_RIGHT - FRONT_SAFETY
FRONT_SAFE_WIDTH = FRONT_SAFE_RIGHT - FRONT_SAFE_LEFT


def check_front_safety(c, text, font_name, font_size, cx):
    """Check if centered text fits within front cover safety zone."""
    w = c.stringWidth(text, font_name, font_size)
    half_w = w / 2
    left_edge = cx - half_w
    right_edge = cx + half_w
    left_margin = (left_edge - FRONT_TRIM_LEFT) / inch
    right_margin = (FRONT_TRIM_RIGHT - right_edge) / inch
    min_margin = min(left_margin, right_margin)
    status = "OK" if min_margin >= 0.125 else "WARN"
    print(f'  [{status}] "{text}" ({font_name} {font_size}pt): '
          f'metric width={w/inch:.2f}", margins: L={left_margin:.3f}" R={right_margin:.3f}"')
    return min_margin >= 0.125


def wrap_text(c, text, font_name, font_size, max_width):
    """Wrap text to fit within max_width. Returns list of lines."""
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_background(c):
    """Fill entire document with deep midnight blue."""
    c.setFillColor(DEEP_BLUE)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw front cover: background image + text overlay."""
    cx = FRONT_CENTER_X

    # --- Place background image ---
    img = ImageReader(str(BG_IMAGE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    # Portrait image on portrait cover — scale to fill
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

    # --- Semi-transparent overlay at top for title readability ---
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_COVER_LEFT, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)

    steps = 40
    top_y = DOC_H
    grad_height = 4.0 * inch
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.5
        c.setFillColor(Color(0.06, 0.08, 0.14, alpha))
        y = top_y - (i * grad_height / steps)
        h = grad_height / steps + 1
        c.rect(FRONT_COVER_LEFT, y - h, target_w, h, fill=1, stroke=0)

    c.restoreState()

    # --- Title: "From the" ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 22)
    c.drawCentredString(cx, DOC_H - 1.5 * inch, "From the")
    check_front_safety(c, "From the", "EBGaramond-Italic", 22, cx)

    # --- Title: "Beginning" ---
    c.setFont("EBGaramond", 48)
    c.drawCentredString(cx, DOC_H - 2.2 * inch, "Beginning")
    check_front_safety(c, "Beginning", "EBGaramond", 48, cx)

    # --- Subtitle (dark blue for contrast against bright horizon) ---
    c.setFillColor(DEEP_BLUE)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, DOC_H - 2.85 * inch, "The Gospel from the Ground Up")
    check_front_safety(c, "The Gospel from the Ground Up", "EBGaramond-Italic", 13, cx)

    # --- Semi-transparent overlay at bottom for author ---
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_COVER_LEFT, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)

    bottom_grad_height = 2.0 * inch
    for i in range(steps):
        alpha = 0.5 * (i / steps) ** 1.5
        c.setFillColor(Color(0.06, 0.08, 0.14, alpha))
        y = bottom_grad_height * (1 - i / steps)
        h = bottom_grad_height / steps + 1
        c.rect(FRONT_COVER_LEFT, y - h, target_w, h, fill=1, stroke=0)

    c.restoreState()

    # --- Author name ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    author_y = TRIM_BOTTOM + SAFETY + 0.2 * inch
    c.drawCentredString(cx, author_y, "P A U L   &   P A M   H A I N L I N E")
    check_front_safety(c, "P A U L   &   P A M   H A I N L I N E", "EBGaramond", 16, cx)


def draw_spine(c):
    """Draw spine text. Lulu gives us 0.407" — a bit more room than
    IngramSpark's 0.347" but still tight, so keep the text small."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(0, 3, "From the Beginning")
    c.setFont("EBGaramond", 6.5)
    c.drawCentredString(0, -6, "Paul & Pam Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover text on deep midnight blue background."""
    safe_left = BACK_TRIM_LEFT + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X

    # --- Opening verse (italic, gold) ---
    y = TRIM_TOP - 1.0 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 10)
    verse = "\u201cIn the beginning God created the heavens and the earth.\u201d"
    c.drawCentredString(cx, y, verse)
    y -= 14
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, y, "\u2014 Genesis 1:1")
    y -= 10

    # --- Thin decorative line ---
    y -= 8
    line_hw = 0.6 * inch
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 20

    # --- Body text (cream) ---
    c.setFillColor(CREAM)
    line_height = 13.5

    body_paragraphs = [
        "You don\u2019t need a church background to read this book. You don\u2019t need to know anything about the Bible. You just need to be willing to look.",
        "From the Beginning starts where the Bible starts \u2014 with a God who created you on purpose, who knew you before you were born, and who had a plan for your rescue before the world began. In ten chapters, it walks you through the whole story: who God is, what went wrong, the long thread of promise that runs through Scripture, and the Christ who fulfilled every word of it.",
        "This is not a book of opinions. Every claim is anchored in Scripture. Every chapter builds on the last. And by the end, you\u2019ll understand not just what God did \u2014 but what He asks you to do about it.",
        "If you\u2019ve been looking for the starting line, this is it.",
    ]

    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # --- Attribution ---
    y -= line_height * 0.3
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y, "Scripture quotations from the New American Standard Bible\u00ae (NASB).")

    # --- Imprint mark in the lower area (no ISBN for this printing) ---
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(GOLD_LIGHT)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating Lulu PAPERBACK cover PDF for "From the Beginning"...')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages, Lulu B&W white paper)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')
    print(f'  Expected (from Lulu template): 11.657" x 8.750"')
    print(f'  Front cover type safety: {FRONT_SAFETY/inch}" from trim edges')
    print(f'  Front cover safe text width: {FRONT_SAFE_WIDTH/inch:.2f}"')
    print(f'\nFront cover text safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("From the Beginning - Lulu Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
