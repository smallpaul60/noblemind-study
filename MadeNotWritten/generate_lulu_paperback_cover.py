#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'Made, Not Written'.

Lulu specs (5.5x8.5 perfect-bound paperback, 196 pages, B&W cream interior):
  Trim: 5.5" x 8.5"
  Spine: 0.500"  (cream formula 196 × 0.00226 + 0.057 ≈ 0.500" — pull
                  final width from Lulu's downloaded template before submit)
  Bleed: 0.125" outside edges
  Total document: ~11.750" x 8.750"

Front cover is purely typographic — no image. Title in EB Garamond
(italic "Made," + upright "Not Written"), thin slate-blue rule, italic
subtitle, author in spaced gold caps, imprint at base. The all-text
treatment honors the book's voice (sober, plain language) and stands
out on a shelf of AI books that all reach for the same neural-mesh
visual clichés the book itself argues against. Reasoning: ChatGPT,
Gemini, and Grok all failed to depict what AI is — each one drew the
picture that flattered its training (cherub, cozy desk, branded
Thinker robot). A typographic cover refuses the picture-the-AI-
wants-to-be-seen-as and lets the title's own argument carry the front.

Back cover: deep slate/black ground (matching the index.html theme),
slate-blue rule (echoing the machine-block accent inside the book),
Luke 12:48 as the anchor verse, four-paragraph blurb, NobleMind footer.

ReportLab is configured to embed all fonts (including Standard-14 aliases
from tools/isbn_barcode.py) so Lulu's preflight accepts the cover.

No ISBN — book ships without an assigned ISBN per author's standing
position (he will not allow a Lulu-supplied ISBN).
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
OUTPUT = BOOK_DIR / "Made_Not_Written_Lulu_Paperback_Cover.pdf"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Dimensions ---
SPINE_W = 0.5014  # Lulu template (196 pp cream); formula 0.500 — template wins
BLEED = 0.125
TRIM_W = 5.5
TRIM_H = 8.5

DOC_W = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch   # ~11.750
DOC_H = (BLEED + TRIM_H + BLEED) * inch                       #  8.750

# --- Layout anchors ---
BACK_LEFT = 0
BACK_RIGHT = (BLEED + TRIM_W) * inch
SPINE_LEFT = BACK_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
FRONT_LEFT = SPINE_RIGHT
FRONT_RIGHT = DOC_W
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

BACK_TRIM_LEFT = BLEED * inch
BACK_TRIM_RIGHT = BACK_RIGHT
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT = FRONT_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

TRIM_TOP = DOC_H - BLEED * inch
TRIM_BOTTOM = BLEED * inch

SAFETY = 0.5 * inch

# --- Palette (matches the book's site theme: gold + slate-blue on slate-black) ---
NEAR_BLACK  = Color(0.051, 0.059, 0.078)   # #0D0F14 — back-cover ground
CREAM       = Color(0.941, 0.925, 0.894)   # #F0ECE4 — body text
CREAM_SOFT  = Color(0.804, 0.749, 0.647)   # #CDBFA5 — softer body
ACCENT_GOLD = Color(0.769, 0.643, 0.290)   # #C4A44A — anchor verse, imprint
GOLD_DEEP   = Color(0.541, 0.490, 0.400)   # #8A7D66 — attribution
SLATE_BLUE  = Color(0.478, 0.561, 0.659)   # #7A8FA8 — machine-block accent / rule


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
    """Solid dark ground for the entire wraparound."""
    c.setFillColor(NEAR_BLACK)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    """Purely typographic front — no image.

    Title music: italic "Made," (the gentle observation) over upright
    "Not Written" (the firm correction). The italic-to-upright shift
    visually carries the rhetorical pause built into the title itself.
    A single thin slate-blue rule under the title — same accent that
    appears on the back cover, the same accent the machine-block uses
    inside the book — ties the three surfaces together.
    """
    cx = FRONT_CENTER_X

    # Vertical anchors (measured from top of trim)
    # The title block sits high; the author/imprint sits low.
    y_title_top = TRIM_TOP - 2.1 * inch

    # --- Title block ---
    # "Made," — italic, cream-soft, large
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond-Italic", 52)
    c.drawCentredString(cx, y_title_top, "Made,")

    # "Not Written" — upright, cream, slightly larger, just below
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 58)
    c.drawCentredString(cx, y_title_top - 64, "Not Written")

    # --- Slate-blue rule (matches back-cover rule + machine-block accent) ---
    rule_y = y_title_top - 64 - 26
    c.setStrokeColor(SLATE_BLUE)
    c.setLineWidth(0.8)
    c.line(cx - 1.0 * inch, rule_y, cx + 1.0 * inch, rule_y)

    # --- Subtitle ---
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond-Italic", 15)
    c.drawCentredString(cx, rule_y - 26, "A Bible Student Looks")
    c.drawCentredString(cx, rule_y - 26 - 19, "at the Machine")

    # --- Author block (spaced caps, gold) ---
    author_y = TRIM_BOTTOM + 1.45 * inch
    c.setFillColor(ACCENT_GOLD)
    _draw_centered_spaced(c, "PAUL HAINLINE", "EBGaramond", 14, cx,
                          author_y, 2.0)

    # --- Imprint footer ---
    c.setFillColor(GOLD_DEEP)
    _draw_centered_spaced(c, "NOBLEMIND PUBLISHING", "EBGaramond", 8, cx,
                          author_y - 22, 1.6)


def draw_spine(c):
    """0.500\" spine — comfortable for the title and the author."""
    # Title: top-anchored, reads top-to-bottom on shelf (per house style).
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_TOP - 0.55 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 11)
    c.drawString(0, -3.0, "Made, Not Written")
    c.restoreState()

    # Author: bottom-anchored
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + 1.3 * inch)
    c.rotate(-90)
    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond", 9)
    c.drawString(0, -3.0, "PAUL HAINLINE")
    c.restoreState()


def draw_back_cover(c):
    cx = BACK_CENTER_X
    blurb_inset = SAFETY + 0.05 * inch
    safe_left = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left

    # --- Anchor verse: Luke 12:48 ---
    y = TRIM_TOP - 0.95 * inch
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

    # --- Slate-blue rule (echoes the machine-block accent inside the book) ---
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
        lines = wrap_text(c, para, font, size, text_width)
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
    mark_y = TRIM_BOTTOM + SAFETY + 0.20 * inch
    c.setFillColor(ACCENT_GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Publishing")
    c.setFillColor(CREAM_SOFT)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 13, "noblemind.study")


def main():
    print('Generating Lulu PAPERBACK cover for "Made, Not Written"...')
    print(f'  Trim:    {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine:   {SPINE_W:.3f}"  (196 pp cream — pull final from Lulu template)')
    print(f'  Bleed:   {BLEED}" outside edges')
    print(f'  Document: {DOC_W/inch:.3f}" x {DOC_H/inch:.3f}"')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Made, Not Written — Lulu Paperback Cover")
    draw_background(c)
    draw_back_cover(c)
    draw_spine(c)
    draw_front_cover(c)
    c.showPage()
    c.save()
    print(f"\nWrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
