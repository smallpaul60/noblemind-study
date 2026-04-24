#!/usr/bin/env python3
"""Generate the EPUB for 'Why Do You Delay?'.

Structure:
  cover  /  title  /  copyright  /  epigraph  /  nav  /
  preface  /
  Part One page  +  Ch 1-5  /
  Part Two page  +  Ch 6-8  /
  Part Three page  +  Ch 9-13  /
  epilogue.

Output: Why_Do_You_Delay.epub
"""

from pathlib import Path
from ebooklib import epub

from _book_source import (
    parse_book, md_body_to_html,
    TITLE, SUBTITLE, AUTHOR,
)

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_Do_You_Delay.epub"
COVER    = BOOK_DIR / "cover_front.jpg"


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

.part-page {
    text-align: center;
    margin-top: 30%;
}
.part-page .part-label {
    font-size: 0.85em; letter-spacing: 0.22em; color: #8B6914;
    text-transform: uppercase; margin-bottom: 1em;
}
.part-page h1 {
    font-size: 1.8em; font-weight: normal; line-height: 1.25;
    margin: 0 0.5em 0.5em;
}
.part-page .part-rule {
    width: 2em; height: 1px; background: #bbb; margin: 0.8em auto;
}
.part-page .part-intro {
    font-style: italic; color: #3a3a3a; max-width: 28em;
    margin: 1em auto; text-align: left; line-height: 1.7;
}
.part-page .part-intro p { text-indent: 0; }
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
    book_data = parse_book()
    print(f'Building EPUB for "{TITLE}"...')
    print(f"  Parsed: {len(book_data['chapters'])} chapters in {len(book_data['parts'])} parts")

    book = epub.EpubBook()
    book.set_identifier('noblemind-why-do-you-delay-2026')
    book.set_title(TITLE)
    book.set_language('en')
    book.add_author(AUTHOR)
    book.add_metadata('DC', 'publisher', 'NobleMind Press')
    book.add_metadata('DC', 'description',
        'Is baptism really necessary? The question has been asked in churches, '
        'Bible studies, and living room conversations for generations. This book '
        'looks at what the Lord and His apostles actually taught, what the early '
        'church actually did, and the common objections raised in our time — '
        'letting Scripture, and not tradition, be the final word. Thirteen '
        'chapters across three parts, drawn from the full witness of the '
        'New Testament, ending at the question Ananias asked Saul of Tarsus: '
        'why do you delay?')

    with open(COVER, 'rb') as f:
        book.set_cover('cover.jpg', f.read())

    css = epub.EpubItem(uid='style', file_name='style/default.css',
                        media_type='text/css', content=STYLE)
    book.add_item(css)

    def attach(ch):
        ch.add_item(css)
        return ch

    # --- Title page ---
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

    # --- Copyright page ---
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

    # --- Epigraph ---
    epi_html = '''
    <div class="epigraph-page">
      <blockquote>
        <p>&#8220;Now why do you delay? Get up and be baptized,<br/>
        and wash away your sins, calling on His name.&#8221;</p>
        <cite>&#8212; Acts 22:16</cite>
      </blockquote>
    </div>
    '''
    epi_ch = attach(make_chapter('Epigraph', 'epigraph.xhtml', epi_html))
    book.add_item(epi_ch)

    # --- Preface ---
    preface_body = md_body_to_html(book_data['preface_md'])
    preface_html = f'<p class="chapter-num">Preface</p>{preface_body}'
    preface_ch = attach(make_chapter('Preface', 'preface.xhtml', preface_html))
    book.add_item(preface_ch)

    # --- Parts + chapters ---
    part_sections = []  # for TOC nesting
    chapter_items_flat = [preface_ch]
    for p_idx, part in enumerate(book_data['parts'], start=1):
        # Part page
        part_intro = md_body_to_html(part['intro_md'])
        part_html = f'''
        <div class="part-page">
          <p class="part-label">{part['label']}</p>
          <h1>{part['title']}</h1>
          <div class="part-rule"></div>
          <div class="part-intro">{part_intro}</div>
        </div>
        '''
        part_ch = attach(make_chapter(
            f'{part["label"]}: {part["title"]}',
            f'part-{p_idx}.xhtml',
            part_html,
        ))
        book.add_item(part_ch)
        chapter_items_flat.append(part_ch)

        # Chapters of this part
        ch_items = [part_ch]
        for ch in part['chapters']:
            body = md_body_to_html(ch['md'])
            html = f'<p class="chapter-num">{ch["label"]}</p><h1>{ch["title"]}</h1>{body}'
            ch_item = attach(make_chapter(
                f'Chapter {ch["num"]}: {ch["title"]}',
                f'chapter-{ch["num"]:02d}.xhtml',
                html,
            ))
            book.add_item(ch_item)
            chapter_items_flat.append(ch_item)
            ch_items.append(ch_item)

        # Grouped under part for TOC nesting
        part_sections.append(
            (epub.Section(f'{part["label"]}: {part["title"]}'), ch_items)
        )

    # --- Epilogue ---
    epi_body_html = md_body_to_html(book_data['epilogue_md'])
    epilogue_html = (
        f'<p class="chapter-num">Epilogue</p>'
        f'<h1>{book_data["epilogue_title"]}</h1>'
        f'{epi_body_html}'
    )
    epilogue_ch = attach(make_chapter(
        f'Epilogue: {book_data["epilogue_title"]}',
        'epilogue.xhtml',
        epilogue_html,
    ))
    book.add_item(epilogue_ch)
    chapter_items_flat.append(epilogue_ch)

    # --- Nested TOC ---
    book.toc = [preface_ch, *part_sections, epilogue_ch]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_ch, copy_ch, epi_ch, 'nav',
                  *chapter_items_flat]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT.name}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
