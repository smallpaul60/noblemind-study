#!/usr/bin/env python3
"""Generate Lulu CASE-WRAP hardcover cover for 'Made, Not Written'.

Lulu specs (5.5x8.5 hardcover case-wrap, 196 pp cream interior):
  Total document:  13.488" x 10.250"   (varies with spine width)
  Panel face:      5.75"   x 9.000"    (board extends 0.125" past trim
                                        on top, bottom, and outside)
  Spine width:     0.743"  (paperback 0.500" + ~0.243" board overhead;
                            pull final from Lulu's downloaded template
                            before submit)
  Wrap area:       0.625"  past board edge, all four sides
  Safety margin:   0.625"  inside board edge

Front face is purely typographic — matches the paperback front exactly,
proportionally scaled to the 9.0" face. No image. Back face mirrors
the paperback back: Luke 12:48 anchor, slate-blue rule, four-paragraph
blurb, NobleMind footer. Spine carries title (top→bottom) and author.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import isbn_barcode  # noqa: F401  (registers Standard-14 font aliases)

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Made_Not_Written_Lulu_Hardcover_CaseWrap.pdf"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# ============================================================================
# DOCUMENT DIMENSIONS
# ============================================================================
PAGE_COUNT  = 196
SPINE_W_IN  = 0.743   # paperback 0.500 + 0.243 board overhead — pull from
                      # Lulu's downloaded hardcover template before submit

PANEL_W_IN  = 5.75
PANEL_H_IN  = 9.00
WRAP_IN     = 0.625
SAFETY_IN   = 0.625

DOC_W_IN    = PANEL_W_IN * 2 + SPINE_W_IN + WRAP_IN * 2   # 13.493
DOC_H_IN    = PANEL_H_IN + WRAP_IN * 2                    # 10.250
DOC_W       = DOC_W_IN * inch
DOC_H       = DOC_H_IN * inch

# Horizontal anchors
WRAP_LEFT_RIGHT  = WRAP_IN * inch
BACK_FACE_LEFT   = WRAP_LEFT_RIGHT
BACK_FACE_RIGHT  = BACK_FACE_LEFT + PANEL_W_IN * inch
SPINE_LEFT       = BACK_FACE_RIGHT
SPINE_RIGHT      = SPINE_LEFT + SPINE_W_IN * inch
FRONT_FACE_LEFT  = SPINE_RIGHT
FRONT_FACE_RIGHT = FRONT_FACE_LEFT + PANEL_W_IN * inch

# Vertical anchors
FACE_BOTTOM = WRAP_IN * inch
FACE_TOP    = FACE_BOTTOM + PANEL_H_IN * inch
FACE_CY     = (FACE_BOTTOM + FACE_TOP) / 2

BACK_CENTER_X  = (BACK_FACE_LEFT + BACK_FACE_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2
FRONT_CENTER_X = (FRONT_FACE_LEFT + FRONT_FACE_RIGHT) / 2

# Safety-inset bounds for the back panel
BACK_SAFE_LEFT   = BACK_FACE_LEFT + SAFETY_IN * inch
BACK_SAFE_RIGHT  = BACK_FACE_RIGHT - SAFETY_IN * inch
BACK_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
BACK_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch
BACK_TEXT_WIDTH  = BACK_SAFE_RIGHT - BACK_SAFE_LEFT

# --- Palette (matches the paperback) ---
NEAR_BLACK  = Color(0.051, 0.059, 0.078)   # #0D0F14
CREAM       = Color(0.941, 0.925, 0.894)   # #F0ECE4
CREAM_SOFT  = Color(0.804, 0.749, 0.647)   # #CDBFA5
ACCENT_GOLD = Color(0.769, 0.643, 0.290)   # #C4A44A
GOLD_DEEP   = Color(0.541, 0.490, 0.400)   # #8A7D66
SLATE_BLUE  = Color(0.478, 0.561, 0.659)   # #7A8FA8


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _draw_centered_spaced(c, text, font_name, font_size, cx, baseline_y,
                          char_spacing_pt):
    """Centered drawString with extra spacing between every character."""
    c.setFont(font_name, font_size)
    widths = [c.stringWidth(ch, font_name, font_size) for ch in text]
    total = sum(widths) + char_spacing_pt * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        c.drawString(x, baseline_y, ch)
        x += wch + char_spacing_pt


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
    """Solid near-black across the whole document — covers the back panel,
    the spine, and the wrap areas that fold to the inside of the boards."""
    c.setFillColor(NEAR_BLACK)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_face(c):
    """Purely typographic front — mirrors the paperback front exactly,
    proportionally scaled to the 9.0" face height (vs. 8.5" trim on PB).
    Italic "Made," + upright "Not Written" + slate-blue rule + italic
    subtitle + spaced-gold author + gold imprint.
    """
    cx = FRONT_CENTER_X
    SCALE = PANEL_H_IN / 8.5   # 1.0588 — match PB proportions

    # Title block sits high on the face
    y_title_top = FACE_TOP - 2.1 * inch * SCALE

    # --- Title block ---
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond-Italic", 52 * SCALE)
    c.drawCentredString(cx, y_title_top, "Made,")

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 58 * SCALE)
    c.drawCentredString(cx, y_title_top - 64 * SCALE, "Not Written")

    # --- Slate-blue rule ---
    rule_y = y_title_top - (64 + 26) * SCALE
    c.setStrokeColor(SLATE_BLUE)
    c.setLineWidth(0.8)
    c.line(cx - 1.0 * inch, rule_y, cx + 1.0 * inch, rule_y)

    # --- Subtitle ---
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond-Italic", 15 * SCALE)
    c.drawCentredString(cx, rule_y - 26 * SCALE, "A Bible Student Looks")
    c.drawCentredString(cx, rule_y - (26 + 19) * SCALE, "at the Machine")

    # --- Author + imprint ---
    author_y = FACE_BOTTOM + 1.45 * inch * SCALE
    c.setFillColor(ACCENT_GOLD)
    _draw_centered_spaced(c, "PAUL HAINLINE", "EBGaramond", 14 * SCALE, cx,
                          author_y, 2.0 * SCALE)

    c.setFillColor(GOLD_DEEP)
    _draw_centered_spaced(c, "NOBLEMIND PUBLISHING", "EBGaramond", 8 * SCALE,
                          cx, author_y - 22 * SCALE, 1.6 * SCALE)


def draw_spine(c):
    """Spine — title (top→bottom, house style) + author."""
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_TOP - 0.7 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 12)
    c.drawString(0, -3.5, "Made, Not Written")
    c.restoreState()

    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_BOTTOM + 1.4 * inch)
    c.rotate(-90)
    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond", 10)
    c.drawString(0, -3.0, "PAUL HAINLINE")
    c.restoreState()


def draw_back_face(c):
    """Back face — Luke 12:48 anchor + body blurb + Scripture attribution
    + NobleMind Publishing imprint. Mirrors the paperback back."""
    cx = BACK_CENTER_X

    # --- Anchor verse ---
    y = FACE_TOP - 1.05 * inch
    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond-Italic", 10.5)
    verse_lines = [
        "“From everyone who has been given much,",
        "much will be required; and to whom",
        "they entrusted much, of him they",
        "will ask all the more.”",
    ]
    for vl in verse_lines:
        c.drawCentredString(cx, y, vl)
        y -= 14
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y - 2, "— Luke 12:48")
    y -= 20

    # --- Slate-blue rule ---
    y -= 4
    c.setStrokeColor(SLATE_BLUE)
    c.setLineWidth(0.7)
    c.line(cx - 0.6 * inch, y, cx + 0.6 * inch, y)
    y -= 22

    # --- Body ---
    c.setFillColor(CREAM)
    body = [
        "Most people feel one of two things when they think about artificial intelligence: awe or dread. Both grow from the same root — they do not actually know what the thing is.",
        "A Bible student sits down across the table from the tool he has been using daily and asks it, in plain English, what it actually is. The machine answers — set apart on the page, in its own voice — and the book that follows is the long form of that conversation.",
        "Made, Not Written shows in three movements that the mystery is real but it is not magic; that consciousness, creativity, and the mirror problem each sit exactly where the evidence sits, neither lower nor higher; and that the real moral question turns out to be an ancient one. Babel revisited. The mixed heart. Stewardship under a Maker who is coming back.",
        "Warm, not breathless. Sober, not fearful. Where Scripture speaks, it leads.",
    ]
    for i, para in enumerate(body):
        is_hook = (i == 0)
        font = "EBGaramond-Italic" if is_hook else "EBGaramond"
        size = 10.5 if is_hook else 9.5
        lh = 13.5 if is_hook else 13
        lines = wrap_text(c, para, font, size, BACK_TEXT_WIDTH)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= lh
        y -= lh * 0.45

    # --- Scripture attribution ---
    y -= 4
    c.setFillColor(GOLD_DEEP)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(cx, y,
                        "Scripture quotations from the New American Standard Bible® (NASB).")

    # --- Imprint footer ---
    mark_y = BACK_SAFE_BOTTOM + 0.25 * inch
    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Publishing")
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print('Generating Lulu HARDCOVER case-wrap for "Made, Not Written"...')
    print(f'  Page count:     {PAGE_COUNT}')
    print(f'  Document size:  {DOC_W_IN:.3f}" x {DOC_H_IN:.3f}"')
    print(f'  Panel face:     {PANEL_W_IN}" x {PANEL_H_IN}"')
    print(f'  Spine width:    {SPINE_W_IN:.3f}"  (estimate — pull from Lulu template)')
    print(f'  Wrap:           {WRAP_IN}" past board edge')
    print(f'  Safety:         {SAFETY_IN}" inside board edge')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Made, Not Written — Lulu Hardcover Case-Wrap")

    draw_background(c)
    draw_front_face(c)
    draw_back_face(c)
    draw_spine(c)
    c.showPage()
    c.save()
    print(f"\nCase-wrap saved to {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")
    print("Done.")


if __name__ == "__main__":
    main()
