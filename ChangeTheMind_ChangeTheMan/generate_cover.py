#!/usr/bin/env python3
"""Generate Lulu-ready cover PDF for Change the Mind, Change the Man.

Template specs (from Lulu template for 5.5x8.5 hardcover with flaps, 141 pages):
  Total document size (with bleed): 19.375" x 9.25"
  Book cover size (with bleed): 5.75" x 8.75"
  Book trim size: 5.5" x 8.5"
  Spine width: 0.625" (page count: 141)
  Bleed area: 0.125" on cover panels
  Safety margin: 0.5"
  Flap dimension: 3.25" x 8.5"
  Flap live area: 2.25" x 7.75"
  Fold safety margin: 0.25"
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "ChangeTheMind_ChangeTheMan_Cover.pdf"
IMAGE_FILE = BOOK_DIR / "desert_valley_cover_1725x2775.png"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions ---
DOC_W = 19.375 * inch
DOC_H = 9.25 * inch

# --- Colors ---
DARK_BG = Color(0.05, 0.05, 0.05)   # Near-black for background
TEXT_WHITE = Color(1, 1, 1)           # Pure white
TEXT_CREAM = Color(0.95, 0.93, 0.88)  # Soft cream white
SHADOW = Color(0, 0, 0, 0.6)         # Semi-transparent black for text shadow

# --- Layout positions (from left edge of document) ---
# Layout: bleed(0.125) + back_flap(3.25) + fold(0.25) + back_cover_w_bleed(5.75)
#         + spine(0.625) + front_cover_w_bleed(5.75) + fold(0.25) + front_flap(3.25) + bleed(0.125)
# Total: 0.125 + 3.25 + 0.25 + 5.75 + 0.625 + 5.75 + 0.25 + 3.25 + 0.125 = 19.375" ✓

OUTER_BLEED = 0.125 * inch
FLAP_W = 3.25 * inch
FOLD_MARGIN = 0.25 * inch
COVER_W_BLEED = 5.75 * inch
SPINE_W = 0.625 * inch

# Zone boundaries (from left)
BACK_FLAP_LEFT = OUTER_BLEED
BACK_FLAP_RIGHT = BACK_FLAP_LEFT + FLAP_W

BACK_COVER_LEFT = BACK_FLAP_RIGHT + FOLD_MARGIN
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W_BLEED

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W_BLEED

FRONT_FLAP_LEFT = FRONT_COVER_RIGHT + FOLD_MARGIN
FRONT_FLAP_RIGHT = FRONT_FLAP_LEFT + FLAP_W

# Trim edges (0.125" inside bleed on cover panels)
COVER_BLEED = 0.125 * inch

FRONT_TRIM_LEFT = FRONT_COVER_LEFT + COVER_BLEED
FRONT_TRIM_RIGHT = FRONT_COVER_RIGHT - COVER_BLEED
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

BACK_TRIM_LEFT = BACK_COVER_LEFT + COVER_BLEED
BACK_TRIM_RIGHT = BACK_COVER_RIGHT - COVER_BLEED
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

# Vertical
V_BLEED = 0.375 * inch  # (9.25 - 8.5) / 2
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_HEIGHT = TRIM_TOP - TRIM_BOTTOM
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

# Safety margin: 0.5" inside trim
SAFETY = 0.5 * inch

# Flap text area — Lulu live area is 2.25" x 7.75"
# Front flap: inner edge has fold margin, outer edge has bleed
FRONT_FLAP_SAFE_LEFT = FRONT_FLAP_LEFT + 0.5 * inch   # generous inner margin
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - 0.5 * inch  # outer margin
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT  # ~2.25"

# Back flap: shift right to account for outer bleed on left edge
BACK_FLAP_SAFE_LEFT = BACK_FLAP_LEFT + 0.625 * inch
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - 0.375 * inch
BACK_FLAP_TEXT_W = BACK_FLAP_SAFE_RIGHT - BACK_FLAP_SAFE_LEFT  # ~2.25"


def draw_background(c):
    """Fill entire document with dark background."""
    c.setFillColor(DARK_BG)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover_image(c):
    """Place the cover image on the front cover area, filling it completely."""
    img = ImageReader(str(IMAGE_FILE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    # Target area: front cover with bleed — full height of document
    target_x = FRONT_COVER_LEFT
    target_w = COVER_W_BLEED
    target_h = DOC_H
    target_aspect = target_w / target_h

    # Scale image to cover the target area completely
    if img_aspect > target_aspect:
        # Image is wider — fit height, center horizontally
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = target_x + (target_w - draw_w) / 2
        draw_y = 0
    else:
        # Image is taller — fit width, center vertically
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = target_x
        draw_y = (target_h - draw_h) / 2

    # Clip to front cover area and draw
    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()


def draw_front_cover_text(c):
    """Draw title, author, and inspired-by text on front cover.
    No background overlay — white text directly on the grey sky.
    Title near top, author and inspired-by near bottom.
    """
    cx = FRONT_CENTER_X

    # Title line 1: "Change the Mind," — white on grey sky
    c.setFillColor(TEXT_WHITE)
    c.setFont("EBGaramond", 34)
    c.drawCentredString(cx, TRIM_TOP - 1.4 * inch, "Change the Mind,")

    # Title line 2: "Change the Man"
    c.setFont("EBGaramond", 34)
    c.drawCentredString(cx, TRIM_TOP - 2.0 * inch, "Change the Man")

    # Author name — pushed down toward bottom of cover
    c.setFont("EBGaramond", 20)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.6 * inch, "Paul Hainline")

    # Inspired by — below author
    c.setFont("EBGaramond-Italic", 14)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.1 * inch, "Inspired by the teaching of Freddie Anderson")


def draw_spine(c):
    """Draw spine text (reading top to bottom)."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(TEXT_WHITE)
    c.setFont("EBGaramond", 10)
    # Title and author on spine
    c.drawCentredString(0, 3, "Change the Mind, Change the Man")
    c.setFont("EBGaramond", 8)
    c.drawCentredString(0, -8, "Paul Hainline")

    c.restoreState()


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


def draw_back_cover(c):
    """Draw back cover text — centered within back cover safety area."""
    # Center within back cover safety area, shifted slightly right
    # to account for fold margin on left side
    safe_left = BACK_TRIM_LEFT + SAFETY + 0.125 * inch
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    c.setFillColor(TEXT_WHITE)

    # Back cover text from dustjacket_text.md
    paragraphs = [
        ("EBGaramond", 13, "Someone you love is destroying himself."),
        ("EBGaramond", 13, "Or maybe that someone is you."),
        (None, 0, ""),  # spacer
        ("EBGaramond", 10, "You have tried everything \u2014 the conversations, the ultimatums, the promises, the programs. You have lain awake at night asking questions that have no answers and praying prayers that feel like they hit the ceiling. You have watched addiction take a person you knew and replace him with someone you don\u2019t recognize. And you have wondered, more times than you can count, whether there is a way through this \u2014 or whether \u201cthrough\u201d is just a word people say when they don\u2019t know what else to offer."),
        (None, 0, ""),  # spacer
        ("EBGaramond", 10, "This book was not written by a counselor, a clinician, or a theologian. It was written by a man who was introduced to drugs at fourteen, arrested at seventeen and sentenced to life in prison, and who spent the next three decades watching addiction destroy everything it touched \u2014 including himself."),
        (None, 0, ""),  # spacer
        ("EBGaramond", 10, "It is a straightforward examination of what God\u2019s Word says about how the mind turns away from God, how it turns back, and why the substance was never the real problem. The gaze was."),
        (None, 0, ""),  # spacer
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
        y -= line_height * 0.3  # paragraph spacing


def draw_front_flap(c):
    """Draw front flap text — constrained to flap live area."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    paragraphs = [
        ("EBGaramond", 8, "Freddie Anderson, the preacher who shaped the author\u2019s approach to Scripture, used to say: if you change a person\u2019s mind, you change everything about them. If you don\u2019t change their mind, you don\u2019t change anything."),
        (None, 0, ""),
        ("EBGaramond", 8, "That is the argument of this book."),
        (None, 0, ""),
        ("EBGaramond", 8, "Change the Mind, Change the Man traces two movements that mirror the actual experience of addiction and recovery. The first five chapters follow the descent \u2014 the crisis, the progression, the guilt, the hidden prisons, and the agonizing decisions families are forced to make. The second five chapters follow the return \u2014 the biblical mechanism of change, genuine repentance, forgiveness, the long daily road of recovery, and the gospel invitation for anyone who reaches the end and realizes they need the foundation it describes."),
        (None, 0, ""),
        ("EBGaramond", 8, "This is not a twelve-step program. It is not a clinical treatment guide. It is a careful, honest walk through Scripture \u2014 with the Greek and Hebrew examined where they illuminate meaning \u2014 applied directly to the reality of addiction by a man who has lived every chapter of it."),
        (None, 0, ""),
        ("EBGaramond", 8, "Whether you are the one struggling, a family member carrying the weight, or a friend searching for answers \u2014 this book speaks to you. Not to one and then the other. To all of you at once. Because addiction is a shared story, and the road through it is walked together."),
    ]

    c.setFillColor(TEXT_CREAM)
    y = TRIM_TOP - SAFETY
    line_height = 11

    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.5
            continue

        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            c.drawString(safe_left, y, line)
            y -= line_height
        y -= line_height * 0.2


def draw_back_flap(c):
    """Draw back flap text (About the Author) — constrained to flap live area."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(TEXT_CREAM)

    # "About the Author" heading
    c.setFont("EBGaramond", 10)
    y = TRIM_TOP - SAFETY
    c.drawString(safe_left, y, "About the Author")
    y -= 16

    paragraphs = [
        "Paul was introduced to drugs at the age of fourteen. At seventeen, he was arrested for robbery and murder and sentenced to life in prison. He served thirty-three years before parole was granted.",
        "",
        "During those years, he witnessed the full cycle of addiction \u2014 men who walked out of prison determined to go straight and fell within weeks, and men who walked out with no intention of changing at all. He tried self-help books, the wisdom of man, and spent years trying to convince himself that God was not real. None of it filled the void.",
        "",
        "It was the teaching of Freddie Anderson \u2014 a preacher whose method was always \u201cLet\u2019s see what the Bible says\u201d \u2014 and the daily discipline of being in God\u2019s Word that finally changed everything. Not the circumstances. Not the environment. The mind.",
        "",
        "Paul obeyed the gospel, was baptized into Christ, and the man who walked into that prison at seventeen became a different man entirely. He is now sixty-five years old and the author of One Day Closer to Home and Change the Mind, Change the Man.",
        "",
        "He writes not from theory, not from a safe distance, but from the road itself.",
    ]

    line_height = 10.5
    for text in paragraphs:
        if text == "":
            y -= line_height * 0.4
            continue

        lines = wrap_text(c, text, "EBGaramond", 7.5, text_width)
        for line in lines:
            c.setFont("EBGaramond", 7.5)
            c.drawString(safe_left, y, line)
            y -= line_height
        y -= line_height * 0.15


def main():
    print('Generating Lulu cover PDF for "Change the Mind, Change the Man"...')
    print(f'  Document size: 19.375" x 9.25"')
    print(f'  Spine width: 0.625"')
    print(f'  Page count: 141')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))

    draw_background(c)
    draw_front_cover_image(c)
    draw_front_cover_text(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
