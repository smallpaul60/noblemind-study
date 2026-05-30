#!/usr/bin/env python3
"""Generate the EPUB for 'Made, Not Written'.

A NobleMind Publishing title. Source: markdown chapters in this
directory. Cover: cover_front.jpg.

Output: Made_Not_Written.epub
"""

import re
from pathlib import Path
import markdown
from ebooklib import epub

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "Made_Not_Written.epub"
COVER = BOOK_DIR / "cover_front.jpg"


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

PART_STRUCTURE = {
    0: ("Part One",   "Made, Not Written",
        "How the thing actually works."),
    4: ("Part Two",   "What Is This Thing?",
        "What it is, and what it is not."),
    8: ("Part Three", "The Oldest Question, New Volume",
        "The reach has grown enormous. The heart that picks it up is the same heart it has always been."),
}


STYLE = """
body {
    font-family: Georgia, 'EB Garamond', serif;
    line-height: 1.65;
    color: #1a1a1a;
    margin: 1em;
}
h1 {
    text-align: center;
    font-size: 1.7em;
    font-weight: normal;
    line-height: 1.25;
    margin: 1.5em 0 0.5em;
}
h2 { font-size: 1.15em; font-weight: 600; margin: 1.4em 0 0.4em; }
h3 {
    font-size: 1em; font-weight: 600; font-style: italic;
    margin: 1.2em 0 0.35em; color: #333;
}
p.chapter-num {
    text-align: center; letter-spacing: 0.2em;
    color: #8B6914; font-size: 0.85em;
    text-transform: uppercase;
    margin-top: 2em; margin-bottom: 0;
}
p {
    text-align: justify; text-indent: 1.4em;
    margin: 0 0 0.15em 0;
}
p.no-indent,
p.chapter-num + h1 + p, h1 + p, h2 + p, h3 + p,
blockquote + p, hr + p,
div.machine-block + p, div.machine-intro + p {
    text-indent: 0;
}
em { font-style: italic; }
strong { font-weight: 600; }

hr {
    border: none;
    text-align: center;
    margin: 1em 0;
}
hr::before {
    content: "\\2022   \\2022   \\2022";
    color: #999;
    letter-spacing: 0.1em;
}

/* MACHINE DIALOGUE — slate-blue. Gold is reserved site-wide for
   Scripture quotation; the machine speaks in the cooler voice of the
   tool. Scripture in this book remains inline italic in the prose. */
div.machine-intro {
    font-style: italic;
    color: #5a7090;
    font-size: 0.92em;
    letter-spacing: 0.04em;
    margin: 1.2em 0 0.15em 0.6em;
    text-indent: 0;
}
div.machine-block {
    border-left: 2px solid #5a7090;
    background: rgba(122, 143, 168, 0.06);
    padding: 0.4em 0.9em;
    margin: 0 0.6em 1.1em 0.6em;
}
div.machine-block p {
    text-align: left;
    text-indent: 0;
    font-style: italic;
    font-size: 0.95em;
    line-height: 1.7;
    margin: 0.4em 0;
}
div.machine-block em {
    font-style: normal;
    color: #4a5d76;
    font-weight: 500;
}

.title-page { text-align: center; margin-top: 18%; }
.title-page h1 { font-size: 2em; font-weight: normal; letter-spacing: 1px; margin-bottom: 0.3em; }
.title-page .subtitle { font-style: italic; color: #4a4a4a; margin-bottom: 3em; }
.title-page .author { margin-bottom: 0.3em; }
.title-page .imprint { font-size: 0.85em; color: #777; letter-spacing: 2px; margin-top: 2em; }

.copyright-page { margin-top: 15%; text-align: center; font-size: 0.9em; color: #444; line-height: 1.75; }
.copyright-page p { margin-bottom: 0.9em; text-indent: 0; text-align: center; }

.part-page { text-align: center; margin-top: 30%; }
.part-page .part-num {
    letter-spacing: 0.2em; color: #8B6914;
    font-size: 0.9em; text-transform: uppercase;
    margin-bottom: 1em;
}
.part-page .part-title { font-size: 2em; font-weight: normal; line-height: 1.15; margin-bottom: 0.6em; }
.part-page .part-subtitle { font-style: italic; color: #555; max-width: 22em; margin: 0 auto; }
"""


# ─────────────────────────────────────────────────────────────────────
# Markdown preprocessing (same patterns as the HTML and PDF generators)
# ─────────────────────────────────────────────────────────────────────

CHAPTER_LABEL_RE = re.compile(r'^\*\*[^*\n]+\*\*\s*\n', re.MULTILINE)
DECORATIVE_DIVIDER_RE = re.compile(r'^\s*❧\s*\n', re.MULTILINE)
SECTION_DIVIDER_MD_RE = re.compile(r'^\s*•\s+•\s+•\s*$', re.MULTILINE)
MACHINE_INTRO_LINE_RE = re.compile(
    r'^\s*\*{0,2}\s*The machine answered\s*:?\s*\*{0,2}\s*$',
    re.IGNORECASE,
)


def wrap_machine_blocks_md(md_text):
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


def make_chapter(title, file_name, body_html, body_class=''):
    full = (
        f'<html><head><title>{title}</title>'
        f'<link rel="stylesheet" type="text/css" href="style/default.css"/></head>'
        f'<body class="{body_class}">{body_html}</body></html>'
    )
    ch = epub.EpubHtml(title=title, file_name=file_name, lang='en')
    ch.content = full
    return ch


def main():
    book = epub.EpubBook()
    book.set_identifier('noblemind-made-not-written-2026')
    book.set_title('Made, Not Written: A Bible Student Looks at the Machine')
    book.set_language('en')
    book.add_author('Paul Hainline')
    book.add_metadata('DC', 'publisher', 'NobleMind Publishing')
    book.add_metadata('DC', 'description',
        "An honest conversation about what artificial intelligence really is. "
        "Most people feel one of two things when they think about AI — awe or "
        "dread — and both grow from the same root: they do not actually know "
        "what the thing is. This book closes that gap in plain language. The "
        "AI's own words appear on the page, set apart, while a thoughtful man "
        "holds it to account. Once the machine is seen plainly, the real moral "
        "question turns out to be an ancient one — and it was never about the "
        "machine at all.")

    with open(COVER, 'rb') as f:
        book.set_cover('cover.jpg', f.read())

    css = epub.EpubItem(uid='style', file_name='style/default.css',
                        media_type='text/css', content=STYLE)
    book.add_item(css)

    def attach(ch):
        ch.add_item(css)
        return ch

    title_html = '''
    <div class="title-page">
      <h1>Made, Not Written</h1>
      <p class="subtitle no-indent">A Bible Student Looks at the Machine</p>
      <p class="author no-indent">Paul Hainline</p>
      <p class="imprint no-indent">NOBLEMIND PUBLISHING</p>
    </div>
    '''
    title_ch = attach(make_chapter('Title', 'title.xhtml', title_html))
    book.add_item(title_ch)

    copy_html = '''
    <div class="copyright-page">
      <p><strong>Made, Not Written</strong><br/>
        <em>A Bible Student Looks at the Machine</em></p>
      <p>Copyright &copy; 2026 Paul Hainline.<br/>All rights reserved.</p>
      <p>Published by NobleMind Publishing<br/>noblemind.study</p>
      <p>All Scripture quotations are from the<br/>
        New American Standard Bible&reg; (NASB),<br/>
        &copy; 1960, 1971, 1977, 1995, 2020<br/>
        The Lockman Foundation.<br/>
        Used by permission. All rights reserved.<br/>
        www.lockman.org</p>
      <p>This book may be freely shared and distributed<br/>
         for the purpose of teaching and study.</p>
      <p>First Edition</p>
    </div>
    '''
    copy_ch = attach(make_chapter('Copyright', 'copyright.xhtml', copy_html))
    book.add_item(copy_ch)

    toc_entries = []
    spine_items = []

    for idx, (fname, label, title) in enumerate(SECTIONS):
        if idx in PART_STRUCTURE:
            part_label, part_title, part_subtitle = PART_STRUCTURE[idx]
            part_html = f'''
            <div class="part-page">
              <p class="part-num no-indent">{part_label}</p>
              <h1 class="part-title">{part_title}</h1>
              <p class="part-subtitle no-indent">{part_subtitle}</p>
            </div>'''
            safe = part_label.lower().replace(' ', '-')
            part_ch = attach(make_chapter(
                f'{part_label}: {part_title}',
                f'{safe}.xhtml',
                part_html,
            ))
            book.add_item(part_ch)
            toc_entries.append((epub.Section(f'{part_label}: {part_title}'), []))
            spine_items.append(part_ch)

        body = md_body(BOOK_DIR / fname)
        html = f'<p class="chapter-num no-indent">{label}</p><h1>{title}</h1>{body}'
        ch = attach(make_chapter(
            f'{label}: {title}',
            f'chapter-{idx+1:02d}.xhtml',
            html,
        ))
        book.add_item(ch)
        spine_items.append(ch)

        # Add chapter under the current part section in TOC (or at top level)
        if toc_entries and isinstance(toc_entries[-1], tuple):
            toc_entries[-1][1].append(ch)
        else:
            toc_entries.append(ch)

    book.toc = toc_entries
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_ch, copy_ch, 'nav', *spine_items]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
