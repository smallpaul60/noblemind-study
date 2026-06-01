#!/usr/bin/env python3
"""Generate Lulu perfect-bound paperback full wraparound cover.

Specs from the Lulu template for this title (224 pages, 5.5x8.5 paperback,
cream interior — confirmed via the cover template PDF Lulu generated on
the Design step):
  - Document size: 11.815 in x 8.75 in
  - Spine width:   0.565 in   (cream paper is thicker than the generic
                                0.002252 formula, which would predict
                                ~0.504 in; always trust Lulu's value)
  - Bleed:         0.125 in on the three outside edges (top/bottom/outside)

Layout (left to right):
  [0.125 bleed] [5.5 back trim] [0.565 spine] [5.5 front trim] [0.125 bleed]
  Top/bottom: 0.125 bleed.

Design mirrors the published hardcover (The_Last_Week_of_the_Lamb_
Lulu_Hardcover_Cover.pdf) so the editions sit together on a shelf:
  - Solid black background across the whole document
  - Front: doorframe image fit-by-width into the trim; cream title;
    gold rule; cream-dim italic subtitle; cream author; gold imprint
  - Back: blurb in white EB Garamond, gold tagline closer, gold imprint
  - Spine: rotated title in cream + author at the foot
    (the hardcover spine was blank because the 0.813" wrap+overhang gave
     a heavier visual; the paperback's 0.565" looks naked without text
     and benefits from a label on the shelf)

Outputs:
  - The_Last_Week_of_the_Lamb_Lulu_Paperback_Cover.pdf  (print-ready)
"""

import sys
from pathlib import Path

# Register Standard-14 font overrides (Helvetica → embedded Liberation Sans)
# BEFORE any ReportLab Canvas is constructed. Without this Lulu/IngramSpark
# preflight reports Helvetica as unembedded and rejects the cover.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401  (import-for-side-effects)

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
IMAGE_FILE = BOOK_DIR / "book_cover_doorframe.png"
OUTPUT_PDF = BOOK_DIR / "The_Last_Week_of_the_Lamb_Lulu_Paperback_Cover.pdf"

FONT_DIR = Path.home() / ".local" / "share" / "fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions ---
# 2026-06-01: page count grew 224 → 232 with the Wednesday-vs-Friday
# comparison appendix. Spine 0.5825" from Lulu's downloaded template
# after upload (formula predicted 0.581", held within 0.0015").
SPINE_W = 0.5825 * inch  # 232pp cream from Lulu template (was 0.565" at 224pp)
DOC_W = 0.125 + 5.5 + (SPINE_W / inch) + 5.5 + 0.125  # = 11.831"
DOC_W = DOC_W * inch
DOC_H = 8.75 * inch
BLEED = 0.125 * inch
TRIM_W = 5.5 * inch
TRIM_H = 8.5 * inch

# --- Layout anchors (PDF coordinates, origin bottom-left) ---
BACK_TRIM_LEFT = BLEED                         # 0.125
BACK_TRIM_RIGHT = BACK_TRIM_LEFT + TRIM_W      # 5.625
SPINE_LEFT = BACK_TRIM_RIGHT                   # 5.625
SPINE_RIGHT = SPINE_LEFT + SPINE_W             # 6.190
FRONT_TRIM_LEFT = SPINE_RIGHT                  # 6.190
FRONT_TRIM_RIGHT = FRONT_TRIM_LEFT + TRIM_W    # 11.690

TRIM_BOTTOM = BLEED                            # 0.125
TRIM_TOP = TRIM_BOTTOM + TRIM_H                # 8.625

FRONT_TRIM_CX = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2
BACK_TRIM_CX = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2
SPINE_CX = (SPINE_LEFT + SPINE_RIGHT) / 2
TRIM_CY = (TRIM_TOP + TRIM_BOTTOM) / 2

# --- Colors (matching the hardcover) ---
CREAM = Color(0.96, 0.93, 0.84)
CREAM_DIM = Color(0.85, 0.80, 0.70)
GOLD = Color(0.79, 0.66, 0.31)
WHITE = Color(1, 1, 1)

# --- Front cover anchors (matching hardcover proportions) ---
DARK_CENTER_X_FRAC = 0.525        # doorframe well horizontal center within the image
TITLE_Y_FRAC_FROM_TOP = 0.30
SUBTITLE_Y_FRAC_FROM_TOP = 0.435
AUTHOR_Y_FRAC_FROM_TOP = 0.87
IMPRINT_Y_FRAC_FROM_TOP = 0.93


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    """Fill the entire document (bleed + trims + spine) with solid black."""
    c.setFillColor(black)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover_image(c):
    """Draw the doorframe image fit-by-width into the visible front trim.

    Image aspect (~0.667) is wider than trim aspect (5.5/8.5 = 0.647), so
    fit-by-width leaves ~0.127" of black band at top and bottom of trim.
    Those bands sit on the black background and read as the image's own
    border.
    """
    img = ImageReader(str(IMAGE_FILE))
    iw, ih = img.getSize()
    img_aspect = iw / ih

    draw_w = TRIM_W
    draw_h = draw_w / img_aspect
    draw_x = FRONT_TRIM_LEFT
    draw_y = TRIM_CY - (draw_h / 2)

    c.drawImage(
        img, draw_x, draw_y, width=draw_w, height=draw_h,
        preserveAspectRatio=True, mask="auto",
    )


def frac_to_front_pdf_y(frac_from_top):
    return TRIM_TOP - (frac_from_top * TRIM_H)


def draw_front_cover_text(c):
    """Title / gold rule / subtitle / author / imprint — mirrors hardcover."""
    cx = FRONT_TRIM_LEFT + (DARK_CENTER_X_FRAC * TRIM_W)

    # --- Title ---
    c.setFillColor(CREAM)
    title_size = 22
    c.setFont("EBGaramond", title_size)
    y1 = frac_to_front_pdf_y(TITLE_Y_FRAC_FROM_TOP)
    c.drawCentredString(cx, y1, "The Last Week")
    y2 = y1 - (title_size * 1.05)
    c.drawCentredString(cx, y2, "of the Lamb")

    # --- Gold rule ---
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    rule_y = y2 - 0.28 * inch
    rule_half = 0.7 * inch
    c.line(cx - rule_half, rule_y, cx + rule_half, rule_y)

    # --- Subtitle ---
    c.setFillColor(CREAM_DIM)
    subtitle_size = 14
    c.setFont("EBGaramond-Italic", subtitle_size)
    sy = frac_to_front_pdf_y(SUBTITLE_Y_FRAC_FROM_TOP)
    c.drawCentredString(cx, sy, "The Passover Pattern")
    c.drawCentredString(cx, sy - (subtitle_size * 1.35), "Good Friday Missed")

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 18)
    ay = frac_to_front_pdf_y(AUTHOR_Y_FRAC_FROM_TOP)
    c.drawCentredString(cx, ay, "Paul Hainline")

    # --- Imprint ---
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 9)
    iy = frac_to_front_pdf_y(IMPRINT_Y_FRAC_FROM_TOP)
    c.drawCentredString(cx, iy, "N O B L E M I N D   P R E S S")


# ---------------------------------------------------------------------------
# BACK COVER
# ---------------------------------------------------------------------------

# 0.5" safety inside the visible back trim (per CLAUDE.md cover-clearance rule)
BACK_SAFE_LEFT = BACK_TRIM_LEFT + 0.5 * inch
BACK_SAFE_RIGHT = BACK_TRIM_RIGHT - 0.5 * inch
BACK_SAFE_TOP = TRIM_TOP - 0.5 * inch
BACK_SAFE_BOTTOM = TRIM_BOTTOM + 0.5 * inch
BACK_TEXT_WIDTH = BACK_SAFE_RIGHT - BACK_SAFE_LEFT


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip() if current else word
        if c.stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_back_cover(c):
    """Back cover copy — white EB Garamond on black, mirroring the hardcover."""
    cx = BACK_TRIM_CX
    c.setFillColor(WHITE)

    hook_font, hook_size, hook_lh = "EBGaramond", 16, 21
    body_font, body_size, body_lh = "EBGaramond", 9.5, 13
    close_font, close_size, close_lh = "EBGaramond-Italic", 10.5, 14

    blocks = [
        ("hook", "What if the tradition is wrong?"),
        ("body",
         "For seventeen centuries, the church has placed the crucifixion on a Friday. "
         "But Friday gives you two nights in the tomb — not three. It leaves you "
         "with a spice-buying sequence that contradicts itself. And it breaks the one "
         "sign Jesus Himself gave to prove who He was."),
        ("body",
         "This book doesn’t start with tradition. It starts with the text."),
        ("body",
         "Following the time markers that Matthew, Mark, Luke, and John actually wrote "
         "— “the next day,” “after two days,” "
         "“six days before the Passover” — a different week emerges. "
         "A week where two independent Gospel chronologies converge on the same day. "
         "A week where every authority in Israel examines Jesus and finds no fault. "
         "A week where the Lamb of God dies on the exact day, at the exact hour, that "
         "God commanded the Passover lamb to be killed fifteen centuries earlier."),
        ("body",
         "This is not a commentary. It is not a denominational position. It is a "
         "guided walk through the text itself — every conclusion shown, every "
         "assumption identified, every inference labeled honestly. No verse is asked "
         "to carry more weight than it can bear."),
        ("body",
         "You will not be asked to take anyone’s word for it. You will be asked "
         "to open your Bible."),
        ("close",
         "The tradition is old. But the text is older."),
    ]

    y = BACK_SAFE_TOP - 0.1 * inch
    for kind, text in blocks:
        if kind == "hook":
            c.setFont(hook_font, hook_size)
            for line in wrap_text(c, text, hook_font, hook_size, BACK_TEXT_WIDTH):
                c.drawCentredString(cx, y, line)
                y -= hook_lh
            y -= hook_lh * 0.6
        elif kind == "body":
            lines = wrap_text(c, text, body_font, body_size, BACK_TEXT_WIDTH)
            c.setFont(body_font, body_size)
            for line in lines:
                c.drawCentredString(cx, y, line)
                y -= body_lh
            y -= body_lh * 0.45
        elif kind == "close":
            y -= close_lh * 0.3
            c.setFont(close_font, close_size)
            for line in wrap_text(c, text, close_font, close_size, BACK_TEXT_WIDTH):
                c.drawCentredString(cx, y, line)
                y -= close_lh

    # Footer
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, BACK_SAFE_BOTTOM + 0.1 * inch, "noblemind.study")


# ---------------------------------------------------------------------------
# SPINE
# ---------------------------------------------------------------------------

def draw_spine(c):
    """Rotated title in cream, author at the foot — title reads top-to-bottom
    when the book is shelved spine-out (US/UK convention).

    Spine layout (0.565" wide, 8.5" tall): keep text inside a 0.0625" safety
    margin on each long edge. Title runs along the spine; author sits near
    the bottom in a smaller size.
    """
    spine_safety_long = 0.5 * inch     # top/bottom safety from trim edges
    title_text = "The Last Week of the Lamb"
    author_text = "Paul Hainline"

    # --- Title (rotated -90°: baseline runs top-to-bottom) ---
    c.saveState()
    c.translate(SPINE_CX, TRIM_TOP - spine_safety_long)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 13)
    # After translate+rotate, text is drawn left-to-right along what is now
    # the vertical axis of the spine, starting from the top of the trim.
    # Center the baseline within the spine width (~ -4pt vertical offset).
    c.drawString(0, -4, title_text)
    c.restoreState()

    # --- Author near foot of spine, also rotated ---
    c.saveState()
    # Position the author near the bottom — anchor to the bottom of the trim
    # plus enough room that the rotated baseline sits inside the safety margin
    c.translate(SPINE_CX, TRIM_BOTTOM + spine_safety_long + 1.6 * inch)
    c.rotate(-90)
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 9)
    c.drawString(0, -3, author_text)
    c.restoreState()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("Generating Lulu paperback cover (perfect-bound)...")
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')
    print(f'  Spine:    {SPINE_W/inch:.3f}" (232 pp cream interior — pull exact from Lulu template)')
    print(f'  Bleed:    {BLEED/inch:.3f}" on outside edges')
    print(f'  Trim:     {TRIM_W/inch:.2f}" x {TRIM_H/inch:.2f}" per panel')

    c = canvas.Canvas(str(OUTPUT_PDF), pagesize=(DOC_W, DOC_H))
    c.setTitle("The Last Week of the Lamb — Lulu Paperback Cover")

    draw_background(c)
    draw_front_cover_image(c)
    draw_front_cover_text(c)
    draw_back_cover(c)
    draw_spine(c)

    c.save()
    print(f"  PDF saved to {OUTPUT_PDF}")
    print("Done.")


if __name__ == "__main__":
    main()
