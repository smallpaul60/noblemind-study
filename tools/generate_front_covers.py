#!/usr/bin/env python3
"""Generate front cover images for books that lack publisher cover PDFs.

Produces 400px-wide JPG front covers with title/subtitle/author overlaid
on artwork, matching the style of existing Lulu covers (EB Garamond,
gradient overlays for readability).
"""

from pathlib import Path
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import Color, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import subprocess
import tempfile

BOOK_DIR = Path(__file__).parent.parent
FONT_DIR = Path.home() / ".local/share/fonts"

pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))

# Cover dimensions (5.5" x 8.5" at 300 DPI)
COVER_W = 5.5 * inch
COVER_H = 8.5 * inch

CREAM = Color(0.961, 0.902, 0.784)


BOOKS = [
    {
        "dir": "OneDayCloserToHome",
        "image": "One Day Closer to Home.png",
        "bg_color": Color(0.08, 0.06, 0.04),
        "title_lines": [
            ("EBGaramond-Italic", 20, "One Day Closer"),
            ("EBGaramond", 44, "to Home"),
        ],
        "subtitle_lines": [
            "A Book of Hope for Those",
            "in the Final Chapters",
        ],
        "author": "P A U L   H A I N L I N E",
        "title_color": CREAM,
        "subtitle_color": CREAM,
        "overlay_color": (0.06, 0.04, 0.02),
        "top_alpha": 0.55,
        "bottom_alpha": 0.50,
    },
    {
        "dir": "TheGodWhoShowedUp",
        "image": "TheBurningBush.png",
        "bg_color": Color(0.08, 0.04, 0.02),
        "title_lines": [
            ("EBGaramond-Italic", 18, "The God Who"),
            ("EBGaramond", 42, "Showed Up"),
        ],
        "subtitle_lines": [
            "What His Names Reveal",
            "About Who He Is",
        ],
        "author": "P A U L   &   P A M   H A I N L I N E",
        "title_color": CREAM,
        "subtitle_color": CREAM,
        "overlay_color": (0.04, 0.02, 0.01),
        "top_alpha": 0.60,
        "bottom_alpha": 0.55,
    },
    {
        "dir": "ANewAndLivingWay",
        "image": "in_the_garden.png",
        "bg_color": Color(0.04, 0.06, 0.08),
        "title_lines": [
            ("EBGaramond-Italic", 18, "A New and"),
            ("EBGaramond", 42, "Living Way"),
        ],
        "subtitle_lines": [
            "What the Bible Teaches",
            "About Prayer",
        ],
        "author": "P A U L   H A I N L I N E",
        "title_color": CREAM,
        "subtitle_color": CREAM,
        "overlay_color": (0.04, 0.05, 0.08),
        "top_alpha": 0.60,
        "bottom_alpha": 0.55,
    },
]


def draw_cover(book):
    """Generate a single front cover as cover_front.jpg."""
    book_path = BOOK_DIR / book["dir"]
    img_path = book_path / book["image"]
    output_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    output_jpg = book_path / "cover_front.jpg"

    c = canvas.Canvas(output_pdf.name, pagesize=(COVER_W, COVER_H))

    # Background color
    c.setFillColor(book["bg_color"])
    c.rect(0, 0, COVER_W, COVER_H, fill=1, stroke=0)

    # Background image — scale to fill
    img = ImageReader(str(img_path))
    img_w, img_h = img.getSize()
    img_aspect = img_w / img_h
    cover_aspect = COVER_W / COVER_H

    if img_aspect > cover_aspect:
        draw_h = COVER_H
        draw_w = COVER_H * img_aspect
        draw_x = (COVER_W - draw_w) / 2
        draw_y = 0
    else:
        draw_w = COVER_W
        draw_h = COVER_W / img_aspect
        draw_x = 0
        draw_y = (COVER_H - draw_h) / 2

    c.saveState()
    path = c.beginPath()
    path.rect(0, 0, COVER_W, COVER_H)
    path.close()
    c.clipPath(path, stroke=0)
    c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
    c.restoreState()

    # Top gradient overlay for title readability
    r, g, b = book["overlay_color"]
    steps = 40
    grad_height = 4.0 * inch
    c.saveState()
    for i in range(steps):
        alpha = book["top_alpha"] * (1 - i / steps) ** 1.5
        c.setFillColor(Color(r, g, b, alpha))
        y = COVER_H - (i * grad_height / steps)
        h = grad_height / steps + 1
        c.rect(0, y - h, COVER_W, h, fill=1, stroke=0)
    c.restoreState()

    # Bottom gradient overlay for author readability
    bottom_grad_height = 2.0 * inch
    c.saveState()
    for i in range(steps):
        alpha = book["bottom_alpha"] * (i / steps) ** 1.5
        c.setFillColor(Color(r, g, b, alpha))
        y = bottom_grad_height * (1 - i / steps)
        h = bottom_grad_height / steps + 1
        c.rect(0, y - h, COVER_W, h, fill=1, stroke=0)
    c.restoreState()

    cx = COVER_W / 2

    # Title
    y = COVER_H - 1.4 * inch
    c.setFillColor(book["title_color"])
    for font, size, text in book["title_lines"]:
        c.setFont(font, size)
        c.drawCentredString(cx, y, text)
        y -= size * 1.4

    # Subtitle
    y -= 0.15 * inch
    c.setFillColor(book["subtitle_color"])
    c.setFont("EBGaramond-Italic", 13)
    for line in book["subtitle_lines"]:
        c.drawCentredString(cx, y, line)
        y -= 17

    # Author
    c.setFillColor(book["title_color"])
    c.setFont("EBGaramond", 16)
    c.drawCentredString(cx, 0.5 * inch + 0.2 * inch, book["author"])

    c.save()

    # Convert PDF to JPG
    subprocess.run([
        "pdftoppm", "-jpeg", "-r", "300", "-f", "1", "-l", "1",
        output_pdf.name, output_pdf.name + "_img"
    ], check=True)

    rendered = Path(output_pdf.name + "_img-1.jpg")
    subprocess.run([
        "convert", str(rendered),
        "-resize", "400x",
        "-quality", "88",
        str(output_jpg),
    ], check=True)

    rendered.unlink()
    Path(output_pdf.name).unlink()

    print(f"  {book['dir']}/cover_front.jpg")


def main():
    print("Generating front cover images...")
    for book in BOOKS:
        draw_cover(book)
    print("Done.")


if __name__ == "__main__":
    main()
