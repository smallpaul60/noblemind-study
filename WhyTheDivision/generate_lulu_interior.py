#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for 'Why the Division Among Brethren?'.

Specs (5.5" x 8.5", no bleed, text-only):
  - Page size: 5.5in x 8.5in
  - Gutter (inside margin): 0.75in
  - Outside margin: 0.625in
  - Top/bottom margin: 0.75in
  - Chapters and Part pages start on recto (right-hand, odd) pages
  - All fonts embedded
  - Page count ends on an even page

Front matter:  half-title, title, copyright (no ISBN), epigraph, contents.
Body:          preface; four parts (each with a part-title page); 11 chapters.
Back matter:   Scripture Index.
"""

from pathlib import Path

import weasyprint

from _book_source import (
    parse_book, md_body_to_html,
    TITLE, SUBTITLE, AUTHOR, PUBLISHER,
)
from _scripture_index import build_index

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_The_Division_Lulu_Interior.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"


# ============================================================================
# SCRIPTURE INDEX HTML RENDERER
# ============================================================================

def build_scripture_index_html():
    """Render the Scripture index as HTML for the back matter."""
    idx = build_index()
    parts = []
    for group in idx:
        head = f'<h3 class="index-book">{group["book"]}</h3>'
        rows = []
        for e in group["entries"]:
            verse_part = ""
            if e["verses"]:
                verse_part = ":" + e["verses"].replace('-', '–')
            ref = f'{group["book"]} {e["chapter"]}{verse_part}'
            locs = ", ".join(
                "Pref" if n == 0 else f"Ch. {n}"
                for n in e["locations"]
            )
            rows.append(
                f'<div class="index-entry">'
                f'<span class="index-ref">{ref}</span>'
                f'<span class="index-chapters">{locs}</span>'
                f'</div>'
            )
        # Keep the heading with at least its first two entries on the same
        # page, then let the rest flow.
        kept = head + "\n" + "\n".join(rows[:2])
        parts.append(f'<div class="index-book-group">{kept}</div>')
        parts.extend(rows[2:])
    return "\n".join(parts)


# ============================================================================
# SECTION BUILDERS
# ============================================================================

def build_toc(book):
    rows = [
        '<div class="toc-entry toc-front">'
        '<a href="#preface">'
        '<span class="toc-num"></span>'
        '<span class="toc-title">Preface</span>'
        '<span class="toc-dots"></span>'
        '</a></div>'
    ]

    for p_idx, part in enumerate(book["parts"], start=1):
        rows.append(
            f'<div class="toc-part-header">'
            f'<a href="#part-{p_idx}">{part["label"]}: {part["title"]}</a>'
            f'</div>'
        )
        for ch in part["chapters"]:
            rows.append(
                f'<div class="toc-entry">'
                f'<a href="#ch-{ch["num"]}">'
                f'<span class="toc-num">Chapter {ch["num"]}</span>'
                f'<span class="toc-title">{ch["title"]}</span>'
                f'<span class="toc-dots"></span>'
                f'</a></div>'
            )

    rows.append(
        '<div class="toc-entry toc-back">'
        '<a href="#scripture-index">'
        '<span class="toc-num"></span>'
        '<span class="toc-title">Scripture Index</span>'
        '<span class="toc-dots"></span>'
        '</a></div>'
    )
    return "\n".join(rows)


def build_preface(md):
    body = md_body_to_html(md)
    return f"""
    <section class="chapter preface" id="preface">
      <div class="chapter-header">
        <p class="chapter-num">Preface</p>
        <div class="chapter-rule"></div>
      </div>
      <div class="chapter-body">{body}</div>
    </section>
    """


def build_part_page(part, p_idx):
    intro = md_body_to_html(part["intro_md"])
    return f"""
    <section class="part-page" id="part-{p_idx}">
      <div class="part-label">{part["label"]}</div>
      <h1 class="part-title">{part["title"]}</h1>
      <div class="part-rule"></div>
      <div class="part-intro">{intro}</div>
    </section>
    """


def build_chapter(ch):
    body = md_body_to_html(ch["md"])
    return f"""
    <section class="chapter" id="ch-{ch['num']}">
      <div class="chapter-header">
        <p class="chapter-num">{ch['label']}</p>
        <h1>{ch['title']}</h1>
        <div class="chapter-rule"></div>
      </div>
      <div class="chapter-body">{body}</div>
    </section>
    """


# ============================================================================
# CSS
# ============================================================================

CSS = r"""
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond.ttf') format('truetype');
    font-weight: normal; font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond-Italic.ttf') format('truetype');
    font-weight: normal; font-style: italic;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond.ttf') format('truetype');
    font-weight: bold; font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond-Italic.ttf') format('truetype');
    font-weight: bold; font-style: italic;
}

/* === PAGE SETUP ===
   5.5" x 8.5", no bleed.
   Gutter (inside) = 0.75in, Outside = 0.625in
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
    margin-left: 0.75in; margin-right: 0.625in;
}
@page front-matter:left {
    margin-left: 0.625in; margin-right: 0.75in;
}
@page toc-page:right {
    margin-left: 0.75in; margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
}
@page toc-page:left {
    margin-left: 0.625in; margin-right: 0.75in;
    @bottom-right { content: none; }
    @bottom-left  { content: none; }
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
    margin: 0; padding: 0;
}

/* === FRONT MATTER === */
.half-title-page {
    page: front-matter; page-break-after: always;
    text-align: center; padding-top: 3.2in;
}
.half-title-page h1 {
    font-size: 18pt; font-weight: normal; letter-spacing: 0.04em;
    color: #1a1a1a; line-height: 1.25;
    padding: 0 0.4in;
}

.title-page {
    page: front-matter; break-before: right; page-break-after: always;
    text-align: center; padding-top: 1.6in;
}
.title-page h1 {
    font-size: 26pt; font-weight: bold; line-height: 1.2;
    margin-bottom: 0.2in; color: #1a1a1a;
    padding: 0 0.3in;
}
.title-page .book-subtitle {
    font-size: 11.5pt; font-style: italic; color: #444;
    margin-bottom: 0.6in; line-height: 1.45; padding: 0 0.4in;
}
.title-page .title-rule {
    width: 1.2in; height: 1px; background: #aaa;
    margin: 0.35in auto 0.5in;
}
.title-page .author {
    font-size: 14pt; margin-top: 1.0in;
    color: #1a1a1a; letter-spacing: 0.08em;
}
.title-page .imprint {
    font-size: 10pt; font-style: italic;
    color: #666; margin-top: 0.25in;
}

.copyright-page {
    page: front-matter; page-break-after: always;
    padding-top: 2.0in;
}
.copyright-page p {
    font-size: 9pt; line-height: 1.5; color: #555;
    margin: 0 0 6pt 0; text-align: center;
}
.copyright-page .sep { height: 10pt; }

.epigraph-page {
    page: front-matter; break-before: right; page-break-after: always;
    padding-top: 3.2in; text-align: center;
}
.epigraph-page blockquote {
    margin: 0 0.7in; font-style: italic; font-size: 12pt;
    line-height: 1.6; color: #222; border: none; padding: 0;
}
.epigraph-page cite {
    display: block; margin-top: 0.25in; font-style: normal;
    font-size: 10pt; color: #666; letter-spacing: 0.04em;
}

/* === TABLE OF CONTENTS === */
.toc-section {
    page: toc-page; break-before: right; page-break-after: always;
}
.toc-section h1 {
    font-size: 20pt; font-weight: bold; text-align: center;
    margin-bottom: 0.45in; padding-top: 0.3in;
    color: #1a1a1a; letter-spacing: 0.04em;
}
.toc-entry {
    font-size: 10.5pt; line-height: 1.85; color: #222;
    padding-left: 0.2in;
}
.toc-entry a {
    color: inherit; text-decoration: none;
    display: flex; align-items: baseline; gap: 0.08in;
}
.toc-entry .toc-num {
    flex: 0 0 auto;
    font-variant: small-caps;
    font-size: 9.5pt; letter-spacing: 0.06em;
    color: #555;
    min-width: 0.95in;
    order: 1;
}
.toc-entry .toc-title { flex: 0 1 auto; order: 2; }
.toc-entry .toc-dots {
    flex: 1 1 auto;
    border-bottom: 1px dotted #bbb;
    transform: translateY(-3px);
    margin: 0 0.1in;
    order: 3;
}
.toc-entry a::after {
    content: target-counter(attr(href), page);
    flex: 0 0 auto;
    order: 4;
    font-size: 10pt; color: #333;
    min-width: 0.25in; text-align: right;
}
.toc-front, .toc-back {
    font-weight: 600;
    margin-top: 0.08in;
}
.toc-part-header {
    margin-top: 0.22in; margin-bottom: 0.05in;
    font-size: 11.5pt; color: #1a1a1a; font-weight: bold;
    letter-spacing: 0.03em;
    padding-left: 0.05in;
}
.toc-part-header a { color: inherit; text-decoration: none; }

/* === PART PAGES (recto) === */
.part-page {
    break-before: right;
    text-align: center;
    padding-top: 1.6in;
    page-break-after: always;
}
.part-page .part-label {
    font-size: 10pt; letter-spacing: 0.22em;
    color: #666; text-transform: uppercase;
    margin-bottom: 0.18in;
}
.part-page .part-title {
    font-size: 22pt; font-weight: bold;
    line-height: 1.25; color: #1a1a1a;
    margin: 0 0.3in 0.3in;
}
.part-page .part-rule {
    width: 0.9in; height: 1px; background: #bbb;
    margin: 0.25in auto 0.3in;
}
.part-page .part-intro {
    text-align: left;
    max-width: 4in; margin: 0 auto;
    font-size: 11pt; font-style: italic;
    color: #333; line-height: 1.6;
}
.part-page .part-intro p {
    text-indent: 0;
    margin-bottom: 8pt;
}

/* === CHAPTERS — start on recto pages === */
.chapter { break-before: right; }

.chapter-header {
    text-align: center;
    margin-bottom: 0.45in;
    padding-top: 0.6in;
}
.chapter-header .chapter-num {
    font-size: 10pt; letter-spacing: 0.18em; color: #666;
    margin-bottom: 10pt; text-transform: uppercase;
}
.chapter-header h1 {
    font-size: 22pt; font-weight: bold; color: #1a1a1a;
    margin: 0 0 0.18in 0; line-height: 1.2;
    padding: 0 0.3in;
}
.chapter-header .chapter-rule {
    width: 0.7in; height: 1px; background: #bbb;
    margin: 0.15in auto 0;
}

/* Preface: hide the empty H1 (preface has no separate title) */
.chapter.preface .chapter-header h1 { display: none; }

/* === BODY === */
.chapter-body p {
    text-align: justify; text-indent: 0.3in;
    margin: 0; orphans: 2; widows: 2; hyphens: auto;
}
.chapter-body > p:first-child,
.chapter-body > hr + p,
.chapter-body > h2 + p,
.chapter-body > h3 + p {
    text-indent: 0;
}

.chapter-body hr {
    border: none; text-align: center;
    margin: 0.25in 0 0.15in; padding: 0; height: 10pt;
}
.chapter-body hr::before {
    content: "\2766";
    color: #aaa; font-size: 11pt; letter-spacing: 0.4em;
}

.chapter-body h2 {
    font-size: 13pt; font-weight: bold; color: #1a1a1a;
    margin-top: 0.3in; margin-bottom: 0.12in;
    page-break-after: avoid; break-after: avoid-page;
    orphans: 3; widows: 3; text-align: center;
}
.chapter-body h3 {
    font-size: 11.5pt; font-weight: bold; font-style: italic;
    color: #1a1a1a; margin-top: 0.28in; margin-bottom: 0.1in;
    page-break-after: avoid; break-after: avoid-page;
    orphans: 3; widows: 3; text-align: center;
}
.chapter-body h2 + p,
.chapter-body h3 + p {
    page-break-before: avoid; break-before: avoid-page;
    orphans: 4; widows: 4;
}

/* === SCRIPTURE BLOCKQUOTES === */
.chapter-body blockquote {
    margin: 0.22in 0.35in 0.22in 0.4in;
    padding: 0.02in 0 0.02in 0.22in;
    border-left: 1.5pt solid #6f8d6f;
    font-style: italic; font-size: 10.5pt; line-height: 1.55;
    color: #222;
    page-break-inside: avoid; break-inside: avoid;
}
.chapter-body blockquote p {
    text-indent: 0 !important; text-align: left;
    margin: 0; hyphens: auto;
}
.chapter-body blockquote cite {
    display: block; margin-top: 5pt;
    font-style: normal; font-size: 8.5pt;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: #555; text-align: right;
}

/* === SCRIPTURE INDEX === */
.scripture-index { break-before: right; }
.scripture-index h1 {
    font-size: 20pt; font-weight: bold; text-align: center;
    margin-bottom: 0.4in; padding-top: 0.5in;
    color: #1a1a1a; letter-spacing: 0.04em;
}
.scripture-index .index-intro {
    text-align: center; font-size: 9.5pt; font-style: italic;
    color: #666; margin-bottom: 0.35in;
    padding: 0 0.5in;
}
.index-book-group { page-break-inside: avoid; break-inside: avoid; }
.index-book {
    font-size: 12pt; font-weight: bold; color: #1a1a1a;
    margin-top: 0.2in; margin-bottom: 0.08in;
    page-break-after: avoid; break-after: avoid;
}
.index-entry {
    font-size: 10pt; line-height: 1.7;
    margin-left: 0.2in; color: #333;
    display: flex; gap: 0.15in;
}
.index-entry .index-ref { flex: 0 0 auto; min-width: 1.65in; }
.index-entry .index-chapters {
    flex: 1 1 auto; font-style: italic;
    font-size: 9.5pt; color: #555;
}

.pad-page {
    page: front-matter;
    page-break-before: always;
    visibility: hidden;
}

em { font-style: italic; }
strong { font-weight: bold; }
a { color: inherit; text-decoration: none; }
"""


# ============================================================================
# FULL HTML ASSEMBLY
# ============================================================================

def build_full_html(book, toc_html, scripture_index_html):
    css = CSS.replace("FONT_DIR", str(FONT_DIR))

    part_sections = []
    for p_idx, part in enumerate(book["parts"], start=1):
        part_sections.append(build_part_page(part, p_idx))
        for ch in part["chapters"]:
            part_sections.append(build_chapter(ch))

    preface_html = build_preface(book["preface_md"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{TITLE}</title>
  <style>{css}</style>
</head>
<body>

  <div class="half-title-page">
    <h1>{TITLE}</h1>
  </div>

  <div class="title-page">
    <h1>{TITLE}</h1>
    <p class="book-subtitle">{SUBTITLE}</p>
    <div class="title-rule"></div>
    <p class="author">{AUTHOR.upper()}</p>
    <p class="imprint">{PUBLISHER}</p>
  </div>

  <div class="copyright-page">
    <p>{TITLE}<br><em>{SUBTITLE}</em></p>
    <p>Copyright &copy; 2026 {AUTHOR}</p>
    <p>All rights reserved.</p>
    <div class="sep"></div>
    <p>First Edition.</p>
    <p>Published by {PUBLISHER}</p>
    <p>noblemind.study</p>
    <div class="sep"></div>
    <p>Scripture quotations are taken from the New American Standard Bible&reg;<br>
    (NASB), Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <div class="sep"></div>
    <p>No part of this publication may be reproduced, stored in a retrieval system,<br>
    or transmitted in any form or by any means without the prior written<br>
    permission of the author, except as provided by U.S. copyright law.</p>
    <div class="sep"></div>
    <p>Printed in the United States of America</p>
  </div>

  <div class="epigraph-page">
    <blockquote>
      <p><em>A position must stand or fall based on what the Scriptures actually teach.</em></p>
      <cite>&mdash; the thesis of this booklet</cite>
    </blockquote>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {preface_html}
  {"".join(part_sections)}

  <section class="scripture-index" id="scripture-index">
    <h1>Scripture Index</h1>
    <p class="index-intro">References are listed in the canonical order of the Bible. The chapter(s) of this booklet in which each reference appears are given as &ldquo;Ch.&rdquo; (chapter) or &ldquo;Pref&rdquo; (Preface).</p>
    {scripture_index_html}
  </section>

</body>
</html>"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f'Generating Lulu interior PDF for "{TITLE}"...')
    book = parse_book()
    print(f"  Parsed: {len(book['chapters'])} chapters in {len(book['parts'])} parts")
    print(f"  Page size: 5.5\" x 8.5\"")
    print(f"  Gutter: 0.75in inside, 0.625in outside")

    print("Building TOC...")
    toc_html = build_toc(book)

    print("Building Scripture index...")
    scripture_index_html = build_scripture_index_html()

    print("Assembling HTML...")
    full_html = build_full_html(book, toc_html, scripture_index_html)

    debug = BOOK_DIR / "_lulu_debug.html"
    debug.write_text(full_html, encoding="utf-8")

    print("Rendering PDF...")
    doc = weasyprint.HTML(string=full_html, base_url=str(BOOK_DIR))
    pdf_doc = doc.render()
    page_count = len(pdf_doc.pages)
    print(f"  Raw page count: {page_count}")

    if page_count % 2 != 0:
        print("  Odd page count; adding a blank pad page.")
        padded = full_html.replace(
            "</body>",
            '<div class="pad-page">&nbsp;</div>\n</body>',
        )
        doc = weasyprint.HTML(string=padded, base_url=str(BOOK_DIR))
        pdf_doc = doc.render()
        page_count = len(pdf_doc.pages)
        print(f"  Adjusted page count: {page_count}")

    pdf_doc.write_pdf(str(OUTPUT))
    print(f"\nWrote {OUTPUT.name}")
    print(f"  Total pages: {page_count}")
    print(f"  Fonts embedded; Parts and Chapters on recto; Scripture index included.")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
