#!/usr/bin/env python3
"""Generate IngramSpark hardcover DUST JACKET for Change the Mind, Change the Man.

IngramSpark template specs (from IngramSpark-hardback-dust-jacket.pdf,
Lightning Source request CSS5209581, ISBN 979-8-9954288-5-5):
  Document size:    24.000" x 12.500"     (must match template exactly)
  Bleed area:       19.625" x 9.000"      positioned at (3.375", 3.000")
                                          (asymmetric: left=3.375, right=1.000,
                                           top=0.500, bottom=3.000)
  Trim per cover:   5.500" x 8.500"
  Cover panel bleed: 5.938" x 8.750"      each (incl. board overhang/bleed)
  Spine width:      0.500"                (144 pages, creme paper, B&W)
  Flap:             3.250" each
  Wrap:             0.250" between cover and flap
  Bleed within bleed area: 0.125"
  Page count:       144

Layout left-to-right within the bleed area:
  [bleed 0.125][back flap 3.25][wrap 0.25][back cover 5.938]
  [spine 0.50]
  [front cover 5.938][wrap 0.25][front flap 3.25][bleed 0.125]
  Sum: 0.125 + 3.25 + 0.25 + 5.9375 + 0.5 + 5.9375 + 0.25 + 3.25 + 0.125 = 19.625

The template carries IngramSpark's trim/fold marks in its outer white
margins. We render artwork only within the bleed area and overlay it
onto the template via pypdf.merge_page so those marks survive.

Design mirrors the Lulu hardcover dust jacket (near-black background,
white EB Garamond typography, desert-valley sunset on the front, full
back-cover blurb, front-flap teaser, back-flap author bio) so both
editions read as the same book.
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

TEMPLATE_FILE  = BOOK_DIR / "IngramSpark-hardback-dust-jacket.pdf"
ARTWORK_TMP    = BOOK_DIR / "_ingram_hc_artwork.pdf"
OUTPUT         = BOOK_DIR / "ChangeTheMind_ChangeTheMan_IngramSpark_Hardcover_Jacket.pdf"
IMAGE_FILE     = BOOK_DIR / "desert_valley_cover_1725x2775.png"
ISBN_HARDCOVER = "979-8-9954288-5-5"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (must match IngramSpark template exactly) ---
PAGE_COUNT = 144
DOC_W_IN   = 24.000
DOC_H_IN   = 12.500
DOC_W      = DOC_W_IN * inch
DOC_H      = DOC_H_IN * inch

# Bleed artwork area — exact position and size measured from the template
BLEED_AREA_W_IN = 19.625
BLEED_AREA_H_IN =  9.000
BLEED_LEFT_IN   =  3.375
BLEED_BOTTOM_IN =  3.000
BLEED_RIGHT_IN  = BLEED_LEFT_IN + BLEED_AREA_W_IN     # 23.000
BLEED_TOP_IN    = BLEED_BOTTOM_IN + BLEED_AREA_H_IN   # 12.000

BLEED_LEFT   = BLEED_LEFT_IN   * inch
BLEED_RIGHT  = BLEED_RIGHT_IN  * inch
BLEED_BOTTOM = BLEED_BOTTOM_IN * inch
BLEED_TOP    = BLEED_TOP_IN    * inch

# Panel widths (exact 16ths)
BLEED_W = 0.1250    # bleed inset within bleed area
FLAP_W  = 3.2500
WRAP_W  = 0.2500
COVER_W = 5.9375    # = 95/16"
SPINE_W = 0.5000
COVER_H = 8.7500

# Trim edges (just inside the bleed margins of the bleed area)
TRIM_LEFT_IN   = BLEED_LEFT_IN   + BLEED_W   # 3.500
TRIM_RIGHT_IN  = BLEED_RIGHT_IN  - BLEED_W   # 22.875
TRIM_BOTTOM_IN = BLEED_BOTTOM_IN + BLEED_W   # 3.125
TRIM_TOP_IN    = BLEED_TOP_IN    - BLEED_W   # 11.875

# --- Panel x-positions (from left edge of document, in points) ---
BACK_FLAP_LEFT   = TRIM_LEFT_IN * inch
BACK_FLAP_RIGHT  = BACK_FLAP_LEFT + FLAP_W * inch
BACK_WRAP_LEFT   = BACK_FLAP_RIGHT
BACK_WRAP_RIGHT  = BACK_WRAP_LEFT + WRAP_W * inch
BACK_COVER_LEFT  = BACK_WRAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W * inch

SPINE_LEFT     = BACK_COVER_RIGHT
SPINE_RIGHT    = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT  = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W * inch
FRONT_WRAP_LEFT   = FRONT_COVER_RIGHT
FRONT_WRAP_RIGHT  = FRONT_WRAP_LEFT + WRAP_W * inch
FRONT_FLAP_LEFT   = FRONT_WRAP_RIGHT
FRONT_FLAP_RIGHT  = FRONT_FLAP_LEFT + FLAP_W * inch

# Vertical
TRIM_TOP       = TRIM_TOP_IN    * inch
TRIM_BOTTOM    = TRIM_BOTTOM_IN * inch
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

BACK_CENTER_X  = (BACK_COVER_LEFT  + BACK_COVER_RIGHT)  / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# --- Colors (matches Lulu CTM cover palette) ---
DARK_BG    = Color(0.05, 0.05, 0.05)
TEXT_WHITE = Color(1, 1, 1)
SOFT_GREY  = Color(0.78, 0.76, 0.72)

# Safety: TTV's IngramSpark hardcover uses 0.75" everywhere because
# IngramSpark preflight has rejected tighter values. Hold the same.
SAFETY = 0.75 * inch
FLAP_FOLD_SAFETY = 0.75 * inch
FLAP_TRIM_SAFETY = 0.75 * inch

FRONT_FLAP_SAFE_LEFT  = FRONT_FLAP_LEFT  + FLAP_FOLD_SAFETY
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - FLAP_TRIM_SAFETY
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT

BACK_FLAP_SAFE_LEFT  = BACK_FLAP_LEFT  + FLAP_TRIM_SAFETY
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - FLAP_FOLD_SAFETY
BACK_FLAP_TEXT_W = BACK_FLAP_SAFE_RIGHT - BACK_FLAP_SAFE_LEFT


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
    """Desert valley image filling the front cover panel."""
    img = ImageReader(str(IMAGE_FILE))
    src_w, src_h = img.getSize()
    src_aspect = src_w / src_h

    target_x = FRONT_COVER_LEFT
    target_w = COVER_W * inch
    target_y = BLEED_BOTTOM
    target_h = BLEED_AREA_H_IN * inch
    target_aspect = target_w / target_h

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

    c.setFont("EBGaramond", 36)
    c.drawCentredString(cx, TRIM_TOP - 1.4 * inch, "Change the Mind,")
    c.drawCentredString(cx, TRIM_TOP - 2.0 * inch, "Change the Man")

    c.setFont("EBGaramond", 22)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.7 * inch, "Paul Hainline")

    c.setFont("EBGaramond-Italic", 14)
    c.drawCentredString(cx, TRIM_BOTTOM + 1.15 * inch,
                        "Inspired by the teaching of Freddie Anderson")


def draw_spine(c):
    """0.500" spine — wider than the paperback, so we can run a full
    title + author + small imprint vertical."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(TEXT_WHITE)
    c.setFont("EBGaramond", 14)
    c.drawCentredString(0, -4, "Change the Mind, Change the Man")

    # Author near the head of the spine
    spine_half = (TRIM_TOP - TRIM_BOTTOM) / 2  # in rotated x' axis
    c.setFont("EBGaramond", 10)
    c.drawCentredString(-spine_half + 1.0 * inch, -3, "PAUL HAINLINE")

    c.restoreState()


def draw_back_cover(c):
    """Back cover blurb — text from BACK COVER section of dust jacket."""
    safe_left  = BACK_COVER_LEFT  + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X
    c.setFillColor(TEXT_WHITE)

    paragraphs = [
        ("EBGaramond", 14, "Someone you love is destroying himself."),
        ("EBGaramond", 14, "Or maybe that someone is you."),
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
            "back, and why the substance was never the real problem. "
            "The gaze was."),
        (None, 0, ""),
        ("EBGaramond-Italic", 9,
            "Scripture quotations from the New American Standard Bible®."),
    ]

    y = TRIM_TOP - 1.1 * inch
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


def draw_front_flap(c):
    """Front flap: teaser / pull quote from FRONT FLAP section."""
    cx = (FRONT_FLAP_SAFE_LEFT + FRONT_FLAP_SAFE_RIGHT) / 2
    text_width = FRONT_FLAP_TEXT_W
    c.setFillColor(TEXT_WHITE)

    paragraphs = [
        ("EBGaramond-Italic", 10,
            "Freddie Anderson, the preacher who shaped the author’s "
            "approach to Scripture, used to say: if you change a person’s "
            "mind, you change everything about them. If you don’t change "
            "their mind, you don’t change anything."),
        (None, 0, ""),
        ("EBGaramond", 10, "That is the argument of this book."),
        (None, 0, ""),
        ("EBGaramond", 9,
            "Change the Mind, Change the Man traces two movements that "
            "mirror the actual experience of addiction and recovery. The "
            "first five chapters follow the descent — the crisis, the "
            "progression, the guilt, the hidden prisons, and the agonizing "
            "decisions families are forced to make. The second five "
            "chapters follow the return — the biblical mechanism of "
            "change, genuine repentance, forgiveness, the long daily road "
            "of recovery, and the gospel invitation for anyone who "
            "reaches the end and realizes they need the foundation it "
            "describes."),
        (None, 0, ""),
        ("EBGaramond", 9,
            "This is not a twelve-step program. It is not a clinical "
            "treatment guide. It is a careful, honest walk through "
            "Scripture — with the Greek and Hebrew examined where they "
            "illuminate meaning — applied directly to the reality of "
            "addiction by a man who has lived every chapter of it."),
        (None, 0, ""),
        ("EBGaramond-Italic", 9,
            "Whether you are the one struggling, a family member carrying "
            "the weight, or a friend searching for answers — this book "
            "speaks to you. Not to one and then the other. To all of you "
            "at once."),
    ]

    y = TRIM_TOP - 0.95 * inch
    line_height = 12
    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.5
            continue
        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.3


def draw_back_flap(c):
    """Back flap: About the Author."""
    cx = (BACK_FLAP_SAFE_LEFT + BACK_FLAP_SAFE_RIGHT) / 2
    text_width = BACK_FLAP_TEXT_W
    c.setFillColor(TEXT_WHITE)

    # Heading
    c.setFont("EBGaramond-Italic", 13)
    y = TRIM_TOP - 0.95 * inch
    c.drawCentredString(cx, y, "About the Author")
    y -= 16

    # Thin rule
    rule_hw = 0.5 * inch
    c.setStrokeColor(SOFT_GREY)
    c.setLineWidth(0.4)
    c.line(cx - rule_hw, y, cx + rule_hw, y)
    y -= 18

    paragraphs = [
        ("EBGaramond", 9,
            "Paul was introduced to drugs at the age of thirteen. At "
            "seventeen, he was arrested for robbery and murder and "
            "sentenced to life in prison. He served thirty-three years "
            "before parole was granted."),
        (None, 0, ""),
        ("EBGaramond", 9,
            "During those years, he witnessed the full cycle of addiction "
            "— men who walked out of prison determined to go straight "
            "and fell within weeks, and men who walked out with no "
            "intention of changing at all. He tried self-help books, the "
            "wisdom of man, and spent years trying to convince himself "
            "that God was not real. None of it filled the void."),
        (None, 0, ""),
        ("EBGaramond", 9,
            "It was the teaching of Freddie Anderson — a preacher whose "
            "method was always “Let’s see what the Bible says” — and "
            "the daily discipline of being in God’s Word that finally "
            "changed everything. Not the circumstances. Not the "
            "environment. The mind."),
        (None, 0, ""),
        ("EBGaramond", 9,
            "Paul obeyed the gospel, was baptized into Christ, and the "
            "man who walked into that prison at seventeen became a "
            "different man entirely. He is now sixty-five years old and "
            "the author of One Day Closer to Home and Change the Mind, "
            "Change the Man."),
        (None, 0, ""),
        ("EBGaramond-Italic", 9,
            "He writes not from theory, not from a safe distance, but "
            "from the road itself."),
    ]

    line_height = 12
    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.5
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

    print('Generating IngramSpark HARDCOVER (dust jacket) for "Change the Mind, Change the Man"...')
    print(f'  Document size: {DOC_W_IN}" x {DOC_H_IN}" (per IngramSpark template)')
    print(f'  Bleed area:    {BLEED_AREA_W_IN}" x {BLEED_AREA_H_IN}" '
          f'at ({BLEED_LEFT_IN}", {BLEED_BOTTOM_IN}")')
    print(f'  Cover panel:   {COVER_W}" x {COVER_H}"')
    print(f'  Spine:         {SPINE_W}" ({PAGE_COUNT} pages, creme)')
    print(f'  Flap:          {FLAP_W}"   Wrap: {WRAP_W}"   Bleed: {BLEED_W}"')

    c = canvas.Canvas(str(ARTWORK_TMP), pagesize=(DOC_W, DOC_H))
    c.setTitle("Change the Mind, Change the Man — IngramSpark Hardcover Jacket")

    draw_background(c)
    draw_front_cover_image(c)
    draw_front_cover_text(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    # ISBN barcode — bottom-right of back panel
    barcode_panel_w = 1.85 * inch
    draw_isbn_barcode(
        c,
        ISBN_HARDCOVER,
        x_left=BACK_COVER_RIGHT - SAFETY - barcode_panel_w,
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
    print(f"\nJacket saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
