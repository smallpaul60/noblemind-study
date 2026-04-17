#!/usr/bin/env python3
"""Compose the front cover for 'The God Who Showed Up'.

Input: TheBurningBush.png (1024 x 1536, Moses shielding his eyes from
the flame of the burning bush).
Output:
  - cover_front.jpg  (1100 x 1700)
  - cover_thumb.jpg  (400 x 618)

The prior hand-made cover had the title block sitting low enough that
the subtitle "What His Names Reveal About Who He Is" landed across
Moses's face and forearm. This script puts the full title stack at the
very top — above both the flame's peak and Moses's raised hand — so
the figure is left unobscured.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BOOK_DIR = Path(__file__).parent
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

SOURCE    = BOOK_DIR / "TheBurningBush.png"
OUT_FRONT = BOOK_DIR / "cover_front.jpg"
OUT_THUMB = BOOK_DIR / "cover_thumb.jpg"

W, H = 1100, 1700

CREAM      = (245, 232, 205)
CREAM_SOFT = (225, 210, 180)

FONT_BOLD   = FONT_DIR / "EBGaramond.ttf"
FONT_ITALIC = FONT_DIR / "EBGaramond-Italic.ttf"


def load_font(path, size):
    return ImageFont.truetype(str(path), size)


def build_cover(target_w, target_h):
    # 1. Cover-fit the source to the canvas, minor side crop.
    src = Image.open(SOURCE).convert("RGB")
    sw, sh = src.size
    scale = max(target_w / sw, target_h / sh)
    new_w = int(round(sw * scale))
    new_h = int(round(sh * scale))
    src = src.resize((new_w, new_h), Image.LANCZOS)
    off_x = (new_w - target_w) // 2
    off_y = (new_h - target_h) // 2
    canvas = src.crop((off_x, off_y, off_x + target_w, off_y + target_h))

    # 2. Soft darkening band across the TOP so cream title reads cleanly
    #    over the bright flame. The flame reaches near the upper edge;
    #    without this, "The God Who" drops into a yellow-orange area with
    #    weak cream-on-warm contrast. A ~30% alpha black wash down to
    #    about 22% from the top solves it without looking letterboxed.
    top_shade = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(top_shade)
    shade_h = int(target_h * 0.22)
    for y in range(shade_h):
        t = y / max(shade_h - 1, 1)
        alpha = int((1 - t) * 115)
        shade_draw.line([(0, y), (target_w, y)], fill=(10, 8, 6, alpha))
    # 3. Matching soft vignette at the bottom for the author line.
    vignette_h = int(target_h * 0.16)
    for y in range(vignette_h):
        t = y / max(vignette_h - 1, 1)
        alpha = int(t * 100)
        shade_draw.line(
            [(0, target_h - vignette_h + y), (target_w, target_h - vignette_h + y)],
            fill=(10, 8, 6, alpha),
        )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), top_shade).convert("RGB")

    # 4. Typography
    draw = ImageDraw.Draw(canvas)
    s = target_h / 1700

    small_title_size = int(70  * s)  # "The God Who" — italic
    big_title_size   = int(112 * s)  # "Showed Up"   — bold
    subtitle_size    = int(36  * s)
    author_size      = int(38  * s)

    f_small    = load_font(FONT_ITALIC, small_title_size)
    f_big      = load_font(FONT_BOLD,   big_title_size)
    f_subtitle = load_font(FONT_ITALIC, subtitle_size)
    f_author   = load_font(FONT_BOLD,   author_size)

    def center_text(y, text, font, fill, spacing=0):
        if spacing:
            widths = [draw.textbbox((0, 0), ch, font=font)[2] for ch in text]
            total = sum(widths) + spacing * (len(text) - 1)
            x = (target_w - total) // 2
            for ch, wch in zip(text, widths):
                draw.text((x, y), ch, font=font, fill=fill)
                x += wch + spacing
        else:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((target_w - tw) // 2, y), text, font=font, fill=fill)

    # Title block — pushed right to the top so it sits above Moses's
    # raised hand and the peak of the flame.
    small_y = int(target_h * 0.035)
    big_y   = small_y + int(small_title_size * 1.15)
    center_text(small_y, "The God Who", f_small, CREAM)
    center_text(big_y,   "Showed Up",   f_big,   CREAM)

    # Subtitle, italic smaller, positioned below "Showed Up" with full
    # descender clearance (the "p" and "g") but still inside the top
    # shading band so it isn't on top of Moses.
    subtitle_y = big_y + int(big_title_size * 1.3)
    center_text(subtitle_y, "What His Names Reveal About Who He Is",
                f_subtitle, CREAM_SOFT)

    # Author — letter-spaced caps, bottom vignette.
    author_y = target_h - int(target_h * 0.065)
    center_text(author_y, "PAUL & PAM HAINLINE", f_author, CREAM,
                spacing=int(7 * s))

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
