#!/usr/bin/env python3
"""Shared parser for 'Why the Division Among Brethren?'

The canonical manuscript lives in a single file, why-the-division-book.md,
with H1 marking Parts (and the book title), H2 marking Preface and the
Chapter headings, and H3 marking subsections inside each chapter. Every
generator (reader PDF, EPUB, Lulu interior, online reader, Scripture
index) imports parse_book() from this module so the split between
canonical content and presentation logic stays clean.

Usage:
    from _book_source import parse_book, md_body_to_html
    book = parse_book()
    for part in book["parts"]:
        for ch in part["chapters"]:
            html = md_body_to_html(ch["md"])
"""

import re
from pathlib import Path

import markdown

BOOK_DIR = Path(__file__).parent
MARKDOWN_FILE = BOOK_DIR / "why-the-division-book.md"

TITLE = "Why the Division Among Brethren?"
SUBTITLE = "The Underlying Issue Between Institutional and Non-Institutional churches of Christ"
AUTHOR = "Paul Hainline"
PUBLISHER = "NobleMind Press"

# Chapter words used for display labels ("Chapter One", "Chapter Two", ...).
CHAPTER_WORDS = [
    "One", "Two", "Three", "Four", "Five", "Six", "Seven",
    "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
]

# Map English Part labels to Roman/Arabic equivalents for downstream use.
PART_NUMBERS = {
    "Part One":   ("I",   1),
    "Part Two":   ("II",  2),
    "Part Three": ("III", 3),
    "Part Four":  ("IV",  4),
}


# ============================================================================
# SCRIPTURE CITATION DETECTION
# ============================================================================

# Full canonical names. Used for index sorting and detection inside prose.
BIBLE_BOOKS_FULL = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
    "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]

# Abbreviation -> canonical full name. The manuscript predominantly uses
# abbreviated forms inside parenthetical citations: "(Col. 3:17)",
# "(1 Cor. 16:1-3)", "(Matt. 28:19)", etc.
BIBLE_BOOK_ABBREVS = {
    "Gen": "Genesis", "Ex": "Exodus", "Exod": "Exodus", "Lev": "Leviticus",
    "Num": "Numbers", "Deut": "Deuteronomy",
    "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth",
    "1 Sam": "1 Samuel", "2 Sam": "2 Samuel",
    "1 Kgs": "1 Kings", "2 Kgs": "2 Kings",
    "1 Chr": "1 Chronicles", "2 Chr": "2 Chronicles",
    "Ezra": "Ezra", "Neh": "Nehemiah", "Est": "Esther",
    "Job": "Job", "Ps": "Psalms", "Psa": "Psalms", "Pss": "Psalms",
    "Prov": "Proverbs", "Eccl": "Ecclesiastes", "Song": "Song of Solomon",
    "Isa": "Isaiah", "Jer": "Jeremiah", "Lam": "Lamentations",
    "Ezek": "Ezekiel", "Dan": "Daniel",
    "Hos": "Hosea", "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah",
    "Jonah": "Jonah", "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk",
    "Zeph": "Zephaniah", "Hag": "Haggai", "Zech": "Zechariah", "Mal": "Malachi",
    "Matt": "Matthew", "Mt": "Matthew", "Mark": "Mark", "Mk": "Mark",
    "Luke": "Luke", "Lk": "Luke", "John": "John", "Jn": "John",
    "Acts": "Acts",
    "Rom": "Romans",
    "1 Cor": "1 Corinthians", "2 Cor": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians",
    "Col": "Colossians",
    "1 Thess": "1 Thessalonians", "2 Thess": "2 Thessalonians",
    "1 Tim": "1 Timothy", "2 Tim": "2 Timothy",
    "Titus": "Titus", "Philem": "Philemon",
    "Heb": "Hebrews", "James": "James", "Jas": "James",
    "1 Pet": "1 Peter", "2 Pet": "2 Peter",
    "1 John": "1 John", "2 John": "2 John", "3 John": "3 John",
    "Jude": "Jude", "Rev": "Revelation",
}

# Canonical book order, used by the Scripture index.
CANONICAL_BOOK_ORDER = {
    name: i for i, name in enumerate([
        b for b in BIBLE_BOOKS_FULL
        if b != "Psalm"  # de-duplicate; index uses "Psalms"
    ])
}


def canonical_book_name(token: str):
    """Return the canonical full book name for either a full or abbreviated
    token, or None if not recognized."""
    token = token.strip().rstrip('.').strip()
    if token in BIBLE_BOOKS_FULL:
        return "Psalms" if token == "Psalm" else token
    return BIBLE_BOOK_ABBREVS.get(token)


# Build a regex that matches every form a book name appears in inside the
# manuscript. We sort longest first so "1 Cor" matches before "Cor",
# and so multi-word names ("Song of Solomon") match before single-word ones.
_BOOK_TOKENS = sorted(
    set(BIBLE_BOOKS_FULL) | set(BIBLE_BOOK_ABBREVS.keys()),
    key=len, reverse=True,
)
_BOOK_TOKEN_PAT = "|".join(re.escape(b) for b in _BOOK_TOKENS)

# Reference body: chapter:verse(-verse)? optionally chained with commas
# ("Acts 9:36, 39") or semicolons handled separately.
_REF_BODY = (
    r'\d+(?::\d+(?:\s*[–—-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[–—-]\s*\d+)?)*)?'
)
# Full single reference: book + body, optionally followed by ".".
SCRIPTURE_REF_PAT = (
    r'(?:' + _BOOK_TOKEN_PAT + r')\.?\s+' + _REF_BODY
)

# Matches an entire markdown paragraph that IS a Scripture quote in
# parenthetical-citation form:
#     "Whatever you do in word or deed..." (Col. 3:17)
# The detection is conservative: the whole paragraph must be the quote +
# the citation, with at most a trailing period. This guards against
# false-positive promotion of quoted phrases that happen to end in a
# Scripture reference inside a longer paragraph.
SCRIPTURE_PARA_RE = re.compile(
    r'^\s*["“”](.+)["“”]\s+\(('
    + SCRIPTURE_REF_PAT + r')\)\.?\s*$',
    re.DOTALL,
)

# After markdown conversion: lift the trailing citation inside a <blockquote>
# into a <cite>.
CITE_IN_BLOCKQUOTE_EMDASH_RE = re.compile(
    r'<blockquote>\s*<p>(.*?)\s*[—–-]\s*('
    + SCRIPTURE_REF_PAT + r')\.?\s*</p>\s*</blockquote>',
    re.DOTALL,
)
CITE_IN_BLOCKQUOTE_PAREN_RE = re.compile(
    r'<blockquote>\s*<p>(.*?)\s*\(('
    + SCRIPTURE_REF_PAT + r')\)\.?\s*</p>\s*</blockquote>',
    re.DOTALL,
)


def promote_scripture_paragraphs(md_text: str) -> str:
    """Wrap whole-paragraph Scripture quotes in markdown blockquote syntax
    so the rendered HTML lifts them out of the body type.

    Applies only when the entire paragraph IS the quote + citation.
    Inline parenthetical references inside longer prose are left alone.
    """
    paragraphs = re.split(r'\n\s*\n', md_text)
    out = []
    for para in paragraphs:
        stripped = para.strip()
        if stripped and SCRIPTURE_PARA_RE.match(stripped):
            out.append("> " + stripped)
        else:
            out.append(para)
    return "\n\n".join(out)


def _clean_quote(quote: str) -> str:
    quote = quote.strip()
    quote = re.sub(r'</?em>', '', quote)
    quote = re.sub(
        r'^(&ldquo;|&rdquo;|&lsquo;|&rsquo;|[“”"\'])+',
        '', quote,
    )
    quote = re.sub(
        r'(&ldquo;|&rdquo;|&lsquo;|&rsquo;|[“”"\'])+$',
        '', quote,
    )
    return quote.strip()


_MULTI_P_BQ_RE = re.compile(
    r'<blockquote>\s*((?:<p>(?:(?!</blockquote>).)*?</p>\s*){2,})</blockquote>',
    re.DOTALL,
)
_P_SPLIT_RE = re.compile(r'(<p>(?:(?!</p>).)*?</p>)', re.DOTALL)


def _split_multi_paragraph_blockquotes(html: str) -> str:
    def _sub(m):
        inner = m.group(1)
        paragraphs = [p for p in _P_SPLIT_RE.findall(inner) if p.strip()]
        return "\n".join(f'<blockquote>{p}</blockquote>' for p in paragraphs)
    return _MULTI_P_BQ_RE.sub(_sub, html)


def lift_citation_to_cite(html: str) -> str:
    """Rewrite <blockquote><p>"quote" — Ref</p></blockquote> into a
    styled scripture block with the citation in a <cite>."""
    html = _split_multi_paragraph_blockquotes(html)

    def _sub(m):
        quote = _clean_quote(m.group(1))
        cite = m.group(2).strip()
        return (
            f'<blockquote class="scripture">'
            f'<p>&ldquo;{quote}&rdquo;</p>'
            f'<cite>&mdash; {cite}</cite>'
            f'</blockquote>'
        )
    html = CITE_IN_BLOCKQUOTE_EMDASH_RE.sub(_sub, html)
    html = CITE_IN_BLOCKQUOTE_PAREN_RE.sub(_sub, html)
    return html


def md_body_to_html(md_text: str) -> str:
    """Convert a body-markdown fragment to HTML with Scripture blocks styled."""
    md_text = promote_scripture_paragraphs(md_text)
    html = markdown.markdown(md_text, extensions=['smarty', 'tables'])
    html = lift_citation_to_cite(html)
    return html


# ============================================================================
# SCRIPTURE INDEX EXTRACTION
# ============================================================================

# Single-reference matcher with capture groups for the index. We do NOT use
# SCRIPTURE_REF_PAT directly because the index needs structured output
# (book, chapter, verse-range), and the comma-chained verse list is split
# into individual entries.
#
# verses group accepts either:
#   simple: "12"
#   range:  "12-15"
#   cross-chapter: "22-6:4"   (renders as "5:22–6:4" using the chapter)
SINGLE_REF_RE = re.compile(
    r'(' + _BOOK_TOKEN_PAT + r')\.?\s+'
    r'(\d+):(\d+(?:\s*[–—-]\s*\d+(?::\d+)?)?)'
)
# Whole-chapter reference (no verse part): "Acts 6", "1 Corinthians 11".
WHOLE_CHAPTER_RE = re.compile(
    r'(?<![:\d])(' + _BOOK_TOKEN_PAT + r')\.?\s+(\d+)(?![:\d])'
)


def _normalize_verse_range(s: str) -> str:
    s = re.sub(r'\s*[–—-]\s*', '–', s)
    return s


def extract_scripture_references(text: str):
    """Return a list of (canonical_book, chapter, verse_range_or_None) tuples
    for every Scripture reference found in the text."""
    refs = []
    seen_spans = []  # to avoid double-counting whole-chapter refs that
                     # actually belonged to a verse-bearing match.
    for m in SINGLE_REF_RE.finditer(text):
        book = canonical_book_name(m.group(1))
        if not book:
            continue
        ch = int(m.group(2))
        verses = _normalize_verse_range(m.group(3))
        refs.append((book, ch, verses))
        seen_spans.append((m.start(), m.end()))

    for m in WHOLE_CHAPTER_RE.finditer(text):
        # Skip if this overlaps a verse-bearing match already captured.
        if any(a <= m.start() < b for a, b in seen_spans):
            continue
        book = canonical_book_name(m.group(1))
        if not book:
            continue
        # Don't capture standalone numbers like "Chapter 6" (where Chapter
        # is the immediately preceding non-Bible word). The token regex
        # already excludes "Chapter", so this guard is mostly redundant —
        # but guard against rare cases like "Romans 7" inside a phrase.
        ch = int(m.group(2))
        refs.append((book, ch, None))
    return refs


# ============================================================================
# STRUCTURAL PARSER
# ============================================================================

HEADING_RE = re.compile(r'^(#{1,3})\s+(.+?)\s*$')
PART_HEAD_RE = re.compile(
    r'^Part\s+(One|Two|Three|Four)\s*[—–-]\s*(.+)$'
)
CHAPTER_HEAD_RE = re.compile(
    r'^Chapter\s+(\d+)\s*[—–-]\s*(.+)$'
)


def _split_sections(raw: str):
    """Split the manuscript into [(level, heading, body), ...].
    H3 stays inside its parent body as raw markdown.
    """
    sections = []
    current = None

    for line in raw.split('\n'):
        m = HEADING_RE.match(line)
        # Treat H3 as body — let it flow inside the chapter.
        if m and len(m.group(1)) <= 2:
            if current is not None:
                sections.append(current)
            level = len(m.group(1))
            heading = m.group(2).strip()
            current = {"level": level, "heading": heading, "body": []}
        else:
            if current is None:
                current = {"level": 0, "heading": "__PREAMBLE__", "body": []}
            current["body"].append(line)

    if current is not None:
        sections.append(current)
    return sections


def _clean_body(lines):
    body = "\n".join(lines)
    body = re.sub(r'\A\s*(?:---+\s*\n)+', '', body)
    body = re.sub(r'(?:\n\s*---+\s*)+\s*\Z', '', body)
    return body.strip()


def parse_book():
    """Return the manuscript as structured sections.

    Returns:
        {
          "title":       "Why the Division Among Brethren?",
          "subtitle":    "...",
          "author":      "Paul Hainline",
          "publisher":   "NobleMind Press",
          "preface_md":  "...",
          "parts": [
            {
              "label":    "Part One",
              "roman":    "I",
              "number":   1,
              "title":    "Background",
              "intro_md": "...",
              "chapters": [
                {"num": 1, "label": "Chapter One",
                 "title": "Why This Matters", "md": "..."},
                ...
              ],
            },
            ...
          ],
          "chapters":    [...],   # flat list across all parts
        }
    """
    raw = MARKDOWN_FILE.read_text(encoding='utf-8')
    sections = _split_sections(raw)

    preface_md = None
    parts = []
    current_part = None

    for s in sections:
        h = s["heading"]
        body = _clean_body(s["body"])

        if h == TITLE:
            continue
        if h == "__PREAMBLE__":
            continue
        if h == "Contents":
            continue
        if h == "Preface":
            preface_md = body
            continue

        pm = PART_HEAD_RE.match(h)
        if pm:
            label = f"Part {pm.group(1)}"
            roman, number = PART_NUMBERS[label]
            current_part = {
                "label": label,
                "roman": roman,
                "number": number,
                "title": pm.group(2).strip(),
                "intro_md": body,
                "chapters": [],
            }
            parts.append(current_part)
            continue

        cm = CHAPTER_HEAD_RE.match(h)
        if cm:
            num = int(cm.group(1))
            title = cm.group(2).strip()
            if not (1 <= num <= len(CHAPTER_WORDS)):
                raise ValueError(f"Chapter number {num} out of range")
            word_label = CHAPTER_WORDS[num - 1]
            if current_part is None:
                raise ValueError(
                    f"Chapter '{h}' appeared before any Part heading"
                )
            current_part["chapters"].append({
                "num": num,
                "label": f"Chapter {word_label}",
                "title": title,
                "md": body,
            })
            continue

        raise ValueError(f"Unrecognized section heading: {h!r}")

    all_chapters = []
    for p in parts:
        all_chapters.extend(p["chapters"])

    return {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "author": AUTHOR,
        "publisher": PUBLISHER,
        "preface_md": preface_md,
        "parts": parts,
        "chapters": all_chapters,
    }


# ============================================================================
# SELF-TEST
# ============================================================================

if __name__ == "__main__":
    book = parse_book()
    print(f"Title:    {book['title']}")
    print(f"Subtitle: {book['subtitle']}")
    print(f"Author:   {book['author']}")
    print(f"Preface:  {len(book['preface_md'] or '')} chars")
    print(f"Parts:    {len(book['parts'])}")
    for p in book["parts"]:
        print(f"  {p['label']} ({p['roman']}): {p['title']}  "
              f"(intro {len(p['intro_md'])} chars, "
              f"{len(p['chapters'])} chapters)")
        for ch in p["chapters"]:
            print(f"    Ch {ch['num']:>2} ({ch['label']}): {ch['title']}  "
                  f"({len(ch['md']):,} chars)")
    print(f"Chapters total: {len(book['chapters'])}")

    # Light sanity test on the Scripture index extractor.
    sample_refs = []
    for ch in book["chapters"]:
        sample_refs.extend(extract_scripture_references(ch["md"]))
    sample_refs.extend(extract_scripture_references(book["preface_md"] or ""))
    print(f"\nScripture references detected: {len(sample_refs)}")
    unique_books = sorted({r[0] for r in sample_refs},
                          key=lambda b: CANONICAL_BOOK_ORDER.get(b, 99))
    print(f"Books referenced: {len(unique_books)}")
    print("  " + ", ".join(unique_books))
