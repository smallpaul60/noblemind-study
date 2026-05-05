#!/usr/bin/env python3
"""Generate Your Name Means Everything PDF from HTML chapter files."""

from pathlib import Path
from bs4 import BeautifulSoup
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "YourNameMeansEverything.pdf"

CHAPTERS = [
    "introduction.html",
    "chapter-01.html",
    "chapter-02.html",
    "chapter-03.html",
    "chapter-04.html",
    "chapter-05.html",
    "chapter-06.html",
    "chapter-07.html",
    "chapter-08.html",
    "chapter-09.html",
    "chapter-10.html",
    "chapter-11.html",
    "chapter-12.html",
    "chapter-13.html",
    "chapter-14.html",
    "conclusion.html",
]

CHAPTER_TITLES = {
    "introduction.html": ("Nobody Told You This", "Introduction", None),
    "chapter-01.html": ("Your Name Is Your Most Valuable Asset", "Chapter 1", "Part One: Who You Are"),
    "chapter-02.html": ("The Man in the Mirror Isn\u2019t the Whole Story", "Chapter 2", "Part One: Who You Are"),
    "chapter-03.html": ("When Nobody\u2019s Watching Becomes When Everybody\u2019s Watching", "Chapter 3", "Part One: Who You Are"),
    "chapter-04.html": ("You Were Made On Purpose, For a Purpose", "Chapter 4", "Part One: Who You Are"),
    "chapter-05.html": ("The Relationship You Actually Need Most", "Chapter 5", "Part Two: Who God Is"),
    "chapter-06.html": ("The Bible Isn\u2019t What You Think It Is", "Chapter 6", "Part Two: Who God Is"),
    "chapter-07.html": ("Putting Down the Phone Long Enough to Hear Something True", "Chapter 7", "Part Two: Who God Is"),
    "chapter-08.html": ("She Is Somebody\u2019s Daughter", "Chapter 8", "Part Three: How You Treat People"),
    "chapter-09.html": ("What to Expect from a Young Woman Who Fears God", "Chapter 9", "Part Three: How You Treat People"),
    "chapter-10.html": ("The Friends You Choose Will Choose Your Future", "Chapter 10", "Part Three: How You Treat People"),
    "chapter-11.html": ("Honor Your Father and Mother (Even When It\u2019s Hard)", "Chapter 11", "Part Three: How You Treat People"),
    "chapter-12.html": ("Work Like It Matters Because It Does", "Chapter 12", "Part Four: How You Build a Life"),
    "chapter-13.html": ("Money Will Test Your Character", "Chapter 13", "Part Four: How You Build a Life"),
    "chapter-14.html": ("The Church Is Not Optional", "Chapter 14", "Part Four: How You Build a Life"),
    "conclusion.html": ("Your Move", "Conclusion", None),
}


def extract_content(filepath):
    """Extract the body content from a chapter HTML file."""
    soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "html.parser")

    parts = []

    # Extract epigraph (before the content div)
    epigraph = soup.find("section", class_="epigraph")
    if epigraph:
        parts.append(str(epigraph))

    content_div = soup.find("div", class_="content")
    if not content_div:
        return "\n".join(parts)

    for el in content_div.children:
        if hasattr(el, "name") and el.name:
            # Skip nav controls, mark-complete buttons, footers, reflection sections
            if el.get("class") and any(
                c in el.get("class", [])
                for c in ["nav-controls", "mark-complete", "footer-nav", "reflection-section"]
            ):
                continue

            if el.name == "div" and "divider" in el.get("class", []):
                parts.append('<div class="divider">*&emsp;*&emsp;*</div>')
            elif el.name == "blockquote" and "scripture" in el.get("class", []):
                parts.append(str(el))
            elif el.name == "div" and "principle-box" in el.get("class", []):
                parts.append(str(el))
            elif el.name == "section" and "epigraph" in el.get("class", []):
                parts.append(str(el))
            elif el.name in ("p", "h2", "h3", "blockquote", "ul", "ol"):
                parts.append(str(el))

    return "\n".join(parts)


def build_chapter_html(filename):
    """Build the HTML section for a single chapter."""
    filepath = BOOK_DIR / filename
    title, chapter_num, part_subtitle = CHAPTER_TITLES[filename]
    content = extract_content(filepath)

    header_parts = []
    if chapter_num:
        header_parts.append(f'<p class="chapter-num">{chapter_num}</p>')
    header_parts.append(f"<h1>{title}</h1>")
    if part_subtitle:
        header_parts.append(f'<p class="part-subtitle"><em>{part_subtitle}</em></p>')

    header_html = "\n".join(header_parts)

    return f"""
    <section class="chapter">
      <div class="chapter-header">
        {header_html}
      </div>
      <div class="chapter-body">
        {content}
      </div>
    </section>
    """


def build_toc():
    """Build the table of contents."""
    toc_items = []

    # Introduction (no part)
    toc_items.append('<div class="toc-entry"><span>Introduction: Nobody Told You This</span></div>')

    current_part = None
    for filename in CHAPTERS[1:-1]:  # skip introduction and conclusion
        title, chapter_num, part = CHAPTER_TITLES[filename]
        if part != current_part:
            current_part = part
            toc_items.append(f'<div class="toc-part"><strong>{part}</strong></div>')
        num = chapter_num.replace("Chapter ", "")
        toc_items.append(
            f'<div class="toc-entry toc-chapter">'
            f"<span>Chapter {num}: {title}</span>"
            f"</div>"
        )

    # Conclusion (no part)
    toc_items.append('<div class="toc-entry" style="margin-top: 16pt;"><span>Conclusion: Your Move</span></div>')

    return "\n".join(toc_items)


CSS = """
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Italic'), local('EB Garamond');
    font-weight: normal;
    font-style: italic;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold'), local('EB Garamond');
    font-weight: bold;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold Italic'), local('EB Garamond');
    font-weight: bold;
    font-style: italic;
}

@page {
    size: 5.5in 8.5in;
    margin: 0.85in 0.75in 0.9in 0.75in;

    @bottom-center {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #333;
    }
}

@page :first {
    @bottom-center { content: none; }
}

@page frontmatter {
    @bottom-center {
        content: counter(page, lower-roman);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #333;
    }
}

@page title-page {
    @bottom-center { content: none; }
}

@page copyright-page {
    @bottom-center { content: none; }
}

@page toc-page {
    @bottom-center { content: none; }
}

body {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
}

/* === TITLE PAGE === */
.title-page {
    page: title-page;
    page-break-after: always;
    text-align: center;
    padding-top: 1.8in;
}
.title-page h1 {
    font-size: 26pt;
    font-weight: bold;
    line-height: 1.25;
    margin-bottom: 0.15in;
    color: #1a1a1a;
}
.title-page .subtitle-line {
    font-size: 13pt;
    color: #333;
    margin-bottom: 4pt;
}
.title-page .tagline {
    font-size: 11pt;
    font-style: italic;
    color: #555;
    margin-top: 0.35in;
    margin-bottom: 4pt;
    line-height: 1.5;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 0.8in;
    color: #1a1a1a;
}

/* === COPYRIGHT PAGE === */
.copyright-page {
    page: copyright-page;
    page-break-after: always;
    text-align: center;
    padding-top: 3in;
    font-size: 9.5pt;
    line-height: 1.7;
    color: #444;
}
.copyright-page p {
    margin-bottom: 10pt;
}
.copyright-page .book-title {
    font-style: normal;
    font-weight: normal;
}
.copyright-page .edition {
    margin-top: 18pt;
}

/* === TABLE OF CONTENTS === */
.toc-section {
    page: toc-page;
    page-break-after: always;
}
.toc-section h1 {
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 0.35in;
    color: #1a1a1a;
}
.toc-part {
    margin-top: 16pt;
    margin-bottom: 6pt;
    font-size: 10.5pt;
    color: #1a1a1a;
}
.toc-entry {
    font-size: 10.5pt;
    line-height: 1.8;
    color: #333;
}
.toc-chapter {
    padding-left: 0.25in;
}

/* === CHAPTERS === */
.chapter {
    page-break-before: always;
}

.chapter-header {
    text-align: center;
    margin-bottom: 0.3in;
    padding-bottom: 0.15in;
}

.chapter-header .chapter-num {
    font-size: 10pt;
    letter-spacing: 0.08em;
    color: #555;
    margin-bottom: 2pt;
    text-transform: uppercase;
}

.chapter-header h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 6pt;
    line-height: 1.2;
}

.chapter-header .part-subtitle {
    font-size: 10.5pt;
    color: #555;
    margin-top: 2pt;
}

/* === BODY TEXT === */
.chapter-body p {
    text-align: justify;
    text-indent: 0.3in;
    margin-bottom: 0;
    margin-top: 0;
    orphans: 2;
    widows: 2;
}

.chapter-body h2 + p,
.chapter-body .divider + p,
.chapter-body .scripture + p,
.chapter-body .principle-box + p,
.chapter-body .epigraph + p {
    text-indent: 0;
}

/* First paragraph of chapter */
.chapter-body > p:first-child {
    text-indent: 0;
}

/* First element after epigraph */
.chapter-body > .epigraph + p,
.chapter-body > section.epigraph + p {
    text-indent: 0;
}

/* === SECTION HEADINGS === */
.chapter-body h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.3in;
    margin-bottom: 0.12in;
    page-break-after: avoid;
}

/* === SCRIPTURE QUOTES === */
blockquote.scripture {
    margin: 0.15in 0 0.15in 0.4in;
    padding: 0;
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.5;
    border: none;
    page-break-inside: avoid;
}

blockquote.scripture p {
    text-indent: 0 !important;
    text-align: left;
    margin-bottom: 0;
}

blockquote.scripture cite {
    display: block;
    margin-top: 3pt;
    font-style: normal;
    font-weight: 500;
    font-size: 9.5pt;
    color: #444;
}

/* === PRINCIPLE BOX === */
.principle-box {
    margin: 0.18in 0.3in;
    padding: 0.12in 0.18in;
    border-left: 2pt solid #666;
    font-size: 10.5pt;
    page-break-inside: avoid;
}

.principle-box p {
    text-indent: 0 !important;
    text-align: left;
}

/* === EPIGRAPH === */
section.epigraph, .epigraph {
    margin: 0.15in 0.5in 0.25in 0.5in;
    text-align: center;
    page-break-inside: avoid;
}

section.epigraph blockquote, .epigraph blockquote {
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.55;
    margin-bottom: 0;
    border: none;
    padding: 0;
}

section.epigraph cite, .epigraph cite {
    display: block;
    margin-top: 4pt;
    font-style: normal;
    font-size: 9.5pt;
    color: #444;
}

/* === DIVIDERS === */
.divider {
    text-align: center;
    margin: 0.2in 0;
    color: #888;
    font-size: 10pt;
    letter-spacing: 0.15em;
}

/* === LISTS === */
.chapter-body ul, .chapter-body ol {
    margin: 0.1in 0 0.1in 0.5in;
    padding: 0;
    font-size: 10.5pt;
    line-height: 1.55;
}

.chapter-body ul li, .chapter-body ol li {
    margin-bottom: 4pt;
    text-indent: 0;
}

/* === MISC === */
em { font-style: italic; }
strong { font-weight: bold; }
"""


def build_full_html(chapter_sections, toc_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <!-- TITLE PAGE -->
  <div class="title-page">
    <h1>Your Name<br>Means Everything</h1>
    <p class="subtitle-line">A Good Name</p>
    <p class="tagline">A Straight-Talk Guide for Young Men<br>Who Want to Matter</p>
    <p class="author">Paul &amp; Pam Hainline</p>
  </div>

  <!-- COPYRIGHT PAGE -->
  <div class="copyright-page">
    <p class="book-title">Your Name Means Everything: A Good Name</p>
    <p>Copyright &copy; 2026 Paul &amp; Pam Hainline. All Rights Reserved.</p>
    <p>All Scripture quotations are from the New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p class="edition">First Edition</p>
  </div>

  <!-- TABLE OF CONTENTS -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- CHAPTERS -->
  {chapter_sections}

</body>
</html>"""


def main():
    print("Extracting chapter content...")
    chapter_sections = []
    for filename in CHAPTERS:
        print(f"  {filename}")
        chapter_sections.append(build_chapter_html(filename))

    print("Building table of contents...")
    toc_html = build_toc()

    print("Assembling HTML...")
    full_html = build_full_html("\n".join(chapter_sections), toc_html)

    # Save intermediate HTML for debugging
    debug_html = BOOK_DIR / "_book_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")
    print(f"  Debug HTML saved to {debug_html}")

    print("Generating PDF with WeasyPrint...")
    doc = weasyprint.HTML(string=full_html)
    doc.write_pdf(str(OUTPUT))
    print(f"PDF saved to {OUTPUT}")

    # Clean up debug file
    debug_html.unlink(missing_ok=True)
    print("Done.")


if __name__ == "__main__":
    main()
