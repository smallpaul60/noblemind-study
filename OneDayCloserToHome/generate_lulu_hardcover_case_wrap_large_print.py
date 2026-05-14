#!/usr/bin/env python3
"""Generate Lulu CASE-WRAP hardcover for the LARGE-PRINT edition of
'One Day Closer to Home'. Designed for elderly readers — 6x9 trim,
case wrap (no jacket to fumble with), prominent LARGE PRINT EDITION
badge so buyers and gift-givers can identify it at a glance.

Lulu specs (verified 2026-05-14 against case-wrap template):
  Document size:   14.563" x 10.75"
  Panel face:      6.25" x 9.50"   (6.0 trim + 0.25" overhang per side
                                     — wider overhang than 5.5x8.5)
  Spine width:     0.813"  (236 pp cream interior)
  Wrap:            0.625" past board edge, all four sides
  Safety:          0.625" inside board edge

Design carries the paperback palette (sunset porch + warm dark wood
+ cream + sunrise gold) but with extra prominence on the LARGE PRINT
indicator. Spine carries title + author; image fills the front face.
"""

import sys
from io import BytesIO
from pathlib import Path

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
OUTPUT = BOOK_DIR / "One_Day_Closer_to_Home_LargePrint_Lulu_Hardcover_CaseWrap.pdf"
COVER_SOURCE = BOOK_DIR / "One Day Closer to Home.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions (Lulu template) ---
SPINE_W_IN = 0.813
PANEL_W_IN = 6.25
PANEL_H_IN = 9.50
WRAP_IN    = 0.625
SAFETY_IN  = 0.625

DOC_W_IN = PANEL_W_IN * 2 + SPINE_W_IN + WRAP_IN * 2   # 14.563
DOC_H_IN = PANEL_H_IN + WRAP_IN * 2                     # 10.750
DOC_W    = DOC_W_IN * inch
DOC_H    = DOC_H_IN * inch

# --- Panel positions ---
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

BACK_SAFE_LEFT   = BACK_FACE_LEFT + SAFETY_IN * inch
BACK_SAFE_RIGHT  = BACK_FACE_RIGHT - SAFETY_IN * inch
BACK_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
BACK_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch
BACK_TEXT_WIDTH  = BACK_SAFE_RIGHT - BACK_SAFE_LEFT

# --- Colors (matched to the paperback) ---
DEEP_BROWN   = Color(0.137, 0.090, 0.063)   # #231710
CREAM        = Color(0.953, 0.910, 0.792)   # #F3E8CA
SUNRISE_GOLD = Color(0.886, 0.624, 0.275)   # #E29F46
GOLD_DEEP    = Color(0.706, 0.467, 0.180)   # #B4772E
SLATE        = Color(0.604, 0.561, 0.494)   # #9A8F7E


def _load_hires_cover():
    """2x LANCZOS — 1024x1536 → 2048x3072. At the 6.25" face width that's
    ~328 PPI, comfortably above Lulu's 200 floor."""
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
    c.setFillColor(DEEP_BROWN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_face(c):
    """Sunset porch image fills the full front face. Title overlay,
    subtitle, prominent LARGE PRINT EDITION badge, author."""
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

    # --- Top wash so title reads cleanly ---
    c.saveState()
    p = c.beginPath(); p.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, target_h); p.close()
    c.clipPath(p, stroke=0)
    steps = 220
    top_h = 2.6 * inch
    for i in range(steps):
        alpha = 0.55 * (1 - i / steps) ** 1.4
        c.setFillColor(Color(0.08, 0.05, 0.03, alpha))
        y = FACE_TOP - (i * top_h / steps)
        h = top_h / steps + 1
        c.rect(FRONT_FACE_LEFT, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Title block (cream over the dark sky) ---
    cx = FRONT_CENTER_X
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 28)
    c.drawCentredString(cx, FACE_TOP - 0.95 * inch, "One Day Closer")

    c.setFont("EBGaramond", 42)
    c.drawCentredString(cx, FACE_TOP - 1.6 * inch, "to Home")

    # Subtitle (two italic lines)
    c.setFont("EBGaramond-Italic", 14)
    c.drawCentredString(cx, FACE_TOP - 2.05 * inch, "A Book of Hope for Those")
    c.drawCentredString(cx, FACE_TOP - 2.32 * inch, "in the Final Chapters")

    # --- LARGE PRINT EDITION badge ---
    # Sits between subtitle and author. Sunrise gold so it stands out
    # cleanly against the dark wash but doesn't compete with the title.
    badge_y = FACE_TOP - 2.85 * inch
    c.setStrokeColor(SUNRISE_GOLD)
    c.setLineWidth(0.6)
    rule_hw = 1.0 * inch
    c.line(cx - rule_hw, badge_y + 0.18 * inch, cx + rule_hw, badge_y + 0.18 * inch)
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond", 12)
    c.drawCentredString(cx, badge_y, "L A R G E   P R I N T   E D I T I O N")
    c.line(cx - rule_hw, badge_y - 0.10 * inch, cx + rule_hw, badge_y - 0.10 * inch)

    # --- Bottom gradient for author ---
    c.saveState()
    p = c.beginPath(); p.rect(FRONT_FACE_LEFT, FACE_BOTTOM, target_w, target_h); p.close()
    c.clipPath(p, stroke=0)
    bot_h = 1.8 * inch
    bsteps = 220
    for i in range(bsteps):
        alpha = 0.55 * (i / bsteps) ** 1.4
        c.setFillColor(Color(0.08, 0.05, 0.03, alpha))
        y = FACE_BOTTOM + bot_h * (1 - i / bsteps)
        h = bot_h / bsteps + 1
        c.rect(FRONT_FACE_LEFT, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # --- Author ---
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    c.drawCentredString(cx, FACE_BOTTOM + SAFETY_IN * inch + 0.2 * inch,
                        "P A U L   H A I N L I N E")


def draw_spine(c):
    """0.813\" spine — comfortable for prominent title + author."""
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_TOP - 0.5 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 16)
    c.drawString(0, -6, "One Day Closer to Home")
    c.restoreState()

    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_BOTTOM + 0.5 * inch + 1.8 * inch)
    c.rotate(-90)
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond", 11)
    c.drawString(0, -4, "Paul Hainline")
    c.restoreState()


def draw_back_face(c):
    """2 Cor 4:16 verse + body blurb + LARGE PRINT confirmation + imprint.
    Body text is set slightly larger (12pt instead of 9.5pt) so the back-
    cover blurb itself is readable to the same large-print audience."""
    cx = BACK_CENTER_X

    # --- Anchor verse (italic gold) ---
    y = FACE_TOP - 1.0 * inch
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond-Italic", 13)
    verse_lines = [
        "“Therefore we do not lose heart,",
        "but though our outer man is decaying,",
        "yet our inner man is being renewed",
        "day by day.”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 17
    c.setFont("EBGaramond", 11)
    c.drawCentredString(cx, y - 2, "— 2 Corinthians 4:16")
    y -= 24

    # --- Gold rule ---
    y -= 4
    c.setStrokeColor(SUNRISE_GOLD)
    c.setLineWidth(0.6)
    c.line(cx - 0.7 * inch, y, cx + 0.7 * inch, y)
    y -= 24

    # --- Body — slightly larger than the paperback back so a large-print
    # buyer can read the blurb itself ---
    c.setFillColor(CREAM)
    body = [
        "Aging is not the long ending of a good story. It is the long approach to a better one.",
        "Scripture does not flinch from the body that is breaking down — but it never lets that "
        "be the whole picture. Simeon held the Christ child and was ready to depart in peace. "
        "Anna never left the temple. Caleb at eighty-five asked for one more mountain. Paul, in "
        "prison and old, called his suffering a momentary light affliction next to what was coming.",
        "Thirteen chapters across three parts walk through the examples, the theology, and the "
        "crescendo of biblical hope for those nearing the end.",
        "If you are walking the final mile, or walking it with someone you love, this book is for you.",
    ]
    for i, para in enumerate(body):
        is_hook = (i == 0)
        font = "EBGaramond-Italic" if is_hook else "EBGaramond"
        size = 13 if is_hook else 12
        lh = 17 if is_hook else 16
        lines = wrap_text(c, para, font, size, BACK_TEXT_WIDTH)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= lh
        y -= lh * 0.4

    # --- LARGE PRINT confirmation line on back ---
    y -= 8
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, y, "Large-print edition · 16-point type · 6 × 9 inches")
    y -= 14

    # --- Attribution ---
    y -= 8
    c.setFillColor(GOLD_DEEP)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = BACK_SAFE_BOTTOM + 0.3 * inch
    c.setFillColor(SUNRISE_GOLD)
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 10)
    c.drawCentredString(cx, mark_y - 15, "noblemind.study")


def main():
    print('Generating Lulu HARDCOVER case-wrap (LARGE PRINT) for ODCH...')
    print(f'  Document: {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}"')
    print(f'  Panel:    {PANEL_W_IN}" x {PANEL_H_IN}"  (6x9 trim + 0.25" overhang)')
    print(f'  Spine:    {SPINE_W_IN}"  (236 pp cream, from Lulu template)')
    print(f'  Wrap:     {WRAP_IN}" all four sides')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("One Day Closer to Home (Large Print) — Lulu Hardcover Case-Wrap")

    draw_background(c)
    draw_back_face(c)
    draw_front_face(c)
    draw_spine(c)

    c.save()
    print(f"\nCase-wrap saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
