#!/usr/bin/env python3
"""Generate IngramSpark hardcover dust jacket PDF for Strength and Dignity.

This script overlays book artwork onto IngramSpark's official Cover Generator
template (downloaded by ISBN). The template defines the exact 24" x 12.5"
document size, trim/fold marks, and bleed area that IngramSpark's automated
checker requires. Our artwork is drawn into the bleed area only, then merged
onto the template so the outer-margin marks remain unaltered.

Specs (IngramSpark template, ISBN 979-8-9954288-3-1):
  Document size:    24.000" x 12.500"
  Bleed area:       19.625" x  9.000"  at (3.375", 3.000")
  Trim size:         5.500" x  8.500"
  Cover panel:       5.938" x  8.750"  (each)
  Spine:             0.500"            (158 pages, B&W creme paper)
  Flap:              3.250"            (each)
  Wrap:              0.250"            (between cover and flap)
  Bleed:             0.125"            (all four edges of bleed area)
  Page count:        158
"""

from pathlib import Path
import pypdf
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
TEMPLATE_FILE = BOOK_DIR / "StregthAndDignity_Cover_Generator_Template.pdf"  # sic (as saved)
ARTWORK_TMP = BOOK_DIR / "_hc_artwork_overlay.pdf"
OUTPUT = BOOK_DIR / "Strength_and_Dignity_IngramSpark_Hardcover_Cover.pdf"
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-3-1.png"   # hardcover ISBN

# Register EB Garamond fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (must match IngramSpark template exactly) ---
# The bleed artwork area is NOT centered. It is positioned toward the upper
# right of the 24x12.5 document, leaving room for template labels/marks in
# the outer margins.
PAGE_COUNT  = 158
DOC_W_IN    = 24.000
DOC_H_IN    = 12.500
DOC_W       = DOC_W_IN * inch
DOC_H       = DOC_H_IN * inch

# Bleed artwork area — exact position and size from measured template
BLEED_AREA_W_IN = 19.6250   # = 19 5/8"  (template labels this as "19.625")
BLEED_AREA_H_IN =  9.0000
BLEED_LEFT_IN   =  3.3750   # = 3 3/8"
BLEED_BOTTOM_IN =  3.0000
BLEED_RIGHT_IN  = BLEED_LEFT_IN  + BLEED_AREA_W_IN    # 23.0000"
BLEED_TOP_IN    = BLEED_BOTTOM_IN + BLEED_AREA_H_IN   # 12.0000"

BLEED_LEFT   = BLEED_LEFT_IN   * inch
BLEED_RIGHT  = BLEED_RIGHT_IN  * inch
BLEED_BOTTOM = BLEED_BOTTOM_IN * inch
BLEED_TOP    = BLEED_TOP_IN    * inch

# Panel widths (from template — exact halves/eighths)
BLEED_W   = 0.1250
FLAP_W    = 3.2500
WRAP_W    = 0.2500
COVER_W   = 5.9375    # = 95/16"
SPINE_W   = 0.5000    # = 1/2"  (158 pages creme)
COVER_H   = 8.7500
TRIM_W    = 5.5
TRIM_H    = 8.5

# Trim edges (just inside the bleed margins)
TRIM_LEFT_IN   = BLEED_LEFT_IN   + BLEED_W    # 3.5000"
TRIM_RIGHT_IN  = BLEED_RIGHT_IN  - BLEED_W    # 22.8750"
TRIM_BOTTOM_IN = BLEED_BOTTOM_IN + BLEED_W    # 3.1250"
TRIM_TOP_IN    = BLEED_TOP_IN    - BLEED_W    # 11.8750"

# --- Colors ---
DEEP_ROSE = Color(0.235, 0.082, 0.145)    # #3C1525 deep burgundy-rose
CREAM = Color(0.957, 0.922, 0.855)        # #F4EBDA warm cream
GOLD_ACCENT = Color(0.769, 0.663, 0.306)  # #C4A94E warm gold

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

# Centers
BACK_CENTER_X  = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2

# Safety margins
# IngramSpark's absolute minimum is 0.125" from any trim or fold line, but
# the automated checker has rejected prior submissions at ~0.25", so we
# aim for 0.5" on every panel, every edge. Text width ends up the same
# (2.25" on flaps, 4.625" on boards) — we just stop hugging the fold.
SAFETY = 0.5 * inch             # Board cover panels (front / back)
FRONT_SAFETY = 0.5 * inch       # Front cover
FLAP_FOLD_SAFETY = 0.5 * inch   # Flap fold line (toward board)
FLAP_TRIM_SAFETY = 0.5 * inch   # Flap turn-in edge (paper trim side)
TOP_HEAD_PAD = 0.625 * inch     # Extra headroom for ascenders on first line

# Flap text safe areas — symmetric 0.5"/0.5" (previously 0.25"/0.75" which
# put the fold side right at IngramSpark's minimum).
FRONT_FLAP_SAFE_LEFT = FRONT_FLAP_LEFT + FLAP_FOLD_SAFETY
FRONT_FLAP_SAFE_RIGHT = FRONT_FLAP_RIGHT - FLAP_TRIM_SAFETY
FRONT_FLAP_TEXT_W = FRONT_FLAP_SAFE_RIGHT - FRONT_FLAP_SAFE_LEFT

BACK_FLAP_SAFE_LEFT = BACK_FLAP_LEFT + FLAP_TRIM_SAFETY
BACK_FLAP_SAFE_RIGHT = BACK_FLAP_RIGHT - FLAP_FOLD_SAFETY
BACK_FLAP_TEXT_W = BACK_FLAP_SAFE_RIGHT - BACK_FLAP_SAFE_LEFT


def wrap_text(c, text, font_name, font_size, max_width):
    """Wrap text to fit within max_width."""
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
# Every draw call for text, lines, and images records its bbox to this
# list. At the end of the run we walk the list and check each element
# against the panel edges, flagging anything under the target clearance.

# Target clearance — we flag anything tighter than this.
# IngramSpark's hard minimum is 0.125"; we use 0.375" as the warning
# threshold so we always have cushion when their checker runs.
SAFETY_WARN_THRESHOLD = 0.375  # inches

_drawn_elements = []  # list of (panel, label, left, right, top, bottom)

def _panel_for_x(x):
    """Identify which panel an x coordinate sits in.
    Returns (panel_name, panel_left_pt, panel_right_pt,
             left_is_fold, right_is_fold).

    Layout: back_flap | wrap | back_cover | spine | front_cover | wrap | front_flap
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


# Font ascent/descent fractions (EB Garamond is fairly typical)
_FONT_ASC = 0.73
_FONT_DES = 0.22

def record_text(text, font, size, cx, baseline, centered=True, left_anchored_x=None):
    """Measure text and record its bbox for the audit."""
    w = _canvas.stringWidth(text, font, size)
    if centered:
        left = cx - w / 2
        right = cx + w / 2
    else:
        left = left_anchored_x
        right = left + w
    asc = _FONT_ASC * size
    des = _FONT_DES * size
    top = baseline + asc
    bottom = baseline - des
    # Use the centroid to pick the panel
    mid = (left + right) / 2
    panel = _panel_for_x(mid)[0]
    _drawn_elements.append((panel, f"{font} {size}pt '{text[:44]}'", left, right, top, bottom))

def record_rect(label, x, y, w, h):
    """Record a rectangular element (line, barcode, etc.)."""
    mid = x + w / 2
    panel = _panel_for_x(mid)[0]
    _drawn_elements.append((panel, label, x, x + w, y + h, y))

_canvas = None  # set in main() so record_text can call stringWidth


def run_safety_audit():
    """Walk every recorded element and warn on any within
    SAFETY_WARN_THRESHOLD of a trim or fold edge."""
    print("\n=== Safety audit (warn threshold: "
          f"{SAFETY_WARN_THRESHOLD}\") ===")
    warnings = 0
    worst_by_panel = {}
    for panel, label, left, right, top, bottom in _drawn_elements:
        if panel == "spine":
            continue  # spine handled separately — text is rotated
        info = _panel_for_x((left + right) / 2)
        _, L, R, fold_l, fold_r = info
        edges = [
            ("left",   (left - L) / 72,     fold_l),
            ("right",  (R - right) / 72,    fold_r),
            ("top",    (TRIM_TOP - top) / 72,       False),
            ("bottom", (bottom - TRIM_BOTTOM) / 72, False),
        ]
        side, dist, is_fold = min(edges, key=lambda e: e[1])
        worst = worst_by_panel.get(panel)
        if worst is None or dist < worst[0]:
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
        print("\n  ALL CLEAR — every element is at least "
              f"{SAFETY_WARN_THRESHOLD}\" from every edge.")
    else:
        print(f"\n  {warnings} element(s) below warn threshold.")
# ---------------------------------------------------------------------


def draw_background(c):
    """Fill the bleed area only with deep burgundy-rose.

    We clip to the bleed area so the IngramSpark template's trim/fold marks
    in the white outer margins remain visible after the merge.
    """
    c.saveState()
    clip = c.beginPath()
    clip.rect(BLEED_LEFT, BLEED_BOTTOM,
              BLEED_RIGHT - BLEED_LEFT, BLEED_TOP - BLEED_BOTTOM)
    clip.close()
    c.clipPath(clip, stroke=0)
    c.setFillColor(DEEP_ROSE)
    c.rect(BLEED_LEFT, BLEED_BOTTOM,
           BLEED_RIGHT - BLEED_LEFT, BLEED_TOP - BLEED_BOTTOM,
           fill=1, stroke=0)
    c.restoreState()


def draw_front_cover(c):
    """Draw front cover text."""
    cx = FRONT_CENTER_X
    line_w = 1.5 * inch
    line_thick = 0.5

    def deco(y):
        c.setStrokeColor(CREAM)
        c.setLineWidth(line_thick)
        c.line(cx - line_w / 2, y, cx + line_w / 2, y)
        record_rect("decor line", cx - line_w / 2, y - line_thick / 2,
                    line_w, line_thick)

    def centered(text, font, size, baseline):
        c.setFont(font, size)
        c.drawCentredString(cx, baseline, text)
        record_text(text, font, size, cx, baseline, centered=True)

    # Decorative line above title
    deco(BLEED_TOP - 2.0 * inch)

    # Series title
    c.setFillColor(CREAM)
    centered("YOUR NAME",        "EBGaramond", 28, BLEED_TOP - 2.65 * inch)
    centered("MEANS EVERYTHING", "EBGaramond", 28, BLEED_TOP - 3.1 * inch)

    # Decorative line between title and subtitle
    deco(BLEED_TOP - 3.45 * inch)

    # Volume subtitle
    centered("Strength and Dignity", "EBGaramond-Italic", 18, BLEED_TOP - 3.9 * inch)

    # Tagline
    centered("What the Bible Says to Young Women", "EBGaramond-Italic", 12, BLEED_TOP - 4.6 * inch)
    centered("About Character, Wisdom, and Faith", "EBGaramond-Italic", 12, BLEED_TOP - 4.85 * inch)

    # Decorative line above author
    deco(BLEED_TOP - 5.35 * inch)

    # Author name
    centered("Paul & Pam Hainline", "EBGaramond", 17, BLEED_TOP - 5.8 * inch)

    # Scripture near bottom
    quote_y = TRIM_BOTTOM + 1.3 * inch
    c.setStrokeColor(CREAM)
    c.line(cx - 0.3 * inch, quote_y + 0.35 * inch, cx + 0.3 * inch, quote_y + 0.35 * inch)
    record_rect("scripture decor line",
                cx - 0.3 * inch, quote_y + 0.35 * inch - line_thick / 2,
                0.6 * inch, line_thick)
    centered("\u201cStrength and dignity are her clothing,",
             "EBGaramond-Italic", 10.5, quote_y)
    centered("and she smiles at the future.\u201d",
             "EBGaramond-Italic", 10.5, quote_y - 0.2 * inch)
    centered("P R O V E R B S  3 1 : 2 5",
             "EBGaramond", 8.5, quote_y - 0.5 * inch)


def draw_spine(c):
    """Draw spine text. At 0.434" there's room for text."""
    c.saveState()
    c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
    c.rotate(270)

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 7)
    c.drawCentredString(0, 3, "YOUR NAME MEANS EVERYTHING: STRENGTH AND DIGNITY")
    c.setFont("EBGaramond", 6)
    c.drawCentredString(0, -5, "Paul & Pam Hainline")

    c.restoreState()


def draw_back_cover(c):
    """Draw back cover blurb."""
    safe_left = BACK_COVER_LEFT + SAFETY
    safe_right = BACK_COVER_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = (safe_left + safe_right) / 2
    ls = 16

    def centered(text, font, size, baseline):
        c.setFont(font, size)
        c.drawCentredString(cx, baseline, text)
        record_text(text, font, size, cx, baseline, centered=True)

    c.setFillColor(CREAM)

    # Opening
    y = BLEED_TOP - 1.8 * inch
    centered("Nobody told you this was coming.", "EBGaramond-Italic", 12, y)
    y -= ls * 1.5

    for line in [
        "One day you\u2019re watching the clock in a classroom.",
        "The next, the world steps back and says \u2014",
    ]:
        centered(line, "EBGaramond", 10.5, y)
        y -= ls
    centered("your turn.", "EBGaramond-Italic", 10.5, y)
    y -= ls * 1.3

    body_paragraphs = [
        "The decisions are real now. And the voices competing for your attention have never been louder.",
        "Your Name Means Everything: Strength and Dignity is a straight-talk guide rooted in Scripture for young women stepping into adulthood. Through thirteen chapters, it walks through the things that matter most \u2014 identity, character, purpose, relationships, work, money, and faith \u2014 not with opinions or platitudes, but with what God\u2019s Word actually says.",
        "From Ruth\u2019s loyalty to Rahab\u2019s courage to the Proverbs 31 woman who clothed herself in strength and dignity and smiled at the future \u2014 this book shows what it looks like to build a life and a name that will outlast you.",
    ]

    for para in body_paragraphs:
        wrapped = wrap_text(c, para, "EBGaramond", 10.5, text_width)
        for line in wrapped:
            centered(line, "EBGaramond", 10.5, y)
            y -= ls
        y -= ls * 0.5

    # Scripture
    centered("\u201cA good name is to be more desired than great wealth;",
             "EBGaramond-Italic", 10.5, y); y -= ls
    centered("favor is better than silver and gold.\u201d",
             "EBGaramond-Italic", 10.5, y); y -= ls
    centered("\u2014 Proverbs 22:1", "EBGaramond", 9.5, y)

    # Author at bottom left
    author_text = "P A U L  &  P A M  H A I N L I N E"
    author_baseline = TRIM_BOTTOM + SAFETY
    c.setFont("EBGaramond", 9)
    c.drawString(safe_left, author_baseline, author_text)
    record_text(author_text, "EBGaramond", 9, safe_left, author_baseline,
                centered=False, left_anchored_x=safe_left)

    # --- ISBN Barcode (bottom-right of back cover) ---
    # Keep the barcode inside the 0.5" safety box — the -0.15" nudge in
    # the previous revision pushed the bottom edge down to 0.35" from
    # trim, which was tighter than we want. Sit it flush with SAFETY.
    barcode_w = 2.0 * inch
    barcode_h = 1.2 * inch
    barcode_x = safe_right - barcode_w
    barcode_y = TRIM_BOTTOM + SAFETY

    c.setFillColor(white)
    c.rect(barcode_x, barcode_y, barcode_w, barcode_h, fill=1, stroke=0)
    record_rect("ISBN barcode box", barcode_x, barcode_y, barcode_w, barcode_h)

    barcode_img = str(BOOK_DIR / "barcode_978-8-9954288-3-1.png")
    c.drawImage(barcode_img, barcode_x + 0.1 * inch, barcode_y + 0.1 * inch,
                width=barcode_w - 0.2 * inch, height=barcode_h - 0.2 * inch,
                preserveAspectRatio=True, anchor='c')


def draw_front_flap(c):
    """Draw front flap text — book description."""
    safe_left = FRONT_FLAP_SAFE_LEFT
    text_width = FRONT_FLAP_TEXT_W

    c.setFillColor(CREAM)
    y = TRIM_TOP - TOP_HEAD_PAD
    line_height = 11

    paragraphs = [
        ("EBGaramond-Italic", 8.5,
         "Strength and Dignity is written for a young woman standing at the threshold of adulthood \u2014 facing real decisions with very little honest guidance rooted in God\u2019s Word."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "Through thirteen chapters built entirely on Scripture, Paul and Pam Hainline address the questions that will define a young woman\u2019s life: who she is, what she\u2019s worth, how she treats people, and how she builds something that lasts."),
        (None, 0, ""),
        ("EBGaramond", 8,
         "Not with opinions. Not with trends. With what God actually says \u2014 and the examples of women in Scripture who lived it."),
    ]

    for font, size, text in paragraphs:
        if font is None:
            y -= line_height * 0.5
            continue
        lines = wrap_text(c, text, font, size, text_width)
        for line in lines:
            c.setFont(font, size)
            c.drawString(safe_left, y, line)
            record_text(line, font, size, safe_left, y,
                        centered=False, left_anchored_x=safe_left)
            y -= line_height
        y -= line_height * 0.2


def draw_back_flap(c):
    """Draw back flap text — About the Authors."""
    safe_left = BACK_FLAP_SAFE_LEFT
    text_width = BACK_FLAP_TEXT_W

    c.setFillColor(CREAM)

    y = TRIM_TOP - TOP_HEAD_PAD
    header = "About the Authors"
    c.setFont("EBGaramond", 10)
    c.drawString(safe_left, y, header)
    record_text(header, "EBGaramond", 10, safe_left, y,
                centered=False, left_anchored_x=safe_left)
    y -= 16

    line_height = 10.5

    paragraphs = [
        "Paul and Pam Hainline are students of God\u2019s Word who write from the conviction that Scripture interprets Scripture. Their work is rooted in a desire to point readers back to the biblical text \u2014 not to opinions, traditions, or denominational systems. They are the founders of NobleMind Press (noblemind.study).",
    ]

    for text in paragraphs:
        lines = wrap_text(c, text, "EBGaramond", 7.5, text_width)
        for line in lines:
            c.setFont("EBGaramond", 7.5)
            c.drawString(safe_left, y, line)
            record_text(line, "EBGaramond", 7.5, safe_left, y,
                        centered=False, left_anchored_x=safe_left)
            y -= line_height
        y -= line_height * 0.2


def main():
    if not TEMPLATE_FILE.exists():
        raise SystemExit(f"ERROR: IngramSpark template not found at {TEMPLATE_FILE}")

    print('Generating IngramSpark HARDCOVER (dust jacket) cover PDF...')
    print(f'  Title: Your Name Means Everything: Strength and Dignity')
    print(f'  Document size:   {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}" (per IngramSpark template)')
    print(f'  Bleed area:      {BLEED_AREA_W_IN:.4f}" x {BLEED_AREA_H_IN:.4f}" '
          f'at ({BLEED_LEFT_IN:.4f}", {BLEED_BOTTOM_IN:.4f}")')
    print(f'  Trim size:       {TRIM_W}" x {TRIM_H}"')
    print(f'  Cover panel:     {COVER_W}" x {COVER_H}"')
    print(f'  Spine:           {SPINE_W}" ({PAGE_COUNT} pages, creme paper)')
    print(f'  Flap:            {FLAP_W}"   Wrap: {WRAP_W}"   Bleed: {BLEED_W}"')

    # --- Step 1: render artwork to an intermediate PDF at 24x12.5 ---------
    global _canvas
    c = canvas.Canvas(str(ARTWORK_TMP), pagesize=(DOC_W, DOC_H))
    _canvas = c  # so record_text() can call stringWidth
    c.setTitle("Your Name Means Everything: Strength and Dignity - IngramSpark Hardcover Dust Jacket")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\n  Artwork overlay rendered: {ARTWORK_TMP.name}")

    # --- Step 2: overlay artwork onto IngramSpark template ----------------
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
