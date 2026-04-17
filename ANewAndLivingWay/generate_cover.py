#!/usr/bin/env python3
"""Compose the front cover for 'A New and Living Way'.

Input: in_the_garden.png (1024 x 1536, Jesus praying in Gethsemane).
Output:
  - cover_front.jpg  (1100 x 1700, portrait, title + subtitle + author
                     overlaid over the dark upper sky so the artwork of
                     Jesus remains unobscured)
  - cover_thumb.jpg  (400 x 618, same layout scaled down, for the book card)

The prior hand-made cover had 'A New and' sitting too low and the subtitle
overlapping the figure; this script places the full title block above
Jesus's head so nothing sits on top of the artwork.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BOOK_DIR = Path(__file__).parent
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

SOURCE    = BOOK_DIR / "in_the_garden.png"
OUT_FRONT = BOOK_DIR / "cover_front.jpg"
OUT_THUMB = BOOK_DIR / "cover_thumb.jpg"

# Final canvas — 5.5 x 8.5 inch ratio (0.647) at ~200dpi.
W, H = 1100, 1700

# Typography colors
CREAM      = (240, 228, 200)
CREAM_SOFT = (220, 208, 180)

FONT_BOLD   = FONT_DIR / "EBGaramond.ttf"
FONT_ITALIC = FONT_DIR / "EBGaramond-Italic.ttf"


def load_font(path, size):
    return ImageFont.truetype(str(path), size)


def build_cover(target_w, target_h):
    # 1. Cover-fit the source to the canvas (minor side crop).
    src = Image.open(SOURCE).convert("RGB")
    sw, sh = src.size
    scale = max(target_w / sw, target_h / sh)
    new_w = int(round(sw * scale))
    new_h = int(round(sh * scale))
    src = src.resize((new_w, new_h), Image.LANCZOS)
    off_x = (new_w - target_w) // 2
    off_y = (new_h - target_h) // 2
    canvas = src.crop((off_x, off_y, off_x + target_w, off_y + target_h))

    # 2. Very soft vignette at the very bottom so the author name reads
    #    cleanly over the darker cloak. The image is already dark there
    #    so the overlay is light — 30% max alpha.
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    vignette_h = int(target_h * 0.18)
    for y in range(vignette_h):
        t = y / max(vignette_h - 1, 1)
        alpha = int(t * 80)
        ov_draw.line(
            [(0, target_h - vignette_h + y), (target_w, target_h - vignette_h + y)],
            fill=(0, 0, 0, alpha),
        )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    # 3. Typography
    draw = ImageDraw.Draw(canvas)
    scale_t = target_h / 1700

    a_new_size    = int(70  * scale_t)   # "A New and"  — italic
    living_size   = int(112 * scale_t)   # "Living Way" — bold
    subtitle_size = int(36  * scale_t)   # "What the Bible Teaches About Prayer"
    author_size   = int(42  * scale_t)   # "PAUL HAINLINE"

    f_a_new    = load_font(FONT_ITALIC, a_new_size)
    f_living   = load_font(FONT_BOLD,   living_size)
    f_subtitle = load_font(FONT_ITALIC, subtitle_size)
    f_author   = load_font(FONT_BOLD,   author_size)

    def center_text(y, text, font, fill, spacing=0):
        if spacing:
            # letter-spaced — draw each character individually
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

    # Title block — sits entirely above Jesus's head, which starts around
    # 22-23% down the image (roughly y=390 at 1700px height).
    a_new_y  = int(target_h * 0.035)
    living_y = a_new_y + int(a_new_size * 1.15)
    center_text(a_new_y,  "A New and",  f_a_new,  CREAM)
    center_text(living_y, "Living Way", f_living, CREAM)

    # Subtitle — tucked under the title, clear of the figure.
    subtitle_y = living_y + int(living_size * 1.25)
    center_text(subtitle_y, "What the Bible Teaches About Prayer",
                f_subtitle, CREAM_SOFT)

    # Author — letter-spaced caps, near the bottom over the darkened cloak.
    author_y = target_h - int(target_h * 0.065)
    center_text(author_y, "PAUL HAINLINE", f_author, CREAM,
                spacing=int(8 * scale_t))

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
