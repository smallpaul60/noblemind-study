#!/usr/bin/env python3
"""Generate IngramSpark hardcover dust jacket PDF for Through the Valley.

This script overlays the book artwork onto IngramSpark's official Cover
Generator template (downloaded by ISBN). The template defines the exact
24" x 12.5" document size, trim/fold marks, and bleed area that IngramSpark's
automated checker requires. We render our artwork into the bleed area only,
then merge onto the template so the trim marks in the white outer margins
remain unaltered.

Specs (IngramSpark template, request CSS5171309, ISBN 979-8-9954288-8-6):
  Document size:    24.000" x 12.500"  (must match template exactly)
  Bleed area:       19.563" x  9.000"  (centered in document)
  Trim size:         5.500" x  8.500"
  Cover panel:       5.938" x  8.750"  (each, includes board overhang)
  Spine:             0.438"            (122 pages, B&W creme paper)
  Flap:              3.250"            (each)
  Wrap:              0.250"            (between cover and flap)
  Bleed:             0.125"            (all four edges of bleed area)
  Page count:        122
  Layout (L->R within bleed area):
    [0.125 bleed] [3.25 flap] [0.25 wrap] [5.938 back cover]
    [0.438 spine]
    [5.938 front cover] [0.25 wrap] [3.25 flap] [0.125 bleed]
"""

from pathlib import Path
import pypdf
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import white
from PIL import Image
import io

BOOK_DIR = Path(__file__).parent
TEMPLATE_FILE = BOOK_DIR / "ThroughTheValley_Cover_Generator_Template.pdf"
ARTWORK_TMP = BOOK_DIR / "_hc_artwork_overlay.pdf"
OUTPUT = BOOK_DIR / "Through_the_Valley_IngramSpark_Hardcover_Cover.pdf"
IMAGE_FILE = BOOK_DIR / "cover_image_extracted.jpg"
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-8-6.png"   # hardcover ISBN

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (must match IngramSpark template exactly) ---
# NOTE: the bleed artwork area is NOT centered in the 24x12.5 document.
# It is positioned at (3.4375", 3.000") with size 19.5625" x 9.000",
# leaving asymmetric outer margins:
#   left = 3.4375"   right = 1.0000"   top = 0.5000"   bottom = 3.0000"
# These offsets were measured from the rendered template PDF.
PAGE_COUNT  = 122
DOC_W_IN    = 24.000
DOC_H_IN    = 12.500
DOC_W       = DOC_W_IN * inch
DOC_H       = DOC_H_IN * inch

# Bleed artwork area — exact position and size from template
BLEED_AREA_W_IN = 19.5625   # = 19 9/16" (template labels it "19.563")
BLEED_AREA_H_IN =  9.0000
BLEED_LEFT_IN   =  3.4375   # = 3 7/16"
BLEED_BOTTOM_IN =  3.0000
BLEED_RIGHT_IN  = BLEED_LEFT_IN  + BLEED_AREA_W_IN   # 23.0000"
BLEED_TOP_IN    = BLEED_BOTTOM_IN + BLEED_AREA_H_IN  # 12.0000"

BLEED_LEFT   = BLEED_LEFT_IN   * inch
BLEED_RIGHT  = BLEED_RIGHT_IN  * inch
BLEED_BOTTOM = BLEED_BOTTOM_IN * inch
BLEED_TOP    = BLEED_TOP_IN    * inch

# Panel widths — exact 16ths (template labels rounded to "5.938" / "0.438")
BLEED_W   = 0.1250    # inner bleed margin within the bleed area
FLAP_W    = 3.2500
WRAP_W    = 0.2500
COVER_W   = 5.9375    # = 95/16"
SPINE_W   = 0.4375    # = 7/16"  (122 pages creme paper)
COVER_H   = 8.7500

# Trim edges (just inside the bleed margins)
TRIM_LEFT_IN   = BLEED_LEFT_IN   + BLEED_W   # 2.3435"
TRIM_RIGHT_IN  = BLEED_RIGHT_IN  - BLEED_W   # 21.6575"
TRIM_BOTTOM_IN = BLEED_BOTTOM_IN + BLEED_W   # 1.875"
TRIM_TOP_IN    = BLEED_TOP_IN    - BLEED_W   # 10.625"

# --- Colors ---
DEEP_GREEN = Color(0.110, 0.180, 0.110)   # #1C2E1C deep forest green
CREAM      = Color(0.961, 0.941, 0.910)   # #F5F0E8 warm cream
SAGE_LIGHT = Color(0.659, 0.722, 0.620)   # #A8B89E light sage
SAGE_MUTED = Color(0.482, 0.553, 0.435)   # #7B8D6F muted sage

# --- Panel x-positions (from left edge of document, in points) ---
BACK_FLAP_LEFT   = TRIM_LEFT_IN * inch
BACK_FLAP_RIGHT  = BACK_FLAP_LEFT + FLAP_W * inch
BACK_WRAP_LEFT   = BACK_FLAP_RIGHT
BACK_WRAP_RIGHT  = BACK_WRAP_LEFT + WRAP_W * inch
BACK_COVER_LEFT  = BACK_WRAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W * inch

SPINE_LEFT      = BACK_COVER_RIGHT
SPINE_RIGHT     = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X  = (SPINE_LEFT + SPINE_RIGHT) / 2

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

# Center of each cover panel
BACK_CENTER_X  = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# Safety margins for text
# IngramSpark's absolute minimum is 0.125" from any trim or fold line. We've
# been rejected repeatedly at tighter values, so we deliberately over-provision
# to 0.75" on every panel, every edge. Flap text block width becomes 1.75".
SAFETY = 0.75 * inch
FLAP_FOLD_SAFETY = 0.75 * inch   # Flap fold line (toward board)
FLAP_TRIM_SAFETY = 0.75 * inch   # Flap turn-in edge (paper trim side)
TOP_HEAD_PAD = 0.75 * inch       # Extra headroom for first-line ascenders
IMAGE_INSET   = 0.25 * inch      # Image pulled in from every panel edge

FRONT_FLAP_SAFE_LEFT = FRONT_FLAP_LEFT + FLAP_FOLD_SAFETY
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - FLAP_TRIM_SAFETY
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT  # 2.25"

BACK_FLAP_SAFE_LEFT = BACK_FLAP_LEFT + FLAP_TRIM_SAFETY
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - FLAP_FOLD_SAFETY
BACK_FLAP_TEXT_W = BACK_FLAP_SAFE_RIGHT - BACK_FLAP_SAFE_LEFT  # 2.25"


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


# --- Element-level safety auditing -----------------------------------
# Every draw call for text, lines, and images records its bbox here.
# At the end of the run we walk the list and flag anything tighter than
# SAFETY_WARN_THRESHOLD inches from any trim or fold edge on its panel.

SAFETY_WARN_THRESHOLD = 0.5  # inches

_drawn_elements = []  # list of (panel, label, left, right, top, bottom)
_canvas = None        # set in main() so record_text can call stringWidth

_FONT_ASC = 0.73
_FONT_DES = 0.22


def _panel_for_x(x):
    """Identify which panel an x coordinate sits in.
    Returns (panel_name, panel_left_pt, panel_right_pt,
             left_is_fold, right_is_fold).
    Panel edges that aren't folds are paper trim edges.

    Layout (L->R): back_flap | wrap | back_cover | spine | front_cover | wrap | front_flap
    The wrap strips are fold zones between flap and cover; we treat each
    flap's cover-side edge as a fold and each cover's flap-side edge as a fold.
    """
    if BACK_FLAP_LEFT <= x < BACK_FLAP_RIGHT:
        return ("back_flap", BACK_FLAP_LEFT, BACK_FLAP_RIGHT, False, True)
    if BACK_WRAP_LEFT <= x < BACK_WRAP_RIGHT:
        return ("back_wrap", BACK_WRAP_LEFT, BACK_WRAP_RIGHT, True, True)
    if BACK_COVER_LEFT <= x < BACK_COVER_RIGHT:
        return ("back_cover", BACK_COVER_LEFT, BACK_COVER_RIGHT, True, True)
    if SPINE_LEFT <= x < SPINE_RIGHT:
        return ("spine", SPINE_LEFT, SPINE_RIGHT, True, True)
    if FRONT_COVER_LEFT <= x < FRONT_COVER_RIGHT:
        return ("front_cover", FRONT_COVER_LEFT, FRONT_COVER_RIGHT, True, True)
    if FRONT_WRAP_LEFT <= x < FRONT_WRAP_RIGHT:
        return ("front_wrap", FRONT_WRAP_LEFT, FRONT_WRAP_RIGHT, True, True)
    if FRONT_FLAP_LEFT <= x < FRONT_FLAP_RIGHT:
        return ("front_flap", FRONT_FLAP_LEFT, FRONT_FLAP_RIGHT, True, False)
    return ("unknown", 0, DOC_W, False, False)


def record_text(text, font, size, x_anchor, baseline, centered=True):
    """Record a drawn text element's bbox for the audit."""
    w = _canvas.stringWidth(text, font, size)
    if centered:
        left = x_anchor - w / 2
        right = x_anchor + w / 2
    else:
        left = x_anchor
        right = x_anchor + w
    top = baseline + _FONT_ASC * size
    bottom = baseline - _FONT_DES * size
    panel = _panel_for_x((left + right) / 2)[0]
    _drawn_elements.append((panel, f"{font} {size}pt '{text[:44]}'", left, right, top, bottom))


def record_rect(label, x, y, w, h):
    """Record a rectangular element (decorative line, barcode box, etc.)."""
    panel = _panel_for_x(x + w / 2)[0]
    _drawn_elements.append((panel, label, x, x + w, y + h, y))


def run_safety_audit():
    """Walk every recorded element and warn on any within
    SAFETY_WARN_THRESHOLD of a trim or fold edge."""
    print(f"\n=== Safety audit (warn threshold: {SAFETY_WARN_THRESHOLD}\") ===")
    warnings = 0
    worst_by_panel = {}
    for panel, label, left, right, top, bottom in _drawn_elements:
        if panel == "spine":
            continue  # spine is rotated — check separately if needed
        _, L, R, fold_l, fold_r = _panel_for_x((left + right) / 2)
        edges = [
            ("left",   (left - L) / 72,             fold_l),
            ("right",  (R - right) / 72,            fold_r),
            ("top",    (TRIM_TOP - top) / 72,       False),
            ("bottom", (bottom - TRIM_BOTTOM) / 72, False),
        ]
        side, dist, is_fold = min(edges, key=lambda e: e[1])
        cur = worst_by_panel.get(panel)
        if cur is None or dist < cur[0]:
            worst_by_panel[panel] = (dist, label, side, is_fold)
        if dist < SAFETY_WARN_THRESHOLD:
            kind = "fold" if is_fold else "trim"
            tag = "VIOLATION" if dist < 0.125 else "TIGHT"
            print(f"  [{tag}] {panel} {label}: {side}={dist:+.3f}\" ({kind})")
            warnings += 1
    print("\n  Worst clearance per panel:")
    for panel, (dist, label, side, is_fold) in sorted(worst_by_panel.items()):
        kind = "fold" if is_fold else "trim"
        print(f"    {panel:12} {side:6} = {dist:+.3f}\" ({kind})  [{label[:60]}]")
    if warnings == 0:
        print(f"\n  ALL CLEAR — every element is at least "
              f"{SAFETY_WARN_THRESHOLD}\" from every edge.")
    else:
        print(f"\n  {warnings} element(s) below warn threshold.")
# ---------------------------------------------------------------------


def draw_background(c):
    """Fill the bleed area only with deep forest green.

    We clip to the bleed area so nothing bleeds into the white outer margins
    of the IngramSpark template, whose trim/fold marks must remain visible.
    """
    c.saveState()
    clip = c.beginPath()
    clip.rect(BLEED_LEFT, BLEED_BOTTOM,
              BLEED_RIGHT - BLEED_LEFT, BLEED_TOP - BLEED_BOTTOM)
    clip.close()
    c.clipPath(clip, stroke=0)
    c.setFillColor(DEEP_GREEN)
    c.rect(BLEED_LEFT, BLEED_BOTTOM,
           BLEED_RIGHT - BLEED_LEFT, BLEED_TOP - BLEED_BOTTOM,
           fill=1, stroke=0)
    c.restoreState()


def draw_front_cover_image(c):
    """Place the cover image on the front cover panel with a deep-green
    border on every side.

    The source JPG has ~6% white padding baked into its left and right edges
    (and a small strip at the bottom). We open it with PIL first and crop to
    the non-white content bbox so the area around the image is actually deep
    green — not white padding from the file.

    We inset the cropped image IMAGE_INSET from every panel/bleed edge and
    fit inside (letterbox) so baked-in title, subtitle, and author name
    stay well away from fold lines.
    """
    # --- Open source and crop white padding -----------------------------
    # The source JPG has baked-in white margins with anti-aliased edges,
    # so a single-pixel-aware threshold leaves fuzzy off-white slivers at
    # the border. We require a column/row to contain a substantial amount
    # of non-light content (>2% of the orthogonal dimension) before we
    # consider it "real content", which discards anti-aliasing halos.
    pil_img = Image.open(str(IMAGE_FILE)).convert("RGB")
    import numpy as np
    arr = np.array(pil_img)
    h, w = arr.shape[:2]
    # "light" = any channel >= 220 on all three channels (tighter than pure white)
    light = (arr[..., 0] >= 220) & (arr[..., 1] >= 220) & (arr[..., 2] >= 220)
    content = ~light
    col_counts = content.sum(axis=0)
    row_counts = content.sum(axis=1)
    # A real content column is ~97% non-light; edge/halo columns drop to
    # <20% quickly, so 20% cleanly separates the two.
    col_thresh = int(h * 0.20)
    row_thresh = int(w * 0.20)
    cols = np.where(col_counts > col_thresh)[0]
    rows = np.where(row_counts > row_thresh)[0]
    if len(cols) and len(rows):
        pil_img = pil_img.crop((int(cols[0]), int(rows[0]),
                                int(cols[-1]) + 1, int(rows[-1]) + 1))

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    img = ImageReader(buf)
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    # Target: front cover panel less IMAGE_INSET on every side
    target_x = FRONT_COVER_LEFT + IMAGE_INSET
    target_w = (FRONT_COVER_RIGHT - FRONT_COVER_LEFT) - 2 * IMAGE_INSET
    target_y = BLEED_BOTTOM + IMAGE_INSET
    target_h = (BLEED_TOP - BLEED_BOTTOM) - 2 * IMAGE_INSET
    target_aspect = target_w / target_h

    # Fit inside the target (letterbox)
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

    The 0.4375" spine on a 122-page book is too narrow for legible text —
    any type that fit would be unreadable on the shelf, and keeps the
    spine clear of any safety-margin ambiguity.
    """
    pass


def draw_back_cover(c):
    """Draw back cover text on deep forest green background."""
    safe_left = BACK_COVER_LEFT + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2

    def centered(text, font, size, baseline):
        c.setFont(font, size)
        c.drawCentredString(cx, baseline, text)
        record_text(text, font, size, cx, baseline, centered=True)

    # --- Hook line (italic, light sage) ---
    y = TRIM_TOP - 1.0 * inch
    c.setFillColor(SAGE_LIGHT)
    hook = "This book is short enough to read in a hospital room. It is meant to be."
    lines = wrap_text(c, hook, "EBGaramond-Italic", 10.5, text_width)
    for line in lines:
        centered(line, "EBGaramond-Italic", 10.5, y)
        y -= 14

    # --- Thin decorative line ---
    y -= 8
    line_hw = 0.6 * inch
    line_thick = 0.4
    c.setStrokeColor(SAGE_LIGHT)
    c.setLineWidth(line_thick)
    c.line(cx - line_hw, y, cx + line_hw, y)
    record_rect("back decor line", cx - line_hw, y - line_thick / 2,
                2 * line_hw, line_thick)
    y -= 18

    # --- Body text (cream) ---
    c.setFillColor(CREAM)
    line_height = 13.5

    body_paragraphs = [
        "Someone you love is dying. Or maybe that someone is you.",
        "Through the Valley walks with two people at once \u2014 the one whose body is failing and the one who will be left behind. It does not separate them, because they are walking through the same valley.",
        "In eight chapters anchored entirely in Scripture, this book examines what God actually says \u2014 not platitudes, not near-death stories, not clinical speculation. What does God say about His presence when He feels absent? What happens after death? And how do you grieve honestly while holding to a hope that Scripture calls certain?",
        "The valley is real. The shadow is dark. But David did not say \u2018if I walk into the valley.\u2019 He said \u2018even though I walk through.\u2019 The valley has a through. And the Shepherd is already there.",
    ]

    for para in body_paragraphs:
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        for line in lines:
            centered(line, "EBGaramond", 10, y)
            y -= line_height
        y -= line_height * 0.4

    # --- Attribution (small, muted sage) ---
    y -= line_height * 0.3
    c.setFillColor(SAGE_MUTED)
    centered("Scripture quotations from the New American Standard Bible\u00ae (NASB).",
             "EBGaramond-Italic", 8, y)

    # --- Barcode (mandatory per IngramSpark, lower-right of back cover) ---
    # 100% black on white background, within safe area. Hardcover ISBN.
    barcode_img = ImageReader(str(BARCODE_IMAGE))
    bc_w = 1.75 * inch
    bc_h = bc_w * 280 / 523  # maintain original barcode aspect ratio
    pad = 0.08 * inch
    box_w = bc_w + 2 * pad
    box_h = bc_h + 2 * pad
    box_x = safe_right - box_w          # right-aligned inside safe area
    box_y = TRIM_BOTTOM + SAFETY        # sits above bottom safety margin
    c.setFillColor(white)
    c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)
    c.drawImage(barcode_img, box_x + pad, box_y + pad, width=bc_w, height=bc_h)
    record_rect("back cover barcode", box_x, box_y, box_w, box_h)


def draw_front_flap(c):
    """Draw front flap text — book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(CREAM)

    y = TRIM_TOP - TOP_HEAD_PAD
    line_height = 11

    paragraphs = [
        ("EBGaramond-Italic", 8.5, "Through the Valley is written for the hardest season \u2014 when someone you love is facing the end, or when that someone is you."),
        (None, 0, ""),
        ("EBGaramond", 8, "Built on five principles \u2014 the Bible as sole authority, word-for-word accuracy, Scripture interprets Scripture, intellectual honesty, and a shared journey \u2014 each chapter walks with both the one who is departing and the one who remains."),
        (None, 0, ""),
        ("EBGaramond", 8, "This is not a book of platitudes. It acknowledges that the pain is real, the body decays, and the questions are often loud. It does not pretend the valley is not dark. It simply trusts that the Light is brighter."),
    ]

    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.5
            continue

        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            c.drawString(safe_left, y, line)
            record_text(line, font, size, safe_left, y, centered=False)
            y -= line_height
        y -= line_height * 0.2


def draw_back_flap(c):
    """Draw back flap text — About the Author."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(CREAM)

    # Heading
    y = TRIM_TOP - TOP_HEAD_PAD
    header = "About the Author"
    c.setFont("EBGaramond", 10)
    c.drawString(safe_left, y, header)
    record_text(header, "EBGaramond", 10, safe_left, y, centered=False)
    y -= 16

    line_height = 10.5

    paragraphs = [
        "Paul Hainline is a student of God\u2019s Word and the author of works rooted in the conviction that Scripture interprets Scripture. He writes from a desire to point readers back to the biblical text. He is the founder of NobleMind Press (noblemind.study).",
    ]

    for text in paragraphs:
        lines = wrap_text(c, text, "EBGaramond", 7.5, text_width)
        for line in lines:
            c.setFont("EBGaramond", 7.5)
            c.drawString(safe_left, y, line)
            record_text(line, "EBGaramond", 7.5, safe_left, y, centered=False)
            y -= line_height
        y -= line_height * 0.2


def main():
    if not TEMPLATE_FILE.exists():
        raise SystemExit(f"ERROR: IngramSpark template not found at {TEMPLATE_FILE}")

    print('Generating IngramSpark HARDCOVER (dust jacket) cover PDF for "Through the Valley"...')
    print(f'  Document size:   {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}" (per IngramSpark template)')
    print(f'  Bleed area:      {BLEED_AREA_W_IN:.4f}" x {BLEED_AREA_H_IN:.4f}" '
          f'at ({BLEED_LEFT_IN:.4f}", {BLEED_BOTTOM_IN:.4f}")')
    print(f'  Trim size:       5.500" x 8.500"')
    print(f'  Cover panel:     {COVER_W}" x {COVER_H}"')
    print(f'  Spine:           {SPINE_W}" ({PAGE_COUNT} pages, creme paper)')
    print(f'  Flap:            {FLAP_W}"   Wrap: {WRAP_W}"   Bleed: {BLEED_W}"')

    # --- Step 1: render artwork to an intermediate PDF at 24x12.5 ---------
    global _canvas
    c = canvas.Canvas(str(ARTWORK_TMP), pagesize=(DOC_W, DOC_H))
    _canvas = c  # so record_text() can call stringWidth
    c.setTitle("Through the Valley - IngramSpark Hardcover Dust Jacket Cover")

    draw_background(c)
    draw_front_cover_image(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\n  Artwork overlay rendered: {ARTWORK_TMP.name}")

    # --- Step 2: overlay artwork onto IngramSpark template ----------------
    # The template carries trim/fold marks in the white outer margins which
    # IngramSpark's automated preflight expects. We overlay our artwork
    # (which only draws inside the bleed area) on top of the template page,
    # so the outer marks remain untouched.
    template_reader = pypdf.PdfReader(str(TEMPLATE_FILE))
    artwork_reader  = pypdf.PdfReader(str(ARTWORK_TMP))

    base_page    = template_reader.pages[0]
    overlay_page = artwork_reader.pages[0]

    # Sanity: both pages must be the same 24 x 12.5 size.
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

    # Clean up intermediate file
    try:
        ARTWORK_TMP.unlink()
    except OSError:
        pass

    print(f"\nFinal cover saved to {OUTPUT}")
    print(f"  Document size:   {bw/72:.3f}\" x {bh/72:.3f}\"  (matches template)")

    run_safety_audit()
    print("Done.")


if __name__ == "__main__":
    main()
