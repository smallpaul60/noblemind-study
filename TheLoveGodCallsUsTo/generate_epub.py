#!/usr/bin/env python3
"""Generate the EPUB for The Love God Calls Us To.

Usage:
    python3 generate_epub.py             # general edition
    python3 generate_epub.py --class     # class edition
"""

import argparse
from pathlib import Path

from ebooklib import epub

import _book_source as bs

BOOK_DIR = Path(__file__).parent
COVER_IMAGE = BOOK_DIR / "cover_front.jpg"  # optional

BOOK_ID_BASE = "the-love-god-calls-us-to-2026"

BOOK_CSS = """\
body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 1em;
    line-height: 1.55;
    color: #1a1a1a;
    margin: 1em;
}
.title-page { text-align: center; margin-top: 30%; }
.title-page h1 { font-size: 2.2em; font-weight: bold; line-height: 1.2; margin-bottom: 0.4em; }
.title-page .subtitle { font-size: 1.1em; font-style: italic; color: #444; margin-bottom: 0.3em; }
.title-page .author { font-size: 1.1em; margin-top: 2em; letter-spacing: 0.15em; }
.copyright-page { margin-top: 30%; font-size: 0.85em; color: #555; text-align: center; }
.copyright-page p { margin-bottom: 0.5em; }
.chapter-header { text-align: center; margin-bottom: 1.5em; padding-top: 1.5em; }
.chapter-label { font-variant: small-caps; letter-spacing: 0.2em; color: #888; font-size: 0.85em; }
.chapter-header h1 { font-size: 1.5em; letter-spacing: 0.02em; margin-top: 0.3em; }
.chapter-body p { margin-bottom: 0.6em; text-align: justify; }
.chapter-body h2 { font-size: 1.15em; margin-top: 1.3em; margin-bottom: 0.4em; }
.chapter-body h3 { font-size: 1.05em; margin-top: 1em; margin-bottom: 0.35em; }
.chapter-body blockquote { margin: 1em 0 1em 1.5em; padding-left: 0.7em; font-style: italic; border-left: 3px solid #C4513F; color: #333; }
.chapter-body blockquote p { margin-bottom: 0.3em; }
.chapter-body blockquote cite { display: block; margin-top: 0.4em; font-style: normal; font-variant: small-caps; letter-spacing: 0.05em; font-size: 0.85em; color: #C4513F; }
.chapter-body .divider { text-align: center; margin: 1.3em 0; color: #888; }
.chapter-body .reflection { margin-top: 2em; padding-top: 1em; border-top: 1px solid #ddd; }
.chapter-body .reflection-header h3 { font-variant: small-caps; letter-spacing: 0.15em; color: #555; text-align: center; }
.chapter-body .reflection-body p { text-indent: 0; }
"""


def wrap_xhtml_body(body_html):
    return body_html or "<p>&#160;</p>"


def section_xhtml_filename(section):
    return f"{section['slug']}.xhtml"


def build_section_content(section):
    parts = ['<div class="chapter-header">']
    if section["label_meta"]:
        parts.append(f'<p class="chapter-label">{section["label_meta"]}</p>')
    parts.append(f'<h1>{section["title_meta"]}</h1>')
    parts.append('</div>')
    parts.append('<div class="chapter-body">')
    if section["epigraph_html"]:
        parts.append(section["epigraph_html"])
    parts.append(section["body_html"])
    parts.append('</div>')
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="class_edition", action="store_true")
    args = ap.parse_args()

    print(f"Building EPUB (class_edition={args.class_edition})...")
    sections = bs.load_all_sections(class_edition=args.class_edition)

    book = epub.EpubBook()
    book.set_identifier(BOOK_ID_BASE + ("-class" if args.class_edition else ""))
    book.set_title(bs.TITLE)
    book.set_language(bs.LANGUAGE)
    book.add_author(bs.AUTHOR)
    book.add_metadata("DC", "publisher", bs.PUBLISHER)
    book.add_metadata("DC", "date", bs.YEAR)
    book.add_metadata("DC", "description", bs.DESCRIPTION)
    book.add_metadata("DC", "rights",
                      f"© {bs.YEAR} {bs.AUTHOR}. All Rights Reserved.")

    if COVER_IMAGE.exists():
        book.set_cover("cover.jpg", COVER_IMAGE.read_bytes())
        print(f"  Cover embedded: {COVER_IMAGE.name}")

    css = epub.EpubItem(uid="style", file_name="style/book.css",
                        media_type="text/css", content=BOOK_CSS.encode("utf-8"))
    book.add_item(css)

    # Title and copyright pages
    edition_note = "Class Edition" if args.class_edition else ""
    title_html = f"""\
<div class="title-page">
  <h1>{bs.TITLE}</h1>
  <p class="subtitle">{bs.SUBTITLE}</p>
  <p class="author">{bs.AUTHOR}</p>
</div>"""
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = wrap_xhtml_body(title_html)
    title_page.add_item(css)
    book.add_item(title_page)

    copyright_html = f"""\
<div class="copyright-page">
  <p><strong>{bs.TITLE}</strong></p>
  <p>{bs.SUBTITLE}</p>
  <p>&copy; {bs.YEAR} {bs.AUTHOR}. All Rights Reserved.</p>
  <p>Published by {bs.PUBLISHER}{(' &mdash; ' + edition_note) if edition_note else ''}</p>
  <p>Unless otherwise noted, all Scripture quotations are from the<br/>
  New American Standard Bible&reg; (NASB), &copy; The Lockman Foundation.<br/>
  Used by permission.</p>
</div>"""
    copyright_page = epub.EpubHtml(title="Copyright", file_name="copyright.xhtml", lang="en")
    copyright_page.content = wrap_xhtml_body(copyright_html)
    copyright_page.add_item(css)
    book.add_item(copyright_page)

    spine = [title_page, copyright_page, "nav"]
    toc = []

    for s in sections:
        epub_fn = section_xhtml_filename(s)
        if s["label_meta"].startswith("Chapter"):
            full_title = f'{s["label_meta"]}: {s["title_meta"]}'
        elif s["label_meta"].startswith("Appendix"):
            full_title = f'{s["label_meta"]}: {s["title_meta"]}'
        elif s["label_meta"] == "Inscription & Dedication":
            full_title = "Dedication"
        else:
            full_title = s["title_meta"]

        body = build_section_content(s)
        page = epub.EpubHtml(title=full_title, file_name=epub_fn, lang="en")
        page.content = wrap_xhtml_body(body)
        page.add_item(css)
        book.add_item(page)
        spine.append(page)
        toc.append(epub.Link(epub_fn, full_title, s["slug"]))

    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    out_name = "The_Love_God_Calls_Us_To"
    if args.class_edition:
        out_name += "_ClassEdition"
    output = BOOK_DIR / f"{out_name}.epub"
    epub.write_epub(str(output), book, {})
    print(f"\nEPUB saved to {output}")
    print(f"  Sections: {len(sections)}")


if __name__ == "__main__":
    main()
