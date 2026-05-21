#!/usr/bin/env python3
"""Generate the Lulu print interior PDF for The Love God Calls Us To.

5.5" x 8.5" with mirror margins:
  - gutter 0.75"
  - outside 0.625"
  - top 0.85", bottom 0.9"
Alternating facing-page margins. Chapter sections start recto.
No cover (Lulu uses a separate cover file).
Page numbers alternate to outside corners (bottom).

Usage:
    python3 generate_lulu_interior.py             # general edition
    python3 generate_lulu_interior.py --class     # class edition
"""

import argparse
from pathlib import Path

import weasyprint

import _book_source as bs

BOOK_DIR = Path(__file__).parent
FONT_DIR = Path.home() / ".local/share/fonts"


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

/* Mirror-margin pages for Lulu interior. Page numbers alternate to
   the outside (right corner on recto, left corner on verso). */

@page :right {
    size: 5.5in 8.5in;
    margin: 0.85in 0.625in 0.9in 0.75in;  /* top right bottom left (gutter on left for recto) */
    @bottom-right {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #333;
    }
}

@page :left {
    size: 5.5in 8.5in;
    margin: 0.85in 0.75in 0.9in 0.625in;  /* top right bottom left (gutter on right for verso) */
    @bottom-left {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9.5pt;
        color: #333;
    }
}

/* Front matter pages get no numbers */
@page title-page { @bottom-right { content: none; } @bottom-left { content: none; } }
@page copyright-page { @bottom-right { content: none; } @bottom-left { content: none; } }
@page dedication-page { @bottom-right { content: none; } @bottom-left { content: none; } }
@page toc-page { @bottom-right { content: none; } @bottom-left { content: none; } }
@page :first { @bottom-right { content: none; } @bottom-left { content: none; } }

body {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    text-rendering: optimizeLegibility;
}

.title-page {
    page: title-page;
    page-break-after: always;
    text-align: center;
    padding-top: 2in;
}
.title-page h1 { font-size: 26pt; font-weight: bold; line-height: 1.25; margin-bottom: 0.2in; color: #1a1a1a; }
.title-page .subtitle-line { font-size: 12pt; font-style: italic; color: #444; margin-bottom: 6pt; }
.title-page .author { font-size: 14pt; margin-top: 0.8in; color: #1a1a1a; }

.copyright-page {
    page: copyright-page;
    page-break-after: always;
    text-align: center;
    padding-top: 3in;
    font-size: 9.5pt;
    line-height: 1.7;
    color: #444;
}
.copyright-page p { margin-bottom: 10pt; }
.copyright-page .edition { margin-top: 18pt; }

.toc-section {
    page: toc-page;
    page-break-after: always;
    page-break-before: right;  /* recto */
}
.toc-section h1 { font-size: 18pt; font-weight: bold; margin-bottom: 0.35in; color: #1a1a1a; text-align: center; }
.toc-entry { font-size: 10.5pt; line-height: 1.8; color: #333; }

/* Chapters start on recto (right page) */
.chapter { page-break-before: right; }

.chapter-header { text-align: center; margin-bottom: 0.3in; padding-top: 0.6in; padding-bottom: 0.15in; }
.chapter-header .chapter-num { font-size: 10pt; letter-spacing: 0.08em; color: #555; margin-bottom: 2pt; text-transform: uppercase; }
.chapter-header h1 { font-size: 20pt; font-weight: bold; color: #1a1a1a; margin-bottom: 6pt; line-height: 1.2; }

.chapter-body p { text-align: justify; text-indent: 0.3in; margin-bottom: 0; margin-top: 0; orphans: 2; widows: 2; }
.chapter-body h2 + p, .chapter-body .divider + p, .chapter-body .scripture + p,
.chapter-body .epigraph + p { text-indent: 0; }
.chapter-body > p:first-child { text-indent: 0; }
.chapter-body blockquote + p { text-indent: 0; }

.chapter-body h2 { font-size: 13pt; font-weight: bold; color: #1a1a1a; margin-top: 0.3in; margin-bottom: 0.12in; page-break-after: avoid; }
.chapter-body h3 { font-size: 12pt; font-weight: bold; color: #333; margin-top: 0.25in; margin-bottom: 0.1in; page-break-after: avoid; }

blockquote.scripture {
    margin: 0.15in 0 0.15in 0.4in; padding: 0;
    font-style: italic; font-size: 10.5pt; line-height: 1.5;
    border-left: 2pt solid #C4513F; padding-left: 0.18in;
}
blockquote.scripture p { text-indent: 0 !important; text-align: left; margin-bottom: 0; }
blockquote.scripture cite { display: block; margin-top: 3pt; font-style: normal; font-variant: small-caps; letter-spacing: 0.05em; font-size: 9pt; color: #C4513F; }

.divider { text-align: center; margin: 0.2in 0; color: #888; font-size: 10pt; letter-spacing: 0.15em; }

.reflection { page-break-inside: avoid; margin-top: 0.35in; padding-top: 0.15in; border-top: 0.5pt solid #ccc; }
.reflection-header h3 { font-size: 11pt; font-variant: small-caps; letter-spacing: 0.15em; color: #555; margin-bottom: 0.1in; text-align: center; }
.reflection-body p { text-indent: 0; }

em { font-style: italic; }
strong { font-weight: bold; }

/* Scripture Index back-matter section */
.scripture-index .chapter-body { font-size: 10.5pt; line-height: 1.45; }
.scripture-index .chapter-body p { text-indent: 0; }
.si-intro { font-style: italic; color: #444; margin-bottom: 0.2in !important; text-align: left !important; }
.si-book { font-size: 12pt; font-weight: bold; color: #1a1a1a; margin-top: 0.18in !important; margin-bottom: 0.06in !important; page-break-after: avoid; }
.si-entry { font-size: 10pt; line-height: 1.45; padding-left: 0.2in; margin-top: 0 !important; margin-bottom: 2pt !important; text-align: left !important; }
.si-ref { display: inline-block; min-width: 1.6in; font-variant: small-caps; letter-spacing: 0.02em; color: #1a1a1a; }
.si-locations { color: #555; }
"""


def build_chapter_html(section):
    parts = ['<section class="chapter">']
    parts.append('<div class="chapter-header">')
    if section["label_meta"]:
        parts.append(f'<p class="chapter-num">{section["label_meta"]}</p>')
    parts.append(f'<h1>{section["title_meta"]}</h1>')
    parts.append('</div>')
    parts.append('<div class="chapter-body">')
    if section["epigraph_html"]:
        parts.append(section["epigraph_html"])
    parts.append(section["body_html"])
    parts.append('</div>')
    parts.append('</section>')
    return "\n".join(parts)


def build_toc(sections):
    items = []
    for s in sections:
        if s["label_meta"] in ("Inscription & Dedication",):
            label = "Dedication"
        elif s["label_meta"] in ("Preface",):
            label = "Preface"
        elif s["label_meta"].startswith("Chapter"):
            label = f'{s["label_meta"]}: {s["title_meta"]}'
        elif s["label_meta"].startswith("Appendix"):
            label = f'{s["label_meta"]}: {s["title_meta"]}'
        else:
            label = s["title_meta"]
        items.append(f'<div class="toc-entry">{label}</div>')
    return "\n".join(items)


def build_full_html(class_edition, sections):
    edition_note = "Class Edition" if class_edition else ""
    toc_html = build_toc(sections)
    chapter_html = "\n".join(build_chapter_html(s) for s in sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>

  <div class="title-page">
    <h1>{bs.TITLE}</h1>
    <p class="subtitle-line">{bs.SUBTITLE}</p>
    <p class="author">{bs.AUTHOR}</p>
  </div>

  <div class="copyright-page">
    <p><em>{bs.TITLE}</em></p>
    <p>{bs.SUBTITLE}</p>
    <p>Copyright &copy; {bs.YEAR} {bs.AUTHOR}<br>All rights reserved.</p>
    <p>Scripture quotations are from the New American Standard Bible&reg; (NASB),<br>
    Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p class="edition">First Edition &mdash; {bs.PUBLISHER}{(' &mdash; ' + edition_note) if edition_note else ''}</p>
  </div>

  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  {chapter_html}

</body>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="class_edition", action="store_true",
                    help="Build the class-edition dedication instead of the general one")
    args = ap.parse_args()

    print(f"Loading sections (class_edition={args.class_edition})...")
    sections = bs.load_all_sections(class_edition=args.class_edition)
    print(f"  Loaded {len(sections)} sections")

    print("Building HTML...")
    full_html = build_full_html(args.class_edition, sections)

    debug_html = BOOK_DIR / "_lulu_debug.html"
    debug_html.write_text(full_html, encoding="utf-8")

    out_name = "The_Love_God_Calls_Us_To_Lulu_Interior"
    if args.class_edition:
        out_name += "_ClassEdition"
    output = BOOK_DIR / f"{out_name}.pdf"

    print("Generating Lulu interior PDF with WeasyPrint...")
    weasyprint.HTML(string=full_html).write_pdf(str(output))
    print(f"\nLulu interior saved to {output}")
    debug_html.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
