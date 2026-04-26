#!/usr/bin/env python3
"""Generate Lulu paperback cover PDF for 'Why the Division Among Brethren?'.

Typographic cover (no imagery): deep forest green base, cream typography,
muted gold accent.

Lulu specs (5.5x8.5 perfect bound paperback, B&W white paper):
  Trim size: 5.5" x 8.5"
  Spine width: PAGE_COUNT * 0.0029" approximate (Lulu's actual paper
               stock runs about 1.3x the generic 0.002252 formula
               based on the WhyDoYouDelay template comparison —
               update SPINE_W to Lulu's exact value from their template
               tool before final upload).
  Bleed: 0.125" on all outside edges (not on spine edges)
"""

from pathlib import Path

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_The_Division_Lulu_Paperback_Cover.pdf"

# Fonts
FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic",
                                str(FONT_DIR / "EBGaramond-Italic.ttf")))

# --- Page count & spine width ---
# Update PAGE_COUNT to match the printed Lulu interior page count.
# Update SPINE_W to Lulu's exact value once you generate the cover
# template in Lulu's design step. The formula below is an estimate;
# Lulu's actual value for 88-page B&W white was 0.258" (~0.0029/page).
PAGE_COUNT = 170
SPINE_W    = round(PAGE_COUNT * 0.0029, 3)

# --- Document dimensions ---
BLEED  = 0.125
TRIM_W = 5.5
TRIM_H = 8.5
DOC_W  = (BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED) * inch
DOC_H  = (BLEED + TRIM_H + BLEED) * inch

# --- Color palette: deep forest green / cream / muted gold ---
DEEP_GREEN   = Color(0.075, 0.137, 0.094)   # #13231A — deep forest
FOREST       = Color(0.137, 0.224, 0.149)   # #233927 — slightly lighter
SAGE_GLOW    = Color(0.227, 0.345, 0.243)   # #3A583E — soft inner light
CREAM        = Color(0.965, 0.949, 0.890)   # #F6F2E3 — title cream
PAPER        = Color(0.945, 0.918, 0.847)   # #F1EAD8 — body cream
GOLD         = Color(0.749, 0.616, 0.310)   # #BF9D4F — muted gold accent
MUTED_GOLD   = Color(0.580, 0.475, 0.255)   # #957941 — dimmer gold
SAGE         = Color(0.486, 0.561, 0.467)   # #7C8F77 — muted sage

# --- Layout positions ---
BACK_COVER_LEFT  = 0
BACK_COVER_RIGHT = (BLEED + TRIM_W) * inch

SPINE_LEFT   = BACK_COVER_RIGHT
SPINE_RIGHT  = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT  = SPINE_RIGHT
FRONT_COVER_RIGHT = DOC_W

BACK_TRIM_LEFT   = BLEED * inch
BACK_TRIM_RIGHT  = BACK_COVER_RIGHT
BACK_CENTER_X    = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

FRONT_TRIM_LEFT  = FRONT_COVER_LEFT
FRONT_TRIM_RIGHT = DOC_W - BLEED * inch
FRONT_CENTER_X   = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

TRIM_TOP       = DOC_H - BLEED * inch
TRIM_BOTTOM    = BLEED * inch
COVER_CENTER_Y = DOC_H / 2

SAFETY       = 0.5 * inch
FRONT_SAFETY = 0.25 * inch


def check_front_safety(c, text, font_name, font_size, cx):
    w = c.stringWidth(text, font_name, font_size)
    half_w = w / 2
    left_edge = cx - half_w
    right_edge = cx + half_w
    left_margin = (left_edge - FRONT_TRIM_LEFT) / inch
    right_margin = (FRONT_TRIM_RIGHT - right_edge) / inch
    status = "OK" if min(left_margin, right_margin) >= 0.125 else "WARN"
    print(f'  [{status}] "{text}" ({font_name} {font_size}pt): '
          f'L={left_margin:.3f}" R={right_margin:.3f}"')


def wrap_text(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    words = text.split()
    lines, current = [], ""
    for w in words:
        test = f"{current} {w}".strip() if current else w
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_background(c):
    """Fill with the deep-green base color across the full document."""
    c.setFillColor(DEEP_GREEN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def _draw_radial_glow(c, cx, cy, max_radius, color, steps=80, max_alpha=0.18):
    """Soft radial vignette to lift the centre of the front cover slightly,
    without breaking the typographic feel."""
    c.saveState()
    for i in range(steps, 0, -1):
        r = max_radius * (i / steps)
        alpha = max_alpha * (1 - i / steps) ** 1.5
        c.setFillColor(Color(color.red, color.green, color.blue, alpha))
        c.circle(cx, cy, r, stroke=0, fill=1)
    c.restoreState()


def draw_front_cover(c):
    cx = FRONT_CENTER_X
    cy = COVER_CENTER_Y

    # Subtle radial light from upper-third
    _draw_radial_glow(c, cx, DOC_H * 0.62, 4.0 * inch,
                      SAGE_GLOW, steps=60, max_alpha=0.12)

    # --- Inner border rule (gold, single hairline) ---
    inset = 0.32 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.45)
    border_left = FRONT_TRIM_LEFT + inset
    border_right = FRONT_TRIM_RIGHT - inset
    border_top = TRIM_TOP - inset
    border_bot = TRIM_BOTTOM + inset
    c.rect(border_left, border_bot,
           border_right - border_left, border_top - border_bot,
           fill=0, stroke=1)

    # --- Top ornament: small fleuron + thin rule ---
    orn_y = DOC_H - 1.05 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 13)
    c.drawCentredString(cx, orn_y, "❦")  # floral heart bullet
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.3)
    rule_hw = 0.6 * inch
    c.line(cx - rule_hw, orn_y - 12, cx - 0.15 * inch, orn_y - 12)
    c.line(cx + 0.15 * inch, orn_y - 12, cx + rule_hw, orn_y - 12)

    # --- Title (split into "Why the Division" / "Among Brethren?")
    # Using a measured two-line treatment with subtle italic on second line.
    title_top_y = DOC_H - 2.1 * inch

    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 30)
    c.drawCentredString(cx, title_top_y, "Why the Division")
    check_front_safety(c, "Why the Division", "EBGaramond", 30, cx)

    c.setFont("EBGaramond-Italic", 30)
    c.drawCentredString(cx, title_top_y - 0.55 * inch, "Among Brethren?")
    check_front_safety(c, "Among Brethren?", "EBGaramond-Italic", 30, cx)

    # --- Decorative double rule below title ---
    rule_y = title_top_y - 1.05 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.45)
    rule_hw = 0.85 * inch
    c.line(cx - rule_hw, rule_y, cx + rule_hw, rule_y)
    c.setLineWidth(0.25)
    c.line(cx - rule_hw * 0.55, rule_y - 4,
           cx + rule_hw * 0.55, rule_y - 4)

    # --- Subtitle (centered, italic, two lines, with care for width) ---
    sub_max_w = (FRONT_TRIM_RIGHT - FRONT_TRIM_LEFT) - 2 * 0.55 * inch
    subtitle_lines = [
        "The Underlying Issue Between",
        "Institutional and Non-Institutional",
        "churches of Christ",
    ]
    sub_y = rule_y - 0.55 * inch
    c.setFillColor(PAPER)
    c.setFont("EBGaramond-Italic", 13)
    for line in subtitle_lines:
        c.drawCentredString(cx, sub_y, line)
        check_front_safety(c, line, "EBGaramond-Italic", 13, cx)
        sub_y -= 0.28 * inch

    # --- Lower fleuron, separating subtitle and author block ---
    orn2_y = TRIM_BOTTOM + SAFETY + 1.3 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 12)
    c.drawCentredString(cx, orn2_y, "❦")

    # --- Author ---
    author_y = TRIM_BOTTOM + SAFETY + 0.7 * inch
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 14)
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")
    check_front_safety(c, "P A U L   H A I N L I N E", "EBGaramond", 14, cx)

    # --- Imprint at bottom ---
    imp_y = TRIM_BOTTOM + SAFETY + 0.05 * inch
    c.setFillColor(MUTED_GOLD)
    c.setFont("EBGaramond-Italic", 9)
    c.drawCentredString(cx, imp_y, "NOBLEMIND PRESS")


def draw_spine(c):
    """Spine: solid forest base, vertical cream title + author when wide
    enough. Lulu recommends spine text only when the spine is at least
    ~0.0625" (1/16") on each side margin — for our 170pp ~0.49" spine
    that's comfortable. Below ~0.25" we'd skip text."""
    c.setFillColor(FOREST)
    c.rect(SPINE_LEFT, 0, SPINE_W * inch, DOC_H, fill=1, stroke=0)

    if SPINE_W < 0.30:
        # Spine too narrow for legible text — leave plain.
        return

    # Vertical text: title near the top of the spine reading bottom-to-top
    # (the standard for English-language print spines).
    c.saveState()
    c.translate(SPINE_CENTER_X, DOC_H - 1.2 * inch)
    c.rotate(-90)

    # Title
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 11)
    c.drawString(0, -3, "Why the Division Among Brethren?")

    c.restoreState()

    # Author near the bottom
    c.saveState()
    c.translate(SPINE_CENTER_X, TRIM_BOTTOM + 1.2 * inch)
    c.rotate(-90)
    c.setFillColor(MUTED_GOLD)
    c.setFont("EBGaramond-Italic", 9)
    c.drawString(0, -2.5, "Paul Hainline")
    c.restoreState()


def draw_back_cover(c):
    blurb_inset = SAFETY + 0.2 * inch
    safe_left = BACK_TRIM_LEFT + blurb_inset
    safe_right = BACK_TRIM_RIGHT - blurb_inset
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X

    # --- Inner border rule ---
    inset = 0.32 * inch
    c.setStrokeColor(MUTED_GOLD)
    c.setLineWidth(0.4)
    c.rect(BACK_TRIM_LEFT + inset, TRIM_BOTTOM + inset,
           BACK_TRIM_RIGHT - BACK_TRIM_LEFT - 2 * inset,
           TRIM_TOP - TRIM_BOTTOM - 2 * inset,
           fill=0, stroke=1)

    # --- Opening epigraph ---
    y = TRIM_TOP - 1.0 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11.5)
    c.drawCentredString(cx, y, "A position must stand or fall")
    y -= 16
    c.drawCentredString(cx, y, "based on what the Scriptures")
    y -= 16
    c.drawCentredString(cx, y, "actually teach.")
    y -= 18
    c.setFont("EBGaramond", 9)
    c.setFillColor(SAGE)
    c.drawCentredString(cx, y, "— the thesis of this booklet")

    # --- Thin rule ---
    y -= 18
    line_hw = 0.55 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 22

    # --- Body blurb ---
    c.setFillColor(PAPER)
    line_height = 13.2

    body_paragraphs = [
        "More than seventy years ago, a division took place among the "
        "churches of Christ. Most of those who live with its consequences "
        "today have never had the division fairly explained to them.",
        "This booklet states both positions — institutional and "
        "non-institutional — in the way their best advocates would "
        "state them, walks the relevant Scriptures text by text, and "
        "lets the text carry the conclusion.",
        "Eleven chapters across four parts, written for the reader who "
        "wants to think for himself in front of the open Bible.",
    ]
    for i, para in enumerate(body_paragraphs):
        c.setFont("EBGaramond", 9.5)
        if i == 0:
            c.setFont("EBGaramond-Italic", 10)
        lines = wrap_text(c, para, "EBGaramond", 9.5, text_width)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.5

    # --- Closing tag (italic, gold) ---
    y -= line_height * 0.2
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(cx, y, "Read with the Book open.")

    # --- Attribution ---
    attr_y = TRIM_BOTTOM + SAFETY + 0.85 * inch
    c.setFillColor(SAGE)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(
        cx, attr_y,
        "Scripture quotations from the New American Standard Bible® (NASB).",
    )

    # --- Imprint (no ISBN — first edition) ---
    mark_y = TRIM_BOTTOM + SAFETY + 0.25 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SAGE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")


def main():
    doc_w_in = DOC_W / inch
    doc_h_in = DOC_H / inch

    print('Generating Lulu PAPERBACK cover PDF for '
          '"Why the Division Among Brethren?"...')
    print(f'  Trim size: {TRIM_W}" x {TRIM_H}"')
    print(f'  Spine width: {SPINE_W:.3f}" '
          f'({PAGE_COUNT} pages × 0.0029 estimate; '
          'update with Lulu template value before final upload)')
    print(f'  Bleed: {BLEED}"')
    print(f'  Total document size: {doc_w_in:.3f}" x {doc_h_in:.3f}"')
    print(f'\nFront cover text safety checks:')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Why the Division Among Brethren? — Lulu Paperback Cover")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)

    c.save()
    print(f"\nCover saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
