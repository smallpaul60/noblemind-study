#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'Change the Mind, Change the Man'.

Distinct from the Lulu print interior. Reader-friendly single-sided layout
with cover, title, copyright, TOC, and 10 chapters.

The reader PDF is encrypted with the password 'freddie', matching the
online reader gate. The password also guards the download button client-side.

Output: Change_the_Mind_Change_the_Man.pdf  (5.5" x 8.5", EB Garamond)
"""

import re
from pathlib import Path
import weasyprint
from pypdf import PdfReader, PdfWriter

# Reuse the chapter list + markdown parser from the existing Lulu script.
# The parser understands this book's specific markdown conventions
# (# **Chapter N** / # **Title** / ## *tagline*, citation-after-quote, etc).
from generate_lulu_interior import CHAPTERS, parse_markdown_to_html

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Change_the_Mind_Change_the_Man.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER = BOOK_DIR / "cover_front_only.jpg"

TITLE = "Change the Mind, Change the Man"
SUBTITLE = "A Biblical Path from Addiction to Recovery"
AUTHOR = "Paul Hainline"
# Password that gates both the online reader and the PDF file itself.
PDF_PASSWORD = "freddie"


def build_chapter(filename, label, title, tagline):
    md_text = (BOOK_DIR / filename).read_text(encoding='utf-8')
    body_html = parse_markdown_to_html(md_text)
    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{label}</p>
        <h1>{title}</h1>
        <p class="chapter-tagline"><em>{tagline}</em></p>
      </div>
      <div class="chapter-body">
        {body_html}
      </div>
    </section>
    """


def build_toc():
    items = []
    for _fname, label, title, _tagline in CHAPTERS:
        items.append(
            f'<div class="toc-entry">'
            f'<span class="toc-num">{label}</span>'
            f'<span class="toc-title">{title}</span>'
            f'</div>'
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
@page cover-page     {{ size: 5.5in 8.5in; margin: 0; @bottom-center {{ content: none; }} }}
@page title-page     {{ @bottom-center {{ content: none; }} }}
@page copyright-page {{ @bottom-center {{ content: none; }} }}
@page toc-page       {{ @bottom-center {{ content: none; }} }}

body {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11.5pt;
    line-height: 1.58;
    color: #1a1a1a;
}}

.cover-page {{ page: cover-page; page-break-after: always; margin: 0; padding: 0; }}
.cover-page img {{ width: 5.5in; height: 8.5in; display: block; }}

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
    margin-bottom: 1.4in;
}}
.title-page .author  {{ font-size: 13pt; color: #1a1a1a; }}
.title-page .imprint {{ font-size: 10pt; color: #777; margin-top: 0.45in; letter-spacing: 1pt; }}

.copyright-page {{
    page: copyright-page; page-break-after: always;
    text-align: center; padding-top: 1.8in;
    font-size: 10pt; line-height: 1.65; color: #444;
}}
.copyright-page p {{ margin-bottom: 9pt; }}

.toc-section {{ page: toc-page; page-break-after: always; padding-top: 0.2in; }}
.toc-section h1 {{
    font-size: 18pt; font-weight: normal; letter-spacing: 1pt;
    text-align: center; margin-bottom: 0.4in; color: #1a1a1a;
}}
.toc-entry {{
    display: flex; align-items: baseline;
    font-size: 11pt; line-height: 1.95; color: #2a2a2a;
}}
.toc-num {{ min-width: 1.1in; color: #C4A94E; }}
.toc-title {{ flex: 1; }}

.chapter {{ page-break-before: always; }}
.chapter-header {{
    text-align: center; margin-top: 0.4in; margin-bottom: 0.3in;
}}
.chapter-header .chapter-num {{
    font-size: 10pt; letter-spacing: 0.18em; color: #C4A94E;
    margin-bottom: 6pt; text-transform: uppercase;
}}
.chapter-header h1 {{
    font-size: 20pt; font-weight: normal; line-height: 1.25; color: #1a1a1a;
    margin-bottom: 0.1in;
}}
.chapter-header .chapter-tagline {{
    font-size: 11pt; color: #555; text-indent: 0;
    margin-top: 2pt;
}}

.chapter-body p {{
    text-align: justify; text-indent: 0.28in;
    margin: 0; orphans: 2; widows: 2; hyphens: auto;
}}
.chapter-body > p:first-child {{ text-indent: 0; }}
.chapter-body h2 + p,
.chapter-body h3 + p,
.chapter-body blockquote + p,
.chapter-body .divider + p {{ text-indent: 0; }}

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

.chapter-body .divider {{
    text-align: center; margin: 0.22in 0;
    color: #aaa; letter-spacing: 0.1em; font-size: 10pt;
}}

blockquote.scripture {{
    margin: 0.14in 0 0.14in 0.35in;
    padding-left: 0.22in;
    border-left: 2pt solid #C4A94E;
    font-style: italic;
    font-size: 10.8pt;
    line-height: 1.5;
    page-break-inside: avoid;
}}
blockquote.scripture p {{ text-indent: 0 !important; text-align: left; margin-bottom: 0; }}
blockquote.scripture cite {{
    display: block; margin-top: 3pt;
    font-style: normal; font-size: 9.5pt; color: #4a4a4a;
    letter-spacing: 0.02em;
}}

p.citation {{
    text-indent: 0;
    font-size: 9.5pt;
    color: #555;
    margin-bottom: 0.1in;
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
    <h1>{TITLE}</h1>
    <p class="subtitle">{SUBTITLE}</p>
    <p class="author">{AUTHOR}</p>
    <p class="imprint">NOBLEMIND PRESS</p>
  </div>

  <div class="copyright-page">
    <p><strong>{TITLE}</strong></p>
    <p>Copyright &copy; 2026 {AUTHOR}. All rights reserved.</p>
    <p>Published by NobleMind Press &bull; noblemind.study</p>
    <p style="margin-top:14pt;">Inspired by the teaching of Freddie Anderson.</p>
    <p style="margin-top:14pt;">All Scripture quotations are from the<br>
    New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p style="margin-top:14pt;">ISBN (Paperback): 979-8-9954288-4-8<br>
    ISBN (Hardcover): 979-8-9954288-5-5</p>
    <p style="margin-top:14pt;">First Edition</p>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {chapter_sections}
</body>
</html>"""


def encrypt_pdf(path, password):
    """Re-write the PDF encrypted with the given password (AES-256)."""
    reader = PdfReader(str(path))
    writer = PdfWriter(clone_from=reader)
    writer.encrypt(user_password=password, owner_password=None, algorithm="AES-256")
    with open(path, "wb") as f:
        writer.write(f)


def main():
    print("Building chapters...")
    sections = []
    for fname, label, title, tagline in CHAPTERS:
        print(f"  {fname}")
        sections.append(build_chapter(fname, label, title, tagline))

    toc_html = build_toc()
    html = build_full_html("\n".join(sections), toc_html)

    debug = BOOK_DIR / "_pdf_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))
    size_before = OUTPUT.stat().st_size
    print(f"  wrote {size_before:,} bytes (unencrypted)")

    print(f"Encrypting with password '{PDF_PASSWORD}'...")
    encrypt_pdf(OUTPUT, PDF_PASSWORD)
    size_after = OUTPUT.stat().st_size
    print(f"Wrote {OUTPUT}  ({size_after:,} bytes, AES-256)")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
