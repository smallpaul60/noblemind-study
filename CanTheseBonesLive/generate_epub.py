#!/usr/bin/env python3
"""Generate the EPUB for 'Can These Bones Live?'.

Source: markdown chapters + appendices in this directory.
Cover: cover_front.jpg.

Output: CanTheseBonesLive.epub
"""

import re
from pathlib import Path
import markdown
from ebooklib import epub

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "CanTheseBonesLive.epub"
COVER = BOOK_DIR / "cover_front.jpg"

TITLE = "Can These Bones Live?"
SUBTITLE = "How the Word and the Spirit Make Dead Things Live"
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
p.no-indent, h1 + p, h2 + p, h3 + p, blockquote + p, hr + p {
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
    border: none; text-align: center; margin: 1em 0;
}
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
th { background: #f0ece0; font-weight: 600; }

.title-page { text-align: center; margin-top: 18%; }
.title-page h1 { font-size: 2em; font-weight: normal; letter-spacing: 1px; margin-bottom: 0.3em; }
.title-page .subtitle { font-style: italic; color: #4a4a4a; margin-bottom: 3em; }
.title-page .author { margin-bottom: 0.3em; }
.title-page .imprint { font-size: 0.85em; color: #777; letter-spacing: 2px; margin-top: 2em; }

.copyright-page { margin-top: 15%; text-align: center; font-size: 0.9em; color: #444; line-height: 1.75; }
.copyright-page p { margin-bottom: 0.9em; text-indent: 0; text-align: center; }

.epigraph-page { text-align: center; margin-top: 40%; }
.epigraph-page blockquote { border: none; padding: 0; margin: 0 1em; font-style: italic; }
.epigraph-page blockquote p { font-size: 1.2em; margin-bottom: 0.8em; text-indent: 0; }
.epigraph-page blockquote cite { display: block; font-style: normal; color: #555; font-size: 0.95em; }
"""


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
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    text = re.sub(r'^##\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    text = promote_scripture_paragraphs(text)
    html = markdown.markdown(text, extensions=['smarty', 'tables'])
    return lift_citation_to_cite(html)


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
    book.set_identifier('noblemind-can-these-bones-live-2026')
    book.set_title(TITLE)
    book.set_language('en')
    book.add_author(AUTHOR)
    book.add_metadata('DC', 'publisher', 'NobleMind Press')
    book.add_metadata('DC', 'description',
        'God showed Ezekiel a valley of dry bones and asked the one question '
        'only God can answer: can these live? The answer, then and now, is '
        'the same — and it comes by the same means. The word of God gives '
        'form. The Spirit of God gives life. Together, and only together, '
        'they raise the dead. Eleven chapters trace that pattern from Eden '
        'through the prophets, into the ministry of Jesus, out through the '
        'church of Acts, and forward to the last page of Revelation.')

    with open(COVER, 'rb') as f:
        book.set_cover('cover.jpg', f.read())

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
      <p>Copyright &copy; 2026 {AUTHOR}.<br/>All rights reserved.</p>
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

    epi_html = '''
    <div class="epigraph-page">
      <blockquote>
        <p>“Son of man, can these bones live?”</p>
        <cite>— Ezekiel 37:3</cite>
      </blockquote>
    </div>
    '''
    epi_ch = attach(make_chapter('Epigraph', 'epigraph.xhtml', epi_html))
    book.add_item(epi_ch)

    chapter_items = []
    for idx, (fname, label, title) in enumerate(CHAPTERS, start=1):
        body = md_body(BOOK_DIR / fname)
        html = f'<p class="chapter-num">{label}</p><h1>{title}</h1>{body}'
        ch = attach(make_chapter(
            f'{label}: {title}',
            f'chapter-{idx:02d}.xhtml',
            html,
        ))
        book.add_item(ch)
        chapter_items.append(ch)

    appendix_items = []
    for idx, (fname, label, title) in enumerate(APPENDICES, start=1):
        body = md_body(BOOK_DIR / fname)
        html = f'<p class="chapter-num">{label}</p><h1>{title}</h1>{body}'
        ch = attach(make_chapter(
            f'{label}: {title}',
            f'appendix-{idx}.xhtml',
            html,
        ))
        book.add_item(ch)
        appendix_items.append(ch)

    book.toc = [
        *chapter_items,
        (epub.Section('Appendices'), appendix_items),
    ]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_ch, copy_ch, epi_ch, 'nav',
                  *chapter_items, *appendix_items]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
