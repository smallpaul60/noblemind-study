#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'From the Beginning'.

Distinct from the Lulu print interior (see generate_lulu_interior.py).
Single-sided, reader-friendly, with cover image on page 1, part dividers,
scripture blockquotes, and centered page numbers.

Output: FromTheBeginning.pdf  (5.5" x 8.5", EB Garamond)
"""

import re
from html import unescape as html_unescape
from pathlib import Path
import markdown
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "FromTheBeginning.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER = BOOK_DIR / "cover_front.jpg"

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
    0: ("Part One",   "The Foundation",    "Who is God, and why do you matter?"),
    4: ("Part Two",   "The Turning Point", "Who is Jesus, and what did He do?"),
    7: ("Part Three", "The Response",      "What does God ask you to do?"),
}


def convert_scripture_blockquotes(html):
    """Lift plain <blockquote>"...text..." — Reference</blockquote> into
    <blockquote class="scripture"><p>"text"</p><cite>— Reference</cite></blockquote>."""

    def convert(match):
        inner = match.group(1).strip()
        inner = re.sub(r'^<p>(.*)</p>$', r'\1', inner, flags=re.DOTALL).strip()

        parts = re.split(r'\s*[\u2014\u2013]\s*(?=<strong>)', inner, maxsplit=1)
        if len(parts) != 2:
            return match.group(0)

        quote_text = parts[0].strip()
        cite_text = parts[1].strip()
        quote_text = re.sub(r'^<em>(.*)</em>$', r'\1', quote_text, flags=re.DOTALL)
        # smarty emits &ldquo;/&rdquo; HTML entities — resolve them before stripping
        quote_text = html_unescape(quote_text).strip().strip('\u201c\u201d"\'')
        cite_text = re.sub(r'</?strong>', '', cite_text)
        cite_text = re.sub(r',?\s*NASB\s*$', '', cite_text).strip()

        return (
            '<blockquote class="scripture">'
            f'<p>\u201c{quote_text}\u201d</p>'
            f'<cite>\u2014 {cite_text}</cite>'
            '</blockquote>'
        )

    return re.sub(r'<blockquote>\s*(.*?)\s*</blockquote>', convert, html, flags=re.DOTALL)


def md_body(path):
    """Markdown file → HTML, stripping only the first H1 (chapter title).
    H2s are preserved as in-chapter section headings."""
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    html = markdown.markdown(text, extensions=['smarty'])
    return convert_scripture_blockquotes(html)


def build_dedication():
    html = md_body(BOOK_DIR / "FromTheBeginning_Dedication.md")
    return f"""
    <section class="chapter frontmatter-chapter">
      <div class="chapter-header">
        <h1>To the Seeker</h1>
      </div>
      <div class="chapter-body dedication-body">
        {html}
      </div>
    </section>
    """


def build_part_page(label, title, subtitle):
    return f"""
    <section class="part-page">
      <p class="part-num">{label}</p>
      <h1 class="part-title">{title}</h1>
      <p class="part-subtitle"><em>{subtitle}</em></p>
    </section>
    """


def build_chapter(filename, label, title):
    html = md_body(BOOK_DIR / filename)
    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{label}</p>
        <h1>{title}</h1>
      </div>
      <div class="chapter-body">
        {html}
      </div>
    </section>
    """


def build_toc():
    items = ['<div class="toc-entry"><span>To the Seeker</span></div>']
    for idx, (fname, label, title) in enumerate(CHAPTERS):
        if idx in PART_STRUCTURE:
            part_label, part_title, _ = PART_STRUCTURE[idx]
            items.append(
                f'<div class="toc-part"><strong>{part_label}: {part_title}</strong></div>'
            )
        items.append(
            f'<div class="toc-entry toc-chapter">'
            f'<span>{label}: {title}</span></div>'
        )
    return "\n".join(items)


CSS = f"""
@font-face {{
    font-family: 'EB Garamond';
    src: url('file://{FONT_DIR / "EBGaramond.ttf"}');
    font-weight: normal; font-style: normal;
}}
@font-face {{
    font-family: 'EB Garamond';
    src: url('file://{FONT_DIR / "EBGaramond-Italic.ttf"}');
    font-weight: normal; font-style: italic;
}}

@page {{
    size: 5.5in 8.5in;
    margin: 0.85in 0.75in 0.9in 0.75in;
    @bottom-center {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #555;
    }}
}}
@page cover-page    {{ size: 5.5in 8.5in; margin: 0; @bottom-center {{ content: none; }} }}
@page title-page    {{ @bottom-center {{ content: none; }} }}
@page copyright-page {{ @bottom-center {{ content: none; }} }}
@page toc-page      {{ @bottom-center {{ content: none; }} }}
@page part-div-page {{ @bottom-center {{ content: none; }} }}

body {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11.5pt;
    line-height: 1.58;
    color: #1a1a1a;
}}

/* COVER */
.cover-page {{ page: cover-page; page-break-after: always; margin: 0; padding: 0; }}
.cover-page img {{ width: 5.5in; height: 8.5in; display: block; }}

/* TITLE */
.title-page {{
    page: title-page; page-break-after: always;
    text-align: center; padding-top: 2.0in;
}}
.title-page h1 {{
    font-size: 28pt; font-weight: normal; letter-spacing: 1pt;
    line-height: 1.2; margin-bottom: 0.25in; color: #1a1a1a;
}}
.title-page .subtitle {{
    font-size: 13pt; font-style: italic; color: #4a4a4a;
    margin-bottom: 1.4in;
}}
.title-page .author  {{ font-size: 13pt; color: #1a1a1a; }}
.title-page .imprint {{ font-size: 10pt; color: #777; margin-top: 0.45in; letter-spacing: 1pt; }}

/* COPYRIGHT */
.copyright-page {{
    page: copyright-page; page-break-after: always;
    text-align: center; padding-top: 1.8in;
    font-size: 10pt; line-height: 1.65; color: #444;
}}
.copyright-page p {{ margin-bottom: 9pt; }}

/* TOC */
.toc-section {{ page: toc-page; page-break-after: always; padding-top: 0.2in; }}
.toc-section h1 {{
    font-size: 18pt; font-weight: normal; letter-spacing: 1pt;
    text-align: center; margin-bottom: 0.4in; color: #1a1a1a;
}}
.toc-part {{
    margin-top: 14pt; margin-bottom: 4pt;
    font-size: 11.5pt; color: #1a1a1a;
}}
.toc-entry {{ font-size: 11pt; line-height: 1.85; color: #2a2a2a; text-align: left; }}
.toc-chapter {{ padding-left: 0.2in; }}

/* PART DIVIDER */
.part-page {{
    page: part-div-page; page-break-before: always; page-break-after: always;
    text-align: center; padding-top: 3.3in;
}}
.part-page .part-num {{
    font-size: 11pt; letter-spacing: 0.2em; color: #8B6914;
    text-transform: uppercase; margin-bottom: 14pt;
}}
.part-page .part-title {{
    font-size: 26pt; font-weight: normal; line-height: 1.15;
    color: #1a1a1a; margin-bottom: 16pt;
}}
.part-page .part-subtitle {{ font-size: 12pt; color: #555; }}

/* CHAPTER */
.chapter {{ page-break-before: always; }}
.chapter-header {{
    text-align: center; margin-top: 0.4in; margin-bottom: 0.32in;
    padding-bottom: 0.1in;
}}
.chapter-header .chapter-num {{
    font-size: 10pt; letter-spacing: 0.18em; color: #8B6914;
    margin-bottom: 6pt; text-transform: uppercase;
}}
.chapter-header h1 {{
    font-size: 20pt; font-weight: normal; line-height: 1.25; color: #1a1a1a;
}}

.chapter-body p {{
    text-align: justify; text-indent: 0.28in;
    margin: 0; orphans: 2; widows: 2; hyphens: auto;
}}
.chapter-body > p:first-child {{ text-indent: 0; }}
.chapter-body h2 + p,
.chapter-body h3 + p,
.chapter-body blockquote + p,
.chapter-body hr + p {{ text-indent: 0; }}

.chapter-body h2 {{
    font-size: 13pt; font-weight: 600;
    margin-top: 0.28in; margin-bottom: 0.12in;
    page-break-after: avoid; color: #1a1a1a;
}}
.chapter-body h3 {{
    font-size: 11.5pt; font-weight: 600; font-style: italic;
    margin-top: 0.22in; margin-bottom: 0.1in;
    page-break-after: avoid; color: #333;
}}

.chapter-body em {{ font-style: italic; }}
.chapter-body strong {{ font-weight: 600; }}

.chapter-body hr {{
    border: none; text-align: center; margin: 0.22in 0;
}}
.chapter-body hr::before {{
    content: "\u2022   \u2022   \u2022";
    color: #aaa; letter-spacing: 0.1em; font-size: 10pt;
}}

/* SCRIPTURE */
blockquote.scripture {{
    margin: 0.14in 0 0.14in 0.35in;
    padding: 0;
    font-style: italic;
    font-size: 10.8pt;
    line-height: 1.5;
    border-left: 2pt solid #8B6914;
    padding-left: 0.22in;
    page-break-inside: avoid;
}}
blockquote.scripture p {{
    text-indent: 0 !important; text-align: left; margin-bottom: 0;
}}
blockquote.scripture cite {{
    display: block; margin-top: 3pt;
    font-style: normal; font-size: 9.5pt; color: #4a4a4a;
    letter-spacing: 0.02em;
}}

/* DEDICATION */
.dedication-body p {{ text-align: left; text-indent: 0; margin-bottom: 10pt; }}
"""


def build_full_html(chapter_sections, toc_html):
    cover_tag = (
        f'<div class="cover-page"><img src="file://{COVER}" alt="cover"></div>'
        if COVER.exists() else ''
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>
  {cover_tag}

  <div class="title-page">
    <h1>From the Beginning</h1>
    <p class="subtitle">The Gospel from the Ground Up</p>
    <p class="author">Paul &amp; Pam Hainline</p>
    <p class="imprint">NOBLEMIND PRESS</p>
  </div>

  <div class="copyright-page">
    <p><strong>From the Beginning: The Gospel from the Ground Up</strong></p>
    <p>Copyright &copy; 2026 Paul &amp; Pam Hainline. All rights reserved.</p>
    <p>Published by NobleMind Press &bull; noblemind.study</p>
    <p style="margin-top:16pt;">All Scripture quotations are from the<br>
    New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p style="margin-top:16pt;">This book may be freely shared and distributed for<br>
    the purpose of teaching and study.</p>
    <p style="margin-top:16pt;">First Edition</p>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {chapter_sections}
</body>
</html>"""


def main():
    print("Building dedication...")
    sections = [build_dedication()]
    for idx, (fname, label, title) in enumerate(CHAPTERS):
        if idx in PART_STRUCTURE:
            part_label, part_title, part_subtitle = PART_STRUCTURE[idx]
            print(f"  -- {part_label}: {part_title}")
            sections.append(build_part_page(part_label, part_title, part_subtitle))
        print(f"  {fname}")
        sections.append(build_chapter(fname, label, title))

    toc_html = build_toc()
    html = build_full_html("\n".join(sections), toc_html)

    debug = BOOK_DIR / "_pdf_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
