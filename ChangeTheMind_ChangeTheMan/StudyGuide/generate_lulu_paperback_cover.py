#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for the Study Guide.

Lulu prints on cream paper, which is bulkier than IngramSpark's 50# white,
so the spine is wider for the same page count. Spine width is taken from
Lulu's downloaded cover template, NOT from the per-page formula
(see CLAUDE.md memory note: cream paper spine ≠ formula).

Lulu specs for 7" x 10" perfect-bound paperback (62-page Study Guide):
  Trim size:      7" x 10"
  Spine width:    0.197" / 5mm   (per Lulu cover template)
  Bleed:          0.125" on outside edges only
  Total document: 14.447" x 10.25"
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

GUIDE_DIR_FOR_TOOLS = Path(__file__).parent
sys.path.insert(0, str(GUIDE_DIR_FOR_TOOLS.parent.parent / "tools"))
from isbn_barcode import draw_isbn_barcode  # noqa: E402

ISBN_STUDY_GUIDE = "979-8-9954288-6-2"

GUIDE_DIR = Path(__file__).parent
OUTPUT = GUIDE_DIR / "ChangeTheMind_StudyGuide_Lulu_Paperback_Cover.pdf"

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (from Lulu cover template, NOT computed) ---
PAGE_COUNT = 62
SPINE_W = 0.197 * inch          # Lulu cream paper, per template

TRIM_W = 7.0 * inch
TRIM_H = 10.0 * inch
BLEED = 0.125 * inch
SAFETY = 0.5 * inch          # used for the ISBN barcode placement
BLURB_INSET = 1.0 * inch     # back-cover blurb column inset (wider than SAFETY for a more readable measure)

DOC_W = BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED   # 14.447"
DOC_H = BLEED + TRIM_H + BLEED                      # 10.25"

# --- Colors ---
NAVY = Color(9/255, 21/255, 40/255)        # #091528
GOLD = Color(196/255, 169/255, 78/255)     # #C4A94E
CREAM = Color(240/255, 232/255, 216/255)   # #F0E8D8
WHITE = Color(1, 1, 1)

# --- Zone boundaries ---
BACK_LEFT = 0
BACK_RIGHT = BLEED + TRIM_W
SPINE_LEFT = BACK_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W
FRONT_LEFT = SPINE_RIGHT
FRONT_RIGHT = DOC_W

BACK_TRIM_LEFT = BLEED
BACK_TRIM_RIGHT = BACK_RIGHT
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = FRONT_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

V_BLEED_BOTTOM = BLEED
V_BLEED_TOP = DOC_H - BLEED
TRIM_BOTTOM = V_BLEED_BOTTOM
TRIM_TOP = V_BLEED_TOP


def wrap_text(c, text, font_name, font_size, max_width):
    """Wrap text to fit within max_width. Returns list of lines."""
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
    """Fill entire document with navy."""
    c.setFillColor(NAVY)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw the front cover: title, subtitle, author, gold rule."""
    cx = FRONT_CENTER_X

    # Title — two lines in gold
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 32)
    c.drawCentredString(cx, TRIM_TOP - 2.8 * inch, "Change the Mind,")
    c.drawCentredString(cx, TRIM_TOP - 3.4 * inch, "Change the Man")

    # Gold rule
    rule_y = TRIM_TOP - 3.8 * inch
    rule_half = 1.8 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.75)
    c.line(cx - rule_half, rule_y, cx + rule_half, rule_y)

    # Subtitle — italic, cream
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 16)
    c.drawCentredString(cx, TRIM_TOP - 4.35 * inch, "A Scriptural Study Guide")

    # Audience line — smaller, cream
    c.setFont("EBGaramond-Italic", 10.5)
    c.setFillColor(Color(0.75, 0.72, 0.65))  # slightly muted cream
    c.drawCentredString(cx, TRIM_TOP - 4.85 * inch, "For Use with Prison Ministries, Reentry Programs,")
    c.drawCentredString(cx, TRIM_TOP - 5.1 * inch, "Congregational Studies, and Families")

    # Author — gold, bottom area
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 18)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.2 * inch, "Paul Hainline")


def draw_back_cover(c):
    """Draw back cover with blurb text."""
    safe_left = BACK_TRIM_LEFT + BLURB_INSET
    safe_right = BACK_TRIM_RIGHT - BLURB_INSET
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X

    y = TRIM_TOP - 1.3 * inch
    line_h = 15

    def draw_paragraph(text, font, size, color, centered=True, spacing=0.3):
        nonlocal y
        c.setFillColor(color)
        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            if centered:
                c.drawCentredString(cx, y, line)
            else:
                c.drawString(safe_left, y, line)
            y -= line_h
        y -= line_h * spacing

    def draw_gap(factor=0.5):
        nonlocal y
        y -= line_h * factor

    # Hook line — gold, larger
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, y, "The book tells you where to look.")
    y -= line_h + 2
    c.drawCentredString(cx, y, "The Bible tells you what to see.")
    y -= line_h * 1.5

    # Gold rule
    rule_half = 1.2 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - rule_half, y, cx + rule_half, y)
    y -= line_h * 1.2

    # Description
    draw_paragraph(
        "This ten-week Scripture study guide walks groups through "
        "Change the Mind, Change the Man one chapter at a time — "
        "but the book is not the curriculum. The Bible is. Every question "
        "sends the group into the biblical text. Every discussion begins "
        "and ends in Scripture.",
        "EBGaramond", 10, CREAM, centered=True
    )

    draw_gap(0.3)

    # Two tracks highlight
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 11)
    c.drawCentredString(cx, y, "Two tracks. One room.")
    y -= line_h * 1.0

    draw_paragraph(
        "Each week includes questions for the person in the struggle "
        "and questions for the family carrying the weight — because these "
        "two audiences are living inside the same story, and they belong "
        "in the same conversation.",
        "EBGaramond", 10, CREAM, centered=True
    )

    draw_gap(0.3)

    draw_paragraph(
        "Designed for prison ministries, reentry programs, congregational "
        "Bible studies, and families — wherever people are willing to "
        "open the text and stay in it.",
        "EBGaramond-Italic", 9.5,
        Color(0.7, 0.67, 0.6), centered=True
    )

    # NASB attribution — very small, raised above the ISBN barcode panel
    c.setFillColor(Color(0.5, 0.48, 0.43))
    c.setFont("EBGaramond-Italic", 7.5)
    nasb_y = TRIM_BOTTOM + 1.8 * inch
    c.drawCentredString(cx, nasb_y + line_h * 0.6,
                        "Scripture quotations from the New American Standard Bible® (NASB).")
    c.drawCentredString(cx, nasb_y,
                        "Copyright © The Lockman Foundation. Used by permission.")


def main():
    spine_in = SPINE_W / inch
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating Lulu paperback cover for the Study Guide...')
    print(f'  Trim size:      7" x 10"')
    print(f'  Page count:     {PAGE_COUNT}')
    print(f'  Spine width:    {spine_in:.3f}" (Lulu cream paper, per template)')
    print(f'  Document size:  {doc_w_in:.3f}" x {doc_h_in:.3f}"')
    print()

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))

    draw_background(c)
    draw_front_cover(c)
    draw_back_cover(c)
    # Spine is too thin for text — just navy background

    # ISBN barcode — bottom-right of back panel
    barcode_panel_w = 1.75 * inch
    draw_isbn_barcode(
        c,
        ISBN_STUDY_GUIDE,
        x_left=BACK_TRIM_RIGHT - SAFETY - barcode_panel_w,
        y_bottom=TRIM_BOTTOM + SAFETY,
        panel_w=barcode_panel_w,
    )

    c.save()
    print(f'Cover saved to {OUTPUT}')
    print('Done.')


if __name__ == '__main__':
    main()
