#!/usr/bin/env python3
"""Generate IngramSpark paperback cover for Change the Mind, Change the Man.

IngramSpark template specs (from IngramSpark-paperback-cover-template.pdf,
Lightning Source Perfect Bound, request CSS5209513):
  Document size:    15.000" x 12.000"   (must match template exactly)
  Bleed area:       11.835" x 8.750"    centered in the document
  Trim per cover:   5.500" x 8.500"
  Spine width:      0.335"              (144 pages, creme paper, B&W)
  Page count:       144
  ISBN:             979-8-9954288-4-8

Layout in document space (left to right):
  [1.5825 template margin]
  [0.125 back outer bleed][5.5 back trim][0.125 back inner bleed]
  [0.335 spine]
  [0.125 front inner bleed][5.5 front trim][0.125 front outer bleed]
  [1.5825 template margin]

The template carries IngramSpark's trim/fold marks in its outer white
margins. We render artwork only inside the bleed area and overlay it
onto the template via pypdf.merge_page so those outer marks survive.

Design mirrors the existing Lulu paperback cover (near-black background,
white EB Garamond typography, desert-valley image filling the front,
full back-cover blurb, ISBN barcode bottom-right of back panel) so both
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
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
sys.path.insert(0, str(BOOK_DIR.parent / "tools"))
from isbn_barcode import draw_isbn_barcode  # noqa: E402

TEMPLATE_FILE = BOOK_DIR / "9798995428848-Perfect.pdf"
ARTWORK_TMP   = BOOK_DIR / "_ingram_pb_artwork.pdf"
OUTPUT        = BOOK_DIR / "ChangeTheMind_ChangeTheMan_IngramSpark_Paperback_Cover.pdf"
IMAGE_FILE    = BOOK_DIR / "desert_valley_cover_1725x2775.png"
ISBN_PAPERBACK = "979-8-9954288-4-8"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document and template geometry ---
# IMPORTANT: the IngramSpark template trim area is NOT centered in the
# 15x12 document. It sits in the upper-right with offsets:
#   left margin = 2.915", right margin = 0.500"
#   bottom margin = 3.2506", top margin = 0.000"
# These offsets were extracted from the template's drawn rectangles. If
# IngramSpark issues a different template (different page count or paper
# stock), re-extract by parsing the rectangles in the content stream.
DOC_W_IN = 15.0
DOC_H_IN = 12.0

# Per-cover panel = 5.5" trim + 0.125" bleed on the OUTSIDE edge only
# (the spine side has no bleed — covers butt directly against the spine).
COVER_PANEL_W_IN = 5.625      # trim 5.5 + 0.125 outside bleed
SPINE_W_IN       = 0.335
BLEED_AREA_W_IN  = COVER_PANEL_W_IN * 2 + SPINE_W_IN   # 11.585
BLEED_AREA_H_IN  = 8.75       # trim 8.5 + 0.125 top + 0.125 bottom

BLEED_LEFT_IN   = 2.915       # template offset, NOT centered
BLEED_BOTTOM_IN = 3.2506      # template offset, NOT centered

BLEED_W_IN      = 0.125       # bleed thickness on each OUTSIDE edge

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

PAGE_COUNT = 144

# Anchors (document space, in pts)
BLEED_LEFT   = BLEED_LEFT_IN   * inch
BLEED_BOTTOM = BLEED_BOTTOM_IN * inch
BLEED_RIGHT  = BLEED_LEFT + BLEED_AREA_W_IN * inch
BLEED_TOP    = BLEED_BOTTOM + BLEED_AREA_H_IN * inch

BACK_BLEED_LEFT  = BLEED_LEFT
BACK_BLEED_RIGHT = BACK_BLEED_LEFT + COVER_PANEL_W_IN * inch
SPINE_LEFT       = BACK_BLEED_RIGHT
SPINE_RIGHT      = SPINE_LEFT + SPINE_W_IN * inch
FRONT_BLEED_LEFT = SPINE_RIGHT
FRONT_BLEED_RIGHT = FRONT_BLEED_LEFT + COVER_PANEL_W_IN * inch

# Trim edges. Bleed is only on the OUTSIDE of each cover panel (spine
# side has no bleed because covers butt directly against the spine).
BACK_TRIM_LEFT   = BACK_BLEED_LEFT  + BLEED_W_IN * inch
BACK_TRIM_RIGHT  = BACK_BLEED_RIGHT                      # no spine-side bleed
FRONT_TRIM_LEFT  = FRONT_BLEED_LEFT                      # no spine-side bleed
FRONT_TRIM_RIGHT = FRONT_BLEED_RIGHT - BLEED_W_IN * inch

TRIM_BOTTOM = BLEED_BOTTOM + BLEED_W_IN * inch
TRIM_TOP    = BLEED_TOP    - BLEED_W_IN * inch

BACK_CENTER_X  = (BACK_TRIM_LEFT  + BACK_TRIM_RIGHT)  / 2
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2
BLEED_CENTER_Y = BLEED_BOTTOM + BLEED_AREA_H_IN * inch / 2

SAFETY = 0.5 * inch

# --- Colors (matches Lulu paperback) ---
DARK_BG    = Color(0.05, 0.05, 0.05)
TEXT_WHITE = Color(1, 1, 1)


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
    """Fill ONLY the bleed area with the dark background. Outside the
    bleed area we leave the canvas untouched so the IngramSpark template
    marks survive the merge."""
    c.setFillColor(DARK_BG)
    c.rect(BLEED_LEFT, BLEED_BOTTOM,
           BLEED_AREA_W_IN * inch, BLEED_AREA_H_IN * inch,
           fill=1, stroke=0)


def draw_front_cover_image(c):
    img = ImageReader(str(IMAGE_FILE))
    src_w, src_h = img.getSize()
    src_aspect = src_w / src_h

    # Image fills the FRONT cover bleed panel (5.75 x 8.75)
    target_x = FRONT_BLEED_LEFT
    target_w = COVER_PANEL_W_IN * inch
    target_h = BLEED_AREA_H_IN * inch
    target_y = BLEED_BOTTOM
    target_aspect = target_w / target_h

    # Scale-to-fill, centered on the trim center so the visible-when-bound
    # composition is balanced (rather than centered on the bleed panel).
    trim_center_x = FRONT_CENTER_X
    if src_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * src_aspect
        draw_x = trim_center_x - draw_w / 2
        draw_y = target_y
    else:
        draw_w = target_w
        draw_h = target_w / src_aspect
        draw_x = trim_center_x - draw_w / 2
        draw_y = target_y + (target_h - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(target_x, target_y, target_w, target_h)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()


def draw_front_cover_text(c):
    cx = FRONT_CENTER_X
    c.setFillColor(TEXT_WHITE)
    c.setFont("EBGaramond", 34)
    c.drawCentredString(cx, TRIM_TOP - 1.4 * inch, "Change the Mind,")
    c.drawCentredString(cx, TRIM_TOP - 2.0 * inch, "Change the Man")

    c.setFont("EBGaramond", 20)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.6 * inch, "Paul Hainline")

    c.setFont("EBGaramond-Italic", 14)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.1 * inch,
                        "Inspired by the teaching of Freddie Anderson")


def draw_spine(c):
    """0.335" spine — small fonts, title + author only."""
    c.saveState()
    c.translate(SPINE_CENTER_X, BLEED_CENTER_Y)
    c.rotate(270)
    c.setFillColor(TEXT_WHITE)
    c.setFont("EBGaramond", 7)
    c.drawCentredString(0, 2, "Change the Mind, Change the Man")
    c.setFont("EBGaramond", 6)
    c.drawCentredString(0, -6, "Paul Hainline")
    c.restoreState()


def draw_back_cover(c):
    safe_left  = BACK_TRIM_LEFT  + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2
    c.setFillColor(TEXT_WHITE)

    paragraphs = [
        ("EBGaramond", 13, "Someone you love is destroying himself."),
        ("EBGaramond", 13, "Or maybe that someone is you."),
        (None, 0, ""),
        ("EBGaramond", 10,
            "You have tried everything — the conversations, the "
            "ultimatums, the promises, the programs. You have lain awake "
            "at night asking questions that have no answers and praying "
            "prayers that feel like they hit the ceiling. You have watched "
            "addiction take a person you knew and replace him with someone "
            "you don’t recognize. And you have wondered, more times "
            "than you can count, whether there is a way through this — "
            "or whether “through” is just a word people say when "
            "they don’t know what else to offer."),
        (None, 0, ""),
        ("EBGaramond", 10,
            "This book was not written by a counselor, a clinician, or a "
            "theologian. It was written by a man who was introduced to "
            "drugs at thirteen, arrested at seventeen and sentenced to life "
            "in prison, and who spent the next three decades watching "
            "addiction destroy everything it touched — including "
            "himself."),
        (None, 0, ""),
        ("EBGaramond", 10,
            "It is a straightforward examination of what God’s Word "
            "says about how the mind turns away from God, how it turns "
            "back, and why the substance was never the real problem. The "
            "gaze was."),
        (None, 0, ""),
        ("EBGaramond-Italic", 9,
            "Scripture quotations from the New American Standard Bible®."),
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
    if not TEMPLATE_FILE.exists():
        raise SystemExit(f"ERROR: IngramSpark template not found at {TEMPLATE_FILE}")

    print('Generating IngramSpark PAPERBACK cover for "Change the Mind, Change the Man"...')
    print(f'  Document size: {DOC_W_IN}" x {DOC_H_IN}" (per IngramSpark template)')
    print(f'  Bleed area:    {BLEED_AREA_W_IN}" x {BLEED_AREA_H_IN}" '
          f'at ({BLEED_LEFT_IN}", {BLEED_BOTTOM_IN}")')
    print(f'  Spine:         {SPINE_W_IN}" ({PAGE_COUNT} pages, creme)')

    # --- Step 1: render artwork onto a 15x12 canvas, drawing only inside
    # the bleed area so the template marks survive the merge.
    c = canvas.Canvas(str(ARTWORK_TMP), pagesize=(DOC_W, DOC_H))
    c.setTitle("Change the Mind, Change the Man — IngramSpark Paperback Cover")

    draw_background(c)
    draw_front_cover_image(c)
    draw_front_cover_text(c)
    draw_spine(c)
    draw_back_cover(c)

    # ISBN barcode: bottom-right of back panel, on the spine side.
    barcode_panel_w = 1.75 * inch
    draw_isbn_barcode(
        c,
        ISBN_PAPERBACK,
        x_left=BACK_TRIM_RIGHT - SAFETY - barcode_panel_w,
        y_bottom=TRIM_BOTTOM + SAFETY,
        panel_w=barcode_panel_w,
    )
    c.save()
    print(f"\n  Artwork rendered: {ARTWORK_TMP.name}")

    # --- Step 2: merge artwork onto the IngramSpark template.
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
