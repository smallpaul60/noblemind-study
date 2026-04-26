#!/usr/bin/env python3
"""Generate Lulu CASE-WRAP hardcover cover for
'Why the Division Among Brethren?'.

Typographic cover (no imagery) — same forest-green palette as the
paperback. The hardcover spine is wider than the paperback because the
case-wrap adds the binding boards' thickness.

Lulu specs (from Lulu's case-wrap template for a 5.5x8.5 hardcover):
  Total document size:  PANEL_W_IN*2 + SPINE_W_IN + WRAP_IN*2  by
                        PANEL_H_IN + WRAP_IN*2
  Book trim (board):    PANEL_W_IN x PANEL_H_IN  (5.75" x 9")
  Spine width:          formula below — UPDATE WITH LULU'S EXACT VALUE
                        from the hardcover template before final upload.
  Wrap area:            0.625" past board edge, all four sides
  Safety margin:        0.625" inside the board edge
"""

from pathlib import Path

from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_The_Division_Lulu_Hardcover_CaseWrap.pdf"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic",
                                str(FONT_DIR / "EBGaramond-Italic.ttf")))

# ============================================================================
# DOCUMENT DIMENSIONS — Lulu hardcover case-wrap template for 5.5x8.5
# interior, 170 B&W white pages.
#
# WhyDoYouDelay reference: 88-page paperback spine 0.258" → hardcover
# spine 0.5"; the case-wrap adds ~0.242" of board thickness on top of
# the paperback spine. We carry the same offset forward as a starting
# estimate. Always update SPINE_W_IN to Lulu's exact value from the
# hardcover template tool before final upload.
# ============================================================================
PAGE_COUNT  = 170
PB_SPINE    = round(PAGE_COUNT * 0.0029, 3)
HC_OVERHEAD = 0.242                    # board-thickness add observed for WDYD
SPINE_W_IN  = round(PB_SPINE + HC_OVERHEAD, 3)

PANEL_W_IN  = 5.75
PANEL_H_IN  = 9.00
WRAP_IN     = 0.625
SAFETY_IN   = 0.625

DOC_W_IN    = PANEL_W_IN * 2 + SPINE_W_IN + WRAP_IN * 2
DOC_H_IN    = PANEL_H_IN + WRAP_IN * 2
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

BACK_CENTER_X  = (BACK_FACE_LEFT + BACK_FACE_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2
FRONT_CENTER_X = (FRONT_FACE_LEFT + FRONT_FACE_RIGHT) / 2

# Safety-inset bounds (text must stay inside)
FRONT_SAFE_LEFT   = FRONT_FACE_LEFT + SAFETY_IN * inch
FRONT_SAFE_RIGHT  = FRONT_FACE_RIGHT - SAFETY_IN * inch
FRONT_SAFE_BOTTOM = FACE_BOTTOM + SAFETY_IN * inch
FRONT_SAFE_TOP    = FACE_TOP - SAFETY_IN * inch

BACK_SAFE_LEFT    = BACK_FACE_LEFT + SAFETY_IN * inch
BACK_SAFE_RIGHT   = BACK_FACE_RIGHT - SAFETY_IN * inch
BACK_SAFE_BOTTOM  = FACE_BOTTOM + SAFETY_IN * inch
BACK_SAFE_TOP     = FACE_TOP - SAFETY_IN * inch

# ============================================================================
# COLORS — match the paperback palette
# ============================================================================
DEEP_GREEN   = Color(0.075, 0.137, 0.094)
FOREST       = Color(0.137, 0.224, 0.149)
SAGE_GLOW    = Color(0.227, 0.345, 0.243)
CREAM        = Color(0.965, 0.949, 0.890)
PAPER        = Color(0.945, 0.918, 0.847)
GOLD         = Color(0.749, 0.616, 0.310)
MUTED_GOLD   = Color(0.580, 0.475, 0.255)
SAGE         = Color(0.486, 0.561, 0.467)


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


def check_safe(label, x, y, side):
    if side == "front":
        l, r, b, t = (FRONT_SAFE_LEFT, FRONT_SAFE_RIGHT,
                      FRONT_SAFE_BOTTOM, FRONT_SAFE_TOP)
    else:
        l, r, b, t = (BACK_SAFE_LEFT, BACK_SAFE_RIGHT,
                      BACK_SAFE_BOTTOM, BACK_SAFE_TOP)
    inside = (l <= x <= r) and (b <= y <= t)
    print(f"  [{'OK' if inside else 'WARN'}] {label}: ({x/inch:.2f}, {y/inch:.2f})")


def draw_background(c):
    c.setFillColor(DEEP_GREEN)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def _draw_radial_glow(c, cx, cy, max_radius, color, steps=80, max_alpha=0.18):
    c.saveState()
    for i in range(steps, 0, -1):
        r = max_radius * (i / steps)
        alpha = max_alpha * (1 - i / steps) ** 1.5
        c.setFillColor(Color(color.red, color.green, color.blue, alpha))
        c.circle(cx, cy, r, stroke=0, fill=1)
    c.restoreState()


def draw_front_face(c):
    cx = FRONT_CENTER_X

    # Subtle glow above the title region
    _draw_radial_glow(c, cx, FACE_BOTTOM + PANEL_H_IN * inch * 0.65,
                      4.0 * inch, SAGE_GLOW, steps=60, max_alpha=0.13)

    # Inner border rule (gold)
    inset = 0.32 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.45)
    c.rect(FRONT_SAFE_LEFT - 0.18 * inch,
           FRONT_SAFE_BOTTOM - 0.18 * inch,
           FRONT_SAFE_RIGHT - FRONT_SAFE_LEFT + 0.36 * inch,
           FRONT_SAFE_TOP - FRONT_SAFE_BOTTOM + 0.36 * inch,
           fill=0, stroke=1)

    # Top fleuron + thin rule
    orn_y = FRONT_SAFE_TOP - 0.5 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 13)
    c.drawCentredString(cx, orn_y, "❦")
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.3)
    rule_hw = 0.6 * inch
    c.line(cx - rule_hw, orn_y - 12, cx - 0.15 * inch, orn_y - 12)
    c.line(cx + 0.15 * inch, orn_y - 12, cx + rule_hw, orn_y - 12)

    # Title — two lines
    title_top_y = FRONT_SAFE_TOP - 1.55 * inch
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 30)
    c.drawCentredString(cx, title_top_y, "Why the Division")
    c.setFont("EBGaramond-Italic", 30)
    c.drawCentredString(cx, title_top_y - 0.55 * inch, "Among Brethren?")

    # Decorative double rule
    rule_y = title_top_y - 1.05 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.45)
    rule_hw = 0.85 * inch
    c.line(cx - rule_hw, rule_y, cx + rule_hw, rule_y)
    c.setLineWidth(0.25)
    c.line(cx - rule_hw * 0.55, rule_y - 4,
           cx + rule_hw * 0.55, rule_y - 4)

    # Subtitle
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
        sub_y -= 0.28 * inch

    # Lower fleuron
    orn2_y = FRONT_SAFE_BOTTOM + 1.05 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 12)
    c.drawCentredString(cx, orn2_y, "❦")

    # Author
    author_y = FRONT_SAFE_BOTTOM + 0.5 * inch
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 14)
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")
    check_safe("Author", cx, author_y, "front")

    # Imprint
    imp_y = FRONT_SAFE_BOTTOM + 0.05 * inch
    c.setFillColor(MUTED_GOLD)
    c.setFont("EBGaramond-Italic", 9)
    c.drawCentredString(cx, imp_y, "NOBLEMIND PRESS")


def draw_spine(c):
    """Hardcover spine — wider than paperback, comfortable for vertical text."""
    c.setFillColor(FOREST)
    c.rect(SPINE_LEFT, 0, SPINE_W_IN * inch, DOC_H, fill=1, stroke=0)

    # Even at narrow widths the case-wrap spine sits between the two
    # board faces and reads more cleanly than a paperback's. We always
    # render text on the hardcover spine.
    c.saveState()
    # Title near the top-third of the spine, reading bottom-to-top.
    c.translate(SPINE_CENTER_X, FACE_TOP - 0.7 * inch)
    c.rotate(-90)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 12)
    c.drawString(0, -3, "Why the Division Among Brethren?")
    c.restoreState()

    # Author near the bottom-third, same direction
    c.saveState()
    c.translate(SPINE_CENTER_X, FACE_BOTTOM + 1.0 * inch)
    c.rotate(-90)
    c.setFillColor(MUTED_GOLD)
    c.setFont("EBGaramond-Italic", 10)
    c.drawString(0, -2.5, "Paul Hainline")
    c.restoreState()

    # Small fleuron at the geometric center of the spine
    c.saveState()
    c.translate(SPINE_CENTER_X, (FACE_TOP + FACE_BOTTOM) / 2)
    c.setFillColor(GOLD)
    c.setFont("EBGaramond", 11)
    c.drawCentredString(0, -3, "❦")
    c.restoreState()


def draw_back_face(c):
    cx = BACK_CENTER_X
    blurb_inset = 0.35 * inch
    safe_left = BACK_SAFE_LEFT + blurb_inset
    safe_right = BACK_SAFE_RIGHT - blurb_inset
    text_width = safe_right - safe_left

    # Inner border
    c.setStrokeColor(MUTED_GOLD)
    c.setLineWidth(0.4)
    c.rect(BACK_SAFE_LEFT - 0.18 * inch,
           BACK_SAFE_BOTTOM - 0.18 * inch,
           BACK_SAFE_RIGHT - BACK_SAFE_LEFT + 0.36 * inch,
           BACK_SAFE_TOP - BACK_SAFE_BOTTOM + 0.36 * inch,
           fill=0, stroke=1)

    # Thesis epigraph
    y = BACK_SAFE_TOP - 0.55 * inch
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

    # Thin rule
    y -= 18
    line_hw = 0.55 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 22

    # Body
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

    # Closing tag
    y -= line_height * 0.2
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(cx, y, "Read with the Book open.")

    # Attribution
    attr_y = BACK_SAFE_BOTTOM + 0.85 * inch
    c.setFillColor(SAGE)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(
        cx, attr_y,
        "Scripture quotations from the New American Standard Bible® (NASB).",
    )

    # Imprint
    mark_y = BACK_SAFE_BOTTOM + 0.25 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SAGE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")


def main():
    print('Generating Lulu HARDCOVER case-wrap PDF for '
          '"Why the Division Among Brethren?"...')
    print(f'  Document size: {DOC_W_IN}" x {DOC_H_IN}"')
    print(f'  Panel face size: {PANEL_W_IN}" x {PANEL_H_IN}"')
    print(f'  Spine width: {SPINE_W_IN:.3f}" (estimated; '
          'update with Lulu template value before final upload)')
    print(f'  Wrap: {WRAP_IN}" past board edge')
    print(f'  Safety: {SAFETY_IN}" inside board edge')
    print()
    print("Front-face safety check:")

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Why the Division Among Brethren? — Lulu Hardcover Case Wrap")

    draw_background(c)
    draw_back_face(c)
    draw_spine(c)
    draw_front_face(c)

    c.save()
    print(f"\nCase-wrap saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
