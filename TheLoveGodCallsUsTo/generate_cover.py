#!/usr/bin/env python3
"""Compose the front cover for 'The Love God Calls Us To'.

Source: washing_feet_cover.png (Christ kneeling, washing the feet of a
disciple — warm earth tones, oil lamp on the wall, basin at the floor).

The footwashing is the textbook anti-arrogance image (Ch06) and the
deepest demonstration in the Gospels of love that does not seek its
own (Ch08). It is the right cover for this book.

Layout decisions:
  - Title block sits in the upper ~20% of the cover, above both
    figures' heads (the seated disciple's head is around 30% from
    the top, Christ's around 40%). A soft darkening band runs across
    the top so the cream typography reads cleanly on the warmer wall.
  - Author + publisher at the foot, on a matching darkening band.
  - No anchor verse on the cover — the figures are the verse.

Outputs:
  - cover_front.jpg  (1100 x 1700, embedded in PDF and EPUB)
  - cover_thumb.jpg  (400 x 618, books.html card thumbnail)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BOOK_DIR = Path(__file__).parent
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

SOURCE = BOOK_DIR / "washing_feet_cover.png"
OUT_FRONT = BOOK_DIR / "cover_front.jpg"
OUT_THUMB = BOOK_DIR / "cover_thumb.jpg"

W, H = 1100, 1700

# Cream / warm-cream palette to read against the painting's warm earth tones
CREAM = (245, 232, 205)
CREAM_SOFT = (225, 210, 180)
ACCENT_GOLD = (212, 180, 110)

FONT_BOLD = FONT_DIR / "EBGaramond.ttf"
FONT_ITALIC = FONT_DIR / "EBGaramond-Italic.ttf"


def load_font(path, size):
    return ImageFont.truetype(str(path), size)


def build_cover(target_w, target_h):
    # 1. Cover-fit the source to the canvas
    src = Image.open(SOURCE).convert("RGB")
    sw, sh = src.size
    scale = max(target_w / sw, target_h / sh)
    new_w = int(round(sw * scale))
    new_h = int(round(sh * scale))
    src = src.resize((new_w, new_h), Image.LANCZOS)
    off_x = (new_w - target_w) // 2
    off_y = (new_h - target_h) // 2
    canvas = src.crop((off_x, off_y, off_x + target_w, off_y + target_h))

    # 2. Darkening bands at top and bottom for typography contrast.
    #    Top band ~24% (covers above the figures' heads).
    #    Bottom band ~14% (covers the floor / basin foreground for author line).
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(overlay)

    top_h = int(target_h * 0.24)
    for y in range(top_h):
        t = y / max(top_h - 1, 1)
        alpha = int((1 - t) * 130)
        shade_draw.line([(0, y), (target_w, y)], fill=(10, 6, 4, alpha))

    bot_h = int(target_h * 0.14)
    for y in range(bot_h):
        t = y / max(bot_h - 1, 1)
        alpha = int(t * 130)
        shade_draw.line(
            [(0, target_h - bot_h + y), (target_w, target_h - bot_h + y)],
            fill=(10, 6, 4, alpha),
        )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    # 3. Typography
    draw = ImageDraw.Draw(canvas)
    s = target_h / 1700  # scale factor

    label_size = int(26 * s)        # "1 CORINTHIANS 13" cap label
    small_title_size = int(64 * s)  # "The Love God" italic
    big_title_size = int(108 * s)   # "Calls Us To" bold
    subtitle_size = int(34 * s)     # "Walking Out 1 Corinthians 13"
    author_size = int(42 * s)
    publisher_size = int(20 * s)

    f_label = load_font(FONT_ITALIC, label_size)
    f_small = load_font(FONT_ITALIC, small_title_size)
    f_big = load_font(FONT_BOLD, big_title_size)
    f_subtitle = load_font(FONT_ITALIC, subtitle_size)
    f_author = load_font(FONT_BOLD, author_size)
    f_pub = load_font(FONT_ITALIC, publisher_size)

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

    # TOP BLOCK — pushed high so the figures stay clear
    label_y = int(target_h * 0.032)
    center_text(label_y, "1 CORINTHIANS 13", f_label, ACCENT_GOLD,
                spacing=int(7 * s))

    small_y = label_y + int(label_size * 2.4)
    center_text(small_y, "The Love God", f_small, CREAM)

    big_y = small_y + int(small_title_size * 1.15)
    center_text(big_y, "Calls Us To", f_big, CREAM)

    subtitle_y = big_y + int(big_title_size * 1.05)
    center_text(subtitle_y, "Walking Out 1 Corinthians 13",
                f_subtitle, CREAM_SOFT)

    # BOTTOM BLOCK — author + publisher in the darkened floor area
    author_y = target_h - int(85 * s)
    center_text(author_y, "PAUL HAINLINE", f_author, CREAM,
                spacing=int(8 * s))

    pub_y = target_h - int(35 * s)
    center_text(pub_y, "NobleMind Press", f_pub, ACCENT_GOLD)

    return canvas


def main():
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
