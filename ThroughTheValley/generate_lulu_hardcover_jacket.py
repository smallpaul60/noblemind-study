#!/usr/bin/env python3
"""Generate Lulu hardcover dust jacket for Through the Valley.

Lulu specs (from the dust-jacket-cover-template.pdf downloaded for this
title):
  Document size:    19.25" x 9.25"
  Spine width:      0.5"
  Front/back flap:  3.25" x 9.25" each
  Flap fold width:  0.25" (between cover panel and flap)

Layout (left to right):
  [3.25 back flap][0.25 fold][5.875 back cover][0.5 spine]
  [5.875 front cover][0.25 fold][3.25 front flap]
  Sum: 3.25 + 0.25 + 5.875 + 0.5 + 5.875 + 0.25 + 3.25 = 19.25 in.

Design:
  - Whole jacket fills with deep green #1C2E1C.
  - Front cover image inset 0.2" inside the front panel, leaving a thin
    dark-green frame.
  - Title in EB Garamond Italic, two lines ("Through the" / "Valley"),
    set over the misty sky portion of the image.
  - Subtitle "What God Says When the Shadow Is Real" in upright italic
    serif below the title.
  - Byline "PAUL & PAM HAINLINE" in spaced caps near the bottom of the
    front image.
  - Back cover: Psalm 23:4 pull, dedication, NobleMind imprint, ISBN
    barcode lower-right.  0.75" inset each side.
  - Front flap: book description.  Back flap: author bio.
    0.25" inset each side on flaps.
"""

import sys
from pathlib import Path

# Side-effect import: registers Standard 14 PDF font aliases (Helvetica,
# Times-Roman, etc.) to embedded Liberation* TTFs so Lulu doesn't reject
# the cover for unembedded fonts.
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import isbn_barcode  # noqa: F401

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Through_the_Valley_Lulu_Hardcover_Jacket.pdf"
COVER_IMAGE = BOOK_DIR / "new-cover-image-upscaled.png"
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-8-6.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions ---
DOC_W_IN = 19.25
DOC_H_IN = 9.25
SPINE_W_IN = 0.5
FLAP_W_IN = 3.25
FOLD_W_IN = 0.25
COVER_W_IN = (DOC_W_IN - 2 * FLAP_W_IN - 2 * FOLD_W_IN - SPINE_W_IN) / 2  # 5.875

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# --- Horizontal layout anchors (in pts) ---
BACK_FLAP_LEFT = 0
BACK_FLAP_RIGHT = FLAP_W_IN * inch
BACK_FOLD_LEFT = BACK_FLAP_RIGHT
BACK_FOLD_RIGHT = BACK_FOLD_LEFT + FOLD_W_IN * inch
BACK_COVER_LEFT = BACK_FOLD_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W_IN * inch
SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W_IN * inch
FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W_IN * inch
FRONT_FOLD_LEFT = FRONT_COVER_RIGHT
FRONT_FOLD_RIGHT = FRONT_FOLD_LEFT + FOLD_W_IN * inch
FRONT_FLAP_LEFT = FRONT_FOLD_RIGHT
FRONT_FLAP_RIGHT = DOC_W

BACK_CENTER_X = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

# True visible front-cover face when the jacket is wrapped. Per the Lulu
# template's "BOOK COVER SIZE" label this is 5.75" wide; the 5.875" panel
# carries an extra 0.125" of wrap on the outer (fold) side. The visible
# face is bounded by the spine right edge and the detected front fold
# line at x = 15.625". Image and front-cover typography center on this.
VISIBLE_FRONT_LEFT = SPINE_RIGHT
VISIBLE_FRONT_RIGHT = 15.625 * inch
VISIBLE_FRONT_CENTER = (VISIBLE_FRONT_LEFT + VISIBLE_FRONT_RIGHT) / 2

# --- Colors ---
DEEP_GREEN = Color(0.110, 0.180, 0.110)   # #1C2E1C base field
CREAM      = Color(0.961, 0.941, 0.910)   # #F5F0E8
GOLD       = Color(0.788, 0.659, 0.306)
GOLD_MUTED = Color(0.580, 0.475, 0.220)
DARK_INK   = Color(0.090, 0.130, 0.090)   # near-black green for title
SLATE      = Color(0.608, 0.580, 0.525)
WHITE      = Color(1, 1, 1)

# --- Padding ---
BACK_TEXT_INSET = 0.75 * inch     # back panel: 0.25" Lulu safety + 0.5" breathing
COVER_FRAME_IN = 0.2 * inch       # dark-green frame around front image

# Flap safe-text boundaries extracted directly from the Lulu dust-jacket
# template (lulu dust jacket-cover-template.pdf, blue safety lines). The
# safe area is asymmetric: ~0.75" inset from the outer flap edge (which
# wraps around to the inside of the board) and ~0.25" from the fold.
BACK_FLAP_SAFE_LEFT = 0.747 * inch
BACK_FLAP_SAFE_RIGHT = 2.996 * inch
FRONT_FLAP_SAFE_LEFT = 16.244 * inch
FRONT_FLAP_SAFE_RIGHT = 18.494 * inch
FLAP_INNER_PAD = 0.15 * inch      # breathing room inside the blue safe line


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
    """Fill the entire jacket with deep green."""
    c.setFillColor(DEEP_GREEN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Front panel: image inset with dark-green frame; title + subtitle +
    byline overlaid on the image. All content is centered on the
    visible-cover midpoint (between spine right edge and front fold)
    so the composition is balanced when the jacket is wrapped."""
    cx = VISIBLE_FRONT_CENTER

    img_x = VISIBLE_FRONT_LEFT + COVER_FRAME_IN
    img_y = COVER_FRAME_IN
    img_w = (VISIBLE_FRONT_RIGHT - VISIBLE_FRONT_LEFT) - 2 * COVER_FRAME_IN
    img_h = DOC_H - 2 * COVER_FRAME_IN

    # Scale-to-fill with center crop
    img = ImageReader(str(COVER_IMAGE))
    src_w, src_h = img.getSize()
    src_aspect = src_w / src_h
    target_aspect = img_w / img_h

    if src_aspect > target_aspect:
        draw_h = img_h
        draw_w = img_h * src_aspect
        draw_x = img_x + (img_w - draw_w) / 2
        draw_y = img_y
    else:
        draw_w = img_w
        draw_h = img_w / src_aspect
        draw_x = img_x
        draw_y = img_y + (img_h - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(img_x, img_y, img_w, img_h)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # Title — two-line italic serif at near-equal sizes so it reads as a
    # single unified title rather than a small-over-large pair.
    title_top_y = DOC_H - COVER_FRAME_IN - 1.0 * inch
    c.setFillColor(DARK_INK)
    c.setFont("EBGaramond-Italic", 46)
    c.drawCentredString(cx, title_top_y, "Through the")

    title_main_y = title_top_y - 0.7 * inch
    c.setFont("EBGaramond-Italic", 50)
    c.drawCentredString(cx, title_main_y, "Valley")

    rule_y = title_main_y - 0.4 * inch
    rule_hw = 0.55 * inch
    c.setStrokeColor(DARK_INK)
    c.setLineWidth(0.6)
    c.line(cx - rule_hw, rule_y, cx + rule_hw, rule_y)

    c.setFont("EBGaramond-Italic", 14.5)
    sub_y = rule_y - 0.3 * inch
    c.drawCentredString(cx, sub_y, "What God Says When the Shadow Is Real")

    # Soft dark gradient at the bottom of the front image so the byline
    # reads cleanly regardless of what part of the painted scene sits
    # under it (path vs. wildflowers vs. grass).
    c.saveState()
    grad_path = c.beginPath()
    grad_path.rect(img_x, img_y, img_w, img_h)
    grad_path.close()
    c.clipPath(grad_path, stroke=0)
    grad_h = 1.6 * inch
    bsteps = 240
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.04, 0.07, 0.04, alpha))
        y_band = grad_h * (1 - i / bsteps) + img_y
        h_band = grad_h / bsteps + 1
        c.rect(img_x, y_band - h_band, img_w, h_band, fill=1, stroke=0)
    c.restoreState()

    # Byline in cream over the dark-gradient footer
    byline_y = COVER_FRAME_IN + 0.55 * inch
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    c.drawCentredString(cx, byline_y, "P A U L  &  P A M   H A I N L I N E")


def draw_spine(c):
    """Vertical title only, centered on the 0.5" spine. Authors and
    imprint were dropped because they sat too close to the head/foot
    of the spine and were wrapping around onto the boards."""
    c.saveState()
    c.translate(SPINE_CENTER_X, DOC_H / 2)
    c.rotate(-90)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 18)
    c.drawCentredString(0, -6, "Through the Valley")

    c.restoreState()


def draw_back_cover(c):
    """Back panel: Psalm 23:4 pull, dedication, imprint, barcode."""
    cx = BACK_CENTER_X

    # Psalm 23:4 pull
    y = DOC_H - 1.4 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 13)
    psalm_lines = [
        "“Even though I walk through the valley",
        "of the shadow of death,",
        "I fear no evil, for You are with me…”",
    ]
    line_height = 19
    for line in psalm_lines:
        c.drawCentredString(cx, y, line)
        y -= line_height

    y -= 6
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond", 10)
    c.drawCentredString(cx, y, "— Psalm 23:4")
    y -= 22

    # Thin gold rule
    rule_hw = 0.7 * inch
    c.setStrokeColor(GOLD_MUTED)
    c.setLineWidth(0.5)
    c.line(cx - rule_hw, y, cx + rule_hw, y)
    y -= 28

    # Dedication
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, y, "To all those who are going")
    y -= 19
    c.drawCentredString(cx, y, "through the valley.")

    # Imprint — positioned well above the barcode area so the centered
    # mark doesn't collide with the lower-right barcode.
    mark_y = 2.5 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")

    # ISBN barcode in lower-right of back cover, on a white panel
    bc_w = 1.85 * inch
    bc_h = bc_w * 280 / 523  # preserve PNG aspect (523x280)
    pad = 0.08 * inch
    box_w = bc_w + 2 * pad
    box_h = bc_h + 2 * pad
    box_x = BACK_COVER_RIGHT - 0.5 * inch - box_w
    box_y = 0.5 * inch
    c.setFillColor(WHITE)
    c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)
    bc_img = ImageReader(str(BARCODE_IMAGE))
    c.drawImage(bc_img, box_x + pad, box_y + pad, width=bc_w, height=bc_h)


def draw_front_flap(c):
    """Book description / hook for the buyer."""
    safe_left = FRONT_FLAP_SAFE_LEFT + FLAP_INNER_PAD
    safe_right = FRONT_FLAP_SAFE_RIGHT - FLAP_INNER_PAD
    text_width = safe_right - safe_left
    flap_cx = (FRONT_FLAP_SAFE_LEFT + FRONT_FLAP_SAFE_RIGHT) / 2

    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 13)
    y = DOC_H - 0.9 * inch
    c.drawCentredString(flap_cx, y, "Through the Valley")
    y -= 20

    rule_hw = 0.45 * inch
    c.setStrokeColor(GOLD_MUTED)
    c.setLineWidth(0.4)
    c.line(flap_cx - rule_hw, y, flap_cx + rule_hw, y)
    y -= 18

    c.setFillColor(CREAM)
    line_height = 13
    paragraphs = [
        ("EBGaramond-Italic", 10,
            "Most books about grief are written for after.  But you’re "
            "not after.  You’re in it right now."),
        ("EBGaramond", 10,
            "Maybe your body is the one that is failing.  Maybe you’re "
            "the one sitting beside the bed, watching someone you love move "
            "toward the end of their life on this earth.  Either way, you "
            "know something most people around you do not fully understand "
            "— this valley is real, it is dark, and it does not care "
            "about your schedule or your prayers or your plans."),
        ("EBGaramond-Italic", 10,
            "This book was written for both of you.  To be read together, "
            "while you still can."),
        ("EBGaramond", 10,
            "There is no pretending here.  No platitudes.  No “just "
            "trust God and you’ll feel better.”  This is a book "
            "for the bedside.  For the chair beside the hospital bed.  For "
            "the morning after the diagnosis."),
        ("EBGaramond", 10,
            "Eight slow chapters drawn from Psalm 23, 2 Corinthians 4, Job "
            "42, Ecclesiastes 4, 1 Corinthians 2, and the prophets who knew "
            "suffering as well as anyone in the Bible.  No curriculum.  "
            "No five steps.  Only Scripture, slowly read, slowly applied, "
            "and the quiet promise that the same God who walked into Eden "
            "walks into every valley with His people."),
    ]
    for font, size, text in paragraphs:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.45


def draw_back_flap(c):
    """About the Authors."""
    safe_left = BACK_FLAP_SAFE_LEFT + FLAP_INNER_PAD
    safe_right = BACK_FLAP_SAFE_RIGHT - FLAP_INNER_PAD
    text_width = safe_right - safe_left
    flap_cx = (BACK_FLAP_SAFE_LEFT + BACK_FLAP_SAFE_RIGHT) / 2

    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 13)
    y = DOC_H - 0.9 * inch
    c.drawCentredString(flap_cx, y, "About the Authors")
    y -= 20

    rule_hw = 0.45 * inch
    c.setStrokeColor(GOLD_MUTED)
    c.setLineWidth(0.4)
    c.line(flap_cx - rule_hw, y, flap_cx + rule_hw, y)
    y -= 18

    c.setFillColor(CREAM)
    line_height = 13
    paragraphs = [
        ("EBGaramond", 10,
            "Paul Hainline writes using the Berean approach of "
            "“examining the Scriptures daily to see whether these "
            "things were so” (Acts 17:11), and letting Scripture "
            "interpret Scripture.  He is the author of multiple books on "
            "Bible study, evangelism, and Christian living, including "
            "From the Beginning, Change the Mind — Change the Man, "
            "The Character No One Could Invent, Why Do You Delay, and "
            "Can These Bones Live?"),
        ("EBGaramond", 10,
            "He writes with his wife Pam on books for teenagers, including "
            "Your Name Means Everything: A Good Name (for young men), and "
            "Your Name Means Everything: Strength and Dignity (for young "
            "ladies)."),
        ("EBGaramond-Italic", 10,
            "All of his books are available as free PDF and EPUB downloads "
            "at noblemind.study, alongside the Noble Mind Study Tool "
            "— a free, offline-capable Bible study application built "
            "around the same Berean methodology."),
    ]
    for font, size, text in paragraphs:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.45

    # Imprint at bottom of back flap
    mark_y = 0.85 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(flap_cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(flap_cx, mark_y - 12, "noblemind.study")


def main():
    print('Generating Lulu HARDCOVER JACKET PDF for "Through the Valley"...')
    print(f'  Document size:  {DOC_W_IN}" x {DOC_H_IN}"')
    print(f'  Spine:          {SPINE_W_IN}"')
    print(f'  Cover panel:    {COVER_W_IN}" x {DOC_H_IN}" each')
    print(f'  Flap:           {FLAP_W_IN}" x {DOC_H_IN}"   Fold: {FOLD_W_IN}"')
    print()
    print(f'  Panel x-positions (inches):')
    print(f'    back flap  : {BACK_FLAP_LEFT/inch:.3f} .. {BACK_FLAP_RIGHT/inch:.3f}')
    print(f'    back cover : {BACK_COVER_LEFT/inch:.3f} .. {BACK_COVER_RIGHT/inch:.3f}')
    print(f'    spine      : {SPINE_LEFT/inch:.3f} .. {SPINE_RIGHT/inch:.3f}')
    print(f'    front cover: {FRONT_COVER_LEFT/inch:.3f} .. {FRONT_COVER_RIGHT/inch:.3f}')
    print(f'    front flap : {FRONT_FLAP_LEFT/inch:.3f} .. {FRONT_FLAP_RIGHT/inch:.3f}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Through the Valley — Lulu Hardcover Jacket")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\nJacket saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
