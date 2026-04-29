#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for Change the Mind, Change the Man.

Lulu specs for 5.5" x 8.5" Digest (no bleed, text-only):
  - Page size: 5.5in x 8.5in
  - Safety margin: 0.5in minimum on all sides
  - Gutter (inside margin): 0.75in
  - Outside margin: 0.625in
  - Chapters start on recto (right-hand, odd) pages
  - Alternating left/right margins for facing pages
  - All fonts embedded
  - No trim/bleed/margin lines
"""

import re
from pathlib import Path
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "ChangeTheMind_ChangeTheMan_Lulu_Interior.pdf"

CHAPTERS = [
    ("chapter01_the_phone_call.md", "Chapter 1", "The Phone Call",
     "The moment everything splits into before and after."),
    ("chapter02_the_progression.md", "Chapter 2", "The Progression",
     "How the mind turns \u2014 one step at a time."),
    ("chapter03_where_did_we_go_wrong.md", "Chapter 3", "Where Did We Go Wrong?",
     "The question that keeps the family awake \u2014 and the answer no one wants to hear."),
    ("chapter04_imprisoned.md", "Chapter 4", "All of the Imprisoned Are Not in Prison",
     "Not every prison has walls you can see."),
    ("chapter05_love_that_says_no.md", "Chapter 5", "Love That Says No",
     "What if helping is the very thing that is hurting them?"),
    ("chapter06_think.md", "Chapter 6", "THINK!", "Think. Think. Think."),
    ("chapter07_coming_to_himself.md", "Chapter 7", "Coming to Himself", "True repentance has feet."),
    ("chapter08_the_father_ran.md", "Chapter 8", "The Father Ran",
     "He did not wait for the speech."),
    ("chapter09_the_long_road.md", "Chapter 9", "The Long Road",
     "Recovery is not a moment. It is a road made of mornings."),
    ("chapter10_the_god_who_finds_you.md", "Chapter 10", "The God Who Finds You",
     "Come to Me, all who are weary and heavy-laden."),
]


def parse_markdown_to_html(md_text):
    """Convert chapter markdown body text to HTML.

    Handles: paragraphs, blockquotes with citations, emphasis, bold,
    section dividers (bullet separators), and sub-headings.
    """
    lines = md_text.strip().split("\n")
    html_parts = []
    i = 0
    in_blockquote = False
    bq_lines = []

    def flush_blockquote():
        nonlocal in_blockquote, bq_lines
        if not bq_lines:
            in_blockquote = False
            return
        # Separate citation from quote text
        quote_lines = []
        cite_text = None
        for bl in bq_lines:
            stripped = bl.lstrip("> ").strip()
            if stripped.startswith("\u2014 ") or stripped.startswith("— "):
                cite_text = stripped[2:].strip()
            else:
                quote_lines.append(stripped)
        # Build quote paragraphs
        quote_html = format_inline("\n".join(quote_lines))
        # Split into paragraphs on blank lines
        quote_paragraphs = re.split(r'\n\s*\n', quote_html)
        inner = ""
        for qp in quote_paragraphs:
            qp = qp.strip()
            if qp:
                inner += f"<p>{qp}</p>\n"
        cite_html = f'<cite>{format_inline(cite_text)}</cite>' if cite_text else ""
        html_parts.append(f'<blockquote class="scripture">\n{inner}{cite_html}\n</blockquote>')
        bq_lines = []
        in_blockquote = False

    def format_inline(text):
        """Convert inline markdown (bold, italic, etc.) to HTML."""
        # Bold+italic ***text*** or ___text___
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        # Bold **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic *text*
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Line breaks
        text = text.replace("\n", " ")
        return text

    while i < len(lines):
        line = lines[i]

        # Skip the chapter title lines (# **Chapter N**, # **Title**, ## *subtitle*)
        # These are handled by the chapter header template
        if i < 6 and (line.startswith("# **") or line.startswith("## *")):
            i += 1
            continue

        # Skip top-level headings that duplicate chapter title
        if line.startswith("# "):
            i += 1
            continue

        # Section dividers: lines like "• • •" or "•  •  •" or "* * *"
        stripped = line.strip()
        if stripped in ("• • •", "•  •  •", "•   •   •", "* * *", "---"):
            flush_blockquote()
            html_parts.append('<div class="divider">\u2022\u2003\u2022\u2003\u2022</div>')
            i += 1
            continue

        # Sub-headings (## within body)
        if line.startswith("## "):
            flush_blockquote()
            heading_text = line[3:].strip().strip("*")
            html_parts.append(f'<h2>{format_inline(heading_text)}</h2>')
            i += 1
            continue

        # Sub-sub-headings (### within body)
        if line.startswith("### "):
            flush_blockquote()
            heading_text = line[4:].strip().strip("*")
            html_parts.append(f'<h3>{format_inline(heading_text)}</h3>')
            i += 1
            continue

        # Blockquote lines
        if line.startswith("> ") or line.startswith(">"):
            in_blockquote = True
            bq_lines.append(line)
            i += 1
            continue

        # If we were in a blockquote and hit a non-quote line, flush
        if in_blockquote:
            flush_blockquote()

        # Blank lines
        if stripped == "" or stripped == "&nbsp;":
            i += 1
            continue

        # Standalone citation line: "— Book C:V" or "— Book C:V (NASB)"
        # This follows a standalone italic quote and should attach to the
        # previous element as a citation
        if stripped.startswith("— ") or stripped.startswith("\u2014 "):
            cite_ref = stripped[2:].strip()
            # Check if previous html_part was a scripture quote paragraph
            # Convert the last paragraph into a blockquote with citation
            if html_parts and html_parts[-1].startswith("<p>"):
                last_p = html_parts.pop()
                # Extract paragraph content
                p_content = re.sub(r'^<p>(.*)</p>$', r'\1', last_p, flags=re.DOTALL)
                cite_html = f'<cite>{format_inline(cite_ref)}</cite>'
                html_parts.append(
                    f'<blockquote class="scripture">\n<p>{p_content}</p>\n{cite_html}\n</blockquote>'
                )
            else:
                # Just render as a citation line
                html_parts.append(f'<p class="citation">{format_inline(cite_ref)}</p>')
            i += 1
            continue

        # Regular paragraph — collect continuation lines
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            next_stripped = next_line.strip()
            # Stop at blank, heading, blockquote, divider, citation line
            if (next_stripped == "" or next_stripped == "&nbsp;" or
                next_line.startswith("#") or next_line.startswith("> ") or
                next_stripped.startswith("— ") or next_stripped.startswith("\u2014 ") or
                next_stripped in ("• • •", "•  •  •", "•   •   •", "* * *", "---")):
                break
            para_lines.append(next_line)
            i += 1

        para_text = " ".join(l.strip() for l in para_lines)
        html_parts.append(f"<p>{format_inline(para_text)}</p>")

    # Flush any remaining blockquote
    flush_blockquote()

    return "\n".join(html_parts)


def extract_chapter_body(md_text):
    """Extract the body text, skipping the chapter heading lines at top."""
    lines = md_text.strip().split("\n")
    # Skip initial heading lines (# **Chapter N**, # **Title**, ## *subtitle*, blank)
    body_start = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") or stripped.startswith("## ") or stripped == "" or stripped == "&nbsp;":
            body_start = idx + 1
            continue
        # First non-heading, non-blank line is the body
        break

    body_text = "\n".join(lines[body_start:])
    return body_text


def build_chapter_html(filename, chapter_num, title, subtitle):
    """Build HTML section for a single chapter."""
    md_text = (BOOK_DIR / filename).read_text(encoding="utf-8")
    body_text = extract_chapter_body(md_text)
    body_html = parse_markdown_to_html(body_text)

    subtitle_html = f'<p class="chapter-subtitle"><em>{subtitle}</em></p>' if subtitle else ""

    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{chapter_num}</p>
        <h1>{title}</h1>
        {subtitle_html}
      </div>
      <div class="chapter-body">
        {body_html}
      </div>
    </section>
    """


def extract_scripture_refs(md_text, chapter_title):
    """Extract all scripture references from a chapter's markdown text.

    Extracts from two formats:
    1. Blockquote citation lines: "> — Book C:V (NASB)"
    2. Standalone citation lines: "— Book C:V" (at start of line)
    Only matches lines that are purely citation lines, not inline body text.
    Returns list of (reference_string, chapter_title) tuples.
    """
    refs = []
    ref_pattern = r'—\s*((?:\d\s+)?[A-Z][a-z]+(?:\s+[A-Za-z]+)*\s+\d+:\d+(?:[-–]\d+)?)\s*(?:\([A-Z]+\))?'

    for line in md_text.split("\n"):
        stripped = line.strip()

        # Format 1: blockquote citation "> — Book C:V (NASB)"
        if stripped.startswith(">"):
            content = stripped.lstrip(">").strip()
            match = re.match(ref_pattern, content)
            if match:
                ref = match.group(1).strip()
                if ref not in [r[0] for r in refs]:
                    refs.append((ref, chapter_title))
            continue

        # Format 2: standalone citation line "— Book C:V" or "— Book C:V (NASB)"
        # Must be the entire line (just the citation, nothing else substantial)
        if stripped.startswith("—") or stripped.startswith("— "):
            match = re.match(ref_pattern, stripped)
            if match:
                ref = match.group(1).strip()
                # Verify this is a citation-only line (not body text starting with em-dash)
                # Citation lines are short and contain only the reference
                remainder = stripped[match.end():].strip()
                if len(remainder) < 10:  # allow for trailing (NASB) etc
                    if ref not in [r[0] for r in refs]:
                        refs.append((ref, chapter_title))

    return refs


# Bible book ordering for sorting scripture index
BIBLE_BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalm", "Psalms",
    "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians",
    "Ephesians", "Philippians", "Colossians",
    "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]


def bible_sort_key(ref_str):
    """Generate a sort key for a scripture reference."""
    # Extract book name and chapter:verse
    match = re.match(r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(\d+):(\d+)', ref_str)
    if not match:
        return (999, 0, 0)
    book = match.group(1).strip()
    chapter = int(match.group(2))
    verse = int(match.group(3))

    # Normalize "Psalms" to "Psalm"
    if book == "Psalms":
        book = "Psalm"

    try:
        book_idx = BIBLE_BOOK_ORDER.index(book)
    except ValueError:
        book_idx = 999

    return (book_idx, chapter, verse)


def build_scripture_index():
    """Build the scripture index from all chapters."""
    all_refs = []

    for filename, chapter_num, title, subtitle in CHAPTERS:
        md_text = (BOOK_DIR / filename).read_text(encoding="utf-8")
        short_title = title  # Use chapter title
        refs = extract_scripture_refs(md_text, f"{chapter_num}: {title}")
        all_refs.extend(refs)

    # Also check front matter for refs
    for fm_file in ["AUTHORS_DISCLAIMER.md", "LEGAL_DISCLAIMER.md"]:
        path = BOOK_DIR / fm_file
        if path.exists():
            md_text = path.read_text(encoding="utf-8")
            refs = extract_scripture_refs(md_text, "Front Matter")
            all_refs.extend(refs)

    # Group by reference, collecting all chapters where it appears
    ref_chapters = {}
    for ref, chapter in all_refs:
        if ref not in ref_chapters:
            ref_chapters[ref] = []
        if chapter not in ref_chapters[ref]:
            ref_chapters[ref].append(chapter)

    # Sort by biblical order
    sorted_refs = sorted(ref_chapters.keys(), key=bible_sort_key)

    # Build HTML
    entries = []
    current_book = None
    for ref in sorted_refs:
        # Extract book name
        match = re.match(r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)*)', ref)
        book = match.group(1).strip() if match else ref

        if book != current_book:
            current_book = book
            entries.append(f'<h3 class="index-book">{book}</h3>')

        chapters_str = "; ".join(ref_chapters[ref])
        entries.append(
            f'<div class="index-entry">'
            f'<span class="index-ref">{ref}</span>'
            f'<span class="index-chapters">{chapters_str}</span>'
            f'</div>'
        )

    return "\n".join(entries)


def build_toc():
    """Build the table of contents."""
    items = []
    for filename, chapter_num, title, subtitle in CHAPTERS:
        num = chapter_num.replace("Chapter ", "")
        items.append(
            f'<div class="toc-entry">'
            f'<span class="toc-num">Chapter {num}</span>'
            f'<span class="toc-title">{title}</span>'
            f'</div>'
        )
    items.append('<div class="toc-entry toc-backmatter"><span class="toc-title">Scripture Index</span></div>')
    return "\n".join(items)


CSS = r"""
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
    margin-bottom: 0.2in;
    color: #1a1a1a;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 0.8in;
    color: #1a1a1a;
}
.title-page .inspired-by {
    font-size: 10.5pt;
    font-style: italic;
    color: #555;
    margin-top: 0.15in;
}

/* === COPYRIGHT PAGE (verso, page 2, facing dedication recto) === */
.copyright-page {
    page: front-verso;
    page-break-after: always;
    padding-top: 1.5in;
    text-align: center;
    font-size: 9pt;
    line-height: 1.55;
    color: #333;
}
.copyright-page p { margin-bottom: 3pt; }
.copyright-page .book-title {
    font-style: italic;
    font-size: 10pt;
    margin-bottom: 0.2in;
    color: #1a1a1a;
}
.copyright-page .section-gap { margin-top: 0.18in; }
.copyright-page .isbn { font-variant-numeric: tabular-nums; }

/* === DEDICATION PAGE (recto, page 3, facing copyright verso) === */
.dedication-page {
    page: front-recto;
    page-break-after: always;
    padding-top: 1.5in;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #333;
}
.dedication-page h2 {
    font-size: 14pt;
    font-weight: bold;
    margin-bottom: 0.25in;
    text-align: center;
    color: #1a1a1a;
}
.dedication-page p {
    margin-bottom: 8pt;
    text-align: justify;
    text-indent: 0.3in;
}
.dedication-page .dedicatee {
    font-style: italic;
    font-size: 11pt;
    margin-bottom: 0.2in;
    text-align: center;
    text-indent: 0;
}

/* === DISCLAIMER PAGES === */
.disclaimer-page {
    page: front-verso;
    page-break-after: always;
    padding-top: 1.5in;
}
.disclaimer-page h2 {
    font-size: 14pt;
    font-weight: bold;
    margin-bottom: 0.2in;
    text-align: center;
    color: #1a1a1a;
}
.disclaimer-page h3 {
    font-size: 12pt;
    font-weight: bold;
    margin-top: 0.2in;
    margin-bottom: 0.1in;
    color: #1a1a1a;
}
.disclaimer-page p {
    font-size: 10pt;
    line-height: 1.6;
    text-align: justify;
    margin-bottom: 8pt;
    color: #333;
}

.legal-disclaimer {
    page: front-recto;
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
.toc-backmatter {
    margin-top: 0.2in;
    padding-left: 0;
}

/* === CHAPTERS — start on recto pages === */
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

.chapter-subtitle {
    font-size: 10.5pt;
    color: #555;
    margin-top: 2pt;
    font-style: italic;
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
.chapter-body h3 + p,
.chapter-body .divider + p,
.chapter-body .scripture + p,
.chapter-body blockquote + p {
    text-indent: 0;
}

.chapter-body > p:first-child {
    text-indent: 0;
}

/* === SECTION HEADINGS — keep with following text, avoid orphaned subtitles === */
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

/* === DIVIDERS === */
.divider {
    text-align: center;
    margin: 0.2in 0;
    color: #888;
    font-size: 10pt;
    letter-spacing: 0.15em;
    page-break-before: avoid;
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

/* === MISC === */
em { font-style: italic; }
strong { font-weight: bold; }
"""


def build_dedication_html():
    """Build the dedication page from the title_and_dedication.md file."""
    md = (BOOK_DIR / "title_and_dedication.md").read_text(encoding="utf-8")
    # Extract dedication section
    lines = md.strip().split("\n")
    in_dedication = False
    ded_lines = []
    for line in lines:
        if line.strip().startswith("## Dedication"):
            in_dedication = True
            continue
        if in_dedication:
            ded_lines.append(line)

    # Parse dedication text
    ded_text = "\n".join(ded_lines).strip()
    # Split into paragraphs
    paragraphs = re.split(r'\n\n+', ded_text)
    ded_html = ""
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue
        # First paragraph is the dedicatee
        if i == 0:
            # Convert inline markdown
            para = re.sub(r'\*(.+?)\*', r'<em>\1</em>', para)
            ded_html += f'<p class="dedicatee">{para}</p>\n'
        else:
            para = re.sub(r'\*(.+?)\*', r'<em>\1</em>', para)
            ded_html += f"<p>{para}</p>\n"

    return ded_html


def build_authors_disclaimer_html():
    """Parse the author's disclaimer markdown into HTML."""
    md = (BOOK_DIR / "AUTHORS_DISCLAIMER.md").read_text(encoding="utf-8")
    lines = md.strip().split("\n")
    parts = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            continue  # skip main title, we add it ourselves
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            parts.append(f"<h3>{heading}</h3>")
        elif stripped == "" or stripped == "&nbsp;":
            continue
        else:
            # Convert inline markdown
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', stripped)
            parts.append(f"<p>{text}</p>")
    return "\n".join(parts)


def build_legal_disclaimer_html():
    """Parse the legal disclaimer markdown into HTML."""
    md = (BOOK_DIR / "LEGAL_DISCLAIMER.md").read_text(encoding="utf-8")
    lines = md.strip().split("\n")
    parts = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            continue
        if stripped == "" or stripped == "&nbsp;":
            continue
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', stripped)
        parts.append(f"<p>{text}</p>")
    return "\n".join(parts)


def build_full_html(chapter_sections, toc_html, scripture_index_html, dedication_html,
                    authors_disclaimer_html, legal_disclaimer_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <!-- TITLE PAGE (page 1, recto) -->
  <div class="title-page">
    <h1>Change the Mind,<br>Change the Man</h1>
    <p class="inspired-by" style="margin-top: 0.3in; font-style: italic;">\u201cIf you change a person\u2019s mind, you change everything about them.\u201d</p>
    <p class="inspired-by">\u2014 Freddie Anderson</p>
    <p class="author">Paul Hainline</p>
    <p class="inspired-by">Inspired by the teaching of Freddie Anderson</p>
  </div>

  <!-- COPYRIGHT PAGE (page 2, verso) -->
  <div class="copyright-page">
    <p class="book-title">Change the Mind, Change the Man</p>
    <p>Copyright \u00a9 2026 Paul Hainline</p>
    <p>All rights reserved.</p>
    <p class="section-gap">No part of this book may be reproduced or transmitted in any form without written permission from the author, except for brief quotations in critical articles or reviews.</p>
    <p class="section-gap">Scripture quotations are taken from the New American Standard Bible\u00ae (NASB), Copyright \u00a9 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation. Used by permission. All rights reserved. (www.lockman.org)</p>
    <p class="section-gap isbn">ISBN (Paperback): 979-8-9954288-4-8</p>
    <p class="isbn">ISBN (Hardcover): 979-8-9954288-5-5</p>
    <p class="section-gap">NobleMind Press</p>
    <p>noblemind.study</p>
    <p class="section-gap">Printed in the United States of America</p>
  </div>

  <!-- DEDICATION (page 3, recto) -->
  <div class="dedication-page">
    <h2>Dedication</h2>
    {dedication_html}
  </div>

  <!-- AUTHOR'S DISCLAIMER (page 4, verso) -->
  <div class="disclaimer-page">
    <h2>Author\u2019s Disclaimer</h2>
    {authors_disclaimer_html}
  </div>

  <!-- LEGAL DISCLAIMER (page 5, recto) -->
  <div class="disclaimer-page legal-disclaimer">
    <h2>Legal Disclaimer</h2>
    {legal_disclaimer_html}
  </div>

  <!-- TABLE OF CONTENTS (starts recto) -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

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
    print('Generating Lulu interior PDF for "Change the Mind, Change the Man"...')
    print(f'  Page size: 5.5" x 8.5" (Digest)')
    print(f"  Gutter: 0.75in inside, 0.625in outside")
    print()

    print("Building front matter...")
    dedication_html = build_dedication_html()
    authors_disclaimer_html = build_authors_disclaimer_html()
    legal_disclaimer_html = build_legal_disclaimer_html()

    print("Building table of contents...")
    toc_html = build_toc()

    print("Extracting chapter content from Markdown files...")
    chapter_sections = []
    for filename, chapter_num, title, subtitle in CHAPTERS:
        print(f"  {filename}")
        chapter_sections.append(build_chapter_html(filename, chapter_num, title, subtitle))

    print("Building scripture index...")
    scripture_index_html = build_scripture_index()

    print("Assembling HTML...")
    full_html = build_full_html(
        "\n".join(chapter_sections),
        toc_html,
        scripture_index_html,
        dedication_html,
        authors_disclaimer_html,
        legal_disclaimer_html,
    )

    # Save intermediate HTML for debugging
    debug_html = BOOK_DIR / "_lulu_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")

    print("Generating PDF with WeasyPrint (fonts will be embedded)...")
    doc = weasyprint.HTML(string=full_html)
    doc.write_pdf(str(OUTPUT))

    print(f"\nPDF saved to {OUTPUT}")
    print(f"  Chapters: start on recto (right-hand) pages")
    print(f"  Fonts: EB Garamond (embedded)")
    print(f"  Scripture index: included")
    print("Done.")


if __name__ == "__main__":
    main()
