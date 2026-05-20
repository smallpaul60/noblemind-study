#!/usr/bin/env python3
"""Generate IngramSpark paperback cover for the CTM Study Guide.

IngramSpark template specs (from 9798995428862-Perfect.pdf,
Lightning Source request CSS5209702, ISBN 979-8-9954288-6-2):
  Document size:    19.000" x 12.000"     (must match template exactly)
  Bleed area:       14.628" x 10.250"     positioned at (3.372", 1.750")
                                          (asymmetric: left=3.372,
                                           right=1.000, top=0, bottom=1.75)
  Trim per cover:   7.000" x 10.000"
  Cover panel bleed: 7.250" x 10.250"     each
  Spine width:      0.128"                (62 pages, white paper, B&W)
  Bleed within bleed area: 0.125"
  Page count:       62

Layout left-to-right within the bleed area:
  [back cover bleed 7.25][spine 0.128][front cover bleed 7.25]
  Sum: 7.25 + 0.128 + 7.25 = 14.628 in.

The template carries IngramSpark's trim/fold marks in its outer white
margins. We render artwork only within the bleed area and overlay it
onto the template via pypdf.merge_page so those marks survive.

Design mirrors the Lulu Study Guide cover (navy field, gold typographic
title, gold rule, cream subtitle + audience line, full back-cover
description with the two-tracks structure, NASB attribution) so both
editions read as the same book on a shelf.
"""

import sys
from pathlib import Path
import pypdf

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

GUIDE_DIR = Path(__file__).parent
sys.path.insert(0, str(GUIDE_DIR.parent.parent / "tools"))
from isbn_barcode import draw_isbn_barcode  # noqa: E402

TEMPLATE_FILE = GUIDE_DIR / "9798995428862-Perfect.pdf"
ARTWORK_TMP   = GUIDE_DIR / "_ingram_sg_artwork.pdf"
OUTPUT        = GUIDE_DIR / "ChangeTheMind_StudyGuide_IngramSpark_Paperback_Cover.pdf"
ISBN_STUDY_GUIDE = "979-8-9954288-6-2"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (must match IngramSpark template exactly) ---
PAGE_COUNT      = 62
DOC_W_IN        = 19.000
DOC_H_IN        = 12.000
DOC_W           = DOC_W_IN * inch
DOC_H           = DOC_H_IN * inch

BLEED_AREA_W_IN = 14.628
BLEED_AREA_H_IN = 10.250
# Bleed area position measured from the actual template: the bleed
# boundary on the LEFT sits at ~x=2.97" (just past a trim/fold mark),
# the TOP runs to the doc edge (y=12), so the bottom = 12 - 10.25 = 1.75
# and the right edge = 2.972 + 14.628 = 17.6. That leaves a wider right
# margin (~1.4") containing the template instruction box.
BLEED_LEFT_IN   =  2.972
BLEED_BOTTOM_IN =  1.750
BLEED_RIGHT_IN  = BLEED_LEFT_IN + BLEED_AREA_W_IN     # 17.600
BLEED_TOP_IN    = BLEED_BOTTOM_IN + BLEED_AREA_H_IN   # 12.000

BLEED_LEFT   = BLEED_LEFT_IN   * inch
BLEED_RIGHT  = BLEED_RIGHT_IN  * inch
BLEED_BOTTOM = BLEED_BOTTOM_IN * inch
BLEED_TOP    = BLEED_TOP_IN    * inch

# Panel widths
BLEED_W          = 0.125          # bleed inset within bleed area
COVER_BLEED_W_IN = 7.250          # = trim 7.0 + 0.125 outer + 0.125 inner
SPINE_W_IN       = 0.128
TRIM_W_IN        = 7.000
TRIM_H_IN        = 10.000

# --- Panel x-positions (document space, in points) ---
BACK_BLEED_LEFT   = BLEED_LEFT
BACK_BLEED_RIGHT  = BACK_BLEED_LEFT + COVER_BLEED_W_IN * inch
SPINE_LEFT        = BACK_BLEED_RIGHT
SPINE_RIGHT       = SPINE_LEFT + SPINE_W_IN * inch
FRONT_BLEED_LEFT  = SPINE_RIGHT
FRONT_BLEED_RIGHT = FRONT_BLEED_LEFT + COVER_BLEED_W_IN * inch

# Trim edges (0.125" inset from each bleed edge of the cover panels)
BACK_TRIM_LEFT   = BACK_BLEED_LEFT  + BLEED_W * inch
BACK_TRIM_RIGHT  = BACK_BLEED_RIGHT - BLEED_W * inch
FRONT_TRIM_LEFT  = FRONT_BLEED_LEFT + BLEED_W * inch
FRONT_TRIM_RIGHT = FRONT_BLEED_RIGHT - BLEED_W * inch

TRIM_BOTTOM = BLEED_BOTTOM + BLEED_W * inch
TRIM_TOP    = BLEED_TOP    - BLEED_W * inch

BACK_CENTER_X  = (BACK_TRIM_LEFT  + BACK_TRIM_RIGHT)  / 2
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# --- Colors (matches Lulu Study Guide cover palette) ---
NAVY  = Color(9/255, 21/255, 40/255)      # #091528
GOLD  = Color(196/255, 169/255, 78/255)   # #C4A94E
CREAM = Color(240/255, 232/255, 216/255)  # #F0E8D8
SOFT  = Color(0.75, 0.72, 0.65)
WHITE = Color(1, 1, 1)

# Safety: 0.75" everywhere, matching the over-provisioned IngramSpark
# practice we landed on after preflight rejected tighter values on TTV.
SAFETY      = 0.75 * inch
BLURB_INSET = 1.00 * inch    # extra breathing room for the back-cover blurb


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
    """Fill ONLY the bleed area with navy. Outside the bleed area we
    leave the canvas untouched so the IngramSpark template marks survive."""
    c.setFillColor(NAVY)
    c.rect(BLEED_LEFT, BLEED_BOTTOM,
           BLEED_AREA_W_IN * inch, BLEED_AREA_H_IN * inch,
           fill=1, stroke=0)


def draw_front_cover(c):
    """Title, gold rule, subtitle, audience line, byline."""
    cx = FRONT_CENTER_X

    # Title in gold, two lines
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 36)
    c.drawCentredString(cx, TRIM_TOP - 2.8 * inch, "Change the Mind,")
    c.drawCentredString(cx, TRIM_TOP - 3.4 * inch, "Change the Man")

    # Gold rule
    rule_y = TRIM_TOP - 3.85 * inch
    rule_half = 1.9 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.85)
    c.line(cx - rule_half, rule_y, cx + rule_half, rule_y)

    # Subtitle — italic cream
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 17)
    c.drawCentredString(cx, TRIM_TOP - 4.4 * inch, "A Scriptural Study Guide")

    # Audience line — smaller, soft
    c.setFillColor(SOFT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, TRIM_TOP - 4.95 * inch,
                        "For Use with Prison Ministries, Reentry Programs,")
    c.drawCentredString(cx, TRIM_TOP - 5.20 * inch,
                        "Congregational Studies, and Families")

    # Author — gold, lower portion
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 19)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.3 * inch, "Paul Hainline")


def draw_back_cover(c):
    """Hook + description, two-tracks structure, NASB attribution."""
    safe_left  = BACK_TRIM_LEFT  + BLURB_INSET
    safe_right = BACK_TRIM_RIGHT - BLURB_INSET
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    y = TRIM_TOP - 1.3 * inch
    line_h = 16

    def draw_paragraph(text, font, size, color, spacing=0.3):
        nonlocal y
        c.setFillColor(color)
        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            c.drawCentredString(cx, y, line)
            y -= line_h
        y -= line_h * spacing

    def gap(factor=0.5):
        nonlocal y
        y -= line_h * factor

    # Hook lines — gold italic, larger
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 14)
    c.drawCentredString(cx, y, "The book tells you where to look.")
    y -= line_h + 3
    c.drawCentredString(cx, y, "The Bible tells you what to see.")
    y -= line_h * 1.6

    # Gold rule
    rule_half = 1.3 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - rule_half, y, cx + rule_half, y)
    y -= line_h * 1.3

    # Description
    draw_paragraph(
        "This ten-week Scripture study guide walks groups through "
        "Change the Mind, Change the Man one chapter at a time — "
        "but the book is not the curriculum. The Bible is. Every question "
        "sends the group into the biblical text. Every discussion begins "
        "and ends in Scripture.",
        "EBGaramond", 11, CREAM
    )
    gap(0.3)

    # Two tracks subhead
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 12)
    c.drawCentredString(cx, y, "Two tracks. One room.")
    y -= line_h * 1.1

    draw_paragraph(
        "Each week includes questions for the person in the struggle "
        "and questions for the family carrying the weight — because "
        "these two audiences are living inside the same story, and they "
        "belong in the same conversation.",
        "EBGaramond", 11, CREAM
    )
    gap(0.3)

    draw_paragraph(
        "Designed for prison ministries, reentry programs, congregational "
        "Bible studies, and families — wherever people are willing "
        "to open the text and stay in it.",
        "EBGaramond-Italic", 10.5, SOFT
    )

    # NASB attribution — small, raised above the barcode panel
    c.setFillColor(Color(0.55, 0.53, 0.48))
    c.setFont("EBGaramond-Italic", 8)
    nasb_y = TRIM_BOTTOM + 1.9 * inch
    c.drawCentredString(cx, nasb_y + line_h * 0.6,
        "Scripture quotations from the New American Standard Bible® (NASB).")
    c.drawCentredString(cx, nasb_y,
        "Copyright © The Lockman Foundation. Used by permission.")


def main():
    if not TEMPLATE_FILE.exists():
        raise SystemExit(f"ERROR: IngramSpark template not found at {TEMPLATE_FILE}")

    print('Generating IngramSpark PAPERBACK cover for the CTM Study Guide...')
    print(f'  Document size: {DOC_W_IN}" x {DOC_H_IN}" (per IngramSpark template)')
    print(f'  Bleed area:    {BLEED_AREA_W_IN}" x {BLEED_AREA_H_IN}" '
          f'at ({BLEED_LEFT_IN}", {BLEED_BOTTOM_IN}")')
    print(f'  Spine:         {SPINE_W_IN}" ({PAGE_COUNT} pages, white)')

    c = canvas.Canvas(str(ARTWORK_TMP), pagesize=(DOC_W, DOC_H))
    c.setTitle("Change the Mind, Change the Man — Study Guide — IngramSpark Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_back_cover(c)
    # Spine is too thin (0.128") for any text; navy field only.

    # ISBN barcode — bottom-right of back panel, on the spine side
    barcode_panel_w = 1.85 * inch
    draw_isbn_barcode(
        c,
        ISBN_STUDY_GUIDE,
        x_left=BACK_TRIM_RIGHT - SAFETY - barcode_panel_w,
        y_bottom=TRIM_BOTTOM + SAFETY,
        panel_w=barcode_panel_w,
    )
    c.save()
    print(f"\n  Artwork rendered: {ARTWORK_TMP.name}")

    # --- Merge artwork onto IngramSpark template ---
    template_reader = pypdf.PdfReader(str(TEMPLATE_FILE))
    artwork_reader  = pypdf.PdfReader(str(ARTWORK_TMP))

    base_page    = template_reader.pages[0]
    overlay_page = artwork_reader.pages[0]

    bw = float(base_page.mediabox.width)
    bh = float(base_page.mediabox.height)
    ow = float(overlay_page.mediabox.width)
    oh = float(overlay_page.mediabox.height)
    if abs(bw - ow) > 0.5 or abs(bh - oh) > 0.5:
        raise SystemExit(
            f"ERROR: page size mismatch. template={bw}x{bh}pt, "
            f"artwork={ow}x{oh}pt")

    base_page.merge_page(overlay_page)

    writer = pypdf.PdfWriter()
    writer.add_page(base_page)
    with open(OUTPUT, "wb") as f:
        writer.write(f)

    ARTWORK_TMP.unlink(missing_ok=True)
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
