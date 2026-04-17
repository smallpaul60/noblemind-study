#!/usr/bin/env python3
"""Generate the EPUB for 'The Last Week of the Lamb'.

Source: markdown prologue/chapters/interlude/epilogue in this directory.
Cover: The_Last_Week_of_the_Lamb_Front_Cover_Mockup.png.

Output: The_Last_Week_of_the_Lamb.epub
"""

import re
from html import unescape as html_unescape
from pathlib import Path
import markdown
from ebooklib import epub

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "The_Last_Week_of_the_Lamb.epub"
COVER = BOOK_DIR / "The_Last_Week_of_the_Lamb_Front_Cover_Mockup.png"

TITLE = "The Last Week of the Lamb"
SUBTITLE = "The Passover Pattern Good Friday Missed"
AUTHOR = "Paul Hainline"

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
    color: #C87941;
    font-size: 0.85em;
    text-transform: uppercase;
    margin-top: 2em;
    margin-bottom: 0;
}
p { text-align: justify; text-indent: 1.4em; margin: 0 0 0.15em 0; }
p.no-indent, h1 + p, h2 + p, h3 + p, blockquote + p, hr + p { text-indent: 0; }
em { font-style: italic; }
strong { font-weight: 600; }

blockquote { margin: 0.9em 1.6em; font-style: italic; }
blockquote p { text-indent: 0; text-align: left; }

blockquote.scripture {
    border-left: 3px solid #D4A848;
    padding-left: 0.9em;
    margin: 0.9em 0.6em 0.9em 0.8em;
    font-style: italic;
}
blockquote.scripture p { text-indent: 0; text-align: left; margin-bottom: 0.2em; }
blockquote.scripture cite {
    display: block; font-style: normal; font-size: 0.88em; color: #555;
}

hr { border: none; text-align: center; margin: 1em 0; }
hr::before {
    content: "\\2022   \\2022   \\2022";
    color: #999; letter-spacing: 0.1em;
}

table {
    border-collapse: collapse; margin: 1em 0; width: 100%;
    font-size: 0.9em;
}
th, td {
    border: 1px solid #bbb; padding: 4pt 7pt; vertical-align: top;
    text-align: left;
}
th { background: #f5e8cc; font-weight: 600; }

.title-page { text-align: center; margin-top: 18%; }
.title-page h1 { font-size: 2em; font-weight: normal; letter-spacing: 1px; margin-bottom: 0.3em; }
.title-page .subtitle { font-style: italic; color: #4a4a4a; margin-bottom: 3em; }
.title-page .author { margin-bottom: 0.3em; }
.title-page .imprint { font-size: 0.85em; color: #777; letter-spacing: 2px; margin-top: 2em; }

.copyright-page { margin-top: 15%; text-align: center; font-size: 0.9em; color: #444; line-height: 1.75; }
.copyright-page p { margin-bottom: 0.9em; text-indent: 0; text-align: center; }

.part-page { text-align: center; margin-top: 30%; }
.part-page .part-num { letter-spacing: 0.2em; color: #D4A848; font-size: 0.9em; text-transform: uppercase; margin-bottom: 1em; }
.part-page .part-title { font-size: 2em; font-weight: normal; line-height: 1.15; margin-bottom: 0.6em; }
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
    html = markdown.markdown(text, extensions=['smarty', 'tables'])
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
    book.set_identifier('noblemind-last-week-of-the-lamb-2026')
    book.set_title(TITLE)
    book.set_language('en')
    book.add_author('Paul Hainline')
    book.add_author('Pam Hainline')
    book.add_metadata('DC', 'publisher', 'NobleMind Press')
    book.add_metadata('DC', 'description',
        'For seventeen centuries the church has placed the crucifixion on a '
        'Friday — but Friday gives you two nights in the tomb, not three. '
        'This book does not start with tradition. It starts with the text. '
        'Following the time markers the Gospel writers actually wrote — '
        '"the next day," "after two days," "six days before the Passover" — '
        'a different week emerges. Twelve chapters, a prologue, an '
        'interlude on the Hebrew calendar, and an epilogue, walking through '
        'the timeline of Passion Week with every assumption labeled and '
        'every Scripture shown in its place.')

    with open(COVER, 'rb') as f:
        book.set_cover('cover.png', f.read())

    css = epub.EpubItem(uid='style', file_name='style/default.css',
                        media_type='text/css', content=STYLE)
    book.add_item(css)

    def attach(ch):
        ch.add_item(css)
        return ch

    title_html = f'''
    <div class="title-page">
      <h1>{TITLE}</h1>
      <p class="subtitle no-indent">{SUBTITLE}</p>
      <p class="author no-indent">{AUTHOR}</p>
      <p class="imprint no-indent">NOBLEMIND PRESS</p>
    </div>
    '''
    title_ch = attach(make_chapter('Title', 'title.xhtml', title_html))
    book.add_item(title_ch)

    copy_html = f'''
    <div class="copyright-page">
      <p><strong>{TITLE}: {SUBTITLE}</strong></p>
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

    chapter_items = []    # for spine, in order
    toc_entries = []      # nested for nav
    current_part = None
    current_part_chapters = []

    def flush_part():
        nonlocal current_part, current_part_chapters
        if current_part is not None:
            toc_entries.append((epub.Section(current_part), current_part_chapters))
            current_part = None
            current_part_chapters = []

    for i, (kind, fname, label, title) in enumerate(SECTIONS):
        if kind == "part":
            flush_part()
            part_html = f'''
            <div class="part-page">
              <p class="part-num">{label}</p>
              <h1 class="part-title">{title}</h1>
            </div>'''
            safe = label.lower().replace(' ', '-')
            part_ch = attach(make_chapter(f'{label}: {title}', f'{safe}.xhtml', part_html))
            book.add_item(part_ch)
            chapter_items.append(part_ch)
            current_part = f'{label}: {title}'
            continue

        body = md_body(BOOK_DIR / fname)
        html = f'<p class="chapter-num">{label}</p><h1>{title}</h1>{body}'
        safe = Path(fname).stem.lower().replace('_', '-')[:40]
        ch = attach(make_chapter(
            f'{label}: {title}',
            f'{safe}.xhtml',
            html,
        ))
        book.add_item(ch)
        chapter_items.append(ch)

        if current_part is not None:
            current_part_chapters.append(ch)
        else:
            toc_entries.append(ch)

    flush_part()

    book.toc = toc_entries
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_ch, copy_ch, 'nav', *chapter_items]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
