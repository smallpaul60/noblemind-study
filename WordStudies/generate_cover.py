#!/usr/bin/env python3
"""Generate cover_thumb.jpg for Gems of the Original Languages."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "cover_thumb.jpg"
FONTS = Path.home() / ".local/share/fonts"

W, H = 600, 900
BG = (12, 12, 16)
GOLD = (196, 168, 84)
GOLD_DIM = (144, 124, 64)
AMBER = (168, 68, 45)
CREAM = (240, 236, 228)

img = Image.new("RGB", (W, H), BG)

# Soft single corner glow — very subtle
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for r in range(360, 0, -2):
    alpha = int(20 * (1 - r/360))
    if alpha <= 0: continue
    gd.ellipse([W//2 - r, H//2 - r - 100, W//2 + r, H//2 + r - 100],
               fill=(196, 168, 84, alpha))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
draw = ImageDraw.Draw(img)

def load_font(name, size):
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except (OSError, FileNotFoundError):
        return ImageFont.load_default()

def center(y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, font=font, fill=fill)

# Outer border frame
draw.rectangle([18, 18, W-18, H-18], outline=GOLD, width=2)
draw.rectangle([28, 28, W-28, H-28], outline=GOLD_DIM, width=1)

# Top label
font_label = load_font("EBGaramond.ttf", 18)
LABEL = "NOBLE   MIND   PRESS"
center(80, LABEL, font_label, GOLD_DIM)

# Divider rule under label
draw.rectangle([180, 116, W-180, 117], fill=GOLD_DIM)

# Main title — three-line stack
font_title_xl = load_font("EBGaramond.ttf", 92)
font_title_md = load_font("EBGaramond-Italic.ttf", 42)
center(260, "Gems", font_title_xl, GOLD)
center(380, "of the Original", font_title_md, CREAM)
center(440, "Languages", font_title_xl, GOLD)

# Three small dots ornament
dot_y = 590
spacing = 30
draw.ellipse([W//2 - spacing - 4, dot_y, W//2 - spacing + 4, dot_y + 8], fill=AMBER)
draw.ellipse([W//2 - 4,           dot_y, W//2 + 4,           dot_y + 8], fill=AMBER)
draw.ellipse([W//2 + spacing - 4, dot_y, W//2 + spacing + 4, dot_y + 8], fill=AMBER)

# Subtitle
font_sub = load_font("EBGaramond-Italic.ttf", 26)
center(640, "A Hebrew and Greek", font_sub, CREAM)
center(680, "Study Companion", font_sub, CREAM)

# Bottom rule + footer
draw.rectangle([180, H-160, W-180, H-159], fill=GOLD_DIM)
font_foot = load_font("EBGaramond-Italic.ttf", 18)
center(H - 130, "to the Noble Mind Press Books", font_foot, CREAM)
center(H - 88, "Compiled from the catalog of", font_foot, GOLD_DIM)
font_foot_b = load_font("EBGaramond.ttf", 20)
center(H - 65, "PAUL  &  PAM  HAINLINE", font_foot_b, GOLD)

img.save(OUT, "JPEG", quality=92)
print(f"  wrote {OUT} ({OUT.stat().st_size//1024} KB)")
