#!/usr/bin/env python3
"""Generate EPUB for The Character No One Could Invent."""

from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from ebooklib import epub

BOOK_DIR = Path(__file__).parent

BOOK_ID = "the-character-no-one-could-invent-2026"
TITLE = "The Character No One Could Invent"
SUBTITLE = "Why Jesus Cannot Be Explained Away"
AUTHORS = ["Paul Hainline"]
PUBLISHER = "NobleMind Press"
YEAR = "2026"
LANGUAGE = "en"
DESCRIPTION = (
    "A 13-chapter examination of the character of Jesus Christ \u2014 "
    "why the Gospel writers could not have invented Him, why He cannot "
    "be reduced to myth, and why His claims demand a verdict."
)

CHAPTERS = [
    ("foreword.html", "Foreword", "About This Book", None),
    ("chapter-01.html", "Chapter 1", "The Character in the Books", "Part I: Could They Have Invented Him?"),
    ("chapter-02.html", "Chapter 2", "The Writers vs. the Character", None),
    ("chapter-03.html", "Chapter 3", "Not a Myth", None),
    ("chapter-04.html", "Chapter 4", "Not a Natural Product", None),
    ("chapter-05.html", "Chapter 5", "How He Knew", "Part II: Unlike Any Mere Man"),
    ("chapter-06.html", "Chapter 6", "How He Taught", None),
    ("chapter-07.html", "Chapter 7", "What He Came to Do", None),
    ("chapter-08.html", "Chapter 8", "The Impossible Mission", None),
    ("chapter-09.html", "Chapter 9", "The Way of Perishing", None),
    ("chapter-10.html", "Chapter 10", "What He Claims", "Part III: His Claims and His Evidence"),
    ("chapter-11.html", "Chapter 11", "What He Built", None),
    ("chapter-12.html", "Chapter 12", "The One Universal Man", None),
    ("chapter-13.html", "Chapter 13", "The Verdict", None),
]

BOOK_CSS = """\
body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 1em;
    line-height: 1.4;
    color: #1a1a1a;
    margin: 1em;
}
.title-page { text-align: center; margin-top: 30%; }
.title-page h1 { font-size: 2.2em; font-weight: bold; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.5em; }
.title-page .subtitle { font-size: 1.1em; font-style: italic; color: #444; margin-bottom: 0.3em; }
.title-page .author { font-size: 1.1em; margin-top: 2em; letter-spacing: 0.15em; }
.copyright-page { margin-top: 60%; font-size: 0.85em; color: #555; text-align: center; }
.copyright-page p { margin-bottom: 0.5em; }
.part-divider { text-align: center; margin-top: 30%; }
.part-number { font-variant: small-caps; letter-spacing: 0.3em; color: #888; font-size: 0.9em; }
.part-title { font-size: 1.6em; font-weight: bold; margin-top: 0.5em; }
.chapter-header { text-align: center; margin-bottom: 2em; padding-top: 2em; }
.chapter-label { font-variant: small-caps; letter-spacing: 0.2em; color: #888; font-size: 0.85em; }
.chapter-header h1 { font-size: 1.5em; letter-spacing: 0.05em; margin-top: 0.3em; }
.epigraph { text-align: center; margin-bottom: 2em; font-style: italic; color: #333; }
.epigraph cite { display: block; margin-top: 0.3em; font-size: 0.9em; color: #555; }
.chapter-body p { margin-bottom: 0.5em; }
.chapter-body h2 { font-size: 1.15em; margin-top: 1.3em; margin-bottom: 0.5em; }
.chapter-body h3 { font-size: 1.05em; margin-top: 1em; margin-bottom: 0.4em; }
.chapter-body blockquote { margin: 1em 1.5em; padding: 0.5em 0.8em; font-style: italic; border-left: 3px solid #999; color: #333; }
.chapter-body blockquote p { margin-bottom: 0.3em; }
.chapter-body hr { border: none; border-top: 1px solid #ddd; margin: 1.5em 3em; }
.principle-box { margin: 1em 1.5em; padding: 0.8em 1em; border: 1px solid #999; text-align: center; font-style: italic; }
.reflection-header { margin-top: 2em; }
.reflection-header h3 { font-size: 1.1em; font-variant: small-caps; letter-spacing: 0.15em; color: #555; }
.reflection-question { margin: 0.8em 0; }
.q-num { font-weight: bold; margin-right: 0.3em; }
.scripture-list { list-style: none; padding-left: 0; margin-bottom: 0.5em; }
.scripture-list li { margin-bottom: 0.2em; }
.ref { font-weight: bold; margin-right: 0.5em; }
.chapters { color: #666; font-size: 0.9em; }
"""


def extract_content(html_path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    inner = soup.find("div", class_="glass-page-inner")
    if not inner:
        raise ValueError(f"No .glass-page-inner found in {html_path}")
    for el in inner.find_all(["nav", "footer", "script", "textarea"]):
        el.decompose()
    for mc in inner.find_all("div", id="mark-complete"):
        mc.decompose()
    for mc in inner.find_all("div", class_="mark-complete"):
        mc.decompose()

    parts = []
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

    content = inner.find("div", class_="content")
    if content:
        parts.append('<div class="chapter-body">')
        parts.append(clean_content(content))
        parts.append("</div>")
    return "\n".join(parts)


def clean_content(element):
    output = []
    for child in element.children:
        if isinstance(child, NavigableString):
            continue
        if child.name in ("p", "h2", "h3", "h4"):
            output.append(remove_inline_styles(str(child)))
        elif child.name == "blockquote":
            output.append(remove_inline_styles(str(child)))
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
                parts.append(f'<p class="reflection-question"><span class="q-num">{num.get_text()}</span> {text.get_text()}</p>')
    return "\n".join(parts)


def remove_inline_styles(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup.find_all(True):
        if tag.has_attr("style"):
            del tag["style"]
    return str(soup)


def wrap_body(body_content):
    if not body_content.strip():
        body_content = "<p>&#160;</p>"
    return f"<div>{body_content}</div>"


def main():
    print("Generating EPUB for The Character No One Could Invent...")
    book = epub.EpubBook()
    book.set_identifier(BOOK_ID)
    book.set_title(TITLE)
    book.set_language(LANGUAGE)
    for author in AUTHORS:
        book.add_author(author)
    book.add_metadata("DC", "publisher", PUBLISHER)
    book.add_metadata("DC", "date", YEAR)
    book.add_metadata("DC", "description", DESCRIPTION)
    book.add_metadata("DC", "rights", f"\u00a9 {YEAR} Paul Hainline. All Rights Reserved.")

    css = epub.EpubItem(uid="style", file_name="style/book.css", media_type="text/css", content=BOOK_CSS.encode("utf-8"))
    book.add_item(css)

    title_html = f"""\
<div class="title-page">
  <h1>{TITLE}</h1>
  <p class="subtitle">{SUBTITLE}</p>
  <p class="author">Paul Hainline</p>
</div>"""
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = wrap_body(title_html)
    title_page.add_item(css)
    book.add_item(title_page)

    copyright_html = f"""\
<div class="copyright-page">
  <p><strong>{TITLE}</strong></p>
  <p>{SUBTITLE}</p>
  <p>&copy; {YEAR} Paul Hainline. All Rights Reserved.</p>
  <p>Published by {PUBLISHER}</p>
  <p>Unless otherwise noted, all Scripture quotations are from the<br/>
  New American Standard Bible&reg; (NASB), &copy; The Lockman Foundation.<br/>
  Used by permission.</p>
</div>"""
    copyright_page = epub.EpubHtml(title="Copyright", file_name="copyright.xhtml", lang="en")
    copyright_page.content = wrap_body(copyright_html)
    copyright_page.add_item(css)
    book.add_item(copyright_page)

    spine = [title_page, copyright_page, "nav"]
    toc = []
    chapter_items = []
    current_part_num = 0
    part_names = {
        "Part I: Could They Have Invented Him?": ("Part I", "Could They Have Invented Him?"),
        "Part II: Unlike Any Mere Man": ("Part II", "Unlike Any Mere Man"),
        "Part III: His Claims and His Evidence": ("Part III", "His Claims and His Evidence"),
    }

    for filename, label, ch_title, part in CHAPTERS:
        html_path = BOOK_DIR / filename
        if part and part in part_names:
            current_part_num += 1
            pn, pt = part_names[part]
            pp = epub.EpubHtml(title=part, file_name=f"part{current_part_num}.xhtml", lang="en")
            pp.content = wrap_body(f'<div class="part-divider"><p class="part-number">{pn}</p><p class="part-title">{pt}</p></div>')
            pp.add_item(css)
            book.add_item(pp)
            spine.append(pp)

        if html_path.exists():
            print(f"  Processing: {filename} -> {label}: {ch_title}")
            content = extract_content(html_path)
        else:
            print(f"  WARNING: {filename} not found")
            content = f'<div class="chapter-header"><h1>{ch_title}</h1></div>'

        epub_fn = filename.replace(".html", ".xhtml")
        full_title = f"{label}: {ch_title}" if label != ch_title else ch_title
        ch_page = epub.EpubHtml(title=full_title, file_name=epub_fn, lang="en")
        ch_page.content = wrap_body(content)
        ch_page.add_item(css)
        book.add_item(ch_page)
        spine.append(ch_page)
        chapter_items.append(ch_page)
        toc.append(epub.Link(epub_fn, full_title, epub_fn.replace(".xhtml", "")))

    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    output = BOOK_DIR / "The_Character_No_One_Could_Invent.epub"
    epub.write_epub(str(output), book, {})
    print(f"\nEPUB saved to {output}")
    print(f"  Chapters: {len(chapter_items)}")
    print("Done.")

if __name__ == "__main__":
    main()
