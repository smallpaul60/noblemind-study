#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'The Last Week of the Lamb'.

Distinct from the Lulu print interior. This version is single-sided,
reader-friendly: cover, title, copyright, TOC, Prologue, four Parts with
their chapters, Interlude between Parts One and Two, and Epilogue.

Charts from the print interior are intentionally skipped — this is a
text-only reader PDF. The print edition has them.

Output: The_Last_Week_of_the_Lamb.pdf  (5.5" x 8.5", EB Garamond)
"""

import re
from html import unescape as html_unescape
from pathlib import Path
import markdown
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "The_Last_Week_of_the_Lamb.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER = BOOK_DIR / "The_Last_Week_of_the_Lamb_Front_Cover_Mockup.png"

TITLE = "The Last Week of the Lamb"
SUBTITLE = "The Passover Pattern Good Friday Missed"
AUTHOR = "Paul Hainline"

# Ordered table of contents. Types: 'front' (prologue/interlude/epilogue),
# 'part' (divider page), 'chapter'.
SECTIONS = [
    ("front",    "Prologue_The_Promise_and_the_Thread.md",       "Prologue",       "The Promise and the Thread"),
    ("part",     None,                                            "Part One",       "The Pattern"),
    ("chapter",  "Chapter01_The_Lamb_in_Egypt.md",                "Chapter One",    "The Lamb in Egypt"),
    ("chapter",  "Chapter02_The_Lamb_in_Prophecy.md",             "Chapter Two",    "The Lamb in Prophecy"),
    ("front",    "Understanding_the_Hebrew_Calendar_Interlude.md","Interlude",      "Understanding the Hebrew Calendar"),
    ("part",     None,                                            "Part Two",       "The Week"),
    ("chapter",  "Chapter03_The_Arrival_and_the_Selection.md",    "Chapter Three",  "The Arrival and the Selection"),
    ("chapter",  "Chapter04_Leaves_Without_Fruit.md",              "Chapter Four",   "Leaves Without Fruit"),
    ("chapter",  "Chapter05_The_Lamb_Is_Examined.md",              "Chapter Five",   "The Lamb Is Examined"),
    ("chapter",  "Chapter06_The_Anointing_and_the_Betrayal.md",    "Chapter Six",    "The Anointing and the Betrayal"),
    ("chapter",  "Chapter07_The_Passover.md",                      "Chapter Seven",  "The Passover"),
    ("chapter",  "Chapter08_The_Cup_and_the_Trials.md",            "Chapter Eight",  "The Cup and the Trials"),
    ("chapter",  "Chapter09_The_Lamb_Is_Killed.md",                "Chapter Nine",   "The Lamb Is Killed"),
    ("part",     None,                                            "Part Three",      "The Silence"),
    ("chapter",  "Chapter10_Three_Days_and_Three_Nights.md",       "Chapter Ten",    "Three Days and Three Nights"),
    ("part",     None,                                            "Part Four",       "The Open Door"),
    ("chapter",  "Chapter11_The_Stone_Moves.md",                   "Chapter Eleven", "The Stone Moves"),
    ("chapter",  "Chapter12_When_Did_the_Lamb_Die.md",             "Chapter Twelve", "When Did the Lamb Die?"),
    ("front",    "Epilogue_The_Thread_Completed.md",               "Epilogue",       "The Thread Completed"),
]


# ---------------------------------------------------------------------------
# Scripture blockquote conversion — matches FTB style since TLW markdown uses
# `> *"text"* — **Reference**` for scripture quotes.
# ---------------------------------------------------------------------------
def convert_scripture_blockquotes(html_text):
    def convert(match):
        inner = match.group(1).strip()
        inner = re.sub(r'^<p>(.*)</p>$', r'\1', inner, flags=re.DOTALL).strip()

        parts = re.split(r'\s*[\u2014\u2013]\s*(?=<strong>)', inner, maxsplit=1)
        if len(parts) != 2:
            return match.group(0)

        quote_text = parts[0].strip()
        cite_text = parts[1].strip()
        quote_text = re.sub(r'^<em>(.*)</em>$', r'\1', quote_text, flags=re.DOTALL)
        quote_text = html_unescape(quote_text).strip().strip('\u201c\u201d"\'')
        cite_text = re.sub(r'</?strong>', '', cite_text)
        cite_text = re.sub(r',?\s*NASB\s*$', '', cite_text).strip()

        return (
            '<blockquote class="scripture">'
            f'<p>\u201c{quote_text}\u201d</p>'
            f'<cite>\u2014 {cite_text}</cite>'
            '</blockquote>'
        )

    return re.sub(r'<blockquote>\s*(.*?)\s*</blockquote>', convert, html_text, flags=re.DOTALL)


def md_body(path):
    """Strip the first H1 (section title) and render body. H2/H3 kept as
    section subheadings inside the body."""
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    html = markdown.markdown(text, extensions=['smarty', 'tables'])
    return convert_scripture_blockquotes(html)


def build_front_section(filename, label, title):
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


def build_part_page(label, subtitle):
    return f"""
    <section class="part-page">
      <p class="part-num">{label}</p>
      <h1 class="part-title">{subtitle}</h1>
    </section>
    """


def build_toc():
    items = []
    for kind, _fname, label, title in SECTIONS:
        if kind == "part":
            items.append(
                f'<div class="toc-part"><strong>{label}: {title}</strong></div>'
            )
        elif kind == "front":
            # Prologue / Interlude / Epilogue — flush left
            items.append(
                f'<div class="toc-entry">'
                f'<span>{label}: {title}</span></div>'
            )
        else:  # chapter
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
@page cover-page     {{ size: 5.5in 8.5in; margin: 0; @bottom-center {{ content: none; }} }}
@page title-page     {{ @bottom-center {{ content: none; }} }}
@page copyright-page {{ @bottom-center {{ content: none; }} }}
@page toc-page       {{ @bottom-center {{ content: none; }} }}
@page part-div-page  {{ @bottom-center {{ content: none; }} }}

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
.toc-part {{
    margin-top: 14pt; margin-bottom: 4pt;
    font-size: 11.5pt; color: #1a1a1a;
}}
.toc-entry   {{ font-size: 11pt; line-height: 1.85; color: #2a2a2a; text-align: left; }}
.toc-chapter {{ padding-left: 0.2in; }}

.part-page {{
    page: part-div-page; page-break-before: always; page-break-after: always;
    text-align: center; padding-top: 3.2in;
}}
.part-page .part-num {{
    font-size: 11pt; letter-spacing: 0.2em; color: #D4A848;
    text-transform: uppercase; margin-bottom: 14pt;
}}
.part-page .part-title {{
    font-size: 26pt; font-weight: normal; line-height: 1.15;
    color: #1a1a1a; margin-bottom: 16pt;
}}

.chapter {{ page-break-before: always; }}
.chapter-header {{
    text-align: center; margin-top: 0.4in; margin-bottom: 0.32in;
}}
.chapter-header .chapter-num {{
    font-size: 10pt; letter-spacing: 0.18em; color: #C87941;
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

blockquote.scripture {{
    margin: 0.14in 0 0.14in 0.35in;
    padding-left: 0.22in;
    border-left: 2pt solid #D4A848;
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

.chapter-body table {{
    border-collapse: collapse; margin: 0.18in 0; width: 100%;
    font-size: 10pt; page-break-inside: avoid;
}}
.chapter-body th, .chapter-body td {{
    border: 1px solid #bbb; padding: 5pt 7pt; vertical-align: top;
    text-align: left;
}}
.chapter-body th {{ background: #f5e8cc; font-weight: 600; }}
"""


def build_full_html(body_sections, toc_html):
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

  {body_sections}
</body>
</html>"""


def main():
    print("Building sections...")
    body = []
    for kind, fname, label, title in SECTIONS:
        if kind == "part":
            print(f"  -- {label}: {title}")
            body.append(build_part_page(label, title))
        elif kind == "front":
            print(f"  {fname}")
            body.append(build_front_section(fname, label, title))
        else:
            print(f"  {fname}")
            body.append(build_chapter(fname, label, title))

    toc_html = build_toc()
    html = build_full_html("\n".join(body), toc_html)

    debug = BOOK_DIR / "_pdf_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
