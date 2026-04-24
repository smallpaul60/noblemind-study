#!/usr/bin/env python3
"""Generate Lulu linen-hardcover DUST JACKET for 'Why Do You Delay?'.

Lulu specs (ESTIMATED pending Paul's Lulu template-tool confirmation):
  Document size:     19.300" x 9.25"  (will update to Lulu's exact)
  Spine width:       0.550"           (paperback 0.258" + ~0.29" boards)
  Front/back flap:   3.25"  x 9.25" each
  Flap fold width:   0.25" (between cover panel and flap, each side)
  Cover panel:       5.875" (5.5" trim + 0.375" wrap over the board edge)
  Height:            9.25" (8.5" trim + 0.375" wrap top + 0.375" wrap bottom)

Layout (left to right):
  [3.25 back flap][0.25 fold][5.875 back cover][SPINE]
  [5.875 front cover][0.25 fold][3.25 front flap]
  Current total: 3.25 + 0.25 + 5.875 + 0.550 + 5.875 + 0.25 + 3.25 = 19.300"

When Paul gets Lulu's exact hardcover template, update DOC_W_IN and
SPINE_W_IN below and rebuild.

Design matches the approved paperback: same cover art (upscaled for
print), white title over soft bottom vignette, cream subtitle and
gold decorative rule, PAUL HAINLINE at the bottom. Flaps carry a
teaser (front) and the author bio (back).
"""

from io import BytesIO
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_Do_You_Delay_Lulu_Hardcover_Jacket.pdf"
BG_IMAGE = BOOK_DIR / "why-do-you-delay-cover-image.png"

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# ============================================================================
# DOCUMENT DIMENSIONS — update SPINE_W_IN + DOC_W_IN from Lulu's template
# ============================================================================
DOC_H_IN   = 9.25
FLAP_W_IN  = 3.25
FOLD_W_IN  = 0.25
COVER_W_IN = 5.875
SPINE_W_IN = 0.550          # ESTIMATE — replace with Lulu's template value
DOC_W_IN   = 2*FLAP_W_IN + 2*FOLD_W_IN + 2*COVER_W_IN + SPINE_W_IN

DOC_W = DOC_W_IN * inch
DOC_H = DOC_H_IN * inch

# Horizontal layout anchors
BACK_FLAP_LEFT   = 0
BACK_FLAP_RIGHT  = FLAP_W_IN * inch
BACK_FOLD_LEFT   = BACK_FLAP_RIGHT
BACK_FOLD_RIGHT  = BACK_FOLD_LEFT + FOLD_W_IN * inch
BACK_COVER_LEFT  = BACK_FOLD_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + COVER_W_IN * inch
SPINE_LEFT       = BACK_COVER_RIGHT
SPINE_RIGHT      = SPINE_LEFT + SPINE_W_IN * inch
FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + COVER_W_IN * inch
FRONT_FOLD_LEFT  = FRONT_COVER_RIGHT
FRONT_FOLD_RIGHT = FRONT_FOLD_LEFT + FOLD_W_IN * inch
FRONT_FLAP_LEFT  = FRONT_FOLD_RIGHT
FRONT_FLAP_RIGHT = DOC_W

BACK_CENTER_X  = (BACK_COVER_LEFT + BACK_COVER_RIGHT) / 2
FRONT_CENTER_X = (FRONT_COVER_LEFT + FRONT_COVER_RIGHT) / 2
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

# ============================================================================
# COLORS — matched to the paperback cover's baptism-scene palette
# ============================================================================
DEEP_SHADOW = Color(0.075, 0.086, 0.059)   # #13160F near-black water
CANOPY_DARK = Color(0.165, 0.188, 0.110)   # #2A301C deep canopy
CREAM       = Color(0.961, 0.910, 0.804)   # #F5E8CD text cream
GOLD        = Color(0.776, 0.608, 0.337)   # #C69B56 warm gold accent
MUTED_GOLD  = Color(0.616, 0.490, 0.278)   # #9D7D47 subtle gold
SLATE       = Color(0.582, 0.561, 0.494)   # #948F7E muted stone
WHITE       = Color(1, 1, 1)

# Safety margins
COVER_SAFETY    = 0.5 * inch
FLAP_SAFETY     = 0.5 * inch
BACK_BLURB_INSET = 0.7 * inch
FLAP_VISUAL_SHIFT = 0.20 * inch
BACK_VISUAL_SHIFT = 0.10 * inch

# Upscale the source PNG so the embedded image reports >=200 PPI to
# Lulu's preflight — same approach as the paperback cover generator.
COVER_UPSCALE = 2


def _load_hires_cover():
    src = Image.open(str(BG_IMAGE)).convert("RGB")
    hires = src.resize(
        (src.width * COVER_UPSCALE, src.height * COVER_UPSCALE),
        Image.LANCZOS,
    )
    buf = BytesIO()
    hires.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return ImageReader(buf)


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


# ============================================================================
# PANELS
# ============================================================================

def draw_background(c):
    """Deep shadow fill — shows on spine and behind any image letterbox."""
    c.setFillColor(DEEP_SHADOW)
    c.rect(0, 0, DOC_W, DOC_H, fill=1, stroke=0)


def draw_front_cover(c):
    cx = FRONT_CENTER_X
    img = _load_hires_cover()
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h

    target_x = FRONT_COVER_LEFT
    target_w = FRONT_COVER_RIGHT - FRONT_COVER_LEFT
    target_h = DOC_H
    target_aspect = target_w / target_h

    if img_aspect > target_aspect:
        draw_h = target_h
        draw_w = target_h * img_aspect
        draw_x = cx - draw_w / 2
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

    # Top darkening so white title reads against the canopy
    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    top_band_h = 2.2 * inch
    tsteps = 220
    for i in range(tsteps):
        alpha = 0.58 * (1 - i / tsteps) ** 1.4
        c.setFillColor(Color(0.03, 0.05, 0.03, alpha))
        y = DOC_H - (top_band_h * i / tsteps) - 1
        h = top_band_h / tsteps + 1
        c.rect(target_x, y, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # Title: "Why Do You" (italic)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 24)
    c.drawCentredString(cx, DOC_H - 1.1 * inch, "Why Do You")

    # Title: "Delay?" (bold)
    c.setFont("EBGaramond", 46)
    c.drawCentredString(cx, DOC_H - 1.8 * inch, "Delay?")

    # Bottom wash for subtitle + author
    c.saveState()
    path = c.beginPath()
    path.rect(target_x, 0, target_w, DOC_H)
    path.close()
    c.clipPath(path, stroke=0)
    bot_band_h = 2.4 * inch
    bsteps = 260
    for i in range(bsteps):
        alpha = 0.62 * (i / bsteps) ** 1.3
        c.setFillColor(Color(0.02, 0.04, 0.03, alpha))
        y = bot_band_h * (1 - i / bsteps)
        h = bot_band_h / bsteps + 1
        c.rect(target_x, y - h, target_w, h, fill=1, stroke=0)
    c.restoreState()

    # Subtitle (two italic lines)
    c.setFillColor(CREAM)
    c.setFont("EBGaramond-Italic", 12.5)
    sub1_y = COVER_SAFETY + 1.05 * inch
    sub2_y = sub1_y - 0.26 * inch
    c.drawCentredString(cx, sub1_y, "Baptism, Salvation,")
    c.drawCentredString(cx, sub2_y, "and What the Bible Actually Says")

    # Decorative gold rule
    rule_y = COVER_SAFETY + 0.55 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    rule_hw = 0.55 * inch
    c.line(cx - rule_hw, rule_y, cx + rule_hw, rule_y)

    # Author
    c.setFillColor(CREAM)
    c.setFont("EBGaramond", 15)
    author_y = COVER_SAFETY + 0.2 * inch
    c.drawCentredString(cx, author_y, "P A U L   H A I N L I N E")


def draw_spine(c):
    # Narrow spine — leave blank like the paperback. Fill with canopy
    # dark so the spine reads as a clean edge between cover panels.
    c.setFillColor(CANOPY_DARK)
    c.rect(SPINE_LEFT, 0, SPINE_W_IN * inch, DOC_H, fill=1, stroke=0)


def draw_back_cover(c):
    safe_left  = BACK_COVER_LEFT + BACK_BLURB_INSET
    safe_right = BACK_COVER_RIGHT - BACK_BLURB_INSET
    text_width = safe_right - safe_left
    cx = BACK_CENTER_X + BACK_VISUAL_SHIFT

    # Opening verse (Acts 22:16) in gold
    y = DOC_H - 1.0 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, y,      "“Now why do you delay? Get up and be")
    y -= 15
    c.drawCentredString(cx, y,      "baptized, and wash away your sins,")
    y -= 15
    c.drawCentredString(cx, y,      "calling on His name.”")
    y -= 16
    c.setFont("EBGaramond", 9)
    c.drawCentredString(cx, y, "— Acts 22:16")
    y -= 12

    # Thin gold rule
    y -= 8
    line_hw = 0.55 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.4)
    c.line(cx - line_hw, y, cx + line_hw, y)
    y -= 22

    # Body
    c.setFillColor(CREAM)
    line_height = 13
    body_paragraphs = [
        "Is baptism really necessary?",
        "The question has been asked in churches, Bible studies, and living "
        "room conversations for generations. Every answer turns on what the "
        "Scriptures actually say.",
        "This book opens the New Testament and lets it speak. What the Lord "
        "and His apostles taught. What the early church did on the day of "
        "Pentecost and in every conversion after. The common objections, "
        "answered from the text rather than from tradition.",
        "Thirteen chapters across three parts, ending at the question "
        "Ananias asked Saul of Tarsus two thousand years ago — the same "
        "question that echoes through every page of the New Testament:",
        "“Why do you delay?”",
    ]
    for i, para in enumerate(body_paragraphs):
        lines = wrap_text(c, para, "EBGaramond", 9.5, text_width)
        is_emphasis = (i == 0 or i == len(body_paragraphs) - 1)
        if is_emphasis:
            c.setFont("EBGaramond-Italic", 10)
        else:
            c.setFont("EBGaramond", 9.5)
        for line in lines:
            c.drawCentredString(cx, y, line)
            y -= line_height
        y -= line_height * 0.35

    # Attribution
    y -= line_height * 0.2
    c.setFillColor(MUTED_GOLD)
    c.setFont("EBGaramond-Italic", 8)
    c.drawCentredString(
        cx, y,
        "Scripture quotations from the New American Standard Bible® (NASB)."
    )

    # Imprint
    mark_y = COVER_SAFETY + 0.5 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 11)
    c.drawCentredString(cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(cx, mark_y - 14, "noblemind.study")


def draw_front_flap(c):
    """Teaser / hook drawing the reader in."""
    safe_left  = FRONT_FLAP_LEFT + FLAP_SAFETY
    safe_right = FRONT_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (FRONT_FLAP_LEFT + FRONT_FLAP_RIGHT) / 2 - FLAP_VISUAL_SHIFT

    c.setFillColor(CREAM)
    y = DOC_H - 0.85 * inch
    line_height = 11

    opening = ("EBGaramond-Italic", 9.5,
        "The question has echoed through two thousand years of Christian "
        "conversation. It has divided families and churches. It has been "
        "answered with so many assumptions and so few Scriptures that "
        "honest readers wonder if an answer is even available anymore.")

    pivot = ("EBGaramond", 10,
        "It is.")

    second = ("EBGaramond", 9,
        "The New Testament speaks plainly on this — more plainly than "
        "on almost any other subject. The Lord gave a commission. The "
        "apostles carried it out. The early church followed the pattern in "
        "every recorded conversion. And the common objections, when "
        "actually tested against the text, dissolve.")

    pull_font, pull_size, pull_text = ("EBGaramond-Italic", 11,
        "Now why do you delay?")

    rest = [
        ("EBGaramond", 9,
            "Thirteen chapters. One question. The answer the apostles "
            "themselves would give, examined verse by verse, from the book "
            "that still settles the matter today."),
    ]

    for font, size, text in [opening, pivot, second]:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.5

    # Pull quote in gold
    y -= line_height * 0.3
    c.setFillColor(GOLD)
    c.setFont(pull_font, pull_size)
    c.drawCentredString(flap_cx, y, "“" + pull_text + "”")
    y -= line_height * 1.6
    c.setFillColor(CREAM)

    for font, size, text in rest:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.4


def draw_back_flap(c):
    """About the Author."""
    safe_left  = BACK_FLAP_LEFT + FLAP_SAFETY
    safe_right = BACK_FLAP_RIGHT - FLAP_SAFETY
    text_width = safe_right - safe_left
    flap_cx = (BACK_FLAP_LEFT + BACK_FLAP_RIGHT) / 2 + FLAP_VISUAL_SHIFT

    c.setFillColor(GOLD)
    y = DOC_H - 0.85 * inch
    c.setFont("EBGaramond-Italic", 12)
    c.drawCentredString(flap_cx, y, "About the Author")
    y -= 8

    c.setStrokeColor(GOLD)
    c.setLineWidth(0.4)
    rule_hw = 0.4 * inch
    c.line(flap_cx - rule_hw, y, flap_cx + rule_hw, y)
    y -= 20

    c.setFillColor(CREAM)
    line_height = 11.5
    paragraphs = [
        ("EBGaramond", 9,
            "Paul Hainline is a student of God’s Word who writes from "
            "the conviction that the Scriptures, rightly read, are clear "
            "enough to settle every essential question. Together with his "
            "wife Pam, he publishes books grounded in careful attention to "
            "the biblical text — books written to point readers back "
            "to the Scriptures themselves."),
        ("EBGaramond", 9,
            "He is the founder of NobleMind Press."),
    ]
    for font, size, text in paragraphs:
        lines = wrap_text(c, text, font, size, text_width)
        c.setFont(font, size)
        for line in lines:
            c.drawCentredString(flap_cx, y, line)
            y -= line_height
        y -= line_height * 0.4

    mark_y = COVER_SAFETY + 0.6 * inch
    c.setFillColor(GOLD)
    c.setFont("EBGaramond-Italic", 10)
    c.drawCentredString(flap_cx, mark_y, "NobleMind Press")
    c.setFillColor(SLATE)
    c.setFont("EBGaramond", 8)
    c.drawCentredString(flap_cx, mark_y - 12, "noblemind.study")


def main():
    print('Generating Lulu HARDCOVER JACKET PDF for "Why Do You Delay?"...')
    print(f'  Document size:  {DOC_W_IN:.3f}" x {DOC_H_IN}"')
    print(f'  Spine:          {SPINE_W_IN}" (ESTIMATE — verify with Lulu)')
    print(f'  Cover panel:    {COVER_W_IN}" x {DOC_H_IN}" each')
    print(f'  Flap:           {FLAP_W_IN}" x {DOC_H_IN}"   Fold: {FOLD_W_IN}"')
    print()
    print('  Panel x-positions (inches):')
    print(f'    back flap  : {BACK_FLAP_LEFT/inch:.3f} .. {BACK_FLAP_RIGHT/inch:.3f}')
    print(f'    back cover : {BACK_COVER_LEFT/inch:.3f} .. {BACK_COVER_RIGHT/inch:.3f}')
    print(f'    spine      : {SPINE_LEFT/inch:.3f} .. {SPINE_RIGHT/inch:.3f}')
    print(f'    front cover: {FRONT_COVER_LEFT/inch:.3f} .. {FRONT_COVER_RIGHT/inch:.3f}')
    print(f'    front flap : {FRONT_FLAP_LEFT/inch:.3f} .. {FRONT_FLAP_RIGHT/inch:.3f}')

    c = canvas.Canvas(str(OUTPUT), pagesize=(DOC_W, DOC_H))
    c.setTitle("Why Do You Delay? — Lulu Hardcover Jacket")

    draw_background(c)
    draw_front_cover(c)
    draw_spine(c)
    draw_back_cover(c)
    draw_front_flap(c)
    draw_back_flap(c)

    c.save()
    print(f"\nJacket saved to {OUTPUT}")
    print("Done.")


if __name__ == "__main__":
    main()
