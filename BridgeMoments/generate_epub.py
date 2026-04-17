#!/usr/bin/env python3
"""Generate the EPUB for 'Bridge Moments'.

Extracts chapter + appendix content from the existing HTML files (same
source the reader PDF uses), groups chapters under their four Parts in the
nav, and embeds the composed cover as the EPUB cover.

Output: BridgeMoments.epub
"""

from pathlib import Path
from bs4 import BeautifulSoup
from ebooklib import epub

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BridgeMoments.epub"
COVER = BOOK_DIR / "cover_front.jpg"

TITLE = "Bridge Moments"
SUBTITLE = "Making the Most of Every Opportunity"
TAGLINE = "A Bible Study on Conversational Evangelism"
AUTHOR = "Paul Hainline"

# Shares the chapter list with generate_pdf.py.
from generate_pdf import CHAPTERS, APPENDICES, PARTS, extract_content


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
    margin: 1.2em 0 0.4em;
}
h2 { font-size: 1.15em; font-weight: 600; margin: 1.4em 0 0.4em; }
h3 { font-size: 1em; font-weight: 600; font-style: italic; margin: 1.2em 0 0.35em; color: #333; }

p.chapter-num {
    text-align: center;
    letter-spacing: 0.2em;
    color: #B8883E;
    font-size: 0.85em;
    text-transform: uppercase;
    margin-top: 1.6em;
    margin-bottom: 0;
}
p.chapter-subtitle {
    text-align: center;
    font-style: italic;
    color: #555;
    margin-top: 0.4em;
    text-indent: 0;
}

p {
    text-align: justify;
    text-indent: 1.4em;
    margin: 0 0 0.15em 0;
}
p.no-indent, h1 + p, h2 + p, h3 + p, blockquote + p, hr + p,
.divider + p, section.epigraph + p, .chapter-purpose + p { text-indent: 0; }
em { font-style: italic; }
strong { font-weight: 600; }

section.epigraph {
    margin: 1em 1em 1.2em 1em;
    text-align: center;
}
section.epigraph blockquote {
    border: none; padding: 0; margin: 0 0 0.3em 0;
    font-style: italic;
}
section.epigraph blockquote p { text-indent: 0; text-align: center; margin: 0; }
section.epigraph cite {
    display: block; font-style: normal;
    font-size: 0.9em; color: #555;
}

.chapter-purpose {
    margin: 0.9em 0.4em 1em 0.4em;
    padding-left: 0.8em;
    border-left: 3px solid #B8883E;
    font-size: 0.95em; font-style: italic;
    color: #3a3a3a; line-height: 1.5;
    text-indent: 0;
}

blockquote.scripture {
    border-left: 3px solid #B8883E;
    padding-left: 0.9em;
    margin: 0.9em 0.6em 0.9em 0.8em;
    font-style: italic;
}
blockquote.scripture p { text-indent: 0; text-align: left; margin-bottom: 0.2em; }
blockquote.scripture cite {
    display: block; font-style: normal; font-size: 0.88em; color: #555;
}

.divider {
    text-align: center; margin: 1em 0;
    color: #bbb; letter-spacing: 0.1em; font-size: 0.85em;
}

.key-scriptures {
    margin: 1em 0.4em;
    padding: 0.7em 0.9em;
    background: #fbf6ea;
    border-left: 3px solid #B8883E;
    font-size: 0.95em;
}
.key-scriptures h3 {
    font-size: 0.95em; font-weight: 600;
    margin: 0 0 0.4em 0; color: #8b5e2b; font-style: normal;
}

table {
    border-collapse: collapse; margin: 1em 0; width: 100%;
    font-size: 0.88em;
}
th, td {
    border: 1px solid #bbb; padding: 4pt 6pt; vertical-align: top;
    text-align: left;
}
th { background: #f4ead2; font-weight: 600; }

.title-page { text-align: center; margin-top: 15%; }
.title-page h1 { font-size: 2em; font-weight: normal; letter-spacing: 1px; margin-bottom: 0.4em; }
.title-page .subtitle { font-style: italic; color: #4a4a4a; margin-bottom: 0.3em; }
.title-page .tagline { font-style: italic; color: #666; font-size: 0.9em; margin-bottom: 3em; }
.title-page .author { margin-bottom: 0.3em; }
.title-page .imprint { font-size: 0.85em; color: #777; letter-spacing: 2px; margin-top: 2em; }

.copyright-page { margin-top: 15%; text-align: center; font-size: 0.9em; color: #444; line-height: 1.75; }
.copyright-page p { margin-bottom: 0.9em; text-indent: 0; text-align: center; }

.part-page { text-align: center; margin-top: 28%; }
.part-page .part-num {
    letter-spacing: 0.2em; color: #B8883E;
    font-size: 0.9em; text-transform: uppercase; margin-bottom: 1em;
}
.part-page .part-title {
    font-size: 1.8em; font-weight: normal; line-height: 1.2;
}
"""


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
    book.set_identifier('noblemind-bridge-moments-2026')
    book.set_title(TITLE)
    book.set_language('en')
    book.add_author(AUTHOR)
    book.add_metadata('DC', 'publisher', 'NobleMind Press')
    book.add_metadata('DC', 'description',
        'A Bible study on conversational evangelism grounded in '
        'Colossians 4:5–6. Twenty chapters across four parts examine the '
        'power of words, the encounters of Jesus, the pattern continued '
        'in the book of Acts, and the daily practice of living with '
        'bridge-moment eyes — noticing and using the openings God gives '
        'us in ordinary conversation.')

    with open(COVER, 'rb') as f:
        book.set_cover('cover.jpg', f.read())

    css = epub.EpubItem(uid='style', file_name='style/default.css',
                        media_type='text/css', content=STYLE)
    book.add_item(css)

    def attach(ch):
        ch.add_item(css)
        return ch

    # Title page
    title_html = f'''
    <div class="title-page">
      <h1>{TITLE}</h1>
      <p class="subtitle no-indent">{SUBTITLE}</p>
      <p class="tagline no-indent">{TAGLINE}</p>
      <p class="author no-indent">{AUTHOR}</p>
      <p class="imprint no-indent">NOBLEMIND PRESS</p>
    </div>
    '''
    title_ch = attach(make_chapter('Title', 'title.xhtml', title_html))
    book.add_item(title_ch)

    # Copyright
    copy_html = f'''
    <div class="copyright-page">
      <p><strong>{TITLE}: {SUBTITLE}</strong></p>
      <p>{TAGLINE}<br/>Grounded in Colossians 4:5&ndash;6</p>
      <p>Copyright &copy; 2026 {AUTHOR}.<br/>All rights reserved.</p>
      <p>Published by NobleMind Press<br/>noblemind.study</p>
      <p>All Scripture quotations are from the<br/>
        New American Standard Bible&reg; (NASB),<br/>
        &copy; 1960, 1971, 1977, 1995, 2020<br/>
        The Lockman Foundation.<br/>
        Used by permission. All rights reserved.<br/>
        www.lockman.org</p>
      <p>First Edition</p>
    </div>
    '''
    copy_ch = attach(make_chapter('Copyright', 'copyright.xhtml', copy_html))
    book.add_item(copy_ch)

    # Chapters grouped under Parts, with Part divider pages
    spine_items = [title_ch, copy_ch]
    toc_entries = []
    current_part_num = None
    current_part_kids = None

    def flush_part():
        nonlocal current_part_num, current_part_kids
        if current_part_num is not None:
            toc_entries.append(
                (epub.Section(f'Part {current_part_num}: {PARTS[current_part_num]}'),
                 current_part_kids)
            )
            current_part_num = None
            current_part_kids = None

    for entry in CHAPTERS:
        fname, label, title, part_num, part_title, subtitle = entry

        if part_num != current_part_num:
            flush_part()
            # Build a part divider page
            part_html = f'''
            <div class="part-page">
              <p class="part-num">Part {part_num}</p>
              <h1 class="part-title">{part_title}</h1>
            </div>'''
            part_ch = attach(make_chapter(
                f'Part {part_num}: {part_title}',
                f'part-{part_num}.xhtml',
                part_html,
            ))
            book.add_item(part_ch)
            spine_items.append(part_ch)
            current_part_num = part_num
            current_part_kids = []

        content = extract_content(BOOK_DIR / fname)
        subtitle_html = (
            f'<p class="chapter-subtitle no-indent"><em>{subtitle}</em></p>'
            if subtitle else ""
        )
        body = (
            f'<p class="chapter-num">{label}</p>'
            f'<h1>{title}</h1>{subtitle_html}{content}'
        )
        ch_num = int(label.split()[-1])
        ch = attach(make_chapter(
            f'{label}: {title}',
            f'chapter-{ch_num:02d}.xhtml',
            body,
        ))
        book.add_item(ch)
        spine_items.append(ch)
        current_part_kids.append(ch)

    flush_part()

    # Appendices
    appendix_items = []
    for i, (fname, label, title) in enumerate(APPENDICES, start=1):
        content = extract_content(BOOK_DIR / fname)
        body = f'<p class="chapter-num">{label}</p><h1>{title}</h1>{content}'
        ch = attach(make_chapter(
            f'{label}: {title}',
            f'appendix-{i}.xhtml',
            body,
        ))
        book.add_item(ch)
        spine_items.append(ch)
        appendix_items.append(ch)
    toc_entries.append((epub.Section('Appendices'), appendix_items))

    book.toc = toc_entries
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_ch, copy_ch, 'nav', *spine_items[2:]]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
