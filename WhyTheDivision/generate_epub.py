#!/usr/bin/env python3
"""Generate the EPUB for 'Why the Division Among Brethren?'.

Structure:
  title  /  copyright  /  epigraph  /  nav  /
  preface  /
  Part One page  +  Ch 1-2  /
  Part Two page  +  Ch 3-5  /
  Part Three page +  Ch 6-9  /
  Part Four page +  Ch 10-11.

No cover image (this booklet is typographic-only).
The Scripture index is included as a back-matter chapter.

Output: Why_The_Division.epub
"""

from pathlib import Path
from ebooklib import epub

from _book_source import (
    parse_book, md_body_to_html,
    TITLE, SUBTITLE, AUTHOR, PUBLISHER,
)
from _scripture_index import build_index

BOOK_DIR = Path(__file__).parent
OUTPUT   = BOOK_DIR / "Why_The_Division.epub"

ACCENT = "#3F5F3F"


STYLE = f"""
body {{
    font-family: Georgia, 'EB Garamond', serif;
    line-height: 1.65;
    color: #1a1a1a;
    margin: 1em;
}}
h1 {{
    text-align: center;
    font-size: 1.7em;
    font-weight: normal;
    line-height: 1.25;
    margin: 1.5em 0 0.5em;
}}
h2 {{
    font-size: 1.15em;
    font-weight: 600;
    margin: 1.4em 0 0.4em;
}}
h3 {{
    font-size: 1em;
    font-weight: 600;
    font-style: italic;
    margin: 1.2em 0 0.35em;
    color: #333;
}}
p.chapter-num {{
    text-align: center;
    letter-spacing: 0.2em;
    color: {ACCENT};
    font-size: 0.85em;
    text-transform: uppercase;
    margin-top: 2em;
    margin-bottom: 0;
}}
p {{
    text-align: justify;
    text-indent: 1.4em;
    margin: 0 0 0.15em 0;
}}
p.no-indent, h1 + p, h2 + p, h3 + p, blockquote + p, hr + p {{
    text-indent: 0;
}}
em {{ font-style: italic; }}
strong {{ font-weight: 600; }}

blockquote {{
    margin: 0.9em 1.6em;
    font-style: italic;
}}
blockquote p {{ text-indent: 0; text-align: left; }}

blockquote.scripture {{
    border-left: 3px solid {ACCENT};
    padding-left: 0.9em;
    margin: 0.9em 0.6em 0.9em 0.8em;
    font-style: italic;
}}
blockquote.scripture p {{ text-indent: 0; text-align: left; margin-bottom: 0.2em; }}
blockquote.scripture cite {{
    display: block; font-style: normal; font-size: 0.88em; color: #555;
}}

hr {{
    border: none; text-align: center; margin: 1em 0;
}}
hr::before {{
    content: "\\2022   \\2022   \\2022";
    color: #999; letter-spacing: 0.1em;
}}

.title-page {{ text-align: center; margin-top: 18%; }}
.title-page h1 {{ font-size: 1.9em; font-weight: normal; letter-spacing: 1px; margin-bottom: 0.4em; }}
.title-page .subtitle {{ font-style: italic; color: #4a4a4a; margin-bottom: 3em; padding: 0 0.5em; }}
.title-page .accent-rule {{ width: 2.5em; height: 1px; background: #88a888; margin: 1em auto; }}
.title-page .author {{ margin-bottom: 0.3em; letter-spacing: 0.04em; }}
.title-page .imprint {{ font-size: 0.85em; color: #777; letter-spacing: 2px; margin-top: 2em; }}

.copyright-page {{ margin-top: 15%; text-align: center; font-size: 0.9em; color: #444; line-height: 1.75; }}
.copyright-page p {{ margin-bottom: 0.9em; text-indent: 0; text-align: center; }}

.epigraph-page {{ text-align: center; margin-top: 40%; }}
.epigraph-page blockquote {{ border: none; padding: 0; margin: 0 1em; font-style: italic; }}
.epigraph-page blockquote p {{ font-size: 1.2em; margin-bottom: 0.8em; text-indent: 0; }}
.epigraph-page blockquote cite {{ display: block; font-style: normal; color: #555; font-size: 0.95em; }}

.part-page {{
    text-align: center;
    margin-top: 30%;
}}
.part-page .part-label {{
    font-size: 0.85em; letter-spacing: 0.22em; color: {ACCENT};
    text-transform: uppercase; margin-bottom: 1em;
}}
.part-page h1 {{
    font-size: 1.8em; font-weight: normal; line-height: 1.25;
    margin: 0 0.5em 0.5em;
}}
.part-page .part-rule {{
    width: 2em; height: 1px; background: #bbb; margin: 0.8em auto;
}}
.part-page .part-intro {{
    font-style: italic; color: #3a3a3a; max-width: 28em;
    margin: 1em auto; text-align: left; line-height: 1.7;
}}
.part-page .part-intro p {{ text-indent: 0; }}

.scripture-index h2 {{
    font-size: 1.1em; font-weight: 700;
    margin-top: 1.4em; margin-bottom: 0.3em; color: #1a1a1a;
}}
.scripture-index .index-entry {{
    margin: 0.2em 0 0.2em 1em;
    font-size: 0.95em;
}}
.scripture-index .index-ref {{ font-weight: 600; color: #1a1a1a; }}
.scripture-index .index-chapters {{
    color: #555; font-style: italic; font-size: 0.9em; margin-left: 0.5em;
}}
.scripture-index .index-intro {{
    text-align: center; font-style: italic; color: #555;
    font-size: 0.92em; margin: 0.5em 1em 1.5em;
}}
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


def build_scripture_index_html():
    idx = build_index()
    rows = []
    for group in idx:
        rows.append(f'<h2>{group["book"]}</h2>')
        for e in group["entries"]:
            verse_part = ""
            if e["verses"]:
                verse_part = ":" + e["verses"].replace('-', '–')
            ref = f'{group["book"]} {e["chapter"]}{verse_part}'
            locs = ", ".join(
                "Pref" if n == 0 else f"Ch. {n}"
                for n in e["locations"]
            )
            rows.append(
                f'<div class="index-entry">'
                f'<span class="index-ref">{ref}</span>'
                f'<span class="index-chapters">{locs}</span>'
                f'</div>'
            )
    return "\n".join(rows)


def main():
    book_data = parse_book()
    print(f'Building EPUB for "{TITLE}"...')
    print(f"  Parsed: {len(book_data['chapters'])} chapters in "
          f"{len(book_data['parts'])} parts")

    book = epub.EpubBook()
    book.set_identifier('noblemind-why-the-division-2026')
    book.set_title(TITLE)
    book.set_language('en')
    book.add_author(AUTHOR)
    book.add_metadata('DC', 'publisher', PUBLISHER)
    book.add_metadata('DC', 'description',
        'A short, patient look at the institutional/non-institutional '
        'division among churches of Christ. Both positions stated at '
        'their best; relevant Scriptures walked text by text; the four '
        'specific questions of the division (church-supported '
        'institutions, sponsoring church arrangements, the scope of the '
        'treasury in benevolence, fellowship halls) examined alongside '
        'the underlying hermeneutical question that drives all four. '
        'Eleven chapters across four parts, with a Scripture index.')

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
      <div class="accent-rule"></div>
      <p class="author no-indent">{AUTHOR}</p>
      <p class="imprint no-indent">NOBLEMIND PRESS</p>
    </div>
    '''
    title_ch = attach(make_chapter('Title', 'title.xhtml', title_html))
    book.add_item(title_ch)

    # --- Copyright page ---
    copy_html = f'''
    <div class="copyright-page">
      <p><strong>{TITLE}</strong><br/><em>{SUBTITLE}</em></p>
      <p>Copyright &copy; 2026 {AUTHOR}.<br/>All rights reserved.</p>
      <p>Published by {PUBLISHER}<br/>noblemind.study</p>
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
        <p><em>A position must stand or fall based<br/>on what the Scriptures actually teach.</em></p>
        <cite>&#8212; the thesis of this booklet</cite>
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
    part_sections = []
    chapter_items_flat = [preface_ch]
    for p_idx, part in enumerate(book_data['parts'], start=1):
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

        part_sections.append(
            (epub.Section(f'{part["label"]}: {part["title"]}'), ch_items)
        )

    # --- Scripture Index ---
    idx_html = (
        '<h1>Scripture Index</h1>'
        '<p class="index-intro">References are listed in the canonical order '
        'of the Bible. The chapter(s) of this booklet in which each reference '
        'appears are given as &ldquo;Ch.&rdquo; (chapter) or &ldquo;Pref&rdquo; (Preface).</p>'
        + build_scripture_index_html()
    )
    idx_ch = attach(make_chapter(
        'Scripture Index', 'scripture-index.xhtml',
        idx_html, body_class='scripture-index',
    ))
    book.add_item(idx_ch)
    chapter_items_flat.append(idx_ch)

    # --- Nested TOC ---
    book.toc = [preface_ch, *part_sections, idx_ch]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = [title_ch, copy_ch, epi_ch, 'nav', *chapter_items_flat]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT.name}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
