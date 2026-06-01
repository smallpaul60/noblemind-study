#!/usr/bin/env python3
"""Generate PowerPoint-compatible mockups for the What Love Looks Like
wall installation typography.

Outputs to WhatLoveLooksLike/mockup/:
  - banner_what_love_looks_like.png   (36" x 8" @ 300 DPI)
  - panel-06_captioned.png            (existing panel + caption overlay)

These are review mockups so Paul can see the typography decision rendered
before committing. Charles will redo the final overlay in PowerPoint after
all 13 panels are generated.

Font: EB Garamond Regular + Italic (only weights available locally).
Color: deep navy #0C1F38 (the steady anchor against warm-tone panels).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BOOK_DIR = Path(__file__).parent
MOCK_DIR = BOOK_DIR / "mockup"
MOCK_DIR.mkdir(exist_ok=True)

FONT_DIR = Path.home() / ".local/share/fonts"
FONT_REGULAR = FONT_DIR / "EBGaramond.ttf"
FONT_ITALIC  = FONT_DIR / "EBGaramond-Italic.ttf"

# Palette
NAVY        = (12, 31, 56)     # #0C1F38 — text overlay anchor
GOLD        = (196, 168, 100)  # #C4A864 — thin decorative rule
BANNER_BG   = (245, 237, 218)  # #F5EDDA — warm cream banner backdrop

DPI = 300


def load(path, size):
    return ImageFont.truetype(str(path), size)


# ---------------------------------------------------------------------------
# BANNER  —  "What Love Looks Like" + 1 Corinthians 13:4-7
# ---------------------------------------------------------------------------

def build_banner():
    W = int(36.0 * DPI)   # 10800 px
    H = int(8.0  * DPI)   #  2400 px

    canvas = Image.new("RGB", (W, H), BANNER_BG)
    draw = ImageDraw.Draw(canvas)

    title_text = "WHAT  LOVE  LOOKS  LIKE"
    title_size = 500
    title_spacing = 30
    title_font = load(FONT_REGULAR, title_size)

    # Measure title with letter spacing
    widths = [draw.textbbox((0, 0), ch, font=title_font)[2] for ch in title_text]
    total_w = sum(widths) + title_spacing * (len(title_text) - 1)
    title_x = (W - total_w) // 2
    title_y = int(H * 0.18)
    x = title_x
    for ch, wch in zip(title_text, widths):
        draw.text((x, title_y), ch, font=title_font, fill=NAVY)
        x += wch + title_spacing

    # Thin gold rule (60% of title width)
    rule_y = title_y + title_size + int(0.55 * DPI)
    rule_w = int(total_w * 0.55)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, rule_y, rule_x + rule_w, rule_y + 6], fill=GOLD)

    # Verse reference — italic
    ref_text = "1 Corinthians 13:4–7"
    ref_size = 170
    ref_font = load(FONT_ITALIC, ref_size)
    rb = draw.textbbox((0, 0), ref_text, font=ref_font)
    ref_w = rb[2] - rb[0]
    ref_x = (W - ref_w) // 2
    ref_y = rule_y + int(0.55 * DPI)
    draw.text((ref_x, ref_y), ref_text, font=ref_font, fill=NAVY)

    out = MOCK_DIR / "banner_what_love_looks_like.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


# ---------------------------------------------------------------------------
# CAPTIONED PANEL  —  panel-06 with attribute + verse number overlay
# ---------------------------------------------------------------------------

def build_captioned_panel():
    src = BOOK_DIR / "print" / "love-does-not-seek-its-own.png"
    panel = Image.open(src).convert("RGB")
    W, H = panel.size   # 3300 x 2550 (11" x 8.5" landscape @ 300 DPI)
    draw = ImageDraw.Draw(panel)

    # FIXED CAPTION ANCHOR — every panel uses these exact coordinates so the
    # 13 panels line up across the wall. Left edge 0.6" in from the panel
    # edge, top of attribute line 0.45" down from the top edge.
    CAPTION_X = int(0.6 * DPI)
    CAPTION_Y = int(0.45 * DPI)

    # --- Attribute caption (italic, left-aligned at fixed anchor) ---
    attr_text = "Love does not seek its own…"
    attr_size = 200
    attr_font = load(FONT_ITALIC, attr_size)
    ab = draw.textbbox((0, 0), attr_text, font=attr_font)
    attr_w = ab[2] - ab[0]
    draw.text((CAPTION_X, CAPTION_Y), attr_text, font=attr_font, fill=NAVY)

    # --- Verse citation (faux small caps, centered beneath the attribute) ---
    cite_text = "1 CORINTHIANS 13:5"
    cite_size = 80
    cite_spacing = 12
    cite_font = load(FONT_REGULAR, cite_size)
    widths = [draw.textbbox((0, 0), ch, font=cite_font)[2] for ch in cite_text]
    cite_w = sum(widths) + cite_spacing * (len(cite_text) - 1)
    cite_y = CAPTION_Y + attr_size + int(0.04 * DPI)
    cite_cx = CAPTION_X + attr_w // 2
    x = cite_cx - cite_w // 2
    for ch, wch in zip(cite_text, widths):
        draw.text((x, cite_y), ch, font=cite_font, fill=NAVY)
        x += wch + cite_spacing

    out = MOCK_DIR / "panel-06_captioned.png"
    panel.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


# ---------------------------------------------------------------------------
# CENTERPIECE  —  Footwashing painting + book quote + 1 Cor 13:4-7
# ---------------------------------------------------------------------------

def _build_centerpiece(out_name, painting_width_in=12, stanza_gap_in=0.30,
                       paint_top_in=0.6, show_quote=True,
                       verse_size=80, cite_size=60):
    """22" x 28" portrait — sized as the wall's anchor piece.

    The footwashing image (TheLoveGodCallsUsTo/washing_feet_cover.png) fills
    the upper portion. Below it: a thin gold rule, the short book quote in
    italic navy, the book attribution in smaller italic, then the full verse
    in regular navy, then the citation in faux small caps.

    Parameterized so we can produce variants — v1 (original, 12" painting,
    generous gaps) and v2 (13.5" painting, tighter stanza gaps, painting
    dominates the frame more)."""
    W = int(22 * DPI)   # 6600
    H = int(28 * DPI)   # 8400

    canvas = Image.new("RGB", (W, H), BANNER_BG)
    draw = ImageDraw.Draw(canvas)

    # --- Painting ---
    src = BOOK_DIR.parent / "TheLoveGodCallsUsTo" / "washing_feet_cover.png"
    painting = Image.open(src).convert("RGB")
    pw, ph = painting.size

    target_w = int(painting_width_in * DPI)
    target_h = int(target_w * ph / pw)
    painting_resized = painting.resize((target_w, target_h), Image.LANCZOS)

    paint_x = (W - target_w) // 2
    paint_y = int(paint_top_in * DPI)
    canvas.paste(painting_resized, (paint_x, paint_y))

    # --- Gold rule below painting ---
    y = paint_y + target_h + int(0.45 * DPI)
    rule_w = int(0.32 * W)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, y, rule_x + rule_w, y + 10], fill=GOLD)
    y += int(0.45 * DPI)

    if show_quote:
        # --- Quote (italic, large, centered) ---
        quote_text = "“The Corinthian was puffed up. Christ took a towel.”"
        quote_size = 135
        quote_font = load(FONT_ITALIC, quote_size)
        qb = draw.textbbox((0, 0), quote_text, font=quote_font)
        qw = qb[2] - qb[0]
        draw.text(((W - qw) // 2, y), quote_text, font=quote_font, fill=NAVY)
        y += int(quote_size * 1.10) + int(0.10 * DPI)

        # --- Book attribution (smaller italic, centered) ---
        attr_text = "from The Love God Calls Us To"
        attr_size = 68
        attr_font = load(FONT_ITALIC, attr_size)
        ab = draw.textbbox((0, 0), attr_text, font=attr_font)
        aw = ab[2] - ab[0]
        draw.text(((W - aw) // 2, y), attr_text, font=attr_font, fill=NAVY)
        y += int(attr_size * 1.15) + int(0.45 * DPI)

    # --- Full verse (regular, broken into stanzas, centered) ---
    # Each stanza is its own grouping; small gap between stanzas, single-line
    # spacing within a stanza. The five stanzas mirror Paul's verse divisions.
    stanzas = [
        ["Love is patient, love is kind, and is not jealous;"],
        ["love does not brag and is not arrogant,",
         "does not act unbecomingly;"],
        ["it does not seek its own, is not provoked,",
         "does not take into account a wrong suffered;"],
        ["does not rejoice in unrighteousness,",
         "but rejoices with the truth;"],
        ["bears all things, believes all things,",
         "hopes all things, endures all things."],
    ]
    verse_font = load(FONT_REGULAR, verse_size)
    line_height = int(verse_size * 1.25)
    stanza_gap = int(stanza_gap_in * DPI)

    for i, stanza in enumerate(stanzas):
        for line in stanza:
            lb = draw.textbbox((0, 0), line, font=verse_font)
            lw = lb[2] - lb[0]
            draw.text(((W - lw) // 2, y), line, font=verse_font, fill=NAVY)
            y += line_height
        if i < len(stanzas) - 1:
            y += stanza_gap

    y += int(0.45 * DPI)

    # --- Citation (faux small caps, centered with letter spacing) ---
    cite_text = "1 CORINTHIANS 13:4–7  (NASB)"
    cite_spacing = max(6, int(cite_size * 0.15))
    cite_font = load(FONT_REGULAR, cite_size)
    widths = [draw.textbbox((0, 0), ch, font=cite_font)[2] for ch in cite_text]
    total = sum(widths) + cite_spacing * (len(cite_text) - 1)
    x = (W - total) // 2
    for ch, wch in zip(cite_text, widths):
        draw.text((x, y), ch, font=cite_font, fill=NAVY)
        x += wch + cite_spacing

    out = MOCK_DIR / out_name
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


def build_centerpiece():
    """Original: 12" wide painting, generous stanza gaps."""
    _build_centerpiece("centerpiece_footwashing.png",
                       painting_width_in=12, stanza_gap_in=0.30,
                       paint_top_in=0.6)


def build_centerpiece_v2():
    """Variant: 13.5" wide painting (more dominant), tighter stanza gaps."""
    _build_centerpiece("centerpiece_footwashing_v2.png",
                       painting_width_in=13.5, stanza_gap_in=0.20,
                       paint_top_in=0.5)


def build_centerpiece_v3():
    """Variant: same as v2, but drops the quote and book attribution, and
    enlarges the Scripture verse and citation to fill the reclaimed space.
    Scripture stands alone — no Paul-Hainline framing."""
    _build_centerpiece("centerpiece_footwashing_v3.png",
                       painting_width_in=13.5, stanza_gap_in=0.20,
                       paint_top_in=0.5,
                       show_quote=False,
                       verse_size=115, cite_size=85)


def build_centerpiece_v4():
    """Variant from Charles's feedback: same layout as v2, but replaces
    the book quote with John 13:5 — the actual Scripture for the scene —
    above the 1 Corinthians 13:4-7 stanzas. Two passages on one piece:
    the moment in John, the embodiment in 1 Corinthians."""
    W = int(22 * DPI)
    H = int(28 * DPI)

    canvas = Image.new("RGB", (W, H), BANNER_BG)
    draw = ImageDraw.Draw(canvas)

    # --- Painting ---
    src = BOOK_DIR.parent / "TheLoveGodCallsUsTo" / "washing_feet_cover.png"
    painting = Image.open(src).convert("RGB")
    pw, ph = painting.size
    target_w = int(13.5 * DPI)
    target_h = int(target_w * ph / pw)
    painting_resized = painting.resize((target_w, target_h), Image.LANCZOS)
    paint_x = (W - target_w) // 2
    paint_y = int(0.5 * DPI)
    canvas.paste(painting_resized, (paint_x, paint_y))

    # --- Gold rule ---
    y = paint_y + target_h + int(0.40 * DPI)
    rule_w = int(0.32 * W)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, y, rule_x + rule_w, y + 10], fill=GOLD)
    y += int(0.35 * DPI)

    # --- John 13:5 (italic, centered, wrapped) ---
    john_text = ("“Then He poured water into the basin, and began to wash the "
                 "disciples' feet and to wipe them with the towel with which "
                 "He was girded.”")
    john_size = 64
    john_font = load(FONT_ITALIC, john_size)
    john_max_w = int(18.5 * DPI)

    words = john_text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip() if current else word
        bb = draw.textbbox((0, 0), trial, font=john_font)
        if bb[2] - bb[0] <= john_max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    john_line_height = int(john_size * 1.30)
    for line in lines:
        lb = draw.textbbox((0, 0), line, font=john_font)
        lw = lb[2] - lb[0]
        draw.text(((W - lw) // 2, y), line, font=john_font, fill=NAVY)
        y += john_line_height

    # --- John 13:5 attribution (small caps style) ---
    y += int(0.05 * DPI)
    john_cite = "— JOHN 13:5"
    john_cite_size = 42
    john_cite_spacing = 6
    john_cite_font = load(FONT_REGULAR, john_cite_size)
    widths = [draw.textbbox((0, 0), ch, font=john_cite_font)[2] for ch in john_cite]
    total = sum(widths) + john_cite_spacing * (len(john_cite) - 1)
    x = (W - total) // 2
    for ch, wch in zip(john_cite, widths):
        draw.text((x, y), ch, font=john_cite_font, fill=NAVY)
        x += wch + john_cite_spacing
    y += john_cite_size + int(0.45 * DPI)

    # --- 1 Cor 13:4-7 stanzas ---
    stanzas = [
        ["Love is patient, love is kind, and is not jealous;"],
        ["love does not brag and is not arrogant,",
         "does not act unbecomingly;"],
        ["it does not seek its own, is not provoked,",
         "does not take into account a wrong suffered;"],
        ["does not rejoice in unrighteousness,",
         "but rejoices with the truth;"],
        ["bears all things, believes all things,",
         "hopes all things, endures all things."],
    ]
    verse_size = 64
    verse_font = load(FONT_REGULAR, verse_size)
    line_height = int(verse_size * 1.25)
    stanza_gap = int(0.16 * DPI)

    for i, stanza in enumerate(stanzas):
        for line in stanza:
            lb = draw.textbbox((0, 0), line, font=verse_font)
            lw = lb[2] - lb[0]
            draw.text(((W - lw) // 2, y), line, font=verse_font, fill=NAVY)
            y += line_height
        if i < len(stanzas) - 1:
            y += stanza_gap

    y += int(0.30 * DPI)

    # --- 1 Cor citation ---
    cite_text = "1 CORINTHIANS 13:4–7  (NASB)"
    cite_size = 48
    cite_spacing = 7
    cite_font = load(FONT_REGULAR, cite_size)
    widths = [draw.textbbox((0, 0), ch, font=cite_font)[2] for ch in cite_text]
    total = sum(widths) + cite_spacing * (len(cite_text) - 1)
    x = (W - total) // 2
    for ch, wch in zip(cite_text, widths):
        draw.text((x, y), ch, font=cite_font, fill=NAVY)
        x += wch + cite_spacing

    out = MOCK_DIR / "centerpiece_footwashing_v4.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


def build_banner_v2():
    """Variant from Charles's feedback: warm scenic background (a darkened
    crop of the footwashing painting), thicker/larger title pushed to the
    edges, half-inch black border for cut line and visual definition,
    text centered both axes."""
    W = int(36.0 * DPI)   # 10800 px
    H = int(8.0  * DPI)   #  2400 px
    BORDER_PX = int(0.5 * DPI)   # 150 px (= 0.5")

    canvas = Image.new("RGB", (W, H), (12, 31, 56))  # navy as base

    # --- Background: footwashing painting, scaled wide, heavily darkened ---
    src = BOOK_DIR.parent / "TheLoveGodCallsUsTo" / "washing_feet_cover.png"
    bg = Image.open(src).convert("RGB")
    bw, bh = bg.size
    # Scale painting so its height matches the banner; let it crop horizontally
    scale = H / bh
    new_w = int(bw * scale)
    new_h = H
    bg = bg.resize((new_w, new_h), Image.LANCZOS)
    # Center horizontally (the painting is taller than wide, so it'll be
    # quite narrow — we tile/extend rather than stretch). Easier: take the
    # painting tiled across the banner darkened.
    # Actually simplest: paste centered + fill remaining with the painting's
    # ambient warm color. Darken the painting heavily so text reads.
    from PIL import ImageEnhance
    bg = ImageEnhance.Brightness(bg).enhance(0.35)
    bg = ImageEnhance.Contrast(bg).enhance(0.85)

    # Tile the darkened painting horizontally across the banner
    x = (W - new_w) // 2
    canvas.paste(bg, (x, 0))
    # If the painting doesn't fill the full width, blur-extend the edges by
    # pasting darkened mirrored copies on either side
    if x > 0:
        # Left edge fill: a darker warm wash
        left_fill = Image.new("RGB", (x + 10, H), (24, 20, 14))
        canvas.paste(left_fill, (0, 0))
        # Right edge fill mirroring
        canvas.paste(left_fill, (W - x - 10, 0))

    # --- Additional dark overlay across the middle for text legibility ---
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, W, H], fill=(10, 6, 4, 110))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(canvas)

    # --- Black border (0.5" thick) — frame + cut line ---
    draw.rectangle([0, 0, W, BORDER_PX], fill=(0, 0, 0))                       # top
    draw.rectangle([0, H - BORDER_PX, W, H], fill=(0, 0, 0))                   # bottom
    draw.rectangle([0, 0, BORDER_PX, H], fill=(0, 0, 0))                       # left
    draw.rectangle([W - BORDER_PX, 0, W, H], fill=(0, 0, 0))                   # right

    # --- Title: thicker, edge-pushed, centered vertically ---
    inner_left = BORDER_PX + int(0.4 * DPI)   # 0.4" inside border
    inner_right = W - BORDER_PX - int(0.4 * DPI)
    inner_w = inner_right - inner_left
    inner_top = BORDER_PX
    inner_bot = H - BORDER_PX
    inner_h = inner_bot - inner_top

    title_text = "WHAT  LOVE  LOOKS  LIKE"
    title_size = 620
    # Try increasing letter spacing to push first/last letters to the edges
    title_font = load(FONT_REGULAR, title_size)
    widths = [draw.textbbox((0, 0), ch, font=title_font)[2] for ch in title_text]
    # Compute spacing to push title-block to fill inner_w (minus a touch of margin)
    target_total = int(inner_w * 0.97)
    base_total = sum(widths)
    n_gaps = len(title_text) - 1
    title_spacing = max(20, (target_total - base_total) // n_gaps)

    total_w = sum(widths) + title_spacing * n_gaps
    title_x = inner_left + (inner_w - total_w) // 2

    # Vertical block: title + gold rule + verse reference, centered together
    # Measure all heights first
    ref_text = "1 Corinthians 13:4–7"
    ref_size = 200
    ref_font = load(FONT_ITALIC, ref_size)
    rule_thickness = 8
    gap_above_rule = int(0.25 * DPI)
    gap_below_rule = int(0.30 * DPI)

    block_h = title_size + gap_above_rule + rule_thickness + gap_below_rule + ref_size
    block_y_start = inner_top + (inner_h - block_h) // 2

    # Title — fake bold via stroke
    title_y = block_y_start
    x = title_x
    for ch, wch in zip(title_text, widths):
        draw.text((x, title_y), ch, font=title_font, fill=CREAM,
                  stroke_width=6, stroke_fill=CREAM)
        x += wch + title_spacing

    # Gold rule below title
    rule_y = title_y + title_size + gap_above_rule
    rule_w = int(total_w * 0.55)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, rule_y, rule_x + rule_w, rule_y + rule_thickness],
                   fill=GOLD)

    # Verse reference — italic cream
    ref_y = rule_y + rule_thickness + gap_below_rule
    rb = draw.textbbox((0, 0), ref_text, font=ref_font)
    ref_w = rb[2] - rb[0]
    ref_x = (W - ref_w) // 2
    draw.text((ref_x, ref_y), ref_text, font=ref_font, fill=CREAM,
              stroke_width=3, stroke_fill=CREAM)

    out = MOCK_DIR / "banner_what_love_looks_like_v2.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


# Need to add CREAM constant for banner_v2 (was hardcoded inside _build_centerpiece)
CREAM = (245, 237, 218)


def build_banner_v3():
    """V3 banner per Charles's feedback: real scenic mountain background
    (mountain-banner.png), heavier/larger title, first and last letters
    pushed to the edges, centered both axes, 0.5\" black border for the
    cut line. Uses the same title + verse-reference layout as V2."""
    from PIL import ImageEnhance
    W = int(36.0 * DPI)   # 10800
    H = int(8.0  * DPI)   #  2400
    BORDER_PX = int(0.5 * DPI)

    canvas = Image.new("RGB", (W, H), (20, 14, 8))

    # --- Background: mountain scenic, center-cropped to 4.5:1 then scaled ---
    src = BOOK_DIR / "mountain-banner.png"
    bg = Image.open(src).convert("RGB")
    bw, bh = bg.size
    target_aspect = W / H
    src_aspect = bw / bh
    if src_aspect > target_aspect:
        # Wider than target — center-crop horizontally
        new_bw = int(bh * target_aspect)
        x0 = (bw - new_bw) // 2
        bg = bg.crop((x0, 0, x0 + new_bw, bh))
    elif src_aspect < target_aspect:
        # Taller than target — center-crop vertically
        new_bh = int(bw / target_aspect)
        y0 = (bh - new_bh) // 2
        bg = bg.crop((0, y0, bw, y0 + new_bh))
    bg = bg.resize((W, H), Image.LANCZOS)

    # Gentle darkening so cream text reads cleanly against the scenic
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    canvas.paste(bg, (0, 0))

    # Soft dark overlay tilted to keep the central title area readable
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, W, H], fill=(10, 6, 4, 60))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(canvas)

    # --- Black 0.5" border (cut line + visual frame) ---
    draw.rectangle([0, 0, W, BORDER_PX], fill=(0, 0, 0))
    draw.rectangle([0, H - BORDER_PX, W, H], fill=(0, 0, 0))
    draw.rectangle([0, 0, BORDER_PX, H], fill=(0, 0, 0))
    draw.rectangle([W - BORDER_PX, 0, W, H], fill=(0, 0, 0))

    # --- Inner work area ---
    inner_left = BORDER_PX + int(0.4 * DPI)
    inner_right = W - BORDER_PX - int(0.4 * DPI)
    inner_w = inner_right - inner_left
    inner_top = BORDER_PX
    inner_bot = H - BORDER_PX
    inner_h = inner_bot - inner_top

    # --- Title: heavier, edge-pushed, vertically centered with verse ref ---
    title_text = "WHAT  LOVE  LOOKS  LIKE"
    title_size = 620
    title_font = load(FONT_REGULAR, title_size)
    widths = [draw.textbbox((0, 0), ch, font=title_font)[2] for ch in title_text]
    target_total = int(inner_w * 0.97)
    base_total = sum(widths)
    n_gaps = len(title_text) - 1
    title_spacing = max(20, (target_total - base_total) // n_gaps)
    total_w = sum(widths) + title_spacing * n_gaps
    title_x = inner_left + (inner_w - total_w) // 2

    # Verse reference setup
    ref_text = "1 Corinthians 13:4–7"
    ref_size = 200
    ref_font = load(FONT_ITALIC, ref_size)
    rule_thickness = 8
    gap_above_rule = int(0.25 * DPI)
    gap_below_rule = int(0.30 * DPI)

    block_h = title_size + gap_above_rule + rule_thickness + gap_below_rule + ref_size
    block_y_start = inner_top + (inner_h - block_h) // 2

    # Title with fake-bold stroke for added weight
    title_y = block_y_start
    x = title_x
    for ch, wch in zip(title_text, widths):
        draw.text((x, title_y), ch, font=title_font, fill=CREAM,
                  stroke_width=6, stroke_fill=CREAM)
        x += wch + title_spacing

    # Gold rule below title
    rule_y = title_y + title_size + gap_above_rule
    rule_w = int(total_w * 0.55)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, rule_y, rule_x + rule_w, rule_y + rule_thickness],
                   fill=GOLD)

    # Verse reference
    ref_y = rule_y + rule_thickness + gap_below_rule
    rb = draw.textbbox((0, 0), ref_text, font=ref_font)
    ref_w = rb[2] - rb[0]
    ref_x = (W - ref_w) // 2
    draw.text((ref_x, ref_y), ref_text, font=ref_font, fill=CREAM,
              stroke_width=3, stroke_fill=CREAM)

    out = MOCK_DIR / "banner_what_love_looks_like_v3.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


def build_banner_v4():
    """V4 banner per Paul's feedback on V3: skip the dark overlay (the
    sky is already light) and switch to navy text instead of cream. The
    title gets thinner stroke since navy on light sky doesn't need the
    fake-bold weight cream-on-dark required."""
    W = int(36.0 * DPI)
    H = int(8.0  * DPI)
    BORDER_PX = int(0.5 * DPI)

    canvas = Image.new("RGB", (W, H), (200, 180, 140))   # warm fallback

    # --- Background: mountain scenic, center-cropped to 4.5:1, UNDARKENED ---
    src = BOOK_DIR / "mountain-banner.png"
    bg = Image.open(src).convert("RGB")
    bw, bh = bg.size
    target_aspect = W / H
    src_aspect = bw / bh
    if src_aspect > target_aspect:
        new_bw = int(bh * target_aspect)
        x0 = (bw - new_bw) // 2
        bg = bg.crop((x0, 0, x0 + new_bw, bh))
    elif src_aspect < target_aspect:
        new_bh = int(bw / target_aspect)
        y0 = (bh - new_bh) // 2
        bg = bg.crop((0, y0, bw, y0 + new_bh))
    bg = bg.resize((W, H), Image.LANCZOS)
    canvas.paste(bg, (0, 0))

    draw = ImageDraw.Draw(canvas)

    # --- Black 0.5" border ---
    draw.rectangle([0, 0, W, BORDER_PX], fill=(0, 0, 0))
    draw.rectangle([0, H - BORDER_PX, W, H], fill=(0, 0, 0))
    draw.rectangle([0, 0, BORDER_PX, H], fill=(0, 0, 0))
    draw.rectangle([W - BORDER_PX, 0, W, H], fill=(0, 0, 0))

    # --- Inner work area ---
    inner_left = BORDER_PX + int(0.4 * DPI)
    inner_right = W - BORDER_PX - int(0.4 * DPI)
    inner_w = inner_right - inner_left
    inner_top = BORDER_PX
    inner_bot = H - BORDER_PX
    inner_h = inner_bot - inner_top

    # --- Title with navy fill + light stroke for some weight ---
    title_text = "WHAT  LOVE  LOOKS  LIKE"
    title_size = 620
    title_font = load(FONT_REGULAR, title_size)
    widths = [draw.textbbox((0, 0), ch, font=title_font)[2] for ch in title_text]
    target_total = int(inner_w * 0.97)
    base_total = sum(widths)
    n_gaps = len(title_text) - 1
    title_spacing = max(20, (target_total - base_total) // n_gaps)
    total_w = sum(widths) + title_spacing * n_gaps
    title_x = inner_left + (inner_w - total_w) // 2

    ref_text = "1 Corinthians 13:4–7"
    ref_size = 200
    ref_font = load(FONT_ITALIC, ref_size)
    rule_thickness = 8
    gap_above_rule = int(0.25 * DPI)
    gap_below_rule = int(0.30 * DPI)

    block_h = title_size + gap_above_rule + rule_thickness + gap_below_rule + ref_size
    block_y_start = inner_top + (inner_h - block_h) // 2

    title_y = block_y_start
    x = title_x
    for ch, wch in zip(title_text, widths):
        draw.text((x, title_y), ch, font=title_font, fill=NAVY,
                  stroke_width=3, stroke_fill=NAVY)
        x += wch + title_spacing

    rule_y = title_y + title_size + gap_above_rule
    rule_w = int(total_w * 0.55)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, rule_y, rule_x + rule_w, rule_y + rule_thickness],
                   fill=GOLD)

    ref_y = rule_y + rule_thickness + gap_below_rule
    rb = draw.textbbox((0, 0), ref_text, font=ref_font)
    ref_w = rb[2] - rb[0]
    ref_x = (W - ref_w) // 2
    draw.text((ref_x, ref_y), ref_text, font=ref_font, fill=NAVY,
              stroke_width=1, stroke_fill=NAVY)

    out = MOCK_DIR / "banner_what_love_looks_like_v4.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


def build_banner_v5():
    """V5 banner per Charles + Paul's feedback on V4: add the actual
    1 Cor 13:4-7 verse text between the title and the reference, with
    the title bumped higher so the verse fits comfortably below.

    Five semantic-clause lines (NASB 1995), navy regular, 200pt — ~0.47"
    cap-height, comfortable for intentional reading at 10 feet, which is
    what a classroom is. Title shrunk from V4's 620pt to 480pt (~1.12"
    cap-height) to make room while staying dominant from across the
    room. Same scenic background, same black border, same navy + gold
    palette as V4.
    """
    W = int(36.0 * DPI)
    H = int(8.0  * DPI)
    BORDER_PX = int(0.5 * DPI)

    canvas = Image.new("RGB", (W, H), (200, 180, 140))

    # --- Background: mountain scenic, center-cropped, UNDARKENED ---
    src = BOOK_DIR / "mountain-banner.png"
    bg = Image.open(src).convert("RGB")
    bw, bh = bg.size
    target_aspect = W / H
    src_aspect = bw / bh
    if src_aspect > target_aspect:
        new_bw = int(bh * target_aspect)
        x0 = (bw - new_bw) // 2
        bg = bg.crop((x0, 0, x0 + new_bw, bh))
    elif src_aspect < target_aspect:
        new_bh = int(bw / target_aspect)
        y0 = (bh - new_bh) // 2
        bg = bg.crop((0, y0, bw, y0 + new_bh))
    bg = bg.resize((W, H), Image.LANCZOS)
    canvas.paste(bg, (0, 0))

    draw = ImageDraw.Draw(canvas)

    # --- Black 0.5" border ---
    draw.rectangle([0, 0, W, BORDER_PX], fill=(0, 0, 0))
    draw.rectangle([0, H - BORDER_PX, W, H], fill=(0, 0, 0))
    draw.rectangle([0, 0, BORDER_PX, H], fill=(0, 0, 0))
    draw.rectangle([W - BORDER_PX, 0, W, H], fill=(0, 0, 0))

    # --- Inner work area ---
    inner_left = BORDER_PX + int(0.4 * DPI)
    inner_right = W - BORDER_PX - int(0.4 * DPI)
    inner_w = inner_right - inner_left
    inner_top = BORDER_PX
    inner_bot = H - BORDER_PX

    # --- Title — navy, bumped high near top border ---
    title_text = "WHAT  LOVE  LOOKS  LIKE"
    title_size = 480
    title_font = load(FONT_REGULAR, title_size)
    widths = [draw.textbbox((0, 0), ch, font=title_font)[2] for ch in title_text]
    target_total = int(inner_w * 0.95)
    base_total = sum(widths)
    n_gaps = len(title_text) - 1
    title_spacing = max(20, (target_total - base_total) // n_gaps)
    total_w = sum(widths) + title_spacing * n_gaps
    title_x = inner_left + (inner_w - total_w) // 2

    top_pad = int(0.20 * DPI)   # 60px breathing room from the top border
    title_y = inner_top + top_pad
    x = title_x
    for ch, wch in zip(title_text, widths):
        draw.text((x, title_y), ch, font=title_font, fill=NAVY,
                  stroke_width=2, stroke_fill=NAVY)
        x += wch + title_spacing

    # --- Gold rule beneath title ---
    gap_above_rule = int(0.16 * DPI)
    rule_thickness = 8
    rule_y = title_y + title_size + gap_above_rule
    rule_w = int(total_w * 0.55)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, rule_y, rule_x + rule_w, rule_y + rule_thickness],
                   fill=GOLD)

    # --- Verse body — 5 semantic-clause lines, NASB 1995 ---
    verse_lines = [
        "Love is patient, love is kind and is not jealous;",
        "love does not brag and is not arrogant, does not act unbecomingly;",
        "it does not seek its own, is not provoked, does not take into account a wrong suffered,",
        "does not rejoice in unrighteousness, but rejoices with the truth;",
        "bears all things, believes all things, hopes all things, endures all things.",
    ]
    verse_size = 200
    verse_font = load(FONT_REGULAR, verse_size)
    verse_line_height = int(verse_size * 1.22)

    gap_below_rule = int(0.23 * DPI)
    verse_y = rule_y + rule_thickness + gap_below_rule
    for line in verse_lines:
        lb = draw.textbbox((0, 0), line, font=verse_font)
        lw = lb[2] - lb[0]
        draw.text(((W - lw) // 2, verse_y), line, font=verse_font, fill=NAVY)
        verse_y += verse_line_height

    # --- Reference — italic navy ---
    ref_text = "1 Corinthians 13:4–7"
    ref_size = 140
    ref_font = load(FONT_ITALIC, ref_size)
    gap_above_ref = int(0.12 * DPI)
    ref_y = verse_y + gap_above_ref
    rb = draw.textbbox((0, 0), ref_text, font=ref_font)
    ref_w = rb[2] - rb[0]
    ref_x = (W - ref_w) // 2
    draw.text((ref_x, ref_y), ref_text, font=ref_font, fill=NAVY)

    # --- Bottom-overflow safety check ---
    bottom_edge = ref_y + ref_size
    overflow = bottom_edge - inner_bot
    if overflow > 0:
        print(f"  WARNING: content overflows inner area by {overflow}px")

    out = MOCK_DIR / "banner_what_love_looks_like_v5.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


def build_banner_v5a():
    """V5a: V5 with a soft cream-vellum overlay behind the verse + ref.

    Problem from V5: navy verse text lost contrast against the darker
    silhouetted mountains in the lower half of the banner. Lines 1-2
    read crisply on light sky; lines 3-5 + the reference fell on the
    dark band and demanded effort at 10ft.

    Fix: drop a translucent cream rectangle (the same BANNER_BG warm
    cream used elsewhere, at ~67% opacity) behind the verse stanza
    + reference. Mountains stay visible behind the title and around
    the panel edges; the verse area gets the cream "page" navy
    serif type was made for.
    """
    W = int(36.0 * DPI)
    H = int(8.0  * DPI)
    BORDER_PX = int(0.5 * DPI)

    canvas = Image.new("RGB", (W, H), (200, 180, 140))

    # --- Background: mountain scenic, center-cropped, UNDARKENED ---
    src = BOOK_DIR / "mountain-banner.png"
    bg = Image.open(src).convert("RGB")
    bw, bh = bg.size
    target_aspect = W / H
    src_aspect = bw / bh
    if src_aspect > target_aspect:
        new_bw = int(bh * target_aspect)
        x0 = (bw - new_bw) // 2
        bg = bg.crop((x0, 0, x0 + new_bw, bh))
    elif src_aspect < target_aspect:
        new_bh = int(bw / target_aspect)
        y0 = (bh - new_bh) // 2
        bg = bg.crop((0, y0, bw, y0 + new_bh))
    bg = bg.resize((W, H), Image.LANCZOS)
    canvas.paste(bg, (0, 0))

    draw = ImageDraw.Draw(canvas)

    # --- Black 0.5" border ---
    draw.rectangle([0, 0, W, BORDER_PX], fill=(0, 0, 0))
    draw.rectangle([0, H - BORDER_PX, W, H], fill=(0, 0, 0))
    draw.rectangle([0, 0, BORDER_PX, H], fill=(0, 0, 0))
    draw.rectangle([W - BORDER_PX, 0, W, H], fill=(0, 0, 0))

    # --- Inner work area ---
    inner_left = BORDER_PX + int(0.4 * DPI)
    inner_right = W - BORDER_PX - int(0.4 * DPI)
    inner_w = inner_right - inner_left
    inner_top = BORDER_PX
    inner_bot = H - BORDER_PX

    # --- Title — navy, bumped high near top border ---
    title_text = "WHAT  LOVE  LOOKS  LIKE"
    title_size = 480
    title_font = load(FONT_REGULAR, title_size)
    widths = [draw.textbbox((0, 0), ch, font=title_font)[2] for ch in title_text]
    target_total = int(inner_w * 0.95)
    base_total = sum(widths)
    n_gaps = len(title_text) - 1
    title_spacing = max(20, (target_total - base_total) // n_gaps)
    total_w = sum(widths) + title_spacing * n_gaps
    title_x = inner_left + (inner_w - total_w) // 2

    top_pad = int(0.20 * DPI)
    title_y = inner_top + top_pad
    x = title_x
    for ch, wch in zip(title_text, widths):
        draw.text((x, title_y), ch, font=title_font, fill=NAVY,
                  stroke_width=2, stroke_fill=NAVY)
        x += wch + title_spacing

    # --- Gold rule beneath title ---
    gap_above_rule = int(0.16 * DPI)
    rule_thickness = 8
    rule_y = title_y + title_size + gap_above_rule
    rule_w = int(total_w * 0.55)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, rule_y, rule_x + rule_w, rule_y + rule_thickness],
                   fill=GOLD)

    # --- Compute verse layout (positions only, draw later on top of vellum) ---
    verse_lines = [
        "Love is patient, love is kind and is not jealous;",
        "love does not brag and is not arrogant, does not act unbecomingly;",
        "it does not seek its own, is not provoked, does not take into account a wrong suffered,",
        "does not rejoice in unrighteousness, but rejoices with the truth;",
        "bears all things, believes all things, hopes all things, endures all things.",
    ]
    verse_size = 200
    verse_font = load(FONT_REGULAR, verse_size)
    verse_line_height = int(verse_size * 1.22)

    gap_below_rule = int(0.23 * DPI)
    verse_y_start = rule_y + rule_thickness + gap_below_rule
    verse_y_end = verse_y_start + verse_line_height * len(verse_lines)

    # --- Compute reference layout (positions only) ---
    ref_text = "1 Corinthians 13:4–7"
    ref_size = 140
    ref_font = load(FONT_ITALIC, ref_size)
    gap_above_ref = int(0.12 * DPI)
    ref_y = verse_y_end + gap_above_ref
    rb = draw.textbbox((0, 0), ref_text, font=ref_font)
    ref_w = rb[2] - rb[0]
    ref_x = (W - ref_w) // 2

    # --- Vellum overlay: translucent cream behind verse + ref ---
    # Width: hugs the longest verse line + generous side padding (so the
    # overlay reads as a deliberate panel, not a tight box). Centered.
    longest_line_w = max(
        draw.textbbox((0, 0), line, font=verse_font)[2] for line in verse_lines
    )
    vellum_pad_x = int(0.5 * DPI)
    vellum_pad_top = int(0.15 * DPI)
    vellum_pad_bot = int(0.10 * DPI)
    vellum_left  = (W - longest_line_w) // 2 - vellum_pad_x
    vellum_right = (W + longest_line_w) // 2 + vellum_pad_x
    vellum_top   = verse_y_start - vellum_pad_top
    vellum_bot   = ref_y + ref_size + vellum_pad_bot

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [vellum_left, vellum_top, vellum_right, vellum_bot],
        fill=(BANNER_BG[0], BANNER_BG[1], BANNER_BG[2], 175),  # ~69% opacity
    )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # --- Verse body — draw on top of vellum ---
    verse_y = verse_y_start
    for line in verse_lines:
        lb = draw.textbbox((0, 0), line, font=verse_font)
        lw = lb[2] - lb[0]
        draw.text(((W - lw) // 2, verse_y), line, font=verse_font, fill=NAVY)
        verse_y += verse_line_height

    # --- Reference — italic navy on the vellum ---
    draw.text((ref_x, ref_y), ref_text, font=ref_font, fill=NAVY)

    # --- Bottom-overflow safety check ---
    bottom_edge = vellum_bot
    overflow = bottom_edge - inner_bot
    if overflow > 0:
        print(f"  WARNING: vellum overflows inner area by {overflow}px")

    out = MOCK_DIR / "banner_what_love_looks_like_v5a.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes)")


def build_centerpiece_v5():
    """Variant from Paul's request: keep V4's John 13:5 quote, drop the
    1 Cor 13:4-7 stanzas, reframe on a standard 18x24 portrait canvas
    (common print-and-frame size) with a thin navy border inset from
    the edge to suggest a mat-and-frame treatment ready for hanging.
    Content vertically centered inside the border."""
    W = int(18 * DPI)   # 5400
    H = int(24 * DPI)   # 7200

    canvas = Image.new("RGB", (W, H), BANNER_BG)
    draw = ImageDraw.Draw(canvas)

    # --- Frame border (thin navy, inset from edge like a mat line) ---
    border_inset = int(0.25 * DPI)
    border_thickness = 6
    draw.rectangle(
        [border_inset, border_inset, W - border_inset, H - border_inset],
        outline=NAVY, width=border_thickness,
    )

    # --- Pre-measure all content blocks so we can center vertically ---
    src = BOOK_DIR.parent / "TheLoveGodCallsUsTo" / "washing_feet_cover.png"
    painting = Image.open(src).convert("RGB")
    pw, ph = painting.size
    target_w = int(13.5 * DPI)
    target_h = int(target_w * ph / pw)
    painting_resized = painting.resize((target_w, target_h), Image.LANCZOS)

    gap_above_rule = int(0.40 * DPI)
    rule_thickness = 10
    gap_below_rule = int(0.40 * DPI)

    john_text = ("“Then He poured water into the basin, and began to wash the "
                 "disciples' feet and to wipe them with the towel with which "
                 "He was girded.”")
    john_size = 70
    john_font = load(FONT_ITALIC, john_size)
    john_max_w = int(14 * DPI)
    words = john_text.split()
    john_lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip() if current else word
        bb = draw.textbbox((0, 0), trial, font=john_font)
        if bb[2] - bb[0] <= john_max_w:
            current = trial
        else:
            if current:
                john_lines.append(current)
            current = word
    if current:
        john_lines.append(current)
    john_line_height = int(john_size * 1.30)
    john_block_height = john_line_height * len(john_lines)

    gap_before_cite = int(0.10 * DPI)
    john_cite_size = 46
    john_cite_spacing = 7

    content_height = (target_h + gap_above_rule + rule_thickness +
                      gap_below_rule + john_block_height +
                      gap_before_cite + john_cite_size)
    top_margin = (H - content_height) // 2

    # --- Place painting (centered horizontally) ---
    paint_x = (W - target_w) // 2
    paint_y = top_margin
    canvas.paste(painting_resized, (paint_x, paint_y))

    # --- Gold rule ---
    y = paint_y + target_h + gap_above_rule
    rule_w = int(0.40 * W)
    rule_x = (W - rule_w) // 2
    draw.rectangle([rule_x, y, rule_x + rule_w, y + rule_thickness], fill=GOLD)
    y += rule_thickness + gap_below_rule

    # --- John 13:5 (italic, centered) ---
    for line in john_lines:
        lb = draw.textbbox((0, 0), line, font=john_font)
        lw = lb[2] - lb[0]
        draw.text(((W - lw) // 2, y), line, font=john_font, fill=NAVY)
        y += john_line_height

    # --- John 13:5 citation (faux small caps, centered) ---
    y += gap_before_cite
    john_cite = "— JOHN 13:5  (NASB)"
    john_cite_font = load(FONT_REGULAR, john_cite_size)
    widths = [draw.textbbox((0, 0), ch, font=john_cite_font)[2] for ch in john_cite]
    total = sum(widths) + john_cite_spacing * (len(john_cite) - 1)
    x = (W - total) // 2
    for ch, wch in zip(john_cite, widths):
        draw.text((x, y), ch, font=john_cite_font, fill=NAVY)
        x += wch + john_cite_spacing

    out = MOCK_DIR / "centerpiece_footwashing_v5.png"
    canvas.save(out, "PNG", optimize=True)
    print(f"Wrote {out.relative_to(BOOK_DIR)}  ({W}x{H}, {out.stat().st_size:,} bytes) "
          f"— content centered with {top_margin/DPI:.2f}\" margins top + bottom")


def main():
    print("Generating What Love Looks Like typography mockups...")
    build_banner()
    build_banner_v2()
    build_banner_v3()
    build_captioned_panel()
    build_centerpiece()
    build_centerpiece_v2()
    build_centerpiece_v3()
    build_centerpiece_v4()
    build_centerpiece_v5()
    print("\nDone. Open the files in WhatLoveLooksLike/mockup/ to review.")


if __name__ == "__main__":
    main()
