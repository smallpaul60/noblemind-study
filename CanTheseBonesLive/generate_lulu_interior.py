#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for Can These Bones Live?

Specs for 5.5" x 8.5" (no bleed, text-only):
  - Page size: 5.5in x 8.5in
  - Gutter (inside margin): 0.75in
  - Outside margin: 0.625in
  - Top/bottom margin: 0.75in
  - Chapters start on recto (right-hand, odd) pages
  - All fonts embedded
  - Page count divisible by 2

Front matter: half-title, title, copyright (no ISBN), epigraph, contents.
Back matter: Appendix A (Author's Note), Appendix B (Pattern at a Glance),
Scripture Index.
"""

import re
from collections import OrderedDict
from pathlib import Path

import markdown
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "CanTheseBonesLive_Lulu_Interior.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

TITLE = "Can These Bones Live?"
SUBTITLE = "How God Has Always Made Dead Things Live"
AUTHOR = "Paul Hainline"

CHAPTERS = [
    ("chapter1-can-these-bones-live.md",  "Chapter One",    "The Valley"),
    ("chapter2-can-these-bones-live.md",  "Chapter Two",    "Dust and Breath"),
    ("chapter3-can-these-bones-live.md",  "Chapter Three",  "When the Word Goes Silent"),
    ("chapter4-can-these-bones-live.md",  "Chapter Four",   "Destroyed for Lack of Knowledge"),
    ("chapter5-can-these-bones-live.md",  "Chapter Five",   "The Book Lost in the Temple"),
    ("chapter6-can-these-bones-live.md",  "Chapter Six",    "Prophesy to These Bones"),
    ("chapter7-can-these-bones-live.md",  "Chapter Seven",  "Breathe on These Slain"),
    ("chapter8-can-these-bones-live.md",  "Chapter Eight",  "A Rushing Mighty Wind"),
    ("chapter9-can-these-bones-live.md",  "Chapter Nine",   "The Israel of God"),
    ("chapter10-can-these-bones-live.md", "Chapter Ten",    "Letters to the Dead"),
    ("chapter11-can-these-bones-live.md", "Chapter Eleven", "Can These Bones Live?"),
]

APPENDICES = [
    ("Appendix_A_Authors-Note.md",            "Appendix A", "A Note from the Author"),
    ("Appendix_B_The_Pattern_at_a_Glance.md", "Appendix B", "The Pattern at a Glance"),
]


# ============================================================================
# MARKDOWN -> HTML
# ============================================================================

def convert_md_body(md_text):
    """Convert a Markdown document body to HTML with print styling.

    Strips the first H1 and the first H2 (which is the chapter title —
    we render the chapter header ourselves).
    """
    # Remove first H1 (# Can These Bones Live? ...)
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    # Remove first H2 (## The Valley, etc.) — we render the title separately
    md_text = re.sub(r'^##\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()

    md_text = promote_scripture_paragraphs(md_text)

    html = markdown.markdown(md_text, extensions=['smarty', 'tables'])
    html = lift_citation_to_cite(html)
    return html


def promote_scripture_paragraphs(md_text):
    """Rewrite standalone Scripture-quote paragraphs as Markdown blockquotes.

    A paragraph qualifies when the whole paragraph is a quoted sentence
    followed by a single `(Book C:V)` citation. Inline quotes embedded in
    a larger paragraph are left alone.
    """
    paragraphs = re.split(r'\n\s*\n', md_text)
    out = []
    for para in paragraphs:
        stripped = para.strip()
        if stripped and SCRIPTURE_PARA_RE.match(stripped):
            out.append("> " + stripped)
        else:
            out.append(para)
    return "\n\n".join(out)


def lift_citation_to_cite(html):
    return CITE_IN_BLOCKQUOTE_RE.sub(
        r'\1\2</p><cite>\3</cite></blockquote>', html
    )


def build_chapter_html(filename, chapter_label, title, chapter_id):
    md_text = (BOOK_DIR / filename).read_text(encoding='utf-8')
    body_html = convert_md_body(md_text)
    return f"""
    <section class="chapter" id="{chapter_id}">
      <div class="chapter-header">
        <p class="chapter-num">{chapter_label}</p>
        <h1>{title}</h1>
        <div class="chapter-rule"></div>
      </div>
      <div class="chapter-body">
        {body_html}
      </div>
    </section>
    """


def build_appendix_html(filename, label, title, section_id):
    md_text = (BOOK_DIR / filename).read_text(encoding='utf-8')
    body_html = convert_md_body(md_text)
    return f"""
    <section class="chapter appendix" id="{section_id}">
      <div class="chapter-header">
        <p class="chapter-num">{label}</p>
        <h1>{title}</h1>
        <div class="chapter-rule"></div>
      </div>
      <div class="chapter-body">
        {body_html}
      </div>
    </section>
    """


# ============================================================================
# TABLE OF CONTENTS
# ============================================================================

def build_toc():
    rows = []
    for i, (_filename, chapter_label, title) in enumerate(CHAPTERS):
        ch_id = f"ch-{i + 1}"
        rows.append(
            f'<div class="toc-entry">'
            f'<a href="#{ch_id}">'
            f'<span class="toc-num">{chapter_label}</span>'
            f'<span class="toc-dots"></span>'
            f'<span class="toc-title">{title}</span>'
            f'<span class="toc-page"></span>'
            f'</a></div>'
        )
    # Appendices
    for i, (_filename, label, title) in enumerate(APPENDICES):
        ap_id = f"ap-{i + 1}"
        rows.append(
            f'<div class="toc-entry toc-appendix">'
            f'<a href="#{ap_id}">'
            f'<span class="toc-num">{label}</span>'
            f'<span class="toc-dots"></span>'
            f'<span class="toc-title">{title}</span>'
            f'<span class="toc-page"></span>'
            f'</a></div>'
        )
    # Scripture index
    rows.append(
        '<div class="toc-entry toc-appendix">'
        '<a href="#scripture-index">'
        '<span class="toc-num"></span>'
        '<span class="toc-dots"></span>'
        '<span class="toc-title">Scripture Index</span>'
        '<span class="toc-page"></span>'
        '</a></div>'
    )
    return "\n".join(rows)


# ============================================================================
# SCRIPTURE INDEX
# ============================================================================

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
BOOK_ORDER_MAP = {name: i for i, name in enumerate(BIBLE_BOOK_ORDER)}

# Build a regex that matches any canonical book name. Sort by length (desc)
# so "1 Samuel" wins over "Samuel" and "Song of Solomon" matches before
# accidental single-word overlaps.
_BOOK_ALT = "|".join(
    re.escape(b) for b in sorted(BIBLE_BOOK_ORDER, key=len, reverse=True)
)
# Capture: book, chapter, verse_start (opt), verse_end (opt)
# Allows: "Genesis 1", "Genesis 1:26", "Genesis 1:26-27", "Genesis 1:26–27"
REF_RE = re.compile(
    rf'\b({_BOOK_ALT})\s+(\d+)(?::(\d+)(?:\s*[\u2013\u2014\-]\s*(\d+))?)?'
)

# Matches a whole paragraph that is a single quoted Scripture citation,
# e.g. "Our bones are dried up..." (Ezekiel 37:11).
# Handles straight or curly quotes, nested internal quotes, optional
# trailing period, and hyphen / en-dash / em-dash verse ranges.
SCRIPTURE_PARA_RE = re.compile(
    r'^\s*["\u201c\u201d](.+)["\u201c\u201d]\s+'
    r'\(((?:' + _BOOK_ALT + r')\s+\d+(?::\d+(?:\s*[\u2013\u2014-]\s*\d+)?)?)\)'
    r'\.?\s*$'
)

# After markdown conversion, lift the trailing `(Book C:V).` out of the
# blockquote paragraph and render it as a <cite> attribution.
CITE_IN_BLOCKQUOTE_RE = re.compile(
    r'(<blockquote>\s*<p>)(.*?)\s*\(((?:' + _BOOK_ALT
    + r')\s+\d+(?::\d+(?:\s*[\u2013\u2014-]\s*\d+)?)?)\)\.?\s*</p>\s*</blockquote>',
    re.DOTALL,
)


def extract_refs(text):
    """Return list of (book, chapter, verse_start, display_string).
    A reference with no verse is still included (chapter-level).
    """
    refs = []
    for m in REF_RE.finditer(text):
        book = m.group(1)
        chap = int(m.group(2))
        verse_start = m.group(3)
        verse_end = m.group(4)
        if verse_start is None:
            # Chapter-only reference: only index it if the context actually
            # reads like a citation (not e.g. "Acts 2 led to..."). We accept
            # chapter-only for now; they're rare and the index benefits from
            # comprehensiveness.
            display = f"{book} {chap}"
            key = (book, chap, 0)
        else:
            v = int(verse_start)
            if verse_end:
                display = f"{book} {chap}:{v}\u2013{verse_end}"
            else:
                display = f"{book} {chap}:{v}"
            key = (book, chap, v)
        refs.append((book, chap, key[2], display))
    return refs


def build_scripture_index(all_sources):
    """Build HTML for the Scripture Index.

    all_sources: list of (chapter_number_or_label, text). For chapters we
    pass the chapter number (1..11). For appendices we pass "A" or "B".
    """
    # display_string -> (sort_key, book, set(chapter_labels_in_order))
    entries = {}  # display -> dict(sort_key, book, chapters=OrderedDict of label->None)

    for label, text in all_sources:
        for book, chap, verse, display in extract_refs(text):
            sort_key = (BOOK_ORDER_MAP.get(book, 999), chap, verse)
            rec = entries.get(display)
            if rec is None:
                rec = {"sort_key": sort_key, "book": book, "chapters": OrderedDict()}
                entries[display] = rec
            rec["chapters"][label] = None

    # Sort entries by sort_key
    sorted_items = sorted(entries.items(), key=lambda kv: kv[1]["sort_key"])

    # Group by display-book (merge "Psalm" and "Psalms" under "Psalms")
    books_grouped = OrderedDict()
    for display, rec in sorted_items:
        book = rec["book"]
        display_book = "Psalms" if book == "Psalm" else book
        books_grouped.setdefault(display_book, []).append((display, rec))

    # Emit HTML, keeping book heading with first two entries so a heading
    # never appears orphaned at the bottom of a page.
    parts = []
    for display_book, rows in books_grouped.items():
        head_html = f'<h3 class="index-book">{display_book}</h3>'
        entry_htmls = []
        for display, rec in rows:
            ch_labels = list(rec["chapters"].keys())
            ch_labels_str = ", ".join(str(x) for x in ch_labels)
            entry_htmls.append(
                f'<div class="index-entry">'
                f'<span class="index-ref">{display}</span>'
                f'<span class="index-chapters">Ch. {ch_labels_str}</span>'
                f'</div>'
            )
        # Group heading with first 2 entries
        grouped = head_html + "\n" + "\n".join(entry_htmls[:2])
        parts.append(f'<div class="index-book-group">{grouped}</div>')
        parts.extend(entry_htmls[2:])

    return "\n".join(parts)


# ============================================================================
# CSS
# ============================================================================

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
    margin: 0;
    padding: 0;
}

/* === HALF-TITLE PAGE (page 1, recto) === */
.half-title-page {
    page: front-matter;
    page-break-after: always;
    text-align: center;
    padding-top: 3.2in;
}
.half-title-page h1 {
    font-size: 18pt;
    font-weight: normal;
    letter-spacing: 0.04em;
    color: #1a1a1a;
    line-height: 1.25;
}

/* === TITLE PAGE === */
.title-page {
    page: front-matter;
    break-before: right;
    page-break-after: always;
    text-align: center;
    padding-top: 2in;
}
.title-page h1 {
    font-size: 28pt;
    font-weight: bold;
    line-height: 1.2;
    margin-bottom: 0.2in;
    color: #1a1a1a;
}
.title-page .book-subtitle {
    font-size: 13pt;
    font-style: italic;
    color: #444;
    margin-bottom: 1in;
    line-height: 1.4;
    padding: 0 0.3in;
}
.title-page .title-rule {
    width: 1.2in;
    height: 1px;
    background: #aaa;
    margin: 0.35in auto 0.5in;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 1.2in;
    color: #1a1a1a;
    letter-spacing: 0.08em;
}
.title-page .imprint {
    font-size: 10pt;
    font-style: italic;
    color: #666;
    margin-top: 0.25in;
}

/* === COPYRIGHT PAGE === */
.copyright-page {
    page: front-matter;
    page-break-after: always;
    padding-top: 2.2in;
}
.copyright-page p {
    font-size: 9pt;
    line-height: 1.5;
    color: #555;
    margin: 0 0 6pt 0;
    text-align: center;
}
.copyright-page .sep {
    height: 10pt;
}

/* === EPIGRAPH === */
.epigraph-page {
    page: front-matter;
    break-before: right;
    page-break-after: always;
    padding-top: 3.5in;
    text-align: center;
}
.epigraph-page blockquote {
    margin: 0 0.8in;
    font-style: italic;
    font-size: 12pt;
    line-height: 1.5;
    color: #222;
    border: none;
    padding: 0;
}
.epigraph-page cite {
    display: block;
    margin-top: 0.25in;
    font-style: normal;
    font-size: 10pt;
    color: #666;
    letter-spacing: 0.04em;
}

/* === TABLE OF CONTENTS === */
.toc-section {
    page: toc-page;
    break-before: right;
    page-break-after: always;
}
.toc-section h1 {
    font-size: 20pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0.45in;
    padding-top: 0.3in;
    color: #1a1a1a;
    letter-spacing: 0.04em;
}
.toc-entry {
    font-size: 10.5pt;
    line-height: 1.9;
    color: #222;
}
.toc-entry a {
    color: inherit;
    text-decoration: none;
    display: flex;
    align-items: baseline;
    gap: 0.08in;
}
.toc-entry .toc-num {
    flex: 0 0 auto;
    font-variant: small-caps;
    font-size: 9.5pt;
    letter-spacing: 0.06em;
    color: #555;
    min-width: 1.15in;
    order: 1;
}
.toc-entry .toc-title {
    flex: 0 1 auto;
    order: 2;
}
.toc-entry .toc-dots {
    flex: 1 1 auto;
    border-bottom: 1px dotted #bbb;
    transform: translateY(-3px);
    margin: 0 0.1in;
    order: 3;
}
/* target-counter must live on the anchor so attr(href) is defined */
.toc-entry a::after {
    content: target-counter(attr(href), page);
    flex: 0 0 auto;
    order: 4;
    font-size: 10pt;
    color: #333;
    min-width: 0.25in;
    text-align: right;
}
.toc-entry .toc-page { display: none; }
.toc-appendix {
    margin-top: 0.12in;
}
.toc-appendix .toc-num {
    font-style: italic;
}

/* === CHAPTERS -- start on recto pages === */
.chapter {
    break-before: right;
}

.chapter-header {
    text-align: center;
    margin-bottom: 0.45in;
    padding-top: 0.6in;
}

.chapter-header .chapter-num {
    font-size: 10pt;
    letter-spacing: 0.18em;
    color: #666;
    margin-bottom: 10pt;
    text-transform: uppercase;
}

.chapter-header h1 {
    font-size: 22pt;
    font-weight: bold;
    color: #1a1a1a;
    margin: 0 0 0.18in 0;
    line-height: 1.2;
}

.chapter-header .chapter-rule {
    width: 0.7in;
    height: 1px;
    background: #bbb;
    margin: 0.15in auto 0;
}

/* === BODY TEXT === */
.chapter-body p {
    text-align: justify;
    text-indent: 0.3in;
    margin-bottom: 0;
    margin-top: 0;
    orphans: 2;
    widows: 2;
    hyphens: auto;
}

/* First paragraph of a chapter / section: no indent */
.chapter-body > p:first-child,
.chapter-body > hr + p,
.chapter-body > h2 + p,
.chapter-body > h3 + p {
    text-indent: 0;
}

/* Section break (---) rendered as centered ornament */
.chapter-body hr {
    border: none;
    text-align: center;
    margin: 0.25in 0 0.15in;
    padding: 0;
    height: 10pt;
}
.chapter-body hr::before {
    content: "\2766";          /* floral heart ornament */
    color: #aaa;
    font-size: 11pt;
    letter-spacing: 0.4em;
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
    text-align: center;
}

.chapter-body h3 {
    font-size: 11.5pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.28in;
    margin-bottom: 0.1in;
    page-break-after: avoid;
    break-after: avoid;
    orphans: 3;
    widows: 3;
    text-align: center;
    font-style: italic;
}

/* === BLOCKQUOTES (scripture / display quotes) ===
   Standalone Scripture paragraphs are auto-promoted to blockquotes and
   the citation is lifted into a <cite> attribution (see generate script).
*/
.chapter-body blockquote {
    margin: 0.22in 0.35in 0.22in 0.4in;
    padding: 0.02in 0 0.02in 0.22in;
    border-left: 1.5pt solid #8a8a8a;
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.55;
    color: #222;
    page-break-inside: avoid;
    break-inside: avoid;
}
.chapter-body blockquote p {
    text-indent: 0 !important;
    text-align: left;
    margin: 0;
    hyphens: auto;
}
.chapter-body blockquote cite {
    display: block;
    margin-top: 5pt;
    font-style: normal;
    font-size: 8.5pt;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #555;
    text-align: right;
}
.chapter-body blockquote cite::before {
    content: "\2014\00a0";  /* em-dash + non-breaking space */
}

/* === TABLES (Appendix B) === */
.chapter-body table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.3in 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}
.chapter-body th,
.chapter-body td {
    border-top: 0.5pt solid #bbb;
    border-bottom: 0.5pt solid #bbb;
    padding: 5pt 5pt;
    vertical-align: top;
    text-align: left;
    line-height: 1.35;
}
.chapter-body th {
    font-weight: bold;
    background: #f2efe8;
    border-top: 1pt solid #888;
    border-bottom: 1pt solid #888;
    text-align: left;
}

/* === SCRIPTURE INDEX === */
.scripture-index {
    break-before: right;
}
.scripture-index h1 {
    font-size: 20pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0.4in;
    padding-top: 0.5in;
    color: #1a1a1a;
    letter-spacing: 0.04em;
}
.scripture-index .index-intro {
    text-align: center;
    font-size: 9.5pt;
    font-style: italic;
    color: #666;
    margin-bottom: 0.35in;
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
    display: flex;
    gap: 0.15in;
}
.index-entry .index-ref {
    flex: 0 0 auto;
    min-width: 1.4in;
}
.index-entry .index-chapters {
    flex: 1 1 auto;
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
a { color: inherit; text-decoration: none; }
"""


# ============================================================================
# FULL HTML ASSEMBLY
# ============================================================================

def build_full_html(chapter_sections, toc_html, appendix_sections, scripture_index_html):
    css = CSS.replace("FONT_DIR", str(FONT_DIR))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{TITLE}</title>
  <style>{css}</style>
</head>
<body>

  <!-- HALF-TITLE (page 1, recto) -->
  <div class="half-title-page">
    <h1>{TITLE}</h1>
  </div>

  <!-- TITLE PAGE (recto) -->
  <div class="title-page">
    <h1>{TITLE}</h1>
    <p class="book-subtitle">{SUBTITLE}</p>
    <div class="title-rule"></div>
    <p class="author">{AUTHOR.upper()}</p>
    <p class="imprint">NobleMind Press</p>
  </div>

  <!-- COPYRIGHT (verso) -->
  <div class="copyright-page">
    <p>{TITLE}: {SUBTITLE}</p>
    <p>Copyright \u00a9 2026 {AUTHOR}</p>
    <p>All rights reserved.</p>
    <div class="sep"></div>
    <p>Published by NobleMind Press</p>
    <p>noblemind.study</p>
    <div class="sep"></div>
    <p>Scripture quotations are taken from the New American Standard Bible\u00ae (NASB),<br>
    Copyright \u00a9 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <div class="sep"></div>
    <p>No part of this publication may be reproduced, stored in a retrieval system,<br>
    or transmitted in any form or by any means without the prior written<br>
    permission of the author, except as provided by U.S. copyright law.</p>
    <div class="sep"></div>
    <p>Printed in the United States of America</p>
  </div>

  <!-- EPIGRAPH (recto) -->
  <div class="epigraph-page">
    <blockquote>
      <p>\u201cSon of man, can these bones live?\u201d</p>
      <cite>\u2014 Ezekiel 37:3</cite>
    </blockquote>
  </div>

  <!-- TABLE OF CONTENTS (starts recto) -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- CHAPTERS -->
  {chapter_sections}

  <!-- APPENDICES -->
  {appendix_sections}

  <!-- SCRIPTURE INDEX -->
  <section class="scripture-index" id="scripture-index">
    <h1>Scripture Index</h1>
    <p class="index-intro">Chapter numbers are given (\u201cCh.\u201d), not page numbers.</p>
    {scripture_index_html}
  </section>

</body>
</html>"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f'Generating Lulu interior PDF for "{TITLE}"...')
    print(f'  Page size: 5.5" x 8.5"')
    print(f"  Gutter: 0.75in inside, 0.625in outside")
    print(f"  Font: EB Garamond (from {FONT_DIR})")
    print()

    print("Building table of contents...")
    toc_html = build_toc()

    print("Building chapter HTML...")
    chapter_sections = []
    for i, (filename, chapter_label, title) in enumerate(CHAPTERS):
        print(f"  Ch {i + 1}: {title}")
        chapter_sections.append(
            build_chapter_html(filename, chapter_label, title, f"ch-{i + 1}")
        )

    print("Building appendix HTML...")
    appendix_sections = []
    for i, (filename, label, title) in enumerate(APPENDICES):
        print(f"  {label}: {title}")
        appendix_sections.append(
            build_appendix_html(filename, label, title, f"ap-{i + 1}")
        )

    print("Building scripture index...")
    all_sources = []
    for i, (filename, _label, _title) in enumerate(CHAPTERS):
        txt = (BOOK_DIR / filename).read_text(encoding='utf-8')
        all_sources.append((i + 1, txt))
    for i, (filename, _label, _title) in enumerate(APPENDICES):
        txt = (BOOK_DIR / filename).read_text(encoding='utf-8')
        all_sources.append(("A" if i == 0 else "B", txt))
    scripture_index_html = build_scripture_index(all_sources)

    print("Assembling HTML...")
    full_html = build_full_html(
        "\n".join(chapter_sections),
        toc_html,
        "\n".join(appendix_sections),
        scripture_index_html,
    )

    debug_html = BOOK_DIR / "_lulu_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")
    print(f"  Debug HTML saved to {debug_html}")

    print("Rendering PDF with WeasyPrint (fonts will be embedded)...")
    doc = weasyprint.HTML(string=full_html, base_url=str(BOOK_DIR))
    pdf_doc = doc.render()

    page_count = len(pdf_doc.pages)
    print(f"  Raw page count: {page_count}")

    if page_count % 2 != 0:
        print(f"  Page count {page_count} is odd; adding a blank pad page...")
        padded = full_html.replace(
            "</body>",
            '<div class="pad-page">&nbsp;</div>\n</body>'
        )
        doc = weasyprint.HTML(string=padded, base_url=str(BOOK_DIR))
        pdf_doc = doc.render()
        page_count = len(pdf_doc.pages)
        print(f"  Adjusted page count: {page_count}")

    pdf_doc.write_pdf(str(OUTPUT))
    print(f"\nPDF saved to {OUTPUT}")
    print(f"  Total pages: {page_count}")
    print(f"  Chapters start on recto pages, fonts embedded, Scripture index included.")
    print("Done.")


if __name__ == "__main__":
    main()
