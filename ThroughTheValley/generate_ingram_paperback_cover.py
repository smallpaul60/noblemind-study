#!/usr/bin/env python3
"""Generate IngramSpark paperback cover PDF for Through the Valley.

Uses the Strength and Dignity approach: background image on front cover,
all text drawn directly in ReportLab for pixel-perfect centering.

IngramSpark specs (5.5x8.5 perfect bound paperback, B&W white paper, 120 pages):
  Trim size: 5.5" x 8.5"
  Spine width: 120 x 0.002252 = 0.27024" ~ 0.27"
  Bleed: 0.125" on all outside edges (not on spine edges)
  Total document width: 0.125 + 5.5 + 0.27 + 5.5 + 0.125 = 11.52"
  Total document height: 0.125 + 8.5 + 0.125 = 8.75"
  Safety margin: 0.25" inside trim edges for front cover text (IngramSpark recommended)
  Safety margin: 0.5" inside trim edges for back cover text
"""

import io
import shutil
import subprocess
from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image
import numpy as np

BOOK_DIR = Path(__file__).parent
# ReportLab emits an unused /F1 Helvetica reference in the default page state
# (a zero-length BT/ET block), which IngramSpark's preflight flags as a
# non-embedded font. We render to _reportlab_raw.pdf first, then post-process
# through Ghostscript to drop the unused reference and guarantee every font in
# the final PDF is embedded. Output PDF then contains only the three TTFs we
# actually use (EBGaramond, EBGaramond-Italic, GreatVibes), all embedded.
RAW_PDF = BOOK_DIR / "_reportlab_raw.pdf"
OUTPUT = BOOK_DIR / "Through_the_Valley_IngramSpark_Paperback_Cover.pdf"
BG_IMAGE = BOOK_DIR / "cover_image_original_hires.jpg"
BARCODE_IMAGE = BOOK_DIR / "barcode_978-8-9954288-7-9.png"

# Register fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))
pdfmetrics.registerFont(TTFont("GreatVibes", str(FONT_DIR / "GreatVibes-Regular.ttf")))

# --- Spine calculation ---
PAGE_COUNT = 120
SPINE_W = 0.27  # 120 x 0.002252 = 0.27024" ~ 0.27"

# --- Front-cover composition mode ---------------------------------------
# The landscape source (1.5 aspect) can't fit both the shepherd's staff
# (image x ~20%) and a centered valley/sun in a single portrait crop. Two
# strategies are supported:
#
#   USE_STAFF_COMPOSITE = False (simple)
#     A single crop of the source. IMAGE_FOCUS_X picks which fraction of the
#     image lands at the front-cover panel's horizontal center. 0.50 centers
#     (valley/sun centered, staff cropped out); 0.40 shifts left enough for
#     the staff to show but pushes the valley off-center.
#
#   USE_STAFF_COMPOSITE = True (composite)
#     Renders the source twice into a portrait composite: once shifted so
#     the staff lands at STAFF_TARGET_X of the composite, and once centered
#     so valley/sun sit at composite center. The two layers are blended
#     with a soft vertical gradient mask across a feather zone. Because
#     both layers come from the same image, lighting matches automatically;
#     the seam passes through sky/hills/grass which look visually similar
#     in both crops.
USE_STAFF_COMPOSITE = True

# Used when USE_STAFF_COMPOSITE = False
IMAGE_FOCUS_X = 0.40

# Used when USE_STAFF_COMPOSITE = True — tune these if the seam is visible
# or the staff lands in the wrong place.
STAFF_IMAGE_X   = 0.20  # horizontal location of the staff in the source image (0–1)
STAFF_TARGET_X  = 0.26  # where the staff should appear in the composite (0–1)
SEAM_X          = 0.48  # center of the blend transition in the composite (0–1)
FEATHER_WIDTH   = 0.22  # total width of the blend transition zone (0–1)

# --- Document dimensions ---
BLEED = 0.125   # inches
TRIM_W = 5.5    # inches
TRIM_H = 8.5    # inches

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H = (BLEED + TRIM_H + BLEED) * inch

# --- Colors ---
DEEP_GREEN = Color(0.110, 0.180, 0.110)   # #1C2E1C deep forest green
CREAM = Color(0.961, 0.941, 0.910)        # #F5F0E8 warm cream
SAGE_LIGHT = Color(0.659, 0.722, 0.620)   # #A8B89E light sage
SAGE_MUTED = Color(0.482, 0.553, 0.435)   # #7B8D6F muted sage
DARK_TEXT = Color(0.15, 0.12, 0.08)        # Dark brown for text on light image

# --- Layout positions (from left edge of document) ---
BACK_COVER_LEFT = 0
BACK_COVER_RIGHT = (BLEED + TRIM_W) * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

# Trim edges (what the reader sees after cutting)
BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = BACK_COVER_RIGHT
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = FRONT_COVER_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

# Vertical
TRIM_TOP = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch
COVER_CENTER_Y = DOC_H / 2

# Safety margins (distance from trim edge to text)
# IngramSpark requires min 0.125" (3mm), recommends 0.25" (6mm) for covers.
# Script fonts (GreatVibes) have flourishes that extend beyond metric widths,
# so we use generous margins to avoid "elements outside safety area" rejections.
SAFETY = 0.5 * inch          # Back cover text margin (conservative)
FRONT_SAFETY = 0.25 * inch   # Front cover type safety (IngramSpark recommended)

# Front cover safe text area (text must stay within these bounds)
FRONT_SAFE_LEFT = FRONT_TRIM_LEFT + FRONT_SAFETY
FRONT_SAFE_RIGHT = FRONT_TRIM_RIGHT - FRONT_SAFETY
FRONT_SAFE_WIDTH = FRONT_SAFE_RIGHT - FRONT_SAFE_LEFT


def check_front_safety(c, text, font_name, font_size, cx):
    """Check if centered text fits within front cover safety zone. Prints diagnostic."""
    w = c.stringWidth(text, font_name, font_size)
    half_w = w / 2
    left_edge = cx - half_w
    right_edge = cx + half_w
    left_margin = (left_edge - FRONT_TRIM_LEFT) / inch
    right_margin = (FRONT_TRIM_RIGHT - right_edge) / inch
    min_margin = min(left_margin, right_margin)
    # Script fonts visually extend ~8% beyond metrics due to flourishes
    visual_margin = min_margin - (0.08 * w / inch / 2) if "Vibes" in font_name else min_margin
    status = "OK" if visual_margin >= 0.125 else "WARN"
    print(f'  [{status}] "{text}" ({font_name} {font_size}pt): '
          f'metric width={w/inch:.2f}", margins: L={left_margin:.3f}" R={right_margin:.3f}" '
          f'(est. visual margin: {visual_margin:.3f}")')
    return visual_margin >= 0.125


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


def make_staff_composite():
    """Build a portrait background combining a 'staff-visible' crop and a
    'valley-centered' crop of the landscape source, blended with a soft
    vertical gradient. The output has the same aspect as the front-cover
    panel (including bleed) so ReportLab can place it without letterboxing.

    Tuning parameters live at the top of this module (STAFF_IMAGE_X,
    STAFF_TARGET_X, SEAM_X, FEATHER_WIDTH).
    """
    src = Image.open(str(BG_IMAGE)).convert("RGB")
    sw, sh = src.size

    # Composite has the aspect ratio of the front-cover panel with bleed:
    #   width  = bleed + trim    (the spine-side edge has no bleed)
    #   height = bleed + trim + bleed
    panel_aspect = (BLEED + TRIM_W) / (BLEED + TRIM_H + BLEED)

    comp_h = sh
    comp_w = int(round(sh * panel_aspect))

    # Layer A (staff): shift source so STAFF_IMAGE_X of the source lands at
    # STAFF_TARGET_X of the composite.
    ox_a = int(round(STAFF_TARGET_X * comp_w - STAFF_IMAGE_X * sw))
    layer_a = Image.new("RGB", (comp_w, comp_h), (0, 0, 0))
    layer_a.paste(src, (ox_a, 0))

    # Layer B (centered): source midpoint at composite midpoint.
    ox_b = int(round(comp_w / 2 - sw / 2))
    layer_b = Image.new("RGB", (comp_w, comp_h), (0, 0, 0))
    layer_b.paste(src, (ox_b, 0))

    # Horizontal alpha mask: 255 on the left (layer A fully visible) → 0 on
    # the right (layer B fully visible), with a linear ramp across the
    # feather zone. Smoothstep the ramp so the transition is visually soft.
    seam_px    = SEAM_X * comp_w
    feather_px = FEATHER_WIDTH * comp_w
    fx0 = int(round(seam_px - feather_px / 2))
    fx1 = int(round(seam_px + feather_px / 2))
    fx0 = max(0, min(comp_w, fx0))
    fx1 = max(0, min(comp_w, fx1))

    row = np.empty(comp_w, dtype=np.float32)
    row[:fx0] = 1.0
    if fx1 > fx0:
        t = np.linspace(0.0, 1.0, fx1 - fx0, endpoint=True, dtype=np.float32)
        row[fx0:fx1] = 1.0 - (t * t * (3.0 - 2.0 * t))  # smoothstep
    row[fx1:] = 0.0
    mask_arr = np.tile((row * 255).astype(np.uint8), (comp_h, 1))
    mask = Image.fromarray(mask_arr, mode="L")

    return Image.composite(layer_a, layer_b, mask)


def draw_background(c):
    """Fill entire document with deep forest green."""
    c.setFillColor(DEEP_GREEN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Draw front cover: background image + all text drawn directly."""
    cx = FRONT_CENTER_X  # Exact center of trim area

    # --- Place background image ---
    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    if USE_STAFF_COMPOSITE:
        # Pre-composited portrait image already matches the panel's aspect
        # (staff on left, valley centered, feathered seam). Fit exactly —
        # no letterboxing.
        composite = make_staff_composite()
        buf = io.BytesIO()
        composite.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        img = ImageReader(buf)
        draw_w = target_w
        draw_h = target_h
        draw_x = target_x
        draw_y = 0
    else:
        # Single-image mode: landscape source, fit to height, crop sides.
        # IMAGE_FOCUS_X picks which fraction of the image lands at panel center.
        img = ImageReader(str(BG_IMAGE))
        img_w, img_h = img.getSize()
        img_aspect = img_w / img_h
        if img_aspect > target_aspect:
            draw_h = target_h
            draw_w = target_h * img_aspect
            draw_x = cx - IMAGE_FOCUS_X * draw_w
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

    # --- Semi-transparent overlay for text readability at top ---
    # Gradient from dark at top to transparent
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_COVER_LEFT, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)

    steps = 40
    top_y = DOC_H
    grad_height = 3.5 * inch
    for i in range(steps):
        alpha = 0.45 * (1 - i / steps) ** 1.5
        c.setFillColor(Color(0.95, 0.90, 0.80, alpha))
        y = top_y - (i * grad_height / steps)
        h = grad_height / steps + 1
        c.rect(FRONT_COVER_LEFT, y - h, target_w, h, fill=1, stroke=0)

    c.restoreState()

    # --- Title: "Through the" ---
    # Sizes reduced from 52/68/14 to ensure text stays within 0.25" safety zone.
    # GreatVibes flourishes extend beyond metric widths, so extra margin is critical.
    c.setFillColor(DARK_TEXT)
    c.setFont("GreatVibes", 44)
    c.drawCentredString(cx, DOC_H - 1.6 * inch, "Through the")
    check_front_safety(c, "Through the", "GreatVibes", 44, cx)

    # --- Title: "Valley" ---
    c.setFont("GreatVibes", 58)
    c.drawCentredString(cx, DOC_H - 2.35 * inch, "Valley")
    check_front_safety(c, "Valley", "GreatVibes", 58, cx)

    # --- Subtitle ---
    c.setFont("EBGaramond-Italic", 13)
    c.drawCentredString(cx, DOC_H - 3.1 * inch, "What God Says When the Shadow Is Real")
    check_front_safety(c, "What God Says When the Shadow Is Real", "EBGaramond-Italic", 13, cx)

    # --- Semi-transparent overlay for author at bottom ---
    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_COVER_LEFT, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)

    bottom_grad_height = 2.0 * inch
    for i in range(steps):
        alpha = 0.4 * (i / steps) ** 1.5
        c.setFillColor(Color(0.08, 0.10, 0.06, alpha))
        y = bottom_grad_height * (1 - i / steps)
        h = bottom_grad_height / steps + 1
        c.rect(FRONT_COVER_LEFT, y - h, target_w, h, fill=1, stroke=0)

    c.restoreState()

    # --- Author name (well within safety zone) ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 18)
    author_y = TRIM_BOTTOM + SAFETY + 0.3 * inch  # Safely above bottom trim + safety
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")


def draw_spine(c):
    """Spine is only 0.27" — too narrow for text. Leave as solid background color."""
    pass


def draw_back_cover(c):
    """Draw back cover text on deep forest green background."""
    safe_left = BACK_TRIM_LEFT + SAFETY
    safe_right = BACK_TRIM_RIGHT - SAFETY
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X

    # --- Hook line (italic, light sage) ---
    y = TRIM_TOP - 1.0 * inch
    c.setFillColor(SAGE_LIGHT)
    c.setFont("EBGaramond-Italic", 10.5)
    hook = "This book is short enough to read in a hospital room. It is meant to be."
    lines = wrap_text(c, hook, "EBGaramond-Italic", 10.5, text_width)
    for line in lines:
        c.drawCentredString(cx, y, line)
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
        "Through the Valley walks with two people at once \u2014 the one whose body is failing and the one who will be left behind. It does not separate them, because they are walking through the same valley.",
        "In eight chapters anchored entirely in Scripture, this book examines what God actually says \u2014 not platitudes, not near-death stories, not clinical speculation. What does God say about His presence when He feels absent? What happens after death? And how do you grieve honestly while holding to a hope that Scripture calls certain?",
        "The valley is real. The shadow is dark. But David did not say \u2018if I walk into the valley.\u2019 He said \u2018even though I walk through.\u2019 The valley has a through. And the Shepherd is already there.",
    ]

    for i, para in enumerate(body_paragraphs):
        lines = wrap_text(c, para, "EBGaramond", 10, text_width)
        c.setFont("EBGaramond", 10)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    # --- Attribution (small, muted sage) ---
    y -= line_height * 0.3
    c.setFillColor(SAGE_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y, "Scripture quotations from the New American Standard Bible\u00ae (NASB).")

    # --- Barcode (mandatory per IngramSpark, lower-right of back cover) ---
    # 100% black on white background, within safe area.
    # The source PNG is 523x280; at 1.75" wide it renders at 298.86 DPI which
    # fails IngramSpark's 300 DPI preflight. Rendering at 1.70" yields 307.6 DPI
    # (and stays well within IngramSpark's 1.469"–2.045" barcode size spec).
    barcode_img = ImageReader(str(BARCODE_IMAGE))
    bc_w = 1.70 * inch
    bc_h = bc_w * 280 / 523  # Maintain original aspect ratio
    pad = 0.08 * inch
    box_w = bc_w + 2 * pad
    box_h = bc_h + 2 * pad
    box_x = safe_right - box_w          # Right-aligned in safe area
    box_y = TRIM_BOTTOM + SAFETY        # Bottom of safe area
    c.setFillColor(white)
    c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)
    c.drawImage(barcode_img, box_x + pad, box_y + pad, width=bc_w, height=bc_h)


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating IngramSpark PAPERBACK cover PDF for "Through the Valley"...')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {SPINE_W}" ({PAGE_COUNT} pages, B&W white paper)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')
    print(f'  Front cover type safety: {FRONT_SAFETY/inch}" from trim edges')
    print(f'  Front cover safe text width: {FRONT_SAFE_WIDTH/inch:.2f}"')
    print(f'\nFront cover text safety checks:')

    c = canvas.Canvas(str(RAW_PDF), pagesize=(DOC_W, DOC_H))
    c.setTitle("Through the Valley - IngramSpark Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()

    # Post-process with Ghostscript to force-embed all fonts and drop the
    # unused Helvetica reference that ReportLab leaves in page resources.
    gs = shutil.which("gs")
    if not gs:
        print(f"\nWARNING: ghostscript not found in PATH — copying raw ReportLab "
              f"PDF directly to {OUTPUT}. IngramSpark may reject due to the "
              f"unused /Helvetica reference. Install ghostscript and re-run.")
        shutil.copyfile(RAW_PDF, OUTPUT)
    else:
        result = subprocess.run(
            [gs, "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
             "-dEmbedAllFonts=true", "-dSubsetFonts=true",
             "-dCompatibilityLevel=1.4", "-dAutoRotatePages=/None",
             "-dColorConversionStrategy=/LeaveColorUnchanged",
             f"-sOutputFile={OUTPUT}", str(RAW_PDF)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise SystemExit(f"Ghostscript failed:\n{result.stderr}")
        RAW_PDF.unlink(missing_ok=True)
        print(f"\nCover saved to {OUTPUT}")
        print(f"  Post-processed with ghostscript: all fonts embedded, "
              f"dimensions preserved.")
    print("Done.")


if __name__ == "__main__":
    main()
