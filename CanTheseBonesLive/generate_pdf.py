#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'Can These Bones Live?'.

Distinct from the Lulu print interior (generate_lulu_interior.py). This
version is single-sided, reader-friendly: cover image on page 1, title,
copyright, epigraph, TOC, 11 chapters, 2 appendices, centered page numbers.

The Scripture Index is intentionally omitted from the reader PDF (still
in the print interior).

Output: CanTheseBonesLive.pdf  (5.5" x 8.5", EB Garamond)
"""

import re
from html import unescape as html_unescape
from pathlib import Path
import markdown
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "CanTheseBonesLive.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER = BOOK_DIR / "cover_front.jpg"

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


# ---------------------------------------------------------------------------
# Scripture paragraph detection — lifted from the Lulu interior generator
# so the reader PDF renders the same styled blockquotes.
# ---------------------------------------------------------------------------
BIBLE_BOOKS = [
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
_BOOK_ALT = "|".join(re.escape(b) for b in sorted(BIBLE_BOOKS, key=len, reverse=True))

SCRIPTURE_PARA_RE = re.compile(
    r'^\s*["\u201c\u201d](.+)["\u201c\u201d]\s+'
    r'\(((?:' + _BOOK_ALT + r')\s+\d+(?::\d+(?:\s*[\u2013\u2014-]\s*\d+)?)?)\)'
    r'\.?\s*$'
)
CITE_IN_BLOCKQUOTE_RE = re.compile(
    r'(<blockquote>\s*<p>)(.*?)\s*\(((?:' + _BOOK_ALT
    + r')\s+\d+(?::\d+(?:\s*[\u2013\u2014-]\s*\d+)?)?)\)\.?\s*</p>\s*</blockquote>',
    re.DOTALL,
)


def promote_scripture_paragraphs(md_text):
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
        r'<blockquote class="scripture"><p>\2</p><cite>— \3</cite></blockquote>',
        html,
    )


def md_body(path):
    """Markdown → HTML. Strips chapter title (first H1 + first H2) and
    promotes standalone Scripture paragraphs into styled blockquotes."""
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    text = re.sub(r'^##\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    text = promote_scripture_paragraphs(text)
    html = markdown.markdown(text, extensions=['smarty', 'tables'])
    html = lift_citation_to_cite(html)
    return html


def build_chapter(filename, label, title):
    body = md_body(BOOK_DIR / filename)
    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{label}</p>
        <h1>{title}</h1>
      </div>
      <div class="chapter-body">
        {body}
      </div>
    </section>
    """


def build_appendix(filename, label, title):
    body = md_body(BOOK_DIR / filename)
    return f"""
    <section class="chapter appendix">
      <div class="chapter-header">
        <p class="chapter-num">{label}</p>
        <h1>{title}</h1>
      </div>
      <div class="chapter-body">
        {body}
      </div>
    </section>
    """


def build_toc():
    items = []
    for _, label, title in CHAPTERS:
        items.append(
            f'<div class="toc-entry toc-chapter">'
            f'<span>{label}: {title}</span></div>'
        )
    items.append('<div class="toc-appendix-header">Appendices</div>')
    for _, label, title in APPENDICES:
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
@page title-page     {{ @bottom-center {{ content: none; }} }}
@page copyright-page {{ @bottom-center {{ content: none; }} }}
@page epigraph-page  {{ @bottom-center {{ content: none; }} }}
@page toc-page       {{ @bottom-center {{ content: none; }} }}

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
    font-size: 26pt; font-weight: normal; letter-spacing: 1pt;
    line-height: 1.2; margin-bottom: 0.25in; color: #1a1a1a;
}}
.title-page .subtitle {{
    font-size: 13pt; font-style: italic; color: #4a4a4a;
    margin-bottom: 1.4in; line-height: 1.45;
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

/* EPIGRAPH */
.epigraph-page {{
    page: epigraph-page; page-break-after: always;
    text-align: center; padding-top: 3.0in;
}}
.epigraph-page blockquote {{
    margin: 0 0.5in; border: none; padding: 0;
    font-style: italic; font-size: 13pt; line-height: 1.5;
    color: #1a1a1a;
}}
.epigraph-page p {{ margin: 0 0 0.2in 0; text-indent: 0; }}
.epigraph-page cite {{
    display: block; font-style: normal; font-size: 11pt;
    color: #555; letter-spacing: 0.03em;
}}

/* TOC */
.toc-section {{ page: toc-page; page-break-after: always; padding-top: 0.2in; }}
.toc-section h1 {{
    font-size: 18pt; font-weight: normal; letter-spacing: 1pt;
    text-align: center; margin-bottom: 0.4in; color: #1a1a1a;
}}
.toc-entry {{ font-size: 11pt; line-height: 1.85; color: #2a2a2a; text-align: left; }}
.toc-chapter {{ padding-left: 0.2in; }}
.toc-appendix-header {{
    margin-top: 16pt; margin-bottom: 4pt;
    font-size: 11.5pt; color: #1a1a1a; font-weight: 600;
    letter-spacing: 0.04em;
}}

/* CHAPTER */
.chapter {{ page-break-before: always; }}
.chapter-header {{
    text-align: center; margin-top: 0.4in; margin-bottom: 0.32in;
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

.chapter-body em     {{ font-style: italic; }}
.chapter-body strong {{ font-weight: 600; }}

.chapter-body hr {{ border: none; text-align: center; margin: 0.22in 0; }}
.chapter-body hr::before {{
    content: "\u2022   \u2022   \u2022";
    color: #aaa; letter-spacing: 0.1em; font-size: 10pt;
}}

/* SCRIPTURE */
blockquote.scripture {{
    margin: 0.14in 0 0.14in 0.35in;
    padding-left: 0.22in;
    border-left: 2pt solid #8B6914;
    font-style: italic;
    font-size: 10.8pt;
    line-height: 1.5;
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

/* Tables (appendix B) */
.chapter-body table {{
    border-collapse: collapse; margin: 0.18in 0; width: 100%;
    font-size: 10pt; page-break-inside: avoid;
}}
.chapter-body th, .chapter-body td {{
    border: 1px solid #bbb; padding: 5pt 7pt; vertical-align: top;
    text-align: left;
}}
.chapter-body th {{ background: #f0ece0; font-weight: 600; }}
"""


def build_full_html(chapter_sections, appendix_sections, toc_html):
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
    <h1>{TITLE}</h1>
    <p class="subtitle">{SUBTITLE}</p>
    <p class="author">{AUTHOR}</p>
    <p class="imprint">NOBLEMIND PRESS</p>
  </div>

  <div class="copyright-page">
    <p><strong>{TITLE}: {SUBTITLE}</strong></p>
    <p>Copyright &copy; 2026 {AUTHOR}. All rights reserved.</p>
    <p>Published by NobleMind Press &bull; noblemind.study</p>
    <p style="margin-top:16pt;">All Scripture quotations are from the<br>
    New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p style="margin-top:16pt;">This book may be freely shared and distributed for<br>
    the purpose of teaching and study.</p>
    <p style="margin-top:16pt;">First Edition</p>
  </div>

  <div class="epigraph-page">
    <blockquote>
      <p>\u201cSon of man, can these bones live?\u201d</p>
      <cite>\u2014 Ezekiel 37:3</cite>
    </blockquote>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {chapter_sections}
  {appendix_sections}
</body>
</html>"""


def main():
    print("Building chapters...")
    chapter_html = []
    for fname, label, title in CHAPTERS:
        print(f"  {fname}")
        chapter_html.append(build_chapter(fname, label, title))

    print("Building appendices...")
    appendix_html = []
    for fname, label, title in APPENDICES:
        print(f"  {fname}")
        appendix_html.append(build_appendix(fname, label, title))

    toc_html = build_toc()
    html = build_full_html("\n".join(chapter_html), "\n".join(appendix_html), toc_html)

    debug = BOOK_DIR / "_pdf_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
