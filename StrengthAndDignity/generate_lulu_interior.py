#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for Strength and Dignity.

Lulu specs for 5.5" x 8.5" Digest (no bleed, text-only):
  - Page size: 5.5in x 8.5in
  - Safety margin: 0.5in minimum on all sides
  - Gutter (inside margin): 0.75in (above 0.625in recommended for 61-150 pages)
  - Outside margin: 0.625in
  - Chapters start on recto (right-hand, odd) pages
  - Alternating left/right margins for facing pages
  - All fonts embedded
  - No trim/bleed/margin lines
"""

import re
from pathlib import Path
from docx import Document
import weasyprint

BOOK_DIR = Path(__file__).parent
DOCX_DIR = BOOK_DIR.parent / "strength_and_dignity"
OUTPUT = BOOK_DIR / "Strength_and_Dignity_Lulu_Interior.pdf"

# Map of DOCX filenames to (title, chapter_label, part_subtitle)
CHAPTERS = [
    ("StrengthAndDignity_Introduction.docx", "Nobody Told You This", "Introduction", None),
    ("StrengthAndDignity_Chapter1.docx", "Your Name Is Your Most Valuable Asset", "Chapter 1", "Part One: Who You Are"),
    ("StrengthAndDignity_Chapter2.docx", "The Woman in the Mirror Isn\u2019t the Whole Story", "Chapter 2", "Part One: Who You Are"),
    ("StrengthAndDignity_Chapter3.docx", "When Nobody\u2019s Watching Becomes When Everybody\u2019s Watching", "Chapter 3", "Part One: Who You Are"),
    ("StrengthAndDignity_Chapter4.docx", "You Were Made On Purpose, For a Purpose", "Chapter 4", "Part One: Who You Are"),
    ("StrengthAndDignity_Chapter5.docx", "The Relationship You Actually Need Most", "Chapter 5", "Part Two: Who God Is"),
    ("StrengthAndDignity_Chapter6.docx", "The Bible Isn\u2019t What You Think It Is", "Chapter 6", "Part Two: Who God Is"),
    ("StrengthAndDignity_Chapter7.docx", "Putting Down the Phone Long Enough to Hear Something True", "Chapter 7", "Part Two: Who God Is"),
    ("StrengthAndDignity_Chapter8.docx", "He Is Somebody\u2019s Son", "Chapter 8", "Part Three: How You Treat People"),
    ("StrengthAndDignity_Chapter9.docx", "The Friends You Choose Will Choose Your Future", "Chapter 9", "Part Three: How You Treat People"),
    ("StrengthAndDignity_Chapter10.docx", "Honor Your Father and Mother (Even When It\u2019s Hard)", "Chapter 10", "Part Three: How You Treat People"),
    ("StrengthAndDignity_Chapter11.docx", "Work Like It Matters Because It Does", "Chapter 11", "Part Four: How You Build a Life"),
    ("StrengthAndDignity_Chapter12.docx", "Money Will Test Your Character", "Chapter 12", "Part Four: How You Build a Life"),
    ("StrengthAndDignity_Chapter13.docx", "The Church Is Not Optional", "Chapter 13", "Part Four: How You Build a Life"),
    ("StrengthAndDignity_Conclusion.docx", "Your Move", "Conclusion", None),
]


def is_all_bold(para):
    """Check if the entire paragraph is bold."""
    if not para.runs:
        return False
    return all(run.bold for run in para.runs if run.text.strip())


def is_all_italic(para):
    """Check if the entire paragraph is italic."""
    if not para.runs:
        return False
    return all(run.italic for run in para.runs if run.text.strip())


def is_bold_italic(para):
    """Check if the entire paragraph is both bold and italic."""
    if not para.runs:
        return False
    return all(run.bold and run.italic for run in para.runs if run.text.strip())


def format_inline(para):
    """Convert paragraph runs to HTML with inline formatting."""
    parts = []
    for run in para.runs:
        text = run.text
        if not text:
            continue
        # Escape HTML entities
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if run.bold and run.italic:
            parts.append(f"<strong><em>{text}</em></strong>")
        elif run.bold:
            parts.append(f"<strong>{text}</strong>")
        elif run.italic:
            parts.append(f"<em>{text}</em>")
        else:
            parts.append(text)
    return "".join(parts)


def is_divider_line(text):
    """Check if a paragraph is a horizontal rule / divider."""
    stripped = text.strip()
    if re.match(r'^[\u2500\u2014\u2013_\-=]{3,}$', stripped):
        return True
    return False


def is_citation_line(text):
    """Check if a paragraph is a citation line (starts with em-dash)."""
    stripped = text.strip()
    return stripped.startswith("\u2014") or stripped.startswith("—") or stripped.startswith("-- ")


def is_scripture_quote(para):
    """Check if a paragraph is a scripture blockquote (all italic, starts with quote)."""
    text = para.text.strip()
    if not text:
        return False
    if is_all_italic(para) and (text.startswith('"') or text.startswith('\u201c')):
        return True
    return False


def extract_chapter_content(filepath):
    """Extract content from a DOCX file, returning a list of HTML strings."""
    doc = Document(str(filepath))
    paragraphs = doc.paragraphs

    # Skip the first two paragraphs (chapter label + title)
    start_idx = 0
    if len(paragraphs) > 0 and is_all_bold(paragraphs[0]):
        start_idx = 1
    if len(paragraphs) > start_idx and is_all_bold(paragraphs[start_idx]):
        start_idx += 1

    html_parts = []
    i = start_idx
    in_study_section = False
    study_section_parts = []

    while i < len(paragraphs):
        para = paragraphs[i]
        text = para.text.strip()

        if not text:
            i += 1
            continue

        # Check for divider lines
        if is_divider_line(text):
            if in_study_section:
                study_section_parts.append('<div class="divider">*&emsp;*&emsp;*</div>')
            else:
                html_parts.append('<div class="divider">*&emsp;*&emsp;*</div>')
            i += 1
            continue

        # Check for "For Further Study" heading
        if text == "For Further Study" and (is_bold_italic(para) or is_all_bold(para)):
            in_study_section = True
            study_section_parts.append('<h2>For Further Study</h2>')
            i += 1
            continue

        # Check for bullet points
        if text.startswith("•") or text.startswith("\u2022"):
            bullet_items = []
            while i < len(paragraphs) and (paragraphs[i].text.strip().startswith("•") or paragraphs[i].text.strip().startswith("\u2022")):
                bullet_text = paragraphs[i].text.strip()
                bullet_text = re.sub(r'^[•\u2022]\s*', '', bullet_text)
                bullet_text = bullet_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                bullet_items.append(f"<li>{bullet_text}</li>")
                i += 1
            ul_html = "<ul>\n" + "\n".join(bullet_items) + "\n</ul>"
            if in_study_section:
                study_section_parts.append(ul_html)
            else:
                html_parts.append(ul_html)
            continue

        # Check if this is a scripture quote (all italic, starts with quote mark)
        if is_scripture_quote(para):
            quote_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cite_html = ""
            if i + 1 < len(paragraphs) and is_citation_line(paragraphs[i + 1].text.strip()):
                cite_text = paragraphs[i + 1].text.strip()
                cite_text = cite_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                cite_html = f"\n<cite>{cite_text}</cite>"
                i += 1

            remaining_non_empty = [p for p in paragraphs[i + 1:] if p.text.strip()]
            if in_study_section and len(remaining_non_empty) == 0:
                epigraph_html = f'<section class="epigraph">\n<blockquote><p>{quote_text}</p></blockquote>{cite_html}\n</section>'
                study_section_parts.append(epigraph_html)
            else:
                blockquote_html = f'<blockquote class="scripture">\n<p>{quote_text}</p>{cite_html}\n</blockquote>'
                if in_study_section:
                    study_section_parts.append(blockquote_html)
                else:
                    html_parts.append(blockquote_html)
            i += 1
            continue

        # Check for citation line without preceding scripture
        if is_citation_line(text):
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            target = study_section_parts if in_study_section else html_parts
            target.append(f"<p>{escaped}</p>")
            i += 1
            continue

        # Check for bold+italic paragraph (principle box)
        if is_bold_italic(para):
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            target = study_section_parts if in_study_section else html_parts
            target.append(f'<div class="principle-box"><p><em>{escaped}</em></p></div>')
            i += 1
            continue

        # Check for bold section heading
        if is_all_bold(para) and not is_all_italic(para) and len(text) < 100:
            target = study_section_parts if in_study_section else html_parts
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            target.append(f"<h2>{escaped}</h2>")
            i += 1
            continue

        # Regular paragraph
        inline_html = format_inline(para)
        if not inline_html.strip():
            i += 1
            continue
        target = study_section_parts if in_study_section else html_parts
        target.append(f"<p>{inline_html}</p>")
        i += 1

    # Close study section if open
    if in_study_section and study_section_parts:
        html_parts.append('<div class="study-section">')
        html_parts.extend(study_section_parts)
        html_parts.append('</div>')

    return "\n".join(html_parts)


def build_chapter_html(docx_filename, title, chapter_label, part_subtitle):
    """Build the HTML section for a single chapter."""
    filepath = DOCX_DIR / docx_filename
    content = extract_chapter_content(filepath)

    header_parts = []
    if chapter_label and chapter_label != "Introduction" and chapter_label != "Conclusion":
        header_parts.append(f'<p class="chapter-num">{chapter_label}</p>')
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

    toc_items.append('<div class="toc-entry"><span>Introduction: Nobody Told You This</span></div>')

    current_part = None
    for docx_file, title, chapter_label, part in CHAPTERS[1:-1]:  # skip intro and conclusion
        if part != current_part:
            current_part = part
            toc_items.append(f'<div class="toc-part"><strong>{part}</strong></div>')
        num = chapter_label.replace("Chapter ", "")
        toc_items.append(
            f'<div class="toc-entry toc-chapter">'
            f"<span>Chapter {num}: {title}</span>"
            f"</div>"
        )

    toc_items.append('<div class="toc-entry" style="margin-top: 12pt;"><span>Conclusion: Your Move</span></div>')

    return "\n".join(toc_items)


# Lulu interior CSS — 5.5" x 8.5" Digest, no bleed
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

/* === PAGE SETUP ===
   5.5" x 8.5" Digest, no bleed.
   Gutter (inside) = 0.75in, Outside = 0.625in
   Top = 0.75in, Bottom = 0.75in
   Right-hand (recto) pages = odd = gutter on left, outside on right
   Left-hand (verso) pages = even = gutter on right, outside on left
*/

@page {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
}

/* Recto (right-hand, odd pages): gutter LEFT, outside RIGHT */
@page :right {
    margin-left: 0.75in;   /* gutter */
    margin-right: 0.625in; /* outside */

    @bottom-right {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

/* Verso (left-hand, even pages): gutter RIGHT, outside LEFT */
@page :left {
    margin-left: 0.625in;  /* outside */
    margin-right: 0.75in;  /* gutter */

    @bottom-left {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

/* --- Front matter: no page numbers on title, copyright, TOC --- */
@page title-page {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page copyright-page {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page toc-page:right {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page toc-page:left {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

/* Blank verso pages inserted by break-before: right */
@page :blank {
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}


/* === BODY === */
body {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    text-rendering: optimizeLegibility;
}

/* === TITLE PAGE (page 1, recto) === */
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
    margin-bottom: 0.3in;
    color: #1a1a1a;
}
.title-page .subtitle-line {
    font-size: 13pt;
    color: #333;
    margin-bottom: 4pt;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 0.8in;
    color: #1a1a1a;
}

/* === COPYRIGHT PAGE (page 2, verso) === */
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

/* === TABLE OF CONTENTS (starts recto) === */
.toc-section {
    page: toc-page;
    break-before: right;
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

/* === CHAPTERS — start on recto (right-hand) pages === */
.chapter {
    break-before: right;
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

/* No indent after headings, dividers, quotes */
.chapter-body h2 + p,
.chapter-body .divider + p,
.chapter-body .scripture + p,
.chapter-body .principle-box + p,
.chapter-body .epigraph + p,
.chapter-body .study-section + p,
.chapter-body ul + p,
.chapter-body blockquote + p {
    text-indent: 0;
}

.chapter-body > p:first-child {
    text-indent: 0;
}

/* === SECTION HEADINGS — keep with following text === */
.chapter-body h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.3in;
    margin-bottom: 0.12in;
    page-break-after: avoid;
    break-after: avoid;
    orphans: 3;
    widows: 3;
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
    page-break-before: avoid;
}

/* === BULLET LISTS === */
ul {
    margin: 0.12in 0 0.12in 0.4in;
    padding-left: 0.2in;
    font-size: 10.5pt;
    line-height: 1.55;
}

ul li {
    margin-bottom: 4pt;
}

/* === STUDY SECTION === */
.study-section {
    margin-top: 0.25in;
}

.study-section h2 {
    font-size: 13pt;
    font-weight: bold;
    font-style: italic;
    color: #1a1a1a;
    margin-top: 0.3in;
    margin-bottom: 0.12in;
}

.study-section p {
    font-size: 10.5pt;
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

  <!-- TITLE PAGE (page 1, recto) -->
  <div class="title-page">
    <h1>Your Name<br>Means Everything</h1>
    <p class="subtitle-line">Strength and Dignity</p>
    <p class="subtitle-line" style="font-size: 11pt; margin-top: 0.3in;">What the Bible Says to Young Women</p>
    <p class="subtitle-line" style="font-size: 11pt;">About Character, Wisdom, and Faith</p>
    <p class="author">Paul &amp; Pam Hainline</p>
  </div>

  <!-- COPYRIGHT PAGE (page 2, verso) -->
  <div class="copyright-page">
    <p class="book-title">Your Name Means Everything: Strength and Dignity</p>
    <p>Copyright &copy; 2026 Paul &amp; Pam Hainline<br>All rights reserved.</p>
    <p>Scripture quotations are from the New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p class="edition">First Edition</p>
  </div>

  <!-- TABLE OF CONTENTS (starts recto via break-before: right) -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- CHAPTERS (each starts recto via break-before: right) -->
  {chapter_sections}

</body>
</html>"""


def main():
    print("Generating Lulu interior PDF (5.5\" x 8.5\")...")
    print()

    print("Extracting chapter content from DOCX files...")
    chapter_sections = []
    for docx_file, title, chapter_label, part_subtitle in CHAPTERS:
        print(f"  {docx_file}")
        chapter_sections.append(
            build_chapter_html(docx_file, title, chapter_label, part_subtitle)
        )

    print("Building table of contents...")
    toc_html = build_toc()

    print("Assembling HTML...")
    full_html = build_full_html("\n".join(chapter_sections), toc_html)

    # Save intermediate HTML for debugging
    debug_html = BOOK_DIR / "_lulu_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")

    print("Generating PDF with WeasyPrint (fonts will be embedded)...")
    doc = weasyprint.HTML(string=full_html)
    doc.write_pdf(str(OUTPUT))

    # Clean up
    debug_html.unlink(missing_ok=True)

    print(f"\nPDF saved to {OUTPUT}")
    print(f"  Page size: 5.5\" x 8.5\" (Digest)")
    print(f"  Gutter: 0.75in inside, 0.625in outside")
    print(f"  Chapters: start on recto (right-hand) pages")
    print(f"  Fonts: EB Garamond (embedded)")
    print("Done.")


if __name__ == "__main__":
    main()
