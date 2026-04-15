#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for Before I Formed You.

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
OUTPUT = BOOK_DIR / "BeforeIFormedYou_Lulu_Interior.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

CHAPTERS = [
    ("chapter1-before-i-formed-you.md", "Chapter One",   "El Roi: The God Who Sees You"),
    ("chapter2-before-i-formed-you.md", "Chapter Two",   "Fearfully and Wonderfully Made"),
    ("chapter3-before-i-formed-you.md", "Chapter Three", "A Basket in the River"),
    ("chapter4-before-i-formed-you.md", "Chapter Four",  "A Prayer Through Tears"),
    ("chapter5-before-i-formed-you.md", "Chapter Five",  "Gleaning at the Edges"),
    ("chapter6-before-i-formed-you.md", "Chapter Six",   "The Least Likely"),
    ("chapter7-before-i-formed-you.md", "Chapter Seven", "Be It Done to Me"),
    ("chapter8-before-i-formed-you.md", "Chapter Eight", "For Such a Time as This"),
]


def convert_md_to_html(md_text):
    """Convert a Markdown chapter to HTML for print styling."""
    # Remove the first H1 and H2 lines (we provide our own chapter header)
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    md_text = re.sub(r'^##\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()

    html = markdown.markdown(md_text, extensions=['smarty'])
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


def build_closing_html():
    """Build the closing section."""
    md_text = (BOOK_DIR / "closing-before-i-formed-you.md").read_text(encoding='utf-8')
    # Remove H1 heading
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    # Keep the H2 as the section title
    md_text = re.sub(r'^##\s+(.*)$', '', md_text, count=1, flags=re.MULTILINE).strip()
    html = markdown.markdown(md_text, extensions=['smarty'])

    return f"""
    <section class="chapter closing">
      <div class="chapter-header">
        <h1>You Are Not Alone</h1>
      </div>
      <div class="chapter-body">
        {html}
      </div>
    </section>
    """


def build_preface_html():
    """Build the preface section."""
    md_text = (BOOK_DIR / "preface-before-i-formed-you.md").read_text(encoding='utf-8')
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    html = markdown.markdown(md_text, extensions=['smarty'])

    return f"""
    <section class="chapter preface">
      <div class="chapter-header">
        <h1>Preface</h1>
      </div>
      <div class="chapter-body">
        {html}
      </div>
    </section>
    """


def build_toc():
    """Build the table of contents."""
    items = []
    items.append(
        '<div class="toc-entry">'
        '<span class="toc-title">Preface</span>'
        '</div>'
    )
    for filename, chapter_label, title in CHAPTERS:
        items.append(
            f'<div class="toc-entry">'
            f'<span class="toc-num">{chapter_label}</span>'
            f'<span class="toc-title">{title}</span>'
            f'</div>'
        )
    items.append(
        '<div class="toc-entry toc-backmatter">'
        '<span class="toc-title">You Are Not Alone</span>'
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
    padding-top: 2.2in;
}
.title-page h1 {
    font-size: 26pt;
    font-weight: bold;
    line-height: 1.25;
    margin-bottom: 0.25in;
    color: #1a1a1a;
}
.title-page .book-subtitle {
    font-size: 13pt;
    font-style: italic;
    color: #444;
    margin-bottom: 0.6in;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 0.5in;
    color: #1a1a1a;
}
.title-page .press {
    font-size: 9pt;
    margin-top: 1.5in;
    color: #666;
}

/* === COPYRIGHT PAGE (page 2, verso) === */
.copyright-page {
    page: front-matter;
    page-break-after: always;
    padding-top: 4in;
    font-size: 8pt;
    line-height: 1.5;
    color: #555;
}
.copyright-page p {
    margin-bottom: 1pt;
}

/* === TOC === */
.toc-page {
    page: toc-page;
    page-break-before: right;
    page-break-after: always;
}
.toc-page h2 {
    text-align: center;
    font-size: 16pt;
    margin-bottom: 0.6in;
    margin-top: 1.2in;
    font-weight: normal;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #333;
}
.toc-entry {
    padding: 4pt 0;
    font-size: 11pt;
    line-height: 1.65;
}
.toc-num {
    display: inline;
    color: #888;
    font-size: 10pt;
}
.toc-title {
    font-style: italic;
    margin-left: 0.15in;
}
.toc-num + .toc-title {
    margin-left: 0.15in;
}
.toc-backmatter {
    margin-top: 0.25in;
    padding-top: 0.15in;
    border-top: 0.5pt solid #ccc;
}

/* === CHAPTER LAYOUT === */
.chapter {
    page-break-before: right;
}
.chapter-header {
    text-align: center;
    padding-top: 1.4in;
    margin-bottom: 0.5in;
}
.chapter-header .chapter-num {
    font-size: 10pt;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 0.15in;
}
.chapter-header h1 {
    font-size: 20pt;
    font-weight: normal;
    font-style: italic;
    line-height: 1.3;
    color: #1a1a1a;
    margin-top: 0.1in;
}

.chapter-body p {
    text-indent: 0.25in;
    margin-bottom: 0;
    margin-top: 0;
    text-align: justify;
    hyphens: auto;
}
.chapter-body p:first-child {
    text-indent: 0;
}

/* Single-sentence paragraphs get extra spacing for breathing room */
.chapter-body hr {
    border: none;
    border-top: 0.5pt solid #ccc;
    width: 1.5in;
    margin: 0.35in auto;
}

/* === PREFACE === */
.preface .chapter-header {
    padding-top: 1.2in;
}
.preface .chapter-header .chapter-num {
    display: none;
}
.preface .chapter-body p {
    text-align: left;
    text-indent: 0;
    margin-bottom: 0.12in;
}

/* === CLOSING === */
.closing .chapter-header .chapter-num {
    display: none;
}
.closing .chapter-body p {
    text-align: left;
    text-indent: 0;
    margin-bottom: 0.12in;
}
.closing .chapter-body strong {
    font-size: 11pt;
}
"""


def main():
    print('Generating Lulu interior PDF for "Before I Formed You"...')

    css = CSS.replace('FONT_DIR', str(FONT_DIR))

    # --- Build sections ---
    toc_html = build_toc()
    preface_html = build_preface_html()

    chapter_sections = []
    for filename, chapter_label, title in CHAPTERS:
        chapter_sections.append(build_chapter_html(filename, chapter_label, title))

    closing_html = build_closing_html()

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>{css}</style>
</head>
<body>

  <!-- Title Page (page 1, recto) -->
  <div class="title-page">
    <h1>Before I Formed You</h1>
    <p class="book-subtitle">What God Says to the Woman<br>Holding This Book</p>
    <p class="author">Paul &amp; Pam Hainline</p>
    <p class="press">NobleMind Press<br>noblemind.study</p>
  </div>

  <!-- Copyright Page (page 2, verso) -->
  <div class="copyright-page">
    <p><em>Before I Formed You: What God Says to the Woman Holding This Book</em></p>
    <p>Copyright &copy; 2026 Paul and Pam Hainline. All rights reserved.</p>
    <p>&nbsp;</p>
    <p>Scripture quotations taken from the (NASB&reg;) New American Standard Bible&reg;,
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.
    Used by permission. All rights reserved. lockman.org</p>
    <p>&nbsp;</p>
    <p>Published by NobleMind Press &middot; noblemind.study</p>
    <p>&nbsp;</p>
    <p>This book may be freely distributed for non-commercial use.
    No part of this book may be sold without written permission.</p>
  </div>

  <!-- Table of Contents (page 3, recto) -->
  <div class="toc-page">
    <h2>Contents</h2>
    {toc_html}
  </div>

  <!-- Preface -->
  {preface_html}

  <!-- Chapters -->
  {"".join(chapter_sections)}

  <!-- Closing -->
  {closing_html}

</body>
</html>"""

    # Write debug HTML
    debug_path = BOOK_DIR / "_lulu_debug.html"
    debug_path.write_text(full_html, encoding='utf-8')
    print(f"  Debug HTML: {debug_path.name}")

    # Generate PDF via WeasyPrint
    doc = weasyprint.HTML(string=full_html, base_url=str(BOOK_DIR)).render()
    page_count = len(doc.pages)
    print(f"  Page count: {page_count}")

    # Pad to even page count if needed
    if page_count % 2 != 0:
        full_html = full_html.replace(
            '</body>',
            '<div style="page-break-before: always;">&nbsp;</div>\n</body>'
        )
        doc = weasyprint.HTML(string=full_html, base_url=str(BOOK_DIR)).render()
        page_count = len(doc.pages)
        print(f"  Padded to: {page_count} pages (even)")

    doc.write_pdf(str(OUTPUT))
    print(f"\nInterior saved to {OUTPUT}")
    print(f"  Pages: {page_count}")
    print("Done.")


if __name__ == "__main__":
    main()
