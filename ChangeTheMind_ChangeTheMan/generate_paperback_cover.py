#!/usr/bin/env python3
"""Generate Lulu-ready PAPERBACK cover PDF for Change the Mind, Change the Man.

Template specs (from Lulu template for 5.5x8.5 paperback, 141 pages):
  Total document size (with bleed): 11.628" x 8.75"
  Book trim size: 5.5" x 8.5"
  Spine width: 0.378"
  Bleed area: 0.125"
  Safety margin: 0.5"
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "ChangeTheMind_ChangeTheMan_Paperback_Cover.pdf"
IMAGE_FILE = BOOK_DIR / "desert_valley_cover_1725x2775.png"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions ---
DOC_W = 11.628 * inch
DOC_H = 8.75 * inch

# --- Colors ---
DARK_BG = Color(0.05, 0.05, 0.05)
TEXT_WHITE = Color(1, 1, 1)

# --- Layout ---
BLEED = 0.125 * inch
SPINE_W = 0.378 * inch
COVER_W = 5.5 * inch  # trim width of each cover panel
SAFETY = 0.5 * inch

# Zone boundaries (from left edge of document)
# Layout: bleed + back_cover_trim + bleed + spine + bleed + front_cover_trim + bleed
# But the bleeds overlap between panels, so:
# back_cover_with_bleed = bleed + 5.5 + bleed/overlap = 5.625" (left edge to spine)
# Actually: total = back_cover_w_bleed + spine + front_cover_w_bleed
# back_cover_w_bleed = (DOC_W - SPINE_W) / 2 = (11.628 - 0.378) / 2 = 5.625"

BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = (DOC_W - SPINE_W * inch / inch * inch) / 2  # Hmm, let me just calculate directly

# Simpler: from the template, the layout is symmetric
# back_cover_with_bleed_width = (total_width - spine_width) / 2
HALF_W = (DOC_W - SPINE_W) / 2

BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = HALF_W

SPINE_LEFT = HALF_W
SPINE_RIGHT = HALF_W + SPINE_W
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

# Trim edges (0.125" inside bleed on outer edges)
BACK_TRIM_LEFT = BLEED
BACK_TRIM_RIGHT = HALF_W - BLEED  # inner edge near spine
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = SPINE_RIGHT + BLEED  # inner edge near spine
FRONT_TRIM_RIGHT = DOC_W - BLEED
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# Vertical
V_BLEED = (DOC_H - 8.5 * inch) / 2  # = 0.125"
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_CENTER_Y = DOC_H / 2


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
    """Fill entire document with dark background."""
    c.setFillColor(DARK_BG)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover_image(c):
    """Place the cover image on the front cover area."""
    img = ImageReader(str(IMAGE_FILE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    # Center image on TRIM area (not full panel) so content appears visually centered.
    # The panel includes bleed on the right side, which shifts the panel center
    # right of the visual trim center. Correct for this.
    trim_center_x = FRONT_TRIM_LEFT + COVER_W / 2

    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = trim_center_x - draw_w / 2
        draw_y = 0
    else:
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = trim_center_x - draw_w / 2
        draw_y = (target_h - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()


def draw_front_cover_text(c):
    """Draw title, author, and inspired-by text on front cover."""
    cx = FRONT_CENTER_X

    c.setFillColor(TEXT_WHITE)
    c.setFont("EBGaramond", 34)
    c.drawCentredString(cx, TRIM_TOP - 1.4 * inch, "Change the Mind,")
    c.setFont("EBGaramond", 34)
    c.drawCentredString(cx, TRIM_TOP - 2.0 * inch, "Change the Man")

    c.setFont("EBGaramond", 20)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.6 * inch, "Paul Hainline")

    c.setFont("EBGaramond-Italic", 14)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.1 * inch, "Inspired by the teaching of Freddie Anderson")


def draw_spine(c):
    """Draw spine text. Spine is narrow (0.378") so use small font."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(TEXT_WHITE)
    c.setFont("EBGaramond", 7)
    c.drawCentredString(0, 2, "Change the Mind, Change the Man")
    c.setFont("EBGaramond", 6)
    c.drawCentredString(0, -6, "Paul Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover text."""
    safe_left = BACK_TRIM_LEFT + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    c.setFillColor(TEXT_WHITE)

    paragraphs = [
        ("EBGaramond", 13, "Someone you love is destroying himself."),
        ("EBGaramond", 13, "Or maybe that someone is you."),
        (None, 0, ""),
        ("EBGaramond", 10, "You have tried everything \u2014 the conversations, the ultimatums, the promises, the programs. You have lain awake at night asking questions that have no answers and praying prayers that feel like they hit the ceiling. You have watched addiction take a person you knew and replace him with someone you don\u2019t recognize. And you have wondered, more times than you can count, whether there is a way through this \u2014 or whether \u201cthrough\u201d is just a word people say when they don\u2019t know what else to offer."),
        (None, 0, ""),
        ("EBGaramond", 10, "This book was not written by a counselor, a clinician, or a theologian. It was written by a man who was introduced to drugs at thirteen, arrested at seventeen and sentenced to life in prison, and who spent the next three decades watching addiction destroy everything it touched \u2014 including himself."),
        (None, 0, ""),
        ("EBGaramond", 10, "It is a straightforward examination of what God\u2019s Word says about how the mind turns away from God, how it turns back, and why the substance was never the real problem. The gaze was."),
        (None, 0, ""),
        ("EBGaramond-Italic", 9, "Scripture quotations from the New American Standard Bible\u00ae."),
    ]

    y = TRIM_TOP - 1.2 * inch
    line_height = 14

    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.6
            continue
        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.3


def main():
    print('Generating Lulu PAPERBACK cover PDF for "Change the Mind, Change the Man"...')
    print(f'  Document size: 11.628" x 8.75"')
    print(f'  Spine width: 0.378"')
    print(f'  Page count: 141')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))

    draw_background(c)
    draw_front_cover_image(c)
    draw_front_cover_text(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
