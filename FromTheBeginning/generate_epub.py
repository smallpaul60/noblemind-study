#!/usr/bin/env python3
"""Generate the EPUB for 'From the Beginning: The Gospel from the Ground Up'.

Source: markdown chapters + dedication in this directory.
Cover: cover_front.jpg.

Output: FromTheBeginning.epub
"""

import re
from html import unescape as html_unescape
from pathlib import Path
import markdown
from ebooklib import epub

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "FromTheBeginning.epub"
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
h2 {
    font-size: 1.15em;
    font-weight: 600;
    margin: 1.4em 0 0.4em;
}
h3 {
    font-size: 1em;
    font-weight: 600;
    font-style: italic;
    margin: 1.2em 0 0.35em;
    color: #333;
}
p.chapter-num {
    text-align: center;
    letter-spacing: 0.2em;
    color: #8B6914;
    font-size: 0.85em;
    text-transform: uppercase;
    margin-top: 2em;
    margin-bottom: 0;
}
p {
    text-align: justify;
    text-indent: 1.4em;
    margin: 0 0 0.15em 0;
}
p.no-indent, p.chapter-num + h1 + p, h1 + p, h2 + p, h3 + p, blockquote + p, hr + p {
    text-indent: 0;
}
em { font-style: italic; }
strong { font-weight: 600; }

blockquote {
    margin: 0.9em 1.6em;
    font-style: italic;
}
blockquote p { text-indent: 0; text-align: left; }

blockquote.scripture {
    border-left: 3px solid #8B6914;
    padding-left: 0.9em;
    margin: 0.9em 0.6em 0.9em 0.8em;
    font-style: italic;
}
blockquote.scripture p { text-indent: 0; text-align: left; margin-bottom: 0.2em; }
blockquote.scripture cite {
    display: block; font-style: normal; font-size: 0.88em; color: #555;
}

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

.title-page { text-align: center; margin-top: 18%; }
.title-page h1 { font-size: 2em; font-weight: normal; letter-spacing: 1px; margin-bottom: 0.3em; }
.title-page .subtitle { font-style: italic; color: #4a4a4a; margin-bottom: 3em; }
.title-page .author { margin-bottom: 0.3em; }
.title-page .imprint { font-size: 0.85em; color: #777; letter-spacing: 2px; margin-top: 2em; }

.copyright-page { margin-top: 15%; text-align: center; font-size: 0.9em; color: #444; line-height: 1.75; }
.copyright-page p { margin-bottom: 0.9em; text-indent: 0; text-align: center; }

.part-page { text-align: center; margin-top: 30%; }
.part-page .part-num { letter-spacing: 0.2em; color: #8B6914; font-size: 0.9em; text-transform: uppercase; margin-bottom: 1em; }
.part-page .part-title { font-size: 2em; font-weight: normal; line-height: 1.15; margin-bottom: 0.6em; }
.part-page .part-subtitle { font-style: italic; color: #555; }

.dedication-body p { text-align: left; text-indent: 0; margin-bottom: 0.8em; }
"""


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
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    html = markdown.markdown(text, extensions=['smarty'])
    return convert_scripture_blockquotes(html)


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
    book.set_identifier('noblemind-from-the-beginning-2026')
    book.set_title('From the Beginning: The Gospel from the Ground Up')
    book.set_language('en')
    book.add_author('Paul Hainline')
    book.add_author('Pam Hainline')
    book.add_metadata('DC', 'publisher', 'NobleMind Press')
    book.add_metadata('DC', 'description',
        'The gospel from the ground up — starting from zero, with no church '
        'background required. Ten chapters walk from creation, through the '
        'cross and the empty tomb, into the life that follows. Written for '
        'the seeker, the skeptic, and anyone ready to open the Book for the '
        'first time.')

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
      <h1>From the Beginning</h1>
      <p class="subtitle no-indent">The Gospel from the Ground Up</p>
      <p class="author no-indent">Paul &amp; Pam Hainline</p>
      <p class="imprint no-indent">NOBLEMIND PRESS</p>
    </div>
    '''
    title_ch = attach(make_chapter('Title', 'title.xhtml', title_html))
    book.add_item(title_ch)

    copy_html = '''
    <div class="copyright-page">
      <p><strong>From the Beginning: The Gospel from the Ground Up</strong></p>
      <p>Copyright &copy; 2026 Paul &amp; Pam Hainline.<br/>All rights reserved.</p>
      <p>Published by NobleMind Press<br/>noblemind.study</p>
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

    dedication_body = md_body(BOOK_DIR / 'FromTheBeginning_Dedication.md')
    dedication_html = f'<h1>To the Seeker</h1>{dedication_body}'
    dedication_ch = attach(make_chapter('To the Seeker', 'dedication.xhtml',
                                        dedication_html, body_class='dedication-body'))
    book.add_item(dedication_ch)

    toc_entries = [dedication_ch]
    spine_items = []

    for idx, (fname, label, title) in enumerate(CHAPTERS):
        if idx in PART_STRUCTURE:
            part_label, part_title, part_subtitle = PART_STRUCTURE[idx]
            part_html = f'''
            <div class="part-page">
              <p class="part-num">{part_label}</p>
              <h1 class="part-title">{part_title}</h1>
              <p class="part-subtitle">{part_subtitle}</p>
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
        html = f'<p class="chapter-num">{label}</p><h1>{title}</h1>{body}'
        ch = attach(make_chapter(
            f'{label}: {title}',
            f'chapter-{idx+1:02d}.xhtml',
            html,
        ))
        book.add_item(ch)
        spine_items.append(ch)

        # Add chapter under the current part in TOC
        if toc_entries and isinstance(toc_entries[-1], tuple):
            toc_entries[-1][1].append(ch)
        else:
            toc_entries.append(ch)

    book.toc = toc_entries
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_ch, copy_ch, 'nav',
                  dedication_ch, *spine_items]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
