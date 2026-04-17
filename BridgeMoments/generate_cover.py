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

# Typography colors (pulled from the artwork's warm palette + warm cream).
CREAM       = (247, 236, 210)
CREAM_SOFT  = (230, 218, 190)
DARK_SKY    = (22, 18, 26)

# Fonts — EB Garamond family, all loaded from the local fonts dir.
FONT_BOLD    = FONT_DIR / "EBGaramond.ttf"   # has Bold face inside
FONT_ITALIC  = FONT_DIR / "EBGaramond-Italic.ttf"


def load_font(path, size):
    return ImageFont.truetype(str(path), size)


def build_cover(target_w, target_h):
    """Return the composed cover as a PIL RGB image at (target_w, target_h)."""

    # 1. Load the source and match its width to the canvas width, preserving aspect.
    src = Image.open(SOURCE).convert("RGB")
    sw, sh = src.size
    scaled_w = target_w
    scaled_h = int(sh * (scaled_w / sw))
    src = src.resize((scaled_w, scaled_h), Image.LANCZOS)

    # 2. Create the canvas, dark navy like the top of the existing sky.
    canvas = Image.new("RGB", (target_w, target_h), DARK_SKY)

    # 3. Paste the artwork so the BOTTOM edges align (bridge + path sit where
    #    they should). The extra space appears as a dark band above the sky.
    paste_y = target_h - scaled_h
    canvas.paste(src, (0, paste_y))

    # 4. Blend the top of the artwork into the dark navy band so the join is
    #    invisible. We sample the top strip of the artwork and fade from the
    #    dark navy into the image over ~110 pixels. This keeps the existing
    #    sky gradient continuous.
    if paste_y > 0:
        blend_height = 120
        blend_start_y = paste_y - 20       # overlap 20 px into the artwork
        if blend_start_y < 0:
            blend_start_y = 0
        blend_end_y = paste_y + blend_height

        # Sample the mean color of a thin slice of the artwork's top edge.
        top_slice = src.crop((0, 0, scaled_w, 1)).resize((1, 1)).getpixel((0, 0))
        # Slightly darker than the sample for the top band:
        top_color = tuple(int(c * 0.55) for c in top_slice)

        # Draw a vertical linear gradient from DARK_SKY → top_color
        overlay = Image.new("RGB", (target_w, blend_end_y - blend_start_y), DARK_SKY)
        for y in range(overlay.height):
            t = y / max(overlay.height - 1, 1)
            r = int(DARK_SKY[0] * (1 - t) + top_color[0] * t)
            g = int(DARK_SKY[1] * (1 - t) + top_color[1] * t)
            b = int(DARK_SKY[2] * (1 - t) + top_color[2] * t)
            for x in range(target_w):
                overlay.putpixel((x, y), (r, g, b))
        canvas.paste(overlay, (0, blend_start_y))

    # 5. Slight vignette at the very bottom so the author name reads cleanly
    #    over the path. A 25%-height gradient from transparent to 45% black.
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

    # 6. Typography
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

    # Title block — near the top, inside the sky / extended navy band.
    title_y = int(target_h * 0.07)
    center_text(title_y, "Bridge Moments", f_title, CREAM)

    subtitle_y = title_y + int(title_size * 1.15)
    center_text(subtitle_y, "Making the Most of Every Opportunity",
                f_subtitle, CREAM_SOFT)

    tagline_y = subtitle_y + int(subtitle_size * 1.6)
    center_text(tagline_y, "A Bible Study on Conversational Evangelism",
                f_tagline, CREAM_SOFT)

    # Author + imprint at the bottom, over the darkened foreground.
    author_y  = target_h - int(target_h * 0.09)
    imprint_y = target_h - int(target_h * 0.045)
    center_text(author_y,  "Paul Hainline",    f_author,  CREAM)
    center_text(imprint_y, "NOBLEMIND PRESS",  f_imprint, CREAM_SOFT)

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
