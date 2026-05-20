#!/usr/bin/env python3
"""Finish a WhatLoveLooksLike panel for 8.5x11 print.

Workflow per image:
  1. Crop a thin strip off the bottom to remove the Gemini watermark
     (the sparkle logo lives in the bottom-right corner of every Gemini
     image; cropping the full bottom strip is the cleanest fix and only
     costs a sliver of negative space, since the locked-template puts
     subjects in the lower two-thirds and reserves the TOP third for
     text overlay anyway).
  2. Center-crop to 8.5x11 aspect ratio (portrait or landscape).
     For portrait targets from a 4:3 portrait source the aspect is
     already very close, so almost no content is lost. Landscape
     targets from portrait sources are destructive (~50% loss) — only
     use for panels that were generated landscape natively.
  3. Upscale to 300 DPI using LANCZOS.

Default output: WhatLoveLooksLike/print/<source_filename>

Usage:
  python finish_panel.py love-is-not-jealous.png
  python finish_panel.py love-is-kind_gemini.png --landscape
  python finish_panel.py --all                      # every PNG in the dir
  python finish_panel.py love-is-patient-chatgpt.png --no-watermark-crop

Future upgrade path: for sharper results, post-process the output through
Real-ESRGAN (4x model) or Topaz Gigapixel. LANCZOS at 2.4x is acceptable
for a wall viewed from > 6 feet but soft up close.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

DPI = 300
PORTRAIT_W  = int(8.5  * DPI)   # 2550
PORTRAIT_H  = int(11.0 * DPI)   # 3300
LANDSCAPE_W = int(11.0 * DPI)   # 3300
LANDSCAPE_H = int(8.5  * DPI)   # 2550

# Gemini watermark sits ~30-50px tall in the bottom-right of a ~1408-tall
# image. Cropping 6% of height (~85px on a 1408 image) gives a safe margin.
WATERMARK_BOTTOM_FRACTION = 0.06

BOOK_DIR = Path(__file__).parent
OUT_DIR  = BOOK_DIR / "print"


def finish(src_path: Path, orientation: str, strip_watermark: bool) -> Path:
    print(f"\n{src_path.name}")
    img = Image.open(src_path).convert("RGB")
    sw, sh = img.size
    print(f"  source:           {sw}x{sh}")

    # 1. Strip Gemini watermark
    if strip_watermark:
        crop_bottom = int(sh * WATERMARK_BOTTOM_FRACTION)
        img = img.crop((0, 0, sw, sh - crop_bottom))
        sw, sh = img.size
        print(f"  watermark cut:    {sw}x{sh}  (removed {crop_bottom}px from bottom)")

    # 2. Crop to target aspect (center horizontally; bias top-crop downward
    #    so the upper-third negative space stays clear for text overlay)
    if orientation == "portrait":
        target_aspect = PORTRAIT_W / PORTRAIT_H
        target_final  = (PORTRAIT_W, PORTRAIT_H)
    else:
        target_aspect = LANDSCAPE_W / LANDSCAPE_H
        target_final  = (LANDSCAPE_W, LANDSCAPE_H)

    src_aspect = sw / sh
    if abs(src_aspect - target_aspect) < 0.001:
        pass  # already matches
    elif src_aspect > target_aspect:
        new_w = int(round(sh * target_aspect))
        x_off = (sw - new_w) // 2
        img = img.crop((x_off, 0, x_off + new_w, sh))
    else:
        new_h = int(round(sw / target_aspect))
        excess = sh - new_h
        # Bias: 25% of the excess from the top, 75% from the bottom.
        # Keeps subject grounded in lower portion and preserves more of
        # the upper-third negative space for verse text overlay.
        y_off = excess // 4
        img = img.crop((0, y_off, sw, y_off + new_h))
    sw, sh = img.size
    print(f"  aspect-cropped:   {sw}x{sh}  (target aspect {target_aspect:.4f})")

    # 3. Upscale to print resolution
    img = img.resize(target_final, Image.LANCZOS)
    print(f"  upscaled:         {target_final[0]}x{target_final[1]} @ {DPI} DPI")

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / src_path.name
    img.save(out_path, "PNG", optimize=True, dpi=(DPI, DPI))
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  saved:            {out_path.relative_to(BOOK_DIR)}  ({size_mb:.1f} MB)")
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Finish WLLL panels for 8.5x11 print.")
    ap.add_argument("image", nargs="?", help="path to source PNG (or use --all)")
    ap.add_argument("--all", action="store_true",
                    help="process every PNG in WhatLoveLooksLike/ (skips print/)")
    ap.add_argument("--landscape", action="store_true",
                    help="output 11x8.5 landscape instead of 8.5x11 portrait")
    ap.add_argument("--no-watermark-crop", action="store_true",
                    help="skip the bottom-strip crop (use for non-Gemini sources)")
    args = ap.parse_args()

    orientation = "landscape" if args.landscape else "portrait"
    strip_wm = not args.no_watermark_crop

    if args.all:
        sources = sorted(p for p in BOOK_DIR.glob("*.png")
                         if "print" not in p.parts)
        if not sources:
            sys.exit("No PNGs found in WhatLoveLooksLike/")
        for src in sources:
            finish(src, orientation, strip_wm)
    else:
        if not args.image:
            ap.error("provide an image filename or use --all")
        src = Path(args.image)
        if not src.is_absolute():
            src = BOOK_DIR / src
        if not src.exists():
            sys.exit(f"Not found: {src}")
        finish(src, orientation, strip_wm)


if __name__ == "__main__":
    main()
