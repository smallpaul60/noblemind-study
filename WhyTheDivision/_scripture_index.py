#!/usr/bin/env python3
"""Build the Scripture Index appendix for 'Why the Division Among Brethren?'.

The index is generated from the canonical manuscript at build time —
pulled into the Lulu interior, the reader PDF, and the EPUB. Page
numbers are layout-dependent and are filled in by the consumer at the
point of typesetting; this module provides the canonical-order
structure with chapter numbers as the locator (for plain-text formats)
or with placeholder page locators (for typeset formats).

Usage:
    from _scripture_index import build_index, render_index_markdown
    idx = build_index()
    md = render_index_markdown(idx)
"""

import re
from collections import defaultdict

from _book_source import (
    CANONICAL_BOOK_ORDER,
    extract_scripture_references,
    parse_book,
)


def _verse_sort_key(entry):
    """Sort entries within a Bible book by chapter, then by starting verse."""
    chapter = entry["chapter"]
    verses = entry["verses"]
    if not verses:
        return (chapter, 0, 0)
    # "9-10" -> start=9; "9" -> start=9.
    m = re.match(r'(\d+)', verses)
    start = int(m.group(1)) if m else 0
    end_m = re.search(r'(\d+)\s*$', verses)
    end = int(end_m.group(1)) if end_m else start
    return (chapter, start, end)


def _format_locator(verses):
    if not verses:
        return ""
    # Use en-dash for verse ranges in display.
    return ":" + verses.replace('-', '–')


def build_index():
    """Walk the manuscript and return the index structured for rendering.

    Returns:
        [
          {
            "book": "Acts",
            "entries": [
              {"chapter": 2, "verses": "44–45",
               "locations": [(book_chapter_num, ch_title), ...]},
              ...
            ],
          },
          ...
        ]
    Books are returned in canonical Bible order.
    """
    book = parse_book()

    # ref_key (canonical_book, chapter, verses) -> set of chapter nums
    locations = defaultdict(set)
    chapter_titles = {}

    sections = []
    if book["preface_md"]:
        sections.append((0, "Preface", book["preface_md"]))
    for ch in book["chapters"]:
        chapter_titles[ch["num"]] = ch["title"]
        sections.append((ch["num"], ch["title"], ch["md"]))

    for ch_num, ch_title, md in sections:
        for canonical_book, chapter, verses in extract_scripture_references(md):
            key = (canonical_book, chapter, verses or "")
            locations[key].add(ch_num)

    # Group by Bible book in canonical order.
    by_book = defaultdict(list)
    for (canonical_book, chapter, verses), ch_nums in locations.items():
        by_book[canonical_book].append({
            "chapter": chapter,
            "verses": verses,
            "locations": sorted(ch_nums),
        })

    out = []
    ordered_books = sorted(
        by_book.keys(),
        key=lambda b: CANONICAL_BOOK_ORDER.get(b, 99),
    )
    for canonical_book in ordered_books:
        entries = sorted(by_book[canonical_book], key=_verse_sort_key)
        # Coalesce duplicate (chapter, verses) entries (already done by set;
        # this is cosmetic if anything slipped through).
        out.append({"book": canonical_book, "entries": entries})

    return out


def _format_locations(ch_nums):
    """Render a chapter-number list as a human-readable locator.
    "Preface" is encoded as 0; render that as "Pref"."""
    parts = []
    for n in ch_nums:
        parts.append("Pref" if n == 0 else f"Ch. {n}")
    return ", ".join(parts)


def render_index_markdown(idx):
    """Render the index as markdown headed by Bible book names."""
    lines = ["# Scripture Index", ""]
    lines.append(
        "References are listed in the canonical order of the Bible, "
        "with the chapter(s) of this booklet in which each reference "
        "appears. Use the Table of Contents to find each chapter's "
        "starting page."
    )
    lines.append("")
    for group in idx:
        lines.append(f"## {group['book']}")
        lines.append("")
        for e in group["entries"]:
            ref = f"{group['book']} {e['chapter']}{_format_locator(e['verses'])}"
            locs = _format_locations(e["locations"])
            lines.append(f"- **{ref}** — {locs}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    idx = build_index()
    total_refs = sum(len(g["entries"]) for g in idx)
    total_books = len(idx)
    print(f"Scripture Index — {total_refs} unique references across "
          f"{total_books} Bible books\n")
    for group in idx:
        print(f"  {group['book']}: {len(group['entries'])} entries")
    print()
    print(render_index_markdown(idx))
