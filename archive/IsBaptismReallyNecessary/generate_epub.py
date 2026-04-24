#!/usr/bin/env python3
"""Generate EPUB for 'Is Baptism Really Necessary?'"""

from ebooklib import epub
import re

# Read the markdown source
with open('is-baptism-really-necessary.md', 'r') as f:
    md = f.read()

book = epub.EpubBook()

# Metadata
book.set_identifier('noblemind-baptism-study-2026')
book.set_title('Is Baptism Really Necessary?')
book.set_language('en')
book.add_author('Paul Hainline')
book.add_metadata('DC', 'publisher', 'NobleMind Press')
book.add_metadata('DC', 'description',
    'A comprehensive, Scripture-driven examination of baptism — '
    'what Jesus commanded, what the apostles taught, what the early '
    'church did in every conversion, and honest answers to every '
    'common objection.')

# Cover image
with open('Is_Baptism_Really_Necessary_Cover.png', 'rb') as f:
    cover_data = f.read()
book.set_cover('cover.png', cover_data)

# Stylesheet
style = '''
body {
    font-family: Georgia, 'EB Garamond', serif;
    line-height: 1.6;
    color: #1a1a1a;
    margin: 1em;
}
h1 {
    text-align: center;
    font-size: 1.8em;
    font-weight: normal;
    margin: 2em 0 0.5em;
}
h2 {
    text-align: center;
    font-size: 1.3em;
    font-weight: normal;
    margin: 2em 0 1em;
    letter-spacing: 0.5px;
}
p {
    text-align: justify;
    text-indent: 1.5em;
    margin: 0 0 0.5em 0;
}
p.no-indent {
    text-indent: 0;
}
p.opening {
    text-indent: 0;
}
p.prayer {
    text-align: center;
    font-style: italic;
    text-indent: 0;
    margin: 1em 2em;
    line-height: 1.7;
}
blockquote {
    margin: 1em 2em;
    font-style: italic;
}
blockquote p {
    text-indent: 0;
    text-align: left;
}
cite {
    display: block;
    font-style: normal;
    font-size: 0.9em;
    color: #555;
    margin-top: 0.3em;
}
.divider {
    text-align: center;
    margin: 1.5em 0;
    color: #999;
    letter-spacing: 4px;
}
.section-strong {
    font-weight: bold;
}
.title-page {
    text-align: center;
    margin-top: 30%;
}
.title-page h1 {
    font-size: 2em;
    margin-bottom: 0.5em;
}
.title-page .subtitle {
    font-style: italic;
    color: #555;
    margin-bottom: 2em;
}
.title-page .author {
    font-size: 1.1em;
    margin-bottom: 0.3em;
}
.title-page .imprint {
    font-size: 0.85em;
    color: #777;
    margin-top: 2em;
}
.copyright-page {
    margin-top: 30%;
    text-align: center;
    font-size: 0.85em;
    color: #666;
    line-height: 1.8;
}
'''

css = epub.EpubItem(
    uid='style',
    file_name='style/default.css',
    media_type='text/css',
    content=style
)
book.add_item(css)

# --- Helper to convert markdown section to HTML ---
def md_to_html(text):
    """Simple markdown to HTML for our specific format."""
    lines = text.strip().split('\n')
    html_parts = []
    i = 0
    in_blockquote = False

    while i < len(lines):
        line = lines[i]

        # Blank line
        if not line.strip():
            if in_blockquote:
                html_parts.append('</blockquote>')
                in_blockquote = False
            i += 1
            continue

        # Blockquote lines (> prefix)
        if line.startswith('> '):
            if not in_blockquote:
                html_parts.append('<blockquote>')
                in_blockquote = True
            content = line[2:]
            # Citation line
            if content.startswith('—') or content.startswith('&mdash;'):
                html_parts.append(f'<cite>{inline_format(content)}</cite>')
            else:
                html_parts.append(f'<p>{inline_format(content)}</p>')
            i += 1
            continue

        if in_blockquote:
            html_parts.append('</blockquote>')
            in_blockquote = False

        # Section divider
        if line.strip() == '---':
            html_parts.append('<p class="divider">&bull; &bull; &bull;</p>')
            i += 1
            continue

        # Regular paragraph
        html_parts.append(f'<p>{inline_format(line)}</p>')
        i += 1

    if in_blockquote:
        html_parts.append('</blockquote>')

    return '\n'.join(html_parts)


def inline_format(text):
    """Convert inline markdown to HTML."""
    # Bold+italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Em dash
    text = text.replace(' — ', ' &mdash; ')
    text = text.replace(' —', ' &mdash;')
    text = text.replace('— ', '&mdash; ')
    # Curly quotes (basic)
    text = re.sub(r'"([^"]*)"', r'&ldquo;\1&rdquo;', text)
    return text


# --- Split content into sections ---
sections = re.split(r'\n## ', md)
preamble = sections[0]
section_list = sections[1:]

# --- Title page ---
title_html = '''
<div class="title-page">
  <h1>Is Baptism<br/>Really Necessary?</h1>
  <p class="subtitle">A study from the Scriptures alone</p>
  <p class="author">Paul Hainline</p>
  <p class="imprint">NobleMind Press<br/>noblemind.study</p>
</div>
'''

title_ch = epub.EpubHtml(title='Title', file_name='title.xhtml', lang='en')
title_ch.content = f'<html><head><link rel="stylesheet" href="style/default.css"/></head><body>{title_html}</body></html>'
title_ch.add_item(css)
book.add_item(title_ch)

# --- Copyright page ---
copyright_html = '''
<div class="copyright-page">
  <p>&copy; 2026 Paul Hainline. All rights reserved.</p>
  <p>NobleMind Press &bull; noblemind.study</p>
  <p style="margin-top:1em;">All Scripture quotations are from the<br/>
  New American Standard Bible (NASB).</p>
  <p style="margin-top:1em;">This booklet may be freely shared and distributed<br/>
  for the purpose of teaching and study.</p>
</div>
'''

copyright_ch = epub.EpubHtml(title='Copyright', file_name='copyright.xhtml', lang='en')
copyright_ch.content = f'<html><head><link rel="stylesheet" href="style/default.css"/></head><body>{copyright_html}</body></html>'
copyright_ch.add_item(css)
book.add_item(copyright_ch)

# --- Preamble (prayer + opening) ---
# Extract content after the title line and prayer
preamble_lines = preamble.strip().split('\n')
# Skip the "# Is Baptism Really Necessary?" title
preamble_text = '\n'.join(preamble_lines[1:]).strip()

# Extract prayer (first blockquote)
prayer_match = re.search(r'> \*(.+?)\*', preamble_text, re.DOTALL)
prayer_text = ''
if prayer_match:
    prayer_text = prayer_match.group(1).strip()

# Get everything after the prayer blockquote
after_prayer = re.sub(r'> \*.+?\*\n*', '', preamble_text, count=1).strip()

preamble_html = f'<p class="prayer">{inline_format(prayer_text)}</p>\n'
preamble_html += md_to_html(after_prayer)

preamble_ch = epub.EpubHtml(title='Introduction', file_name='introduction.xhtml', lang='en')
preamble_ch.content = f'<html><head><link rel="stylesheet" href="style/default.css"/></head><body>{preamble_html}</body></html>'
preamble_ch.add_item(css)
book.add_item(preamble_ch)

# --- Sections ---
chapters = [title_ch, copyright_ch, preamble_ch]
toc = [preamble_ch]

for idx, section in enumerate(section_list):
    lines = section.strip().split('\n')
    title = lines[0].strip()
    body = '\n'.join(lines[1:]).strip()

    section_html = f'<h2>{inline_format(title)}</h2>\n'
    section_html += md_to_html(body)

    safe_name = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    ch = epub.EpubHtml(
        title=title,
        file_name=f'section-{idx+1:02d}-{safe_name[:30]}.xhtml',
        lang='en'
    )
    ch.content = f'<html><head><link rel="stylesheet" href="style/default.css"/></head><body>{section_html}</body></html>'
    ch.add_item(css)
    book.add_item(ch)
    chapters.append(ch)
    toc.append(ch)

# --- Table of contents & spine ---
book.toc = toc
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
book.spine = ['nav'] + chapters

# --- Write ---
epub.write_epub('Is_Baptism_Really_Necessary.epub', book)
print(f'EPUB created: Is_Baptism_Really_Necessary.epub')
print(f'Sections: {len(section_list)}')
