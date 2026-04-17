#!/usr/bin/env python3
"""Compose the front cover for 'Bridge Moments'.

Input: BridgeMoments-cover-image.png (1024 x 1536, the bridge artwork).
Output:
  - cover_front.jpg  (1100 x 1700, portrait, title + subtitle + author
                     overlaid on the artwork in the sky + path regions)
  - cover_thumb.jpg  (400 x 618, same layout scaled down, for the book card)

The source image is 2:3; the book trim is 11:17. We extend the top with a
painted-in dark navy gradient that blends with the existing sky, giving the
title room to breathe without cropping the bridge.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BOOK_DIR = Path(__file__).parent
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

SOURCE       = BOOK_DIR / "BridgeMoments-cover-image.png"
OUT_FRONT    = BOOK_DIR / "cover_front.jpg"
OUT_THUMB    = BOOK_DIR / "cover_thumb.jpg"

# Final canvas — 5.5 x 8.5 inch ratio (0.647) rendered at ~200dpi.
W, H = 1100, 1700

# Typography colors
CREAM       = (247, 236, 210)  # author / imprint, over the darkened foreground
WHITE       = (255, 255, 255)  # title, sits on the dim upper sky
BLACK       = (18, 14, 10)     # subtitle + tagline, sits on the warm amber sky

# Fonts — EB Garamond family, all loaded from the local fonts dir.
FONT_BOLD    = FONT_DIR / "EBGaramond.ttf"   # has Bold face inside
FONT_ITALIC  = FONT_DIR / "EBGaramond-Italic.ttf"


def load_font(path, size):
    return ImageFont.truetype(str(path), size)


def build_cover(target_w, target_h):
    """Return the composed cover as a PIL RGB image at (target_w, target_h)."""

    # 1. Load the source and scale it to COVER the canvas (may exceed in one
    #    dimension). Then center-crop to the target size. The source is 2:3
    #    and the book trim is 11:17, so this trims ~33 px total off the
    #    sides at a 1100-wide canvas — the composition is centered enough
    #    that trees on both edges survive.
    src = Image.open(SOURCE).convert("RGB")
    sw, sh = src.size
    scale = max(target_w / sw, target_h / sh)
    new_w = int(round(sw * scale))
    new_h = int(round(sh * scale))
    src = src.resize((new_w, new_h), Image.LANCZOS)
    off_x = (new_w - target_w) // 2
    off_y = (new_h - target_h) // 2
    canvas = src.crop((off_x, off_y, off_x + target_w, off_y + target_h))

    # 2. Slight vignette at the very bottom so the author name reads cleanly
    #    over the path. A 22%-height gradient from transparent to dark.
    dark_overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(dark_overlay)
    vignette_h = int(target_h * 0.22)
    for y in range(vignette_h):
        t = y / max(vignette_h - 1, 1)
        alpha = int(t * 110)
        ov_draw.line(
            [(0, target_h - vignette_h + y), (target_w, target_h - vignette_h + y)],
            fill=(0, 0, 0, alpha),
        )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), dark_overlay).convert("RGB")

    # 3. Typography
    draw = ImageDraw.Draw(canvas)

    # scale sizes to target height so the thumb looks right too
    scale = target_h / 1700

    title_size    = int(108 * scale)
    subtitle_size = int(40  * scale)
    tagline_size  = int(26  * scale)
    author_size   = int(36  * scale)
    imprint_size  = int(20  * scale)

    f_title    = load_font(FONT_BOLD,   title_size)
    f_subtitle = load_font(FONT_ITALIC, subtitle_size)
    f_tagline  = load_font(FONT_ITALIC, tagline_size)
    f_author   = load_font(FONT_BOLD,   author_size)
    f_imprint  = load_font(FONT_BOLD,   imprint_size)

    def center_text(y, text, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((target_w - tw) // 2, y), text, font=font, fill=fill)

    # Title in white, near the top where the sky is dim (good contrast).
    title_y = int(target_h * 0.05)
    center_text(title_y, "Bridge Moments", f_title, WHITE)

    # Subtitle in black, just below, where the sky begins to warm.
    subtitle_y = title_y + int(title_size * 1.1)
    center_text(subtitle_y, "Making the Most of Every Opportunity",
                f_subtitle, BLACK)

    # Author + imprint at the bottom, over the darkened foreground.
    author_y  = target_h - int(target_h * 0.09)
    imprint_y = target_h - int(target_h * 0.045)
    center_text(author_y,  "Paul Hainline",    f_author,  CREAM)
    center_text(imprint_y, "NOBLEMIND PRESS",  f_imprint, CREAM)

    return canvas


def main():
    print(f"Source: {SOURCE.name}")

    full = build_cover(W, H)
    full.save(OUT_FRONT, "JPEG", quality=92, optimize=True)
    print(f"Wrote {OUT_FRONT.name}  ({W}x{H}, {OUT_FRONT.stat().st_size:,} bytes)")

    thumb_w = 400
    thumb_h = int(H * (thumb_w / W))
    thumb = build_cover(thumb_w, thumb_h)
    thumb.save(OUT_THUMB, "JPEG", quality=88, optimize=True)
    print(f"Wrote {OUT_THUMB.name}  ({thumb_w}x{thumb_h}, {OUT_THUMB.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
