#!/usr/bin/env python3
"""Generate the Lulu print interior PDF for 'Made, Not Written'.

5.5" x 8.5" with mirror margins, B&W cream paper:
  - gutter 0.75"   (inside)
  - outside 0.625"
  - top 0.85", bottom 0.9"
Alternating facing-page margins. Chapter sections start recto.
No cover (Lulu uses a separate cover file).
Page numbers alternate to outside corners (bottom).

Front matter (unnumbered): half-title, title, copyright, contents.
Body: parts + chapters + conclusion + afterword + appendix.
Back matter: Scripture Index.

Distinct from the reader PDF — that one is single-sided, has the cover
image on page 1, centered page numbers, and skips the Scripture Index.
This generator shares the markdown preprocessing for machine-blocks
and section dividers so the body renders identically.

Output: Made_Not_Written_Lulu_Interior.pdf
"""

import re
from pathlib import Path

import markdown
import pypdf
import weasyprint


BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Made_Not_Written_Lulu_Interior.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"


# (markdown filename, chapter label, chapter title)
SECTIONS = [
    # Part One — Made, Not Written
    ("Made_Not_Written_Ch1.md",  "Chapter One",      "The Stupidly Simple Goal"),
    ("Made_Not_Written_Ch2.md",  "Chapter Two",      "Weights, Not Wires"),
    ("Made_Not_Written_Ch3.md",  "Chapter Three",    "The Ghost That Isn’t There"),
    ("Made_Not_Written_Ch4.md",  "Chapter Four",     "Why Even Its Makers Can’t Fully Read It"),
    # Part Two — What Is This Thing?
    ("Made_Not_Written_Ch5.md",  "Chapter Five",     "Is Anyone Home?"),
    ("Made_Not_Written_Ch6.md",  "Chapter Six",      "Creativity, or Clever Recombination?"),
    ("Made_Not_Written_Ch7.md",  "Chapter Seven",    "The Mirror Problem"),
    ("Made_Not_Written_Ch8.md",  "Chapter Eight",    "Not a Soul, Not a Toaster"),
    # Part Three — The Oldest Question, New Volume
    ("Made_Not_Written_Ch9.md",  "Chapter Nine",     "Babel Revisited"),
    ("Made_Not_Written_Ch10.md", "Chapter Ten",      "The Problem Was Never the Tool"),
    ("Made_Not_Written_Ch11.md", "Chapter Eleven",   "The Mixed Heart"),
    ("Made_Not_Written_Ch12.md", "Chapter Twelve",   "Stewardship, Not Surrender or Salvation"),
    ("Made_Not_Written_Ch13.md", "Chapter Thirteen", "What a Machine Can’t Give You"),
    # Closing
    ("Made_Not_Written_Conclusion.md", "Conclusion", "Working Together, Rightly Ordered"),
    ("Made_Not_Written_Afterword.md",  "Afterword",  "When the Machine Stays On"),
    ("Made_Not_Written_Appendix.md",   "Appendix",   "The Plain Glossary"),
]


# Index → (part label, part title, part subtitle). Inserted BEFORE the
# section at that index, as a part-divider page.
PART_STRUCTURE = {
    0: ("Part One",   "Made, Not Written",              "How the thing actually works."),
    4: ("Part Two",   "What Is This Thing?",            "What it is, and what it is not."),
    8: ("Part Three", "The Oldest Question, New Volume", "The reach has grown enormous. The heart that picks it up is the same heart it has always been."),
}


# ─────────────────────────────────────────────────────────────────────
# Scripture Index data — every citation (with verse) found in the book.
# (book_name_for_sort_order, display_label, list of (reference, chapter_label) tuples)
#
# Sort order follows the canonical biblical order.
# ─────────────────────────────────────────────────────────────────────

SCRIPTURE_INDEX = [
    ("Genesis", [
        ("1:28",       ["Chapter Nine", "Chapter Twelve"]),
        ("2:7",        ["Afterword"]),
        ("2:16–17",    ["Chapter Nine"]),
        ("2:18",       ["Chapter Seven", "Chapter Thirteen"]),
        ("3 (the Fall)", ["Chapter Ten"]),
        ("3:5",        ["Chapter Ten"]),
        ("6:5",        ["Chapter Nine"]),
        ("8:21",       ["Chapter Nine"]),
        ("9:1",        ["Chapter Nine"]),
        ("11:4",       ["Chapter Nine", "Chapter Eleven"]),
        ("11:6",       ["Chapter Nine"]),
        ("12:3",       ["Chapter Nine"]),
    ]),
    ("Deuteronomy", [
        ("6:5",        ["Chapter Eleven"]),
    ]),
    ("Job", [
        ("33:4",       ["Afterword"]),
    ]),
    ("Psalms", [
        ("139:23–24",  ["Chapter Eleven"]),
    ]),
    ("Proverbs", [
        ("3:5",        ["Chapter Ten", "Conclusion", "Afterword"]),
    ]),
    ("Matthew", [
        ("4:8–9",      ["Chapter Ten"]),
        ("22:37–38",   ["Chapter Eleven"]),
        ("25:15",      ["Chapter Twelve"]),
        ("25:19",      ["Chapter Twelve"]),
        ("25:21",      ["Chapter Twelve"]),
    ]),
    ("Luke", [
        ("12:48",      ["Chapter Twelve"]),
    ]),
    ("John", [
        ("4:13–14",    ["Chapter Thirteen"]),
    ]),
    ("Acts", [
        ("17:25",      ["Afterword"]),
        ("17:26–27",   ["Chapter Nine"]),
    ]),
    ("Philippians", [
        ("1:15–17",    ["Chapter Eleven"]),
        ("1:18",       ["Chapter Eleven"]),
    ]),
    ("Hebrews", [
        ("4:15",       ["Chapter Ten"]),
    ]),
    ("James", [
        ("2:26 (alluded)", ["Chapter Five"]),
    ]),
]


# ─────────────────────────────────────────────────────────────────────
# Markdown preprocessing — mirrors the reader PDF generator's logic
# ─────────────────────────────────────────────────────────────────────

CHAPTER_LABEL_RE = re.compile(r'^\*\*[^*\n]+\*\*\s*\n', re.MULTILINE)
DECORATIVE_DIVIDER_RE = re.compile(r'^\s*❧\s*\n', re.MULTILINE)
SECTION_DIVIDER_MD_RE = re.compile(r'^\s*•\s+•\s+•\s*$', re.MULTILINE)

MACHINE_INTRO_LINE_RE = re.compile(
    r'^\s*\*{0,2}\s*The machine answered\s*:?\s*\*{0,2}\s*$',
    re.IGNORECASE,
)


def wrap_machine_blocks_md(md_text):
    """Pre-markdown: wrap each 'The machine answered:' run in explicit
    <div> blocks with markdown="1" so python-markdown still processes
    the italic prose inside."""
    lines = md_text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        if MACHINE_INTRO_LINE_RE.match(lines[i]):
            out.append('<div class="machine-intro">The machine answered:</div>')
            out.append('<div class="machine-block" markdown="1">')
            out.append('')
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            while i < len(lines):
                if not lines[i].strip():
                    out.append('')
                    i += 1
                    continue
                first = lines[i].lstrip()
                if first.startswith('*'):
                    while i < len(lines) and lines[i].strip():
                        out.append(lines[i])
                        i += 1
                elif first.startswith('>'):
                    while i < len(lines) and lines[i].strip().startswith('>'):
                        out.append(re.sub(r'^\s*>\s?', '', lines[i]))
                        i += 1
                else:
                    break
            out.append('</div>')
            out.append('')
        else:
            out.append(lines[i])
            i += 1
    return '\n'.join(out)


def md_body(path):
    text = path.read_text(encoding='utf-8')
    text = CHAPTER_LABEL_RE.sub("", text, count=2).lstrip("\n")
    text = DECORATIVE_DIVIDER_RE.sub("", text, count=1).lstrip("\n")
    text = wrap_machine_blocks_md(text)
    text = SECTION_DIVIDER_MD_RE.sub("\n<hr />\n", text)
    return markdown.markdown(text, extensions=['extra', 'smarty'])


# ─────────────────────────────────────────────────────────────────────
# Page builders
# ─────────────────────────────────────────────────────────────────────

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
    items = []
    for idx, (fname, label, title) in enumerate(SECTIONS):
        if idx in PART_STRUCTURE:
            part_label, part_title, _ = PART_STRUCTURE[idx]
            items.append(
                f'<div class="toc-part"><strong>{part_label}: {part_title}</strong></div>'
            )
        items.append(
            f'<div class="toc-entry toc-chapter">'
            f'<span>{label}: {title}</span></div>'
        )
    items.append('<div class="toc-entry toc-chapter toc-backmatter">'
                 '<span>Scripture Index</span></div>')
    return "\n".join(items)


def build_scripture_index():
    rows = []
    for book_name, entries in SCRIPTURE_INDEX:
        rows.append(f'<div class="si-book">{book_name}</div>')
        for ref, chapters in entries:
            chapter_list = "; ".join(chapters)
            rows.append(
                f'<div class="si-entry">'
                f'<span class="si-ref">{book_name} {ref}</span>'
                f'<span class="si-locs">{chapter_list}</span>'
                f'</div>'
            )
    return f"""
    <section class="scripture-index">
      <div class="chapter-header">
        <p class="chapter-num">Back Matter</p>
        <h1>Scripture Index</h1>
      </div>
      <div class="si-body">
        <p class="si-note"><em>References are by chapter rather than by page; chapter
        headings provide a stable, edition-independent address. Books appear
        in canonical order.</em></p>
        {"".join(rows)}
      </div>
    </section>
    """


# ─────────────────────────────────────────────────────────────────────
# CSS — mirror margins, recto chapter starts, alternating page numbers
# ─────────────────────────────────────────────────────────────────────

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

/* Mirror-margin pages. Page numbers alternate to outside corners. */
@page :right {{
    size: 5.5in 8.5in;
    margin: 0.85in 0.625in 0.9in 0.75in;  /* gutter on left for recto */
    @bottom-right {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt; color: #555;
    }}
}}
@page :left {{
    size: 5.5in 8.5in;
    margin: 0.85in 0.75in 0.9in 0.625in;  /* gutter on right for verso */
    @bottom-left {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt; color: #555;
    }}
}}

/* Front matter + auto-inserted blanks: no page numbers */
@page half-title-page {{ @bottom-right {{ content: none; }} @bottom-left {{ content: none; }} }}
@page title-page      {{ @bottom-right {{ content: none; }} @bottom-left {{ content: none; }} }}
@page copyright-page  {{ @bottom-right {{ content: none; }} @bottom-left {{ content: none; }} }}
@page toc-page        {{ @bottom-right {{ content: none; }} @bottom-left {{ content: none; }} }}
@page part-div-page   {{ @bottom-right {{ content: none; }} @bottom-left {{ content: none; }} }}
@page :blank          {{ @bottom-right {{ content: none; }} @bottom-left {{ content: none; }} }}

body {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11.5pt;
    line-height: 1.58;
    color: #1a1a1a;
}}

/* HALF TITLE (recto) */
.half-title-page {{
    page: half-title-page; page-break-after: always;
    text-align: center; padding-top: 3.3in;
}}
.half-title-page h1 {{
    font-size: 22pt; font-weight: normal; letter-spacing: 1pt;
    line-height: 1.2; color: #1a1a1a;
}}

/* TITLE (recto) */
.title-page {{
    page: title-page; page-break-before: right; page-break-after: always;
    text-align: center; padding-top: 2.0in;
}}
.title-page h1 {{
    font-size: 30pt; font-weight: normal; letter-spacing: 1pt;
    line-height: 1.2; margin-bottom: 0.25in; color: #1a1a1a;
}}
.title-page .subtitle {{
    font-size: 13pt; font-style: italic; color: #4a4a4a;
    margin-bottom: 1.4in;
}}
.title-page .author  {{ font-size: 13pt; color: #1a1a1a; }}
.title-page .imprint {{
    font-size: 10pt; color: #777; margin-top: 0.45in;
    letter-spacing: 2pt;
}}

/* COPYRIGHT (verso) */
.copyright-page {{
    page: copyright-page; page-break-after: always;
    text-align: center; padding-top: 1.8in;
    font-size: 10pt; line-height: 1.65; color: #444;
}}
.copyright-page p {{ margin-bottom: 9pt; }}

/* TOC (recto) */
.toc-section {{ page: toc-page; page-break-before: right; page-break-after: always; padding-top: 0.1in; }}
.toc-section h1 {{
    font-size: 18pt; font-weight: normal; letter-spacing: 1pt;
    text-align: center; margin-bottom: 0.28in; color: #1a1a1a;
}}
.toc-part {{
    margin-top: 10pt; margin-bottom: 2pt;
    font-size: 11pt; color: #1a1a1a;
}}
.toc-entry {{
    font-size: 10.5pt; line-height: 1.55;
    color: #2a2a2a; text-align: left;
}}
.toc-chapter {{ padding-left: 0.2in; }}
.toc-backmatter {{ margin-top: 10pt; }}

/* PART DIVIDER */
.part-page {{
    page: part-div-page; page-break-before: right; page-break-after: always;
    text-align: center; padding-top: 3.0in;
}}
.part-page .part-num {{
    font-size: 11pt; letter-spacing: 0.2em; color: #8B6914;
    text-transform: uppercase; margin-bottom: 14pt;
}}
.part-page .part-title {{
    font-size: 26pt; font-weight: normal; line-height: 1.15;
    color: #1a1a1a; margin-bottom: 18pt;
}}
.part-page .part-subtitle {{
    font-size: 12pt; color: #555;
    max-width: 4in; margin: 0 auto;
    line-height: 1.5;
}}

/* CHAPTER — recto start */
.chapter {{ page-break-before: right; }}
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
.chapter-body hr + p,
.chapter-body div.machine-block + p,
.chapter-body div.machine-intro + p {{ text-indent: 0; }}

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

/* SECTION DIVIDER */
.chapter-body hr {{
    border: none; text-align: center; margin: 0.22in 0;
}}
.chapter-body hr::before {{
    content: "•   •   •";
    color: #aaa; letter-spacing: 0.1em; font-size: 10pt;
}}

/* MACHINE DIALOGUE — slate accent in print (no color screen on
   B&W interior, but the indent + rule still set it apart). The
   border becomes a darker grey under B&W rasterization, which
   reads as exactly the "cooler voice of the tool" treatment we
   want. */
.chapter-body .machine-intro {{
    font-style: italic; font-size: 10.5pt;
    color: #444; letter-spacing: 0.5pt;
    margin: 0.22in 0 0.05in 0.20in;
    page-break-after: avoid;
}}
.chapter-body .machine-block {{
    margin: 0 0 0.22in 0.20in;
    padding: 0.05in 0.22in 0.05in 0.22in;
    border-left: 1.5pt solid #555;
    page-break-inside: auto;
}}
.chapter-body .machine-block p {{
    text-align: left; text-indent: 0;
    font-style: italic; font-size: 10.8pt;
    line-height: 1.6;
    margin: 0.08in 0;
}}
.chapter-body .machine-block p:first-child {{ margin-top: 0.05in; }}
.chapter-body .machine-block p:last-child {{ margin-bottom: 0.05in; }}
.chapter-body .machine-block em {{
    font-style: normal;
    color: #333;
    font-weight: 500;
}}

/* SCRIPTURE INDEX */
.scripture-index {{ page-break-before: right; }}
.scripture-index .si-body {{ margin-top: 0.15in; }}
.scripture-index .si-note {{
    font-size: 10pt; color: #555; line-height: 1.5;
    text-align: center; margin: 0 0.3in 0.25in 0.3in;
    text-indent: 0;
}}
.scripture-index .si-book {{
    font-size: 12pt; font-weight: 600;
    color: #1a1a1a; letter-spacing: 0.5pt;
    margin-top: 14pt; margin-bottom: 6pt;
    page-break-after: avoid;
    border-bottom: 0.5pt solid #888;
    padding-bottom: 3pt;
}}
.scripture-index .si-book:first-of-type {{ margin-top: 0; }}
.scripture-index .si-entry {{
    font-size: 10.5pt; line-height: 1.55;
    margin: 0 0 3pt 0.15in;
    text-indent: 0;
    page-break-inside: avoid;
}}
.scripture-index .si-ref {{
    display: inline-block; min-width: 1.6in;
    color: #1a1a1a;
}}
.scripture-index .si-locs {{
    color: #555; font-style: italic;
}}
"""


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def build_full_html(sections_html, toc_html, scripture_index_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <div class="half-title-page">
    <h1>Made,<br>Not Written</h1>
  </div>

  <div class="title-page">
    <h1>Made,<br>Not Written</h1>
    <p class="subtitle">A Bible Student Looks at the Machine</p>
    <p class="author">Paul Hainline</p>
    <p class="imprint">NOBLEMIND PUBLISHING</p>
  </div>

  <div class="copyright-page">
    <p><strong>Made, Not Written</strong><br>
    <em>A Bible Student Looks at the Machine</em></p>
    <p>Copyright &copy; 2026 Paul Hainline. All rights reserved.</p>
    <p>Published by NobleMind Publishing &bull; noblemind.study</p>
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

  {sections_html}

  {scripture_index_html}

</body>
</html>"""


def main():
    print(f"Building Lulu interior: {OUTPUT.name}")
    parts = []
    for idx, (fname, label, title) in enumerate(SECTIONS):
        if idx in PART_STRUCTURE:
            p_label, p_title, p_sub = PART_STRUCTURE[idx]
            print(f"  -- {p_label}: {p_title}")
            parts.append(build_part_page(p_label, p_title, p_sub))
        print(f"  {fname}")
        parts.append(build_chapter(fname, label, title))

    toc_html = build_toc()
    scripture_index_html = build_scripture_index()
    html = build_full_html("\n".join(parts), toc_html, scripture_index_html)

    debug = BOOK_DIR / "_lulu_interior_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF (WeasyPrint)...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))

    # Lulu requires an even page count for perfect-bound paperback.
    # If odd, append a single blank verso so the bind closes cleanly.
    reader = pypdf.PdfReader(str(OUTPUT))
    n = len(reader.pages)
    if n % 2 == 1:
        writer = pypdf.PdfWriter(clone_from=reader)
        writer.add_blank_page(width=396, height=612)  # 5.5"x8.5" in pt
        writer.write(str(OUTPUT))
        n += 1
        print(f"  (padded final blank verso for even page count)")

    print(f"Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")
    print(f"  Page count: {n}")
    pb_spine = n * 0.00226 + 0.057
    hc_spine = pb_spine + 0.243
    print(f"  PB spine (cream formula): {pb_spine:.3f}\"  — pull final from Lulu template")
    print(f"  HC spine (estimate):      {hc_spine:.3f}\"  — pull final from Lulu template")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
