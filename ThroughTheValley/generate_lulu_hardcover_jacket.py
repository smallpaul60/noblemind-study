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
IMAGE_FILE = BOOK_DIR / "new-cover-image-original.png"   # clean portrait, no baked text
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-8-6.png"   # hardcover ISBN

# Register fonts. EB Garamond for body, Great Vibes for the cover script title.
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))
pdfmetrics.registerFont(TTFont("GreatVibes", str(FONT_DIR / "GreatVibes-Regular.ttf")))

# --- Document dimensions (Lulu spec, confirmed by downloaded template 2026-05-07) ---
PAGE_COUNT = 120
DOC_W_IN = 19.250
DOC_H_IN = 9.250
DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# Panel widths (Lulu — 3.25" flaps, 5.75" covers; sums to exactly 19.25")
BLEED_W = 0.125
FLAP_W = 3.25
WRAP_W = 0.25
COVER_W = 5.75
SPINE_W = 0.50
COVER_H = 8.50
TURN_IN = 0.250          # space between bleed and visible cover area (top/bottom)

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

# --- Visible-when-bound area (fold-to-fold, includes wraps) ---
# Centering text/images to the bare COVER panel pushes content toward the
# spine because the wrap on the outer side adds visible width on the
# bound book. Use these visible spans instead.
BACK_VISIBLE_LEFT   = BACK_WRAP_LEFT       # back flap-cover fold
BACK_VISIBLE_RIGHT  = BACK_COVER_RIGHT     # spine fold (back side)
BACK_VISIBLE_CENTER = (BACK_VISIBLE_LEFT + BACK_VISIBLE_RIGHT) / 2

FRONT_VISIBLE_LEFT   = FRONT_COVER_LEFT    # spine fold (front side)
FRONT_VISIBLE_RIGHT  = FRONT_WRAP_RIGHT    # cover-flap fold (front)
FRONT_VISIBLE_CENTER = (FRONT_VISIBLE_LEFT + FRONT_VISIBLE_RIGHT) / 2

# --- Safety margins ---
# Standing rule (memory: feedback_cover_clearance_and_centering): give plenty
# of clearance on flaps and back-cover text. Vertical space is rarely the
# constraint — readability is.
BLURB_INSET = 1.0 * inch         # back-cover text column inset (each side)
FLAP_FOLD_SAFETY = 0.75 * inch   # flap fold line (toward board)
FLAP_TRIM_SAFETY = 0.75 * inch   # flap outer (turn-in) edge
SAFETY = 0.5 * inch              # generic safety (e.g. barcode placement)
TOP_HEAD_PAD = 0.75 * inch       # extra ascender headroom on first line

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
    """Fill visible front with the image, then overlay vector title,
    subtitle, and byline.

    Image: scaled to fill the visible front width exactly (6.0", from
    spine fold to cover-flap fold) and centered vertically. Any small
    aspect mismatch is absorbed by the top/bottom turn-in folds, which
    are hidden on the bound book.

    Text: all vector. Title in Great Vibes script (matches the original
    cover's title face), subtitle in EB Garamond italic, byline in EB
    Garamond small-caps letter-spaced. New byline reads "Paul & Pam
    Hainline" (replacing the prior PAUL HAINLINE that was rasterized
    into the previous cover image).
    """
    # Pre-crop the source so it matches the visible-front aspect
    # exactly (6.0"/9.25" = 0.649). Image fills the front panel
    # bleed-to-bleed vertically with no green slivers; the few percent
    # of pixels cropped from each side fall outside the focal area
    # (staff, path, sun).
    pil_img = Image.open(str(IMAGE_FILE)).convert("RGB")
    src_w, src_h = pil_img.size
    src_aspect = src_w / src_h

    target_x = FRONT_VISIBLE_LEFT
    target_w = FRONT_VISIBLE_RIGHT - FRONT_VISIBLE_LEFT   # 6.0" in points
    target_h = DOC_H                                       # 9.25" in points
    target_aspect = target_w / target_h                    # ~0.649

    if src_aspect > target_aspect:
        new_w = int(round(src_h * target_aspect))
        x0 = (src_w - new_w) // 2
        pil_img = pil_img.crop((x0, 0, x0 + new_w, src_h))
    elif src_aspect < target_aspect:
        new_h = int(round(src_w / target_aspect))
        y0 = (src_h - new_h) // 2
        pil_img = pil_img.crop((0, y0, src_w, y0 + new_h))

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    img = ImageReader(buf)
    c.drawImage(img, target_x, 0, width=target_w, height=target_h)

    # --- Vector text overlay ---
    cx = FRONT_VISIBLE_CENTER

    # Title in Great Vibes script. Two lines with enough vertical gap
    # between baselines to clear the script font's ascenders/descenders
    # so the lines no longer crowd into each other.
    c.setFillColor(DEEP_GREEN)
    c.setFont("GreatVibes", 60)
    c.drawCentredString(cx, TRIM_TOP - 0.85 * inch, "Through the")
    c.setFont("GreatVibes", 100)
    c.drawCentredString(cx, TRIM_TOP - 2.30 * inch, "Valley")

    # Subtitle, sitting clear of "Valley" descenders.
    c.setFont("EBGaramond-Italic", 17)
    c.drawCentredString(cx, TRIM_TOP - 3.05 * inch,
                        "What God Says When the Shadow Is Real")

    # Byline: EB Garamond all-caps with light letter spacing via the
    # text-object API (Canvas itself has no setCharSpace). Compute the
    # spaced width manually so we can center it.
    c.setFillColor(CREAM)
    byline_font = "EBGaramond"
    byline_size = 17
    char_space = 1.5
    byline_text = "PAUL & PAM HAINLINE"
    natural_w = c.stringWidth(byline_text, byline_font, byline_size)
    spaced_w = natural_w + char_space * (len(byline_text) - 1)
    byline_x = cx - spaced_w / 2
    byline_y = TRIM_BOTTOM + 0.55 * inch
    text_obj = c.beginText(byline_x, byline_y)
    text_obj.setFont(byline_font, byline_size)
    text_obj.setCharSpace(char_space)
    text_obj.textOut(byline_text)
    c.drawText(text_obj)


def draw_spine(c):
    """Spine left intentionally blank.

    Lulu's linen wrap carries the spine title via foil stamp on the linen
    itself (configured separately in the Lulu UI), not on the dust jacket.
    A printed spine on the jacket would compete with the foil stamp once
    the jacket is in place.
    """
    pass


def draw_back_cover(c):
    """Back cover: hook, body paragraphs, broadened dedication, attribution, barcode.

    Text column uses BLURB_INSET (1.0") off the visible-area edges (which
    include the back wrap on the outer side and run to the spine fold on
    the inner side). Centering uses the visible center, not the bare
    cover panel center, so content does not appear shifted toward the
    spine on the bound book.
    """
    safe_left = BACK_VISIBLE_LEFT + BLURB_INSET
    safe_right = BACK_VISIBLE_RIGHT - BLURB_INSET
    text_width = safe_right - safe_left
    cx = BACK_VISIBLE_CENTER

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
    # Barcode placement uses SAFETY (0.5"), independent of BLURB_INSET, so
    # widening the blurb column doesn't push the barcode away from its
    # conventional spine-side bottom-corner position.
    barcode_img = ImageReader(str(BARCODE_IMAGE))
    bc_w = 1.75 * inch
    bc_h = bc_w * 280 / 523                 # preserve barcode PNG aspect
    pad = 0.08 * inch
    box_w = bc_w + 2 * pad
    box_h = bc_h + 2 * pad
    box_x = BACK_VISIBLE_RIGHT - SAFETY - box_w
    box_y = TRIM_BOTTOM + SAFETY
    c.setFillColor(white)
    c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)
    c.drawImage(barcode_img, box_x + pad, box_y + pad, width=bc_w, height=bc_h)


def draw_front_flap(c):
    """Front flap: short book description, centered within the flap text column."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    safe_right = FRONT_FLAP_SAFE_RIGHT
    text_width = FRONT_FLAP_TEXT_W
    cx = (safe_left + safe_right) / 2

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
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.2


def draw_back_flap(c):
    """Back flap: About the Author (centered)."""
    safe_left = BACK_FLAP_SAFE_LEFT
    safe_right = BACK_FLAP_SAFE_RIGHT
    text_width = BACK_FLAP_TEXT_W
    cx = (safe_left + safe_right) / 2

    c.setFillColor(CREAM)

    y = TRIM_TOP - TOP_HEAD_PAD
    header = "About the Author"
    c.setFont("EBGaramond", 10)
    c.drawCentredString(cx, y, header)
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
            c.drawCentredString(cx, y, line)
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
