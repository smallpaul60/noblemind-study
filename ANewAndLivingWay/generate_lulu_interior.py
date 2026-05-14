#!/usr/bin/env python3
"""Generate Lulu print-ready interior — A New and Living Way PDF from HTML chapter files.

Produces a nicely formatted PDF with:
  - Cover page (image with title/author overlay)
  - Title page
  - Copyright page
  - Table of Contents
  - Author's Note + 12 chapters
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
OUTPUT = BOOK_DIR / "A_New_and_Living_Way_Lulu_Interior.pdf"
COVER_IMAGE = BOOK_DIR / "cover_front.jpg"
FONT_DIR = Path.home() / ".local/share/fonts"

CHAPTERS = [
    ("authors-note.html", None, "A Note from the Author", None),
    ("chapter-01.html", "Chapter 1", "A God Who Hears", "Part I: The God Who Hears"),
    ("chapter-02.html", "Chapter 2", "Who Are We That You Are Mindful of Us?", "Part I: The God Who Hears"),
    ("chapter-03.html", "Chapter 3", "From the Beginning: The First Cries", "Part II: When the Veil Still Stood"),
    ("chapter-04.html", "Chapter 4", "Abraham: The Friend of God", "Part II: When the Veil Still Stood"),
    ("chapter-05.html", "Chapter 5", "Moses: Face to Face", "Part II: When the Veil Still Stood"),
    ("chapter-06.html", "Chapter 6", "The Veil Is Torn", "Part III: The Veil Is Torn"),
    ("chapter-07.html", "Chapter 7", "Lord, Teach Us", "Part IV: Through the Open Door"),
    ("chapter-08.html", "Chapter 8", "In My Name", "Part IV: Through the Open Door"),
    ("chapter-09.html", "Chapter 9", "When God Says No", "Part IV: Through the Open Door"),
    ("chapter-10.html", "Chapter 10", "The Prayers of the Church", "Part V: The Life of Prayer"),
    ("chapter-11.html", "Chapter 11", "Standing in the Gap", "Part V: The Life of Prayer"),
    ("chapter-12.html", "Chapter 12", "A New and Living Way", "Part V: The Life of Prayer"),
]

# --- Scripture reference patterns ---
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
    """Return the composed cover_front.jpg as base64 for embedding.

    The cover (with title + subtitle + author typography baked in) is
    produced by generate_cover.py — this function just reads it so the
    PDF and the website card show the same image.
    """
    with open(COVER_IMAGE, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


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
        label = ch_num if ch_num else "Author\u2019s Note"
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
        if label == "Author\u2019s Note":
            return 0
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
    header_parts.append(f"<h1>{title}</h1>")

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
    items.append('<div class="toc-entry"><span>Author\u2019s Note</span></div>')

    current_part = None
    for filename, ch_num, title, part in CHAPTERS[1:]:
        if part != current_part:
            current_part = part
            items.append(f'<div class="toc-part"><strong>{part}</strong></div>')
        num = ch_num.replace("Chapter ", "")
        items.append(
            f'<div class="toc-entry toc-chapter">'
            f'<span>Chapter {num}: {title}</span>'
            f'</div>'
        )
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
    margin-top: 0.85in;
    margin-bottom: 0.9in;
}
@page :right {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #555;
    }
}
@page :left {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-left {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #555;
    }
}
@page front-matter {
    size: 5.5in 8.5in;
    margin-top: 0.85in; margin-bottom: 0.9in;
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
}
@page front-matter:right { margin-left: 0.75in; margin-right: 0.625in; }
@page front-matter:left  { margin-left: 0.625in; margin-right: 0.75in; }
@page toc-page {
    size: 5.5in 8.5in;
    margin-top: 0.85in; margin-bottom: 0.9in;
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
}
@page toc-page:right { margin-left: 0.75in; margin-right: 0.625in; }
@page toc-page:left  { margin-left: 0.625in; margin-right: 0.75in; }
@page part-div-page {
    size: 5.5in 8.5in;
    margin-top: 0.85in; margin-bottom: 0.9in;
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
}
@page part-div-page:right { margin-left: 0.75in; margin-right: 0.625in; }
@page part-div-page:left  { margin-left: 0.625in; margin-right: 0.75in; }
@page title-page {
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
}
@page title-page:right { margin-left: 0.75in; margin-right: 0.625in; }
@page title-page:left  { margin-left: 0.625in; margin-right: 0.75in; }
@page copyright-page {
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
}
@page copyright-page:right { margin-left: 0.75in; margin-right: 0.625in; }
@page copyright-page:left  { margin-left: 0.625in; margin-right: 0.75in; }
@page :blank {
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
}

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

blockquote.scripture {
    margin: 0.15in 0 0.15in 0.4in; padding: 0;
    font-style: italic; font-size: 10.5pt; line-height: 1.5;
    border: none; background: none; border-left: none; border-radius: 0;
}
blockquote.scripture p { text-indent: 0 !important; text-align: left; margin-bottom: 0; }
blockquote.scripture cite { display: block; margin-top: 3pt; font-style: normal; font-weight: 500; font-size: 9.5pt; color: #444; }

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


/* === LULU INTERIOR — half-title + part dividers + recto starts === */
.half-title-page {
    page: front-matter;
    break-before: right;
    page-break-after: always;
    text-align: center;
    padding-top: 3.2in;
}
.half-title-page h1 {
    font-size: 18pt; font-weight: normal; letter-spacing: 0.04em;
    color: #1a1a1a; line-height: 1.25;
}

.title-page          { break-before: right; }
.toc-section         { break-before: right; }
.chapter             { break-before: right; }
.scripture-index     { break-before: right; }

.part-page {
    page: part-div-page;
    break-before: right;
    page-break-after: always;
    text-align: center;
    padding-top: 3.0in;
}
.part-page .part-label {
    font-size: 11pt; letter-spacing: 0.22em; color: #666;
    text-transform: uppercase; margin-bottom: 16pt;
}
.part-page .part-title {
    font-size: 24pt; font-weight: normal; line-height: 1.25;
    color: #1a1a1a;
}
"""


def build_full_html(chapter_sections, toc_html, scripture_index_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <div class="half-title-page"><h1>A New and Living Way</h1></div>

  <div class="title-page">
    <h1>A New and<br>Living Way</h1>
    <p class="subtitle-line">What the Bible Teaches About Prayer</p>
    <p class="author">Paul Hainline</p>
    <p class="anchor-verse">
      &ldquo;Therefore, brethren, since we have confidence to enter the holy place
      by the blood of Jesus, by a new and living way which He inaugurated for us
      through the veil, that is, His flesh &hellip; let us draw near with a sincere
      heart in full assurance of faith.&rdquo;
      <br><span class="anchor-cite">&mdash; Hebrews 10:19&ndash;22 (NASB)</span>
    </p>
  </div>

  <div class="copyright-page">
    <p><em>A New and Living Way</em></p>
    <p>Copyright &copy; 2026 Paul Hainline<br>All rights reserved.</p>
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
    print("Skipping cover (Lulu interior is text block only)")

    print("Extracting chapter content...")
    chapter_sections = []
    current_part = None
    for filename, ch_num, title, part in CHAPTERS:
        if part and part != current_part:
            current_part = part
            label, _, ptitle = part.partition(": ")
            if not ptitle:
                label, ptitle = "", part
            chapter_sections.append(
                f'<section class="part-page">'
                f'<p class="part-label">{label}</p>'
                f'<h1 class="part-title">{ptitle}</h1>'
                f'</section>'
            )
        print(f"  {filename}")
        chapter_sections.append(build_chapter_html(filename, ch_num, title, part))

    print("Building table of contents...")
    toc_html = build_toc()

    print("Building scripture index...")
    scripture_index_html = build_scripture_index()

    print("Assembling HTML...")
    full_html = build_full_html("\n".join(chapter_sections), toc_html, scripture_index_html
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
