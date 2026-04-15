#!/usr/bin/env python3
"""Generate Lulu casewrap hardcover full wraparound cover.

Specs taken from the Lulu template for this book (224 pages, 5.5x8.5 casewrap):
  - Document size: 13.563 in x 10.25 in
  - Spine width: 0.813 in
  - Wrap allowance: 0.875 in on top, bottom, and outside edges
  - Visible trim per panel: 5.5 in x 8.5 in (after the wrap folds around the boards)

Layout (left to right):
  [0.875 wrap] [5.5 back cover] [0.813 spine] [5.5 front cover] [0.875 wrap]
  Top/bottom: 0.875 wrap on both edges.

Design:
  - Solid black background across the entire document (covers wrap + spine)
  - Front cover: doorframe image fit-by-width into the visible front trim,
    with tiny top/bottom black bands from the aspect mismatch (image 0.667,
    trim 0.647). Typography matches the approved paperback mockup.
  - Back cover: blurb from Back_Cover_Blurb.md in white EB Garamond,
    centered in the visible back trim, 0.5" safety margin.
  - Spine: solid black, no text.

Outputs:
  - The_Last_Week_of_the_Lamb_Lulu_Hardcover_Cover.pdf  (print-ready)
  - The_Last_Week_of_the_Lamb_Lulu_Hardcover_Cover.png  (rasterized preview)
"""

import subprocess
from pathlib import Path

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
IMAGE_FILE = BOOK_DIR / "book_cover_doorframe.png"
OUTPUT_PDF = BOOK_DIR / "The_Last_Week_of_the_Lamb_Lulu_Hardcover_Cover.pdf"
OUTPUT_PNG = BOOK_DIR / "The_Last_Week_of_the_Lamb_Lulu_Hardcover_Cover.png"

FONT_DIR = Path.home() / ".local" / "share" / "fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Document dimensions (from Lulu template) ---
# NOTE: a hardcover case board is 0.125" larger than the book block on
# top, bottom, and outside (industry-standard "squares" / overhang).
# So the VISIBLE case per panel is 5.625 x 8.75, not 5.5 x 8.5, and the
# wrap allowance that folds around the case boards is 0.75" on each
# outside edge (not 0.875). Layout check:
#   0.75 + 5.625 + 0.813 + 5.625 + 0.75 = 13.563  (width)
#   0.75 + 8.75 + 0.75                 = 10.25   (height)
DOC_W = 13.563 * inch
DOC_H = 10.25 * inch
SPINE_W = 0.813 * inch
WRAP = 0.75 * inch
CASE_W = 5.625 * inch   # visible panel width (board including 0.125 overhang)
CASE_H = 8.75 * inch    # visible panel height (board including overhangs)

# --- Layout anchors (document coordinates) ---
# Visible back case
BACK_TRIM_LEFT = WRAP                        # 0.750
BACK_TRIM_RIGHT = BACK_TRIM_LEFT + CASE_W    # 6.375
# Spine
SPINE_LEFT = BACK_TRIM_RIGHT                 # 6.375
SPINE_RIGHT = SPINE_LEFT + SPINE_W           # 7.188
# Visible front case
FRONT_TRIM_LEFT = SPINE_RIGHT                # 7.188
FRONT_TRIM_RIGHT = FRONT_TRIM_LEFT + CASE_W  # 12.813
# Visible top/bottom (same for all panels)
TRIM_BOTTOM = WRAP                           # 0.750
TRIM_TOP = TRIM_BOTTOM + CASE_H              # 9.500

# Aliases kept for legibility in the drawing code below
TRIM_W = CASE_W
TRIM_H = CASE_H

# Convenience centers
FRONT_TRIM_CX = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2
BACK_TRIM_CX = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2
TRIM_CY = (TRIM_TOP + TRIM_BOTTOM) / 2

# --- Colors (matching the approved mockup) ---
CREAM = Color(0.96, 0.93, 0.84)
CREAM_DIM = Color(0.85, 0.80, 0.70)
GOLD = Color(0.79, 0.66, 0.31)
WHITE = Color(1, 1, 1)

# --- Front cover text anchors ---
# The doorframe image's dark-well horizontal center is at x = 0.525 of the
# image width (measured from the rendered mockup). With fit-by-width the
# image spans the entire visible front trim, so the dark well sits at:
DARK_CENTER_X_FRAC = 0.525

# Vertical fractions from top of the visible front trim. These mirror the
# approved paperback mockup positions.
TITLE_Y_FRAC_FROM_TOP = 0.30
SUBTITLE_Y_FRAC_FROM_TOP = 0.435
AUTHOR_Y_FRAC_FROM_TOP = 0.87
IMPRINT_Y_FRAC_FROM_TOP = 0.93


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    """Fill the entire document (wrap + panels + spine) with solid black."""
    c.setFillColor(black)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover_image(c):
    """Draw the doorframe image fit-by-width into the visible front trim.

    The image's aspect (0.667) is wider than the trim's aspect (0.647), so
    fitting by width leaves small black bands (~0.128 in) at the top and
    bottom of the trim. Those bands blend into the image's own black
    background and are imperceptible.
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
    """Convert a top-down fraction of the visible front trim to PDF y."""
    return TRIM_TOP - (frac_from_top * TRIM_H)


def draw_front_cover_text(c):
    """Title / gold rule / subtitle / author / imprint — matches the mockup."""
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

# Back cover safe area — 0.5" inside the visible back trim
BACK_SAFE_LEFT = BACK_TRIM_LEFT + 0.5 * inch
BACK_SAFE_RIGHT = BACK_TRIM_RIGHT - 0.5 * inch
BACK_SAFE_TOP = TRIM_TOP - 0.5 * inch
BACK_SAFE_BOTTOM = TRIM_BOTTOM + 0.5 * inch
BACK_TEXT_WIDTH = BACK_SAFE_RIGHT - BACK_SAFE_LEFT


def wrap_text(c, text, font_name, font_size, max_width):
    """Word-wrap text to lines that fit within max_width."""
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current = ""
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
    """Back cover copy — white EB Garamond on the black background.

    Mirrors Back_Cover_Blurb.md structure:
      - Bold hook
      - Three body paragraphs
      - Italic closing tagline: "The tradition is old. But the text is older."
      - Footer: noblemind.study
    """
    cx = BACK_TRIM_CX
    c.setFillColor(WHITE)

    # Hook — tagline weight
    hook_font = "EBGaramond"
    hook_size = 16
    hook_line_height = 21

    # Body — standard
    body_font = "EBGaramond"
    body_size = 9.5
    body_line_height = 13

    # Italic closer
    close_font = "EBGaramond-Italic"
    close_size = 10.5
    close_line_height = 14

    blocks = [
        ("hook",
         "What if the tradition is wrong?"),
        ("body",
         "For seventeen centuries, the church has placed the crucifixion on a Friday. "
         "But Friday gives you two nights in the tomb \u2014 not three. It leaves you "
         "with a spice-buying sequence that contradicts itself. And it breaks the one "
         "sign Jesus Himself gave to prove who He was."),
        ("body",
         "This book doesn\u2019t start with tradition. It starts with the text."),
        ("body",
         "Following the time markers that Matthew, Mark, Luke, and John actually wrote "
         "\u2014 \u201cthe next day,\u201d \u201cafter two days,\u201d "
         "\u201csix days before the Passover\u201d \u2014 a different week emerges. "
         "A week where two independent Gospel chronologies converge on the same day. "
         "A week where every authority in Israel examines Jesus and finds no fault. "
         "A week where the Lamb of God dies on the exact day, at the exact hour, that "
         "God commanded the Passover lamb to be killed fifteen centuries earlier."),
        ("body",
         "This is not a commentary. It is not a denominational position. It is a "
         "guided walk through the text itself \u2014 every conclusion shown, every "
         "assumption identified, every inference labeled honestly. No verse is asked "
         "to carry more weight than it can bear."),
        ("body",
         "You will not be asked to take anyone\u2019s word for it. You will be asked "
         "to open your Bible."),
        ("close",
         "The tradition is old. But the text is older."),
    ]

    # Start from just below the top safety margin
    y = BACK_SAFE_TOP - 0.1 * inch

    for kind, text in blocks:
        if kind == "hook":
            c.setFont(hook_font, hook_size)
            lines = wrap_text(c, text, hook_font, hook_size, BACK_TEXT_WIDTH)
            for line in lines:
                c.drawCentredString(cx, y, line)
                y -= hook_line_height
            y -= hook_line_height * 0.6
        elif kind == "body":
            lines = wrap_text(c, text, body_font, body_size, BACK_TEXT_WIDTH)
            c.setFont(body_font, body_size)
            for line in lines:
                c.drawCentredString(cx, y, line)
                y -= body_line_height
            y -= body_line_height * 0.45  # paragraph break
        elif kind == "close":
            y -= close_line_height * 0.3
            c.setFont(close_font, close_size)
            lines = wrap_text(c, text, close_font, close_size, BACK_TEXT_WIDTH)
            for line in lines:
                c.drawCentredString(cx, y, line)
                y -= close_line_height

    # Footer — noblemind.study at the bottom safety margin
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, BACK_SAFE_BOTTOM + 0.1 * inch, "noblemind.study")


# ---------------------------------------------------------------------------
# PREVIEW
# ---------------------------------------------------------------------------

def render_png_preview():
    tmp_prefix = BOOK_DIR / "_hc_preview"
    subprocess.run(
        ["pdftoppm", "-r", "120", "-png", str(OUTPUT_PDF), str(tmp_prefix)],
        check=True,
    )
    rendered = BOOK_DIR / "_hc_preview-1.png"
    if rendered.exists():
        rendered.rename(OUTPUT_PNG)


def main():
    print("Generating Lulu casewrap hardcover cover...")
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')
    print(f'  Spine: {SPINE_W/inch:.3f}"')
    print(f'  Wrap: {WRAP/inch:.3f}" on top, bottom, and outside edges')
    print(f'  Visible trim per panel: {TRIM_W/inch:.2f}" x {TRIM_H/inch:.2f}"')

    c = canvas.Canvas(str(OUTPUT_PDF), pagesize=(DOC_W, DOC_H))

    draw_background(c)
    draw_front_cover_image(c)
    draw_front_cover_text(c)
    draw_back_cover(c)
    # Spine intentionally left blank

    c.save()
    print(f"  PDF saved to {OUTPUT_PDF}")

    render_png_preview()
    print(f"  PNG preview saved to {OUTPUT_PNG}")
    print("Done.")


if __name__ == "__main__":
    main()
