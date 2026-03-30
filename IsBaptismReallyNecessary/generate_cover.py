#!/usr/bin/env python3
"""Generate cover image for 'Is Baptism Really Necessary?'"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

FONT_DIR = os.path.expanduser('~/.local/share/fonts')
SRC = 'River_Baptism.png'
OUT = 'Is_Baptism_Really_Necessary_Cover.png'

# Target: 5.5x8.5 ratio at high res (1650x2550 at 300dpi)
TARGET_W, TARGET_H = 1650, 2550

img = Image.open(SRC).convert('RGB')

# Resize/crop to target ratio
src_w, src_h = img.size
target_ratio = TARGET_W / TARGET_H
src_ratio = src_w / src_h

if src_ratio > target_ratio:
    # Source is wider — crop sides
    new_w = int(src_h * target_ratio)
    offset = (src_w - new_w) // 2
    img = img.crop((offset, 0, offset + new_w, src_h))
else:
    # Source is taller — crop top/bottom
    new_h = int(src_w / target_ratio)
    offset = (src_h - new_h) // 2
    img = img.crop((0, offset, src_w, offset + new_h))

img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)

draw = ImageDraw.Draw(img)

# --- Dark gradient overlay at top for title ---
for y in range(0, 700):
    alpha = int(180 * (1 - y / 700) ** 1.5)
    draw.line([(0, y), (TARGET_W, y)], fill=(10, 10, 15, alpha))

# Need RGBA for proper overlay
img = img.convert('RGBA')
overlay = Image.new('RGBA', (TARGET_W, TARGET_H), (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)

# Top gradient for title
for y in range(0, 750):
    alpha = int(190 * (1 - y / 750) ** 1.8)
    overlay_draw.line([(0, y), (TARGET_W, y)], fill=(5, 5, 10, alpha))

# Bottom gradient for author
for y in range(TARGET_H - 500, TARGET_H):
    progress = (y - (TARGET_H - 500)) / 500
    alpha = int(170 * progress ** 1.5)
    overlay_draw.line([(0, y), (TARGET_W, y)], fill=(5, 5, 10, alpha))

img = Image.alpha_composite(img, overlay).convert('RGB')
draw = ImageDraw.Draw(img)

# --- Title text ---
font_title = ImageFont.truetype(f'{FONT_DIR}/EBGaramond.ttf', 120)
font_subtitle = ImageFont.truetype(f'{FONT_DIR}/EBGaramond-Italic.ttf', 52)
font_author = ImageFont.truetype(f'{FONT_DIR}/EBGaramond.ttf', 56)
font_imprint = ImageFont.truetype(f'{FONT_DIR}/EBGaramond-Italic.ttf', 36)

# Title — two lines
title_color = (245, 240, 230)
subtitle_color = (210, 205, 195)
author_color = (235, 230, 220)
imprint_color = (180, 175, 165)

# "Is Baptism" line
line1 = "Is Baptism"
bbox1 = draw.textbbox((0, 0), line1, font=font_title)
w1 = bbox1[2] - bbox1[0]
draw.text(((TARGET_W - w1) / 2, 100), line1, fill=title_color, font=font_title)

# "Really Necessary?" line
line2 = "Really Necessary?"
bbox2 = draw.textbbox((0, 0), line2, font=font_title)
w2 = bbox2[2] - bbox2[0]
draw.text(((TARGET_W - w2) / 2, 240), line2, fill=title_color, font=font_title)

# Subtitle
sub = "A study from the Scriptures alone"
bbox_sub = draw.textbbox((0, 0), sub, font=font_subtitle)
w_sub = bbox_sub[2] - bbox_sub[0]
draw.text(((TARGET_W - w_sub) / 2, 410), sub, fill=subtitle_color, font=font_subtitle)

# --- Author at bottom ---
author = "Paul Hainline"
bbox_a = draw.textbbox((0, 0), author, font=font_author)
w_a = bbox_a[2] - bbox_a[0]
draw.text(((TARGET_W - w_a) / 2, TARGET_H - 260), author, fill=author_color, font=font_author)

# Imprint
imprint = "NobleMind Press"
bbox_i = draw.textbbox((0, 0), imprint, font=font_imprint)
w_i = bbox_i[2] - bbox_i[0]
draw.text(((TARGET_W - w_i) / 2, TARGET_H - 170), imprint, fill=imprint_color, font=font_imprint)

# --- Save ---
img.save(OUT, 'PNG', dpi=(300, 300))
print(f'Cover saved: {OUT} ({TARGET_W}x{TARGET_H} @ 300dpi)')
