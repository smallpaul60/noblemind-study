#!/usr/bin/env python3
"""Apply the attribute + verse caption to every print-ready panel.

Uses the typography template approved on panel 6:
  - Attribute text: italic EB Garamond 200pt, navy, left-aligned at the
    fixed anchor (0.6" from left edge, 0.45" from top edge)
  - Verse citation: faux small caps EB Garamond 80pt, navy, centered
    horizontally beneath the attribute text (centered against the widest
    line of the attribute when multi-line)
  - Same physical font size on every panel, landscape or portrait, so
    captions read as one design language across the wall

Source: WhatLoveLooksLike/print/<name>.png  (the resized 11x8.5 or 8.5x11
        300 DPI panels)
Output: WhatLoveLooksLike/captioned/<name>.png

Panel 9 (diptych on the v6 antithesis) and panel 4 (brag + arrogant
combined) get two-line attribute treatments; the citation centers under
the widest line of the block.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BOOK_DIR = Path(__file__).parent
SOURCE_DIR = BOOK_DIR / "print"
OUT_DIR = BOOK_DIR / "captioned"
OUT_DIR.mkdir(exist_ok=True)

FONT_DIR = Path.home() / ".local/share/fonts"
FONT_REGULAR = FONT_DIR / "EBGaramond.ttf"
FONT_ITALIC  = FONT_DIR / "EBGaramond-Italic.ttf"

NAVY = (12, 31, 56)        # #0C1F38 — text overlay anchor
CREAM_BG = (245, 237, 218) # #F5EDDA — semi-transparent backplate cream
DPI = 300

# Default anchor coordinates — most panels share these so the wall lines up.
DEFAULT_CAPTION_X = int(0.6 * DPI)   # 180 px
DEFAULT_CAPTION_Y = int(0.45 * DPI)  # 135 px

ATTR_SIZE = 200
ATTR_LINE_HEIGHT = int(ATTR_SIZE * 1.15)   # 230 px between multi-line attribute lines

CITE_SIZE = 80
CITE_SPACING = 12     # extra px between each char for faux small-caps look
CITE_GAP_BELOW_ATTR = int(0.04 * DPI)   # 12 px below bottom of attribute

# ---------------------------------------------------------------------------
# PANEL CATALOG  —  source filename, attribute line(s), verse citation
# ---------------------------------------------------------------------------

# Each entry: (filename, attribute_lines, citation, **per-panel overrides)
# Available overrides:
#   anchor_right=True     — align caption to upper-right corner instead of left
#   backplate=True        — draw a semi-transparent cream rectangle behind the
#                            caption (for use over busy backgrounds like branches)
PANELS = [
    ("love-is-patient.png",
     ["Love is patient…"],
     "1 CORINTHIANS 13:4", {"backplate": True}),

    ("love-is-kind.png",
     ["Love is kind…"],
     "1 CORINTHIANS 13:4", {"backplate": True}),

    ("love-is-not-jealous.png",
     ["Love is not jealous…"],
     "1 CORINTHIANS 13:4", {"backplate": True}),

    ("love-does-not-brag.png",
     ["Love does not brag",
      "and is not arrogant…"],
     "1 CORINTHIANS 13:4", {"anchor_right": True, "backplate": True}),

    ("love-does-not-act-unbecomingly.png",
     ["Love does not act unbecomingly…"],
     "1 CORINTHIANS 13:5",
     {"attr_size": 180, "cite_size": 72, "caption_y_in": 0.10, "backplate": True}),
    # replaced 2026-07-26 with a portrait cafeteria source. 180pt is the largest
    # size at which this attribute line still fits a 2550-wide panel (200pt
    # overruns by 62px); the tighter 0.10" top margin clears the subject's hair.

    ("love-does-not-seek-its-own.png",
     ["Love does not seek its own…"],
     "1 CORINTHIANS 13:5", {"backplate": True}),

    ("love-is-not-provoked.png",
     ["Love is not provoked…"],
     "1 CORINTHIANS 13:5", {"backplate": True}),

    ("love-does-not-take-into-account-a-wrong-suffered.png",
     ["Love does not take into account",
      "a wrong suffered…"],
     "1 CORINTHIANS 13:5",
     {"attr_size": 130, "cite_size": 54, "caption_y_in": 0.18, "backplate": True}),
    # portrait vertical diptych; smaller font + tight top margin to clear
    # the upper-scene boy's head, plus backplate for uniformity with the wall

    ("love-does-not-rejoice-in-unrighteous-but-with-the-truth.png",
     ["Love does not rejoice in unrighteousness,",
      "but rejoices with the truth…"],
     "1 CORINTHIANS 13:6", {"backplate": True}),

    ("love-bears-all-things.png",
     ["Love bears all things…"],
     "1 CORINTHIANS 13:7", {"backplate": True}),

    ("love-believes-all-things.png",
     ["Love believes all things…"],
     "1 CORINTHIANS 13:7", {"backplate": True}),

    ("love-hopes-all-things.png",
     ["Love hopes all things…"],
     "1 CORINTHIANS 13:7", {"backplate": True}),

    ("love-endures-all-things.png",
     ["Love endures all things…"],
     "1 CORINTHIANS 13:7", {"backplate": True}),
]


def load(path, size):
    return ImageFont.truetype(str(path), size)


def apply_caption(source_path: Path, output_path: Path,
                  attribute_lines, citation_text: str,
                  anchor_right: bool = False, backplate: bool = False,
                  attr_size: int = None, cite_size: int = None,
                  caption_y_in: float = None):
    panel = Image.open(source_path).convert("RGB")
    W, H = panel.size

    # Allow per-panel overrides for tight-headroom situations
    effective_attr_size = attr_size or ATTR_SIZE
    effective_cite_size = cite_size or CITE_SIZE
    effective_line_height = int(effective_attr_size * 1.15)
    effective_caption_y = int(caption_y_in * DPI) if caption_y_in is not None else DEFAULT_CAPTION_Y

    attr_font = load(FONT_ITALIC, effective_attr_size)
    cite_font = load(FONT_REGULAR, effective_cite_size)

    # Measure the widest attribute line (for centering the citation under it,
    # and for right-alignment of the whole caption block)
    measure_draw = ImageDraw.Draw(panel)
    max_attr_w = 0
    for line in attribute_lines:
        bb = measure_draw.textbbox((0, 0), line, font=attr_font)
        line_w = bb[2] - bb[0]
        if line_w > max_attr_w:
            max_attr_w = line_w

    # Compute anchor position
    if anchor_right:
        # Caption block's RIGHT edge sits DEFAULT_CAPTION_X in from the right edge
        caption_left = W - DEFAULT_CAPTION_X - max_attr_w
    else:
        caption_left = DEFAULT_CAPTION_X
    caption_top = effective_caption_y

    # Citation measurements (need first because backplate sizes around full block)
    cite_widths = [measure_draw.textbbox((0, 0), ch, font=cite_font)[2] for ch in citation_text]
    cite_w = sum(cite_widths) + CITE_SPACING * (len(citation_text) - 1)
    last_y_top = caption_top + (len(attribute_lines) - 1) * effective_line_height
    cite_y = last_y_top + effective_attr_size + CITE_GAP_BELOW_ATTR

    # Optional semi-transparent cream backplate (for busy backgrounds like branches)
    if backplate:
        pad_x = int(0.18 * DPI)   # ~54 px horizontal padding
        pad_top = int(0.10 * DPI) # ~30 px above the attribute
        pad_bot = int(0.14 * DPI) # ~42 px below the citation
        bp_left   = caption_left - pad_x
        bp_right  = caption_left + max_attr_w + pad_x
        bp_top    = caption_top - pad_top
        bp_bottom = cite_y + effective_cite_size + pad_bot
        # Build a separate RGBA layer for the translucent box, then composite
        overlay = Image.new("RGBA", panel.size, (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        radius = int(0.10 * DPI)
        ov_draw.rounded_rectangle(
            [bp_left, bp_top, bp_right, bp_bottom],
            radius=radius,
            fill=(*CREAM_BG, 215),   # ~85% opacity cream
        )
        panel = Image.alpha_composite(panel.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(panel)

    # Draw attribute lines
    y = caption_top
    for line in attribute_lines:
        draw.text((caption_left, y), line, font=attr_font, fill=NAVY)
        y += effective_line_height

    # Citation: faux small caps, centered horizontally under the widest attribute line
    cite_cx = caption_left + max_attr_w // 2
    x = cite_cx - cite_w // 2
    for ch, wch in zip(citation_text, cite_widths):
        draw.text((x, cite_y), ch, font=cite_font, fill=NAVY)
        x += wch + CITE_SPACING

    panel.save(output_path, "PNG", optimize=True)

    # Read-out check
    if caption_left < 0 or caption_left + max_attr_w > W:
        overflow_in = max(-caption_left, caption_left + max_attr_w - W) / DPI
        print(f"  WARN: caption extends {overflow_in:.2f}\" past a panel edge")


def main():
    print(f"Applying captions to {len(PANELS)} panels...")
    print(f"  Default anchor: ({DEFAULT_CAPTION_X}px / {DEFAULT_CAPTION_X/DPI:.2f}\", "
          f"{DEFAULT_CAPTION_Y}px / {DEFAULT_CAPTION_Y/DPI:.2f}\") from top-left "
          f"(per-panel right-anchor and backplate available)")
    print(f"  Attribute: EB Garamond Italic {ATTR_SIZE}pt navy")
    print(f"  Citation: EB Garamond Regular {CITE_SIZE}pt navy "
          f"(faux small caps, +{CITE_SPACING}px letter spacing)")
    print()

    missing = []
    for fname, attr_lines, cite, opts in PANELS:
        src = SOURCE_DIR / fname
        if not src.exists():
            print(f"  MISSING: {fname}")
            missing.append(fname)
            continue
        out = OUT_DIR / fname
        apply_caption(src, out, attr_lines, cite, **opts)
        attr_summary = " / ".join(attr_lines)
        tag = ""
        if opts.get("anchor_right"):
            tag += " [right-anchored]"
        if opts.get("backplate"):
            tag += " [backplate]"
        print(f"  OK  {fname:<58}  {attr_summary}{tag}")

    print()
    if missing:
        print(f"WARNING: {len(missing)} panel(s) missing from print/:")
        for m in missing:
            print(f"  - {m}")
    else:
        print(f"All {len(PANELS)} panels captioned into {OUT_DIR.relative_to(BOOK_DIR)}/")


if __name__ == "__main__":
    main()
