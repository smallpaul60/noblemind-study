#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for Before I Formed You.

Lulu specs (5.5x8.5 paperback, 42 pages, B&W white paper):
  Trim: 5.5" x 8.5"
  Spine: 0.155" (Lulu-specified minimum for this title)
  Bleed: 0.125" on all sides
  Total: 11.405" x 8.750"
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BeforeIFormedYou_Lulu_Paperback_Cover.pdf"
COVER_IMAGE = BOOK_DIR / "BeforeIFormed_YouCoverImage_hires.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions ---
PAGE_COUNT = 42
SPINE_W = 0.155  # Lulu-specified for this title
TRIM_W = 5.5
TRIM_H = 8.5
BLEED = 0.125

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H = (BLEED + TRIM_H + BLEED) * inch

# --- Panel positions ---
BACK_LEFT = BLEED * inch
BACK_RIGHT = (BLEED + TRIM_W) * inch
SPINE_LEFT = BACK_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
FRONT_LEFT = SPINE_RIGHT
FRONT_RIGHT = (BLEED + TRIM_W + SPINE_W + TRIM_W) * inch

TRIM_BOTTOM = BLEED * inch
TRIM_TOP = (BLEED + TRIM_H) * inch

BACK_CENTER_X = (BACK_LEFT + BACK_RIGHT) / 2
FRONT_CENTER_X = (FRONT_LEFT + FRONT_RIGHT) / 2

# --- Colors (warm amber/golden tones matching the cover painting) ---
WARM_DARK = Color(0.180, 0.145, 0.100)       # #2E2519 dark warm brown
WARM_CREAM = Color(0.945, 0.910, 0.835)      # #F1E8D5 warm parchment
WARM_GOLD = Color(0.780, 0.690, 0.480)       # #C7B07A muted gold
WARM_LIGHT = Color(0.890, 0.850, 0.760)      # #E3D9C2 light parchment


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip() if current else word
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_background(c):
    """Fill entire cover with warm dark brown."""
    c.setFillColor(WARM_DARK)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Place cover image on front panel with title overlay."""
    img = ImageReader(str(COVER_IMAGE))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    # Fill the front panel + bleed on right edge
    target_x = FRONT_LEFT
    target_w = FRONT_RIGHT + BLEED * inch - FRONT_LEFT
    target_y = 0
    target_h = DOC_H
    target_aspect = target_w / target_h

    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = target_x + (target_w - draw_w) / 2
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

    # Title text overlay at the top
    cx = FRONT_CENTER_X
    safety = 0.5 * inch

    c.setFillColor(WARM_CREAM)
    c.setFont("EBGaramond", 24)
    c.drawCentredString(cx, TRIM_TOP - 1.1 * inch, "Before I Formed You")

    c.setFillColor(WARM_LIGHT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, TRIM_TOP - 1.55 * inch, "What God Says to the Woman")
    c.drawCentredString(cx, TRIM_TOP - 1.75 * inch, "Holding This Book")

    # Author name
    c.setFillColor(WARM_CREAM)
    c.setFont("EBGaramond", 13)
    c.drawCentredString(cx, TRIM_BOTTOM + 0.8 * inch, "Paul & Pam Hainline")


def draw_back_cover(c):
    """Draw back cover — warm parchment with blurb."""
    # Parchment background on back panel
    c.setFillColor(WARM_CREAM)
    c.rect(0, 0, SPINE_LEFT, DOC_H, fill=1, stroke=0)

    cx = BACK_CENTER_X
    safety = 0.625 * inch
    safe_left = BACK_LEFT + safety
    safe_right = BACK_RIGHT - safety
    text_width = safe_right - safe_left

    # Hook line
    c.setFillColor(WARM_DARK)
    y = TRIM_TOP - 1.2 * inch
    c.setFont("EBGaramond-Italic", 11)
    hook = "She sat down a bowshot away, because she said, \u201cDo not let me see the boy die.\u201d"
    lines = wrap_text(c, hook, "EBGaramond-Italic", 11, text_width)
    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= 15

    # Thin decorative line
    y -= 10
    c.setStrokeColor(WARM_GOLD)
    c.setLineWidth(0.4)
    c.line(cx - 0.5 * inch, y, cx + 0.5 * inch, y)
    y -= 20

    # Body text
    ls = 14
    body = [
        "This book is written for you \u2014 the woman holding it right now, wherever you are, whatever you\u2019re facing.",
        "It walks through the stories of women in Scripture who faced moments they did not choose: Hagar, alone in the desert. Jochebed, hiding her son under a death sentence. Hannah, broken and desperate. Ruth, gleaning scraps to survive. Rahab, risking everything on a God she barely knew. Mary, young and frightened and saying yes. Esther, placed where she needed to be for such a time as hers.",
        "Every one of them carried something whose purpose was larger than anything they could see.",
        "Everything in these pages comes from Scripture. We didn\u2019t add to it. We just told the stories and let God\u2019s Word speak for itself.",
    ]

    c.setFillColor(WARM_DARK)
    for para in body:
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        for line in lines:
            c.setFont("EBGaramond", 10)
            c.drawCentredString(cx, y, line)
            y -= ls
        y -= ls * 0.4

    # Scripture at bottom
    y -= ls * 0.3
    c.setFillColor(Color(0.35, 0.30, 0.22))
    c.setFont("EBGaramond-Italic", 9.5)
    c.drawCentredString(cx, y, "\u201cBefore I formed you in the womb I knew you,")
    y -= 13
    c.drawCentredString(cx, y, "before you were born I consecrated you.\u201d")
    y -= 15
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, y, "\u2014 Jeremiah 1:5")

    # NobleMind Press at very bottom
    c.setFillColor(Color(0.50, 0.45, 0.35))
    c.setFont("EBGaramond", 7.5)
    c.drawCentredString(cx, TRIM_BOTTOM + 0.35 * inch, "NobleMind Press \u00b7 noblemind.study")


def main():
    print('Generating Lulu paperback cover for "Before I Formed You"...')
    print(f"  Pages: {PAGE_COUNT}")
    print(f"  Spine: {SPINE_W:.4f}\" (no spine text)")
    print(f"  Doc size: {DOC_W/inch:.4f}\" x {DOC_H/inch:.4f}\"")

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Before I Formed You - Lulu Paperback Cover")

    draw_background(c)
    draw_back_cover(c)
    draw_front_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
