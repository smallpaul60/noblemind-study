#!/usr/bin/env python3
"""Generate EPUB for A New and Living Way.

Uses ebooklib to build a valid EPUB 3.0 from HTML chapter files.
Strips website chrome (glassmorphism, nav, scripts, progress tracking)
and converts to clean XHTML with a print-friendly stylesheet.
"""

from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from ebooklib import epub

BOOK_DIR = Path(__file__).parent

# --- Book metadata ---
BOOK_ID = "a-new-and-living-way-2026"
TITLE = "A New and Living Way"
SUBTITLE = "Learning to Pray as the Bible Actually Teaches"
AUTHORS = ["Paul Hainline"]
PUBLISHER = "NobleMind Press"
YEAR = "2026"
LANGUAGE = "en"
DESCRIPTION = (
    "A 12-chapter study on prayer rooted in Scripture \u2014 tracing the "
    "Bible's teaching on prayer from Genesis through Revelation, from the "
    "first cries of mankind to the new and living way opened by Christ."
)

# --- Chapter files in order ---
CHAPTERS = [
    ("authors-note.html", "Author\u2019s Note", "A Note from the Author", None),
    ("chapter-01.html", "Chapter 1", "A God Who Hears", "Part I: The God Who Hears"),
    ("chapter-02.html", "Chapter 2", "Who Are We That You Are Mindful of Us?", None),
    ("chapter-03.html", "Chapter 3", "From the Beginning: The First Cries", "Part II: When the Veil Still Stood"),
    ("chapter-04.html", "Chapter 4", "Abraham: The Friend of God", None),
    ("chapter-05.html", "Chapter 5", "Moses: Face to Face", None),
    ("chapter-06.html", "Chapter 6", "The Veil Is Torn", "Part III: The Veil Is Torn"),
    ("chapter-07.html", "Chapter 7", "Lord, Teach Us", "Part IV: Through the Open Door"),
    ("chapter-08.html", "Chapter 8", "In My Name", None),
    ("chapter-09.html", "Chapter 9", "When God Says No", None),
    ("chapter-10.html", "Chapter 10", "The Prayers of the Church", "Part V: The Life of Prayer"),
    ("chapter-11.html", "Chapter 11", "Standing in the Gap", None),
    ("chapter-12.html", "Chapter 12", "A New and Living Way", None),
]

# --- Clean EPUB stylesheet ---
BOOK_CSS = """\
body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 1em;
    line-height: 1.4;
    color: #1a1a1a;
    margin: 1em;
}

/* Title Page */
.title-page {
    text-align: center;
    margin-top: 30%;
}
.title-page h1 {
    font-size: 2.2em;
    font-weight: bold;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5em;
}
.title-page .subtitle {
    font-size: 1.1em;
    font-style: italic;
    color: #444;
    margin-bottom: 0.3em;
}
.title-page .author {
    font-size: 1.1em;
    margin-top: 2em;
    letter-spacing: 0.15em;
}

/* Copyright */
.copyright-page {
    margin-top: 60%;
    font-size: 0.85em;
    color: #555;
    text-align: center;
}
.copyright-page p { margin-bottom: 0.5em; }

/* Part Dividers */
.part-divider {
    text-align: center;
    margin-top: 30%;
}
.part-number {
    font-variant: small-caps;
    letter-spacing: 0.3em;
    color: #888;
    font-size: 0.9em;
}
.part-title {
    font-size: 1.6em;
    font-weight: bold;
    margin-top: 0.5em;
}

/* Chapter Headers */
.chapter-header {
    text-align: center;
    margin-bottom: 2em;
    padding-top: 2em;
}
.chapter-label {
    font-variant: small-caps;
    letter-spacing: 0.2em;
    color: #888;
    font-size: 0.85em;
}
.chapter-header h1 {
    font-size: 1.5em;
    letter-spacing: 0.05em;
    margin-top: 0.3em;
}

/* Epigraph / Opening Scripture */
.epigraph {
    text-align: center;
    margin-bottom: 2em;
    font-style: italic;
    color: #333;
}
.epigraph cite {
    display: block;
    margin-top: 0.3em;
    font-size: 0.9em;
    color: #555;
}

/* Chapter Body */
.chapter-body p { margin-bottom: 0.5em; }
.chapter-body h2 { font-size: 1.15em; margin-top: 1.3em; margin-bottom: 0.5em; }
.chapter-body h3 { font-size: 1.05em; margin-top: 1em; margin-bottom: 0.4em; }

.chapter-body blockquote {
    margin: 1em 1.5em;
    padding: 0.5em 0.8em;
    font-style: italic;
    border-left: 3px solid #999;
    color: #333;
}
.chapter-body blockquote p { margin-bottom: 0.3em; }

.chapter-body hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 1.5em 3em;
}

/* Divider */
.divider {
    text-align: center;
    margin: 1.5em 0;
    color: #ccc;
    letter-spacing: 0.3em;
}

/* Principle / callout boxes */
.principle-box {
    margin: 1em 1.5em;
    padding: 0.8em 1em;
    border: 1px solid #999;
    text-align: center;
    font-style: italic;
}

/* Reflection sections */
.reflection-header { margin-top: 2em; }
.reflection-header h3 {
    font-size: 1.1em;
    font-variant: small-caps;
    letter-spacing: 0.15em;
    color: #555;
}
.reflection-question {
    margin: 0.8em 0;
}
.q-num {
    font-weight: bold;
    margin-right: 0.3em;
}

/* Scripture Index */
.scripture-list {
    list-style: none;
    padding-left: 0;
    margin-bottom: 0.5em;
}
.scripture-list li {
    margin-bottom: 0.2em;
}
.ref { font-weight: bold; margin-right: 0.5em; }
.chapters { color: #666; font-size: 0.9em; }
"""


def extract_content(html_path):
    """Extract chapter content from website HTML, stripping chrome."""
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    inner = soup.find("div", class_="glass-page-inner")
    if not inner:
        raise ValueError(f"No .glass-page-inner found in {html_path}")

    # Remove navigation, footer, mark-complete, textareas, scripts
    for nav in inner.find_all("nav"):
        nav.decompose()
    for footer in inner.find_all("footer"):
        footer.decompose()
    for mc in inner.find_all("div", id="mark-complete"):
        mc.decompose()
    for mc in inner.find_all("div", class_="mark-complete"):
        mc.decompose()
    for ta in inner.find_all("textarea"):
        ta.decompose()
    for script in inner.find_all("script"):
        script.decompose()

    parts = []

    # Extract header
    header = inner.find("header")
    if header:
        chapter_num = header.find("p", class_="chapter-num")
        h1 = header.find("h1")
        parts.append('<div class="chapter-header">')
        if chapter_num:
            parts.append(f'  <p class="chapter-label">{chapter_num.get_text()}</p>')
        if h1:
            parts.append(f"  <h1>{h1.get_text()}</h1>")
        parts.append("</div>")

    # Extract epigraph (may be <section> or <div>)
    epigraph = inner.find("section", class_="epigraph") or inner.find("div", class_="epigraph")
    if epigraph:
        parts.append('<div class="epigraph">')
        bq = epigraph.find("blockquote")
        cite = epigraph.find("cite")
        if bq:
            parts.append(f"  <p>{bq.get_text().strip()}</p>")
        if cite:
            parts.append(f"  <cite>{cite.get_text().strip()}</cite>")
        parts.append("</div>")

    # Extract main content
    content = inner.find("div", class_="content")
    if content:
        parts.append('<div class="chapter-body">')
        parts.append(clean_content(content))
        parts.append("</div>")

    return "\n".join(parts)


def clean_content(element):
    """Recursively clean content, preserving structure."""
    output = []
    for child in element.children:
        if isinstance(child, NavigableString):
            continue
        if child.name in ("p", "h2", "h3", "h4"):
            text = str(child)
            text = remove_inline_styles(text)
            output.append(text)
        elif child.name == "blockquote":
            text = str(child)
            text = remove_inline_styles(text)
            output.append(text)
        elif child.name == "div" and "divider" in child.get("class", []):
            output.append('<hr/>')
        elif child.name == "div" and "principle-box" in child.get("class", []):
            output.append(str(child))
        elif child.name == "section" and "reflection" in " ".join(child.get("class", [])):
            output.append(clean_reflection(child))
        elif child.name in ("ul", "ol"):
            output.append(str(child))
        elif child.name == "div":
            output.append(clean_content(child))
    return "\n".join(output)


def clean_reflection(section):
    """Clean reflection/discussion sections."""
    parts = []
    header = section.find(class_="reflection-header")
    if header:
        h3 = header.find("h3")
        if h3:
            parts.append(f'<div class="reflection-header"><h3>{h3.get_text()}</h3></div>')

    body = section.find(class_="reflection-body")
    if body:
        for q in body.find_all(class_="reflection-question"):
            num = q.find(class_="q-num")
            text = q.find(class_="q-text")
            if num and text:
                parts.append(
                    f'<p class="reflection-question">'
                    f'<span class="q-num">{num.get_text()}</span> '
                    f'{text.get_text()}</p>'
                )
    return "\n".join(parts)


def remove_inline_styles(html_str):
    """Remove style attributes from HTML string."""
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup.find_all(True):
        if tag.has_attr("style"):
            del tag["style"]
    return str(soup)


def wrap_body(body_content):
    """Wrap content in minimal XHTML body for ebooklib."""
    if not body_content.strip():
        body_content = "<p>&#160;</p>"
    return f"<div>{body_content}</div>"


def main():
    print("Generating EPUB for A New and Living Way...")

    book = epub.EpubBook()

    # Metadata
    book.set_identifier(BOOK_ID)
    book.set_title(TITLE)
    book.set_language(LANGUAGE)
    for author in AUTHORS:
        book.add_author(author)
    book.add_metadata("DC", "publisher", PUBLISHER)
    book.add_metadata("DC", "date", YEAR)
    book.add_metadata("DC", "description", DESCRIPTION)
    book.add_metadata("DC", "rights", f"\u00a9 {YEAR} Paul Hainline. All Rights Reserved.")

    # Cover image — use the composed cover_front.jpg so the EPUB, PDF,
    # and website card all show the same image with matching typography.
    cover_path = BOOK_DIR / "cover_front.jpg"
    if cover_path.exists():
        book.set_cover("cover.jpg", cover_path.read_bytes())
        print(f"  Cover: {cover_path.name}")

    # Stylesheet
    css = epub.EpubItem(
        uid="style",
        file_name="style/book.css",
        media_type="text/css",
        content=BOOK_CSS.encode("utf-8"),
    )
    book.add_item(css)

    # Title page
    title_html = f"""\
<div class="title-page">
  <h1>A New and Living Way</h1>
  <p class="subtitle">{SUBTITLE}</p>
  <p class="author">Paul Hainline</p>
</div>"""
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = wrap_body(title_html)
    title_page.add_item(css)
    book.add_item(title_page)

    # Copyright page
    copyright_html = f"""\
<div class="copyright-page">
  <p><strong>A New and Living Way</strong></p>
  <p>{SUBTITLE}</p>
  <p>&copy; {YEAR} Paul Hainline. All Rights Reserved.</p>
  <p>Published by {PUBLISHER}</p>
  <p>Unless otherwise noted, all Scripture quotations are from the<br/>
  New American Standard Bible&reg; (NASB), &copy; The Lockman Foundation.<br/>
  Used by permission.</p>
  <p>No part of this publication may be reproduced, distributed, or transmitted
  in any form without the prior written permission of the author, except for
  brief quotations in reviews and certain noncommercial uses permitted by
  copyright law.</p>
</div>"""
    copyright_page = epub.EpubHtml(title="Copyright", file_name="copyright.xhtml", lang="en")
    copyright_page.content = wrap_body(copyright_html)
    copyright_page.add_item(css)
    book.add_item(copyright_page)

    # Build chapters
    spine = [title_page, copyright_page, "nav"]
    toc = []
    chapter_items = []

    current_part_num = 0
    part_names = {
        "Part I: The God Who Hears": ("Part I", "The God Who Hears"),
        "Part II: When the Veil Still Stood": ("Part II", "When the Veil Still Stood"),
        "Part III: The Veil Is Torn": ("Part III", "The Veil Is Torn"),
        "Part IV: Through the Open Door": ("Part IV", "Through the Open Door"),
        "Part V: The Life of Prayer": ("Part V", "The Life of Prayer"),
    }

    for filename, label, ch_title, part in CHAPTERS:
        html_path = BOOK_DIR / filename

        if part and part in part_names:
            current_part_num += 1
            part_num_str, part_title_str = part_names[part]
            part_html = f"""\
<div class="part-divider">
  <p class="part-number">{part_num_str}</p>
  <p class="part-title">{part_title_str}</p>
</div>"""
            part_file = f"part{current_part_num}.xhtml"
            part_page = epub.EpubHtml(title=part, file_name=part_file, lang="en")
            part_page.content = wrap_body(part_html)
            part_page.add_item(css)
            book.add_item(part_page)
            spine.append(part_page)

        if html_path.exists():
            print(f"  Processing: {filename} -> {label}: {ch_title}")
            content = extract_content(html_path)
        else:
            print(f"  WARNING: {filename} not found, creating placeholder")
            content = f'<div class="chapter-header"><h1>{ch_title}</h1></div>'

        epub_filename = filename.replace(".html", ".xhtml")
        full_title = f"{label}: {ch_title}" if label != ch_title else ch_title

        ch_page = epub.EpubHtml(title=full_title, file_name=epub_filename, lang="en")
        ch_page.content = wrap_body(content)
        ch_page.add_item(css)
        book.add_item(ch_page)
        spine.append(ch_page)
        chapter_items.append(ch_page)

        toc.append(epub.Link(epub_filename, full_title, epub_filename.replace(".xhtml", "")))

    # Table of contents and navigation
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    # Write EPUB
    output = BOOK_DIR / "A_New_and_Living_Way.epub"
    epub.write_epub(str(output), book, {})
    print(f"\nEPUB saved to {output}")
    print(f"  Chapters: {len(chapter_items)}")
    print("Done.")


if __name__ == "__main__":
    main()
