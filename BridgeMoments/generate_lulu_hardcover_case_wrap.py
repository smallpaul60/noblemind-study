#!/usr/bin/env python3
"""Generate Lulu CASE-WRAP hardcover cover for 'Bridge Moments'.

Design mirrors the paperback (golden-hour stone footbridge, twilight
amber base, warm gold #B8883E accent). The hardcover spine is wider
because the case binds around boards.

Lulu specs (verified 2026-05-13 against the downloaded case-wrap template):
  Total document size:  13.938" x 10.250"
  Panel face (board):   5.75" x 9.00"   (board extends 0.125" past trim
                                         on top/bottom/outside)
  Spine width:          1.188"   (Lulu template — paperback 0.947" +
                                  ~0.241" board overhead; the 0.243"
                                  rule of thumb held within 0.002")
  Wrap area:            0.625" past board edge, all four sides
  Safety margin:        0.625" inside board edge
"""

import sys
from io import BytesIO
from pathlib import Path

# Register Standard-14 font overrides BEFORE constructing Canvas so any
# default Helvetica reference resolves to embedded Liberation Sans.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401

from PIL import Image
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BridgeMoments_Lulu_Hardcover_CaseWrap.pdf"
COVER_SOURCE = BOOK_DIR / "BridgeMoments-cover-image.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (Lulu template) ---
SPINE_W_IN = 1.188
PANEL_W_IN = 5.75
PANEL_H_IN = 9.00
WRAP_IN    = 0.625
SAFETY_IN  = 0.625

DOC_W_IN = PANEL_W_IN * 2 + SPINE_W_IN + WRAP_IN * 2   # 13.938
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
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2
FRONT_CENTER_X = (FRONT_FACE_LEFT + FRONT_FACE_RIGHT) / 2

# Safety bounds inside the face
BACK_SAFE_LEFT   = BACK_FACE_LEFT + SAFETY_IN * inch
BACK_SAFE_RIGHT  = BACK_FACE_RIGHT - SAFETY_IN * inch
BACK_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
BACK_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch
BACK_TEXT_WIDTH  = BACK_SAFE_RIGHT - BACK_SAFE_LEFT

# --- Colors (matched to the paperback) ---
DEEP_TWILIGHT = Color(0.090, 0.075, 0.055)   # #17130E
CREAM         = Color(0.961, 0.910, 0.804)   # #F5E8CD
GOLD          = Color(0.722, 0.533, 0.247)   # #B8883E warm gold
GOLD_MUTED    = Color(0.580, 0.443, 0.224)   # #94713A
SLATE         = Color(0.620, 0.580, 0.510)   # #9E9482


def _load_hires_cover():
    """2x LANCZOS upscale so front-face PPI clears Lulu's 200 PPI floor.
    Source 1024x1536 → 2048x3072 ≈ 356 PPI at 5.75\" wide."""
    src = Image.open(str(COVER_SOURCE)).convert("RGB")
    hires = src.resize((src.width * 2, src.height * 2), Image.LANCZOS)
    buf = BytesIO()
    hires.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return ImageReader(buf)


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for w in words:
        trial = f"{current} {w}".strip() if current else w
        if c.stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------

def draw_background(c):
    """Solid twilight amber across the whole document."""
    c.setFillColor(DEEP_TWILIGHT)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_face(c):
    """Bridge image fills the full front face; cream title block over the
    dark sky; author + imprint in the bottom gradient wash."""
    img = _load_hires_cover()
    iw, ih = img.getSize()
    img_aspect = iw / ih
    target_w = PANEL_W_IN * inch
    target_h = PANEL_H_IN * inch
    target_aspect = target_w / target_h

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
    p = c.beginPath(); p.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, target_h); p.close()
    c.clipPath(p, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # --- Title block (cream over the dark sky) ---
    cx = FRONT_CENTER_X
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 30)
    c.drawCentredString(cx, FACE_TOP - 1.0 * inch, "Bridge Moments")

    c.setFont("EBGaramond-Italic", 13.5)
    c.drawCentredString(cx, FACE_TOP - 1.42 * inch, "Making the Most of Every Opportunity")

    # --- Bottom gradient so author/imprint read clean against the path ---
    c.saveState()
    p = c.beginPath(); p.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, target_h); p.close()
    c.clipPath(p, stroke=0)
    steps = 240
    band_h = 2.0 * inch
    for i in range(steps):
        alpha = 0.58 * (i / steps) ** 1.4
        c.setFillColor(Color(0.02, 0.015, 0.01, alpha))
        y = FACE_BOTTOM + band_h * (1 - i / steps)
        h = band_h / steps + 1
        c.rect(FRONT_FACE_LEFT, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Author + imprint ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 15)
    c.drawCentredString(cx, FACE_BOTTOM + SAFETY_IN * inch + 0.45 * inch, "Paul Hainline")

    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, FACE_BOTTOM + SAFETY_IN * inch + 0.05 * inch,
                        "N O B L E M I N D   P R E S S")


def draw_spine(c):
    """1.188\" of spine is generous — big bold title in cream, author in
    gold, NobleMind imprint at foot. All rotated -90° to read top-to-bottom."""
    title_text  = "Bridge Moments"
    author_text = "Paul Hainline"
    foot_text   = "NobleMind Press"

    # Title near top of spine
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_TOP - 0.5 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 28)
    c.drawString(0, -9, title_text)
    c.restoreState()

    # Author near foot of spine
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_BOTTOM + 0.5 * inch + 1.8 * inch)
    c.rotate(-90)
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 14)
    c.drawString(0, -5, author_text)
    c.restoreState()

    # Imprint at very foot
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_BOTTOM + 0.5 * inch + 0.5 * inch)
    c.rotate(-90)
    c.setFillColor(SLATE)
    c.setFont("EBGaramond-Italic", 9.5)
    c.drawString(0, -3, foot_text)
    c.restoreState()


def draw_back_face(c):
    """Back face — Colossians 4:5-6 verse + body blurb + NobleMind imprint,
    same copy as the paperback back cover, on the twilight base."""
    cx = BACK_CENTER_X

    # --- Opening verse (italic gold) ---
    y = FACE_TOP - 1.0 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    verse_lines = [
        "“Walk in wisdom toward outsiders,",
        "making the most of the opportunity.",
        "Let your speech always be with grace,",
        "as though seasoned with salt …”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 15
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— Colossians 4:5–6")
    y -= 18

    # --- Gold rule ---
    y -= 8
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "What if you don’t have to be afraid of the conversation?",
        "The Christians we admire most weren’t the ones who memorized "
        "arguments. They were the ones who knew how to listen — to a person "
        "across a table, a coworker pulled aside in the break room, a "
        "stranger on a long flight — and to recognize the moment when the "
        "conversation was ready to turn toward something more.",
        "Jesus called those moments by no name. He just walked into them. "
        "The woman at the well. Nicodemus at night. Zacchaeus in the tree. "
        "The rich young ruler stopping Him on the road. In every one, He "
        "listened first, met the person where they actually were, and let "
        "truth do its own work.",
        "Twenty chapters across four parts — twelve case studies from the "
        "Gospels, three from Acts, and five chapters on practice. Every "
        "claim from Scripture. Three appendices included for small-group use.",
    ]
    body_font, body_size, lh = "EBGaramond", 9.5, 13
    emphasis_font = "EBGaramond-Italic"
    for i, para in enumerate(body):
        is_hook = (i == 0)
        font = emphasis_font if is_hook else body_font
        size = 10.5 if is_hook else body_size
        lines = wrap_text(c, para, font, size, BACK_TEXT_WIDTH)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= lh + (1 if is_hook else 0)
        y -= lh * 0.4

    # --- Scripture attribution ---
    y -= lh * 0.2
    c.setFillColor(GOLD_MUTED)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = BACK_SAFE_BOTTOM + 0.25 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print('Generating Lulu HARDCOVER case-wrap PDF for "Bridge Moments"...')
    print(f'  Document size: {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}"')
    print(f'  Panel face size: {PANEL_W_IN}" x {PANEL_H_IN}"')
    print(f'  Spine width: {SPINE_W_IN:.3f}"  (from Lulu template)')
    print(f'  Wrap: {WRAP_IN}" past board edge')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Bridge Moments — Lulu Hardcover Case-Wrap")

    draw_background(c)
    draw_back_face(c)
    draw_front_face(c)
    draw_spine(c)

    c.save()
    print(f"\nCase-wrap saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
