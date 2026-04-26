#!/usr/bin/env python3
"""Render cover_front.jpg and cover_thumb.jpg by extracting the front
panel of the paperback cover PDF.

Run AFTER generate_lulu_paperback_cover.py — uses that PDF as the source
so the website thumb stays in sync with the print cover.
"""

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

BOOK_DIR = Path(__file__).parent
COVER_PDF = BOOK_DIR / "Why_The_Division_Lulu_Paperback_Cover.pdf"
FRONT_OUT = BOOK_DIR / "cover_front.jpg"
THUMB_OUT = BOOK_DIR / "cover_thumb.jpg"

# Cover PDF layout (must match generate_lulu_paperback_cover.py):
BLEED = 0.125
TRIM_W = 5.5
TRIM_H = 8.5
PAGE_COUNT = 170
SPINE_W = round(PAGE_COUNT * 0.0029, 3)

DOC_W = BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED
DOC_H = BLEED + TRIM_H + BLEED

# Front face starts after BLEED + TRIM (back) + SPINE; ends at DOC_W - BLEED.
FRONT_LEFT_IN  = BLEED + TRIM_W + SPINE_W
FRONT_RIGHT_IN = DOC_W - BLEED
TOP_TRIM_IN    = BLEED
BOT_TRIM_IN    = DOC_H - BLEED

# Render at 300 DPI for a sharp full-size JPG; then downsample for the thumb.
DPI = 300


def main():
    if not COVER_PDF.exists():
        raise SystemExit(f"Cover PDF not found: {COVER_PDF}\n"
                         "Run generate_lulu_paperback_cover.py first.")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp) / "cover"
        # pdftoppm renders the whole spread; we crop afterward.
        subprocess.check_call([
            "pdftoppm",
            "-r", str(DPI),
            "-jpeg",
            "-jpegopt", "quality=92",
            "-f", "1", "-l", "1",
            str(COVER_PDF),
            str(tmp_root),
        ])
        rendered = sorted(Path(tmp).glob("cover-*.jpg"))
        if not rendered:
            raise SystemExit("pdftoppm produced no output.")
        full = Image.open(rendered[0])

        # Crop the front face (in pixels). Trim away the bleed so the JPG
        # matches the printed trim — this is what readers see on the book.
        px_per_in = DPI
        crop = full.crop((
            int(FRONT_LEFT_IN * px_per_in),
            int(TOP_TRIM_IN  * px_per_in),
            int(FRONT_RIGHT_IN * px_per_in),
            int(BOT_TRIM_IN  * px_per_in),
        ))
        # Save full-size cover_front.jpg
        crop.save(FRONT_OUT, "JPEG", quality=90, optimize=True)
        print(f"Wrote {FRONT_OUT.name}  {crop.size[0]}x{crop.size[1]}")

        # Thumb: target ~360px wide (matches the books.html card slot).
        thumb_w = 360
        thumb_h = round(crop.size[1] * (thumb_w / crop.size[0]))
        thumb = crop.resize((thumb_w, thumb_h), Image.LANCZOS)
        thumb.save(THUMB_OUT, "JPEG", quality=85, optimize=True)
        print(f"Wrote {THUMB_OUT.name}  {thumb.size[0]}x{thumb.size[1]}")


if __name__ == "__main__":
    main()
