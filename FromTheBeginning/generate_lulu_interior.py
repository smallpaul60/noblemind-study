#!/usr/bin/env python3
"""Generate Lulu/IngramSpark-ready interior PDF for From the Beginning.

Specs for 5.5" x 8.5" (no bleed, text-only):
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
import markdown
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "FromTheBeginning_Lulu_Interior.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

CHAPTERS = [
    ("FromTheBeginning_Ch1.md",  "Chapter One",   "Not an Accident"),
    ("FromTheBeginning_Ch2.md",  "Chapter Two",   "Made in His Image"),
    ("FromTheBeginning_Ch3.md",  "Chapter Three", "What Went Wrong"),
    ("FromTheBeginning_Ch4.md",  "Chapter Four",  "The Long Promise"),
    ("FromTheBeginning_Ch5.md",  "Chapter Five",  "The Man Who Changed Everything"),
    ("FromTheBeginning_Ch6.md",  "Chapter Six",   "The Death That Paid the Debt"),
    ("FromTheBeginning_Ch7.md",  "Chapter Seven", "The Empty Tomb"),
    ("FromTheBeginning_Ch8.md",  "Chapter Eight", "So What Do I Do Now?"),
    ("FromTheBeginning_Ch9.md",  "Chapter Nine",  "What Happens Next?"),
    ("FromTheBeginning_Ch10.md", "Chapter Ten",   "The Life That Follows"),
]

PART_STRUCTURE = {
    # chapter index -> (part number, part title, part subtitle)
    0: ("Part One", "The Foundation", "Who is God, and why do you matter?"),
    4: ("Part Two", "The Turning Point", "Who is Jesus, and what did He do?"),
    7: ("Part Three", "The Response", "What does God ask you to do?"),
}


def convert_md_to_html(md_text):
    """Convert a Markdown chapter to HTML, then post-process for print styling."""
    # Remove the first H1 line (we'll provide our own chapter header)
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()

    # Convert markdown to HTML
    html = markdown.markdown(md_text, extensions=['smarty'])

    # Convert scripture blockquotes:
    # Pattern: <blockquote> containing <em>"text"</em> — <strong>Reference</strong>
    # Split into <blockquote class="scripture"><p>text</p><cite>Reference</cite></blockquote>
    def convert_scripture_bq(match):
        inner = match.group(1).strip()
        # Remove wrapping <p> tags
        inner = re.sub(r'^<p>(.*)</p>$', r'\1', inner, flags=re.DOTALL).strip()

        # Split on em-dash separating quote from citation
        parts = re.split(r'\s*[—–]\s*(?=<strong>)', inner, maxsplit=1)
        if len(parts) == 2:
            quote_text = parts[0].strip()
            cite_text = parts[1].strip()
            # Clean up the quote text: remove outer <em> wrapping
            quote_text = re.sub(r'^<em>(.*)</em>$', r'\1', quote_text, flags=re.DOTALL)
            # Remove surrounding smart quotes from the quote
            quote_text = quote_text.strip('\u201c\u201d"')
            # Clean up cite: remove <strong> tags and ", NASB" suffix
            cite_text = re.sub(r'</?strong>', '', cite_text)
            cite_text = re.sub(r',?\s*NASB\s*$', '', cite_text).strip()
            return (
                f'<blockquote class="scripture">'
                f'<p>\u201c{quote_text}\u201d</p>'
                f'<cite>\u2014 {cite_text}</cite>'
                f'</blockquote>'
            )
        return match.group(0)

    html = re.sub(
        r'<blockquote>\s*(.*?)\s*</blockquote>',
        convert_scripture_bq,
        html,
        flags=re.DOTALL
    )

    # Convert ## headings to h2, ### to h3 (markdown already does this)
    # No extra work needed

    return html


def build_chapter_html(filename, chapter_label, title):
    """Build HTML section for a single chapter."""
    md_text = (BOOK_DIR / filename).read_text(encoding='utf-8')
    body_html = convert_md_to_html(md_text)

    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{chapter_label}</p>
        <h1>{title}</h1>
      </div>
      <div class="chapter-body">
        {body_html}
      </div>
    </section>
    """


def build_part_page(part_num, part_title, part_subtitle):
    """Build a part divider page."""
    return f"""
    <div class="part-page">
      <p class="part-num">{part_num}</p>
      <h1 class="part-title">{part_title}</h1>
      <p class="part-subtitle"><em>{part_subtitle}</em></p>
    </div>
    """


def build_dedication_html():
    """Build dedication from Markdown file."""
    md_text = (BOOK_DIR / "FromTheBeginning_Dedication.md").read_text(encoding='utf-8')
    # Remove the H1 heading
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    html = markdown.markdown(md_text, extensions=['smarty'])
    return html


def build_toc():
    """Build the table of contents."""
    items = []
    for i, (filename, chapter_label, title) in enumerate(CHAPTERS):
        if i in PART_STRUCTURE:
            part_num, part_title, part_subtitle = PART_STRUCTURE[i]
            items.append(
                f'<div class="toc-part">'
                f'<span class="toc-part-title">{part_num} \u2014 {part_title}</span>'
                f'</div>'
            )
        items.append(
            f'<div class="toc-entry">'
            f'<span class="toc-num">{chapter_label}</span>'
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
@page front-matter {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}
@page front-matter:right {
    margin-left: 0.75in;
    margin-right: 0.625in;
}
@page front-matter:left {
    margin-left: 0.625in;
    margin-right: 0.75in;
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

/* Part divider pages: no page numbers */
@page part-page {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}
@page part-page:right {
    margin-left: 0.75in;
    margin-right: 0.625in;
}
@page part-page:left {
    margin-left: 0.625in;
    margin-right: 0.75in;
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
    page: front-matter;
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

/* === DEDICATION PAGE === */
.dedication-page {
    page: front-matter;
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
.dedication-page blockquote.scripture {
    margin: 0.2in 0.3in;
    text-align: center;
}
.dedication-page blockquote.scripture p {
    text-align: center;
    font-size: 10.5pt;
}
.dedication-page blockquote.scripture cite {
    font-style: normal;
    font-size: 9.5pt;
    color: #555;
}

/* === COPYRIGHT PAGE === */
.copyright-page {
    page: front-matter;
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
    padding-left: 0.3in;
}
.toc-entry .toc-num {
    display: inline;
    margin-right: 0.15in;
}
.toc-entry .toc-title {
    display: inline;
}
.toc-part {
    margin-top: 0.2in;
    margin-bottom: 0.05in;
    padding-left: 0;
}
.toc-part .toc-part-title {
    font-size: 10.5pt;
    font-weight: bold;
    font-style: italic;
    color: #1a1a1a;
}
.toc-backmatter {
    margin-top: 0.2in;
    padding-left: 0;
}

/* === PART DIVIDER PAGES === */
.part-page {
    page: part-page;
    break-before: right;
    page-break-after: always;
    text-align: center;
    padding-top: 2.5in;
}
.part-page .part-num {
    font-size: 11pt;
    letter-spacing: 0.15em;
    color: #555;
    margin-bottom: 0.15in;
    text-transform: uppercase;
}
.part-page .part-title {
    font-size: 22pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 0.15in;
    line-height: 1.2;
}
.part-page .part-subtitle {
    font-size: 11pt;
    color: #555;
    font-style: italic;
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

/* === BODY TEXT === */
.chapter-body p {
    text-align: justify;
    text-indent: 0.3in;
    margin-bottom: 0;
    margin-top: 0;
    orphans: 2;
    widows: 2;
}

/* No indent after headings, dividers, quotes, or at start of chapter */
.chapter-body h2 + p,
.chapter-body h3 + p,
.chapter-body .scripture + p,
.chapter-body blockquote + p {
    text-indent: 0;
}

.chapter-body > p:first-child {
    text-indent: 0;
}

/* === SECTION HEADINGS === */
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

.chapter-body h3 {
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
.index-book-group {
    page-break-inside: avoid;
    break-inside: avoid;
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
    page: front-matter;
    page-break-before: always;
    visibility: hidden;
}

/* === MISC === */
em { font-style: italic; }
strong { font-weight: bold; }
"""


# === SCRIPTURE INDEX BUILDER ===

# Bible book order for sorting
BIBLE_BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
    "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]
BOOK_ORDER_MAP = {}
for i, name in enumerate(BIBLE_BOOK_ORDER):
    BOOK_ORDER_MAP[name.lower()] = i


def parse_ref_for_index(ref_str):
    """Parse a reference like 'Genesis 1:26' into (book_name, chapter, verse_start, sort_key)."""
    ref_str = ref_str.strip()
    ref_str = re.sub(r',?\s*NASB\s*$', '', ref_str)
    ref_str = re.sub(r'\*{1,2}', '', ref_str)
    ref_str = ref_str.strip()

    m = re.match(
        r'^(\d?\s*[A-Za-z][A-Za-z\s]+?)\s+(\d+):(\d+)(?:\s*[–\-]\s*(\d+))?',
        ref_str
    )
    if m:
        book = m.group(1).strip()
        chapter = int(m.group(2))
        verse_start = int(m.group(3))
        verse_end = m.group(4)
        book_order = BOOK_ORDER_MAP.get(book.lower(), 999)
        ref_display = f"{book} {chapter}:{verse_start}"
        if verse_end:
            ref_display += f"\u2013{verse_end}"
        return book, ref_display, (book_order, chapter, verse_start)

    # Chapter-only reference
    m2 = re.match(r'^(\d?\s*[A-Za-z][A-Za-z\s]+?)\s+(\d+)$', ref_str)
    if m2:
        book = m2.group(1).strip()
        chapter = int(m2.group(2))
        book_order = BOOK_ORDER_MAP.get(book.lower(), 999)
        return book, f"{book} {chapter}", (book_order, chapter, 0)

    return None, ref_str, (999, 0, 0)


def extract_refs_from_md(md_text):
    """Extract all scripture references from a Markdown chapter."""
    refs = []
    # Match blockquote lines with citations: > ... — **Reference, NASB**
    for line in md_text.split('\n'):
        line = line.strip()
        if line.startswith('>'):
            content = line[1:].strip()
            # Look for — **Reference** pattern
            m = re.search(r'[—–]\s*\*{0,2}(.+?)(?:\*{0,2})\s*$', content)
            if m:
                ref_text = m.group(1).strip()
                refs.append(ref_text)
        # Also find inline parenthetical references like (Genesis 3:15)
        # and "ref" style references in the running text
        for m in re.finditer(r'\((\d?\s*[A-Za-z][A-Za-z]+\s+\d+:\d+(?:[–\-]\d+)?)\)', line):
            refs.append(m.group(1))
    return refs


def build_scripture_index():
    """Build the scripture index from all chapter files."""
    # ref_display -> set of chapter labels that reference it
    index = {}  # (sort_key, ref_display, book_name) -> set of chapter labels

    for i, (filename, chapter_label, title) in enumerate(CHAPTERS):
        md_text = (BOOK_DIR / filename).read_text(encoding='utf-8')
        refs = extract_refs_from_md(md_text)
        for ref_text in refs:
            book, ref_display, sort_key = parse_ref_for_index(ref_text)
            if book is None:
                continue
            key = (sort_key, ref_display, book)
            if key not in index:
                index[key] = set()
            # Use chapter number for brevity
            ch_num = i + 1
            index[key].add(ch_num)

    # Sort by biblical book order, then chapter, then verse
    sorted_entries = sorted(index.items(), key=lambda x: x[0][0])

    # Group entries by book
    from collections import OrderedDict
    books_entries = OrderedDict()
    for (sort_key, ref_display, book), ch_nums in sorted_entries:
        display_book = book
        if display_book == "Psalm":
            display_book = "Psalms"
        if display_book not in books_entries:
            books_entries[display_book] = []
        ch_list = ", ".join(str(n) for n in sorted(ch_nums))
        books_entries[display_book].append(
            f'<div class="index-entry">'
            f'<span class="index-ref">{ref_display}</span>'
            f'<span class="index-chapters">Ch. {ch_list}</span>'
            f'</div>'
        )

    # Build HTML: wrap each book heading + first 2 entries in a group
    # so heading never appears orphaned at bottom of a page
    html_parts = []
    for display_book, entries in books_entries.items():
        # Group heading with first 2 entries to prevent orphan
        grouped = entries[:2]
        remaining = entries[2:]
        html_parts.append(
            f'<div class="index-book-group">'
            f'<h3 class="index-book">{display_book}</h3>'
            + "\n".join(grouped)
            + '</div>'
        )
        html_parts.extend(remaining)

    return "\n".join(html_parts)


def build_full_html(chapter_sections, toc_html, dedication_html, scripture_index_html):
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
    <h1>From the Beginning</h1>
    <p class="book-subtitle">The Gospel from the Ground Up</p>
    <p class="author">Paul &amp; Pam Hainline</p>
  </div>

  <!-- BLANK VERSO (page 2) — will be blank naturally -->

  <!-- COPYRIGHT PAGE -->
  <div class="copyright-page">
    <p>From the Beginning: The Gospel from the Ground Up</p>
    <p>Copyright \u00a9 2026 Paul &amp; Pam Hainline</p>
    <p>All rights reserved.</p>
    <p>&nbsp;</p>
    <p>Published by NobleMind Press</p>
    <p>&nbsp;</p>
    <p>Scripture quotations are taken from the New American Standard Bible\u00ae (NASB),<br>
    Copyright \u00a9 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p>&nbsp;</p>
    <p>No part of this publication may be reproduced, stored in a retrieval system,<br>
    or transmitted in any form or by any means without the prior written<br>
    permission of the authors, except as provided by U.S. copyright law.</p>
    <p>&nbsp;</p>
    <p>Printed in the United States of America</p>
  </div>

  <!-- DEDICATION -->
  <div class="dedication-page">
    {dedication_html}
  </div>

  <!-- TABLE OF CONTENTS (starts recto) -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- CHAPTERS (with part dividers) -->
  {chapter_sections}

  <!-- SCRIPTURE INDEX -->
  <section class="scripture-index">
    <h1>Scripture Index</h1>
    {scripture_index_html}
  </section>

</body>
</html>"""


def main():
    print('Generating Lulu/IngramSpark interior PDF for "From the Beginning"...')
    print(f'  Page size: 5.5" x 8.5"')
    print(f"  Gutter: 0.75in inside, 0.625in outside")
    print(f"  Font: EB Garamond (from {FONT_DIR})")
    print()

    print("Building table of contents...")
    toc_html = build_toc()

    print("Building dedication page...")
    dedication_html = build_dedication_html()

    print("Building scripture index...")
    scripture_index_html = build_scripture_index()

    print("Converting chapter content from Markdown...")
    chapter_sections = []
    for i, (filename, chapter_label, title) in enumerate(CHAPTERS):
        print(f"  {filename}: {title}")
        # Insert part divider page before the first chapter of each part
        if i in PART_STRUCTURE:
            part_num, part_title, part_subtitle = PART_STRUCTURE[i]
            chapter_sections.append(build_part_page(part_num, part_title, part_subtitle))
        chapter_sections.append(build_chapter_html(filename, chapter_label, title))

    print("Assembling HTML...")
    full_html = build_full_html(
        "\n".join(chapter_sections),
        toc_html,
        dedication_html,
        scripture_index_html,
    )

    # Save intermediate HTML for debugging
    debug_html = BOOK_DIR / "_lulu_debug.html"
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
