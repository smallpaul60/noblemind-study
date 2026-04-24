#!/usr/bin/env python3
"""Compose the front cover for 'Why Do You Delay?'.

Input: why-do-you-delay-cover-image.png — a Norman Rockwell-style river
baptism scene. Warm earth tones, olive/green tree canopy at top, dark
water below, figures clustered in the middle.

Output:
  - cover_front.jpg  (1100 x 1700)
  - cover_thumb.jpg  (400 x 618)

Typography:
  - "Why Do You" (italic) stacked over "Delay?" (bold) at the top
  - Subtitle below: two italic lines
  - Author (letter-spaced caps) at bottom over a soft dark vignette
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BOOK_DIR  = Path(__file__).parent
FONT_DIR  = Path.home() / ".local" / "share" / "fonts"

SOURCE    = BOOK_DIR / "why-do-you-delay-cover-image.png"
OUT_FRONT = BOOK_DIR / "cover_front.jpg"
OUT_THUMB = BOOK_DIR / "cover_thumb.jpg"

W, H = 1100, 1700

# Warm cream — reads well against the green canopy and the dark water
CREAM = (245, 232, 205)
# Warm gold decorative rule between the subtitle and the author — same
# #C69B56 used on the Lulu paperback cover so the print book and the
# website thumbnail stay in sync.
GOLD_RULE = (198, 155, 86)

FONT_BOLD    = FONT_DIR / "EBGaramond.ttf"
FONT_ITALIC  = FONT_DIR / "EBGaramond-Italic.ttf"


def load_font(path, size):
    return ImageFont.truetype(str(path), size)


def build_cover(target_w, target_h):
    # ---- 1. Cover-fit source image into the canvas (center crop) ----
    src = Image.open(SOURCE).convert("RGB")
    sw, sh = src.size
    scale = max(target_w / sw, target_h / sh)
    new_w = int(round(sw * scale))
    new_h = int(round(sh * scale))
    src = src.resize((new_w, new_h), Image.LANCZOS)
    off_x = (new_w - target_w) // 2
    off_y = (new_h - target_h) // 2
    canvas = src.crop((off_x, off_y, off_x + target_w, off_y + target_h))

    # ---- 2. Soft darkening bands so cream type reads cleanly ----
    shade = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)

    # Top band: covers the tree canopy so the title has a consistent
    # darker ground underneath without dimming the figures below.
    top_h = int(target_h * 0.22)
    for y in range(top_h):
        t = y / max(top_h - 1, 1)
        alpha = int((1 - t) * 150)
        sd.line([(0, y), (target_w, y)], fill=(8, 10, 6, alpha))

    # Bottom band: covers the water. Needs to be tall enough to hold
    # subtitle (two lines) + author.
    bot_h = int(target_h * 0.26)
    for y in range(bot_h):
        t = y / max(bot_h - 1, 1)
        alpha = int(t * 165)
        sd.line(
            [(0, target_h - bot_h + y), (target_w, target_h - bot_h + y)],
            fill=(5, 8, 6, alpha),
        )

    canvas = Image.alpha_composite(canvas.convert("RGBA"), shade).convert("RGB")

    # ---- 3. Typography ----
    draw = ImageDraw.Draw(canvas)
    s = target_h / 1700  # scale factor so thumb renders proportionally

    small_size    = int(62  * s)   # "Why Do You"  — italic
    big_size      = int(92  * s)   # "Delay?"      — bold
    subtitle_size = int(28  * s)   # Two subtitle lines
    author_size   = int(34  * s)

    f_small    = load_font(FONT_ITALIC, small_size)
    f_big      = load_font(FONT_BOLD,   big_size)
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

    # --- Title: "Why Do You" / "Delay?" stacked at the top ---
    title_small_y = int(target_h * 0.028)
    title_big_y   = title_small_y + int(small_size * 1.1)
    center_text(title_small_y, "Why Do You", f_small, CREAM)
    center_text(title_big_y,   "Delay?",     f_big,   CREAM)

    # --- Subtitle: two italic lines, bottom of cover above author ---
    author_y = target_h - int(target_h * 0.06)
    sub2_y = author_y - int(author_size * 1.55) - int(subtitle_size * 0.3)
    sub1_y = sub2_y - int(subtitle_size * 1.35)
    center_text(sub1_y, "Baptism, Salvation,",              f_subtitle, CREAM)
    center_text(sub2_y, "and What the Bible Actually Says", f_subtitle, CREAM)

    # --- Gold decorative rule between subtitle and author ---
    # Matches the gold bar on the Lulu paperback cover so print and
    # web covers show the same finish.
    sub2_bbox  = draw.textbbox((0, sub2_y), "Tg", font=f_subtitle)
    rule_y     = (sub2_bbox[3] + author_y) // 2
    rule_hw    = int(target_w * 0.10)
    rule_thick = max(1, int(2 * s))
    cx         = target_w // 2
    draw.line(
        [(cx - rule_hw, rule_y), (cx + rule_hw, rule_y)],
        fill=GOLD_RULE,
        width=rule_thick,
    )

    # --- Author: letter-spaced caps at the very bottom ---
    center_text(author_y, "PAUL HAINLINE", f_author, CREAM,
                spacing=int(7 * s))

    return canvas


def main():
    print(f"Source: {SOURCE.name}  ({Image.open(SOURCE).size})")

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
