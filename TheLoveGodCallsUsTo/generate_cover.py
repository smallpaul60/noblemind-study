#!/usr/bin/env python3
"""Compose a typographic cover for 'The Love God Calls Us To'.

Pure-typographic design — no source image. Deep midnight ground with
warm red and warm gold accents matching the online dark-theme palette.

Outputs:
  - cover_front.jpg  (1100 x 1700, full cover)
  - cover_thumb.jpg  (400 x 618, books.html card thumbnail)

The interior generator scripts (generate_pdf.py, generate_epub.py)
pick up cover_front.jpg automatically if it exists.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BOOK_DIR = Path(__file__).parent
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

OUT_FRONT = BOOK_DIR / "cover_front.jpg"
OUT_THUMB = BOOK_DIR / "cover_thumb.jpg"

W, H = 1100, 1700

# Palette (matches the online dark-theme accents)
BG_DEEP = (13, 13, 13)          # near-black ground
ACCENT_RED = (196, 81, 63)      # warm red — scripture borders, accents
ACCENT_GOLD = (196, 168, 84)    # warm gold — highlights, author line
TEXT_PRIMARY = (240, 236, 228)  # warm cream — main title
TEXT_SECONDARY = (192, 184, 168)  # softer cream — subtitle, anchor verse
TEXT_MUTED = (138, 130, 120)    # muted — minor type

FONT_BOLD = FONT_DIR / "EBGaramond.ttf"
FONT_ITALIC = FONT_DIR / "EBGaramond-Italic.ttf"


def load_font(path, size):
    return ImageFont.truetype(str(path), size)


def add_radial_glow(canvas, center, radius, color, max_alpha):
    """Soft radial gradient blob — used to seed the corners with warm
    accent color so the typography doesn't sit on a flat black field."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = center
    steps = 80
    for i in range(steps):
        t = i / steps
        r = int(radius * (1 - t))
        alpha = int(max_alpha * (1 - t) ** 1.5)
        if r <= 0 or alpha <= 0:
            continue
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(color[0], color[1], color[2], alpha),
        )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=30))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def build_cover(target_w, target_h):
    canvas = Image.new("RGB", (target_w, target_h), BG_DEEP)

    # --- Background glows (warm accents in corners) ---
    s = target_h / 1700  # scale factor for all positioning
    canvas = add_radial_glow(canvas,
                             center=(int(target_w * 0.18), int(target_h * 0.22)),
                             radius=int(700 * s),
                             color=ACCENT_RED, max_alpha=80)
    canvas = add_radial_glow(canvas,
                             center=(int(target_w * 0.82), int(target_h * 0.28)),
                             radius=int(620 * s),
                             color=ACCENT_GOLD, max_alpha=65)
    canvas = add_radial_glow(canvas,
                             center=(int(target_w * 0.5), int(target_h * 0.92)),
                             radius=int(800 * s),
                             color=ACCENT_RED, max_alpha=55)

    draw = ImageDraw.Draw(canvas)

    # --- Top hairline + small label ---
    label_y = int(target_h * 0.085)
    hairline_y = int(target_h * 0.075)
    margin_x = int(target_w * 0.13)
    draw.line(
        [(margin_x, hairline_y), (target_w - margin_x, hairline_y)],
        fill=ACCENT_GOLD, width=1,
    )

    label_font = load_font(FONT_ITALIC, int(28 * s))
    label = "1 CORINTHIANS 13"
    bbox = draw.textbbox((0, 0), label, font=label_font)
    label_w = bbox[2] - bbox[0]
    # Letter-spaced caps for the label
    spacing = int(8 * s)
    widths = [draw.textbbox((0, 0), ch, font=label_font)[2] for ch in label]
    total = sum(widths) + spacing * (len(label) - 1)
    x = (target_w - total) // 2
    for ch, wch in zip(label, widths):
        draw.text((x, label_y), ch, font=label_font, fill=ACCENT_GOLD)
        x += wch + spacing

    # --- Main title ---
    small_title_size = int(82 * s)   # "The Love God"
    big_title_size = int(140 * s)    # "Calls Us To"
    f_small = load_font(FONT_ITALIC, small_title_size)
    f_big = load_font(FONT_BOLD, big_title_size)

    def center_text(y, text, font, fill, spacing=0):
        if spacing:
            widths = [draw.textbbox((0, 0), ch, font=font)[2] for ch in text]
            total = sum(widths) + spacing * (len(text) - 1)
            x = (target_w - total) // 2
            for ch, wch in zip(text, widths):
                draw.text((x, y), ch, font=font, fill=fill)
                x += wch + spacing
            return total
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((target_w - tw) // 2, y), text, font=font, fill=fill)
        return tw

    small_y = int(target_h * 0.235)
    big_y = small_y + int(small_title_size * 1.18)
    center_text(small_y, "The Love God", f_small, TEXT_PRIMARY)
    center_text(big_y, "Calls Us To", f_big, TEXT_PRIMARY)

    # --- Subtitle ---
    subtitle_size = int(40 * s)
    f_subtitle = load_font(FONT_ITALIC, subtitle_size)
    subtitle_y = big_y + int(big_title_size * 1.25)
    center_text(subtitle_y, "Walking Out 1 Corinthians 13",
                f_subtitle, TEXT_SECONDARY)

    # --- Decorative divider ---
    divider_y = subtitle_y + int(subtitle_size * 2.0)
    divider_w = int(target_w * 0.18)
    draw.line(
        [((target_w - divider_w) // 2, divider_y),
         ((target_w + divider_w) // 2, divider_y)],
        fill=ACCENT_RED, width=2,
    )

    # --- Anchor verse (centerpiece below the title) ---
    verse_size = int(34 * s)
    cite_size = int(26 * s)
    f_verse = load_font(FONT_ITALIC, verse_size)
    f_cite = load_font(FONT_BOLD, cite_size)

    verse_lines = [
        "But now faith, hope, love,",
        "abide these three;",
        "but the greatest of these",
        "is love.",
    ]
    verse_y = divider_y + int(40 * s)
    line_h = int(verse_size * 1.45)
    for i, line in enumerate(verse_lines):
        center_text(verse_y + i * line_h, line, f_verse, TEXT_SECONDARY)

    cite_y = verse_y + len(verse_lines) * line_h + int(30 * s)
    cite_text = "1 CORINTHIANS 13:13"
    widths = [draw.textbbox((0, 0), ch, font=f_cite)[2] for ch in cite_text]
    cite_spacing = int(5 * s)
    total = sum(widths) + cite_spacing * (len(cite_text) - 1)
    x = (target_w - total) // 2
    for ch, wch in zip(cite_text, widths):
        draw.text((x, cite_y), ch, font=f_cite, fill=ACCENT_GOLD)
        x += wch + cite_spacing

    # --- Author line ---
    author_size = int(44 * s)
    f_author = load_font(FONT_BOLD, author_size)
    author_y = target_h - int(120 * s)
    center_text(author_y, "PAUL HAINLINE", f_author, TEXT_PRIMARY,
                spacing=int(9 * s))

    # --- Bottom hairline + publisher ---
    publisher_size = int(20 * s)
    f_pub = load_font(FONT_ITALIC, publisher_size)
    pub_y = target_h - int(55 * s)
    bottom_hairline_y = author_y + int(author_size * 1.15)
    draw.line(
        [(margin_x, bottom_hairline_y),
         (target_w - margin_x, bottom_hairline_y)],
        fill=ACCENT_GOLD, width=1,
    )
    center_text(pub_y, "NobleMind Press", f_pub, TEXT_MUTED)

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
