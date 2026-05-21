"""Shared book-source module for The Love God Calls Us To.

Parses the Markdown chapter files into clean HTML body content and
provides the metadata, chapter ordering, and dedication selection that
every output format (HTML, PDF, EPUB, Lulu interior) needs.

Two dedications are supported:
  - GENERAL (default): widely-applicable, no class context
  - CLASS (--class flag on generator scripts): for the gift edition
    given to students working through 1 Corinthians 13 in a class
"""

import re
from pathlib import Path
import markdown as md_lib

BOOK_DIR = Path(__file__).parent

# Book metadata
TITLE = "The Love God Calls Us To"
SUBTITLE = "Walking Out 1 Corinthians 13"
AUTHOR = "Paul Hainline"
PUBLISHER = "NobleMind Press"
YEAR = "2026"
LANGUAGE = "en"
DESCRIPTION = (
    "A walk through 1 Corinthians 13 — the love chapter — taken not "
    "as a wedding text but as the apostle Paul's diagnostic for a "
    "fractured first-century church. Fifteen attributes of love, "
    "addressed across fourteen chapters, with the Greek named where it "
    "helps, the Corinthian failures named where they sharpen the "
    "modern reader's seeing, and the love itself set forth as the "
    "eternal nature of God Himself, into which every believer is being "
    "called."
)
ANCHOR_VERSE = (
    "“But now faith, hope, love, abide these three; but the greatest "
    "of these is love.”"
)
ANCHOR_CITE = "— 1 Corinthians 13:13 (NASB)"

# Front matter, chapter, and back matter ordering.
# Each entry: (md_filename, label, title, part)
#   - label: "Chapter N" / "Preface" / "Appendix A" / "Inscription &
#     Dedication" / None (for intro/conclusion which use the title)
#   - title: chapter title as it appears in the TOC
#   - part: section heading above the chapter in the TOC, or None
FRONT_MATTER = [
    # Dedication filename is selected at load time based on edition flag.
    ("__DEDICATION__", "Inscription & Dedication", "Inscription & Dedication", None),
    ("The_Love_God_Calls_Us_To_FM_Preface.md", "Preface", "Before You Begin", None),
]

CHAPTERS = [
    ("The_Love_God_Calls_Us_To_Ch01_More_Excellent_Way.md",
        "Chapter 1", "The More Excellent Way", None),
    ("The_Love_God_Calls_Us_To_Ch02_Love_Is_Patient.md",
        "Chapter 2", "Love Is Patient", None),
    ("The_Love_God_Calls_Us_To_Ch03_Love_Is_Kind.md",
        "Chapter 3", "Love Is Kind", None),
    ("The_Love_God_Calls_Us_To_Ch04_Love_Is_Not_Jealous.md",
        "Chapter 4", "Love Is Not Jealous", None),
    ("The_Love_God_Calls_Us_To_Ch05_Love_Does_Not_Brag.md",
        "Chapter 5", "Love Does Not Brag", None),
    ("The_Love_God_Calls_Us_To_Ch06_Love_Is_Not_Arrogant.md",
        "Chapter 6", "Love Is Not Arrogant", None),
    ("The_Love_God_Calls_Us_To_Ch07_Love_Does_Not_Act_Unbecomingly.md",
        "Chapter 7", "Love Does Not Act Unbecomingly", None),
    ("The_Love_God_Calls_Us_To_Ch08_Love_Does_Not_Seek_Its_Own.md",
        "Chapter 8", "Love Does Not Seek Its Own", None),
    ("The_Love_God_Calls_Us_To_Ch09_Love_Is_Not_Provoked.md",
        "Chapter 9", "Love Is Not Provoked", None),
    ("The_Love_God_Calls_Us_To_Ch10_Wrong_Suffered.md",
        "Chapter 10", "Love Does Not Take Into Account a Wrong Suffered", None),
    ("The_Love_God_Calls_Us_To_Ch11_Love_Does_Not_Rejoice_In_Unrighteousness_But_Rejoices_With_The_Truth.md",
        "Chapter 11", "Love Does Not Rejoice in Unrighteousness, but Rejoices With the Truth", None),
    ("The_Love_God_Calls_Us_To_Ch12_Love_Bears_All_Things.md",
        "Chapter 12", "Love Bears All Things", None),
    ("The_Love_God_Calls_Us_To_Ch13_Love_Believes_All_Things.md",
        "Chapter 13", "Love Believes All Things", None),
    ("The_Love_God_Calls_Us_To_Ch14_Love_Hopes_All_Things.md",
        "Chapter 14", "Love Hopes All Things", None),
    ("The_Love_God_Calls_Us_To_Ch15_Love_Endures_All_Things.md",
        "Chapter 15", "Love Endures All Things", None),
    ("The_Love_God_Calls_Us_To_Ch16_Love_Never_Fails.md",
        "Chapter 16", "Love Never Fails", None),
]

BACK_MATTER = [
    ("The_Love_God_Calls_Us_To_AppA_Obey_The_Gospel.md",
        "Appendix A", "What It Means to Obey the Gospel", None),
    ("__SCRIPTURE_INDEX__",
        "Scripture Index", "Scripture Index", None),
]

# All sections in publication order
ALL_SECTIONS = FRONT_MATTER + CHAPTERS + BACK_MATTER


def get_dedication_filename(class_edition: bool = False) -> str:
    if class_edition:
        return "The_Love_God_Calls_Us_To_FM_Inscription_Dedication_class.md"
    return "The_Love_God_Calls_Us_To_FM_Inscription_Dedication.md"


def resolve_filename(filename: str, class_edition: bool = False) -> str:
    if filename == "__DEDICATION__":
        return get_dedication_filename(class_edition)
    return filename


def section_slug(filename: str, label: str) -> str:
    """URL-safe slug for a section, used in HTML chapter filenames."""
    if filename == "__DEDICATION__":
        return "dedication"
    m = re.search(r"_(?:Ch(\d+)|FM|AppA)", filename)
    if filename.endswith("Preface.md"):
        return "preface"
    if "AppA" in filename:
        return "appendix-a"
    if "Inscription" in filename:
        return "dedication"
    if m and m.group(1):
        return f"chapter-{int(m.group(1)):02d}"
    return filename.replace(".md", "").lower()


# --- Markdown parsing ---


def _markdown_to_html(md_text: str) -> str:
    """Convert markdown body text to HTML using the markdown library."""
    return md_lib.markdown(
        md_text,
        extensions=["extra", "smarty"],
    )


def _is_scripture_blockquote(html_str: str) -> bool:
    """Recognize a scripture-style blockquote: a > line followed by an
    em-dash citation line. The markdown library merges both into a single
    <blockquote> containing two <p> tags; the second usually starts with
    em-dash + book name."""
    return bool(re.search(r"<p>\s*[—–\-]\s*\d?\s*[A-Z][a-z]+", html_str))


def _process_blockquote(html_str: str) -> str:
    """Convert a markdown-generated <blockquote> with cited Scripture
    into the project's <blockquote class="scripture"> + <cite> format.

    Handles two markdown shapes:
      A) Multi-paragraph blockquote (separated by blank `>` lines) —
         markdown produces multiple <p> tags inside the blockquote.
      B) Single-paragraph blockquote (consecutive `>` lines, no blank
         separator) — markdown joins them into one <p> with an
         internal newline. The em-dash citation sits at the end of
         that single <p>.
    """
    p_matches = re.findall(r"<p>(.*?)</p>", html_str, flags=re.DOTALL)

    # --- Case A: multi-paragraph blockquote ---
    if len(p_matches) >= 2:
        cite_text = None
        quote_lines = []
        for p in p_matches:
            stripped = p.strip()
            if (cite_text is None
                    and re.match(r"^[—–\-]\s*\d?\s*[A-Z]", stripped)):
                cite_text = re.sub(r"^[—–\-]\s*", "", stripped)
            else:
                quote_lines.append(p)
        if not cite_text:
            return html_str
        quote_html = " ".join(f"<p>{q}</p>" for q in quote_lines)
        return f'<blockquote class="scripture">{quote_html}<cite>{cite_text}</cite></blockquote>'

    # --- Case B: single <p> with an internal em-dash citation ---
    if len(p_matches) == 1:
        p_content = p_matches[0]
        # Look for newline + em-dash + book-name pattern
        m = re.search(
            r"\n\s*[—–\-]\s*(\d?\s*[A-Z][a-z].+)\s*$",
            p_content,
            flags=re.DOTALL,
        )
        if m:
            quote_text = p_content[:m.start()].rstrip()
            cite_text = m.group(1).strip()
            return f'<blockquote class="scripture"><p>{quote_text}</p><cite>{cite_text}</cite></blockquote>'

    return html_str


def parse_chapter_md(md_path: Path) -> dict:
    """Parse a chapter markdown file into structured pieces.

    Returns a dict with:
      title          - the chapter title (from the ## heading)
      label          - "Chapter N" / "Preface" / etc. (from ## heading)
      epigraph_html  - first scripture blockquote in HTML (or None)
      body_html      - the rest of the body as HTML
    """
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Drop the # book-title H1
    body_lines = []
    h2_seen = False
    label = None
    title = None
    for ln in lines:
        if ln.startswith("# ") and not h2_seen:
            continue  # book title H1
        if ln.startswith("## ") and not h2_seen:
            h2_seen = True
            heading = ln[3:].strip()
            # Heading may be "Chapter N — Title" or "Preface" or "Appendix A — Title"
            m = re.match(r"^(.+?)\s*—\s*(.+)$", heading)
            if m:
                label = m.group(1).strip()
                title = m.group(2).strip()
            else:
                label = heading
                title = heading
            continue
        if h2_seen:
            body_lines.append(ln)

    body_md = "\n".join(body_lines).strip()

    # Strip any standalone *italic layout note* paragraphs that appear
    # in FM files (these are author notes for the layout, not content)
    body_md = re.sub(
        r"^\s*\*Layout note:.*?\*\s*\n",
        "",
        body_md,
        flags=re.MULTILINE | re.DOTALL,
    )
    body_md = re.sub(
        r"^\s*\*This is the class edition.*?\*\s*\n",
        "",
        body_md,
        flags=re.MULTILINE | re.DOTALL,
    )

    body_html = _markdown_to_html(body_md)

    # Post-process: convert cite-style blockquotes to .scripture+<cite>
    def _repl(m):
        return _process_blockquote(m.group(0))
    body_html = re.sub(r"<blockquote>.*?</blockquote>", _repl, body_html, flags=re.DOTALL)

    # Extract first scripture blockquote as epigraph only when it is the
    # literal first thing in the body. Otherwise (e.g. Appendix A, where
    # the first scripture quote sits several paragraphs deep), leave it
    # in place.
    epigraph_html = None
    m = re.match(r'\s*(<blockquote class="scripture">.*?</blockquote>)', body_html, flags=re.DOTALL)
    if m:
        epigraph_html = m.group(1)
        body_html = body_html[m.end():].strip()

    # Convert <hr /> dividers (from --- in markdown) to .divider divs
    body_html = re.sub(
        r"<hr\s*/?>",
        '<div class="divider">*&emsp;*&emsp;*</div>',
        body_html,
    )

    # Convert ### THINK headings to a reflection block: the H3 plus the
    # paragraph that immediately follows becomes a styled reflection
    # section.
    body_html = re.sub(
        r'<h3>THINK</h3>\s*<p>',
        '<section class="reflection"><div class="reflection-header"><h3>THINK</h3></div><div class="reflection-body"><p class="reflection-question"><span class="q-text">',
        body_html,
        count=1,
    )
    # Close the reflection block at the end of the body if it was opened
    if '<section class="reflection">' in body_html:
        body_html = body_html.rstrip()
        if body_html.endswith('</p>'):
            body_html = body_html[:-len('</p>')] + '</span></p></div></section>'

    return {
        "label": label,
        "title": title,
        "epigraph_html": epigraph_html,
        "body_html": body_html,
    }


BIBLE_BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalm", "Proverbs",
    "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
    "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]

SCRIPTURE_RE = re.compile(
    r'\b('
    r'Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|'
    r'1\s*Samuel|2\s*Samuel|1\s*Kings|2\s*Kings|1\s*Chronicles|2\s*Chronicles|'
    r'Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|Ecclesiastes|Song\s*of\s*Solomon|'
    r'Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|'
    r'Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|'
    r'Matthew|Mark|Luke|John|Acts|Romans|'
    r'1\s*Corinthians|2\s*Corinthians|Galatians|Ephesians|Philippians|Colossians|'
    r'1\s*Thessalonians|2\s*Thessalonians|1\s*Timothy|2\s*Timothy|Titus|Philemon|'
    r'Hebrews|James|1\s*Peter|2\s*Peter|1\s*John|2\s*John|3\s*John|Jude|Revelation'
    r')\s+'
    r'(\d+(?::\d+(?:\s*[-–]\s*\d+)*)?(?:\s*[-–]\s*\d+(?::\d+)?)?)',
    re.IGNORECASE,
)


def _canonicalize_book_name(raw: str) -> str:
    """Normalize a captured book name to its canonical form."""
    normalized = re.sub(r'\s+', ' ', raw.strip())
    # Title-case-friendly normalization for canonical lookup
    lower = normalized.lower().replace('  ', ' ')
    for book in BIBLE_BOOK_ORDER + ["Psalms"]:
        if lower == book.lower():
            return "Psalm" if book == "Psalms" else book
    # Last resort: just title-case it
    return normalized


def _extract_scripture_refs_from_text(text: str) -> list:
    """Return a list of (canonical_book, ref_string) tuples found in text."""
    refs = []
    for m in SCRIPTURE_RE.finditer(text):
        book = _canonicalize_book_name(m.group(1))
        verse_part = re.sub(r'\s+', '', m.group(2))
        full_ref = f"{book} {verse_part}"
        # Tidy any en-dashes back to en-dash glyph for display
        full_ref = full_ref.replace('-', '–')
        refs.append((book, full_ref))
    return refs


def _verse_sort_key(ref: str) -> tuple:
    """Sort by chapter then starting verse so 4:7 comes before 4:18.
    Pulls the chapter:verse from the END of the ref so leading book
    numbers (1 Corinthians, 2 Peter, etc.) don't poison the sort."""
    m = re.search(r'(\d+)(?::(\d+))?(?:[-–]\d+(?::\d+)?)?$', ref)
    if not m:
        return (0, 0)
    chapter = int(m.group(1))
    verse = int(m.group(2)) if m.group(2) else 0
    return (chapter, verse)


def build_scripture_index_section(sections: list) -> dict:
    """Build a Scripture Index section dict from already-loaded sections.

    Scans every section's body_html (and epigraph) for Bible references,
    groups them by book in canonical order, lists where each reference
    appears (Preface / Chapter N / Appendix A), and returns a section
    dict with the same shape as a parsed chapter."""
    from collections import defaultdict
    ref_locations = defaultdict(set)

    def label_for(section):
        meta = section.get("label_meta", "")
        if meta == "Inscription & Dedication":
            return "Dedication"
        return meta

    for section in sections:
        if section.get("filename") == "__SCRIPTURE_INDEX__":
            continue
        # Combine epigraph + body for ref scanning
        combined = (section.get("epigraph_html") or "") + " " + \
                   (section.get("body_html") or "")
        # Strip HTML tags to plain text for clean matching
        plain = re.sub(r'<[^>]+>', ' ', combined)
        plain = re.sub(r'&[a-zA-Z]+;', ' ', plain)
        plain = re.sub(r'\s+', ' ', plain)
        for book, full_ref in _extract_scripture_refs_from_text(plain):
            ref_locations[(book, full_ref)].add(label_for(section))

    # Sort: by canonical book order, then by chapter/verse within book
    book_index = {b: i for i, b in enumerate(BIBLE_BOOK_ORDER)}
    sorted_keys = sorted(
        ref_locations.keys(),
        key=lambda k: (book_index.get(k[0], 999), _verse_sort_key(k[1])),
    )

    # Build HTML grouped by book
    parts = []
    current_book = None
    for book, ref in sorted_keys:
        if book != current_book:
            current_book = book
            parts.append(
                f'<h2 class="si-book">{book}</h2>'
            )
        locations = sorted(
            ref_locations[(book, ref)],
            key=lambda L: (
                0 if L == "Dedication"
                else 1 if L == "Preface"
                else 2 if L.startswith("Chapter")
                else 3,
                int(re.search(r'\d+', L).group()) if re.search(r'\d+', L) else 0
            ),
        )
        loc_str = ", ".join(locations)
        parts.append(
            f'<p class="si-entry">'
            f'<span class="si-ref">{ref}</span>'
            f'<span class="si-locations">{loc_str}</span>'
            f'</p>'
        )

    intro = (
        '<p class="si-intro">Every Scripture reference cited in the book, '
        'in canonical order, with the section(s) where it appears. The '
        'main passage of the book — 1 Corinthians 13 — is referenced in '
        'almost every chapter and is not listed exhaustively below; '
        'individual verses within it (13:4, 13:5, 13:6, 13:7, 13:8&#x2013;13) '
        'are listed where the discussion centers on them.</p>'
    )

    body_html = (
        '<section class="chapter scripture-index">'
        '<div class="chapter-body">'
        + intro
        + "\n".join(parts)
        + '</div></section>'
    )

    return {
        "label": "Scripture Index",
        "title": "Scripture Index",
        "epigraph_html": "",
        "body_html": body_html,
        "filename": "__SCRIPTURE_INDEX__",
        "slug": "scripture-index",
        "label_meta": "Scripture Index",
        "title_meta": "Scripture Index",
        "part": None,
    }


def load_all_sections(class_edition: bool = False) -> list:
    """Return a list of parsed sections in publication order.

    Each item is a dict with the keys from parse_chapter_md PLUS:
      filename  - the md filename used
      slug      - URL-safe slug
      label_meta - the section's listing label from ALL_SECTIONS
      title_meta - the title as recorded in ALL_SECTIONS (may differ
                   slightly from the parsed title — meta wins for TOC)
      part      - the part heading (or None)

    Special handling: the __SCRIPTURE_INDEX__ sentinel triggers a
    dynamically-built index section based on Scripture references in
    all previously-loaded sections.
    """
    out = []
    for meta_filename, meta_label, meta_title, meta_part in ALL_SECTIONS:
        if meta_filename == "__SCRIPTURE_INDEX__":
            # Build the index from sections loaded so far
            index_section = build_scripture_index_section(out)
            out.append(index_section)
            continue
        actual = resolve_filename(meta_filename, class_edition)
        md_path = BOOK_DIR / actual
        if not md_path.exists():
            raise FileNotFoundError(f"Missing source file: {md_path}")
        parsed = parse_chapter_md(md_path)
        parsed["filename"] = actual
        parsed["slug"] = section_slug(meta_filename, meta_label)
        parsed["label_meta"] = meta_label
        parsed["title_meta"] = meta_title
        parsed["part"] = meta_part
        out.append(parsed)
    return out
