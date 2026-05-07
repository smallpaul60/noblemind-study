#!/usr/bin/env python3
"""Generate IngramSpark-ready interior PDF for Through the Valley.

IngramSpark specs for 5.5" x 8.5" (no bleed, text-only):
  - Page size: 5.5in x 8.5in
  - Gutter (inside margin): 0.75in
  - Outside margin: 0.625in
  - Top/bottom margin: 0.75in
  - Chapters start on recto (right-hand, odd) pages
  - Alternating left/right margins for facing pages
  - All fonts embedded
  - Page count divisible by 2
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Through_the_Valley_Lulu_Interior.pdf"

FONT_DIR = Path.home() / ".local" / "share" / "fonts"

CHAPTERS = [
    ("chapter-01.html", "Chapter One", "Even Though I Walk"),
    ("chapter-02.html", "Chapter Two", "For You Are With Me"),
    ("chapter-03.html", "Chapter Three", "My Flesh and My Heart May Fail"),
    ("chapter-04.html", "Chapter Four", "Two Are Better Than One"),
    ("chapter-05.html", "Chapter Five", "What No Eye Has Seen"),
    ("chapter-06.html", "Chapter Six", "Things Too Wonderful for Me"),
    ("chapter-07.html", "Chapter Seven", "So We Do Not Grieve as Those Who Have No Hope"),
    ("chapter-08.html", "Chapter Eight", "I Will Fear No Evil"),
]


def extract_content_div(html_file):
    """Parse an HTML chapter file and extract the content div's inner HTML."""
    html_text = (BOOK_DIR / html_file).read_text(encoding="utf-8")
    soup = BeautifulSoup(html_text, "html.parser")
    content_div = soup.find("div", class_="content")
    if not content_div:
        # Try front-content for front-matter
        content_div = soup.find("div", class_="front-content")
    return content_div


def extract_epigraph(html_file):
    """Extract the epigraph section from a chapter HTML file."""
    html_text = (BOOK_DIR / html_file).read_text(encoding="utf-8")
    soup = BeautifulSoup(html_text, "html.parser")
    epigraph = soup.find("section", class_="epigraph")
    if not epigraph:
        epigraph = soup.find("div", class_="epigraph")
    return epigraph


def process_content_for_print(content_div):
    """Process a BeautifulSoup content div for print output.

    Removes interactive elements (textareas, onclick handlers) and
    converts the content to clean HTML suitable for PDF generation.
    """
    if content_div is None:
        return ""

    # Work on a copy
    soup_copy = BeautifulSoup(str(content_div), "html.parser")

    # Remove textareas (interactive elements)
    for textarea in soup_copy.find_all("textarea"):
        textarea.decompose()

    # Remove reflection header arrow spans
    for arrow in soup_copy.find_all("span", class_="arrow"):
        arrow.decompose()

    # Remove onclick attributes
    for elem in soup_copy.find_all(attrs={"onclick": True}):
        del elem["onclick"]

    # Get inner HTML of the content div
    content_wrapper = soup_copy.find("div", class_=re.compile(r"content|front-content"))
    if content_wrapper:
        return content_wrapper.decode_contents()
    return soup_copy.decode_contents()


def build_chapter_html(filename, chapter_num, title):
    """Build HTML section for a single chapter."""
    content_div = extract_content_div(filename)
    epigraph = extract_epigraph(filename)
    body_html = process_content_for_print(content_div)

    # Build epigraph HTML
    epigraph_html = ""
    if epigraph:
        bq = epigraph.find("blockquote")
        cite = epigraph.find("cite")
        if bq and cite:
            epigraph_html = f"""
      <div class="chapter-epigraph">
        <blockquote class="scripture epigraph-quote">
          <p>{bq.decode_contents()}</p>
          <cite>{cite.get_text()}</cite>
        </blockquote>
      </div>"""

    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{chapter_num}</p>
        <h1>{title}</h1>
      </div>
      {epigraph_html}
      <div class="chapter-body">
        {body_html}
      </div>
    </section>
    """


def build_front_matter_html():
    """Extract and build the 'How to Use This Book' section from front-matter.html."""
    content_div = extract_content_div("front-matter.html")
    if content_div is None:
        return ""

    body_html = process_content_for_print(content_div)

    # Remove the duplicate "How to Use This Book" h2 heading since we have it
    # as the section header already. It comes from the HTML as an h2 with
    # class="section-heading".
    body_html = re.sub(
        r'<h2 class="section-heading">How to Use This Book</h2>\s*',
        '',
        body_html,
        count=1
    )

    return body_html


def build_scripture_index_html():
    """Extract and build the scripture index from scripture-index.html."""
    html_text = (BOOK_DIR / "scripture-index.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html_text, "html.parser")
    content_div = soup.find("div", class_="content")
    if not content_div:
        return ""

    table = content_div.find("table", class_="scripture-table")
    if not table:
        return ""

    # Convert table rows to index entries grouped by book
    entries = []
    tbody = table.find("tbody")
    if not tbody:
        return ""

    current_book = None
    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        ref_text = cells[0].get_text(strip=True)
        # Extract chapter references (strip HTML links, keep text)
        chapter_text = cells[1].get_text(strip=True)

        # Determine book name for grouping
        book = extract_book_name(ref_text)
        if book != current_book:
            current_book = book
            entries.append(f'<h3 class="index-book">{book}</h3>')

        entries.append(
            f'<div class="index-entry">'
            f'<span class="index-ref">{ref_text}</span>'
            f'<span class="index-chapters">{chapter_text}</span>'
            f'</div>'
        )

    return "\n".join(entries)


def extract_book_name(ref_str):
    """Extract the Bible book name from a reference string."""
    match = re.match(r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)*)\s+\d', ref_str)
    if match:
        return match.group(1).strip()
    return ref_str


def build_toc():
    """Build the table of contents."""
    items = []
    # How to Use This Book
    items.append(
        '<div class="toc-entry toc-frontmatter">'
        '<span class="toc-title">How to Use This Book</span>'
        '</div>'
    )
    for filename, chapter_num, title in CHAPTERS:
        items.append(
            f'<div class="toc-entry">'
            f'<span class="toc-num">{chapter_num}</span>'
            f'<span class="toc-title">{title}</span>'
            f'</div>'
        )
    items.append(
        '<div class="toc-entry toc-backmatter">'
        '<span class="toc-title">Scripture Index</span>'
        '</div>'
    )
    return "\n".join(items)


CSS = r"""
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond.ttf') format('truetype');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond-Italic.ttf') format('truetype');
    font-weight: normal;
    font-style: italic;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond.ttf') format('truetype');
    font-weight: bold;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond-Italic.ttf') format('truetype');
    font-weight: bold;
    font-style: italic;
}

/* === PAGE SETUP ===
   5.5" x 8.5", no bleed.
   Gutter (inside) = 0.75in, Outside = 0.625in
   Top = 0.75in, Bottom = 0.75in
*/

@page {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
}

/* Recto (right-hand, odd pages): gutter LEFT, outside RIGHT */
@page :right {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

/* Verso (left-hand, even pages): gutter RIGHT, outside LEFT */
@page :left {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-left {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

/* Front matter pages: no page numbers */
@page front-recto {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}
@page front-verso {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
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

/* How to Use This Book section: no page numbers */
@page howto-page:right {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}
@page howto-page:left {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

/* Blank pages inserted by break-before: right */
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
    page: front-recto;
    page-break-after: always;
    text-align: center;
    padding-top: 2in;
}
.title-page h1 {
    font-size: 26pt;
    font-weight: bold;
    line-height: 1.25;
    margin-bottom: 0.15in;
    color: #1a1a1a;
}
.title-page .book-subtitle {
    font-size: 12pt;
    font-style: italic;
    color: #444;
    margin-bottom: 0.8in;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 0.8in;
    color: #1a1a1a;
}

/* === DEDICATION PAGE (verso after title) === */
.dedication-page {
    page: front-verso;
    page-break-after: always;
    padding-top: 2.5in;
    text-align: center;
}
.dedication-page p {
    font-size: 11pt;
    line-height: 1.65;
    color: #333;
    font-style: italic;
    margin-bottom: 4pt;
}

/* === COPYRIGHT PAGE (recto) === */
.copyright-page {
    page: front-recto;
    page-break-after: always;
    padding-top: 2.5in;
}
.copyright-page p {
    font-size: 8.5pt;
    line-height: 1.45;
    color: #555;
    margin-bottom: 3pt;
    text-align: center;
}
.copyright-page .isbn {
    font-weight: bold;
    color: #333;
}

/* === TABLE OF CONTENTS === */
.toc-section {
    page: toc-page;
    break-before: right;
    page-break-after: always;
}
.toc-section h1 {
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0.4in;
    padding-top: 0.5in;
    color: #1a1a1a;
}
.toc-entry {
    font-size: 10.5pt;
    line-height: 2.0;
    color: #333;
    padding-left: 0.15in;
}
.toc-entry .toc-num {
    display: inline;
    margin-right: 0.15in;
}
.toc-entry .toc-title {
    display: inline;
}
.toc-frontmatter {
    margin-bottom: 0.15in;
    padding-left: 0;
}
.toc-backmatter {
    margin-top: 0.2in;
    padding-left: 0;
}

/* === HOW TO USE THIS BOOK SECTION === */
.howto-section {
    page: howto-page;
    break-before: right;
    page-break-after: always;
}
.howto-section .howto-header {
    text-align: center;
    margin-bottom: 0.35in;
    padding-top: 0.5in;
}
.howto-section .howto-header h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 6pt;
    line-height: 1.2;
}
.howto-section p {
    text-align: justify;
    text-indent: 0.3in;
    margin-bottom: 0;
    margin-top: 0;
    orphans: 2;
    widows: 2;
}
.howto-section h2 + p,
.howto-section .principle-box + p {
    text-indent: 0;
}
.howto-section > p:first-child {
    text-indent: 0;
}
.howto-body > p:first-child {
    text-indent: 0;
}

/* === CHAPTERS -- start on recto pages === */
.chapter {
    break-before: right;
}

.chapter-header {
    text-align: center;
    margin-bottom: 0.35in;
    padding-top: 0.5in;
}

.chapter-header .chapter-num {
    font-size: 10pt;
    letter-spacing: 0.1em;
    color: #555;
    margin-bottom: 4pt;
    text-transform: uppercase;
}

.chapter-header h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 6pt;
    line-height: 1.2;
}

/* === CHAPTER EPIGRAPH === */
.chapter-epigraph {
    margin-bottom: 0.3in;
    text-align: center;
}
.chapter-epigraph blockquote.scripture {
    margin: 0 0.5in;
    border: none;
    text-align: center;
}
.chapter-epigraph blockquote.scripture p {
    text-align: center;
    text-indent: 0 !important;
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

/* No indent after headings, dividers, quotes, principle boxes, epigraphs */
.chapter-body h2 + p,
.chapter-body h3 + p,
.chapter-body .divider + p,
.chapter-body .scripture + p,
.chapter-body blockquote + p,
.chapter-body .principle-box + p,
.chapter-body .chapter-epigraph + p {
    text-indent: 0;
}

.chapter-body > p:first-child {
    text-indent: 0;
}

/* === SECTION HEADINGS -- keep with following text, avoid orphaned subtitles === */
.chapter-body h2,
.howto-section h2 {
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

.chapter-body h3,
.howto-section h3 {
    font-size: 11.5pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.25in;
    margin-bottom: 0.1in;
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

/* === PRINCIPLE BOXES === */
.principle-box {
    margin: 0.15in 0;
    padding: 0.12in 0.2in;
    border-left: 2pt solid #888;
    font-size: 10.5pt;
    line-height: 1.5;
    page-break-inside: avoid;
}
.principle-box p {
    text-indent: 0 !important;
    text-align: justify;
    margin-bottom: 0;
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

/* === REFLECTION SECTION === */
.reflection-section {
    margin-top: 0.3in;
    padding-top: 0.15in;
    border-top: 0.5pt solid #ccc;
}
.reflection-section h2,
.reflection-header h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 0.12in;
    page-break-after: avoid;
    break-after: avoid;
}
.reflection-question {
    margin-bottom: 0.12in;
    font-size: 10.5pt;
    line-height: 1.5;
    page-break-inside: avoid;
}
.reflection-question .q-num {
    font-weight: bold;
    margin-right: 4pt;
}
.reflection-question .q-text {
    display: inline;
}

/* === SCRIPTURE INDEX === */
.scripture-index {
    break-before: right;
}
.scripture-index h1 {
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0.35in;
    padding-top: 0.5in;
    color: #1a1a1a;
}
.index-book {
    font-size: 12pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.2in;
    margin-bottom: 0.08in;
    page-break-after: avoid;
    break-after: avoid;
}
.index-entry {
    font-size: 10pt;
    line-height: 1.7;
    margin-left: 0.2in;
    color: #333;
}
.index-ref {
    display: inline;
    margin-right: 0.15in;
}
.index-chapters {
    display: inline;
    font-style: italic;
    font-size: 9.5pt;
    color: #555;
}

/* Pad page for even page count */
.pad-page {
    page: front-verso;
    page-break-before: always;
    visibility: hidden;
}

/* === MISC === */
em { font-style: italic; }
strong { font-weight: bold; }
/* Override section-heading class from HTML source */
.section-heading {
    font-size: 13pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.3in;
    margin-bottom: 0.12in;
    padding-bottom: 0;
    border-bottom: none;
    page-break-after: avoid;
    break-after: avoid;
    orphans: 3;
    widows: 3;
}
"""


def build_full_html(chapter_sections, toc_html, scripture_index_html, front_matter_html):
    css = CSS.replace("FONT_DIR", str(FONT_DIR))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{css}</style>
</head>
<body>

  <!-- TITLE PAGE (page 1, recto) -->
  <div class="title-page">
    <h1>Through the Valley</h1>
    <p class="book-subtitle">What God Says When the Shadow Is Real</p>
    <p class="author">Paul Hainline</p>
  </div>

  <!-- DEDICATION (page 2, verso) -->
  <div class="dedication-page">
    <p>To everyone walking through this valley &mdash;</p>
    <p>the one whose body is failing,</p>
    <p>and the one sitting at the bedside.</p>
    <p>&nbsp;</p>
    <p>You are not walking into the valley; you are walking through it.</p>
    <p>The Shepherd is already there.</p>
  </div>

  <!-- COPYRIGHT PAGE (page 3, recto) -->
  <div class="copyright-page">
    <p>Through the Valley: What God Says When the Shadow Is Real</p>
    <p>Copyright \u00a9 2026 Paul Hainline</p>
    <p>All rights reserved.</p>
    <p>&nbsp;</p>
    <p>Published by NobleMind Press</p>
    <p>&nbsp;</p>
    <p class="isbn">Paperback ISBN: 979-8-9954288-7-9</p>
    <p class="isbn">Hardcover ISBN: 979-8-9954288-8-6</p>
    <p>&nbsp;</p>
    <p>Scripture quotations are taken from the New American Standard Bible\u00ae (NASB),<br>
    Copyright \u00a9 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p>&nbsp;</p>
    <p>No part of this publication may be reproduced, stored in a retrieval system,<br>
    or transmitted in any form or by any means without the prior written<br>
    permission of the author, except as provided by U.S. copyright law.</p>
    <p>&nbsp;</p>
    <p>Printed in the United States of America</p>
  </div>

  <!-- TABLE OF CONTENTS (starts recto) -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- HOW TO USE THIS BOOK -->
  <section class="howto-section">
    <div class="howto-header">
      <h1>How to Use This Book</h1>
    </div>
    <div class="howto-body">
      {front_matter_html}
    </div>
  </section>

  <!-- CHAPTERS -->
  {chapter_sections}

  <!-- SCRIPTURE INDEX -->
  <section class="scripture-index">
    <h1>Scripture Index</h1>
    {scripture_index_html}
  </section>

</body>
</html>"""


def main():
    print('Generating IngramSpark interior PDF for "Through the Valley"...')
    print(f'  Page size: 5.5" x 8.5"')
    print(f"  Gutter: 0.75in inside, 0.625in outside")
    print(f"  Font: EB Garamond (from {FONT_DIR})")
    print()

    print("Building table of contents...")
    toc_html = build_toc()

    print("Extracting front matter (How to Use This Book)...")
    front_matter_html = build_front_matter_html()

    print("Extracting chapter content from HTML files...")
    chapter_sections = []
    for filename, chapter_num, title in CHAPTERS:
        print(f"  {filename}: {title}")
        chapter_sections.append(build_chapter_html(filename, chapter_num, title))

    print("Extracting scripture index...")
    scripture_index_html = build_scripture_index_html()

    print("Assembling HTML...")
    full_html = build_full_html(
        "\n".join(chapter_sections),
        toc_html,
        scripture_index_html,
        front_matter_html,
    )

    # Save intermediate HTML for debugging
    debug_html = BOOK_DIR / "_ingram_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")
    print(f"  Debug HTML saved to {debug_html}")

    print("Generating PDF with WeasyPrint (fonts will be embedded)...")
    doc = weasyprint.HTML(string=full_html, base_url=str(BOOK_DIR))
    pdf_doc = doc.render()

    page_count = len(pdf_doc.pages)
    print(f"  Raw page count: {page_count}")

    # Ensure page count is divisible by 2
    if page_count % 2 != 0:
        print(f"  Page count {page_count} is odd; adding a blank page...")
        # Add a blank padding page by re-rendering with a pad div
        full_html_padded = full_html.replace(
            "</body>",
            '<div class="pad-page">&nbsp;</div>\n</body>'
        )
        doc = weasyprint.HTML(string=full_html_padded, base_url=str(BOOK_DIR))
        pdf_doc = doc.render()
        page_count = len(pdf_doc.pages)
        print(f"  Adjusted page count: {page_count}")

    pdf_doc.write_pdf(str(OUTPUT))

    print(f"\nPDF saved to {OUTPUT}")
    print(f"  Total pages: {page_count}")
    print(f"  Chapters start on recto (right-hand) pages")
    print(f"  Fonts: EB Garamond (embedded)")
    print(f"  Scripture index: included")
    print("Done.")


if __name__ == "__main__":
    main()
