#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for The Character No One Could Invent.

Lulu specs for 5.5" x 8.5" Digest (no bleed, text-only):
  - Page size: 5.5in x 8.5in
  - Safety margin: 0.5in minimum on all sides
  - Gutter (inside margin): 0.75in (above 0.625in recommended for 61-150 pages)
  - Outside margin: 0.625in
  - Chapters start on recto (right-hand, odd) pages
  - Alternating left/right margins for facing pages
  - All fonts embedded
  - No trim/bleed/margin lines
"""

import sys
from pathlib import Path
from bs4 import BeautifulSoup
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "The_Character_No_One_Could_Invent_Lulu_Interior.pdf"

CHAPTERS = [
    "foreword.html",
    "chapter-01.html",
    "chapter-02.html",
    "chapter-03.html",
    "chapter-04.html",
    "chapter-05.html",
    "chapter-06.html",
    "chapter-07.html",
    "chapter-08.html",
    "chapter-09.html",
    "chapter-10.html",
    "chapter-11.html",
    "chapter-12.html",
    "chapter-13.html",
]

CHAPTER_TITLES = {
    "foreword.html": ("Foreword", None, None),
    "chapter-01.html": ("The Character in the Books", "Chapter 1", "Part I: Could They Have Invented Him?"),
    "chapter-02.html": ("The Writers vs. the Character", "Chapter 2", "Part I: Could They Have Invented Him?"),
    "chapter-03.html": ("Not a Myth", "Chapter 3", "Part I: Could They Have Invented Him?"),
    "chapter-04.html": ("Not a Natural Product", "Chapter 4", "Part I: Could They Have Invented Him?"),
    "chapter-05.html": ("How He Knew", "Chapter 5", "Part II: Unlike Any Mere Man"),
    "chapter-06.html": ("How He Taught", "Chapter 6", "Part II: Unlike Any Mere Man"),
    "chapter-07.html": ("What He Came to Do", "Chapter 7", "Part II: Unlike Any Mere Man"),
    "chapter-08.html": ("The Impossible Mission", "Chapter 8", "Part II: Unlike Any Mere Man"),
    "chapter-09.html": ("The Way of Perishing", "Chapter 9", "Part II: Unlike Any Mere Man"),
    "chapter-10.html": ("What He Claims", "Chapter 10", "Part III: His Claims and His Evidence"),
    "chapter-11.html": ("What He Built", "Chapter 11", "Part III: His Claims and His Evidence"),
    "chapter-12.html": ("The One Universal Man", "Chapter 12", "Part III: His Claims and His Evidence"),
    "chapter-13.html": ("The Verdict", "Chapter 13", "Part III: His Claims and His Evidence"),
}


def extract_content(filepath):
    """Extract the body content from a chapter HTML file."""
    soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "html.parser")
    content_div = soup.find("div", class_="content")
    if not content_div:
        return ""

    parts = []
    for el in content_div.children:
        if hasattr(el, "name") and el.name:
            if el.get("class") and any(
                c in el.get("class", [])
                for c in ["nav-controls", "mark-complete", "footer-nav"]
            ):
                continue

            if el.name == "div" and "divider" in el.get("class", []):
                parts.append('<div class="divider">*&emsp;*&emsp;*</div>')
            elif el.name == "blockquote" and "scripture" in el.get("class", []):
                parts.append(str(el))
            elif el.name == "div" and "principle-box" in el.get("class", []):
                parts.append(str(el))
            elif el.name == "section" and "epigraph" in el.get("class", []):
                parts.append(str(el))
            elif el.name in ("p", "h2", "h3", "blockquote"):
                parts.append(str(el))

    return "\n".join(parts)


def build_chapter_html(filename):
    """Build the HTML section for a single chapter."""
    filepath = BOOK_DIR / filename
    title, chapter_num, part_subtitle = CHAPTER_TITLES[filename]
    content = extract_content(filepath)

    header_parts = []
    if chapter_num:
        header_parts.append(f'<p class="chapter-num">{chapter_num}</p>')
    header_parts.append(f"<h1>{title}</h1>")
    if part_subtitle:
        header_parts.append(f'<p class="part-subtitle"><em>{part_subtitle}</em></p>')

    header_html = "\n".join(header_parts)

    # page-break-before: right forces recto (right-hand/odd page) start
    return f"""
    <section class="chapter">
      <div class="chapter-header">
        {header_html}
      </div>
      <div class="chapter-body">
        {content}
      </div>
    </section>
    """


def build_toc():
    """Build the table of contents."""
    toc_items = []

    toc_items.append('<div class="toc-entry"><span>Foreword</span></div>')

    current_part = None
    for filename in CHAPTERS[1:]:
        title, chapter_num, part = CHAPTER_TITLES[filename]
        if part != current_part:
            current_part = part
            toc_items.append(f'<div class="toc-part"><strong>{part}</strong></div>')
        num = chapter_num.replace("Chapter ", "")
        toc_items.append(
            f'<div class="toc-entry toc-chapter">'
            f"<span>Chapter {num}: {title}</span>"
            f"</div>"
        )

    return "\n".join(toc_items)


# Lulu interior CSS — 5.5" x 8.5" Digest, no bleed
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

/* === PAGE SETUP ===
   5.5" x 8.5" Digest, no bleed.
   Gutter (inside) = 0.75in, Outside = 0.625in
   Top = 0.75in, Bottom = 0.75in
   Right-hand (recto) pages = odd = gutter on left, outside on right
   Left-hand (verso) pages = even = gutter on right, outside on left
*/

@page {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
}

/* Recto (right-hand, odd pages): gutter LEFT, outside RIGHT */
@page :right {
    margin-left: 0.75in;   /* gutter */
    margin-right: 0.625in; /* outside */

    @bottom-right {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

/* Verso (left-hand, even pages): gutter RIGHT, outside LEFT */
@page :left {
    margin-left: 0.625in;  /* outside */
    margin-right: 0.75in;  /* gutter */

    @bottom-left {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

/* --- Front matter: no page numbers on title, copyright, TOC --- */
@page title-page {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page copyright-page {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page toc-page:right {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page toc-page:left {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

/* Blank verso pages inserted by break-before: right */
@page :blank {
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}


/* === BODY === */
body {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    text-rendering: optimizeLegibility;
}

/* === TITLE PAGE (page 1, recto) === */
.title-page {
    page: title-page;
    page-break-after: always;
    text-align: center;
    padding-top: 1.8in;
}
.title-page h1 {
    font-size: 26pt;
    font-weight: bold;
    line-height: 1.25;
    margin-bottom: 0.3in;
    color: #1a1a1a;
}
.title-page .subtitle-line {
    font-size: 13pt;
    color: #333;
    margin-bottom: 4pt;
}
.title-page .based-on {
    font-size: 10pt;
    font-style: italic;
    color: #555;
    margin-top: 0.5in;
    margin-bottom: 4pt;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 0.8in;
    color: #1a1a1a;
}

/* === COPYRIGHT PAGE (page 2, verso) === */
.copyright-page {
    page: copyright-page;
    page-break-after: always;
    text-align: center;
    padding-top: 3in;
    font-size: 9.5pt;
    line-height: 1.7;
    color: #444;
}
.copyright-page p {
    margin-bottom: 10pt;
}
.copyright-page .book-title {
    font-style: normal;
    font-weight: normal;
}
.copyright-page .edition {
    margin-top: 18pt;
}

/* === TABLE OF CONTENTS (starts recto) === */
.toc-section {
    page: toc-page;
    break-before: right;
    page-break-after: always;
}
.toc-section h1 {
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 0.35in;
    color: #1a1a1a;
}
.toc-part {
    margin-top: 16pt;
    margin-bottom: 6pt;
    font-size: 10.5pt;
    color: #1a1a1a;
}
.toc-entry {
    font-size: 10.5pt;
    line-height: 1.8;
    color: #333;
}
.toc-chapter {
    padding-left: 0.25in;
}

/* === CHAPTERS — start on recto (right-hand) pages === */
.chapter {
    break-before: right;
}

.chapter-header {
    text-align: center;
    margin-bottom: 0.3in;
    padding-bottom: 0.15in;
}

.chapter-header .chapter-num {
    font-size: 10pt;
    letter-spacing: 0.08em;
    color: #555;
    margin-bottom: 2pt;
    text-transform: uppercase;
}

.chapter-header h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 6pt;
    line-height: 1.2;
}

.chapter-header .part-subtitle {
    font-size: 10.5pt;
    color: #555;
    margin-top: 2pt;
}

/* === BODY TEXT === */
.chapter-body p {
    text-align: justify;
    text-indent: 0.3in;
    margin-bottom: 0;
    margin-top: 0;
    orphans: 2;
    widows: 2;
}

/* No indent after headings, dividers, quotes */
.chapter-body h2 + p,
.chapter-body .divider + p,
.chapter-body .scripture + p,
.chapter-body .principle-box + p,
.chapter-body .epigraph + p {
    text-indent: 0;
}

.chapter-body > p:first-child {
    text-indent: 0;
}

/* === SECTION HEADINGS — keep with following text === */
.chapter-body h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.3in;
    margin-bottom: 0.12in;
    page-break-after: avoid;
    break-after: avoid;
    orphans: 3;
    widows: 3;
}

/* === SCRIPTURE QUOTES === */
blockquote.scripture {
    margin: 0.15in 0 0.15in 0.4in;
    padding: 0;
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.5;
    border: none;
    page-break-inside: avoid;
}

blockquote.scripture p {
    text-indent: 0 !important;
    text-align: left;
    margin-bottom: 0;
}

blockquote.scripture cite {
    display: block;
    margin-top: 3pt;
    font-style: normal;
    font-weight: 500;
    font-size: 9.5pt;
    color: #444;
}

/* === PRINCIPLE BOX === */
.principle-box {
    margin: 0.18in 0.3in;
    padding: 0.12in 0.18in;
    border-left: 2pt solid #666;
    font-size: 10.5pt;
    page-break-inside: avoid;
}

.principle-box p {
    text-indent: 0 !important;
    text-align: left;
}

/* === EPIGRAPH === */
section.epigraph, .epigraph {
    margin: 0.15in 0.5in 0.25in 0.5in;
    text-align: center;
    page-break-inside: avoid;
}

section.epigraph blockquote, .epigraph blockquote {
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.55;
    margin-bottom: 0;
    border: none;
    padding: 0;
}

section.epigraph cite, .epigraph cite {
    display: block;
    margin-top: 4pt;
    font-style: normal;
    font-size: 9.5pt;
    color: #444;
}

/* === DIVIDERS === */
.divider {
    text-align: center;
    margin: 0.2in 0;
    color: #888;
    font-size: 10pt;
    letter-spacing: 0.15em;
    page-break-before: avoid;
}

/* === MISC === */
em { font-style: italic; }
strong { font-weight: bold; }
"""


def build_full_html(chapter_sections, toc_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <!-- TITLE PAGE (page 1, recto) -->
  <div class="title-page">
    <h1>The Character<br>No One Could Invent</h1>
    <p class="subtitle-line">The Evidence of Jesus&rsquo; Deity</p>
    <p class="subtitle-line">in the Portrait Itself</p>
    <p class="based-on">Based on The Man of Galilee by Atticus G. Haygood (1889)</p>
    <p class="based-on">Rewritten and Corrected for Modern Readers</p>
    <p class="author">Paul Hainline</p>
  </div>

  <!-- COPYRIGHT PAGE (page 2, verso) -->
  <div class="copyright-page">
    <p class="book-title">The Character No One Could Invent</p>
    <p>Copyright &copy; 2026 Paul Hainline<br>All rights reserved.</p>
    <p>Based on <em>The Man of Galilee</em> by Atticus G. Haygood (1889),<br>
    a work now in the public domain.</p>
    <p>Scripture quotations are from the New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p class="edition">First Edition</p>
  </div>

  <!-- TABLE OF CONTENTS (starts recto via break-before: right) -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- CHAPTERS (each starts recto via break-before: right) -->
  {chapter_sections}

</body>
</html>"""


def main():
    print("Generating Lulu interior PDF (5.5\" x 8.5\")...")
    print()

    print("Extracting chapter content...")
    chapter_sections = []
    for filename in CHAPTERS:
        print(f"  {filename}")
        chapter_sections.append(build_chapter_html(filename))

    print("Building table of contents...")
    toc_html = build_toc()

    print("Assembling HTML...")
    full_html = build_full_html("\n".join(chapter_sections), toc_html)

    # Save intermediate HTML for debugging
    debug_html = BOOK_DIR / "_lulu_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")

    print("Generating PDF with WeasyPrint (fonts will be embedded)...")
    doc = weasyprint.HTML(string=full_html)
    doc.write_pdf(str(OUTPUT))

    # Clean up
    debug_html.unlink(missing_ok=True)

    print(f"\nPDF saved to {OUTPUT}")
    print(f"  Page size: 5.5\" x 8.5\" (Digest)")
    print(f"  Gutter: 0.75in inside, 0.625in outside")
    print(f"  Chapters: start on recto (right-hand) pages")
    print(f"  Fonts: EB Garamond (embedded)")
    print("Done.")


if __name__ == "__main__":
    main()
