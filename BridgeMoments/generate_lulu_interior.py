#!/usr/bin/env python3
"""Generate the Lulu print-ready INTERIOR PDF for 'Bridge Moments'.

Modeled on generate_pdf.py (the reader PDF), but with Lulu's interior
conventions:
  - 5.5" x 8.5", no cover page (Lulu uploads the cover separately)
  - Mirror margins: gutter 0.75", outside 0.625" (alternating)
  - Recto starts for title page, TOC, part dividers, chapters
  - Page numbers in bottom outside corner (alternating), suppressed
    on front matter and part-divider/chapter opening pages
  - Front matter: half-title -> title -> copyright -> TOC -> body
    (no dedication per author's choice for this title)

Source: the existing chapter-NN.html and appendix-X.html files.
"""

from pathlib import Path
from bs4 import BeautifulSoup
import weasyprint

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "BridgeMoments_Lulu_Interior.pdf"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"

TITLE = "Bridge Moments"
SUBTITLE = "Making the Most of Every Opportunity"
TAGLINE = "A Bible Study on Conversational Evangelism"
AUTHOR = "Paul Hainline"

CHAPTERS = [
    ("chapter-01.html", "Chapter 1",  "The Weight of Words",                               1, "The Foundation: Why Words Matter",                  ""),
    ("chapter-02.html", "Chapter 2",  "The Kairos Principle",                              1, "The Foundation: Why Words Matter",                  ""),
    ("chapter-03.html", "Chapter 3",  "Love, Not Agenda",                                  1, "The Foundation: Why Words Matter",                  ""),
    ("chapter-04.html", "Chapter 4",  "“Give Me a Drink”",                       2, "The Master’s Method: Jesus’ Bridge Moments", "The Woman at the Well • John 4:1–42"),
    ("chapter-05.html", "Chapter 5",  "“You Must Be Born Again”",                2, "The Master’s Method: Jesus’ Bridge Moments", "Nicodemus • John 3:1–21"),
    ("chapter-06.html", "Chapter 6",  "“I Must Stay at Your House”",             2, "The Master’s Method: Jesus’ Bridge Moments", "Zacchaeus • Luke 19:1–10"),
    ("chapter-07.html", "Chapter 7",  "Jesus Felt a Love for Him",                         2, "The Master’s Method: Jesus’ Bridge Moments", "The Rich Young Ruler • Mark 10:17–27"),
    ("chapter-08.html", "Chapter 8",  "“Neither Do I Condemn You”",              2, "The Master’s Method: Jesus’ Bridge Moments", "The Woman Caught in Adultery • John 8:1–11"),
    ("chapter-09.html", "Chapter 9",  "Were Not Our Hearts Burning?",                      2, "The Master’s Method: Jesus’ Bridge Moments", "The Road to Emmaus • Luke 24:13–35"),
    ("chapter-10.html", "Chapter 10", "“Follow Me”",                             2, "The Master’s Method: Jesus’ Bridge Moments", "The Calling of the First Disciples • John 1:35–51"),
    ("chapter-11.html", "Chapter 11", "“Do You See This Woman?”",                2, "The Master’s Method: Jesus’ Bridge Moments", "Simon’s House • Luke 7:36–50"),
    ("chapter-12.html", "Chapter 12", "“Do You Love Me?”",                       2, "The Master’s Method: Jesus’ Bridge Moments", "Peter’s Restoration • John 21:1–19"),
    ("chapter-13.html", "Chapter 13", "“Do You Understand What You Are Reading?”",3, "The Pattern Continued: Bridge Moments in Acts",      "Philip & the Ethiopian • Acts 8:26–40"),
    ("chapter-14.html", "Chapter 14", "“Men of Athens”",                          3, "The Pattern Continued: Bridge Moments in Acts",      "Paul on Mars Hill • Acts 17:16–34"),
    ("chapter-15.html", "Chapter 15", "“What Must I Do to Be Saved?”",           3, "The Pattern Continued: Bridge Moments in Acts",      "The Philippian Jailer • Acts 16:16–34"),
    ("chapter-16.html", "Chapter 16", "Learning to Listen",                                 4, "The Practice: Living with Bridge Moment Eyes",       "Hearing What People Are Really Saying • James 1:19"),
    ("chapter-17.html", "Chapter 17", "From Natural to Spiritual",                          4, "The Practice: Living with Bridge Moment Eyes",       "Building the Bridge • 1 Peter 3:15"),
    ("chapter-18.html", "Chapter 18", "Seasoned with Salt",                                 4, "The Practice: Living with Bridge Moment Eyes",       "Speaking Truth with Grace • Colossians 4:6"),
    ("chapter-19.html", "Chapter 19", "When They Walk Away",                                4, "The Practice: Living with Bridge Moment Eyes",       "Handling Rejection with Grace • 1 Corinthians 3:6–7"),
    ("chapter-20.html", "Chapter 20", "The Heart Behind the Words",                         4, "The Practice: Living with Bridge Moment Eyes",       "Love as the Only Foundation • 1 Corinthians 13:1–3"),
]

APPENDICES = [
    ("appendix-a.html", "Appendix A", "Quick Reference Chart"),
    ("appendix-b.html", "Appendix B", "Scripture Index"),
    ("appendix-c.html", "Appendix C", "Small Group Exercises"),
]


# ---------------------------------------------------------------------------
# Content extraction (identical to generate_pdf.py)
# ---------------------------------------------------------------------------
EXCLUDE_CLASSES = {
    "nav-controls", "mark-complete", "footer-nav", "reflection-section",
    "part-label", "part-title", "chapter-num",
}


def extract_content(filepath):
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


def build_part_page(num, title):
    return f"""
    <section class="part-page">
      <p class="part-num">Part {num}</p>
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


# ---------------------------------------------------------------------------
# CSS — Lulu interior layout (mirror margins, recto starts, no cover)
# ---------------------------------------------------------------------------

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

/* === PAGE SETUP — 5.5x8.5, gutter 0.75, outside 0.625 ===
   Right (recto) pages: page number bottom-right (outside).
   Left  (verso) pages: page number bottom-left  (outside). */
@page {{
    size: 5.5in 8.5in;
    margin-top: 0.85in;
    margin-bottom: 0.9in;
}}
@page :right {{
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #555;
    }}
}}
@page :left {{
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-left {{
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #555;
    }}
}}

/* Front-matter pages: same margins, but no page number. */
@page front-matter {{
    size: 5.5in 8.5in;
    margin-top: 0.85in; margin-bottom: 0.9in;
    @bottom-right {{ content: none; }}
    @bottom-left  {{ content: none; }}
}}
@page front-matter:right {{ margin-left: 0.75in; margin-right: 0.625in; }}
@page front-matter:left  {{ margin-left: 0.625in; margin-right: 0.75in; }}

/* TOC sits in front matter too — no page numbers. */
@page toc-page {{
    size: 5.5in 8.5in;
    margin-top: 0.85in; margin-bottom: 0.9in;
    @bottom-right {{ content: none; }}
    @bottom-left  {{ content: none; }}
}}
@page toc-page:right {{ margin-left: 0.75in; margin-right: 0.625in; }}
@page toc-page:left  {{ margin-left: 0.625in; margin-right: 0.75in; }}

/* Part divider pages — no page number on the divider face itself. */
@page part-div-page {{
    size: 5.5in 8.5in;
    margin-top: 0.85in; margin-bottom: 0.9in;
    @bottom-right {{ content: none; }}
    @bottom-left  {{ content: none; }}
}}
@page part-div-page:right {{ margin-left: 0.75in; margin-right: 0.625in; }}
@page part-div-page:left  {{ margin-left: 0.625in; margin-right: 0.75in; }}

@page :blank {{
    @bottom-right {{ content: none; }}
    @bottom-left  {{ content: none; }}
}}

body {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11.5pt;
    line-height: 1.58;
    color: #1a1a1a;
}}

/* === FRONT MATTER === */
.half-title-page {{
    page: front-matter; break-before: right; page-break-after: always;
    text-align: center; padding-top: 3.2in;
}}
.half-title-page h1 {{
    font-size: 18pt; font-weight: normal; letter-spacing: 0.04em;
    color: #1a1a1a; line-height: 1.25;
}}

.title-page {{
    page: front-matter; break-before: right; page-break-after: always;
    text-align: center; padding-top: 1.8in;
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

/* Copyright flows to the natural next page (verso of title) — no forced break. */
.copyright-page {{
    page: front-matter; page-break-after: always;
    text-align: center; padding-top: 1.8in;
    font-size: 10pt; line-height: 1.65; color: #444;
}}
.copyright-page p {{ margin-bottom: 9pt; }}

/* TOC must start on recto. */
.toc-section {{
    page: toc-page; break-before: right; page-break-after: always;
    padding-top: 0.2in;
}}
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

/* === PART DIVIDER — recto start === */
.part-page {{
    page: part-div-page; break-before: right; page-break-after: always;
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

/* === CHAPTER — recto start === */
.chapter {{ break-before: right; }}
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
    font-size: 10.5pt; color: #555; text-indent: 0; margin-top: 5pt;
}}

/* EPIGRAPH */
section.epigraph {{
    margin: 0.15in 0.4in 0.22in 0.4in;
    text-align: center; page-break-inside: avoid;
}}
section.epigraph blockquote {{
    font-style: italic; font-size: 10.5pt; line-height: 1.5;
    margin: 0 0 4pt 0; border: none; padding: 0; color: #2a2a2a;
}}
section.epigraph cite {{
    display: block; font-style: normal; font-size: 9.5pt; color: #555;
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
    font-style: italic; font-size: 10.8pt; line-height: 1.5;
    page-break-inside: avoid;
}}
blockquote.scripture p {{ text-indent: 0 !important; text-align: left; margin-bottom: 0; }}
blockquote.scripture cite {{
    display: block; margin-top: 3pt;
    font-style: normal; font-size: 9.5pt; color: #4a4a4a;
    letter-spacing: 0.02em;
}}

.key-scriptures {{
    margin: 0.18in 0.2in;
    padding: 0.12in 0.18in;
    background: #fbf6ea;
    border-left: 2pt solid #B8883E;
    font-size: 10.2pt; page-break-inside: avoid;
}}
.key-scriptures h3 {{
    font-size: 10.5pt; font-weight: 600; margin-top: 0;
    margin-bottom: 0.1in; color: #8b5e2b; font-style: normal;
}}

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
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <div class="half-title-page">
    <h1>{TITLE}</h1>
  </div>

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
    print("Building Lulu interior for 'Bridge Moments'...")
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

    print("Appendices...")
    for fname, label, title in APPENDICES:
        print(f"  {fname}")
        sections.append(build_appendix_html(fname, label, title))

    toc_html = build_toc()
    html = build_full_html("\n".join(sections), toc_html)

    debug = BOOK_DIR / "_lulu_debug.html"
    debug.write_text(html, encoding="utf-8")

    print("Rendering Lulu interior PDF...")
    weasyprint.HTML(string=html, base_url=str(BOOK_DIR)).write_pdf(str(OUTPUT))
    print(f"Wrote {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")

    debug.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
