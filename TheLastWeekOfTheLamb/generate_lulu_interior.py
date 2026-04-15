#!/usr/bin/env python3
"""Generate Lulu-ready interior PDF for The Last Week of the Lamb.

Matches the 5.5" x 8.5" Lulu interior spec (also compatible with IngramSpark).
  - Page size: 5.5in x 8.5in
  - Gutter (inside margin): 0.75in
  - Outside margin: 0.625in
  - Top/bottom margin: 0.75in
  - Chapters start on recto (right-hand, odd) pages
  - All fonts embedded (EB Garamond)
  - Page count forced even

Source: markdown files in this directory. This first pass builds the text-only
interior with placeholder boxes where the 15 charts will be rendered later.
"""

import re
from pathlib import Path

import markdown as md
import weasyprint
from docx import Document

BOOK_DIR = Path(__file__).parent
OUTPUT = BOOK_DIR / "The_Last_Week_of_the_Lamb_Lulu_Interior.pdf"
DEBUG_HTML = BOOK_DIR / "_lulu_debug.html"

FONT_DIR = Path.home() / ".local" / "share" / "fonts"

BOOK_TITLE = "The Last Week of the Lamb"
BOOK_SUBTITLE = "The Passover Pattern Good Friday Missed"
AUTHOR = "Paul Hainline"
IMPRINT = "NobleMind Press"
COPYRIGHT_YEAR = "2026"


# --------------------------------------------------------------------------
# BOOK STRUCTURE
# --------------------------------------------------------------------------
# Each entry:
#   kind: 'prologue' | 'chapter' | 'interlude' | 'epilogue'
#   file: markdown filename
#   label: top-of-page label (Chapter One / Prologue / Interlude / Epilogue)
#   charts_after: list of chart IDs to insert at the END of this section
#   charts_in:    list of (chart_id, anchor_text) to insert after the
#                 first paragraph containing anchor_text (None = append)
#
# Charts are inserted as placeholder boxes in this first pass; final visuals
# come in a second pass once Paul finalizes the 16th chart.

SECTIONS = [
    {
        "kind": "prologue",
        "file": "Prologue_The_Promise_and_the_Thread.md",
        "label": "Prologue",
        "charts_after": ["A"],
    },
    {"kind": "part", "title": "Part One", "subtitle": "The Pattern"},
    {
        "kind": "chapter",
        "file": "Chapter01_The_Lamb_in_Egypt.md",
        "label": "Chapter One",
        "charts_after": ["1"],
    },
    {
        "kind": "chapter",
        "file": "Chapter02_The_Lamb_in_Prophecy.md",
        "label": "Chapter Two",
        "charts_after": ["2"],
    },
    {
        "kind": "interlude",
        "file": "Understanding_the_Hebrew_Calendar_Interlude.md",
        "label": "Interlude",
        "charts_after": ["3"],
    },
    {"kind": "part", "title": "Part Two", "subtitle": "The Week"},
    {
        "kind": "chapter",
        "file": "Chapter03_The_Arrival_and_the_Selection.md",
        "label": "Chapter Three",
        "charts_after": ["4", "5"],
    },
    {
        "kind": "chapter",
        "file": "Chapter04_Leaves_Without_Fruit.md",
        "label": "Chapter Four",
        "charts_after": ["6"],
    },
    {
        "kind": "chapter",
        "file": "Chapter05_The_Lamb_Is_Examined.md",
        "label": "Chapter Five",
        "charts_after": ["7"],
    },
    {
        "kind": "chapter",
        "file": "Chapter06_The_Anointing_and_the_Betrayal.md",
        "label": "Chapter Six",
        "charts_after": [],
    },
    {
        "kind": "chapter",
        "file": "Chapter07_The_Passover.md",
        "label": "Chapter Seven",
        "charts_after": ["8"],
    },
    {
        "kind": "chapter",
        "file": "Chapter08_The_Cup_and_the_Trials.md",
        "label": "Chapter Eight",
        "charts_after": ["9"],
    },
    {
        "kind": "chapter",
        "file": "Chapter09_The_Lamb_Is_Killed.md",
        "label": "Chapter Nine",
        "charts_after": ["10", "11"],
    },
    {"kind": "part", "title": "Part Three", "subtitle": "The Silence"},
    {
        "kind": "chapter",
        "file": "Chapter10_Three_Days_and_Three_Nights.md",
        "label": "Chapter Ten",
        "charts_after": ["12", "13", "14"],
    },
    {"kind": "part", "title": "Part Four", "subtitle": "The Open Door"},
    {
        "kind": "chapter",
        "file": "Chapter11_The_Stone_Moves.md",
        "label": "Chapter Eleven",
        "charts_after": [],
    },
    {
        "kind": "chapter",
        "file": "Chapter12_When_Did_the_Lamb_Die.md",
        "label": "Chapter Twelve",
        "charts_after": [],
    },
    {
        "kind": "epilogue",
        "file": "Epilogue_The_Thread_Completed.md",
        "label": "Epilogue",
        "charts_after": ["15"],
    },
]

CHART_TITLES = {
    "A":  "The Thread",
    "1":  "The Passover Blueprint",
    "2":  "Two Portraits of the Same Lamb",
    "3":  "Two Sabbaths in One Week",
    "4":  "John's Count",
    "5":  "Two Paths to the Same Day",
    "6":  "Mark's Next-Day Sequence",
    "7":  "The Examination of the Lamb",
    "8":  "The Timing Question",
    "9":  "The Inspection Complete",
    "10": "Nisan 14 — The Longest Day",
    "11": "The Blueprint Fulfilled",
    "12": "The Spice Paradox",
    "13": "The Count",
    "14": "Friday vs. Wednesday",
    "15": "From Bethany to the Empty Tomb",
}


# --------------------------------------------------------------------------
# MARKDOWN PROCESSING
# --------------------------------------------------------------------------

# Matches the book's scripture-quote format:
#   > *"quote text ..."* — **Book Ref**
# The quote may contain fancy double quotes; the dash may be em or hyphen.
SCRIPTURE_QUOTE_RE = re.compile(
    r'^>\s*\*["\u201C]([^"\u201D]+)["\u201D]\*\s*[\u2014\-]+\s*\*\*([^*]+?)\*\*\s*$',
    re.MULTILINE,
)

# Matches the first heading line of a source file (the section title).
TITLE_LINE_RE = re.compile(r'^#\s+(.+?)\s*$', re.MULTILINE)


def parse_title(title_text):
    """Split `Chapter Three: The Arrival — Nisan 9-10` into label/title/subtitle.

    Returns (label, main_title, subtitle_or_none). If there's no colon label
    (e.g. `Understanding the Hebrew Calendar`), label is None.
    """
    # Split off optional subtitle after em dash
    main = title_text
    subtitle = None
    if "\u2014" in main:  # em dash
        parts = main.split("\u2014", 1)
        main = parts[0].strip()
        subtitle = parts[1].strip()

    # Split off optional label (before colon)
    if ":" in main:
        label, title = main.split(":", 1)
        return label.strip(), title.strip(), subtitle
    return None, main.strip(), subtitle


def convert_scripture_quotes(text):
    """Replace the custom scripture-quote format with HTML blockquotes."""
    def replace(m):
        quote = m.group(1).strip()
        ref = m.group(2).strip()
        return (
            f'<blockquote class="scripture"><p>{quote}</p>'
            f'<cite>{ref}</cite></blockquote>'
        )
    return SCRIPTURE_QUOTE_RE.sub(replace, text)


def process_markdown(md_text):
    """Convert the book's markdown flavor to HTML body."""
    # Strip the first heading line (handled separately as chapter title)
    md_text = TITLE_LINE_RE.sub("", md_text, count=1).lstrip("\n")

    # Pre-process scripture quotes to raw HTML (markdown will pass through)
    md_text = convert_scripture_quotes(md_text)

    # Convert to HTML
    html = md.markdown(md_text, extensions=["extra", "smarty"])

    # Wrap `---` horizontal rules as ornamental dividers.
    # python-markdown renders --- as <hr />; style with CSS instead of changing.
    return html


def load_section(filename):
    """Load a markdown file and return (label, title, subtitle, body_html)."""
    src = (BOOK_DIR / filename).read_text(encoding="utf-8")

    # Extract title from first heading
    m = TITLE_LINE_RE.search(src)
    raw_title = m.group(1) if m else filename
    label, title, subtitle = parse_title(raw_title)

    body_html = process_markdown(src)
    return label, title, subtitle, body_html


def chart_placeholder(chart_id):
    """Dispatch to the appropriate chart renderer."""
    renderer = CHART_RENDERERS.get(chart_id)
    if renderer is None:
        return ""
    return renderer()


# =====================================================================
# CHART RENDERERS
# =====================================================================
#
# Each function returns an HTML fragment for one chart. All charts are
# wrapped in a <figure class="chart"> containing:
#   - <p class="chart-label">Chart N</p>
#   - <p class="chart-title">Chart Name</p>
#   - the chart body (table, flow, or specialized structure)
#   - optional <p class="chart-note"> caption
#
# Everything renders in grayscale using the value ladder established by
# Appendix B: #1a1a1a (header), #555 (primary band), #ddd (secondary band),
# #f5f5f5 (zebra), #c8c8c8 (borders).
# =====================================================================


def _chart_open(chart_id, title):
    return (
        '<figure class="chart">'
        f'<p class="chart-label">Chart {chart_id}</p>'
        f'<p class="chart-title">{title}</p>'
    )


def _chart_close(note=None):
    note_html = f'<figcaption class="chart-note">{note}</figcaption>' if note else ""
    return f"{note_html}</figure>"


def _simple_table(
    chart_id,
    title,
    headers,
    rows,
    col_widths=None,
    emphasis_rows=None,
    note=None,
):
    """Build a chart consisting of a single data table.

    headers: list of column labels (None for no header row).
    rows: list of row data; each row is a list of cells.
    col_widths: optional list of CSS widths (e.g. ['25%','50%','25%']).
    emphasis_rows: set of row indices that should render with dark emphasis.
    note: optional italic caption below the table.
    """
    emphasis_rows = emphasis_rows or set()

    colgroup = ""
    if col_widths:
        colgroup = (
            "<colgroup>"
            + "".join(f'<col style="width:{w}">' for w in col_widths)
            + "</colgroup>"
        )

    thead = ""
    if headers:
        thead = (
            '<thead><tr>'
            + "".join(f"<th>{h}</th>" for h in headers)
            + "</tr></thead>"
        )

    body_rows = []
    for i, row in enumerate(rows):
        cls = "chart-row-emphasis" if i in emphasis_rows else ""
        tr_class = f' class="{cls}"' if cls else ""
        cells_html = "".join(f"<td>{c}</td>" for c in row)
        body_rows.append(f"<tr{tr_class}>{cells_html}</tr>")
    tbody = "<tbody>" + "".join(body_rows) + "</tbody>"

    return (
        _chart_open(chart_id, title)
        + f'<table class="chart-table">{colgroup}{thead}{tbody}</table>'
        + _chart_close(note)
    )


# ---------------------------------------------------------------------
# Chart A — The Thread (vertical flow)
# ---------------------------------------------------------------------

def build_chart_A():
    nodes = [
        ("Genesis 3:15", "The seed of the woman will crush the serpent's head"),
        ("Abraham", "&ldquo;In your seed all the nations shall be blessed&rdquo; (Genesis 22:18)"),
        ("Judah", "&ldquo;The scepter shall not depart&rdquo; (Genesis 49:10)"),
        ("David", "&ldquo;I will establish the throne of his kingdom forever&rdquo; (2 Samuel 7:12&ndash;16)"),
        ("Bethlehem", "&ldquo;Too small to be counted&hellip; yet from you One will go forth&rdquo; (Micah 5:2)"),
        ("Isaiah", "&ldquo;Like a lamb that is led to slaughter&rdquo; (Isaiah 53:7)"),
        ("Exodus 12", "The Passover Lamb: selected, kept, killed, blood applied"),
        ("John 1:29", "&ldquo;Behold, the Lamb of God who takes away the sin of the world!&rdquo;"),
    ]
    items = "".join(
        f'<li class="thread-node">'
        f'<span class="thread-label">{label}</span>'
        f'<span class="thread-text">{text}</span>'
        f"</li>"
        for label, text in nodes
    )
    return (
        _chart_open("A", CHART_TITLES["A"])
        + f'<ol class="chart-thread">{items}</ol>'
        + _chart_close()
    )


# ---------------------------------------------------------------------
# Chart 1 — The Passover Blueprint
# ---------------------------------------------------------------------

def build_chart_1():
    rows = [
        ["1. Selection",
         '&ldquo;Each household is to take a lamb&rdquo; &mdash; on Nisan 10',
         "Exodus 12:3"],
        ["2. Requirement",
         '&ldquo;Your lamb shall be an unblemished male&rdquo;',
         "Exodus 12:5"],
        ["3. Keeping",
         '&ldquo;You shall keep it until the fourteenth day&rdquo; &mdash; four days',
         "Exodus 12:6a"],
        ["4. Killing",
         '&ldquo;The whole assembly of Israel is to kill it at twilight&rdquo; &mdash; Nisan 14',
         "Exodus 12:6b"],
        ["5. Blood applied",
         '&ldquo;Take some of the blood and put it on the two doorposts and on the lintel&rdquo;',
         "Exodus 12:7"],
        ["6. Promise",
         '&ldquo;When I see the blood I will pass over you&rdquo;',
         "Exodus 12:13"],
    ]
    return _simple_table(
        "1", CHART_TITLES["1"],
        headers=["Step", "What God Commanded", "Scripture"],
        rows=rows,
        col_widths=["22%", "58%", "20%"],
    )


# ---------------------------------------------------------------------
# Chart 2 — Two Portraits of the Same Lamb
# ---------------------------------------------------------------------

def build_chart_2():
    rows = [
        ["Selected for sacrifice",
         '&ldquo;The LORD was pleased to crush Him&rdquo; (53:10)'],
        ["Unblemished &mdash; no defect",
         '&ldquo;He had done no violence, nor was there any deceit in His mouth&rdquo; (53:9)'],
        ["Kept in the household",
         '&ldquo;Despised and forsaken of men&rdquo; &mdash; He lived among them (53:3)'],
        ["Silent at the slaughter",
         '&ldquo;Like a lamb that is led to slaughter&hellip; He did not open His mouth&rdquo; (53:7)'],
        ["Killed at the appointed time",
         '&ldquo;Cut off out of the land of the living&rdquo; (53:8)'],
        ["Blood saves from death",
         '&ldquo;Pierced through for our transgressions&hellip; by His scourging we are healed&rdquo; (53:5)'],
        ["&mdash;",
         '&ldquo;He will see His offspring, He will prolong His days&rdquo; &mdash; He dies <em>and</em> lives again (53:10)'],
    ]
    return _simple_table(
        "2", CHART_TITLES["2"],
        headers=["The Pattern (Exodus 12)", "The Prophecy (Isaiah 53)"],
        rows=rows,
        col_widths=["50%", "50%"],
    )


# ---------------------------------------------------------------------
# Chart 3 — Two Sabbaths in One Week
# ---------------------------------------------------------------------

def build_chart_3():
    rows = [
        ["<strong>Wednesday</strong>", "Nisan 14", "Preparation Day",
         "Crucifixion and burial before sundown"],
        ["<strong>Thursday</strong>", "Nisan 15", "<strong>HIGH-DAY SABBATH</strong>",
         'First day of Unleavened Bread &mdash; commanded rest (Lev 23:6&ndash;7). '
         '&ldquo;That Sabbath was a high day&rdquo; (John 19:31)'],
        ["<strong>Friday</strong>", "Nisan 16", "<strong>Working Day</strong>",
         "Ordinary day &mdash; women buy and prepare spices (Mark 16:1; Luke 23:56)"],
        ["<strong>Saturday</strong>", "Nisan 17", "<strong>WEEKLY SABBATH</strong>",
         'Seventh-day rest &mdash; &ldquo;On the Sabbath they rested according to the commandment&rdquo; (Luke 23:56b)'],
        ["<strong>Sunday</strong>", "Nisan 18", "First day of the week",
         "Tomb found empty at dawn (John 20:1)"],
    ]
    return _simple_table(
        "3", CHART_TITLES["3"],
        headers=["Day", "Date", "Type", "Activity"],
        rows=rows,
        col_widths=["16%", "14%", "24%", "46%"],
        emphasis_rows={1, 3},  # two Sabbath rows
    )


# ---------------------------------------------------------------------
# Chart 4 — John's Count
# ---------------------------------------------------------------------

def build_chart_4():
    rows = [
        ["Day 1", "14", "Wednesday", "Passover &mdash; the Lamb is killed"],
        ["Day 2", "13", "Tuesday", ""],
        ["Day 3", "12", "Monday", ""],
        ["Day 4", "11", "Sunday", ""],
        ["Day 5", "10", "Saturday", "Entry into Jerusalem"],
        ["Day 6", "9", "Friday", "<strong>Jesus arrives in Bethany</strong> (John 12:1)"],
    ]
    return _simple_table(
        "4", CHART_TITLES["4"],
        headers=["Count", "Nisan Date", "Weekday", "Event"],
        rows=rows,
        col_widths=["16%", "18%", "22%", "44%"],
        emphasis_rows={5},
    )


# ---------------------------------------------------------------------
# Chart 5 — Two Paths to the Same Day
# ---------------------------------------------------------------------

def build_chart_5():
    path1_rows = [
        ['&ldquo;After two days is the Passover&rdquo; (Mark 14:1)', "Wednesday", "14"],
        ["&larr; teaching day, fig tree withered (Mark 11:20)", "Monday", "12"],
        ['&larr; &ldquo;on the next day&rdquo; &mdash; fig tree cursed, temple cleansed (Mark 11:12)',
         "Sunday", "11"],
        ['&larr; &ldquo;on the next day&rdquo; &mdash; entry into Jerusalem (John 12:12)',
         "<strong>Saturday</strong>", "<strong>10</strong>"],
    ]
    path2_rows = [
        ["Day 6 = arrival in Bethany", "9", "Friday"],
        ['Day 5 = &ldquo;on the next day&rdquo; = entry',
         "<strong>10</strong>", "<strong>Saturday</strong>"],
    ]

    def _subtable(caption, headers, rows, col_widths):
        thead = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>"
        tbody_html = "<tbody>" + "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows
        ) + "</tbody>"
        colgroup = (
            "<colgroup>"
            + "".join(f'<col style="width:{w}">' for w in col_widths)
            + "</colgroup>"
        )
        return (
            f'<p class="chart-subhead">{caption}</p>'
            f'<table class="chart-table">{colgroup}{thead}{tbody_html}</table>'
        )

    body = (
        _subtable(
            "Path 1 &mdash; Mark's Sequence (backward from the known anchor)",
            ["Marker", "Day", "Nisan"],
            path1_rows,
            ["66%", "20%", "14%"],
        )
        + _subtable(
            "Path 2 &mdash; John's Count (backward from Passover)",
            ["Count", "Nisan", "Weekday"],
            path2_rows,
            ["56%", "18%", "26%"],
        )
        + '<p class="chart-landing">Both paths &rarr; Saturday, Nisan 10 for the entry into Jerusalem.</p>'
    )
    return _chart_open("5", CHART_TITLES["5"]) + body + _chart_close()


# ---------------------------------------------------------------------
# Chart 6 — Mark's Next-Day Sequence (vertical timeline)
# ---------------------------------------------------------------------

def build_chart_6():
    phases = [
        {
            "day": "SATURDAY, Nisan 10",
            "events": [
                "Entry into Jerusalem (John 12:12; Mark 11:1&ndash;11)",
                "Looks around the temple, returns to Bethany (Mark 11:11)",
            ],
            "transition": '&ldquo;on the next day&rdquo; (Mark 11:12)',
        },
        {
            "day": "SUNDAY, Nisan 11",
            "events": [
                "Fig tree cursed (Mark 11:12&ndash;14)",
                "Temple cleansed (Mark 11:15&ndash;17)",
            ],
            "transition": '&ldquo;in the morning&rdquo; (Mark 11:20)',
        },
        {
            "day": "MONDAY, Nisan 12",
            "events": [
                "Fig tree withered (Mark 11:20)",
                "Teaching all day (Mark 11:27&ndash;13:37)",
                '&ldquo;After two days the Passover&rdquo; (Mark 14:1)',
            ],
            "transition": "Tuesday, Nisan 13 &mdash; betrayal arranged; evening: Last Supper begins Nisan 14",
        },
        {
            "day": "WEDNESDAY, Nisan 14",
            "events": [
                "Trials, crucifixion, burial before sundown",
            ],
            "transition": None,
        },
    ]

    blocks = []
    for p in phases:
        events = "".join(f"<li>{e}</li>" for e in p["events"])
        block = (
            '<li class="timeline-phase">'
            f'<div class="timeline-day">{p["day"]}</div>'
            f'<ul class="timeline-events">{events}</ul>'
            "</li>"
        )
        blocks.append(block)
        if p["transition"]:
            blocks.append(
                f'<li class="timeline-transition"><em>{p["transition"]}</em></li>'
            )

    body = '<ol class="chart-timeline">' + "".join(blocks) + "</ol>"
    return _chart_open("6", CHART_TITLES["6"]) + body + _chart_close()


# ---------------------------------------------------------------------
# Chart 7 — The Examination of the Lamb
# ---------------------------------------------------------------------

def build_chart_7():
    rows = [
        ["Chief priests, scribes, elders",
         "Sanhedrin &mdash; ruling council",
         '&ldquo;By what authority are You doing these things?&rdquo; (Mark 11:27&ndash;28)',
         "Could not answer His counter-question &mdash; withdrew (Mark 11:33)"],
        ["Pharisees and Herodians",
         "Religious law + political power",
         '&ldquo;Is it lawful to pay a poll-tax to Caesar?&rdquo; (Mark 12:13&ndash;15)',
         '&ldquo;They were amazed at Him&rdquo; &mdash; withdrew (Mark 12:17)'],
        ["Sadducees",
         "Temple aristocracy",
         "Resurrection trick question &mdash; seven brothers (Mark 12:18&ndash;23)",
         '&ldquo;You are greatly mistaken&rdquo; &mdash; silenced (Mark 12:27)'],
        ["A scribe",
         "Legal expertise",
         '&ldquo;What commandment is the foremost?&rdquo; (Mark 12:28)',
         '&ldquo;You are not far from the kingdom of God&rdquo; &mdash; no one dared ask any more (Mark 12:34)'],
        ["<strong>Cumulative verdict</strong>",
         "<strong>Every authority in Israel</strong>",
         "",
         '<strong>&ldquo;No one was able to answer Him a word, nor did anyone dare from that day on to ask Him another question&rdquo; (Matthew 22:46)</strong>'],
    ]
    return _simple_table(
        "7", CHART_TITLES["7"],
        headers=["Examiner", "Their Authority", "Their Test", "Result"],
        rows=rows,
        col_widths=["22%", "20%", "28%", "30%"],
        emphasis_rows={4},
    )


# ---------------------------------------------------------------------
# Chart 8 — The Timing Question (two-part)
# ---------------------------------------------------------------------

def build_chart_8():
    tension_rows = [
        ["<strong>The Last Supper</strong>",
         'A Passover meal &mdash; &ldquo;I have earnestly desired to eat this Passover with you before I suffer&rdquo; (Luke 22:15)',
         "Judas left to betray Him during the meal (John 13:21&ndash;30)"],
        ["<strong>The next morning</strong>",
         "Jesus already under arrest and on trial",
         'The Jewish leaders &ldquo;did not enter into the Praetorium so that they would not be defiled, but might eat the Passover&rdquo; (John 18:28)'],
        ["<strong>The crucifixion day</strong>",
         '&ldquo;The day of preparation&rdquo; (Mark 15:42)',
         '&ldquo;The day of preparation for the Passover&rdquo; (John 19:14)'],
        ["<strong>The tension</strong>",
         "Jesus ate the Passover the night before",
         "The leaders had not yet eaten it the next morning"],
    ]

    readings_rows = [
        ['<strong>&ldquo;Passover&rdquo; = broader festival</strong>',
         '&ldquo;Eat the Passover&rdquo; in John 18:28 refers to festival meals, not the lamb specifically. Luke 22:1 shows the terms overlapped.',
         "Simple resolution",
         'Requires &ldquo;eat the Passover&rdquo; to mean something other than its most natural sense'],
        ["<strong>Jesus ate early</strong>",
         "Jesus ate the Passover ahead of the national observance because He would be dead before the nation sat down for it. He could not eat the Passover and BE the Passover at the same time.",
         "Preserves natural meaning of both accounts; aligns with Exodus 12 pattern",
         "Inference &mdash; the text does not state this in so many words"],
    ]

    def _subtable(caption, headers, rows, col_widths):
        thead = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>"
        tbody_html = "<tbody>" + "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows
        ) + "</tbody>"
        colgroup = (
            "<colgroup>"
            + "".join(f'<col style="width:{w}">' for w in col_widths)
            + "</colgroup>"
        )
        return (
            f'<p class="chart-subhead">{caption}</p>'
            f'<table class="chart-table">{colgroup}{thead}{tbody_html}</table>'
        )

    body = (
        _subtable(
            "The tension",
            ["", "The Synoptics Say", "John Says"],
            tension_rows,
            ["22%", "39%", "39%"],
        )
        + _subtable(
            "Two possible readings",
            ["Reading", "Explanation", "Strength", "Limitation"],
            readings_rows,
            ["22%", "38%", "20%", "20%"],
        )
    )
    return _chart_open("8", CHART_TITLES["8"]) + body + _chart_close()


# ---------------------------------------------------------------------
# Chart 9 — The Inspection Complete
# ---------------------------------------------------------------------

def build_chart_9():
    rows = [
        ["Chief priests, scribes, elders", "Jewish ruling council",
         "Could not answer &mdash; withdrew", "Mark 11:27&ndash;33"],
        ["Pharisees and Herodians", "Religious law + political power",
         "Amazed &mdash; withdrew", "Mark 12:13&ndash;17"],
        ["Sadducees", "Temple aristocracy",
         "Silenced", "Mark 12:18&ndash;27"],
        ["A scribe", "Legal expertise",
         '&ldquo;Not far from the kingdom&rdquo; &mdash; no more questions', "Mark 12:28&ndash;34"],
        ["Annas", "Former high priest",
         "Sent Him bound to Caiaphas", "John 18:13&ndash;24"],
        ["Caiaphas and the Sanhedrin", "Supreme Jewish court",
         "False witnesses &mdash; testimony did not agree (Mark 14:56, 59). Condemned on His own testimony.",
         "Mark 14:53&ndash;65"],
        ["Pilate (first)", "Roman governor",
         '<strong>&ldquo;I find no guilt in this man&rdquo;</strong> (Luke 23:4)',
         "Luke 23:1&ndash;5"],
        ["Herod Antipas", "Tetrarch of Galilee",
         "No charge &mdash; mocked Him and sent Him back", "Luke 23:6&ndash;12"],
        ["Pilate (second)", "Roman governor",
         '<strong>&ldquo;I have found no guilt in this man&rdquo;</strong> &mdash; noted Herod agreed (Luke 23:14&ndash;15)',
         "Luke 23:13&ndash;16"],
        ["Pilate (third)", "Roman governor",
         '<strong>&ldquo;I find no guilt in Him&rdquo;</strong> (John 19:4)',
         "John 19:4"],
        ["<strong>Total</strong>", "<strong>Every religious and civil authority</strong>",
         "<strong>No legitimate fault found</strong>", ""],
    ]
    return _simple_table(
        "9", CHART_TITLES["9"],
        headers=["Examiner", "Authority", "Finding", "Scripture"],
        rows=rows,
        col_widths=["26%", "22%", "36%", "16%"],
        emphasis_rows={10},
        note='The Passover lamb was required to be &ldquo;unblemished&rdquo; '
             '(Exodus 12:5). Every examiner searched for a blemish. '
             'None found one. <em>(Typological inference.)</em>',
    )


# ---------------------------------------------------------------------
# Chart 10 — Nisan 14 The Longest Day (vertical phase timeline)
# ---------------------------------------------------------------------

def build_chart_10():
    phases = [
        ("Tuesday evening", "Nisan 14 begins at sundown",
         ["Last Supper", "Gethsemane", "Arrest"]),
        ("Night", "Religious trials under cover of darkness",
         ["Before Annas", "Before Caiaphas and the Sanhedrin", "Peter's denial"]),
        ("Wednesday morning", "Dawn &mdash; civil trials begin",
         ["Before Pilate", "Before Herod", "Before Pilate again"]),
        ("Noon", "The sixth hour (Mark 15:33)",
         ["Crucifixion"]),
        ("Noon &ndash; 3 PM", "Three hours of darkness",
         ["Darkness over the land"]),
        ("3 PM", "The ninth hour (Mark 15:34)",
         ["Death &mdash; &ldquo;It is finished&rdquo;"]),
        ("Before sundown", "Preparation Day must not bleed into the Sabbath",
         ["Burial by Joseph of Arimathea and Nicodemus"]),
    ]
    blocks = []
    for time, detail, events in phases:
        events_html = "".join(f"<li>{e}</li>" for e in events)
        blocks.append(
            '<li class="longest-phase">'
            f'<div class="longest-time">{time}</div>'
            f'<div class="longest-detail">{detail}</div>'
            f'<ul class="longest-events">{events_html}</ul>'
            "</li>"
        )
    body = '<ol class="chart-longest-day">' + "".join(blocks) + "</ol>"
    return (
        _chart_open("10", CHART_TITLES["10"])
        + body
        + _chart_close(
            "One continuous day &mdash; from sundown Tuesday evening through burial before sundown Wednesday."
        )
    )


# ---------------------------------------------------------------------
# Chart 11 — The Blueprint Fulfilled
# ---------------------------------------------------------------------

def build_chart_11():
    rows = [
        ["<strong>Nisan 10:</strong> Select the lamb (Exodus 12:3)",
         "<strong>Saturday, Nisan 10:</strong> Jesus enters Jerusalem &mdash; "
         "presented to the nation (John 12:12; Mark 11:1&ndash;11). "
         "<em>(Typological inference)</em>"],
        ["<strong>Nisan 10&ndash;13:</strong> Keep the lamb &mdash; must be unblemished (Exodus 12:5&ndash;6)",
         "<strong>Sunday&ndash;Tuesday, Nisan 11&ndash;13:</strong> Every authority group "
         "in Israel examines Jesus. No fault found (Matt 22:46). "
         "<em>(Typological inference &mdash; the text does not say the keeping period was for inspection.)</em>"],
        ["<strong>Nisan 14 at twilight:</strong> Kill the lamb (Exodus 12:6)",
         "<strong>Wednesday, Nisan 14:</strong> Jesus crucified, dies at approximately 3 PM &mdash; "
         "the hour when the Passover lambs were being slaughtered (Mark 15:34, 37)"],
        ["Blood applied to the doorposts (Exodus 12:7)",
         'His blood poured out &mdash; &ldquo;for the forgiveness of sins&rdquo; (Matthew 26:28)'],
        ['&ldquo;When I see the blood, I will pass over you&rdquo; (Exodus 12:13)',
         '&ldquo;Christ our Passover has been sacrificed&rdquo; (1 Corinthians 5:7) '
         '&mdash; <em>Scripture&rsquo;s own connection</em>'],
        ["The lamb's death brings deliverance from death",
         "Three days and three nights in the tomb. The stone moves. The tomb is empty."],
    ]
    return _simple_table(
        "11", CHART_TITLES["11"],
        headers=["The Blueprint (Exodus 12)", "The Fulfillment (The Gospels)"],
        rows=rows,
        col_widths=["44%", "56%"],
    )


# ---------------------------------------------------------------------
# Chart 12 — The Spice Paradox
# ---------------------------------------------------------------------

def build_chart_12():
    rows = [
        ["Women observe where the body is laid", "Luke 23:55", "Wednesday before sundown"],
        ["Women return home and prepare spices and perfumes", "Luke 23:56a", "???"],
        ["Women rest on the Sabbath according to the commandment", "Luke 23:56b", "A Sabbath"],
        ['<strong>&ldquo;When the Sabbath was over,&rdquo;</strong> Mary Magdalene, '
         'Mary, and Salome <strong>buy</strong> spices',
         "Mark 16:1", "After a Sabbath ended"],
        ["Women come to the tomb at dawn", "Mark 16:2", "Sunday morning"],
    ]
    table_html = (
        '<table class="chart-table">'
        '<colgroup><col style="width:56%"><col style="width:18%"><col style="width:26%"></colgroup>'
        '<thead><tr><th>Event</th><th>Scripture</th><th>When It Happened</th></tr></thead>'
        '<tbody>'
        + "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows
        )
        + "</tbody></table>"
    )
    paradox = (
        '<p class="chart-landing">You cannot prepare what you have not yet purchased.</p>'
    )
    explanation = (
        '<p class="chart-body-text">If there is only one Sabbath (Saturday), Luke '
        'says they prepared spices <em>before</em> Saturday and Mark says they '
        '<em>bought</em> spices <em>after</em> a Sabbath. They cannot prepare '
        'spices they haven&rsquo;t bought yet &mdash; unless there are '
        '<strong>two Sabbaths</strong>: a high-day Sabbath (Thursday), after '
        'which they buy spices on Friday, prepare them, and then rest again on '
        'the weekly Sabbath (Saturday).</p>'
    )
    flow = (
        '<div class="chart-flow">'
        '<span class="flow-step">Wed (burial)</span>'
        '<span class="flow-arrow">&rarr;</span>'
        '<span class="flow-step flow-emphasis">Thu (HIGH-DAY SABBATH)</span>'
        '<span class="flow-arrow">&rarr;</span>'
        '<span class="flow-step">Fri (buy &amp; prepare spices)</span>'
        '<span class="flow-arrow">&rarr;</span>'
        '<span class="flow-step flow-emphasis">Sat (WEEKLY SABBATH)</span>'
        '<span class="flow-arrow">&rarr;</span>'
        '<span class="flow-step">Sun (tomb empty)</span>'
        '</div>'
    )
    return (
        _chart_open("12", CHART_TITLES["12"])
        + table_html
        + paradox
        + explanation
        + flow
        + _chart_close()
    )


# ---------------------------------------------------------------------
# Chart 13 — The Count
# ---------------------------------------------------------------------

def build_chart_13():
    rows = [
        ["<strong>Night 1</strong>", "Wed sundown &rarr; Thu sunrise",
         "Body in the tomb. High-day Sabbath begins.", "&#9632;"],
        ["<strong>Day 1</strong>", "Thu sunrise &rarr; Thu sundown",
         "High-day Sabbath (Nisan 15). Guard posted (Matt 27:62&ndash;66).", "&#9632;"],
        ["<strong>Night 2</strong>", "Thu sundown &rarr; Fri sunrise",
         "", "&#9632;"],
        ["<strong>Day 2</strong>", "Fri sunrise &rarr; Fri sundown",
         "Working day. Women buy spices (Mark 16:1), prepare them (Luke 23:56a).", "&#9632;"],
        ["<strong>Night 3</strong>", "Fri sundown &rarr; Sat sunrise",
         "Weekly Sabbath begins.", "&#9632;"],
        ["<strong>Day 3</strong>", "Sat sunrise &rarr; Sat sundown",
         "Weekly Sabbath. Women rest (Luke 23:56b). Three days and three nights complete at sundown.",
         "&#9632;"],
        ["",
         "<strong>After Saturday sundown</strong>",
         "<strong>RISEN</strong> &mdash; tomb found empty Sunday at dawn (John 20:1)",
         ""],
    ]
    return _simple_table(
        "13", CHART_TITLES["13"],
        headers=["Period", "From &rarr; To", "What Happened", ""],
        rows=rows,
        col_widths=["16%", "26%", "48%", "10%"],
        emphasis_rows={6},
        note="Total: Three nights. Three days. Exactly as He said (Matthew 12:40).",
    )


# ---------------------------------------------------------------------
# Chart 14 — Friday vs. Wednesday
# ---------------------------------------------------------------------

def build_chart_14():
    rows = [
        ["<strong>Sign of Jonah (Matt 12:40)</strong>",
         "2 nights (Fri, Sat), partial days &mdash; requires &ldquo;three days and three nights&rdquo; to be figurative",
         "3 nights (Wed, Thu, Fri) + 3 days (Thu, Fri, Sat) &mdash; literal fulfillment"],
        ['<strong>&ldquo;High day&rdquo; Sabbath (John 19:31)</strong>',
         "Must mean the weekly Saturday Sabbath",
         "Nisan 15 = feast-day Sabbath (Lev 23:6&ndash;7) &mdash; a different Sabbath than Saturday"],
        ["<strong>The spice sequence</strong>",
         "Women buy AND prepare spices on Saturday evening after one Sabbath &mdash; very compressed timeline",
         "Women buy spices Friday (after high-day Sabbath), prepare them, rest again Saturday (weekly Sabbath) &mdash; two Sabbaths, one working day"],
        ['<strong>&ldquo;Preparation day&rdquo;</strong>',
         "Friday &mdash; the day before the weekly Sabbath",
         "The day before any Sabbath &mdash; in this case, the high-day Sabbath of Nisan 15"],
        ['<strong>Emmaus: &ldquo;third day&rdquo; (Luke 24:21)</strong>',
         "Counting from Friday: Sat=1, Sun=2 &mdash; only the second day",
         "Counting from Thursday (guard posted, last public event): Fri=1, Sat=2, Sun=3 &mdash; fits"],
        ["<strong>Passover typology</strong>",
         "Nisan 14 on a Friday &mdash; no alignment with Nisan 10 entry",
         "Nisan 14 on a Wednesday &mdash; entry on Nisan 10 (Saturday), four-day keeping period aligns with Exodus 12"],
    ]
    return _simple_table(
        "14", CHART_TITLES["14"],
        headers=["Evidence", "Friday Crucifixion", "Wednesday Crucifixion"],
        rows=rows,
        col_widths=["24%", "38%", "38%"],
    )


# ---------------------------------------------------------------------
# Chart 15 — From Bethany to the Empty Tomb (master timeline)
# ---------------------------------------------------------------------

def build_chart_15():
    rows = [
        ["<strong>Nisan 9 &mdash; Friday</strong>", "Arrival in Bethany",
         'Jesus arrives &ldquo;six days before the Passover&rdquo; (John 12:1). '
         "Supper at Lazarus&rsquo;s house. Mary anoints His feet (John 12:2&ndash;8).",
         "&mdash;", ""],
        ["<strong>Nisan 10 &mdash; Saturday</strong>", "The Lamb Is Selected",
         '&ldquo;On the next day&rdquo; (John 12:12). Rides into Jerusalem. '
         'Crowds: &ldquo;Hosanna!&rdquo; Enters temple, looks around, returns to Bethany (Mark 11:11).',
         "Every household selects its Passover lamb (Exodus 12:3). "
         "<em>(Typological inference)</em>", ""],
        ["<strong>Nisan 11 &mdash; Sunday</strong>", "Leaves Without Fruit",
         "Fig tree cursed (Mark 11:12&ndash;14). Temple cleansed (Matt 21:13). "
         '&ldquo;The next day&rdquo; after the entry (Mark 11:12).',
         "Lamb kept in the household &mdash; Day 1 <em>(Typological inference)</em>", ""],
        ["<strong>Nisan 12 &mdash; Monday</strong>", "The Lamb Is Examined",
         "Fig tree withered (Mark 11:20). Longest day of teaching (Matt 21:23&ndash;25:46). "
         'Every authority tests Him. No fault found. &ldquo;After two days the Passover&rdquo; (Mark 14:1).',
         "Lamb kept &mdash; Day 2 <em>(Typological inference)</em>", ""],
        ["<strong>Nisan 13 &mdash; Tuesday</strong>", "The Betrayal &amp; The Last Supper",
         "Judas arranges betrayal (Mark 14:10&ndash;11). Evening (sundown = Nisan 14): "
         "Passover meal. Bread and cup instituted. "
         '&ldquo;I have earnestly desired to eat this Passover with you before I suffer&rdquo; (Luke 22:15).',
         "Lamb kept &mdash; Day 3. Evening: Passover meal. "
         "<em>(Typological inference)</em>", ""],
        ["<strong>Nisan 14 &mdash; Wednesday</strong>", "The Lamb Is Killed",
         "Gethsemane. Arrest. Trials &mdash; Annas, Caiaphas, Sanhedrin, Pilate, Herod, Pilate. "
         '&ldquo;I find no guilt&rdquo; (Luke 23:4). Crucifixion noon&ndash;3 PM. Veil torn. '
         'Burial before sundown. &ldquo;That Sabbath was a high day&rdquo; (John 19:31).',
         'Lamb killed &ldquo;at twilight&rdquo; (Exodus 12:6). Blood applied.', ""],
        ["<strong>Nisan 15 &mdash; Thursday</strong>", "High-Day Sabbath",
         "First day of Unleavened Bread &mdash; commanded rest (Lev 23:6&ndash;7). "
         "Guard posted (Matt 27:62&ndash;66).",
         "", "Night 1, Day 1"],
        ["<strong>Nisan 16 &mdash; Friday</strong>", "The Day Between",
         "Working day. Women buy spices (Mark 16:1) and prepare them (Luke 23:56a).",
         "", "Night 2, Day 2"],
        ["<strong>Nisan 17 &mdash; Saturday</strong>", "Weekly Sabbath",
         '&ldquo;On the Sabbath they rested according to the commandment&rdquo; (Luke 23:56b). '
         "Three days and three nights complete at sundown.",
         "", "Night 3, Day 3"],
        ["<strong>1st Day &mdash; Sunday</strong>", "He Is Risen",
         "Tomb found empty at dawn. "
         '&ldquo;He is not here, for He has risen, just as He said&rdquo; (Matt 28:6).',
         "", ""],
    ]
    return _simple_table(
        "15", CHART_TITLES["15"],
        headers=["Date / Day", "Event", "What Happened", "Exodus 12 Parallel", "In Tomb"],
        rows=rows,
        col_widths=["17%", "18%", "37%", "19%", "9%"],
        note="The Exodus 12 column shows what God commanded Israel to do with the Passover "
             "lamb &mdash; and how Jesus fulfilled each step on the corresponding day. The "
             "correspondence between the keeping period and the Gospel examinations is our "
             "observation &mdash; a typological inference, not an explicit statement in the text.",
    )


# Dispatch table — maps chart ID to its builder function
CHART_RENDERERS = {
    "A":  build_chart_A,
    "1":  build_chart_1,
    "2":  build_chart_2,
    "3":  build_chart_3,
    "4":  build_chart_4,
    "5":  build_chart_5,
    "6":  build_chart_6,
    "7":  build_chart_7,
    "8":  build_chart_8,
    "9":  build_chart_9,
    "10": build_chart_10,
    "11": build_chart_11,
    "12": build_chart_12,
    "13": build_chart_13,
    "14": build_chart_14,
    "15": build_chart_15,
}


# --------------------------------------------------------------------------
# SECTION BUILDERS
# --------------------------------------------------------------------------

def build_section_html(section):
    kind = section["kind"]

    if kind == "part":
        return build_part_page(section["title"], section["subtitle"])

    label, title, subtitle, body_html = load_section(section["file"])

    # Force the label from the outline when provided (consistent TOC/heading)
    if section.get("label"):
        label = section["label"]

    # Append chart placeholders at the end of the section
    charts_after = section.get("charts_after") or []
    for cid in charts_after:
        body_html += chart_placeholder(cid)

    subtitle_html = f'<p class="chapter-subtitle">{subtitle}</p>' if subtitle else ""
    label_html = f'<p class="chapter-num">{label}</p>' if label else ""

    section_class = "chapter"
    if kind == "prologue":
        section_class = "chapter prologue"
    elif kind == "interlude":
        section_class = "chapter interlude"
    elif kind == "epilogue":
        section_class = "chapter epilogue"

    return f"""
    <section class="{section_class}">
      <div class="chapter-header">
        {label_html}
        <h1>{title}</h1>
        {subtitle_html}
      </div>
      <div class="chapter-body">
        {body_html}
      </div>
    </section>
    """


def build_part_page(title, subtitle):
    return f"""
    <section class="part-page">
      <div class="part-inner">
        <p class="part-num">{title}</p>
        <h1 class="part-title">{subtitle}</h1>
      </div>
    </section>
    """


# --------------------------------------------------------------------------
# TABLE OF CONTENTS
# --------------------------------------------------------------------------

def build_toc():
    items = []
    for section in SECTIONS:
        if section["kind"] == "part":
            items.append(
                f'<div class="toc-part">'
                f'<span class="toc-part-num">{section["title"]}</span>'
                f'<span class="toc-part-title">{section["subtitle"]}</span>'
                f'</div>'
            )
            continue

        label, title, subtitle, _ = load_section(section["file"])
        if section.get("label"):
            label = section["label"]

        if section["kind"] in ("prologue", "epilogue", "interlude"):
            items.append(
                f'<div class="toc-entry toc-special">'
                f'<span class="toc-title">{label}: {title}</span>'
                f'</div>'
            )
        else:
            items.append(
                f'<div class="toc-entry">'
                f'<span class="toc-num">{label}</span>'
                f'<span class="toc-title">{title}</span>'
                f'</div>'
            )

    items.append(
        '<div class="toc-entry toc-backmatter">'
        '<span class="toc-num">Appendix B</span>'
        '<span class="toc-title">Gospel Parallel Reference Chart</span>'
        '</div>'
    )
    items.append(
        '<div class="toc-entry toc-backmatter">'
        '<span class="toc-num">Appendix C</span>'
        '<span class="toc-title">Scripture Reference Index</span>'
        '</div>'
    )
    return "\n".join(items)


# --------------------------------------------------------------------------
# GOSPEL PARALLEL REFERENCE CHART (APPENDIX B)
# --------------------------------------------------------------------------

def build_gospel_parallel_html():
    """Parse Gospel_Parallel_Reference_Chart.docx and render as HTML table.

    Row types:
      - Header row (first row): "Event | Matthew | Mark | Luke | John"
      - Primary day banner: merged cell starting with "Nisan" or "First Day"
      - Sub-section banner: merged cell that doesn't start with "Nisan"/"First Day"
        (e.g. "Gethsemane and Arrest", "The Trials", "Crucifixion...")
      - Event row: 5 distinct cells
    """
    doc = Document(str(BOOK_DIR / "Gospel_Parallel_Reference_Chart.docx"))
    table = doc.tables[0]

    # Build rows in order; group each banner with its immediately following
    # event row in a small <tbody class="gp-sticky"> so WeasyPrint keeps them
    # together across page breaks (avoids orphaned banners at page bottom).
    # Subsequent event rows under the same banner go into individual tbodies
    # without the keep-together constraint so long sections can still flow.

    # First pass: collect rows as (kind, html) tuples.
    # Zebra-stripe event rows at build time (each will live in its own tbody,
    # so :nth-of-type CSS selectors can't reach across siblings).
    raw_rows = []
    event_counter = 0
    for ri, row in enumerate(table.rows):
        cells = [c.text.strip().replace("\n", " ") for c in row.cells]

        if ri == 0:
            raw_rows.append((
                "header",
                '<tr class="gp-header">'
                + "".join(f"<th>{c}</th>" for c in cells)
                + "</tr>",
            ))
            continue

        is_banner = all(c == cells[0] for c in cells) and bool(cells[0])
        if is_banner:
            text = cells[0]
            is_primary = text.startswith("Nisan") or text.startswith("First Day")
            kind = "day" if is_primary else "subsection"
            row_class = "gp-day" if is_primary else "gp-subsection"
            raw_rows.append((
                kind,
                f'<tr class="{row_class}"><td colspan="5">{text}</td></tr>',
            ))
            continue

        event_cell, *refs = cells
        ref_html = "".join(f'<td class="gp-ref">{r}</td>' for r in refs)
        zebra = "gp-event-alt" if event_counter % 2 == 1 else ""
        event_counter += 1
        raw_rows.append((
            "event",
            f'<tr class="gp-event {zebra}">'
            f'<td class="gp-event-name">{event_cell}</td>'
            f'{ref_html}'
            f'</tr>',
        ))

    # Second pass: group into tbodies.
    # - Header row: its own <thead> (repeats on page breaks)
    # - Banner + next event row: <tbody class="gp-sticky"> (kept together)
    # - Subsequent events: one per <tbody> (free to break)
    tbodies = []
    i = 0
    n = len(raw_rows)

    # Emit header as <thead> so WeasyPrint repeats it on each page break
    if n and raw_rows[0][0] == "header":
        tbodies.append(f"<thead>{raw_rows[0][1]}</thead>")
        i = 1

    while i < n:
        kind, html = raw_rows[i]
        if kind in ("day", "subsection"):
            # Gather banner(s) + first event into a sticky tbody
            group = [html]
            i += 1
            # Consecutive banners (e.g. "Nisan 14 Wednesday" immediately
            # followed by "Gethsemane and Arrest") are all grouped together
            while i < n and raw_rows[i][0] in ("day", "subsection"):
                group.append(raw_rows[i][1])
                i += 1
            # Attach the first event row if present
            if i < n and raw_rows[i][0] == "event":
                group.append(raw_rows[i][1])
                i += 1
            tbodies.append(
                '<tbody class="gp-sticky">' + "".join(group) + "</tbody>"
            )
        else:
            # Standalone event row — its own tbody, free to break
            tbodies.append(f"<tbody>{html}</tbody>")
            i += 1

    rows_html = tbodies

    intro = (
        '<p class="gp-intro">Where each event in the last week is recorded '
        'across the four Gospels. All references NASB.</p>'
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
        + "\n".join(rows_html)
        + '</table>'
    )
    return intro + table_html


# --------------------------------------------------------------------------
# SCRIPTURE REFERENCE INDEX (APPENDIX C)
# --------------------------------------------------------------------------

def build_scripture_index_html():
    """Convert Scripture_Reference_Index.md into indexed HTML entries."""
    src = (BOOK_DIR / "Scripture_Reference_Index.md").read_text(encoding="utf-8")

    entries = []
    for line in src.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("### "):
            # Book heading
            book = line[4:].strip()
            entries.append(f'<h3 class="index-book">{book}</h3>')
        elif line.startswith("- "):
            # Reference entry: `- Genesis 3:15 — Prologue, Epilogue`
            body = line[2:].strip()
            if "\u2014" in body:
                ref, locs = body.split("\u2014", 1)
                entries.append(
                    f'<div class="index-entry">'
                    f'<span class="index-ref">{ref.strip()}</span>'
                    f'<span class="index-chapters">{locs.strip()}</span>'
                    f'</div>'
                )
            else:
                entries.append(f'<div class="index-entry">{body}</div>')
        # Skip # / ## / *intro* lines in the index
    return "\n".join(entries)


# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------

CSS = r"""
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond.ttf') format('truetype');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond-Italic.ttf') format('truetype');
    font-weight: normal;
    font-style: italic;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond.ttf') format('truetype');
    font-weight: bold;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: url('FONT_DIR/EBGaramond-Italic.ttf') format('truetype');
    font-weight: bold;
    font-style: italic;
}

/* === PAGE SETUP ===
   5.5" x 8.5", no bleed.
   Gutter (inside) = 0.75in, Outside = 0.625in
   Top = 0.75in, Bottom = 0.75in
*/

@page {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
}

@page :right {
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

@page :left {
    margin-left: 0.625in;
    margin-right: 0.75in;
    @bottom-left {
        content: counter(page);
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 9pt;
        color: #333;
    }
}

/* Front matter: no page numbers */
@page front-recto {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}
@page front-verso {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
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

/* Part title pages: no page numbers */
@page part-page {
    size: 5.5in 8.5in;
    margin-top: 0.75in;
    margin-bottom: 0.75in;
    margin-left: 0.75in;
    margin-right: 0.625in;
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

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

/* === HALF TITLE PAGE === */
.half-title-page {
    page: front-recto;
    page-break-after: always;
    text-align: center;
    padding-top: 3in;
}
.half-title-page h1 {
    font-size: 18pt;
    font-weight: normal;
    font-variant: small-caps;
    letter-spacing: 0.08em;
    color: #1a1a1a;
}

/* Blank verso after half title */
.blank-verso {
    page: front-verso;
    page-break-after: always;
    visibility: hidden;
}

/* === TITLE PAGE === */
.title-page {
    page: front-recto;
    page-break-after: always;
    text-align: center;
    padding-top: 1.8in;
}
.title-page h1 {
    font-size: 22pt;
    font-weight: bold;
    line-height: 1.2;
    margin: 0 0 0.2in 0;
    color: #1a1a1a;
}
.title-page .book-subtitle {
    font-size: 12pt;
    font-style: italic;
    color: #444;
    margin-bottom: 1.1in;
}
.title-page .author {
    font-size: 14pt;
    margin-top: 0.5in;
    color: #1a1a1a;
}
.title-page .imprint {
    font-size: 10pt;
    font-variant: small-caps;
    letter-spacing: 0.1em;
    color: #555;
    margin-top: 1.1in;
}

/* === COPYRIGHT PAGE === */
.copyright-page {
    page: front-verso;
    page-break-after: always;
    padding-top: 1.8in;
}
.copyright-page p {
    font-size: 8.5pt;
    line-height: 1.45;
    color: #555;
    margin-bottom: 3pt;
    text-align: center;
}

/* === TABLE OF CONTENTS === */
.toc-section {
    page: toc-page;
    break-before: right;
    page-break-after: always;
}
.toc-section h1 {
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0.4in;
    padding-top: 0.5in;
    color: #1a1a1a;
}
.toc-entry {
    font-size: 10.5pt;
    line-height: 1.9;
    color: #333;
    padding-left: 0.15in;
}
.toc-entry .toc-num {
    display: inline;
    margin-right: 0.15in;
}
.toc-entry .toc-title {
    display: inline;
}
.toc-special {
    font-style: italic;
    padding-left: 0;
    margin-top: 0.08in;
    margin-bottom: 0.08in;
}
.toc-backmatter {
    margin-top: 0.25in;
    padding-left: 0;
    font-style: italic;
}
.toc-backmatter + .toc-backmatter {
    margin-top: 0;
}
.toc-part {
    margin-top: 0.22in;
    margin-bottom: 0.08in;
    text-align: center;
}
.toc-part-num {
    font-size: 9pt;
    font-variant: small-caps;
    letter-spacing: 0.08em;
    color: #666;
    display: block;
}
.toc-part-title {
    font-size: 11.5pt;
    font-weight: bold;
    color: #1a1a1a;
    display: block;
}

/* === PART TITLE PAGES === */
.part-page {
    page: part-page;
    break-before: right;
    page-break-after: always;
    text-align: center;
}
.part-page .part-inner {
    padding-top: 3in;
}
.part-page .part-num {
    font-size: 11pt;
    font-variant: small-caps;
    letter-spacing: 0.15em;
    color: #555;
    margin-bottom: 0.3in;
}
.part-page .part-title {
    font-size: 22pt;
    font-weight: bold;
    color: #1a1a1a;
}

/* === CHAPTERS — start on recto === */
.chapter {
    break-before: right;
}

.chapter-header {
    text-align: center;
    margin-bottom: 0.35in;
    padding-top: 0.5in;
}

.chapter-header .chapter-num {
    font-size: 10pt;
    letter-spacing: 0.12em;
    color: #555;
    margin-bottom: 6pt;
    text-transform: uppercase;
}

.chapter-header h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 6pt;
    line-height: 1.2;
}

.chapter-header .chapter-subtitle {
    font-size: 11pt;
    font-style: italic;
    color: #555;
    margin-top: 4pt;
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

/* No indent after headings / dividers / quotes */
.chapter-body h2 + p,
.chapter-body h3 + p,
.chapter-body hr + p,
.chapter-body blockquote + p,
.chapter-body blockquote.scripture + p,
.chapter-body .chart-placeholder + p {
    text-indent: 0;
}

.chapter-body > p:first-child {
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
    break-after: avoid;
    orphans: 3;
    widows: 3;
}

.chapter-body h3 {
    font-size: 11.5pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.22in;
    margin-bottom: 0.1in;
    page-break-after: avoid;
    break-after: avoid;
    orphans: 3;
    widows: 3;
}

/* === SCRIPTURE QUOTES === */
blockquote.scripture {
    margin: 0.15in 0.4in;
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

/* === GENERIC BLOCKQUOTES (non-scripture) === */
blockquote {
    margin: 0.15in 0.4in;
    font-style: italic;
    font-size: 10.5pt;
    line-height: 1.5;
    border: none;
}
blockquote p {
    text-indent: 0 !important;
}

/* === DIVIDERS (from markdown ---) === */
hr {
    border: none;
    text-align: center;
    margin: 0.2in 0;
    height: 0;
}
hr::after {
    content: "\2042";  /* asterism-ish ornament */
    font-size: 11pt;
    color: #888;
    letter-spacing: 0.15em;
}

/* === CHARTS (inline, grayscale) === */
figure.chart {
    margin: 0.25in 0;
    padding: 0;
    page-break-inside: avoid;
    break-inside: avoid;
}
figure.chart .chart-label {
    font-size: 9pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555;
    text-align: center;
    margin: 0 0 3pt 0;
    text-indent: 0 !important;
}
figure.chart .chart-title {
    font-size: 13pt;
    font-weight: bold;
    color: #1a1a1a;
    text-align: center;
    margin: 0 0 0.12in 0;
    text-indent: 0 !important;
    line-height: 1.2;
}
figure.chart .chart-note,
figure.chart figcaption.chart-note {
    font-size: 8.5pt;
    font-style: italic;
    color: #555;
    text-align: center;
    margin: 6pt 0.2in 0 0.2in;
    text-indent: 0 !important;
    line-height: 1.4;
}
figure.chart .chart-subhead {
    font-size: 9.5pt;
    font-weight: bold;
    color: #1a1a1a;
    text-align: center;
    margin: 0.12in 0 4pt 0;
    text-indent: 0 !important;
}
figure.chart .chart-landing {
    font-size: 10.5pt;
    font-weight: bold;
    font-style: italic;
    color: #1a1a1a;
    text-align: center;
    margin: 0.12in 0.2in;
    text-indent: 0 !important;
    line-height: 1.35;
}
figure.chart .chart-body-text {
    font-size: 9pt;
    color: #1a1a1a;
    text-align: justify;
    margin: 6pt 0.2in;
    text-indent: 0 !important;
    line-height: 1.45;
}

/* Generic chart table — used by most inline charts */
table.chart-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
    line-height: 1.35;
    color: #1a1a1a;
    table-layout: fixed;
    margin: 0;
}
table.chart-table th,
table.chart-table td {
    padding: 3.5pt 4pt;
    vertical-align: top;
    border: 0.4pt solid #c8c8c8;
    text-align: left;
}
table.chart-table thead th {
    background: #1a1a1a;
    color: #ffffff;
    font-weight: bold;
    font-size: 8.5pt;
}
table.chart-table tbody tr:nth-child(odd) td {
    background: #ffffff;
}
table.chart-table tbody tr:nth-child(even) td {
    background: #f5f5f5;
}
/* Emphasis rows — dark value for landing / verdict / total */
table.chart-table tbody tr.chart-row-emphasis td {
    background: #555555 !important;
    color: #ffffff;
}
table.chart-table tbody tr.chart-row-emphasis td em {
    color: #f0f0f0;
}

/* Chart A — The Thread (vertical flow) */
ol.chart-thread {
    list-style: none;
    padding: 0 0.3in;
    margin: 0;
    counter-reset: thread;
}
ol.chart-thread li.thread-node {
    position: relative;
    padding: 6pt 0 6pt 0;
    text-align: center;
    border-top: 0.4pt solid #c8c8c8;
}
ol.chart-thread li.thread-node:first-child {
    border-top: none;
}
ol.chart-thread .thread-label {
    display: block;
    font-weight: bold;
    font-size: 10pt;
    color: #1a1a1a;
    margin-bottom: 2pt;
}
ol.chart-thread .thread-text {
    display: block;
    font-size: 9pt;
    font-style: italic;
    color: #333;
    line-height: 1.35;
}

/* Chart 6 — Mark's Next-Day Sequence (vertical timeline) */
ol.chart-timeline {
    list-style: none;
    padding: 0 0.2in;
    margin: 0;
}
ol.chart-timeline li.timeline-phase {
    border-left: 1.5pt solid #555;
    padding: 4pt 0 4pt 10pt;
    margin: 0;
}
ol.chart-timeline .timeline-day {
    font-weight: bold;
    font-size: 10pt;
    color: #1a1a1a;
    margin-bottom: 3pt;
}
ol.chart-timeline .timeline-events {
    list-style: none;
    padding: 0 0 0 6pt;
    margin: 0;
}
ol.chart-timeline .timeline-events li {
    font-size: 9pt;
    color: #333;
    line-height: 1.4;
    margin-bottom: 2pt;
}
ol.chart-timeline li.timeline-transition {
    padding: 3pt 0 3pt 18pt;
    font-size: 8.5pt;
    color: #666;
    border-left: 0.6pt dashed #888;
    margin: 2pt 0;
}

/* Chart 10 — The Longest Day (vertical phase list) */
ol.chart-longest-day {
    list-style: none;
    padding: 0 0.15in;
    margin: 0;
}
ol.chart-longest-day li.longest-phase {
    display: block;
    padding: 5pt 8pt 6pt 8pt;
    margin: 0;
    border-bottom: 0.4pt solid #c8c8c8;
}
ol.chart-longest-day li.longest-phase:first-child {
    border-top: 0.6pt solid #1a1a1a;
}
ol.chart-longest-day li.longest-phase:last-child {
    border-bottom: 0.6pt solid #1a1a1a;
}
ol.chart-longest-day .longest-time {
    font-weight: bold;
    font-size: 10pt;
    color: #1a1a1a;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
ol.chart-longest-day .longest-detail {
    font-size: 8.5pt;
    font-style: italic;
    color: #666;
    margin-bottom: 3pt;
}
ol.chart-longest-day .longest-events {
    list-style: none;
    padding: 0 0 0 10pt;
    margin: 0;
}
ol.chart-longest-day .longest-events li {
    font-size: 9pt;
    color: #1a1a1a;
    line-height: 1.35;
}

/* Chart 12 — Spice Paradox flow */
figure.chart .chart-flow {
    text-align: center;
    margin: 10pt 0.1in 2pt 0.1in;
    line-height: 1.8;
}
figure.chart .chart-flow .flow-step {
    display: inline-block;
    font-size: 8.5pt;
    padding: 2pt 6pt;
    border: 0.5pt solid #888;
    background: #f5f5f5;
    color: #1a1a1a;
    white-space: nowrap;
}
figure.chart .chart-flow .flow-step.flow-emphasis {
    background: #555;
    color: #ffffff;
    border-color: #1a1a1a;
    font-weight: bold;
}
figure.chart .chart-flow .flow-arrow {
    display: inline-block;
    color: #555;
    padding: 0 3pt;
    font-size: 10pt;
}

/* === APPENDIX COMMON === */
.appendix {
    break-before: right;
}
.appendix .appendix-header {
    text-align: center;
    margin-bottom: 0.3in;
    padding-top: 0.5in;
}
.appendix .appendix-label {
    font-size: 10pt;
    letter-spacing: 0.12em;
    color: #555;
    margin-bottom: 6pt;
    text-transform: uppercase;
}
.appendix h1 {
    font-size: 18pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 6pt;
    line-height: 1.2;
}

/* === GOSPEL PARALLEL TABLE (Appendix B) === */
.gp-intro {
    font-style: italic;
    font-size: 9.5pt;
    color: #555;
    text-align: center;
    text-indent: 0 !important;
    margin: 0 0 0.15in 0;
}
table.gospel-parallel {
    width: 100%;
    border-collapse: collapse;
    font-size: 8pt;
    line-height: 1.35;
    color: #1a1a1a;
    table-layout: fixed;
}
table.gospel-parallel .gp-col-event { width: 42%; }
table.gospel-parallel .gp-col-ref   { width: 14.5%; }

table.gospel-parallel th,
table.gospel-parallel td {
    padding: 3.5pt 4pt;
    vertical-align: top;
    border: 0.4pt solid #c8c8c8;
}

/* Header row — near-black background, white text */
table.gospel-parallel tr.gp-header th {
    background: #1a1a1a;
    color: #ffffff;
    font-weight: bold;
    font-size: 8.5pt;
    text-align: left;
}

/* Primary Nisan-day banner — dark gray, white text */
table.gospel-parallel tr.gp-day td {
    background: #555555;
    color: #ffffff;
    font-weight: bold;
    font-size: 8.5pt;
    padding: 4pt 5pt;
}

/* Sub-section banner — light gray, dark italic */
table.gospel-parallel tr.gp-subsection td {
    background: #dddddd;
    color: #1a1a1a;
    font-style: italic;
    font-weight: bold;
    font-size: 8pt;
    padding: 3pt 5pt;
}

/* Keep banner(s) + first event row together across page breaks — prevents
   orphaned banners at the bottom of a page. WeasyPrint honors
   page-break-inside: avoid on tbody elements. */
table.gospel-parallel tbody.gp-sticky {
    page-break-inside: avoid;
    break-inside: avoid;
}

/* Event rows — zebra stripes, bold event name */
table.gospel-parallel tr.gp-event {
    page-break-inside: avoid;
}
table.gospel-parallel tr.gp-event td {
    background: #ffffff;
}
table.gospel-parallel tr.gp-event.gp-event-alt td {
    background: #f5f5f5;
}
table.gospel-parallel td.gp-event-name {
    font-weight: bold;
}
table.gospel-parallel td.gp-ref {
    font-size: 7.5pt;
    color: #333;
    text-align: left;
}

/* === SCRIPTURE INDEX === */
.index-book {
    font-size: 12pt;
    font-weight: bold;
    color: #1a1a1a;
    margin-top: 0.2in;
    margin-bottom: 0.08in;
    page-break-after: avoid;
    break-after: avoid;
}
.index-entry {
    font-size: 10pt;
    line-height: 1.7;
    margin-left: 0.2in;
    color: #333;
    page-break-inside: avoid;
}
.index-ref {
    display: inline;
    margin-right: 0.15in;
}
.index-chapters {
    display: inline;
    font-style: italic;
    font-size: 9.5pt;
    color: #555;
}

/* === PAD PAGE (force even count) === */
.pad-page {
    page: front-verso;
    page-break-before: always;
    visibility: hidden;
}

em { font-style: italic; }
strong { font-weight: bold; }
"""


# --------------------------------------------------------------------------
# FULL HTML ASSEMBLY
# --------------------------------------------------------------------------

def build_full_html(sections_html, toc_html, scripture_index_html, gospel_parallel_html):
    css = CSS.replace("FONT_DIR", str(FONT_DIR))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{css}</style>
</head>
<body>

  <!-- HALF TITLE (p. i, recto) -->
  <div class="half-title-page">
    <h1>{BOOK_TITLE}</h1>
  </div>

  <!-- BLANK VERSO (p. ii) -->
  <div class="blank-verso">&nbsp;</div>

  <!-- TITLE PAGE (p. iii, recto) -->
  <div class="title-page">
    <h1>{BOOK_TITLE}</h1>
    <p class="book-subtitle">{BOOK_SUBTITLE}</p>
    <p class="author">{AUTHOR}</p>
    <p class="imprint">{IMPRINT}</p>
  </div>

  <!-- COPYRIGHT PAGE (p. iv, verso) -->
  <div class="copyright-page">
    <p>{BOOK_TITLE}: {BOOK_SUBTITLE}</p>
    <p>Copyright \u00a9 {COPYRIGHT_YEAR} {AUTHOR}</p>
    <p>All rights reserved.</p>
    <p>&nbsp;</p>
    <p>Published by {IMPRINT}</p>
    <p>noblemind.study</p>
    <p>&nbsp;</p>
    <p>Scripture quotations are taken from the New American Standard Bible\u00ae (NASB),<br>
    Copyright \u00a9 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation.<br>
    Used by permission. All rights reserved. www.lockman.org</p>
    <p>&nbsp;</p>
    <p>No part of this publication may be reproduced, stored in a retrieval system,<br>
    or transmitted in any form or by any means without the prior written<br>
    permission of the author, except as provided by U.S. copyright law.</p>
    <p>&nbsp;</p>
    <p>Printed in the United States of America</p>
  </div>

  <!-- TABLE OF CONTENTS -->
  <div class="toc-section">
    <h1>Contents</h1>
    {toc_html}
  </div>

  <!-- MAIN CONTENT -->
  {sections_html}

  <!-- APPENDIX B: GOSPEL PARALLEL REFERENCE CHART -->
  <section class="appendix gospel-parallel-section">
    <div class="appendix-header">
      <p class="appendix-label">Appendix B</p>
      <h1>Gospel Parallel Reference Chart</h1>
    </div>
    {gospel_parallel_html}
  </section>

  <!-- APPENDIX C: SCRIPTURE REFERENCE INDEX -->
  <section class="appendix scripture-index">
    <div class="appendix-header">
      <p class="appendix-label">Appendix C</p>
      <h1>Scripture Reference Index</h1>
    </div>
    {scripture_index_html}
  </section>

</body>
</html>"""


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main():
    print(f'Generating Lulu interior PDF for "{BOOK_TITLE}"...')
    print(f'  Page size: 5.5" x 8.5"')
    print(f"  Gutter: 0.75in inside, 0.625in outside")
    print(f"  Font: EB Garamond (from {FONT_DIR})")
    print()

    print("Building table of contents...")
    toc_html = build_toc()

    print("Processing sections...")
    section_parts = []
    for section in SECTIONS:
        if section["kind"] == "part":
            print(f"  [PART] {section['title']} — {section['subtitle']}")
        else:
            print(f"  {section['file']}")
        section_parts.append(build_section_html(section))
    sections_html = "\n".join(section_parts)

    print("Building Gospel Parallel Reference Chart (Appendix B)...")
    gospel_parallel_html = build_gospel_parallel_html()

    print("Building Scripture Reference Index (Appendix C)...")
    scripture_index_html = build_scripture_index_html()

    print("Assembling HTML...")
    full_html = build_full_html(
        sections_html, toc_html, scripture_index_html, gospel_parallel_html
    )

    DEBUG_HTML.write_text(full_html, encoding="utf-8")
    print(f"  Debug HTML saved to {DEBUG_HTML}")

    print("Rendering PDF with WeasyPrint (fonts will be embedded)...")
    doc = weasyprint.HTML(string=full_html, base_url=str(BOOK_DIR))
    pdf_doc = doc.render()

    page_count = len(pdf_doc.pages)
    print(f"  Raw page count: {page_count}")

    if page_count % 2 != 0:
        print(f"  Odd page count; adding a blank pad page...")
        full_html_padded = full_html.replace(
            "</body>",
            '<div class="pad-page">&nbsp;</div>\n</body>',
        )
        doc = weasyprint.HTML(string=full_html_padded, base_url=str(BOOK_DIR))
        pdf_doc = doc.render()
        page_count = len(pdf_doc.pages)
        print(f"  Adjusted page count: {page_count}")

    pdf_doc.write_pdf(str(OUTPUT))

    print()
    print(f"PDF saved to {OUTPUT}")
    print(f"  Total pages: {page_count}")
    print(f"  Chapters start on recto (right-hand) pages")
    print(f"  Fonts: EB Garamond (embedded)")
    print("Done.")


if __name__ == "__main__":
    main()
