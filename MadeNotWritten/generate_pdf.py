#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'Made, Not Written'.

A NobleMind Publishing title. Distinct from the Lulu print interior
(separate generator). Single-sided, reader-friendly, with cover image
on page 1, three-part structure, slate-blue machine-dialogue blocks,
inline Scripture (no blockquote treatment — see the chapter HTML
generator for the reasoning), and centered page numbers.

Output: Made_Not_Written.pdf  (5.5" x 8.5", EB Garamond)
"""

import re
from pathlib import Path
import markdown
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Made_Not_Written.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER = BOOK_DIR / "cover_front.jpg"


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
# Markdown preprocessing — mirrors the chapter HTML generator's logic
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
    the italic prose inside. Accepts both bold and plain introducers
    and both italic-paragraph and blockquote-paragraph body forms."""
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
    """Read a MadeNotWritten markdown source and convert to body HTML.
    Strips the bold chapter label + bold chapter title at the top
    (those are surfaced separately in the page template) and the
    decorative ❧ glyph. Section dividers (• • •)
    become <hr>. Machine dialogue runs become div.machine-block."""
    text = path.read_text(encoding='utf-8')
    text = CHAPTER_LABEL_RE.sub("", text, count=2).lstrip("\n")
    text = DECORATIVE_DIVIDER_RE.sub("", text, count=1).lstrip("\n")
    text = wrap_machine_blocks_md(text)
    text = SECTION_DIVIDER_MD_RE.sub("\n<hr />\n", text)
    return markdown.markdown(text, extensions=['extra', 'smarty'])


# ─────────────────────────────────────────────────────────────────────
# Page building blocks
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
    return "\n".join(items)


# ─────────────────────────────────────────────────────────────────────
# CSS
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

/* COVER */
.cover-page {{ page: cover-page; page-break-after: always; margin: 0; padding: 0; }}
.cover-page img {{ width: 5.5in; height: 8.5in; display: block; }}

/* TITLE */
.title-page {{
    page: title-page; page-break-after: always;
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
.toc-entry {{
    font-size: 11pt; line-height: 1.85;
    color: #2a2a2a; text-align: left;
}}
.toc-chapter {{ padding-left: 0.2in; }}

/* PART DIVIDER */
.part-page {{
    page: part-div-page; page-break-before: always; page-break-after: always;
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

/* SECTION DIVIDER (the three centered bullets) */
.chapter-body hr {{
    border: none; text-align: center; margin: 0.22in 0;
}}
.chapter-body hr::before {{
    content: "•   •   •";
    color: #aaa; letter-spacing: 0.1em; font-size: 10pt;
}}

/* MACHINE DIALOGUE — slate-blue, not gold. Gold is reserved for
   Scripture quotation site-wide; this is the cooler voice of the
   tool, the steel of the machine. */
.chapter-body .machine-intro {{
    font-style: italic; font-size: 10.5pt;
    color: #5a7090; letter-spacing: 0.5pt;
    margin: 0.22in 0 0.05in 0.20in;
    page-break-after: avoid;
}}
.chapter-body .machine-block {{
    margin: 0 0 0.22in 0.20in;
    padding: 0.05in 0.22in 0.05in 0.22in;
    border-left: 1.5pt solid #5a7090;
    background: rgba(122, 143, 168, 0.05);
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
/* Nested upright Roman inside the italic block — author's typographic
   emphasis where italic momentarily breaks to highlight a phrase. */
.chapter-body .machine-block em {{
    font-style: normal;
    color: #4a5d76;
    font-weight: 500;
}}
"""


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def build_full_html(sections_html, toc_html):
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
</body>
</html>"""


def main():
    print(f"Building reader PDF: {OUTPUT.name}")
    parts = []
    for idx, (fname, label, title) in enumerate(SECTIONS):
        if idx in PART_STRUCTURE:
            p_label, p_title, p_sub = PART_STRUCTURE[idx]
            print(f"  -- {p_label}: {p_title}")
            parts.append(build_part_page(p_label, p_title, p_sub))
        print(f"  {fname}")
        parts.append(build_chapter(fname, label, title))

    toc_html = build_toc()
    html = build_full_html("\n".join(parts), toc_html)

    debug = BOOK_DIR / "_pdf_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF (WeasyPrint)...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
