#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'Why Do You Delay?'.

Distinct from the Lulu print interior (generate_lulu_interior.py). This
version is single-sided, reader-friendly: cover image on page 1, title,
copyright, epigraph, TOC, preface, 3 parts with 13 chapters total, and
the epilogue. Centered page numbers. No Scripture index (kept for the
print edition only).

Output: Why_Do_You_Delay.pdf  (5.5" x 8.5", EB Garamond)
"""

from pathlib import Path
import weasyprint

from _book_source import (
    parse_book, md_body_to_html,
    TITLE, SUBTITLE, AUTHOR,
)

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_Do_You_Delay.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER    = BOOK_DIR / "cover_front.jpg"


# ============================================================================
# SECTION BUILDERS
# ============================================================================

def build_part_page(part):
    return f"""
    <section class="part-page">
      <p class="part-label">{part['label']}</p>
      <h1>{part['title']}</h1>
      <div class="part-rule"></div>
      <div class="part-intro">{md_body_to_html(part['intro_md'])}</div>
    </section>
    """


def build_preface(preface_md):
    body = md_body_to_html(preface_md)
    return f"""
    <section class="chapter preface">
      <div class="chapter-header">
        <p class="chapter-num">Preface</p>
      </div>
      <div class="chapter-body">{body}</div>
    </section>
    """


def build_chapter(ch):
    body = md_body_to_html(ch["md"])
    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{ch['label']}</p>
        <h1>{ch['title']}</h1>
      </div>
      <div class="chapter-body">{body}</div>
    </section>
    """


def build_epilogue(title, md):
    body = md_body_to_html(md)
    return f"""
    <section class="chapter epilogue">
      <div class="chapter-header">
        <p class="chapter-num">Epilogue</p>
        <h1>{title}</h1>
      </div>
      <div class="chapter-body">{body}</div>
    </section>
    """


def build_toc(book):
    items = ['<div class="toc-entry toc-front"><span>Preface</span></div>']
    for part in book["parts"]:
        items.append(
            f'<div class="toc-part-header">{part["label"]}: {part["title"]}</div>'
        )
        for ch in part["chapters"]:
            items.append(
                f'<div class="toc-entry toc-chapter">'
                f'<span class="toc-num">Chapter {ch["num"]}</span>'
                f'<span class="toc-dots"></span>'
                f'<span class="toc-title">{ch["title"]}</span>'
                f'</div>'
            )
    items.append(
        f'<div class="toc-entry toc-epilogue"><span>Epilogue: {book["epilogue_title"]}</span></div>'
    )
    return "\n".join(items)


# ============================================================================
# CSS
# ============================================================================

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
@font-face {{
    font-family: 'EB Garamond';
    src: url('file://{FONT_DIR / "EBGaramond.ttf"}');
    font-weight: bold; font-style: normal;
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
@page front-matter  {{ @bottom-center {{ content: none; }} }}

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
    page: front-matter; page-break-after: always;
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
    page: front-matter; page-break-after: always;
    text-align: center; padding-top: 1.8in;
    font-size: 10pt; line-height: 1.65; color: #444;
}}
.copyright-page p {{ margin-bottom: 9pt; }}

/* EPIGRAPH */
.epigraph-page {{
    page: front-matter; page-break-after: always;
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
.toc-section {{ page: front-matter; page-break-after: always; padding-top: 0.2in; }}
.toc-section h1 {{
    font-size: 18pt; font-weight: normal; letter-spacing: 1pt;
    text-align: center; margin-bottom: 0.4in; color: #1a1a1a;
}}
.toc-entry {{ font-size: 11pt; line-height: 1.9; color: #2a2a2a; }}
.toc-chapter {{
    padding-left: 0.25in;
    display: flex;
    align-items: baseline;
    gap: 0.08in;
}}
.toc-num {{
    flex: 0 0 auto;
    font-variant: small-caps;
    color: #555;
    min-width: 0.85in;
    font-size: 10.5pt;
    letter-spacing: 0.04em;
}}
.toc-title {{ flex: 0 1 auto; }}
.toc-dots {{
    flex: 1 1 auto;
    border-bottom: 1px dotted #bbb;
    transform: translateY(-3px);
    margin: 0 0.1in;
}}
.toc-part-header {{
    margin-top: 14pt; margin-bottom: 4pt;
    font-size: 11.5pt; color: #1a1a1a; font-weight: 600;
    letter-spacing: 0.04em;
}}
.toc-front, .toc-epilogue {{
    font-weight: 600;
    font-size: 11pt;
}}
.toc-front {{ margin-bottom: 10pt; }}
.toc-epilogue {{ margin-top: 14pt; }}

/* PART PAGE */
.part-page {{
    page-break-before: always;
    text-align: center;
    padding-top: 1.8in;
}}
.part-page .part-label {{
    font-size: 10pt; letter-spacing: 0.22em;
    color: #8B6914; text-transform: uppercase;
    margin-bottom: 14pt;
}}
.part-page h1 {{
    font-size: 22pt; font-weight: normal;
    line-height: 1.25; color: #1a1a1a;
    margin: 0 0.4in 0.4in;
}}
.part-page .part-rule {{
    width: 0.8in; height: 1px; background: #bbb;
    margin: 0 auto 0.4in;
}}
.part-page .part-intro {{
    text-align: left;
    max-width: 4in;
    margin: 0 auto;
    font-size: 11pt;
    font-style: italic;
    color: #3a3a3a;
    line-height: 1.6;
}}
.part-page .part-intro p {{
    text-indent: 0;
    margin-bottom: 10pt;
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
    content: "•   •   •";
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
"""


# ============================================================================
# FULL HTML ASSEMBLY
# ============================================================================

def build_full_html(book):
    cover_tag = (
        f'<div class="cover-page"><img src="file://{COVER}" alt="cover"></div>'
        if COVER.exists() else ''
    )

    preface_html = build_preface(book["preface_md"])

    part_sections = []
    for part in book["parts"]:
        part_sections.append(build_part_page(part))
        for ch in part["chapters"]:
            part_sections.append(build_chapter(ch))

    epilogue_html = build_epilogue(book["epilogue_title"], book["epilogue_md"])
    toc_html = build_toc(book)

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
      <p>&ldquo;Now why do you delay? Get up and be baptized,<br>
      and wash away your sins, calling on His name.&rdquo;</p>
      <cite>&mdash; Acts 22:16</cite>
    </blockquote>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {preface_html}
  {"".join(part_sections)}
  {epilogue_html}
</body>
</html>"""


def main():
    print(f'Building reader PDF for "{TITLE}"...')
    book = parse_book()
    print(f"  Parsed: {len(book['chapters'])} chapters in {len(book['parts'])} parts")

    html = build_full_html(book)

    debug = BOOK_DIR / "_pdf_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF...")
    doc = weasyprint.HTML(string=html, base_url=str(BOOK_DIR))
    pdf_doc = doc.render()
    page_count = len(pdf_doc.pages)
    pdf_doc.write_pdf(str(OUTPUT))

    print(f"Wrote {OUTPUT.name}  ({page_count} pages, {OUTPUT.stat().st_size:,} bytes)")
    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
