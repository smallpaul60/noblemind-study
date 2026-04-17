#!/usr/bin/env python3
"""Generate the downloadable reader PDF for 'Bridge Moments'.

Source: the existing chapter-NN.html and appendix-X.html files in this
directory. Content is already richly structured (epigraph, chapter-purpose,
scripture blockquotes, h2/h3 sections), so we extract with BeautifulSoup.

Output: BridgeMoments.pdf  (5.5" x 8.5", EB Garamond, warm-gold accents)
"""

from pathlib import Path
from bs4 import BeautifulSoup
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BridgeMoments.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
COVER = BOOK_DIR / "cover_front.jpg"

TITLE = "Bridge Moments"
SUBTITLE = "Making the Most of Every Opportunity"
TAGLINE = "A Bible Study on Conversational Evangelism"
AUTHOR = "Paul Hainline"

CHAPTERS = [
    # (file, label, title, part_num, part_title, subtitle)
    ("chapter-01.html", "Chapter 1",  "The Weight of Words",                               1, "The Foundation: Why Words Matter",                  ""),
    ("chapter-02.html", "Chapter 2",  "The Kairos Principle",                              1, "The Foundation: Why Words Matter",                  ""),
    ("chapter-03.html", "Chapter 3",  "Love, Not Agenda",                                  1, "The Foundation: Why Words Matter",                  ""),
    ("chapter-04.html", "Chapter 4",  "\u201cGive Me a Drink\u201d",                       2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "The Woman at the Well \u2022 John 4:1\u201342"),
    ("chapter-05.html", "Chapter 5",  "\u201cYou Must Be Born Again\u201d",                2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "Nicodemus \u2022 John 3:1\u201321"),
    ("chapter-06.html", "Chapter 6",  "\u201cI Must Stay at Your House\u201d",             2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "Zacchaeus \u2022 Luke 19:1\u201310"),
    ("chapter-07.html", "Chapter 7",  "Jesus Felt a Love for Him",                         2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "The Rich Young Ruler \u2022 Mark 10:17\u201327"),
    ("chapter-08.html", "Chapter 8",  "\u201cNeither Do I Condemn You\u201d",              2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "The Woman Caught in Adultery \u2022 John 8:1\u201311"),
    ("chapter-09.html", "Chapter 9",  "Were Not Our Hearts Burning?",                      2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "The Road to Emmaus \u2022 Luke 24:13\u201335"),
    ("chapter-10.html", "Chapter 10", "\u201cFollow Me\u201d",                             2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "The Calling of the First Disciples \u2022 John 1:35\u201351"),
    ("chapter-11.html", "Chapter 11", "\u201cDo You See This Woman?\u201d",                2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "Simon\u2019s House \u2022 Luke 7:36\u201350"),
    ("chapter-12.html", "Chapter 12", "\u201cDo You Love Me?\u201d",                       2, "The Master\u2019s Method: Jesus\u2019 Bridge Moments", "Peter\u2019s Restoration \u2022 John 21:1\u201319"),
    ("chapter-13.html", "Chapter 13", "\u201cDo You Understand What You Are Reading?\u201d",3, "The Pattern Continued: Bridge Moments in Acts",      "Philip & the Ethiopian \u2022 Acts 8:26\u201340"),
    ("chapter-14.html", "Chapter 14", "\u201cMen of Athens\u201d",                          3, "The Pattern Continued: Bridge Moments in Acts",      "Paul on Mars Hill \u2022 Acts 17:16\u201334"),
    ("chapter-15.html", "Chapter 15", "\u201cWhat Must I Do to Be Saved?\u201d",           3, "The Pattern Continued: Bridge Moments in Acts",      "The Philippian Jailer \u2022 Acts 16:16\u201334"),
    ("chapter-16.html", "Chapter 16", "Learning to Listen",                                 4, "The Practice: Living with Bridge Moment Eyes",       "Hearing What People Are Really Saying \u2022 James 1:19"),
    ("chapter-17.html", "Chapter 17", "From Natural to Spiritual",                          4, "The Practice: Living with Bridge Moment Eyes",       "Building the Bridge \u2022 1 Peter 3:15"),
    ("chapter-18.html", "Chapter 18", "Seasoned with Salt",                                 4, "The Practice: Living with Bridge Moment Eyes",       "Speaking Truth with Grace \u2022 Colossians 4:6"),
    ("chapter-19.html", "Chapter 19", "When They Walk Away",                                4, "The Practice: Living with Bridge Moment Eyes",       "Handling Rejection with Grace \u2022 1 Corinthians 3:6\u20137"),
    ("chapter-20.html", "Chapter 20", "The Heart Behind the Words",                         4, "The Practice: Living with Bridge Moment Eyes",       "Love as the Only Foundation \u2022 1 Corinthians 13:1\u20133"),
]

APPENDICES = [
    ("appendix-a.html", "Appendix A", "Quick Reference Chart"),
    ("appendix-b.html", "Appendix B", "Scripture Index"),
    ("appendix-c.html", "Appendix C", "Small Group Exercises"),
]

PARTS = {
    1: "The Foundation: Why Words Matter",
    2: "The Master\u2019s Method: Jesus\u2019 Bridge Moments",
    3: "The Pattern Continued: Bridge Moments in Acts",
    4: "The Practice: Living with Bridge Moment Eyes",
}


# ---------------------------------------------------------------------------
# Content extraction from the existing chapter HTML files.
# ---------------------------------------------------------------------------
EXCLUDE_CLASSES = {
    "nav-controls", "mark-complete", "footer-nav", "reflection-section",
    "part-label", "part-title", "chapter-num",
}


def extract_content(filepath):
    """Pull the chapter body out of chapter-NN.html.

    Keeps: epigraph block, chapter-purpose callout, and the content <div>.
    Drops: navigation, reflection questions, "mark complete" controls.
    """
    soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "html.parser")

    parts = []

    epigraph = soup.find("section", class_="epigraph")
    if epigraph:
        parts.append(str(epigraph))

    purpose = soup.find("div", class_="chapter-purpose")
    if purpose:
        parts.append(str(purpose))

    content_div = soup.find("div", class_="content")
    if content_div is None:
        return "\n".join(parts)

    for el in content_div.children:
        if not hasattr(el, "name") or el.name is None:
            continue
        classes = set(el.get("class") or [])
        if classes & EXCLUDE_CLASSES:
            continue
        # The reflection section may be a <section>, not a <div>.
        if el.name == "section" and "reflection-section" in classes:
            continue
        parts.append(str(el))

    return "\n".join(parts)


def build_chapter_html(filename, label, title, part_num, part_title, subtitle):
    content = extract_content(BOOK_DIR / filename)
    subtitle_html = f'<p class="chapter-subtitle"><em>{subtitle}</em></p>' if subtitle else ""
    return f"""
    <section class="chapter">
      <div class="chapter-header">
        <p class="chapter-num">{label}</p>
        <h1>{title}</h1>
        {subtitle_html}
      </div>
      <div class="chapter-body">
        {content}
      </div>
    </section>
    """


def build_appendix_html(filename, label, title):
    content = extract_content(BOOK_DIR / filename)
    return f"""
    <section class="chapter appendix">
      <div class="chapter-header">
        <p class="chapter-num">{label}</p>
        <h1>{title}</h1>
      </div>
      <div class="chapter-body">
        {content}
      </div>
    </section>
    """


def build_part_page(label, title):
    return f"""
    <section class="part-page">
      <p class="part-num">Part {label}</p>
      <h1 class="part-title">{title}</h1>
    </section>
    """


def build_toc():
    items = []
    seen_parts = set()
    for _fn, label, title, part_num, part_title, _sub in CHAPTERS:
        if part_num not in seen_parts:
            seen_parts.add(part_num)
            items.append(
                f'<div class="toc-part">'
                f'<strong>Part {part_num}: {part_title}</strong></div>'
            )
        items.append(
            f'<div class="toc-entry toc-chapter">'
            f'<span>{label}: {title}</span></div>'
        )
    items.append('<div class="toc-appendix-header">Appendices</div>')
    for _fn, label, title in APPENDICES:
        items.append(
            f'<div class="toc-entry toc-chapter">'
            f'<span>{label}: {title}</span></div>'
        )
    return "\n".join(items)


CSS = f"""
@font-face {{
    font-family: 'EB Garamond';
    src: url('file://{FONT_DIR / "EBGaramond.ttf"}');
    font-weight: normal; font-style: normal;
}}
@font-face {{
    font-family: 'EB Garamond';
    src: url('file://{FONT_DIR / "EBGaramond-Italic.ttf"}');
    font-weight: normal; font-style: italic;
}}

@page {{
    size: 5.5in 8.5in;
    margin: 0.85in 0.75in 0.9in 0.75in;
    @bottom-center {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #555;
    }}
}}
@page cover-page     {{ size: 5.5in 8.5in; margin: 0; @bottom-center {{ content: none; }} }}
@page title-page     {{ @bottom-center {{ content: none; }} }}
@page copyright-page {{ @bottom-center {{ content: none; }} }}
@page toc-page       {{ @bottom-center {{ content: none; }} }}
@page part-div-page  {{ @bottom-center {{ content: none; }} }}

body {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11.5pt;
    line-height: 1.58;
    color: #1a1a1a;
}}

/* COVER */
.cover-page {{ page: cover-page; page-break-after: always; margin: 0; padding: 0; }}
.cover-page img {{ width: 5.5in; height: 8.5in; display: block; }}

/* TITLE */
.title-page {{
    page: title-page; page-break-after: always;
    text-align: center; padding-top: 2.0in;
}}
.title-page h1 {{
    font-size: 28pt; font-weight: normal; letter-spacing: 1pt;
    line-height: 1.2; margin-bottom: 0.25in; color: #1a1a1a;
}}
.title-page .subtitle {{
    font-size: 13pt; font-style: italic; color: #4a4a4a;
    margin-bottom: 0.25in;
}}
.title-page .tagline {{
    font-size: 11pt; font-style: italic; color: #666;
    margin-bottom: 1.3in;
}}
.title-page .author  {{ font-size: 13pt; color: #1a1a1a; }}
.title-page .imprint {{ font-size: 10pt; color: #777; margin-top: 0.45in; letter-spacing: 1pt; }}

/* COPYRIGHT */
.copyright-page {{
    page: copyright-page; page-break-after: always;
    text-align: center; padding-top: 1.8in;
    font-size: 10pt; line-height: 1.65; color: #444;
}}
.copyright-page p {{ margin-bottom: 9pt; }}

/* TOC */
.toc-section {{ page: toc-page; page-break-after: always; padding-top: 0.2in; }}
.toc-section h1 {{
    font-size: 18pt; font-weight: normal; letter-spacing: 1pt;
    text-align: center; margin-bottom: 0.35in; color: #1a1a1a;
}}
.toc-part {{
    margin-top: 13pt; margin-bottom: 3pt;
    font-size: 11pt; color: #1a1a1a;
}}
.toc-entry   {{ font-size: 10.5pt; line-height: 1.7; color: #2a2a2a; text-align: left; }}
.toc-chapter {{ padding-left: 0.2in; }}
.toc-appendix-header {{
    margin-top: 14pt; margin-bottom: 3pt;
    font-size: 11pt; color: #1a1a1a; font-weight: 600;
    letter-spacing: 0.04em;
}}

/* PART DIVIDER */
.part-page {{
    page: part-div-page; page-break-before: always; page-break-after: always;
    text-align: center; padding-top: 3.2in;
}}
.part-page .part-num {{
    font-size: 11pt; letter-spacing: 0.2em; color: #B8883E;
    text-transform: uppercase; margin-bottom: 14pt;
}}
.part-page .part-title {{
    font-size: 24pt; font-weight: normal; line-height: 1.2;
    color: #1a1a1a;
}}

/* CHAPTER */
.chapter {{ page-break-before: always; }}
.chapter-header {{
    text-align: center; margin-top: 0.3in; margin-bottom: 0.32in;
    padding-bottom: 0.12in;
}}
.chapter-header .chapter-num {{
    font-size: 10pt; letter-spacing: 0.18em; color: #B8883E;
    margin-bottom: 6pt; text-transform: uppercase;
}}
.chapter-header h1 {{
    font-size: 20pt; font-weight: normal; line-height: 1.25; color: #1a1a1a;
}}
.chapter-header .chapter-subtitle {{
    font-size: 10.5pt; color: #555; text-indent: 0;
    margin-top: 5pt;
}}

/* EPIGRAPH at the top of each chapter */
section.epigraph {{
    margin: 0.15in 0.4in 0.22in 0.4in;
    text-align: center;
    page-break-inside: avoid;
}}
section.epigraph blockquote {{
    font-style: italic; font-size: 10.5pt; line-height: 1.5;
    margin: 0 0 4pt 0; border: none; padding: 0;
    color: #2a2a2a;
}}
section.epigraph cite {{
    display: block; font-style: normal;
    font-size: 9.5pt; color: #555;
}}

/* Chapter purpose callout */
.chapter-purpose {{
    margin: 0.15in 0.3in;
    padding: 0.12in 0.18in;
    border-left: 2pt solid #B8883E;
    font-size: 10.2pt; font-style: italic;
    color: #3a3a3a; line-height: 1.5;
    page-break-inside: avoid;
}}

.chapter-body p {{
    text-align: justify; text-indent: 0.28in;
    margin: 0; orphans: 2; widows: 2; hyphens: auto;
}}
.chapter-body > p:first-child {{ text-indent: 0; }}
.chapter-body h2 + p,
.chapter-body h3 + p,
.chapter-body blockquote + p,
.chapter-body .divider + p,
.chapter-body .chapter-purpose + p,
.chapter-body section.epigraph + p {{ text-indent: 0; }}

.chapter-body h2 {{
    font-size: 13pt; font-weight: 600;
    margin-top: 0.26in; margin-bottom: 0.1in;
    page-break-after: avoid; color: #1a1a1a;
}}
.chapter-body h3 {{
    font-size: 11.5pt; font-weight: 600; font-style: italic;
    margin-top: 0.2in; margin-bottom: 0.08in;
    page-break-after: avoid; color: #333;
}}

.chapter-body em     {{ font-style: italic; }}
.chapter-body strong {{ font-weight: 600; }}

.chapter-body .divider {{
    text-align: center; margin: 0.2in 0;
    color: #bbb; font-size: 9pt; letter-spacing: 0.1em;
}}

blockquote.scripture {{
    margin: 0.14in 0 0.14in 0.35in;
    padding-left: 0.22in;
    border-left: 2pt solid #B8883E;
    font-style: italic;
    font-size: 10.8pt;
    line-height: 1.5;
    page-break-inside: avoid;
}}
blockquote.scripture p {{ text-indent: 0 !important; text-align: left; margin-bottom: 0; }}
blockquote.scripture cite {{
    display: block; margin-top: 3pt;
    font-style: normal; font-size: 9.5pt; color: #4a4a4a;
    letter-spacing: 0.02em;
}}

/* Key-scripture callout box that appears in some chapters */
.key-scriptures {{
    margin: 0.18in 0.2in;
    padding: 0.12in 0.18in;
    background: #fbf6ea;
    border-left: 2pt solid #B8883E;
    font-size: 10.2pt;
    page-break-inside: avoid;
}}
.key-scriptures h3 {{
    font-size: 10.5pt; font-weight: 600; margin-top: 0;
    margin-bottom: 0.1in; color: #8b5e2b; font-style: normal;
}}

/* Tables (appendix charts) */
.chapter-body table {{
    border-collapse: collapse; margin: 0.18in 0; width: 100%;
    font-size: 9.8pt; page-break-inside: avoid;
}}
.chapter-body th, .chapter-body td {{
    border: 1px solid #bbb; padding: 4pt 6pt; vertical-align: top;
    text-align: left;
}}
.chapter-body th {{ background: #f4ead2; font-weight: 600; }}

.chapter-body ul, .chapter-body ol {{
    margin: 0.1in 0 0.1in 0.4in; padding: 0;
    font-size: 10.8pt; line-height: 1.5;
}}
.chapter-body li {{ margin-bottom: 3pt; text-indent: 0; }}
"""


def build_full_html(body, toc_html):
    cover_tag = (
        f'<div class="cover-page"><img src="file://{COVER}" alt="cover"></div>'
        if COVER.exists() else ''
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>
  {cover_tag}

  <div class="title-page">
    <h1>{TITLE}</h1>
    <p class="subtitle">{SUBTITLE}</p>
    <p class="tagline">{TAGLINE}</p>
    <p class="author">{AUTHOR}</p>
    <p class="imprint">NOBLEMIND PRESS</p>
  </div>

  <div class="copyright-page">
    <p><strong>{TITLE}: {SUBTITLE}</strong></p>
    <p>{TAGLINE}<br>Grounded in Colossians 4:5&ndash;6</p>
    <p>Copyright &copy; 2026 {AUTHOR}. All rights reserved.</p>
    <p>Published by NobleMind Press &bull; noblemind.study</p>
    <p style="margin-top:16pt;">All Scripture quotations are from the<br>
    New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p style="margin-top:16pt;">First Edition</p>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {body}
</body>
</html>"""


def main():
    print("Building chapters...")
    sections = []
    seen_parts = set()
    for entry in CHAPTERS:
        fname, label, title, part_num, part_title, subtitle = entry
        if part_num not in seen_parts:
            seen_parts.add(part_num)
            print(f"  -- Part {part_num}: {part_title}")
            sections.append(build_part_page(part_num, part_title))
        print(f"  {fname}")
        sections.append(build_chapter_html(*entry))

    print("Building appendices...")
    for fname, label, title in APPENDICES:
        print(f"  {fname}")
        sections.append(build_appendix_html(fname, label, title))

    toc_html = build_toc()
    html = build_full_html("\n".join(sections), toc_html)

    debug = BOOK_DIR / "_pdf_debug.html"
    debug.write_text(html, encoding='utf-8')

    print("Rendering PDF...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
