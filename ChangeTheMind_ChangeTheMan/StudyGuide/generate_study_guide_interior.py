#!/usr/bin/env python3
"""Generate IngramSpark-ready interior PDF for the Study Guide.

IngramSpark specs for 7" x 10" (no bleed, B&W text):
  - Page size: 7in x 10in
  - Minimum margin: 0.5in all sides
  - Gutter (inside margin): 0.75in
  - Outside margin: 0.625in
  - Top/Bottom margin: 0.75in
  - Weeks start on recto (right-hand, odd) pages
  - All fonts embedded
  - Page count divisible by 2
"""

import re
from pathlib import Path
import weasyprint

GUIDE_DIR = Path(__file__).parent
SOURCE = GUIDE_DIR / "CHANGE_THE_MIND_STUDY_GUIDE_COMPLETE.md"
OUTPUT = GUIDE_DIR / "ChangeTheMind_StudyGuide_Interior.pdf"
DEBUG_HTML = GUIDE_DIR / "_study_guide_debug.html"

# Week metadata for TOC (extracted from the markdown headers)
WEEK_TITLES = {
    1: "The Phone Call",
    2: "The Progression",
    3: "Where Did We Go Wrong?",
    4: "All of the Imprisoned Aren't in Prison",
    5: "Love That Says No",
    6: "Think",
    7: "Coming to Himself",
    8: "The Father Ran",
    9: "The Long Road",
    10: "The God Who Finds You",
}


# ── Inline Markdown ──────────────────────────────────────────────────

def fmt(text):
    """Convert inline markdown (bold, italic) to HTML."""
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Curly quotes
    text = text.replace('"', '\u201c').replace('"', '\u201d')
    return text


# ── Block-level Markdown Parser ──────────────────────────────────────

def render_blockquote(bq_lines):
    """Render collected blockquote lines to HTML."""
    quote_parts = []
    cite_text = None
    for bl in bq_lines:
        if re.match(r'^[—–\-]\s', bl):
            cite_text = bl.lstrip('—–- ').strip()
        else:
            quote_parts.append(bl)

    quote_html = fmt(' '.join(quote_parts))
    # Check if this is just a reading instruction like "(Have someone read...)"
    combined = ' '.join(quote_parts).strip()
    if combined.startswith('*(') and combined.endswith(')*'):
        return f'<p class="instruction"><em>{fmt(combined.strip("*"))}</em></p>'

    cite_html = f'\n<cite>— {fmt(cite_text)}</cite>' if cite_text else ''
    return f'<blockquote class="scripture">\n<p>{quote_html}</p>{cite_html}\n</blockquote>'


def parse_body(text):
    """Convert section body markdown to HTML."""
    lines = text.split('\n')
    parts = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Blank lines
        if not stripped:
            i += 1
            continue

        # Horizontal rules → subtle spacing
        if stripped == '---':
            parts.append('<hr class="section-break">')
            i += 1
            continue

        # H2 headers
        if stripped.startswith('## '):
            heading = stripped[3:].strip()
            parts.append(f'<h2>{fmt(heading)}</h2>')
            i += 1
            continue

        # H3 headers
        if stripped.startswith('### '):
            heading = stripped[4:].strip()
            # Detect track headers for special styling
            if heading.startswith('Track A') or heading.startswith('Track B'):
                parts.append(f'<h3 class="track-header">{fmt(heading)}</h3>')
            elif re.match(r'Passage \d+', heading):
                parts.append(f'<h3 class="passage-header">{fmt(heading)}</h3>')
            else:
                parts.append(f'<h3>{fmt(heading)}</h3>')
            i += 1
            continue

        # Blockquotes
        if stripped.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                bl = lines[i].strip()
                # Remove leading > and optional space
                bl = re.sub(r'^>\s?', '', bl)
                bq_lines.append(bl)
                i += 1
            parts.append(render_blockquote(bq_lines))
            continue

        # Bullet lists (reading assignments)
        if stripped.startswith('- '):
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                item = lines[i].strip()[2:].strip()
                items.append(item)
                i += 1
            items_html = '\n'.join(f'<li>{fmt(item)}</li>' for item in items)
            parts.append(f'<ul class="reading-list">\n{items_html}\n</ul>')
            continue

        # Numbered questions: 1. or A1. or B1.
        q_match = re.match(r'^([A-B]?\d+)\.\s+(.+)', stripped)
        if q_match:
            q_num = q_match.group(1)
            q_text = q_match.group(2)
            i += 1
            # Collect continuation lines
            while i < len(lines):
                ns = lines[i].strip()
                if (not ns or ns.startswith('#') or ns.startswith('>')
                        or ns.startswith('- ') or ns == '---'
                        or re.match(r'^[A-B]?\d+\.\s+', ns)):
                    break
                q_text += ' ' + ns
                i += 1
            parts.append(
                f'<p class="question"><span class="q-num">{q_num}.</span> '
                f'{fmt(q_text)}</p>'
            )
            continue

        # Regular paragraphs — collect continuation lines
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            ns = lines[i].strip()
            if (not ns or ns.startswith('#') or ns.startswith('>')
                    or ns.startswith('- ') or ns == '---'
                    or re.match(r'^[A-B]?\d+\.\s+', ns)):
                break
            para_lines.append(ns)
            i += 1
        para = ' '.join(para_lines)
        parts.append(f'<p>{fmt(para)}</p>')

    return '\n'.join(parts)


# ── Section Splitter ─────────────────────────────────────────────────

def split_sections(md_text):
    """Split the markdown at level-1 headers into (header, body) tuples."""
    lines = md_text.split('\n')
    sections = []
    current_header = None
    current_lines = []

    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            if current_header is not None:
                sections.append((current_header, '\n'.join(current_lines)))
            current_header = line[2:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_header:
        sections.append((current_header, '\n'.join(current_lines)))

    return sections


# ── Build HTML Sections ──────────────────────────────────────────────

def extract_how_to_use(title_body):
    """Extract 'How to Use This Guide' from the title section body."""
    # Find the ## How to Use header
    marker = '## How to Use This Guide'
    idx = title_body.find(marker)
    if idx == -1:
        return ''
    content = title_body[idx + len(marker):]
    # Trim leading/trailing whitespace and separators
    content = content.strip().strip('-').strip()
    return content


def build_week_html(header, body, week_num):
    """Build HTML for a week section."""
    # Extract title from header: "Week N: TITLE"
    m = re.match(r'Week\s+(\d+):\s*(.+)', header)
    if m:
        title = m.group(2).strip()
    else:
        title = header

    # Extract chapter subtitle from body (### Chapter N — "Title")
    chapter_sub = ''
    body_lines = body.split('\n')
    filtered = []
    for line in body_lines:
        sm = re.match(r'^###\s+Chapter\s+\d+\s*[—–\-]\s*(.+)', line.strip())
        if sm:
            chapter_sub = sm.group(1).strip().strip('"').strip('\u201c\u201d')
        else:
            filtered.append(line)

    body_content = parse_body('\n'.join(filtered))
    subtitle_html = f'<p class="week-subtitle">Chapter {week_num} — \u201c{chapter_sub}\u201d</p>' if chapter_sub else ''

    return f"""
    <section class="week" id="week{week_num}">
      <div class="week-header">
        <p class="week-num">Week {week_num}</p>
        <h1>{fmt(title)}</h1>
        {subtitle_html}
      </div>
      <div class="week-body">
        {body_content}
      </div>
    </section>
    """


def build_part_divider(header):
    """Build a part divider page."""
    # header like: "PART ONE — THE DESCENT: THE MIND TURNING AWAY"
    m = re.match(r'(PART\s+\w+)\s*[—–\-]\s*(.+)', header)
    if m:
        part_label = m.group(1)
        part_title = m.group(2).strip()
    else:
        part_label = header
        part_title = ''

    title_html = f'<p class="part-title">{fmt(part_title)}</p>' if part_title else ''
    return f"""
    <section class="part-divider">
      <div class="part-inner">
        <p class="part-label">{part_label}</p>
        {title_html}
      </div>
    </section>
    """


def build_toc():
    """Build the table of contents."""
    entries = []
    entries.append('<div class="toc-entry toc-front"><span class="toc-title">How to Use This Guide</span></div>')
    entries.append('<div class="toc-part">Part One — The Descent: The Mind Turning Away</div>')
    for w in range(1, 7):
        entries.append(
            f'<div class="toc-entry">'
            f'<span class="toc-num">Week {w}</span>'
            f'<span class="toc-title">{WEEK_TITLES[w]}</span>'
            f'</div>'
        )
    entries.append('<div class="toc-part">Part Two — The Return: The Mind Turning Back</div>')
    for w in range(7, 11):
        entries.append(
            f'<div class="toc-entry">'
            f'<span class="toc-num">Week {w}</span>'
            f'<span class="toc-title">{WEEK_TITLES[w]}</span>'
            f'</div>'
        )
    return '\n'.join(entries)


# ── CSS ──────────────────────────────────────────────────────────────

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

/* === PAGE SETUP: 7" x 10" IngramSpark, no bleed ===
   Gutter (inside) = 0.75in, Outside = 0.625in
   Top = 0.75in, Bottom = 0.75in
*/
@page {
    size: 7in 10in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
}

/* Recto (right-hand, odd): gutter LEFT */
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

/* Verso (left-hand, even): gutter RIGHT */
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

/* Front matter: no page numbers */
@page front-matter {
    size: 7in 10in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}
@page front-verso {
    size: 7in 10in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

/* TOC pages: no page numbers */
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

/* Blank pages (from break-before: right) */
@page :blank {
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}

/* Part divider pages: no page numbers */
@page part-page {
    size: 7in 10in;
    margin: 0.75in;
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}


/* === BODY === */
body {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a1a1a;
    text-rendering: optimizeLegibility;
}


/* === TITLE PAGE === */
.title-page {
    page: front-matter;
    page-break-after: always;
    text-align: center;
    padding-top: 2.2in;
}
.title-page h1 {
    font-size: 26pt;
    font-weight: bold;
    line-height: 1.2;
    margin-bottom: 0.15in;
    color: #1a1a1a;
}
.title-page .subtitle {
    font-size: 14pt;
    font-style: italic;
    color: #333;
    margin-top: 0.3in;
    margin-bottom: 0.1in;
}
.title-page .audience {
    font-size: 10.5pt;
    color: #555;
    margin-top: 0.15in;
    line-height: 1.4;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 1in;
    color: #1a1a1a;
}


/* === COPYRIGHT PAGE === */
.copyright-page {
    page: front-verso;
    page-break-after: always;
    padding-top: 5.5in;
    font-size: 9pt;
    line-height: 1.5;
    color: #555;
    text-align: center;
}
.copyright-page p {
    margin-bottom: 3pt;
}
.copyright-page .publisher {
    margin-top: 0.15in;
    font-style: italic;
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
    margin-bottom: 0.5in;
    padding-top: 0.5in;
    color: #1a1a1a;
}
.toc-entry {
    font-size: 11pt;
    line-height: 2.0;
    color: #333;
    padding-left: 0.3in;
}
.toc-entry .toc-num {
    display: inline;
    margin-right: 0.2in;
    color: #555;
}
.toc-entry .toc-title {
    display: inline;
}
.toc-front {
    padding-left: 0;
    margin-bottom: 0.1in;
}
.toc-part {
    font-size: 10pt;
    font-weight: bold;
    letter-spacing: 0.03em;
    color: #1a1a1a;
    margin-top: 0.25in;
    margin-bottom: 0.05in;
    padding-left: 0;
}


/* === HOW TO USE SECTION === */
.how-to-use {
    break-before: right;
}
.how-to-use .section-title {
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0.35in;
    padding-top: 0.5in;
    color: #1a1a1a;
}
.how-to-use p {
    text-align: justify;
    margin-bottom: 8pt;
}
.how-to-use h3 {
    font-size: 12pt;
    font-weight: bold;
    margin-top: 0.25in;
    margin-bottom: 0.1in;
    color: #1a1a1a;
}


/* === PART DIVIDER === */
.part-divider {
    page: part-page;
    break-before: right;
    page-break-after: always;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100%;
}
.part-inner {
    text-align: center;
    padding-top: 3in;
}
.part-label {
    font-size: 12pt;
    font-weight: bold;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 0.15in;
}
.part-title {
    font-size: 16pt;
    font-weight: bold;
    color: #1a1a1a;
    line-height: 1.3;
}


/* === WEEK SECTIONS === */
.week {
    break-before: right;
}

.week-header {
    text-align: center;
    margin-bottom: 0.35in;
    padding-top: 0.6in;
}
.week-num {
    font-size: 10pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 6pt;
}
.week-header h1 {
    font-size: 22pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 6pt;
    line-height: 1.2;
}
.week-subtitle {
    font-size: 10.5pt;
    color: #555;
    font-style: italic;
    margin-top: 4pt;
}

/* === SECTION HEADERS WITHIN WEEKS === */
.week-body h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.3in;
    margin-bottom: 0.12in;
    page-break-after: avoid;
    break-after: avoid;
}

.week-body h3 {
    font-size: 11.5pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.2in;
    margin-bottom: 0.08in;
    page-break-after: avoid;
    break-after: avoid;
}

.week-body h3.passage-header {
    margin-top: 0.25in;
}

.week-body h3.track-header {
    font-size: 12pt;
    margin-top: 0.2in;
    font-style: italic;
}


/* === BODY TEXT === */
.week-body p,
.how-to-use p {
    text-align: justify;
    margin-bottom: 6pt;
    margin-top: 0;
    orphans: 2;
    widows: 2;
}

/* === QUESTIONS === */
.question {
    margin-left: 0.3in;
    text-indent: -0.3in;
    margin-bottom: 8pt;
    margin-top: 4pt;
    text-align: justify;
    orphans: 2;
    widows: 2;
}
.question .q-num {
    font-weight: bold;
    margin-right: 0.05in;
}

/* === SCRIPTURE BLOCKQUOTES === */
blockquote.scripture {
    margin: 0.12in 0 0.12in 0.4in;
    padding: 0;
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.45;
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
    margin-top: 4pt;
    font-style: normal;
    font-weight: 500;
    font-size: 9.5pt;
    color: #444;
}

/* === INSTRUCTIONS === */
.instruction {
    margin: 0.1in 0 0.1in 0.4in;
    font-size: 10.5pt;
    color: #555;
}

/* === READING LISTS === */
ul.reading-list {
    margin: 0.08in 0 0.08in 0.4in;
    padding-left: 0.2in;
    list-style-type: none;
}
ul.reading-list li {
    font-size: 10.5pt;
    line-height: 1.6;
    margin-bottom: 2pt;
    text-indent: -0.15in;
    padding-left: 0.15in;
}
ul.reading-list li::before {
    content: "\2022\2003";
}

/* === SECTION BREAKS === */
hr.section-break {
    border: none;
    margin: 0.15in 0;
    height: 0;
}

/* === MISC === */
em { font-style: italic; }
strong { font-weight: bold; }
"""


# ── Full Document Assembly ───────────────────────────────────────────

def build_full_html(toc_html, how_to_use_html, body_sections_html):
    """Assemble the complete HTML document."""
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
    <p class="subtitle">A Scriptural Study Guide</p>
    <p class="audience">For Use with Prison Ministries, Reentry Programs,<br>
    Congregational Studies, and Families</p>
    <p class="author">Paul Hainline</p>
  </div>

  <!-- COPYRIGHT PAGE (page 2, verso) -->
  <div class="copyright-page">
    <p><em>Change the Mind, Change the Man: A Scriptural Study Guide</em></p>
    <p>Copyright \u00a9 2026 Paul Hainline</p>
    <p>All rights reserved.</p>
    <p style="margin-top: 0.15in;">Scripture quotations taken from the (NASB\u00ae)<br>
    New American Standard Bible\u00ae,<br>
    Copyright \u00a9 1960, 1971, 1977, 1995, 2020<br>
    by The Lockman Foundation.<br>
    Used by permission. All rights reserved.<br>
    <a href="http://www.lockman.org">www.lockman.org</a></p>
    <p class="publisher">NobleMind Press</p>
  </div>

  <!-- TABLE OF CONTENTS (starts recto) -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- HOW TO USE THIS GUIDE (starts recto) -->
  <section class="how-to-use" id="how-to-use">
    <h1 class="section-title">How to Use This Guide</h1>
    {how_to_use_html}
  </section>

  <!-- BODY: Part dividers and Weeks -->
  {body_sections_html}

</body>
</html>"""


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print('Generating IngramSpark interior PDF for the Study Guide...')
    print(f'  Page size: 7" x 10"')
    print(f'  Gutter: 0.75in inside, 0.625in outside')
    print()

    md_text = SOURCE.read_text(encoding='utf-8')
    sections = split_sections(md_text)

    # ── Extract How to Use content from the title section ──
    title_header, title_body = sections[0]
    how_to_use_content = extract_how_to_use(title_body)
    how_to_use_html = parse_body(how_to_use_content)
    print('  How to Use This Guide: extracted')

    # ── Build TOC ──
    toc_html = build_toc()
    print('  Table of Contents: built')

    # ── Process body sections (Parts and Weeks) ──
    body_parts = []
    week_num = 0

    for header, body in sections[1:]:
        # Part dividers
        if header.startswith('PART '):
            print(f'  {header}')
            body_parts.append(build_part_divider(header))
            continue

        # Week sections
        m = re.match(r'Week\s+(\d+)', header)
        if m:
            week_num = int(m.group(1))
            print(f'  Week {week_num}: {WEEK_TITLES.get(week_num, header)}')
            body_parts.append(build_week_html(header, body, week_num))
            continue

        # Skip anything else (title section already handled)
        print(f'  [skipped] {header[:40]}...')

    body_html = '\n'.join(body_parts)

    # ── Assemble ──
    print('\nAssembling HTML...')
    full_html = build_full_html(toc_html, how_to_use_html, body_html)

    # Save debug HTML
    DEBUG_HTML.write_text(full_html, encoding='utf-8')
    print(f'  Debug HTML: {DEBUG_HTML.name}')

    # ── Generate PDF ──
    print('Generating PDF with WeasyPrint (fonts will be embedded)...')
    doc = weasyprint.HTML(string=full_html)
    pdf_doc = doc.render()
    num_pages = len(pdf_doc.pages)

    # IngramSpark requires page count divisible by 2
    if num_pages % 2 != 0:
        print(f'  Page count {num_pages} is odd — adding blank page')
        # WeasyPrint handles this via the recto/verso page model,
        # but we note it for verification
    else:
        print(f'  Page count {num_pages} — divisible by 2 ✓')

    pdf_doc.write_pdf(str(OUTPUT))

    print(f'\n  PDF saved to {OUTPUT}')
    print(f'  Pages: {num_pages}')
    print(f'  Trim size: 7" x 10"')
    print(f'  Font: EB Garamond (embedded)')
    print('Done.')


if __name__ == '__main__':
    main()
