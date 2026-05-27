#!/usr/bin/env python3
"""Build downloadable PDFs for the OT timeline spokes.

Path A approach: take each spoke's existing HTML and run it through
WeasyPrint with a print-override stylesheet that drops interactive
elements (filter pills, click handlers, sticky bars) and tunes page
breaks, while preserving the spoke's visual identity (parchment
palette, IM Fell English / Crimson Text typography, the colored
side-bars, etc.).

Skips:
  - the-tabernacle:     the SVG floor plan + clickable hotspots IS
                        the spoke; flattening loses the value.
  - the-divided-kingdom: the JS-rendered two-track synoptic chart
                        likewise — would need a separate king-by-king
                        table treatment, which is a different artifact.

Output: each spoke's directory gets a properly-titled PDF alongside
its index.html, e.g. the-covenants/The_Covenants.pdf.

Usage:
    python3 tools/build_spoke_pdfs.py            # build all
    python3 tools/build_spoke_pdfs.py the-covenants  # build one
"""

from __future__ import annotations
import sys
from pathlib import Path
from weasyprint import HTML, CSS

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent


# (slug, output filename, friendly label)
SPOKES = [
    ("genesis-genealogy",      "Genesis_Genealogy.pdf",         "Genesis Genealogy"),
    ("the-lamb-god-provides",  "The_Lamb_God_Provides.pdf",     "The Lamb God Provides"),
    ("the-kinsman-redeemer",   "The_Kinsman_Redeemer.pdf",      "The Kinsman-Redeemer"),
    ("the-covenants",          "The_Covenants.pdf",             "The Covenants of God"),
    ("the-day-of-atonement",   "The_Day_of_Atonement.pdf",      "The Day of Atonement"),
    ("the-appointed-times",    "The_Appointed_Times.pdf",       "The Appointed Times of the LORD"),
    ("the-promise-threads",    "Promise_Threads.pdf",           "Promise Threads"),
    ("the-united-kingdom",     "The_United_Kingdom.pdf",        "The United Kingdom"),
    ("the-prophecies",         "The_Prophecies.pdf",            "The Prophecies"),
]


# ============================================================
# Print-override CSS — applied on top of each spoke's own styles.
# Goal: drop the interactive bits, force expandable content open,
# clean up page-break behavior. Preserve the parchment palette.
# ============================================================

PRINT_CSS = r"""
@page {
    size: 8.5in 11in;
    margin: 0.65in 0.6in 0.7in 0.6in;
}

/* Page numbers at the bottom */
@page {
    @bottom-center {
        content: counter(page);
        font-family: 'IM Fell English', Georgia, serif;
        color: #6B4C1A;
        font-size: 10pt;
        margin-top: 0.2in;
    }
}

/* Hide interactive / navigation elements that don't belong in a PDF */
.backlink,
.filter-bar,
.filter-pill,
.external-link,
button,
nav.filter-bar {
    display: none !important;
}

/* Force <details> panels open so the About / Notes content prints */
details {
    display: block !important;
}
details > summary {
    display: block !important;
    padding-bottom: 8px !important;
    border-bottom: 1px solid #E8D9B5 !important;
    cursor: default !important;
    list-style: none !important;
}
details > summary::marker,
details > summary::-webkit-details-marker {
    display: none !important;
}
details[open] > summary {
    border-bottom: 1px solid #E8D9B5 !important;
}
details > .body {
    display: block !important;
    padding-top: 12px !important;
}

/* Make sure cards that are filter-hidden (Prophecies) still print all of them */
.prophecy.hidden,
.hidden {
    display: block !important;
}

/* Empty filter state (Prophecies) — never relevant in PDF */
.empty-state {
    display: none !important;
}

/* Page-break discipline
 * Only the SMALL atomic units get break-inside:avoid. Larger cards
 * (.covenant-card, .king, .thread, .feast, .prophecy, .step) are big
 * enough that forbidding internal breaks leaves wasted half-pages.
 * Let those flow naturally and use orphans/widows to keep them clean. */
.panel,
.stat-grid,
.goat-card,
.stage,
.quote {
    break-inside: avoid;
    page-break-inside: avoid;
}

/* Don't strand a heading at the bottom of a page */
h1, h2, h3, h4 {
    break-after: avoid;
    page-break-after: avoid;
}

/* General paragraph-orphan/widow control */
p, blockquote {
    orphans: 3;
    widows: 3;
}

/* Drop the fixed parchment texture overlay (slow + irrelevant for print) */
body::before {
    display: none !important;
}

/* Trim outer spacing so content uses the page */
body {
    background: #F5EDD6 !important;
    padding: 0 !important;
    margin: 0 !important;
}

header.page-header {
    padding: 18px 12px 16px !important;
    margin-bottom: 14px !important;
}
header.page-header h1 {
    font-size: 28pt !important;
}
header.page-header h2 {
    font-size: 14pt !important;
}
header.page-header p.lede {
    font-size: 11pt !important;
}

.wrap {
    max-width: none !important;
    padding: 14px 6px 20px !important;
}

/* Footer */
footer.page-footer {
    margin-top: 24px !important;
    padding-top: 12px !important;
    border-top: 1px solid #C4A44A !important;
    font-size: 9.5pt !important;
}
"""


def build(slug: str, output: str, label: str) -> Path:
    html_path = PROJECT_DIR / slug / "index.html"
    pdf_path = PROJECT_DIR / slug / output
    if not html_path.exists():
        raise FileNotFoundError(f"Spoke HTML missing: {html_path}")

    # base_url is required so WeasyPrint can resolve relative font URLs etc.
    print(f"  → {slug} ({label})")
    HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(
        str(pdf_path),
        stylesheets=[CSS(string=PRINT_CSS)],
    )
    size_kb = pdf_path.stat().st_size // 1024
    print(f"    Done: {pdf_path.name} ({size_kb} KB)")
    return pdf_path


def main():
    args = sys.argv[1:]
    if args:
        targets = [(s, o, l) for s, o, l in SPOKES if s in args]
        unknown = [a for a in args if not any(s == a for s, _, _ in SPOKES)]
        if unknown:
            print(f"Unknown spoke(s): {unknown}", file=sys.stderr)
            print(f"Known spokes:")
            for s, _, _ in SPOKES:
                print(f"  - {s}")
            sys.exit(1)
    else:
        targets = SPOKES

    print(f"Building {len(targets)} spoke PDF(s)…")
    print("=" * 60)
    for slug, output, label in targets:
        build(slug, output, label)
    print("=" * 60)
    print("All done.")


if __name__ == "__main__":
    main()
