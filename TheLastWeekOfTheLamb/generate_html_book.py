#!/usr/bin/env python3
"""
Generate HTML online reading version of "The Last Week of the Lamb"
for noblemind.study.

Generates:
  - index.html (Table of Contents)
  - prologue.html
  - chapter-01.html through chapter-12.html
  - interlude.html
  - epilogue.html

Usage:
  python3 generate_html_book.py
"""

import os
import re
from pathlib import Path

import markdown as md
from docx import Document

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR

BOOK_TITLE = "The Last Week of the Lamb"
BOOK_SUBTITLE = "The Passover Pattern Good Friday Missed"
AUTHOR = "Paul &amp; Pam Hainline"
PROGRESS_KEY = "theLastWeekOfTheLamb_progress"
COPYRIGHT = "&copy; 2026 Paul &amp; Pam Hainline. All rights reserved."

# --------------------------------------------------------------------------
# Section definitions
# Each section is a page in the online reader. `slug` is the URL-safe
# basename without extension. `kind` controls dot/progress behavior.
# --------------------------------------------------------------------------

SECTIONS = [
    {
        "slug": "prologue",
        "kind": "prologue",
        "label": "Prologue",
        "title": "The Promise and the Thread",
        "subtitle": "A promise buried inside a curse.",
        "file": "Prologue_The_Promise_and_the_Thread.md",
        "part": None,
    },
    # -- Part One --
    {
        "slug": "chapter-01",
        "kind": "chapter",
        "chapter_num": 1,
        "label": "Chapter One",
        "title": "The Lamb in Egypt",
        "subtitle": "The blueprint God gave on the night He delivered His people.",
        "file": "Chapter01_The_Lamb_in_Egypt.md",
        "part": ("Part One", "The Pattern"),
    },
    {
        "slug": "chapter-02",
        "kind": "chapter",
        "chapter_num": 2,
        "label": "Chapter Two",
        "title": "The Lamb in Prophecy",
        "subtitle": "Isaiah saw the Lamb centuries before He came.",
        "file": "Chapter02_The_Lamb_in_Prophecy.md",
        "part": None,
    },
    {
        "slug": "interlude",
        "kind": "interlude",
        "label": "Interlude",
        "title": "Understanding the Hebrew Calendar",
        "subtitle": "A brief guide before we enter the week.",
        "file": "Understanding_the_Hebrew_Calendar_Interlude.md",
        "part": None,
    },
    # -- Part Two --
    {
        "slug": "chapter-03",
        "kind": "chapter",
        "chapter_num": 3,
        "label": "Chapter Three",
        "title": "The Arrival and the Selection",
        "subtitle": "Nisan 9&ndash;10 &mdash; the Lamb enters the city.",
        "file": "Chapter03_The_Arrival_and_the_Selection.md",
        "part": ("Part Two", "The Week"),
    },
    {
        "slug": "chapter-04",
        "kind": "chapter",
        "chapter_num": 4,
        "label": "Chapter Four",
        "title": "Leaves Without Fruit",
        "subtitle": "The fig tree and the cleansing of the temple.",
        "file": "Chapter04_Leaves_Without_Fruit.md",
        "part": None,
    },
    {
        "slug": "chapter-05",
        "kind": "chapter",
        "chapter_num": 5,
        "label": "Chapter Five",
        "title": "The Lamb Is Examined",
        "subtitle": "Every authority in Israel finds no fault.",
        "file": "Chapter05_The_Lamb_Is_Examined.md",
        "part": None,
    },
    {
        "slug": "chapter-06",
        "kind": "chapter",
        "chapter_num": 6,
        "label": "Chapter Six",
        "title": "The Anointing and the Betrayal",
        "subtitle": "Mary pours out the ointment; Judas settles the price.",
        "file": "Chapter06_The_Anointing_and_the_Betrayal.md",
        "part": None,
    },
    {
        "slug": "chapter-07",
        "kind": "chapter",
        "chapter_num": 7,
        "label": "Chapter Seven",
        "title": "The Passover",
        "subtitle": "Nisan 14 begins &mdash; the upper room.",
        "file": "Chapter07_The_Passover.md",
        "part": None,
    },
    {
        "slug": "chapter-08",
        "kind": "chapter",
        "chapter_num": 8,
        "label": "Chapter Eight",
        "title": "The Cup and the Trials",
        "subtitle": "Gethsemane and the night of six trials.",
        "file": "Chapter08_The_Cup_and_the_Trials.md",
        "part": None,
    },
    {
        "slug": "chapter-09",
        "kind": "chapter",
        "chapter_num": 9,
        "label": "Chapter Nine",
        "title": "The Lamb Is Killed",
        "subtitle": "Nisan 14, afternoon &mdash; the blueprint fulfilled.",
        "file": "Chapter09_The_Lamb_Is_Killed.md",
        "part": None,
    },
    # -- Part Three --
    {
        "slug": "chapter-10",
        "kind": "chapter",
        "chapter_num": 10,
        "label": "Chapter Ten",
        "title": "Three Days and Three Nights",
        "subtitle": "The sign of Jonah, counted honestly.",
        "file": "Chapter10_Three_Days_and_Three_Nights.md",
        "part": ("Part Three", "The Silence"),
    },
    # -- Part Four --
    {
        "slug": "chapter-11",
        "kind": "chapter",
        "chapter_num": 11,
        "label": "Chapter Eleven",
        "title": "The Stone Moves",
        "subtitle": "The first day of the week &mdash; the tomb is empty.",
        "file": "Chapter11_The_Stone_Moves.md",
        "part": ("Part Four", "The Open Door"),
    },
    {
        "slug": "chapter-12",
        "kind": "chapter",
        "chapter_num": 12,
        "label": "Chapter Twelve",
        "title": "When Did the Lamb Die?",
        "subtitle": "The astronomy and the text converge on AD 31.",
        "file": "Chapter12_When_Did_the_Lamb_Die.md",
        "part": None,
    },
    {
        "slug": "epilogue",
        "kind": "epilogue",
        "label": "Epilogue",
        "title": "The Thread Completed",
        "subtitle": "The thread that began in a garden reaches an empty tomb.",
        "file": "Epilogue_The_Thread_Completed.md",
        "part": None,
    },
    # -- Appendix (reference charts) --
    {
        "slug": "timeline-chart",
        "kind": "appendix",
        "label": "Timeline Chart",
        "title": "From Bethany to the Empty Tomb",
        "subtitle": "The week at a glance &mdash; Nisan 9 through the first day.",
        "file": "From_Bethany_to_the_Empty_Tomb_Timeline_Chart.md",
        "part": None,
    },
    {
        "slug": "gospel-parallel",
        "kind": "appendix",
        "label": "Reference Chart",
        "title": "Gospel Parallel Reference",
        "subtitle": "Every event in the last week, across all four Gospels.",
        "file": "Gospel_Parallel_Reference_Chart.docx",
        "part": None,
    },
]

TOTAL_SECTIONS = len(SECTIONS)
TOTAL_CHAPTERS = sum(1 for s in SECTIONS if s["kind"] == "chapter")


# --------------------------------------------------------------------------
# Color scheme &mdash; drawn from the Lulu hardcover palette
# (black cover with cream text and gold accents).
# --------------------------------------------------------------------------
ACCENT = "#D4A848"            # warm gold (headings, primary links)
ACCENT_RGB = "212, 168, 72"
ACCENT_SECONDARY = "#C87941"  # warm copper (secondary accents, scripture border)
ACCENT_SECONDARY_RGB = "200, 121, 65"


# --------------------------------------------------------------------------
# Password gate — REMOVED 2026-04-17. The book is public.
# Kept as an empty placeholder so the two template f-strings below still
# resolve. Do NOT reintroduce the gate without explicit author sign-off.
# --------------------------------------------------------------------------

PASSWORD_JS = ""


# --------------------------------------------------------------------------
# Markdown processing &mdash; reuse the book's custom scripture-quote format
# --------------------------------------------------------------------------

# Matches:
#   > *"quote text ..."* — **Book Ref**
# Allows straight or curly quotes, em-dash or hyphen between quote and ref.
SCRIPTURE_QUOTE_RE = re.compile(
    r'^>\s*\*["\u201C](.+?)["\u201D]\*\s*[\u2014\-]+\s*\*\*(.+?)\*\*\s*$',
    re.MULTILINE,
)

# Matches the first heading line of a source file (the section title).
TITLE_LINE_RE = re.compile(r'^#\s+(.+?)\s*$', re.MULTILINE)


def convert_scripture_quotes(text):
    """Replace the book's scripture-quote format with HTML blockquotes.

    Injected as a raw HTML block so python-markdown leaves it alone.
    """
    def replace(m):
        quote = m.group(1).strip()
        ref = m.group(2).strip()
        return (
            f'<blockquote class="scripture">'
            f'<p><em>&ldquo;{quote}&rdquo;</em></p>'
            f'<cite>&mdash; {ref}</cite>'
            f'</blockquote>'
        )
    return SCRIPTURE_QUOTE_RE.sub(replace, text)


def process_markdown(md_text):
    """Convert the book's markdown flavor to HTML body."""
    # Strip the first # heading (title) — handled separately in the template
    md_text = TITLE_LINE_RE.sub("", md_text, count=1).lstrip("\n")

    # Also strip a leading ## subtitle line if present (interlude has one)
    md_text = re.sub(r'^##\s+.+\n', '', md_text, count=1)

    md_text = convert_scripture_quotes(md_text)
    html = md.markdown(md_text, extensions=["extra", "smarty", "tables"])
    return html


# --------------------------------------------------------------------------
# Appendix chart builders
# --------------------------------------------------------------------------

def build_timeline_chart_html():
    """Render the Bethany-to-empty-tomb timeline chart markdown.

    Unlike the prose chapters we keep the intro lines (the revision date
    and the italic reminder about Hebrew days) so the chart reads cleanly
    as a standalone reference.
    """
    md_path = SCRIPT_DIR / "From_Bethany_to_the_Empty_Tomb_Timeline_Chart.md"
    md_text = md_path.read_text(encoding="utf-8")

    # Strip the first `#` (book title) and the first `##` (chart subtitle)
    # — both are surfaced in the page header, so we don't want duplicates.
    md_text = TITLE_LINE_RE.sub("", md_text, count=1).lstrip("\n")
    md_text = re.sub(r'^##\s+.+\n', '', md_text, count=1)

    html = md.markdown(md_text, extensions=["extra", "smarty", "tables"])
    # Wrap the table(s) in a scroll container so the 5-column layout can
    # survive narrow viewports.
    return f'<div class="chart-content timeline-chart">{html}</div>'


def build_gospel_parallel_html():
    """Parse Gospel_Parallel_Reference_Chart.docx into an HTML table.

    Ported from generate_lulu_interior.py — same row typing (header,
    Nisan-day banner, sub-section banner, event row) and zebra striping.
    We drop WeasyPrint's page-break machinery since it's meaningless on
    the web, and emit a single <tbody>.
    """
    doc = Document(str(SCRIPT_DIR / "Gospel_Parallel_Reference_Chart.docx"))
    table = doc.tables[0]

    header_html = ""
    body_rows = []
    event_counter = 0

    for ri, row in enumerate(table.rows):
        cells = [c.text.strip().replace("\n", " ") for c in row.cells]

        if ri == 0:
            header_html = (
                '<tr class="gp-header">'
                + "".join(f"<th>{c}</th>" for c in cells)
                + "</tr>"
            )
            continue

        is_banner = all(c == cells[0] for c in cells) and bool(cells[0])
        if is_banner:
            text = cells[0]
            is_primary = text.startswith("Nisan") or text.startswith("First Day")
            row_class = "gp-day" if is_primary else "gp-subsection"
            body_rows.append(
                f'<tr class="{row_class}"><td colspan="5">{text}</td></tr>'
            )
            continue

        event_cell, *refs = cells
        ref_html = "".join(f'<td class="gp-ref">{r}</td>' for r in refs)
        zebra = " gp-event-alt" if event_counter % 2 == 1 else ""
        event_counter += 1
        body_rows.append(
            f'<tr class="gp-event{zebra}">'
            f'<td class="gp-event-name">{event_cell}</td>'
            f'{ref_html}'
            f'</tr>'
        )

    table_html = (
        '<table class="gospel-parallel">'
        '<colgroup>'
        '<col class="gp-col-event">'
        '<col class="gp-col-ref">'
        '<col class="gp-col-ref">'
        '<col class="gp-col-ref">'
        '<col class="gp-col-ref">'
        '</colgroup>'
        f'<thead>{header_html}</thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        '</table>'
    )
    intro = (
        '<p class="chart-intro">Where each event in the last week is recorded '
        'across the four Gospels. All references NASB.</p>'
    )
    return f'<div class="chart-content gospel-parallel-wrap">{intro}{table_html}</div>'


# --------------------------------------------------------------------------
# CSS for chapter / section pages
# --------------------------------------------------------------------------

def get_chapter_css():
    return f"""    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #cdbfa5;
      --text-muted: #8a7d66;
      --accent: {ACCENT};
      --accent-glow: rgba({ACCENT_RGB}, 0.4);
      --accent-soft: rgba({ACCENT_RGB}, 0.12);
      --accent-secondary: {ACCENT_SECONDARY};
      --accent-secondary-glow: rgba({ACCENT_SECONDARY_RGB}, 0.3);
      --scripture-border: {ACCENT_SECONDARY};
      --glass-blur: blur(12px);
      --radius-card: 22px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Georgia, serif;
      background: var(--bg-dark);
      color: var(--text-primary);
      font-size: 1.1rem;
      line-height: 1.85;
      min-height: 100vh;
      padding: 30px 20px;
    }}
    body::before {{
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: 0;
      background:
        radial-gradient(circle at top, rgba({ACCENT_RGB},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_RGB},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15),
        0 0 80px rgba({ACCENT_RGB},0.2);
      max-width: 860px;
      width: 100%;
      margin: 0 auto;
    }}
    .glass-page-inner {{
      background: var(--bg-inner);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card);
      padding: 3rem 2.5rem;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }}
    .glass-page-inner::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 150px;
      background: radial-gradient(ellipse at top, rgba({ACCENT_RGB},0.04), transparent 70%);
      pointer-events: none;
    }}
    .glass-tab {{
      position: absolute;
      bottom: -12px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      border-radius: 999px;
      background: radial-gradient(circle at top, rgba({ACCENT_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_RGB},0.4);
    }}
    .nav-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
      padding: 14px 18px;
      background: rgba({ACCENT_RGB},0.04);
      border-radius: 12px;
      border: 1px solid rgba({ACCENT_RGB},0.12);
      position: relative;
      z-index: 1;
    }}
    .nav-controls a, .nav-controls select {{
      color: var(--text-primary);
      text-decoration: none;
      padding: 8px 14px;
      border-radius: 8px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba({ACCENT_RGB},0.25);
      font-size: 0.85rem;
      transition: all 0.3s;
    }}
    .nav-controls a:hover, .nav-controls select:hover {{
      border-color: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }}
    .nav-controls select {{
      cursor: pointer;
      min-width: 200px;
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23D4A848' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      padding-right: 30px;
    }}
    .nav-controls select option {{
      background: var(--bg-dark);
      color: var(--text-primary);
    }}
    .home-link {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--accent-secondary);
      font-size: 0.85rem;
    }}
    .home-link svg {{ width: 14px; height: 14px; fill: currentColor; }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba({ACCENT_RGB},0.2);
      position: relative;
      z-index: 1;
    }}
    h1 {{
      font-size: 2.2rem;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      margin-bottom: 6px;
      font-weight: 600;
    }}
    .chapter-num {{
      font-size: 1rem;
      color: var(--text-secondary);
      margin-bottom: 6px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    .subtitle {{
      font-size: 1.05rem;
      color: var(--text-secondary);
      font-style: italic;
      margin-bottom: 4px;
    }}
    .content {{ position: relative; z-index: 1; }}
    .content p {{
      margin-bottom: 16px;
      color: var(--text-secondary);
      text-align: justify;
    }}
    .content h2 {{
      font-size: 1.4rem;
      color: var(--accent);
      text-shadow: 0 0 12px var(--accent-glow);
      margin: 30px 0 14px;
      padding-bottom: 6px;
      border-bottom: 1px solid rgba({ACCENT_RGB},0.2);
      font-weight: 600;
    }}
    .content h3 {{
      font-size: 1.15rem;
      color: var(--accent-secondary);
      margin: 22px 0 10px;
      font-weight: 600;
    }}
    .content h4 {{
      font-size: 1.0rem;
      color: var(--text-primary);
      margin: 18px 0 8px;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .content ul, .content ol {{
      color: var(--text-secondary);
      margin: 0 0 16px 1.6rem;
    }}
    .content li {{ margin-bottom: 6px; }}
    .content strong {{ color: var(--text-primary); }}
    .content em {{ color: var(--text-primary); }}
    blockquote.scripture {{
      margin: 20px 0;
      padding: 16px 20px;
      background: rgba({ACCENT_SECONDARY_RGB},0.05);
      border-left: 3px solid var(--scripture-border);
      border-radius: 0 10px 10px 0;
    }}
    blockquote.scripture p {{ margin-bottom: 0; color: var(--text-primary); }}
    blockquote.scripture cite {{
      display: block;
      margin-top: 6px;
      color: var(--accent);
      font-style: normal;
      font-weight: 500;
      font-size: 0.9rem;
    }}
    .content hr {{
      border: none;
      text-align: center;
      margin: 28px 0;
      color: var(--text-muted);
      opacity: 0.5;
      height: 1em;
    }}
    .content hr::after {{
      content: "\\2022  \\2022  \\2022";
      letter-spacing: 0.6em;
    }}
    /* === Chart / appendix tables === */
    .chart-content {{
      margin: 10px 0 30px;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}
    .chart-intro {{
      color: var(--text-muted);
      font-size: 0.9rem;
      font-style: italic;
      text-align: center;
      margin-bottom: 14px;
    }}
    .chart-content table {{
      width: 100%;
      min-width: 700px;
      border-collapse: collapse;
      font-size: 0.82rem;
      line-height: 1.5;
      color: var(--text-primary);
    }}
    .chart-content th,
    .chart-content td {{
      padding: 8px 10px;
      vertical-align: top;
      border: 1px solid rgba(148,163,184,0.15);
      text-align: left;
    }}
    .chart-content thead th {{
      background: rgba({ACCENT_RGB},0.18);
      color: var(--accent);
      font-weight: 600;
      font-size: 0.85rem;
      border-bottom: 1px solid rgba({ACCENT_RGB},0.45);
    }}
    .chart-content tbody tr:nth-child(even) td {{
      background: rgba(255,255,255,0.02);
    }}
    .chart-content strong {{ color: var(--text-primary); }}
    .chart-content em {{ color: var(--text-secondary); }}
    .chart-content p {{
      color: var(--text-secondary);
      margin-bottom: 12px;
    }}
    /* Timeline chart leading text (revision date, italic reminder) */
    .timeline-chart > p:first-of-type {{
      font-size: 0.82rem;
      color: var(--text-muted);
      text-align: center;
    }}
    /* === Gospel Parallel Reference Chart === */
    table.gospel-parallel {{
      min-width: 820px;
      table-layout: fixed;
      font-size: 0.8rem;
    }}
    table.gospel-parallel .gp-col-event {{ width: 38%; }}
    table.gospel-parallel .gp-col-ref   {{ width: 15.5%; }}
    table.gospel-parallel tr.gp-header th {{
      background: rgba({ACCENT_RGB},0.22);
      color: var(--accent);
      font-weight: 600;
      text-align: left;
    }}
    table.gospel-parallel tr.gp-day td {{
      background: rgba({ACCENT_SECONDARY_RGB},0.32);
      color: var(--text-primary);
      font-weight: 600;
      font-size: 0.88rem;
      letter-spacing: 0.02em;
    }}
    table.gospel-parallel tr.gp-subsection td {{
      background: rgba({ACCENT_SECONDARY_RGB},0.14);
      color: var(--accent-secondary);
      font-style: italic;
      font-weight: 600;
      font-size: 0.82rem;
    }}
    table.gospel-parallel tr.gp-event td {{
      background: transparent;
    }}
    table.gospel-parallel tr.gp-event.gp-event-alt td {{
      background: rgba(255,255,255,0.025);
    }}
    table.gospel-parallel td.gp-event-name {{
      color: var(--text-primary);
      font-weight: 600;
    }}
    table.gospel-parallel td.gp-ref {{
      font-size: 0.76rem;
      color: var(--text-secondary);
    }}
    .mark-complete {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin: 30px 0 10px;
      padding: 12px;
      background: rgba({ACCENT_RGB},0.06);
      border: 1px solid rgba({ACCENT_RGB},0.2);
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.3s;
      user-select: none;
    }}
    .mark-complete:hover {{
      border-color: var(--accent);
      background: rgba({ACCENT_RGB},0.1);
    }}
    .mark-complete.completed {{
      background: rgba({ACCENT_RGB},0.12);
      border-color: var(--accent);
    }}
    .mark-complete .check {{
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: 2px solid var(--accent);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      color: transparent;
      transition: all 0.3s;
    }}
    .mark-complete.completed .check {{
      background: var(--accent);
      color: #0d0d0d;
    }}
    .mark-complete span:last-child {{
      color: var(--accent);
      font-weight: 600;
      font-size: 0.9rem;
    }}
    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba({ACCENT_RGB},0.15);
      text-align: center;
      position: relative;
      z-index: 1;
    }}
    .footer-nav {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 20px;
    }}
    .footer-nav a {{
      color: var(--accent-secondary);
      text-decoration: none;
      padding: 10px 20px;
      border-radius: 8px;
      background: rgba({ACCENT_SECONDARY_RGB},0.08);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB},0.25);
      transition: all 0.3s;
      font-size: 0.9rem;
      flex: 0 1 auto;
    }}
    .footer-nav a:hover {{
      background: rgba({ACCENT_SECONDARY_RGB},0.15);
      box-shadow: 0 0 10px var(--accent-secondary-glow);
    }}
    .footer-nav a.disabled {{
      opacity: 0.35;
      pointer-events: none;
    }}
    .copyright {{
      color: var(--text-muted);
      font-size: 0.78rem;
      margin-top: 12px;
    }}
    .copyright a {{ color: var(--accent-secondary); text-decoration: none; }}
    @media print {{
      body {{ background: white; color: #333; padding: 0; font-size: 11pt; line-height: 1.5; }}
      body::before {{ display: none; }}
      .glass-page-wrapper {{ box-shadow: none; background: none; padding: 0; max-width: 100%; }}
      .glass-page-inner {{ background: white; padding: 0.5in; border-radius: 0; border: none; }}
      .glass-page-inner::before {{ display: none; }}
      .glass-tab, .nav-controls, .footer-nav, .mark-complete {{ display: none; }}
      header {{ border-bottom: 2px solid #333; }}
      h1 {{ color: #8a6d20; text-shadow: none; font-size: 18pt; }}
      .content p {{ color: #333; }}
      .content h2 {{ color: #8a6d20; border-bottom-color: #ccc; text-shadow: none; }}
      .content h3 {{ color: #8a4f20; }}
      blockquote.scripture {{ background: #f9f5eb; border-left-color: #C87941; }}
      .copyright {{ color: #999; }}
      a {{ color: #333; text-decoration: none; }}
    }}
    @media (max-width: 900px) {{
      body {{ padding: 20px 12px; }}
      .glass-page-inner {{ padding: 2rem 1.8rem; }}
      h1 {{ font-size: 1.8rem; }}
    }}
    @media (max-width: 600px) {{
      html {{ -webkit-text-size-adjust: 100%; }}
      body {{ padding: 10px 6px; font-size: 1rem; line-height: 1.75; }}
      .glass-page-wrapper {{ border-radius: 16px; padding: 2px; }}
      .glass-page-inner {{ padding: 1.2rem 1rem; border-radius: 14px; }}
      .glass-page-inner::before {{ height: 80px; }}
      .glass-tab {{ width: 60px; height: 10px; bottom: -8px; }}
      .nav-controls {{ flex-direction: column; padding: 10px 12px; gap: 8px; }}
      .nav-controls a, .nav-controls select {{ padding: 10px 14px; font-size: 0.9rem; min-height: 44px; }}
      .nav-controls select {{ width: 100%; }}
      header {{ margin-bottom: 20px; padding-bottom: 16px; }}
      h1 {{ font-size: 1.4rem; }}
      .chapter-num {{ font-size: 0.9rem; }}
      .content p {{ text-align: left; margin-bottom: 14px; }}
      .content h2 {{ font-size: 1.2rem; margin: 24px 0 12px; }}
      .content h3 {{ font-size: 1.05rem; margin: 18px 0 8px; }}
      blockquote.scripture {{ padding: 12px 14px; margin: 16px 0; }}
      .mark-complete {{ min-height: 44px; padding: 12px; }}
      footer {{ margin-top: 28px; }}
      .footer-nav {{ flex-direction: column; gap: 10px; }}
      .footer-nav a {{ text-align: center; padding: 12px 20px; min-height: 44px; display: flex; align-items: center; justify-content: center; }}
    }}"""


# --------------------------------------------------------------------------
# Dropdown / nav helpers
# --------------------------------------------------------------------------

def build_section_select(current_slug):
    options = ['          <option value="">Jump to&hellip;</option>']
    appendix_banner_shown = False
    for s in SECTIONS:
        # Insert a disabled label option for part breaks
        if s.get("part"):
            part_name, part_subtitle = s["part"]
            options.append(
                f'          <option disabled>&mdash; {part_name}: {part_subtitle} &mdash;</option>'
            )
        # Insert a disabled label option before the first appendix
        if s["kind"] == "appendix" and not appendix_banner_shown:
            options.append('          <option disabled>&mdash; Appendix &mdash;</option>')
            appendix_banner_shown = True
        selected = ' selected' if s["slug"] == current_slug else ''
        # Compose dropdown label
        if s["kind"] == "chapter":
            label = f'Ch {s["chapter_num"]}: {s["title"]}'
        else:
            label = f'{s["label"]}: {s["title"]}'
        options.append(
            f'          <option value="{s["slug"]}.html"{selected}>{label}</option>'
        )
    return '\n'.join(options)


def progress_dot_id(section):
    return f'dot-{section["slug"]}'


# --------------------------------------------------------------------------
# Per-section page generation
# --------------------------------------------------------------------------

def generate_section_html(section, content_html, index_in_sections):
    num = index_in_sections  # 0-based
    title = section["title"]
    subtitle = section.get("subtitle", "")
    label = section["label"]

    # Prev/next navigation — link across every section, not just chapters
    if num == 0:
        prev_link = '<a href="index.html">&larr; Table of Contents</a>'
        left_target = 'index.html'
    else:
        prev_sec = SECTIONS[num - 1]
        prev_link = (
            f'<a href="{prev_sec["slug"]}.html">&larr; '
            f'{prev_sec["label"]}: {prev_sec["title"]}</a>'
        )
        left_target = f'{prev_sec["slug"]}.html'

    if num == TOTAL_SECTIONS - 1:
        next_link = '<a href="index.html">Table of Contents &rarr;</a>'
    else:
        next_sec = SECTIONS[num + 1]
        next_link = (
            f'<a href="{next_sec["slug"]}.html">'
            f'{next_sec["label"]}: {next_sec["title"]} &rarr;</a>'
        )

    subtitle_html = ''
    if subtitle:
        subtitle_html = f'\n        <p class="subtitle">{subtitle}</p>'

    page_title = f'{label}: {title} | {BOOK_TITLE}'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <style>
{get_chapter_css()}
  </style>
</head>
<body>
  {PASSWORD_JS}
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          {BOOK_TITLE}
        </a>
        <select id="section-select" onchange="goToSection(this.value)">
{build_section_select(section["slug"])}
        </select>
      </nav>

      <header>
        <p class="chapter-num">{label.upper()}</p>
        <h1>{title}</h1>{subtitle_html}
      </header>

      <div class="content">
{content_html}
      </div>

      <div id="mark-complete" class="mark-complete" onclick="toggleComplete()">
        <span class="check"></span>
        <span>Mark Section Complete</span>
      </div>

      <footer>
        <div class="footer-nav">
          {prev_link}
          {next_link}
        </div>
        <p class="copyright">{BOOK_TITLE} {COPYRIGHT}<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var PROGRESS_KEY = '{PROGRESS_KEY}';
    var SECTION_SLUG = '{section["slug"]}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}

    function markVisited() {{
      var p = loadProgress();
      if (!p[SECTION_SLUG]) p[SECTION_SLUG] = 'visited';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
    }}

    function toggleComplete() {{
      var p = loadProgress();
      p[SECTION_SLUG] = p[SECTION_SLUG] === 'complete' ? 'visited' : 'complete';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
      updateCompleteBtn();
    }}

    function updateCompleteBtn() {{
      var p = loadProgress();
      var btn = document.getElementById('mark-complete');
      if (!btn) return;
      var done = p[SECTION_SLUG] === 'complete';
      btn.className = 'mark-complete' + (done ? ' completed' : '');
      btn.querySelector('.check').textContent = done ? '\\u2713' : '';
      btn.querySelector('span:last-child').textContent = done ? 'Section Complete' : 'Mark Section Complete';
    }}

    function goToSection(val) {{
      if (val) window.location.href = val;
    }}

    document.addEventListener('keydown', function(e) {{
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
      if (e.key === 'ArrowLeft') {{
        window.location.href = '{left_target}';
      }} else if (e.key === 'ArrowRight') {{
        var next = document.querySelector('.footer-nav a:last-child');
        if (next && !next.classList.contains('disabled')) next.click();
      }}
    }});

    document.addEventListener('DOMContentLoaded', function() {{
      markVisited();
      updateCompleteBtn();
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Index / Table of Contents
# --------------------------------------------------------------------------

def build_toc_cards():
    """Build the per-section cards, grouped so that Prologue, Interlude, and
    Epilogue each stand alone, and chapters are grouped under their Part
    banner until the next Part (or a non-chapter break)."""
    groups = []  # list of (heading, [sections])
    current_heading = None
    current_list = []

    def flush():
        nonlocal current_list, current_heading
        if current_list:
            groups.append((current_heading, list(current_list)))
            current_list = []
            current_heading = None

    for s in SECTIONS:
        if s["kind"] in ("prologue", "interlude", "epilogue"):
            flush()
            # Each of these stands alone in its own group
            groups.append((s["label"], [s]))
            continue

        if s["kind"] == "appendix":
            # Gather all appendices under a shared "Appendix" heading
            if current_heading != "Appendix":
                flush()
                current_heading = "Appendix"
            current_list.append(s)
            continue

        if s.get("part"):
            flush()
            part_name, part_subtitle = s["part"]
            current_heading = f"{part_name} &mdash; {part_subtitle}"

        current_list.append(s)
    flush()

    html_parts = []
    for heading, secs in groups:
        html_parts.append('      <section class="chapter-section">')
        html_parts.append('        <div class="section-header">')
        html_parts.append(f'          <h2>{heading}</h2>')
        html_parts.append('        </div>')
        html_parts.append('        <div class="lesson-grid">')
        for s in secs:
            if s["kind"] == "chapter":
                num_label = f'Chapter {s["chapter_num"]}'
            else:
                num_label = s["label"]
            subtitle = s.get("subtitle", "")
            subtitle_html = (
                f'\n            <span class="lesson-subtitle">{subtitle}</span>'
                if subtitle else ''
            )
            html_parts.append(
                f'          <a href="{s["slug"]}.html" class="lesson-card" data-slug="{s["slug"]}">\n'
                f'            <span class="lesson-num">{num_label}</span>\n'
                f'            <div class="lesson-title">{s["title"]}</div>'
                f'{subtitle_html}\n'
                f'            <span class="progress-dot" id="dot-{s["slug"]}"></span>\n'
                f'          </a>'
            )
        html_parts.append('        </div>')
        html_parts.append('      </section>')
    return '\n'.join(html_parts)


def build_slugs_js_array():
    return '[' + ', '.join(f"'{s['slug']}'" for s in SECTIONS) + ']'


def generate_index_html():
    toc_html = build_toc_cards()
    slugs_js = build_slugs_js_array()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents | {BOOK_TITLE}</title>
  <style>
    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #cdbfa5;
      --text-muted: #8a7d66;
      --accent: {ACCENT};
      --accent-glow: rgba({ACCENT_RGB}, 0.4);
      --accent-soft: rgba({ACCENT_RGB}, 0.12);
      --accent-secondary: {ACCENT_SECONDARY};
      --accent-secondary-glow: rgba({ACCENT_SECONDARY_RGB}, 0.3);
      --glass-blur: blur(12px);
      --radius-card: 22px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Georgia, serif;
      background: var(--bg-dark);
      color: var(--text-primary);
      font-size: 1.1rem;
      line-height: 1.85;
      min-height: 100vh;
      padding: 30px 20px;
    }}
    body::before {{
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: 0;
      background:
        radial-gradient(circle at top, rgba({ACCENT_RGB},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_RGB},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15),
        0 0 80px rgba({ACCENT_RGB},0.2);
      max-width: 860px;
      width: 100%;
      margin: 0 auto;
    }}
    .glass-page-inner {{
      background: var(--bg-inner);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card);
      padding: 3rem 2.5rem;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }}
    .glass-page-inner::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 150px;
      background: radial-gradient(ellipse at top, rgba({ACCENT_RGB},0.04), transparent 70%);
      pointer-events: none;
    }}
    .glass-tab {{
      position: absolute;
      bottom: -12px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      border-radius: 999px;
      background: radial-gradient(circle at top, rgba({ACCENT_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_RGB},0.4);
    }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba({ACCENT_RGB},0.2);
      position: relative;
      z-index: 1;
    }}
    h1 {{
      font-size: 2.2rem;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      margin-bottom: 6px;
      font-weight: 600;
    }}
    .book-subtitle {{
      font-size: 1.1rem;
      color: var(--text-secondary);
      font-style: italic;
      margin-bottom: 10px;
    }}
    .author {{
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-bottom: 4px;
    }}
    .stats {{
      margin-top: 12px;
      color: var(--text-secondary);
      font-size: 0.9rem;
    }}
    .stats span {{
      color: var(--accent);
      font-weight: 600;
    }}
    .return-link {{
      display: inline-block;
      margin-top: 18px;
      padding: 10px 20px;
      background: rgba({ACCENT_SECONDARY_RGB},0.08);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB},0.25);
      border-radius: 8px;
      color: var(--accent-secondary);
      text-decoration: none;
      font-size: 0.9rem;
      transition: all 0.3s ease;
    }}
    .return-link:hover {{
      background: rgba({ACCENT_SECONDARY_RGB},0.15);
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
    }}
    .download-btn {{
      display: inline-block;
      margin-top: 10px;
      margin-left: 10px;
      padding: 10px 20px;
      background: rgba(100,100,100,0.1);
      border: 1px solid rgba(100,100,100,0.3);
      border-radius: 8px;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.9rem;
      cursor: not-allowed;
      opacity: 0.5;
    }}
    .progress-bar {{
      margin: 20px 0;
      padding: 14px 18px;
      background: rgba({ACCENT_RGB},0.04);
      border: 1px solid rgba({ACCENT_RGB},0.12);
      border-radius: 12px;
      position: relative;
      z-index: 1;
    }}
    .progress-bar .label {{
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }}
    .progress-bar .label span {{ color: var(--accent); font-weight: 600; }}
    .progress-track {{
      height: 8px;
      background: rgba(0,0,0,0.3);
      border-radius: 4px;
      overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
      border-radius: 4px;
      transition: width 0.5s ease;
    }}
    .front-matter {{
      margin-bottom: 28px;
      position: relative;
      z-index: 1;
    }}
    .front-matter .section-header h2 {{
      font-size: 1.3rem;
      color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
      margin-bottom: 14px;
    }}
    .fm-card {{
      display: block;
      padding: 14px 18px;
      margin-bottom: 10px;
      background: rgba(0,0,0,0.2);
      border-radius: 10px;
      border: 1px solid rgba({ACCENT_SECONDARY_RGB}, 0.15);
      text-decoration: none;
      color: var(--text-primary);
      transition: all 0.3s;
      cursor: pointer;
    }}
    .fm-card:hover {{
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
      transform: translateY(-2px);
    }}
    .fm-card-title {{
      color: var(--accent-secondary);
      font-weight: 600;
      font-size: 0.95rem;
    }}
    .fm-card-preview {{
      color: var(--text-muted);
      font-size: 0.8rem;
      font-style: italic;
      margin-top: 4px;
    }}
    .fm-content {{
      display: none;
      padding: 18px 20px;
      margin-top: -1px;
      margin-bottom: 10px;
      background: rgba(0,0,0,0.15);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB}, 0.1);
      border-radius: 0 0 10px 10px;
      color: var(--text-secondary);
      font-size: 0.92rem;
      line-height: 1.7;
    }}
    .fm-content.open {{ display: block; }}
    .fm-card.open {{
      border-radius: 10px 10px 0 0;
      border-bottom-color: transparent;
    }}
    .fm-content p {{ margin-bottom: 10px; }}
    .fm-content em {{ color: var(--text-primary); }}
    .fm-content strong {{ color: var(--text-primary); }}
    .fm-content h3 {{
      color: var(--text-primary);
      font-size: 1rem;
      margin: 14px 0 6px;
    }}
    .fm-content h3:first-child {{ margin-top: 0; }}
    .chapter-section {{
      margin-bottom: 32px;
      position: relative;
      z-index: 1;
    }}
    .section-header h2 {{
      font-size: 1.3rem;
      color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
      margin-bottom: 14px;
      font-weight: 600;
    }}
    .lesson-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
    }}
    .lesson-card {{
      display: block;
      position: relative;
      padding: 14px 18px;
      background: rgba(0,0,0,0.2);
      border-radius: 10px;
      border: 1px solid rgba({ACCENT_RGB},0.12);
      text-decoration: none;
      transition: all 0.3s;
    }}
    .lesson-card:hover {{
      border-color: var(--accent);
      box-shadow: 0 0 15px var(--accent-glow);
      transform: translateY(-2px);
    }}
    .lesson-num {{
      color: var(--accent);
      font-weight: 700;
      font-size: 0.85rem;
    }}
    .lesson-title {{
      color: var(--text-primary);
      font-size: 0.95rem;
      margin: 4px 0;
    }}
    .lesson-subtitle {{
      color: var(--text-muted);
      font-size: 0.8rem;
      font-style: italic;
    }}
    .progress-dot {{
      position: absolute;
      top: 12px;
      right: 14px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 2px solid rgba({ACCENT_RGB},0.3);
      transition: all 0.3s;
    }}
    .progress-dot.visited {{
      border-color: var(--accent);
      background: rgba({ACCENT_RGB},0.3);
    }}
    .progress-dot.complete {{
      border-color: var(--accent);
      background: var(--accent);
    }}
    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba({ACCENT_RGB},0.15);
      text-align: center;
      position: relative;
      z-index: 1;
    }}
    .copyright {{
      color: var(--text-muted);
      font-size: 0.78rem;
      margin-top: 12px;
    }}
    .copyright a {{ color: var(--accent-secondary); text-decoration: none; }}
    @media (max-width: 600px) {{
      html {{ -webkit-text-size-adjust: 100%; }}
      body {{ padding: 10px 6px; font-size: 1rem; line-height: 1.75; }}
      .glass-page-wrapper {{ border-radius: 16px; padding: 2px; }}
      .glass-page-inner {{ padding: 1.2rem 1rem; border-radius: 14px; }}
      .glass-page-inner::before {{ height: 80px; }}
      .glass-tab {{ width: 60px; height: 10px; bottom: -8px; }}
      header {{ margin-bottom: 20px; padding-bottom: 16px; }}
      h1 {{ font-size: 1.4rem; }}
      .return-link {{ padding: 10px 16px; min-height: 44px; display: inline-flex; align-items: center; }}
      .download-btn {{ padding: 10px 16px; min-height: 44px; display: inline-flex; align-items: center; margin-left: 0; }}
      .progress-bar {{ padding: 12px 14px; }}
      .section-header h2 {{ font-size: 1.15rem; }}
      .lesson-grid {{ grid-template-columns: 1fr; gap: 10px; }}
      .lesson-card {{ padding: 14px 16px; min-height: 44px; }}
    }}
    .hero-cover {{
      text-align: center;
      margin: 28px 0 8px;
      position: relative;
      z-index: 1;
    }}
    .hero-cover img {{
      max-width: 280px;
      width: 100%;
      height: auto;
      border-radius: 6px;
      box-shadow:
        0 8px 32px rgba(0,0,0,0.5),
        0 0 60px rgba({ACCENT_RGB}, 0.30);
      border: 1px solid rgba({ACCENT_RGB}, 0.30);
    }}
  </style>
</head>
<body>
  {PASSWORD_JS}
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <header>
        <h1>{BOOK_TITLE}</h1>
        <p class="book-subtitle">{BOOK_SUBTITLE}</p>
        <p class="author">{AUTHOR}</p>
        <p class="stats">
          <span>{TOTAL_CHAPTERS}</span> Chapters
          &nbsp;&middot;&nbsp;
          <span>Prologue</span>
          &nbsp;&middot;&nbsp;
          <span>Interlude</span>
          &nbsp;&middot;&nbsp;
          <span>Epilogue</span>
          &nbsp;&middot;&nbsp;
          <span>Appendix</span>
        </p>
        <a href="../books.html" class="return-link">&larr; Return to Books</a>
        <span class="download-btn">PDF download coming soon</span>
      </header>

      <div class="hero-cover">
        <img src="The_Last_Week_of_the_Lamb_Front_Cover_Mockup.png" alt="The Last Week of the Lamb — book cover" loading="eager">
      </div>

      <div class="progress-bar">
        <div class="label">
          <span>Reading Progress</span>
          <span id="progress-text">0 / {TOTAL_SECTIONS} sections</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
      </div>

      <section class="front-matter">
        <div class="section-header">
          <h2>Front Matter</h2>
        </div>

        <div class="fm-card" onclick="toggleFM('about')">
          <span class="fm-card-title">About This Book</span>
          <div class="fm-card-preview">The tradition is old. But the text is older.</div>
        </div>
        <div class="fm-content" id="about">
          <p><strong>What if the tradition is wrong?</strong></p>
          <p>For seventeen centuries, the church has placed the crucifixion on a Friday. But Friday gives you two nights in the tomb &mdash; not three. It leaves you with a spice-buying sequence that contradicts itself. And it breaks the one sign Jesus Himself gave to prove who He was.</p>
          <p>This book doesn&rsquo;t start with tradition. It starts with the text.</p>
          <p>Following the time markers that Matthew, Mark, Luke, and John actually wrote &mdash; &ldquo;the next day,&rdquo; &ldquo;after two days,&rdquo; &ldquo;six days before the Passover&rdquo; &mdash; a different week emerges. A week where two independent Gospel chronologies converge on the same day. A week where every authority in Israel examines Jesus and finds no fault. A week where the Lamb of God dies on the exact day, at the exact hour, that God commanded the Passover lamb to be killed fifteen centuries earlier.</p>
          <p><em>The Last Week of the Lamb</em> is not a commentary. It is not a denominational position. It is a guided walk through the text itself &mdash; every conclusion shown, every assumption identified, every inference labeled honestly. No verse is asked to carry more weight than it can bear.</p>
          <p>You will not be asked to take anyone&rsquo;s word for it. You will be asked to open your Bible.</p>
          <p><em>The tradition is old. But the text is older.</em></p>
        </div>

        <div class="fm-card" onclick="toggleFM('how-to-read')">
          <span class="fm-card-title">How to Read This Book</span>
          <div class="fm-card-preview">A walk through the week, one section at a time.</div>
        </div>
        <div class="fm-content" id="how-to-read">
          <p>The book unfolds in four parts. <strong>Part One</strong> opens the blueprint God gave in Egypt and traces it through prophecy. An <strong>Interlude</strong> teaches the two rules of the Hebrew calendar you will need before you step into the week itself.</p>
          <p><strong>Part Two</strong> walks day by day through the final week &mdash; the entry into Jerusalem, the examinations, the anointing, the Passover meal, the trials, and the crucifixion. <strong>Part Three</strong> counts the three days and three nights. <strong>Part Four</strong> walks out of the tomb.</p>
          <p>You can read straight through, or jump to any section using the dropdown on each page. Your place will be remembered as you visit each section, and you can mark each one complete when you finish.</p>
        </div>

        <div class="fm-card" onclick="toggleFM('scripture-note')">
          <span class="fm-card-title">A Note on Scripture</span>
          <div class="fm-card-preview">Translation, methodology, and honesty with the text.</div>
        </div>
        <div class="fm-content" id="scripture-note">
          <p>Scripture quotations are taken from the New American Standard Bible&reg; (NASB), Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation. Used by permission. All rights reserved. (www.lockman.org)</p>
          <p>The methodology throughout is simple: Scripture interprets Scripture. Every conclusion is shown from the text. Every assumption is identified. Every inference is labeled. Where the text is silent, this book is silent.</p>
        </div>
      </section>

{toc_html}

      <footer>
        <p class="copyright">{BOOK_TITLE} {COPYRIGHT}<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var SECTION_SLUGS = {slugs_js};
    var TOTAL_SECTIONS = {TOTAL_SECTIONS};
    var PROGRESS_KEY = '{PROGRESS_KEY}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}

    function updateProgressUI() {{
      var p = loadProgress();
      var complete = 0;
      for (var i = 0; i < SECTION_SLUGS.length; i++) {{
        var slug = SECTION_SLUGS[i];
        var dot = document.getElementById('dot-' + slug);
        if (!dot) continue;
        var status = p[slug];
        if (status === 'complete') {{
          dot.className = 'progress-dot complete';
          complete++;
        }} else if (status === 'visited') {{
          dot.className = 'progress-dot visited';
        }}
      }}
      document.getElementById('progress-text').textContent = complete + ' / ' + TOTAL_SECTIONS + ' sections';
      document.getElementById('progress-fill').style.width = (complete / TOTAL_SECTIONS * 100) + '%';
    }}

    function toggleFM(id) {{
      var content = document.getElementById(id);
      var card = content.previousElementSibling;
      var isOpen = content.classList.contains('open');
      document.querySelectorAll('.fm-content').forEach(function(el) {{ el.classList.remove('open'); }});
      document.querySelectorAll('.fm-card').forEach(function(el) {{ el.classList.remove('open'); }});
      if (!isOpen) {{
        content.classList.add('open');
        card.classList.add('open');
      }}
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      updateProgressUI();
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    print(f"Generating HTML book: {BOOK_TITLE}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # index.html
    index_path = OUTPUT_DIR / 'index.html'
    index_path.write_text(generate_index_html(), encoding='utf-8')
    print("  Generated: index.html")

    # Section pages
    for i, section in enumerate(SECTIONS):
        src_path = SCRIPT_DIR / section["file"]
        if not src_path.exists():
            print(f"  WARNING: {section['file']} not found, skipping {section['slug']}")
            continue

        if section["slug"] == "timeline-chart":
            content_html = build_timeline_chart_html()
        elif section["slug"] == "gospel-parallel":
            content_html = build_gospel_parallel_html()
        else:
            md_text = src_path.read_text(encoding='utf-8')
            content_html = process_markdown(md_text)

        page_html = generate_section_html(section, content_html, i)
        out_path = OUTPUT_DIR / f"{section['slug']}.html"
        out_path.write_text(page_html, encoding='utf-8')
        print(f"  Generated: {section['slug']}.html")

    print()
    print("Done! All files generated successfully.")


if __name__ == '__main__':
    main()
