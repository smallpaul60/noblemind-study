#!/usr/bin/env python3
"""Compose the front cover for 'One Day Closer to Home'.

Input: "One Day Closer to Home.png" (1024 x 1536, an elderly man on a
porch at sunset with coffee mug and Bible).
Output:
  - cover_front.jpg  (1100 x 1700)
  - cover_thumb.jpg  (400 x 618)

Per Paul: drop the subtitle from the front cover. Clean title + author
only. The composition is busy (porch architecture, hanging basket,
hat, sunset, figure), so we rely on a soft dark wash at the top to
give the cream title a uniform background.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BOOK_DIR = Path(__file__).parent
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

SOURCE    = BOOK_DIR / "One Day Closer to Home.png"
OUT_FRONT = BOOK_DIR / "cover_front.jpg"
OUT_THUMB = BOOK_DIR / "cover_thumb.jpg"

W, H = 1100, 1700

CREAM = (245, 232, 205)

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

    # 2. Soft darkening bands — top for title, bottom for author.
    shade = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)

    top_h = int(target_h * 0.19)   # covers the porch beams + hat brim area
    for y in range(top_h):
        t = y / max(top_h - 1, 1)
        alpha = int((1 - t) * 135)
        sd.line([(0, y), (target_w, y)], fill=(10, 8, 6, alpha))

    bot_h = int(target_h * 0.15)
    for y in range(bot_h):
        t = y / max(bot_h - 1, 1)
        alpha = int(t * 110)
        sd.line(
            [(0, target_h - bot_h + y), (target_w, target_h - bot_h + y)],
            fill=(10, 8, 6, alpha),
        )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shade).convert("RGB")

    # 3. Typography
    draw = ImageDraw.Draw(canvas)
    s = target_h / 1700

    small_size = int(60  * s)   # "One Day Closer" — italic
    big_size   = int(96  * s)   # "to Home"        — bold
    author_size = int(38 * s)

    f_small  = load_font(FONT_ITALIC, small_size)
    f_big    = load_font(FONT_BOLD,   big_size)
    f_author = load_font(FONT_BOLD,   author_size)

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

    # Title — stacked, right at the top so it sits above the hat and
    # above the porch beam, within the shaded band.
    small_y = int(target_h * 0.025)
    big_y   = small_y + int(small_size * 1.15)
    center_text(small_y, "One Day Closer", f_small, CREAM)
    center_text(big_y,   "to Home",        f_big,   CREAM)

    # Author — letter-spaced caps, bottom vignette.
    author_y = target_h - int(target_h * 0.065)
    center_text(author_y, "PAUL HAINLINE", f_author, CREAM,
                spacing=int(8 * s))

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
