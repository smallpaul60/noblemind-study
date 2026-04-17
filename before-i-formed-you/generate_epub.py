#!/usr/bin/env python3
"""Generate the EPUB for 'Before I Formed You'.

Source: markdown chapters + preface + closing in this directory.
Cover: cover_front.jpg (also used on the website).

Output: BeforeIFormedYou.epub
"""

import re
from pathlib import Path
from ebooklib import epub

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BeforeIFormedYou.epub"
COVER = BOOK_DIR / "cover_front.jpg"

CHAPTERS = [
    ("chapter1-before-i-formed-you.md", "Chapter One",   "El Roi: The God Who Sees You"),
    ("chapter2-before-i-formed-you.md", "Chapter Two",   "Fearfully and Wonderfully Made"),
    ("chapter3-before-i-formed-you.md", "Chapter Three", "A Basket in the River"),
    ("chapter4-before-i-formed-you.md", "Chapter Four",  "A Prayer Through Tears"),
    ("chapter5-before-i-formed-you.md", "Chapter Five",  "Gleaning at the Edges"),
    ("chapter6-before-i-formed-you.md", "Chapter Six",   "The Least Likely"),
    ("chapter7-before-i-formed-you.md", "Chapter Seven", "Be It Done to Me"),
    ("chapter8-before-i-formed-you.md", "Chapter Eight", "For Such a Time as This"),
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
    margin: 1.8em 0 0.6em;
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
p.no-indent, p.opening, h1 + p, p.chapter-num + h1 + p, hr + p {
    text-indent: 0;
}
em { font-style: italic; }
strong { font-weight: 600; }

blockquote {
    margin: 1em 2em;
    font-style: italic;
}
blockquote p { text-indent: 0; text-align: left; }

hr {
    border: none;
    text-align: center;
    margin: 1.2em 0;
}
hr::before {
    content: "\\2022   \\2022   \\2022";
    color: #999;
    letter-spacing: 0.1em;
}

.title-page { text-align: center; margin-top: 18%; }
.title-page h1 { font-size: 2em; font-weight: normal; letter-spacing: 1px; margin-bottom: 0.4em; }
.title-page .subtitle { font-style: italic; color: #4a4a4a; margin-bottom: 3em; }
.title-page .author { margin-bottom: 0.3em; }
.title-page .imprint { font-size: 0.85em; color: #777; letter-spacing: 2px; margin-top: 2em; }

.copyright-page { margin-top: 18%; text-align: center; font-size: 0.9em; color: #444; line-height: 1.75; }
.copyright-page p { margin-bottom: 0.9em; text-indent: 0; text-align: center; }

.preface-body p, .closing-body p { text-align: left; text-indent: 0; margin-bottom: 0.9em; }
"""


def md_to_html(text):
    """Minimal markdown → HTML for the specific subset used in these chapters.
    Paragraphs, italic, bold, horizontal rules."""
    text = text.strip()
    # Inline formatting
    def inline(s):
        s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
        s = s.replace('--', '&mdash;')
        return s

    # Smart-quote a paragraph body (simple pass — source already uses curly
    # quotes in prose, but guard against any stray straight quotes).
    def curly(s):
        s = re.sub(r'(^|[\s\(\[])"', r'\1&ldquo;', s)
        s = s.replace('"', '&rdquo;')
        s = re.sub(r"(^|[\s\(\[])'", r'\1&lsquo;', s)
        s = s.replace("'", '&rsquo;')
        return s

    parts = []
    for block in re.split(r'\n\s*\n', text):
        block = block.strip()
        if not block:
            continue
        if block == '---':
            parts.append('<hr/>')
            continue
        # Skip leftover headings (we supply our own H1)
        if block.startswith('# ') or block.startswith('## '):
            continue
        para = block.replace('\n', ' ')
        parts.append(f'<p>{inline(curly(para))}</p>')
    return '\n'.join(parts)


def md_body(path):
    text = path.read_text(encoding='utf-8')
    # Remove title + section H2 — we provide our own chapter header
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    text = re.sub(r'^##\s+.*$', '', text, count=1, flags=re.MULTILINE).strip()
    return md_to_html(text)


def make_chapter(title, file_name, body_html, extra_class=''):
    html = (
        f'<html><head><title>{title}</title>'
        f'<link rel="stylesheet" type="text/css" href="style/default.css"/></head>'
        f'<body class="{extra_class}">{body_html}</body></html>'
    )
    ch = epub.EpubHtml(title=title, file_name=file_name, lang='en')
    ch.content = html
    return ch


def main():
    book = epub.EpubBook()
    book.set_identifier('noblemind-before-i-formed-you-2026')
    book.set_title('Before I Formed You')
    book.set_language('en')
    book.add_author('Paul Hainline')
    book.add_author('Pam Hainline')
    book.add_metadata('DC', 'publisher', 'NobleMind Press')
    book.add_metadata('DC', 'description',
        'Written for the woman holding it right now — wherever she is, '
        'whatever she is facing. Eight chapters walk through the stories '
        'of women in Scripture who faced moments they did not choose: '
        'Hagar, Jochebed, Hannah, Ruth, Rahab, Mary, and Esther. Each '
        'carried a child whose purpose was larger than she could see.')

    # Cover
    with open(COVER, 'rb') as f:
        book.set_cover('cover.jpg', f.read())

    # Stylesheet
    css = epub.EpubItem(uid='style', file_name='style/default.css',
                        media_type='text/css', content=STYLE)
    book.add_item(css)

    def attach_css(ch):
        ch.add_item(css)
        return ch

    # --- Title page ---
    title_html = '''
    <div class="title-page">
      <h1>Before I Formed You</h1>
      <p class="subtitle no-indent">What God Says to the Woman Holding This Book</p>
      <p class="author no-indent">Paul &amp; Pam Hainline</p>
      <p class="imprint no-indent">NOBLEMIND PRESS</p>
    </div>
    '''
    title_ch = attach_css(make_chapter('Title', 'title.xhtml', title_html))
    book.add_item(title_ch)

    # --- Copyright page ---
    copy_html = '''
    <div class="copyright-page">
      <p><strong>Before I Formed You</strong></p>
      <p>Copyright &copy; 2026 Paul &amp; Pam Hainline.<br/>All rights reserved.</p>
      <p>Published by NobleMind Press<br/>noblemind.study</p>
      <p>All Scripture quotations are from the<br/>
        New American Standard Bible&reg; (NASB),<br/>
        &copy; 1960, 1971, 1977, 1995, 2020<br/>
        The Lockman Foundation.<br/>
        Used by permission. All rights reserved.<br/>
        www.lockman.org</p>
      <p>This booklet may be freely shared and distributed<br/>
         for the purpose of encouragement, teaching, and study.</p>
      <p>First Edition</p>
    </div>
    '''
    copy_ch = attach_css(make_chapter('Copyright', 'copyright.xhtml', copy_html))
    book.add_item(copy_ch)

    # --- Preface ---
    preface_body = md_body(BOOK_DIR / 'preface-before-i-formed-you.md')
    preface_html = f'<h1>Preface</h1>{preface_body}'
    preface_ch = attach_css(make_chapter('Preface', 'preface.xhtml', preface_html,
                                         extra_class='preface-body'))
    book.add_item(preface_ch)

    # --- Chapters ---
    chapter_items = []
    for idx, (fname, label, title) in enumerate(CHAPTERS, start=1):
        body = md_body(BOOK_DIR / fname)
        html = f'<p class="chapter-num">{label}</p><h1>{title}</h1>{body}'
        ch = attach_css(make_chapter(
            f'{label}: {title}',
            f'chapter-{idx:02d}.xhtml',
            html,
        ))
        book.add_item(ch)
        chapter_items.append(ch)

    # --- Closing ---
    closing_raw = (BOOK_DIR / 'closing-before-i-formed-you.md').read_text(encoding='utf-8')
    closing_raw = re.sub(r'^#\s+.*$', '', closing_raw, count=1, flags=re.MULTILINE).strip()
    closing_raw = re.sub(r'^##\s+(.*)$', '', closing_raw, count=1, flags=re.MULTILINE).strip()
    closing_body = md_to_html(closing_raw)
    closing_html = f'<h1>You Are Not Alone</h1>{closing_body}'
    closing_ch = attach_css(make_chapter('You Are Not Alone', 'closing.xhtml',
                                         closing_html, extra_class='closing-body'))
    book.add_item(closing_ch)

    # --- Spine / nav ---
    book.toc = [preface_ch, *chapter_items, closing_ch]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_ch, copy_ch, 'nav',
                  preface_ch, *chapter_items, closing_ch]

    epub.write_epub(str(OUTPUT), book)
    print(f'Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
