#!/usr/bin/env python3
"""Shared parser for 'Why Do You Delay?'

The canonical manuscript lives in a single file, why-do-you-delay-book.md,
with H1/H2 headings marking Parts, Preface, Chapters, and the Epilogue.
Every generator (reader PDF, EPUB, Lulu interior, online reader) imports
parse_book() from this module so the split between canonical content and
presentation logic stays clean.

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
MARKDOWN_FILE = BOOK_DIR / "why-do-you-delay-book.md"

TITLE = "Why Do You Delay?"
SUBTITLE = "Baptism, Salvation, and What the Bible Actually Says"
AUTHOR = "Paul Hainline"

# Chapter words used for display labels ("Chapter One", "Chapter Two", ...).
CHAPTER_WORDS = [
    "One", "Two", "Three", "Four", "Five", "Six", "Seven",
    "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
]


# ============================================================================
# SCRIPTURE CITATION DETECTION
# ============================================================================

BIBLE_BOOKS = [
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
_BOOK_ALT = "|".join(re.escape(b) for b in sorted(BIBLE_BOOKS, key=len, reverse=True))

# Matches a single bible reference like "Matthew 28:19" or "Matthew 28:19–20"
# or "Acts 22:16" — optionally inside a chapter or verse range.
REF_PAT = (
    r'(?:' + _BOOK_ALT + r')\s+\d+(?::\d+(?:\s*[–—-]\s*\d+)?)?'
)

# Matches an entire markdown paragraph that IS a Scripture blockquote.
# In this manuscript scripture is written in one of two shapes:
#
#   (A) Explicit two-line markdown blockquote — the default:
#         > *"Go therefore and make disciples..."*
#         > — Matthew 28:19–20
#
#   (B) One-paragraph inline citation — legacy CTB-style, kept for safety:
#         "Our bones are dried up..." (Ezekiel 37:11).
#
# Shape (A) is already a blockquote so markdown handles it; we only lift
# the citation into a <cite>. Shape (B) is handled by promote_scripture_paragraphs
# which wraps it in `> ` first.
SCRIPTURE_PARA_RE = re.compile(
    r'^\s*["“”](.+)["“”]\s+\(('
    + REF_PAT + r')\)\.?\s*$'
)

# After markdown conversion: lift the trailing citation inside a <blockquote>
# into a <cite>. Matches both citation styles (em-dash-prefixed and
# parenthetical) that may appear in the rendered HTML.
CITE_IN_BLOCKQUOTE_EMDASH_RE = re.compile(
    r'<blockquote>\s*<p>(.*?)\s*[—–-]\s*('
    + REF_PAT + r')\.?\s*</p>\s*</blockquote>',
    re.DOTALL,
)
CITE_IN_BLOCKQUOTE_PAREN_RE = re.compile(
    r'<blockquote>\s*<p>(.*?)\s*\(('
    + REF_PAT + r')\)\.?\s*</p>\s*</blockquote>',
    re.DOTALL,
)


def promote_scripture_paragraphs(md_text):
    """Wrap Shape-B scripture paragraphs in markdown blockquote syntax."""
    paragraphs = re.split(r'\n\s*\n', md_text)
    out = []
    for para in paragraphs:
        stripped = para.strip()
        if stripped and SCRIPTURE_PARA_RE.match(stripped):
            out.append("> " + stripped)
        else:
            out.append(para)
    return "\n\n".join(out)


def _clean_quote(quote):
    """Strip surrounding smart/straight quotes and ALL <em> tags from
    a citation's quoted body before re-rendering.

    We strip every <em> and </em> (rather than only a matched outer pair)
    because python-markdown renders nested `*...**bold**...*` as raggedly
    open/close/open <em> runs. A leaked un-closed <em> propagates italics
    into the rest of the rendered document. The enclosing
    blockquote.scripture CSS is already italic, so removing the inner
    <em> markers loses nothing visually — and it removes the leak.

    <strong> tags are preserved — bold emphasis inside a scripture quote
    is meaningful and survives regardless of italic state.
    """
    quote = quote.strip()
    # Kill every <em> / </em> — see docstring for why.
    quote = re.sub(r'</?em>', '', quote)
    # Strip common quote characters from both ends
    quote = re.sub(
        r'^(&ldquo;|&rdquo;|&lsquo;|&rsquo;|[“”"\'])+',
        '', quote,
    )
    quote = re.sub(
        r'(&ldquo;|&rdquo;|&lsquo;|&rsquo;|[“”"\'])+$',
        '', quote,
    )
    return quote.strip()


# Splits a multi-paragraph <blockquote> into one-paragraph blockquotes so
# each scripture + citation pair can be lifted independently.  Handles
# the case where two adjacent `> ...\n> — Ref` pairs in the source were
# merged by python-markdown into one <blockquote> with two <p> children.
#
# The inner <p>...</p> uses a negative-lookahead tempered match so `.*?`
# cannot gobble past a `</blockquote>` — without that guard the regex
# greedily spans adjacent blockquotes plus the body paragraphs between
# them, wrapping regular prose in a blockquote (the bug that was here
# before).
_MULTI_P_BQ_RE = re.compile(
    r'<blockquote>\s*((?:<p>(?:(?!</blockquote>).)*?</p>\s*){2,})</blockquote>',
    re.DOTALL,
)
_P_SPLIT_RE = re.compile(r'(<p>(?:(?!</p>).)*?</p>)', re.DOTALL)


def _split_multi_paragraph_blockquotes(html):
    def _sub(m):
        inner = m.group(1)
        paragraphs = [p for p in _P_SPLIT_RE.findall(inner) if p.strip()]
        return "\n".join(f'<blockquote>{p}</blockquote>' for p in paragraphs)
    return _MULTI_P_BQ_RE.sub(_sub, html)


def lift_citation_to_cite(html):
    """Rewrite <blockquote><p>"quote" — Ref</p></blockquote> into a
    styled scripture block with the citation in a <cite>."""
    # If markdown merged adjacent scripture quotes into a single
    # multi-paragraph blockquote, split them so each can be lifted.
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


def md_body_to_html(md_text):
    """Convert a body-markdown fragment to HTML with Scripture blocks styled."""
    md_text = promote_scripture_paragraphs(md_text)
    html = markdown.markdown(md_text, extensions=['smarty', 'tables'])
    html = lift_citation_to_cite(html)
    return html


# ============================================================================
# STRUCTURAL PARSER
# ============================================================================

HEADING_RE = re.compile(r'^(#{1,2})\s+(.+?)\s*$')
# Match Part headings like "Part One — Title" with em-dash, en-dash, or hyphen
PART_HEAD_RE = re.compile(
    r'^Part\s+(\w+)\s*[—–-]\s*(.+)$'
)
# Match Chapter headings like "Chapter 1 — Title"
CHAPTER_HEAD_RE = re.compile(
    r'^Chapter\s+(\d+)\s*[—–-]\s*(.+)$'
)
# Match Epilogue headings like "Epilogue — Why Do You Delay?"
EPILOGUE_HEAD_RE = re.compile(
    r'^Epilogue(?:\s*[—–-]\s*(.+))?$'
)


def _split_sections(raw):
    """Split the manuscript into [(level, heading, body), ...].
    Level is 1 for `#` and 2 for `##`. Deeper headings stay inside
    their parent section body."""
    sections = []
    current = None

    for line in raw.split('\n'):
        m = HEADING_RE.match(line)
        if m:
            if current is not None:
                sections.append(current)
            level = len(m.group(1))
            heading = m.group(2).strip()
            current = {"level": level, "heading": heading, "body": []}
        else:
            if current is None:
                # Preamble before any heading — stash under a sentinel
                current = {"level": 0, "heading": "__PREAMBLE__", "body": []}
            current["body"].append(line)

    if current is not None:
        sections.append(current)

    return sections


def _clean_body(lines):
    """Join lines and strip leading/trailing `---` separators + whitespace."""
    body = "\n".join(lines)
    # Remove a leading "---" (possibly with surrounding whitespace)
    body = re.sub(r'\A\s*(?:---+\s*\n)+', '', body)
    # Remove a trailing "---"
    body = re.sub(r'(?:\n\s*---+\s*)+\s*\Z', '', body)
    return body.strip()


def parse_book():
    """Return the manuscript as structured sections.

    Returns:
        {
          "title":       "Why Do You Delay?",
          "subtitle":    "Baptism, Salvation, and What the Bible Actually Says",
          "author":      "Paul Hainline",
          "preface_md":  "...",
          "parts": [
            {
              "label":    "Part One",
              "title":    "What the Lord and His Apostles Taught",
              "intro_md": "...",  # text between the Part heading and first chapter
              "chapters": [
                {
                  "num":   1,
                  "label": "Chapter One",
                  "title": "The Command",
                  "md":    "...",  # body markdown (sub-headings and all)
                },
                ...
              ],
            },
            ...
          ],
          "chapters":     [ ... ],   # flat list across all parts
          "epilogue_md":  "...",
          "epilogue_title": "Why Do You Delay?",
        }
    """
    raw = MARKDOWN_FILE.read_text(encoding='utf-8')
    sections = _split_sections(raw)

    preface_md = None
    parts = []
    current_part = None
    epilogue_md = None
    epilogue_title = None

    for s in sections:
        h = s["heading"]
        body = _clean_body(s["body"])

        # Book title H1 — skip
        if h == TITLE:
            continue
        # Preamble before headings — skip (subtitle + first rule)
        if h == "__PREAMBLE__":
            continue
        # Contents page — skip; we generate TOCs ourselves
        if h == "Contents":
            continue

        if h == "Preface":
            preface_md = body
            continue

        pm = PART_HEAD_RE.match(h)
        if pm:
            current_part = {
                "label": f"Part {pm.group(1).strip()}",
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

        em = EPILOGUE_HEAD_RE.match(h)
        if em:
            epilogue_md = body
            epilogue_title = em.group(1).strip() if em.group(1) else "Epilogue"
            continue

        # Any other heading we don't recognize — warn and skip.
        # This catches typos in the manuscript early.
        raise ValueError(f"Unrecognized section heading: {h!r}")

    # Flat list of chapters for convenience
    all_chapters = []
    for p in parts:
        all_chapters.extend(p["chapters"])

    return {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "author": AUTHOR,
        "preface_md": preface_md,
        "parts": parts,
        "chapters": all_chapters,
        "epilogue_md": epilogue_md,
        "epilogue_title": epilogue_title,
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
        print(f"  {p['label']}: {p['title']}  "
              f"(intro {len(p['intro_md'])} chars, "
              f"{len(p['chapters'])} chapters)")
        for ch in p["chapters"]:
            print(f"    Ch {ch['num']} ({ch['label']}): {ch['title']}  "
                  f"({len(ch['md'])} chars)")
    print(f"Chapters total: {len(book['chapters'])}")
    print(f"Epilogue: {book['epilogue_title']}  ({len(book['epilogue_md'] or '')} chars)")
