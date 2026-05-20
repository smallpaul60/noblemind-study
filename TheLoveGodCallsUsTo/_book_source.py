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
    "addressed one chapter at a time, with the Greek named where it "
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
    into the project's <blockquote class="scripture"> + <cite> format."""
    soup_text = html_str
    # Pull all <p> children of the blockquote
    p_matches = re.findall(r"<p>(.*?)</p>", html_str, flags=re.DOTALL)
    if len(p_matches) < 2:
        return html_str  # not a cite-style blockquote, leave it alone

    # The last <p> starting with an em-dash is the citation
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

    # Extract first scripture blockquote as epigraph (it sits right under the H2)
    epigraph_html = None
    m = re.search(r'(<blockquote class="scripture">.*?</blockquote>)', body_html, flags=re.DOTALL)
    if m:
        epigraph_html = m.group(1)
        body_html = body_html.replace(m.group(1), "", 1).strip()

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


def load_all_sections(class_edition: bool = False) -> list:
    """Return a list of parsed sections in publication order.

    Each item is a dict with the keys from parse_chapter_md PLUS:
      filename  - the md filename used
      slug      - URL-safe slug
      label_meta - the section's listing label from ALL_SECTIONS
      title_meta - the title as recorded in ALL_SECTIONS (may differ
                   slightly from the parsed title — meta wins for TOC)
      part      - the part heading (or None)
    """
    out = []
    for meta_filename, meta_label, meta_title, meta_part in ALL_SECTIONS:
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
