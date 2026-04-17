#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'Before I Formed You'.

Distinct from the Lulu print interior (see generate_lulu_interior.py).
This is a single-sided, reader-friendly PDF with a cover image on page 1
and centered page numbers — meant for download from noblemind.study.

Output: BeforeIFormedYou.pdf  (5.5" x 8.5", EB Garamond)
"""

import re
from pathlib import Path
import markdown
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BeforeIFormedYou.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER = BOOK_DIR / "cover_front.jpg"

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


def md_body(path):
    """Convert a markdown file to HTML, stripping its H1 and H2 headings
    (we supply our own chapter headers)."""
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    text = re.sub(r'^##\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    return markdown.markdown(text, extensions=['smarty'])


def build_preface():
    html = md_body(BOOK_DIR / "preface-before-i-formed-you.md")
    return f"""
    <section class="chapter frontmatter-chapter">
      <div class="chapter-header">
        <h1>Preface</h1>
      </div>
      <div class="chapter-body preface-body">
        {html}
      </div>
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


def build_closing():
    """The closing keeps its internal H2 'You Are Not Alone' as the title."""
    raw = (BOOK_DIR / "closing-before-i-formed-you.md").read_text(encoding='utf-8')
    raw = re.sub(r'^#\s+.*$', '', raw, count=1, flags=re.MULTILINE).strip()
    raw = re.sub(r'^##\s+(.*)$', '', raw, count=1, flags=re.MULTILINE).strip()
    html = markdown.markdown(raw, extensions=['smarty'])
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


def build_toc():
    items = ['<div class="toc-entry"><span>Preface</span></div>']
    for _, label, title in CHAPTERS:
        items.append(
            f'<div class="toc-entry toc-chapter">'
            f'<span>{label}: {title}</span></div>'
        )
    items.append(
        '<div class="toc-entry" style="margin-top:14pt;">'
        '<span>You Are Not Alone</span></div>'
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

@page cover-page {{
    size: 5.5in 8.5in;
    margin: 0;
    @bottom-center {{ content: none; }}
}}
@page title-page   {{ @bottom-center {{ content: none; }} }}
@page copyright-page {{ @bottom-center {{ content: none; }} }}
@page toc-page     {{ @bottom-center {{ content: none; }} }}

body {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11.5pt;
    line-height: 1.58;
    color: #1a1a1a;
}}

/* === COVER PAGE === */
.cover-page {{
    page: cover-page;
    page-break-after: always;
    margin: 0;
    padding: 0;
}}
.cover-page img {{
    width: 5.5in;
    height: 8.5in;
    display: block;
}}

/* === TITLE PAGE === */
.title-page {{
    page: title-page;
    page-break-after: always;
    text-align: center;
    padding-top: 2.1in;
}}
.title-page h1 {{
    font-size: 28pt;
    font-weight: normal;
    letter-spacing: 1pt;
    line-height: 1.2;
    margin-bottom: 0.25in;
    color: #1a1a1a;
}}
.title-page .subtitle {{
    font-size: 12.5pt;
    font-style: italic;
    color: #4a4a4a;
    margin-bottom: 1.4in;
}}
.title-page .author {{
    font-size: 13pt;
    color: #1a1a1a;
}}
.title-page .imprint {{
    font-size: 10pt;
    color: #777;
    margin-top: 0.45in;
    letter-spacing: 1pt;
}}

/* === COPYRIGHT === */
.copyright-page {{
    page: copyright-page;
    page-break-after: always;
    text-align: center;
    padding-top: 3.3in;
    font-size: 10pt;
    line-height: 1.7;
    color: #444;
}}
.copyright-page p {{ margin-bottom: 10pt; }}

/* === TOC === */
.toc-section {{
    page: toc-page;
    page-break-after: always;
    padding-top: 0.2in;
}}
.toc-section h1 {{
    font-size: 18pt;
    font-weight: normal;
    letter-spacing: 1pt;
    text-align: center;
    margin-bottom: 0.45in;
    color: #1a1a1a;
}}
.toc-entry {{
    font-size: 11pt;
    line-height: 1.95;
    color: #2a2a2a;
    text-align: left;
}}
.toc-chapter {{ padding-left: 0.2in; }}

/* === CHAPTER === */
.chapter {{ page-break-before: always; }}

.chapter-header {{
    text-align: center;
    margin-top: 0.4in;
    margin-bottom: 0.35in;
    padding-bottom: 0.12in;
}}
.chapter-header .chapter-num {{
    font-size: 10pt;
    letter-spacing: 0.18em;
    color: #8B6914;
    margin-bottom: 6pt;
    text-transform: uppercase;
}}
.chapter-header h1 {{
    font-size: 20pt;
    font-weight: normal;
    line-height: 1.25;
    color: #1a1a1a;
}}

.chapter-body p {{
    text-align: justify;
    text-indent: 0.28in;
    margin: 0;
    orphans: 2;
    widows: 2;
    hyphens: auto;
}}
.chapter-body > p:first-child,
.chapter-body > p:first-of-type {{ text-indent: 0; }}
.chapter-body hr + p,
.chapter-body h2 + p {{ text-indent: 0; }}

.chapter-body em {{ font-style: italic; }}
.chapter-body strong {{ font-weight: 600; }}

.chapter-body hr {{
    border: none;
    text-align: center;
    margin: 0.22in 0;
}}
.chapter-body hr::before {{
    content: "\u2022   \u2022   \u2022";
    color: #aaa;
    letter-spacing: 0.1em;
    font-size: 10pt;
}}

/* Preface is the softer, letter-tone opener: no indent, a bit more air */
.preface-body p {{
    text-align: left;
    text-indent: 0;
    margin-bottom: 11pt;
}}

/* Closing reads as reflection + resources, left-aligned */
.closing .chapter-body p {{
    text-align: left;
    text-indent: 0;
    margin-bottom: 10pt;
}}
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
    <h1>Before I Formed You</h1>
    <p class="subtitle">What God Says to the Woman Holding This Book</p>
    <p class="author">Paul &amp; Pam Hainline</p>
    <p class="imprint">NOBLEMIND PRESS</p>
  </div>

  <div class="copyright-page">
    <p><strong>Before I Formed You</strong></p>
    <p>Copyright &copy; 2026 Paul &amp; Pam Hainline. All rights reserved.</p>
    <p>Published by NobleMind Press &bull; noblemind.study</p>
    <p style="margin-top:16pt;">All Scripture quotations are from the<br>
    New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p style="margin-top:16pt;">This booklet may be freely shared and distributed for<br>
    the purpose of encouragement, teaching, and study.</p>
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
    print("Building preface...")
    sections = [build_preface()]
    for fname, label, title in CHAPTERS:
        print(f"  {fname}")
        sections.append(build_chapter(fname, label, title))
    print("Building closing...")
    sections.append(build_closing())

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
