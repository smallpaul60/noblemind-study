#!/usr/bin/env python3
"""Generate Lulu CASE-WRAP hardcover cover for 'Before I Formed You'.

42-page booklet at Lulu's hardcover minimum spine (0.25"). Design
mirrors the paperback: warm dark brown wrap, basket-in-reeds image on
the front face, parchment-cream back face with the Hagar opening quote
and the body blurb. The spine is too narrow for legible text.

Lulu template (verified 2026-05-13):
  Total document size:  13.000" x 10.250"
  Panel face (board):   5.75" x 9.00"
  Spine width:          0.250"  (Lulu hardcover floor)
  Wrap area:            0.625" past board edge, all four sides
  Safety margin:        0.625" inside board edge
"""

import sys
from pathlib import Path

# Register Standard-14 font overrides BEFORE constructing Canvas so any
# default Helvetica reference resolves to embedded Liberation Sans.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BeforeIFormedYou_Lulu_Hardcover_CaseWrap.pdf"
COVER_IMAGE = BOOK_DIR / "BeforeIFormed_YouCoverImage_hires.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (from Lulu's case-wrap template) ---
SPINE_W_IN = 0.250
PANEL_W_IN = 5.75
PANEL_H_IN = 9.00
WRAP_IN    = 0.625
SAFETY_IN  = 0.625

DOC_W_IN = PANEL_W_IN * 2 + SPINE_W_IN + WRAP_IN * 2   # 13.000
DOC_H_IN = PANEL_H_IN + WRAP_IN * 2                     # 10.250
DOC_W    = DOC_W_IN * inch
DOC_H    = DOC_H_IN * inch

# --- Panel positions (PDF coords, origin bottom-left) ---
BACK_FACE_LEFT   = WRAP_IN * inch
BACK_FACE_RIGHT  = BACK_FACE_LEFT + PANEL_W_IN * inch
SPINE_LEFT       = BACK_FACE_RIGHT
SPINE_RIGHT      = SPINE_LEFT + SPINE_W_IN * inch
FRONT_FACE_LEFT  = SPINE_RIGHT
FRONT_FACE_RIGHT = FRONT_FACE_LEFT + PANEL_W_IN * inch

FACE_BOTTOM = WRAP_IN * inch
FACE_TOP    = FACE_BOTTOM + PANEL_H_IN * inch
FACE_CY     = (FACE_BOTTOM + FACE_TOP) / 2

BACK_CENTER_X  = (BACK_FACE_LEFT + BACK_FACE_RIGHT) / 2
FRONT_CENTER_X = (FRONT_FACE_LEFT + FRONT_FACE_RIGHT) / 2

# Safety bounds inside the face
FRONT_SAFE_LEFT = FRONT_FACE_LEFT + SAFETY_IN * inch
FRONT_SAFE_TOP  = FACE_TOP - SAFETY_IN * inch
BACK_SAFE_LEFT  = BACK_FACE_LEFT + SAFETY_IN * inch
BACK_SAFE_RIGHT = BACK_FACE_RIGHT - SAFETY_IN * inch
BACK_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
BACK_SAFE_TOP   = FACE_TOP - SAFETY_IN * inch
BACK_TEXT_WIDTH = BACK_SAFE_RIGHT - BACK_SAFE_LEFT

# --- Colors (matched to the paperback) ---
WARM_DARK  = Color(0.180, 0.145, 0.100)   # #2E2519
WARM_CREAM = Color(0.945, 0.910, 0.835)   # #F1E8D5
WARM_GOLD  = Color(0.780, 0.690, 0.480)   # #C7B07A
WARM_LIGHT = Color(0.890, 0.850, 0.760)   # #E3D9C2


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


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    """Solid warm dark brown across the whole document (wraps + spine).
    The front face will be overlaid with the cover image; the back face
    gets a parchment-cream rectangle drawn on top."""
    c.setFillColor(WARM_DARK)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_face(c):
    """Place basket-in-reeds image filling the full front face, then
    overlay title / subtitle / author in cream."""
    img = ImageReader(str(COVER_IMAGE))
    iw, ih = img.getSize()
    img_aspect = iw / ih
    target_w = PANEL_W_IN * inch
    target_h = PANEL_H_IN * inch
    target_aspect = target_w / target_h

    # Cover the full face, cropping the longer dimension
    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = FRONT_CENTER_X - draw_w / 2
        draw_y = FACE_BOTTOM
    else:
        draw_w = target_w
        draw_h = target_w / img_aspect
        draw_x = FRONT_FACE_LEFT
        draw_y = FACE_CY - draw_h / 2

    c.saveState()
    path = c.beginPath()
    path.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, target_h)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # --- Title / subtitle (cream over the upper image) ---
    cx = FRONT_CENTER_X
    c.setFillColor(WARM_CREAM)
    c.setFont("EBGaramond", 24)
    c.drawCentredString(cx, FACE_TOP - 1.1 * inch, "Before I Formed You")

    c.setFillColor(WARM_LIGHT)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, FACE_TOP - 1.55 * inch, "What God Says to the Woman")
    c.drawCentredString(cx, FACE_TOP - 1.75 * inch, "Holding This Book")

    # --- Author near the bottom ---
    c.setFillColor(WARM_CREAM)
    c.setFont("EBGaramond", 13)
    c.drawCentredString(cx, FACE_BOTTOM + 0.8 * inch, "Paul & Pam Hainline")


def draw_back_face(c):
    """Parchment-cream rectangle on the back face + body text. Same
    copy as the paperback back cover."""
    # Parchment background on the back face only
    c.setFillColor(WARM_CREAM)
    c.rect(BACK_FACE_LEFT, FACE_BOTTOM,
           PANEL_W_IN * inch, PANEL_H_IN * inch, fill=1, stroke=0)

    cx = BACK_CENTER_X

    # --- Hook line (italic dark, Hagar) ---
    c.setFillColor(WARM_DARK)
    y = FACE_TOP - 1.2 * inch
    hook = ("She sat down a bowshot away, because she said, "
            "“Do not let me see the boy die.”")
    for line in wrap_text(c, hook, "EBGaramond-Italic", 11, BACK_TEXT_WIDTH):
        c.setFont("EBGaramond-Italic", 11)
        c.drawCentredString(cx, y, line)
        y -= 15

    # --- Gold rule ---
    y -= 10
    c.setStrokeColor(WARM_GOLD)
    c.setLineWidth(0.4)
    c.line(cx - 0.5 * inch, y, cx + 0.5 * inch, y)
    y -= 20

    # --- Body ---
    ls = 14
    body = [
        "This book is written for you — the woman holding it right now, "
        "wherever you are, whatever you’re facing.",
        "It walks through the stories of women in Scripture who faced moments "
        "they did not choose: Hagar, alone in the desert. Jochebed, hiding her "
        "son under a death sentence. Hannah, broken and desperate. Ruth, gleaning "
        "scraps to survive. Rahab, risking everything on a God she barely knew. "
        "Mary, young and frightened and saying yes. Esther, placed where she "
        "needed to be for such a time as hers.",
        "Every one of them carried something whose purpose was larger than "
        "anything they could see.",
        "Everything in these pages comes from Scripture. We didn’t add to it. "
        "We just told the stories and let God’s Word speak for itself.",
    ]
    c.setFillColor(WARM_DARK)
    for para in body:
        lines = wrap_text(c, para, "EBGaramond", 10, BACK_TEXT_WIDTH)
        for line in lines:
            c.setFont("EBGaramond", 10)
            c.drawCentredString(cx, y, line)
            y -= ls
        y -= ls * 0.4

    # --- Jeremiah 1:5 closer ---
    y -= ls * 0.3
    c.setFillColor(Color(0.35, 0.30, 0.22))
    c.setFont("EBGaramond-Italic", 9.5)
    c.drawCentredString(cx, y, "“Before I formed you in the womb I knew you,")
    y -= 13
    c.drawCentredString(cx, y, "before you were born I consecrated you.”")
    y -= 15
    c.setFont("EBGaramond", 8.5)
    c.drawCentredString(cx, y, "— Jeremiah 1:5")

    # --- Imprint footer ---
    c.setFillColor(Color(0.50, 0.45, 0.35))
    c.setFont("EBGaramond", 7.5)
    c.drawCentredString(cx, BACK_SAFE_BOTTOM + 0.1 * inch,
                        "NobleMind Press · noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print('Generating Lulu HARDCOVER case-wrap PDF for "Before I Formed You"...')
    print(f'  Document size: {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}"')
    print(f'  Panel face size: {PANEL_W_IN}" x {PANEL_H_IN}"')
    print(f'  Spine width: {SPINE_W_IN:.3f}"  (Lulu hardcover floor — no spine text)')
    print(f'  Wrap: {WRAP_IN}" past board edge')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Before I Formed You — Lulu Hardcover Case-Wrap")

    draw_background(c)
    draw_back_face(c)
    draw_front_face(c)

    c.save()
    print(f"\nCase-wrap saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
