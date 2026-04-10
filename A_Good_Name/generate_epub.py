#!/usr/bin/env python3
"""Generate EPUB for Your Name Means Everything: A Good Name.

Uses ebooklib to build a valid EPUB 3.0 from HTML chapter files.
Strips website chrome (glassmorphism, nav, scripts, progress tracking)
and converts to clean XHTML with a print-friendly stylesheet.
"""

from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from ebooklib import epub

BOOK_DIR = Path(__file__).parent

# --- Book metadata ---
BOOK_ID = "your-name-means-everything-a-good-name-2026"
TITLE = "Your Name Means Everything: A Good Name"
SUBTITLE = "A Straight-Talk Guide for Young Men Who Want to Matter"
AUTHORS = ["Paul Hainline", "Pam Hainline"]
PUBLISHER = "NobleMind Press"
YEAR = "2026"
LANGUAGE = "en"
ISBN = "979-8-9954288-0-0"
DESCRIPTION = (
    "A Bible-based straight-talk guide for young men navigating identity, "
    "character, relationships, and faith. Thirteen chapters built on "
    "Scripture — not opinions, not trends."
)

# --- Chapter files in order ---
CHAPTERS = [
    ("introduction.html", "Introduction", "Nobody Told You This", None),
    ("chapter-01.html", "Chapter 1", "Your Name Is Your Most Valuable Asset", "Part One: Who You Are"),
    ("chapter-02.html", "Chapter 2", "The Man in the Mirror Isn\u2019t the Whole Story", None),
    ("chapter-03.html", "Chapter 3", "When Nobody\u2019s Watching Becomes When Everybody\u2019s Watching", None),
    ("chapter-04.html", "Chapter 4", "You Were Made On Purpose, For a Purpose", None),
    ("chapter-05.html", "Chapter 5", "The Relationship You Actually Need Most", "Part Two: Who God Is"),
    ("chapter-06.html", "Chapter 6", "The Bible Isn\u2019t What You Think It Is", None),
    ("chapter-07.html", "Chapter 7", "Putting Down the Phone Long Enough to Hear Something True", None),
    ("chapter-08.html", "Chapter 8", "She Is Somebody\u2019s Daughter", "Part Three: How You Treat People"),
    ("chapter-09.html", "Chapter 9", "The Friends You Choose Will Choose Your Future", None),
    ("chapter-10.html", "Chapter 10", "Honor Your Father and Mother (Even When It\u2019s Hard)", None),
    ("chapter-11.html", "Chapter 11", "Work Like It Matters Because It Does", "Part Four: How You Build a Life"),
    ("chapter-12.html", "Chapter 12", "Money Will Test Your Character", None),
    ("chapter-13.html", "Chapter 13", "The Church Is Not Optional", None),
    ("conclusion.html", "Conclusion", "Your Move", None),
    ("scripture-index.html", "Scripture Index", "Scripture Index", None),
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
.title-page .tagline {
    font-size: 0.95em;
    color: #555;
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

    # Find the inner content area
    inner = soup.find("div", class_="glass-page-inner")
    if not inner:
        raise ValueError(f"No .glass-page-inner found in {html_path}")

    # Remove navigation elements
    for nav in inner.find_all("nav"):
        nav.decompose()

    # Remove footer
    for footer in inner.find_all("footer"):
        footer.decompose()

    # Remove mark-complete button
    for mc in inner.find_all("div", id="mark-complete"):
        mc.decompose()
    for mc in inner.find_all("div", class_="mark-complete"):
        mc.decompose()

    # Remove textareas (reflection input fields - not useful in EPUB)
    for ta in inner.find_all("textarea"):
        ta.decompose()

    # Remove scripts
    for script in inner.find_all("script"):
        script.decompose()

    # Build clean XHTML content
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

    # Extract epigraph
    epigraph = inner.find("section", class_="epigraph")
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
            # Remove inline styles
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
            # Recurse into generic divs
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
    # ebooklib expects content with at least a body-level element
    if not body_content.strip():
        body_content = "<p>&#160;</p>"
    return f"<div>{body_content}</div>"


def main():
    print("Generating EPUB for Your Name Means Everything: A Good Name...")

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
    book.add_metadata("DC", "rights", f"\u00a9 {YEAR} Paul & Pam Hainline. All Rights Reserved.")

    # Cover image
    cover_path = BOOK_DIR / "cover_front_only.jpg"
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
  <h1>Your Name Means Everything</h1>
  <p class="subtitle">A Good Name</p>
  <p class="tagline">{SUBTITLE}</p>
  <p class="author">Paul &amp; Pam Hainline</p>
</div>"""
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = wrap_body(title_html)
    title_page.add_item(css)
    book.add_item(title_page)

    # Copyright page
    copyright_html = f"""\
<div class="copyright-page">
  <p><strong>Your Name Means Everything: A Good Name</strong></p>
  <p>{SUBTITLE}</p>
  <p>&copy; {YEAR} Paul &amp; Pam Hainline. All Rights Reserved.</p>
  <p>Published by {PUBLISHER}</p>
  <p>ISBN: {ISBN} (Paperback)</p>
  <p>Unless otherwise noted, all Scripture quotations are from the<br/>
  New American Standard Bible&reg; (NASB), &copy; The Lockman Foundation.<br/>
  Used by permission.</p>
  <p>No part of this publication may be reproduced, distributed, or transmitted
  in any form without the prior written permission of the authors, except for
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
        "Part One: Who You Are": ("Part One", "Who You Are"),
        "Part Two: Who God Is": ("Part Two", "Who God Is"),
        "Part Three: How You Treat People": ("Part Three", "How You Treat People"),
        "Part Four: How You Build a Life": ("Part Four", "How You Build a Life"),
    }

    for filename, label, ch_title, part in CHAPTERS:
        html_path = BOOK_DIR / filename

        # Insert part divider if this chapter starts a new part
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

        # Extract and convert chapter
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
    output = BOOK_DIR / "YourNameMeansEverything.epub"
    epub.write_epub(str(output), book, {})
    print(f"\nEPUB saved to {output}")
    print(f"  Chapters: {len(chapter_items)}")
    print("Done.")


if __name__ == "__main__":
    main()
