#!/usr/bin/env python3
"""Generate Lulu hardcover dust jacket PDF for Through the Valley.

Lulu's Hardcover Linen Wrap binding takes a separate printed dust jacket
that wraps over the linen-bound boards. Unlike IngramSpark, Lulu does NOT
require the artwork to be merged into a 24"x12.5" template — the upload
is a flat artwork file at the exact dust jacket dimensions.

Specs (per Lulu Hardcover Linen Wrap, 5.5x8.5 digest, 116-page interior,
60# cream uncoated, ISBN 979-8-9954288-8-6):
  Document size:    19.250" x  9.250"
  Cover panel:       5.250" x  8.250"   (each — smaller than page trim)
  Spine:             0.500"             (116 pages, cream paper, per Lulu template)
  Flap:              3.750"             (each)
  Wrap:              0.250"             (cover-to-flap fold)
  Bleed:             0.125"             (all four edges)
  Top/bottom turn-in: 0.375"             (between bleed and visible cover area)

  Layout (L->R):
    [0.125 bleed] [3.75 flap] [0.25 wrap] [5.25 back cover]
    [0.5 spine]
    [5.25 front cover] [0.25 wrap] [3.75 flap] [0.125 bleed]
"""

import io
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import Color, white
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Through_the_Valley_Lulu_Hardcover_Jacket.pdf"
IMAGE_FILE = BOOK_DIR / "cover_image_extracted.jpg"
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-8-6.png"   # hardcover ISBN

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (Lulu spec) ---
PAGE_COUNT = 116
DOC_W_IN = 19.250
DOC_H_IN = 9.250
DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# Panel widths (Lulu)
BLEED_W = 0.125
FLAP_W = 3.75
WRAP_W = 0.25
COVER_W = 5.25
SPINE_W = 0.50
COVER_H = 8.25
TURN_IN = 0.375          # space between bleed and visible cover area (top/bottom)

# --- Colors (match IngramSpark version exactly so both editions read the same) ---
DEEP_GREEN = Color(0.110, 0.180, 0.110)   # #1C2E1C deep forest green
CREAM      = Color(0.961, 0.941, 0.910)   # #F5F0E8 warm cream
SAGE_LIGHT = Color(0.659, 0.722, 0.620)   # #A8B89E light sage
SAGE_MUTED = Color(0.482, 0.553, 0.435)   # #7B8D6F muted sage

# --- Panel x-positions (in points, from left of doc) ---
def _x(inches): return inches * inch

BACK_FLAP_LEFT   = _x(BLEED_W)
BACK_FLAP_RIGHT  = BACK_FLAP_LEFT + _x(FLAP_W)
BACK_WRAP_LEFT   = BACK_FLAP_RIGHT
BACK_WRAP_RIGHT  = BACK_WRAP_LEFT + _x(WRAP_W)
BACK_COVER_LEFT  = BACK_WRAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + _x(COVER_W)

SPINE_LEFT       = BACK_COVER_RIGHT
SPINE_RIGHT      = SPINE_LEFT + _x(SPINE_W)
SPINE_CENTER_X   = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT  = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + _x(COVER_W)
FRONT_WRAP_LEFT   = FRONT_COVER_RIGHT
FRONT_WRAP_RIGHT  = FRONT_WRAP_LEFT + _x(WRAP_W)
FRONT_FLAP_LEFT   = FRONT_WRAP_RIGHT
FRONT_FLAP_RIGHT  = FRONT_FLAP_LEFT + _x(FLAP_W)

# Vertical: visible cover area sits inside bleed + turn-in
TRIM_BOTTOM = _x(BLEED_W + TURN_IN)              # 0.5"  from bottom of doc
TRIM_TOP    = DOC_H - _x(BLEED_W + TURN_IN)      # 0.5"  from top of doc
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

# Centers
BACK_CENTER_X  = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# --- Safety margins ---
SAFETY = 0.5 * inch              # text safety from any cover trim edge
FLAP_FOLD_SAFETY = 0.5 * inch    # flap fold line (toward board)
FLAP_TRIM_SAFETY = 0.5 * inch    # flap outer (turn-in) edge
TOP_HEAD_PAD = 0.625 * inch      # extra ascender headroom on first line
IMAGE_INSET = 0.125 * inch       # cover image inset from panel edges

FRONT_FLAP_SAFE_LEFT  = FRONT_FLAP_LEFT + FLAP_FOLD_SAFETY
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - FLAP_TRIM_SAFETY
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT

BACK_FLAP_SAFE_LEFT  = BACK_FLAP_LEFT + FLAP_TRIM_SAFETY
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - FLAP_FOLD_SAFETY
BACK_FLAP_TEXT_W = BACK_FLAP_SAFE_RIGHT - BACK_FLAP_SAFE_LEFT


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
    """Fill entire document with deep forest green."""
    c.setFillColor(DEEP_GREEN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Place the cover image centered on the front cover panel.

    The source JPG has white padding baked into its margins; we crop the
    real content bbox before placing so that deep green surrounds the
    image instead of leaving white slivers.
    """
    pil_img = Image.open(str(IMAGE_FILE)).convert("RGB")
    import numpy as np
    arr = np.array(pil_img)
    h, w = arr.shape[:2]
    light = (arr[..., 0] >= 220) & (arr[..., 1] >= 220) & (arr[..., 2] >= 220)
    content = ~light
    col_thresh = int(h * 0.20)
    row_thresh = int(w * 0.20)
    cols = np.where(content.sum(axis=0) > col_thresh)[0]
    rows = np.where(content.sum(axis=1) > row_thresh)[0]
    if len(cols) and len(rows):
        pil_img = pil_img.crop((int(cols[0]), int(rows[0]),
                                int(cols[-1]) + 1, int(rows[-1]) + 1))

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    img = ImageReader(buf)
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    # Target: visible front cover area, less IMAGE_INSET on each side
    target_x = FRONT_COVER_LEFT + IMAGE_INSET
    target_w = (FRONT_COVER_RIGHT - FRONT_COVER_LEFT) - 2 * IMAGE_INSET
    target_y = TRIM_BOTTOM + IMAGE_INSET
    target_h = (TRIM_TOP - TRIM_BOTTOM) - 2 * IMAGE_INSET
    target_aspect = target_w / target_h

    if img_aspect > target_aspect:
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = target_x
        draw_y = target_y + (target_h - draw_h) / 2
    else:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = target_x + (target_w - draw_w) / 2
        draw_y = target_y

    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)


def draw_spine(c):
    """Spine left intentionally blank.

    Lulu's linen wrap carries the spine title via foil stamp on the linen
    itself (configured separately in the Lulu UI), not on the dust jacket.
    A printed spine on the jacket would compete with the foil stamp once
    the jacket is in place.
    """
    pass


def draw_back_cover(c):
    """Back cover: hook, body paragraphs, broadened dedication, attribution, barcode."""
    safe_left = BACK_COVER_LEFT + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    def centered(text, font, size, baseline):
        c.setFont(font, size)
        c.drawCentredString(cx, baseline, text)

    # --- Hook line (italic, light sage) ---
    y = TRIM_TOP - 0.7 * inch
    c.setFillColor(SAGE_LIGHT)
    hook = "This book is short enough to read in a hospital room. It is meant to be."
    for line in wrap_text(c, hook, "EBGaramond-Italic", 10.5, text_width):
        centered(line, "EBGaramond-Italic", 10.5, y)
        y -= 14

    # --- Thin decorative line ---
    y -= 8
    line_hw = 0.6 * inch
    c.setStrokeColor(SAGE_LIGHT)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 18

    # --- Body text (cream) ---
    c.setFillColor(CREAM)
    line_height = 13.5

    body_paragraphs = [
        "Someone you love is dying. Or maybe that someone is you.",
        "Through the Valley walks with two people at once — the one whose body is failing and the one who will be left behind. It does not separate them, because they are walking through the same valley.",
        "In eight chapters anchored entirely in Scripture, this book examines what God actually says — not platitudes, not near-death stories, not clinical speculation. What does God say about His presence when He feels absent? What happens after death? And how do you grieve honestly while holding to a hope that Scripture calls certain?",
        "The valley is real. The shadow is dark. But David did not say ‘if I walk into the valley.’ He said ‘even though I walk through.’ The valley has a through. And the Shepherd is already there.",
    ]
    for para in body_paragraphs:
        for line in wrap_text(c, para, "EBGaramond", 10, text_width):
            centered(line, "EBGaramond", 10, y)
            y -= line_height
        y -= line_height * 0.4

    # --- Broadened dedication (italic, sage, just above the attribution) ---
    y -= line_height * 0.2
    c.setFillColor(SAGE_LIGHT)
    dedication_lines = [
        "To everyone walking through this valley —",
        "the one whose body is failing,",
        "and the one sitting at the bedside.",
    ]
    for line in dedication_lines:
        centered(line, "EBGaramond-Italic", 9.5, y)
        y -= 12

    # --- Scripture attribution (small, muted sage) ---
    y -= line_height * 0.4
    c.setFillColor(SAGE_MUTED)
    centered("Scripture quotations from the New American Standard Bible® (NASB).",
             "EBGaramond-Italic", 8, y)

    # --- ISBN barcode (mandatory; bottom-right of back cover, on white panel) ---
    barcode_img = ImageReader(str(BARCODE_IMAGE))
    bc_w = 1.75 * inch
    bc_h = bc_w * 280 / 523                 # preserve barcode PNG aspect
    pad = 0.08 * inch
    box_w = bc_w + 2 * pad
    box_h = bc_h + 2 * pad
    box_x = safe_right - box_w
    box_y = TRIM_BOTTOM + SAFETY
    c.setFillColor(white)
    c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)
    c.drawImage(barcode_img, box_x + pad, box_y + pad, width=bc_w, height=bc_h)


def draw_front_flap(c):
    """Front flap: short book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(CREAM)
    y = TRIM_TOP - TOP_HEAD_PAD
    line_height = 11

    paragraphs = [
        ("EBGaramond-Italic", 8.5,
         "Through the Valley is written for the hardest season — when someone you love is facing the end, or when that someone is you."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "Built on five principles — the Bible as sole authority, word-for-word accuracy, Scripture interprets Scripture, intellectual honesty, and a shared journey — each chapter walks with both the one who is departing and the one who remains."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "This is not a book of platitudes. It acknowledges that the pain is real, the body decays, and the questions are often loud. It does not pretend the valley is not dark. It simply trusts that the Light is brighter."),
    ]

    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.5
            continue
        for line in wrap_text(c, text, font, size, text_width):
            c.setFont(font, size)
            c.drawString(safe_left, y, line)
            y -= line_height
        y -= line_height * 0.2


def draw_back_flap(c):
    """Back flap: About the Author (Berean framing per the standing wording)."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(CREAM)

    y = TRIM_TOP - TOP_HEAD_PAD
    header = "About the Author"
    c.setFont("EBGaramond", 10)
    c.drawString(safe_left, y, header)
    y -= 16

    line_height = 10.5

    paragraphs = [
        "Paul Hainline writes using the Berean approach of “examining the Scriptures daily to see whether these things were so” (Acts 17:11), and letting Scripture interpret Scripture. He is the author of multiple books on Bible study, evangelism, and Christian living, and writes with his wife Pam on books for teenagers in the Your Name Means Everything series.",
        "",
        "All of his books are available as free PDF and EPUB downloads at noblemind.study, alongside the Noble Mind Study Tool — a free, offline-capable Bible study application built around the same Berean methodology.",
    ]

    for text in paragraphs:
        if not text:
            y -= line_height * 0.5
            continue
        for line in wrap_text(c, text, "EBGaramond", 7.5, text_width):
            c.setFont("EBGaramond", 7.5)
            c.drawString(safe_left, y, line)
            y -= line_height
        y -= line_height * 0.2


def main():
    print("Generating Lulu hardcover dust jacket for Through the Valley...")
    print(f"  Document size:  {DOC_W_IN:.3f}\" x {DOC_H_IN:.3f}\"")
    print(f"  Cover panel:    {COVER_W}\" x {COVER_H}\"  (each)")
    print(f"  Spine:          {SPINE_W}\"  ({PAGE_COUNT} pages, cream paper)")
    print(f"  Flap:           {FLAP_W}\"   Wrap: {WRAP_W}\"   Bleed: {BLEED_W}\"")
    print()

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Through the Valley — Lulu Hardcover Dust Jacket")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"Saved: {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
