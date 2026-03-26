#!/usr/bin/env python3
"""Generate The God Who Showed Up PDF from HTML chapter files.

Produces a nicely formatted PDF with:
  - Cover page (image with title/author overlay)
  - Title page
  - Copyright page
  - Table of Contents
  - Introduction + 12 chapters + Conclusion
  - Scripture Index
"""

import re
from pathlib import Path
from collections import defaultdict
from io import BytesIO
import base64

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "The_God_Who_Showed_Up.pdf"
COVER_IMAGE = Path(__file__).parent.parent / "ANewAndLivingWay" / "lord_teach_us_to_pray.png"
FONT_DIR = Path.home() / ".local/share/fonts"

CHAPTERS = [
    ("introduction.html", None, "What\u2019s In A Name?", None),
    ("chapter-01.html", "Chapter 1", "Elohim \u2014 The God Who Was Already There", "Part I: The God Who Hears"),
    ("chapter-02.html", "Chapter 2", "El Roi \u2014 The God Who Sees", "Part I: The God Who Hears"),
    ("chapter-03.html", "Chapter 3", "El Shaddai \u2014 God Almighty", "Part I: The God Who Hears"),
    ("chapter-04.html", "Chapter 4", "Jehovah Jireh \u2014 The Lord Will Provide", "Part II: When the Veil Still Stood"),
    ("chapter-05.html", "Chapter 5", "Yahweh \u2014 The Self-Existent One", "Part II: When the Veil Still Stood"),
    ("chapter-06.html", "Chapter 6", "Jehovah Rapha \u2014 The Lord Who Heals", "Part III: The Veil Is Torn"),
    ("chapter-07.html", "Chapter 7", "Jehovah Nissi \u2014 The Lord Is My Banner", "Part III: The Veil Is Torn"),
    ("chapter-08.html", "Chapter 8", "Jehovah Shalom \u2014 The Lord Is Peace", "Part IV: Through the Open Door"),
    ("chapter-09.html", "Chapter 9", "Jehovah Rohi \u2014 The Lord Is My Shepherd", "Part IV: Through the Open Door"),
    ("chapter-10.html", "Chapter 10", "Jehovah Tsidkenu \u2014 The Lord Our Righteousness", "Part V: The Life of Prayer"),
    ("chapter-11.html", "Chapter 11", "Jehovah Shammah \u2014 The Lord Is There", "Part V: The Life of Prayer"),
    ("chapter-12.html", "Chapter 12", "Immanuel \u2014 God With Us", "Part V: The Life of Prayer"),
    ("conclusion.html", None, "He Is Still Showing Up", None),
]

SCRIPTURE_RE = re.compile(
    r'(?:'
    r'(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|'
    r'1\s*Samuel|2\s*Samuel|1\s*Kings|2\s*Kings|1\s*Chronicles|2\s*Chronicles|'
    r'Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|Ecclesiastes|Song\s*of\s*Solomon|'
    r'Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|'
    r'Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|'
    r'Matthew|Mark|Luke|John|Acts|Romans|'
    r'1\s*Corinthians|2\s*Corinthians|Galatians|Ephesians|Philippians|Colossians|'
    r'1\s*Thessalonians|2\s*Thessalonians|1\s*Timothy|2\s*Timothy|Titus|Philemon|'
    r'Hebrews|James|1\s*Peter|2\s*Peter|1\s*John|2\s*John|3\s*John|Jude|Revelation)'
    r')\s+'
    r'(\d+(?::\d+(?:\s*[-\u2013]\s*\d+)*)?)(?:\s*[-\u2013]\s*\d+(?::\d+)?)?',
    re.IGNORECASE,
)


def generate_cover_image():
    """Create cover image with title and author overlaid."""
    src = Image.open(COVER_IMAGE).convert("RGB")
    src_w, src_h = src.size

    cover_w, cover_h = 1650, 2550
    target_ratio = cover_w / cover_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        scale = cover_h / src_h
        new_h = cover_h
        new_w = int(src_w * scale)
        img_scaled = src.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - cover_w) // 2
        img_scaled = img_scaled.crop((left, 0, left + cover_w, cover_h))
    else:
        scale = cover_w / src_w
        new_w = cover_w
        new_h = int(src_h * scale)
        img_scaled = src.resize((new_w, new_h), Image.LANCZOS)
        top = (new_h - cover_h) // 2
        img_scaled = img_scaled.crop((0, top, cover_w, top + cover_h))

    img_rgba = img_scaled.convert("RGBA")
    draw = ImageDraw.Draw(img_rgba)
    w, h = cover_w, cover_h

    # Text colors — warm cream/gold to complement the painting
    title_color = (245, 235, 215)
    subtitle_color = (225, 210, 180)
    author_color = (240, 230, 210)

    # Semi-transparent overlay at top and bottom for text readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    # Top gradient band
    for y in range(0, 380):
        alpha = int(160 * (1 - y / 380))
        overlay_draw.line([(0, y), (w, y)], fill=(15, 12, 8, alpha))
    # Bottom band
    for y in range(h - 200, h):
        alpha = int(140 * ((y - (h - 200)) / 200))
        overlay_draw.line([(0, y), (w, y)], fill=(15, 12, 8, alpha))
    img_rgba = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(img_rgba)

    try:
        font_title = ImageFont.truetype(str(FONT_DIR / "EBGaramond.ttf"), 72)
        font_subtitle = ImageFont.truetype(str(FONT_DIR / "EBGaramond-Italic.ttf"), 30)
        font_author = ImageFont.truetype(str(FONT_DIR / "EBGaramond.ttf"), 38)
    except OSError:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 65)
        font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", 28)
        font_author = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 36)

    # Title at top
    lines = ["The God Who", "Showed Up"]
    y_pos = 65
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x, y_pos), line, font=font_title, fill=title_color)
        y_pos += 95

    # Subtitle
    subtitle = "What His Names Reveal About Who He Is"
    bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    tw = bbox[2] - bbox[0]
    x = (w - tw) // 2
    draw.text((x, y_pos + 15), subtitle, font=font_subtitle, fill=subtitle_color)

    # Author at bottom
    author_text = "Paul & Pam Hainline"
    bbox = draw.textbbox((0, 0), author_text, font=font_author)
    tw = bbox[2] - bbox[0]
    x = (w - tw) // 2
    y = h - 120
    draw.text((x, y), author_text, font=font_author, fill=author_color)

    final = Image.new("RGB", img_rgba.size, (255, 255, 255))
    final.paste(img_rgba, mask=img_rgba.split()[3])

    buf = BytesIO()
    final.save(buf, format="PNG", quality=95)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def extract_content(filepath):
    """Extract the body content from a chapter HTML file."""
    soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "html.parser")
    content_div = soup.find("div", class_="content")
    if not content_div:
        return ""

    parts = []
    for el in content_div.children:
        if hasattr(el, "name") and el.name:
            skip_classes = {"nav-controls", "mark-complete", "footer-nav"}
            el_classes = set(el.get("class", []))
            if el_classes & skip_classes:
                continue

            if el.name == "div" and "divider" in el_classes:
                parts.append('<div class="divider">*&emsp;*&emsp;*</div>')
            elif el.name == "blockquote" and "scripture" in el_classes:
                parts.append(str(el))
            elif el.name == "div" and "principle-box" in el_classes:
                parts.append(str(el))
            elif el.name in ("p", "h2", "h3", "blockquote"):
                parts.append(str(el))

    return "\n".join(parts)


def extract_scripture_refs(filepath, chapter_label):
    """Extract scripture references from a chapter HTML file."""
    text = filepath.read_text(encoding="utf-8")
    soup = BeautifulSoup(text, "html.parser")
    content = soup.find("div", class_="content")
    if not content:
        return []

    plain = content.get_text()
    refs = []
    for match in SCRIPTURE_RE.finditer(plain):
        ref = match.group(0).strip()
        ref = re.sub(r'\s+', ' ', ref)
        ref = ref.rstrip('.,;:)')
        refs.append(ref)
    return refs


def build_scripture_index():
    """Build scripture index from all chapters."""
    ref_to_chapters = defaultdict(set)

    for filename, ch_num, title, part in CHAPTERS:
        filepath = BOOK_DIR / filename
        label = ch_num if ch_num else ("Introduction" if "intro" in filename else "Conclusion")
        refs = extract_scripture_refs(filepath, label)
        for ref in refs:
            ref_to_chapters[ref].add(label)

    BOOK_ORDER = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
        "Ezra", "Nehemiah", "Esther", "Job", "Psalm", "Psalms", "Proverbs",
        "Ecclesiastes", "Song of Solomon",
        "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
        "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
        "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
        "1 Timothy", "2 Timothy", "Titus", "Philemon",
        "Hebrews", "James", "1 Peter", "2 Peter",
        "1 John", "2 John", "3 John", "Jude", "Revelation",
    ]

    def book_sort_key(ref):
        for i, book in enumerate(BOOK_ORDER):
            if ref.startswith(book):
                rest = ref[len(book):].strip()
                parts = re.split(r'[:\-\u2013]', rest)
                nums = []
                for p in parts:
                    p = p.strip()
                    if p.isdigit():
                        nums.append(int(p))
                return (i, nums)
        return (999, [])

    def ch_sort_key(label):
        if label == "Introduction":
            return 0
        if label == "Conclusion":
            return 99
        m = re.search(r'(\d+)', label)
        return int(m.group(1)) if m else 0

    sorted_refs = sorted(ref_to_chapters.keys(), key=book_sort_key)

    entries = []
    current_book = None
    for ref in sorted_refs:
        book_match = re.match(r'((?:\d\s*)?[A-Za-z]+(?:\s+of\s+\w+)?)\s', ref)
        if book_match:
            book = book_match.group(1).strip()
            if book == "Psalms":
                book = "Psalm"
        else:
            book = ref

        if book != current_book:
            current_book = book
            entries.append(f'<div class="si-book">{book}</div>')

        chapters = sorted(ref_to_chapters[ref], key=ch_sort_key)
        ch_list = ", ".join(chapters)
        entries.append(f'<div class="si-entry"><span class="si-ref">{ref}</span> <span class="si-chapters">{ch_list}</span></div>')

    return "\n".join(entries)


def build_chapter_html(filename, chapter_num, title, part):
    """Build the HTML section for a single chapter."""
    filepath = BOOK_DIR / filename
    content = extract_content(filepath)

    header_parts = []
    if chapter_num:
        header_parts.append(f'<p class="chapter-num">{chapter_num}</p>')
    elif "intro" in filename:
        header_parts.append('<p class="chapter-num">Introduction</p>')
    else:
        header_parts.append('<p class="chapter-num">Conclusion</p>')
    header_parts.append(f"<h1>{title}</h1>")
    if part:
        header_parts.append(f'<p class="part-subtitle"><em>{part}</em></p>')

    return f"""
    <section class="chapter">
      <div class="chapter-header">
        {"".join(header_parts)}
      </div>
      <div class="chapter-body">
        {content}
      </div>
    </section>
    """


def build_toc():
    """Build the table of contents."""
    items = []
    items.append('<div class="toc-entry"><span>Introduction: What\u2019s In A Name?</span></div>')

    current_part = None
    for filename, ch_num, title, part in CHAPTERS[1:-1]:  # skip intro and conclusion
        if part != current_part:
            current_part = part
            items.append(f'<div class="toc-part"><strong>{part}</strong></div>')
        if ch_num:
            num = ch_num.replace("Chapter ", "")
            items.append(
                f'<div class="toc-entry toc-chapter">'
                f'<span>Chapter {num}: {title}</span>'
                f'</div>'
            )

    items.append('<div class="toc-entry" style="margin-top: 12pt;"><span>Conclusion: He Is Still Showing Up</span></div>')
    items.append('<div class="toc-entry"><span>Scripture Index</span></div>')
    return "\n".join(items)


CSS = """
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Italic'), local('EB Garamond');
    font-weight: normal;
    font-style: italic;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold'), local('EB Garamond');
    font-weight: bold;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold Italic'), local('EB Garamond');
    font-weight: bold;
    font-style: italic;
}

@page {
    size: 5.5in 8.5in;
    margin: 0.85in 0.75in 0.9in 0.75in;
    @bottom-center {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #333;
    }
}

@page :first { @bottom-center { content: none; } }
@page cover-page { margin: 0; @bottom-center { content: none; } }
@page title-page { @bottom-center { content: none; } }
@page copyright-page { @bottom-center { content: none; } }
@page toc-page { @bottom-center { content: none; } }

body {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    text-rendering: optimizeLegibility;
}

.cover-page { page: cover-page; page-break-after: always; }
.cover-page img { width: 5.5in; height: 8.5in; object-fit: cover; display: block; }

.title-page {
    page: title-page;
    page-break-after: always;
    text-align: center;
    padding-top: 2in;
}
.title-page h1 { font-size: 26pt; font-weight: bold; line-height: 1.25; margin-bottom: 0.2in; color: #1a1a1a; }
.title-page .subtitle-line { font-size: 12pt; font-style: italic; color: #444; margin-bottom: 6pt; }
.title-page .author { font-size: 14pt; margin-top: 0.8in; color: #1a1a1a; }
.title-page .anchor-verse { margin-top: 0.8in; font-size: 10pt; font-style: italic; color: #444; line-height: 1.6; max-width: 3.5in; margin-left: auto; margin-right: auto; page-break-inside: avoid; }
.title-page .anchor-cite { font-style: normal; font-size: 9.5pt; color: #555; }

.copyright-page {
    page: copyright-page;
    page-break-after: always;
    text-align: center;
    padding-top: 3in;
    font-size: 9.5pt;
    line-height: 1.7;
    color: #444;
}
.copyright-page p { margin-bottom: 10pt; }
.copyright-page .edition { margin-top: 18pt; }

.toc-section { page: toc-page; page-break-after: always; }
.toc-section h1 { font-size: 18pt; font-weight: bold; margin-bottom: 0.35in; color: #1a1a1a; text-align: center; }
.toc-part { margin-top: 16pt; margin-bottom: 6pt; font-size: 10.5pt; color: #1a1a1a; }
.toc-entry { font-size: 10.5pt; line-height: 1.8; color: #333; }
.toc-chapter { padding-left: 0.25in; }

.chapter { page-break-before: always; }
.chapter-header { text-align: center; margin-bottom: 0.3in; padding-bottom: 0.15in; }
.chapter-header .chapter-num { font-size: 10pt; letter-spacing: 0.08em; color: #555; margin-bottom: 2pt; text-transform: uppercase; }
.chapter-header h1 { font-size: 20pt; font-weight: bold; color: #1a1a1a; margin-bottom: 6pt; line-height: 1.2; }
.chapter-header .part-subtitle { font-size: 10.5pt; color: #555; margin-top: 2pt; }

.chapter-body p { text-align: justify; text-indent: 0.3in; margin-bottom: 0; margin-top: 0; orphans: 2; widows: 2; }
.chapter-body h2 + p, .chapter-body .divider + p, .chapter-body .scripture + p,
.chapter-body .principle-box + p, .chapter-body .epigraph + p { text-indent: 0; }
.chapter-body > p:first-child { text-indent: 0; }

.chapter-body h2 { font-size: 13pt; font-weight: bold; color: #1a1a1a; margin-top: 0.3in; margin-bottom: 0.12in; page-break-after: avoid; }
.chapter-body h3 { font-size: 12pt; font-weight: bold; font-style: italic; color: #333; margin-top: 0.25in; margin-bottom: 0.1in; page-break-after: avoid; }

blockquote.scripture {
    margin: 0.15in 0 0.15in 0.4in; padding: 0;
    font-style: italic; font-size: 10.5pt; line-height: 1.5;
    border: none; background: none; border-left: none; border-radius: 0;
}
blockquote.scripture p { text-indent: 0 !important; text-align: left; margin-bottom: 0; }
blockquote.scripture cite { display: block; margin-top: 3pt; font-style: normal; font-weight: 500; font-size: 9.5pt; color: #444; }

blockquote:not(.scripture) {
    margin: 0.15in 0 0.15in 0.4in; padding: 0;
    font-style: italic; font-size: 10.5pt; line-height: 1.5;
    border: none; background: none;
}
blockquote:not(.scripture) p { text-indent: 0 !important; text-align: left; margin-bottom: 0; }
blockquote:not(.scripture) cite { display: block; margin-top: 3pt; font-style: normal; font-weight: 500; font-size: 9.5pt; color: #444; }

.principle-box { margin: 0.18in 0.3in; padding: 0.12in 0.18in; border-left: 2pt solid #666; font-size: 10.5pt; }
.principle-box p { text-indent: 0 !important; text-align: left; }

.divider { text-align: center; margin: 0.2in 0; color: #888; font-size: 10pt; letter-spacing: 0.15em; }

.scripture-index { page-break-before: always; }
.scripture-index h1 { font-size: 18pt; font-weight: bold; margin-bottom: 0.3in; text-align: center; color: #1a1a1a; }
.si-book { font-weight: bold; font-size: 11pt; margin-top: 12pt; margin-bottom: 4pt; color: #1a1a1a; }
.si-entry { font-size: 10pt; line-height: 1.7; padding-left: 0.2in; color: #333; }
.si-chapters { color: #555; font-style: italic; }

em { font-style: italic; }
strong { font-weight: bold; }
"""


def build_full_html(cover_b64, chapter_sections, toc_html, scripture_index_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <div class="cover-page">
    <img src="data:image/png;base64,{cover_b64}" alt="Cover">
  </div>

  <div class="title-page">
    <h1>The God Who<br>Showed Up</h1>
    <p class="subtitle-line">What His Names Reveal About Who He Is</p>
    <p class="author">Paul &amp; Pam Hainline</p>
    <p class="anchor-verse">
      &ldquo;Then Moses said to God, &lsquo;Behold, I am going to the sons
      of Israel, and I will say to them, &ldquo;The God of your fathers has
      sent me to you.&rdquo; Now they may say to me, &ldquo;What is His name?&rdquo;
      What shall I say to them?&rsquo; God said to Moses, &lsquo;I AM WHO I AM.&rsquo;&rdquo;
      <br><span class="anchor-cite">&mdash; Exodus 3:13&ndash;14 (NASB)</span>
    </p>
  </div>

  <div class="copyright-page">
    <p><em>The God Who Showed Up: What His Names Reveal About Who He Is</em></p>
    <p>Copyright &copy; 2026 Paul &amp; Pam Hainline<br>All rights reserved.</p>
    <p>Scripture quotations are from the New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p class="edition">First Edition &mdash; NobleMind Press</p>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {chapter_sections}

  <div class="scripture-index">
    <h1>Scripture Index</h1>
    {scripture_index_html}
  </div>

</body>
</html>"""


def main():
    print("Generating cover image with title overlay...")
    cover_b64 = generate_cover_image()
    print("  Cover image ready.")

    print("Extracting chapter content...")
    chapter_sections = []
    for filename, ch_num, title, part in CHAPTERS:
        print(f"  {filename}")
        chapter_sections.append(build_chapter_html(filename, ch_num, title, part))

    print("Building table of contents...")
    toc_html = build_toc()

    print("Building scripture index...")
    scripture_index_html = build_scripture_index()

    print("Assembling HTML...")
    full_html = build_full_html(
        cover_b64, "\n".join(chapter_sections), toc_html, scripture_index_html
    )

    debug_html = BOOK_DIR / "_book_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")
    print(f"  Debug HTML saved to {debug_html}")

    print("Generating PDF with WeasyPrint (this may take a minute)...")
    doc = weasyprint.HTML(string=full_html)
    doc.write_pdf(str(OUTPUT))
    print(f"\nPDF saved to {OUTPUT}")

    debug_html.unlink(missing_ok=True)
    print("Done.")


if __name__ == "__main__":
    main()
