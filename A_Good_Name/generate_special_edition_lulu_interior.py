#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for the SPECIAL EDITION of
"Your Name Means Everything: A Good Name" — personalized copy
for Hagen.

Differences from the standard Lulu interior:
  1. Adds a dedication leaf between Copyright and Contents:
       - recto: "For our grandsons — and for every young man..."
       - verso: personalized messages to Hagen from Nana and Paul
  2. Title page carries a small "Special Edition" mark.
  3. Gold accent (#C4A960, matched to the cover palette) is applied
     to: Part labels, Chapter numbers, Chapter titles, the Contents
     heading, in-chapter section dividers, and scripture/epigraph
     citations.

The Special Edition is local-only — never deployed to the public
site, never linked from books.html, never committed to git history
of generated PDFs (script is committed, PDF is gitignored / deploy-
excluded).
"""

from pathlib import Path
from bs4 import BeautifulSoup
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "YourNameMeansEverything_Special_Edition_Lulu_Interior.pdf"

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
    "chapter-02.html": ("The Man in the Mirror Isn’t the Whole Story", "Chapter 2", "Part One: Who You Are"),
    "chapter-03.html": ("When Nobody’s Watching Becomes When Everybody’s Watching", "Chapter 3", "Part One: Who You Are"),
    "chapter-04.html": ("You Were Made On Purpose, For a Purpose", "Chapter 4", "Part One: Who You Are"),
    "chapter-05.html": ("The Relationship You Actually Need Most", "Chapter 5", "Part Two: Who God Is"),
    "chapter-06.html": ("The Bible Isn’t What You Think It Is", "Chapter 6", "Part Two: Who God Is"),
    "chapter-07.html": ("Putting Down the Phone Long Enough to Hear Something True", "Chapter 7", "Part Two: Who God Is"),
    "chapter-08.html": ("She Is Somebody’s Daughter", "Chapter 8", "Part Three: How You Treat People"),
    "chapter-09.html": ("What to Expect from a Young Woman Who Fears God", "Chapter 9", "Part Three: How You Treat People"),
    "chapter-10.html": ("The Friends You Choose Will Choose Your Future", "Chapter 10", "Part Three: How You Treat People"),
    "chapter-11.html": ("Honor Your Father and Mother (Even When It’s Hard)", "Chapter 11", "Part Three: How You Treat People"),
    "chapter-12.html": ("Work Like It Matters Because It Does", "Chapter 12", "Part Four: How You Build a Life"),
    "chapter-13.html": ("Money Will Test Your Character", "Chapter 13", "Part Four: How You Build a Life"),
    "chapter-14.html": ("The Church Is Not Optional", "Chapter 14", "Part Four: How You Build a Life"),
    "conclusion.html": ("Your Move", "Conclusion", None),
}


def extract_content(filepath):
    soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "html.parser")
    parts = []
    epigraph = soup.find("section", class_="epigraph")
    if epigraph:
        parts.append(str(epigraph))
    content_div = soup.find("div", class_="content")
    if not content_div:
        return "\n".join(parts)
    for el in content_div.children:
        if hasattr(el, "name") and el.name:
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
    toc_items = []
    toc_items.append('<div class="toc-entry"><span>Introduction: Nobody Told You This</span></div>')
    current_part = None
    for filename in CHAPTERS[1:-1]:
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
    toc_items.append('<div class="toc-entry" style="margin-top: 12pt;"><span>Conclusion: Your Move</span></div>')
    return "\n".join(toc_items)


# Cover palette — gold and navy match the navy/gold paperback and hardcover.
# Gold is the frame; Navy carries the title-like content (chapter titles,
# H2 section headings) so the interior speaks the same color language as
# the cover instead of being one undifferentiated wash of gold.
GOLD = "#C4A960"
GOLD_DIM = "#9D8546"
NAVY = "#182030"

CSS = f"""
@font-face {{
    font-family: 'EB Garamond';
    src: local('EB Garamond');
    font-weight: normal;
    font-style: normal;
}}
@font-face {{
    font-family: 'EB Garamond';
    src: local('EB Garamond Italic'), local('EB Garamond');
    font-weight: normal;
    font-style: italic;
}}
@font-face {{
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold'), local('EB Garamond');
    font-weight: bold;
    font-style: normal;
}}
@font-face {{
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold Italic'), local('EB Garamond');
    font-weight: bold;
    font-style: italic;
}}

/* === PAGE SETUP === */
@page {{
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
}}

@page :right {{
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }}
}}

@page :left {{
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-left {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }}
}}

@page title-page {{
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {{ content: none; }}
    @bottom-left {{ content: none; }}
}}

@page copyright-page {{
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right {{ content: none; }}
    @bottom-left {{ content: none; }}
}}

@page dedication-page:right {{
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {{ content: none; }}
    @bottom-left {{ content: none; }}
}}

@page hagen-page:left {{
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right {{ content: none; }}
    @bottom-left {{ content: none; }}
}}

@page toc-page:right {{
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {{ content: none; }}
    @bottom-left {{ content: none; }}
}}

@page toc-page:left {{
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right {{ content: none; }}
    @bottom-left {{ content: none; }}
}}

@page :blank {{
    @bottom-left {{ content: none; }}
    @bottom-right {{ content: none; }}
}}

/* === BODY === */
body {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    text-rendering: optimizeLegibility;
}}

/* === TITLE PAGE === */
.title-page {{
    page: title-page;
    page-break-after: always;
    text-align: center;
    padding-top: 1.6in;
}}
.title-page h1 {{
    font-size: 26pt;
    font-weight: bold;
    line-height: 1.25;
    margin-bottom: 0.15in;
    color: #1a1a1a;
}}
.title-page .subtitle-line {{
    font-size: 13pt;
    color: {GOLD_DIM};
    margin-bottom: 4pt;
}}
.title-page .tagline {{
    font-size: 11pt;
    font-style: italic;
    color: #555;
    margin-top: 0.35in;
    margin-bottom: 4pt;
    line-height: 1.5;
}}
.title-page .author {{
    font-size: 14pt;
    margin-top: 0.7in;
    color: #1a1a1a;
}}
.title-page .special-mark {{
    margin-top: 0.4in;
    font-size: 9.5pt;
    font-style: italic;
    letter-spacing: 0.2em;
    color: {GOLD};
    text-transform: uppercase;
}}

/* === COPYRIGHT PAGE === */
.copyright-page {{
    page: copyright-page;
    page-break-after: always;
    text-align: center;
    padding-top: 3in;
    font-size: 9.5pt;
    line-height: 1.7;
    color: #444;
}}
.copyright-page p {{
    margin-bottom: 10pt;
}}
.copyright-page .edition {{
    margin-top: 18pt;
}}

/* === DEDICATION PAGE (recto) === */
.dedication-page {{
    page: dedication-page;
    break-before: right;
    page-break-after: always;
    text-align: center;
    padding-top: 2.6in;
    font-style: italic;
    font-size: 12pt;
    line-height: 1.7;
    color: #1a1a1a;
}}
.dedication-page p {{
    margin: 0 auto;
    max-width: 3.5in;
}}
.dedication-page .gap {{
    height: 0.4in;
}}
.dedication-page .ornament {{
    color: {GOLD};
    font-size: 14pt;
    letter-spacing: 0.3em;
    margin-bottom: 0.4in;
    font-style: normal;
}}

/* === HAGEN MESSAGE PAGE (verso, back of dedication) === */
.hagen-page {{
    page: hagen-page;
    page-break-after: always;
    text-align: center;
    padding-top: 1.7in;
    font-style: italic;
    font-size: 12pt;
    line-height: 1.7;
    color: #1a1a1a;
}}
.hagen-page .message {{
    margin: 0 auto 0.55in auto;
    max-width: 3.5in;
}}
.hagen-page .signoff {{
    margin-top: 0.18in;
    font-size: 11pt;
}}
.hagen-page .ornament {{
    color: {GOLD};
    font-size: 12pt;
    letter-spacing: 0.3em;
    margin: 0.35in 0;
    font-style: normal;
}}

/* === TABLE OF CONTENTS === */
.toc-section {{
    page: toc-page;
    break-before: right;
    page-break-after: always;
}}
.toc-section h1 {{
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 0.35in;
    color: {GOLD};
    letter-spacing: 0.04em;
}}
.toc-part {{
    margin-top: 16pt;
    margin-bottom: 6pt;
    font-size: 10.5pt;
    color: {GOLD};
}}
.toc-entry {{
    font-size: 10.5pt;
    line-height: 1.8;
    color: #333;
}}
.toc-chapter {{
    padding-left: 0.25in;
}}

/* === CHAPTERS === */
.chapter {{
    break-before: right;
}}

.chapter-header {{
    text-align: center;
    margin-bottom: 0.3in;
    padding-bottom: 0.15in;
}}

.chapter-header .chapter-num {{
    font-size: 10pt;
    letter-spacing: 0.18em;
    color: {GOLD};
    margin-bottom: 4pt;
    text-transform: uppercase;
    font-weight: normal;
}}

.chapter-header h1 {{
    font-size: 20pt;
    font-weight: bold;
    color: {NAVY};
    margin-bottom: 6pt;
    line-height: 1.2;
}}

.chapter-header .part-subtitle {{
    font-size: 10.5pt;
    color: {GOLD_DIM};
    margin-top: 4pt;
}}

/* === BODY TEXT === */
.chapter-body p {{
    text-align: justify;
    text-indent: 0.3in;
    margin-bottom: 0;
    margin-top: 0;
    orphans: 2;
    widows: 2;
}}

.chapter-body h2 + p,
.chapter-body .divider + p,
.chapter-body .scripture + p,
.chapter-body .principle-box + p,
.chapter-body .epigraph + p,
.chapter-body .study-section + p,
.chapter-body ul + p,
.chapter-body ol + p,
.chapter-body blockquote + p {{
    text-indent: 0;
}}

.chapter-body > p:first-child {{
    text-indent: 0;
}}

.chapter-body > .epigraph + p,
.chapter-body > section.epigraph + p {{
    text-indent: 0;
}}

/* === SECTION HEADINGS === */
.chapter-body h2 {{
    font-size: 13pt;
    font-weight: bold;
    color: {NAVY};
    margin-top: 0.3in;
    margin-bottom: 0.12in;
    page-break-after: avoid;
    break-after: avoid;
    orphans: 3;
    widows: 3;
}}

/* === SCRIPTURE QUOTES === */
blockquote.scripture {{
    margin: 0.15in 0 0.15in 0.4in;
    padding: 0;
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.5;
    border-left: 2pt solid {GOLD};
    padding-left: 0.18in;
    page-break-inside: avoid;
}}

blockquote.scripture p {{
    text-indent: 0 !important;
    text-align: left;
    margin-bottom: 0;
}}

blockquote.scripture cite {{
    display: block;
    margin-top: 3pt;
    font-style: normal;
    font-weight: 500;
    font-size: 9.5pt;
    color: {GOLD_DIM};
    font-variant: small-caps;
    letter-spacing: 0.05em;
}}

/* === PRINCIPLE BOX === */
.principle-box {{
    margin: 0.18in 0.3in;
    padding: 0.12in 0.18in;
    border-left: 2pt solid {GOLD};
    font-size: 10.5pt;
    page-break-inside: avoid;
}}

.principle-box p {{
    text-indent: 0 !important;
    text-align: left;
}}

/* === EPIGRAPH === */
section.epigraph, .epigraph {{
    margin: 0.15in 0.5in 0.25in 0.5in;
    text-align: center;
    page-break-inside: avoid;
}}

section.epigraph blockquote, .epigraph blockquote {{
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.55;
    margin-bottom: 0;
    border: none;
    padding: 0;
}}

section.epigraph cite, .epigraph cite {{
    display: block;
    margin-top: 4pt;
    font-style: normal;
    font-size: 9.5pt;
    color: {GOLD_DIM};
    font-variant: small-caps;
    letter-spacing: 0.05em;
}}

/* === DIVIDERS — gold for the special edition === */
.divider {{
    text-align: center;
    margin: 0.22in 0;
    color: {GOLD};
    font-size: 11pt;
    letter-spacing: 0.4em;
    page-break-before: avoid;
}}

/* === LISTS === */
.chapter-body ul, .chapter-body ol {{
    margin: 0.12in 0 0.12in 0.4in;
    padding-left: 0.2in;
    font-size: 10.5pt;
    line-height: 1.55;
}}

.chapter-body ul li, .chapter-body ol li {{
    margin-bottom: 4pt;
    text-indent: 0;
}}

/* === STUDY SECTION === */
.study-section {{
    margin-top: 0.25in;
}}

.study-section h2 {{
    font-size: 13pt;
    font-weight: bold;
    font-style: italic;
    color: {NAVY};
    margin-top: 0.3in;
    margin-bottom: 0.12in;
}}

.study-section p {{
    font-size: 10.5pt;
}}

/* === MISC === */
em {{ font-style: italic; }}
strong {{ font-weight: bold; }}
"""


DEDICATION_HTML = """
  <!-- DEDICATION PAGE (recto, page 3) -->
  <div class="dedication-page">
    <div class="ornament">&#10086;</div>
    <p>For our grandsons &mdash; and for every young man who has been
    handed a world full of noise and not enough truth.</p>
    <div class="gap"></div>
    <p>May you find the Foundation worth building on.</p>
  </div>
"""


HAGEN_HTML = """
  <!-- HAGEN MESSAGE PAGE (verso, page 4 — back of dedication leaf) -->
  <div class="hagen-page">
    <div class="message">
      <p>Hagen, you will always be the little boy<br>
         who stole my heart and the young man<br>
         who makes me proud.</p>
      <p class="signoff">Love always, Nana</p>
    </div>

    <div class="ornament">&#10086;</div>

    <div class="message">
      <p>Hagen, there is no better pursuit in life<br>
         than to become a man after God&rsquo;s own heart.<br>
         You have everything you need to be that man.<br>
         This book is our way of making sure<br>
         you know it.</p>
      <p class="signoff">Love, Paul</p>
    </div>
  </div>
"""


def build_full_html(chapter_sections, toc_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <!-- TITLE PAGE (recto, page 1) -->
  <div class="title-page">
    <h1>Your Name<br>Means Everything</h1>
    <p class="subtitle-line">A Good Name</p>
    <p class="tagline">A Straight-Talk Guide for Young Men<br>Who Want to Matter</p>
    <p class="author">Paul &amp; Pam Hainline</p>
    <p class="author" style="font-size: 10pt; margin-top: 0.4in;">NobleMind Press</p>
    <p class="special-mark">Special Edition</p>
  </div>

  <!-- COPYRIGHT PAGE (verso, page 2) -->
  <div class="copyright-page">
    <p>Your Name Means Everything: A Good Name</p>
    <p>Copyright &copy; 2026 Paul &amp; Pam Hainline<br>All rights reserved.</p>
    <p>Published by NobleMind Press<br>noblemind.study</p>
    <p>ISBN 979-8-9954288-0-0 (paperback)<br>ISBN 979-8-9954288-1-7 (hardcover)</p>
    <p>Scripture quotations are from the New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p class="edition">First Edition &middot; Special Edition Printing</p>
  </div>

  {DEDICATION_HTML}

  {HAGEN_HTML}

  <!-- TABLE OF CONTENTS -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {chapter_sections}

</body>
</html>"""


def main():
    print('Generating SPECIAL EDITION Lulu interior PDF (5.5" x 8.5")...')
    print('  Personalized for: Hagen')
    print()

    print("Extracting chapter content from HTML files...")
    chapter_sections = []
    for filename in CHAPTERS:
        print(f"  {filename}")
        chapter_sections.append(build_chapter_html(filename))

    print("Building table of contents...")
    toc_html = build_toc()

    print("Assembling HTML...")
    full_html = build_full_html("\n".join(chapter_sections), toc_html)

    debug_html = BOOK_DIR / "_special_edition_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")

    print("Generating PDF with WeasyPrint...")
    doc = weasyprint.HTML(string=full_html)
    doc.write_pdf(str(OUTPUT))

    debug_html.unlink(missing_ok=True)

    print(f"\nPDF saved to {OUTPUT}")
    print(f'  Page size: 5.5" x 8.5" (Digest)')
    print(f'  Special edition: Hagen')
    print(f'  Gold accent: {GOLD}')
    print(f'  Fonts: EB Garamond (embedded)')
    print("Done.")


if __name__ == "__main__":
    main()
