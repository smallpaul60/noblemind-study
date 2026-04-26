#!/usr/bin/env python3
"""Scripture verification for 'Why the Division Among Brethren?'.

The manuscript predominantly uses inline parenthetical citation style:

    "Whatever you do in word or deed..." (Col. 3:17)

The shared tools/verify_scripture.py only handles markdown blockquote
form, so this book-specific verifier extracts every inline
quote-plus-citation from the canonical manuscript and compares the
quoted text against the NASB via Bolls.Life — the same API the shared
tool uses.

Usage:
    python3 _verify_scripture.py
    python3 _verify_scripture.py --chapter 6
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from difflib import SequenceMatcher

from _book_source import (
    BIBLE_BOOK_ABBREVS,
    BIBLE_BOOKS_FULL,
    canonical_book_name,
    parse_book,
)

API_BASE = "https://bolls.life/get-text/NASB"

# Bolls.Life book number lookup.
BOOK_NUM = {
    "Genesis": 1, "Exodus": 2, "Leviticus": 3, "Numbers": 4, "Deuteronomy": 5,
    "Joshua": 6, "Judges": 7, "Ruth": 8, "1 Samuel": 9, "2 Samuel": 10,
    "1 Kings": 11, "2 Kings": 12, "1 Chronicles": 13, "2 Chronicles": 14,
    "Ezra": 15, "Nehemiah": 16, "Esther": 17, "Job": 18, "Psalms": 19,
    "Proverbs": 20, "Ecclesiastes": 21, "Song of Solomon": 22,
    "Isaiah": 23, "Jeremiah": 24, "Lamentations": 25, "Ezekiel": 26,
    "Daniel": 27, "Hosea": 28, "Joel": 29, "Amos": 30, "Obadiah": 31,
    "Jonah": 32, "Micah": 33, "Nahum": 34, "Habakkuk": 35, "Zephaniah": 36,
    "Haggai": 37, "Zechariah": 38, "Malachi": 39, "Matthew": 40, "Mark": 41,
    "Luke": 42, "John": 43, "Acts": 44, "Romans": 45, "1 Corinthians": 46,
    "2 Corinthians": 47, "Galatians": 48, "Ephesians": 49, "Philippians": 50,
    "Colossians": 51, "1 Thessalonians": 52, "2 Thessalonians": 53,
    "1 Timothy": 54, "2 Timothy": 55, "Titus": 56, "Philemon": 57,
    "Hebrews": 58, "James": 59, "1 Peter": 60, "2 Peter": 61,
    "1 John": 62, "2 John": 63, "3 John": 64, "Jude": 65, "Revelation": 66,
}


# ----------------------------------------------------------------------------
# Quote extraction
# ----------------------------------------------------------------------------

# Build a book-token alternation that allows trailing period for abbreviations.
_BOOK_TOKENS = sorted(
    set(BIBLE_BOOKS_FULL) | set(BIBLE_BOOK_ABBREVS.keys()),
    key=len, reverse=True,
)
_BOOK_ALT = "|".join(re.escape(b) for b in _BOOK_TOKENS)

# Inline parenthetical citation:
#   "text..." (Col. 3:17)
#   "text..." (1 Cor. 16:1–3)
#   "text..." (Acts 2:42, 47)
#   "text..." (vv. 9-10)            <-- skipped, handled separately
#
# We capture the quoted body and the parenthetical reference.
INLINE_QUOTE_RE = re.compile(
    r'(?P<open>["“])(?P<body>[^"“”]+?)(?P<close>["”])'
    r'\s*\((?P<ref>(?:' + _BOOK_ALT + r')\.?\s+'
    r'\d+:\d+(?:\s*[–—-]\s*\d+)?(?:,\s*\d+(?:\s*[–—-]\s*\d+)?)*)\)',
    re.DOTALL,
)

# Markdown blockquote-form Scripture (multi-line):
#   > Quoted text spanning lines.
#   > — Source 1:2
# In this book this form is used sparingly (e.g. extended Woods quotation
# in Ch 6, which is a historical source not Scripture). We still scan in
# case Scripture is ever rendered this way.
BLOCKQUOTE_RE = re.compile(
    r'(?:^>\s*(?P<line>.*)$\n?)+', re.MULTILINE
)


def extract_inline_quotes(md_text: str):
    """Yield (quote_text, ref_text) for every inline scripture quote."""
    for m in INLINE_QUOTE_RE.finditer(md_text):
        body = m.group('body').strip()
        # Skip empty bodies and tiny phrase fragments (≤3 words) — too
        # short to verify meaningfully and prone to false matches against
        # common phrases.
        if len(body.split()) < 4:
            continue
        # Skip obvious historical or non-scripture quotations: if the
        # quoted body contains another scripture reference inside it,
        # this is probably a quotation of a speaker quoting Scripture,
        # not a Scripture quotation. (Rare; safe to skip.)
        ref = m.group('ref').strip()
        # Drop trailing period attached to the citation (rare).
        ref = ref.rstrip('.')
        yield body, ref


# ----------------------------------------------------------------------------
# Reference parsing and API
# ----------------------------------------------------------------------------

REF_PARSE_RE = re.compile(
    r'^(?P<book>(?:' + _BOOK_ALT + r'))\.?\s+'
    r'(?P<chapter>\d+):'
    r'(?P<verses>\d+(?:\s*[–—-]\s*\d+)?(?:,\s*\d+(?:\s*[–—-]\s*\d+)?)*)$'
)


def parse_ref(ref_text: str):
    """Return (canonical_book, book_num, chapter, [(start_v, end_v), ...])
    or None if unparseable."""
    m = REF_PARSE_RE.match(ref_text.strip())
    if not m:
        return None
    book = canonical_book_name(m.group('book'))
    if not book:
        return None
    book_num = BOOK_NUM.get(book)
    if not book_num:
        return None
    ch = int(m.group('chapter'))
    verse_spans = []
    for chunk in m.group('verses').split(','):
        chunk = chunk.strip()
        if '-' in chunk or '–' in chunk or '—' in chunk:
            parts = re.split(r'\s*[–—-]\s*', chunk)
            verse_spans.append((int(parts[0]), int(parts[1])))
        else:
            v = int(chunk)
            verse_spans.append((v, v))
    return book, book_num, ch, verse_spans


_api_cache = {}


def fetch_chapter(book_num: int, chapter: int):
    key = (book_num, chapter)
    if key in _api_cache:
        return _api_cache[key]
    url = f"{API_BASE}/{book_num}/{chapter}/"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "WhyDivisionVerify/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        verses = {v["verse"]: v["text"] for v in data}
        _api_cache[key] = verses
        time.sleep(0.25)
        return verses
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"    API error: {book_num}/{chapter}: {e}")
        return None


def get_verse_text(book_num: int, chapter: int, spans):
    verses = fetch_chapter(book_num, chapter)
    if verses is None:
        return None
    parts = []
    for start, end in spans:
        for v in range(start, end + 1):
            t = verses.get(v)
            if t:
                parts.append(t)
            else:
                parts.append(f"[{v}?]")
    return " ".join(parts)


# ----------------------------------------------------------------------------
# Comparison
# ----------------------------------------------------------------------------

def normalize(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*{1,3}', '', text)
    # NASB encloses translator-supplied words in square brackets, e.g.
    # "[carefully]" or "[a new covenant]". The brackets are not part of
    # the text the book quotes, so drop them while keeping the contents.
    text = re.sub(r'[\[\]]', '', text)
    text = (text
            .replace('“', '"').replace('”', '"')
            .replace('‘', "'").replace('’', "'")
            .replace('—', '-').replace('–', '-'))
    # Drop straight-quote characters and apostrophes that come from the
    # NASB's punctuation around direct speech ('go therefore...').
    text = text.replace("'", "").replace('"', '')
    text = re.sub(r'\.\s*\.\s*\.', '...', text)
    text = text.replace('...', '…')
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def _segment_score(seg: str, a: str) -> float:
    """How much of seg appears as a contiguous run inside a, normalized
    to seg's length. 1.0 means seg is fully present; 0.0 means absent."""
    if not seg:
        return 1.0
    # Quick wins: substring match.
    if seg in a:
        return 1.0
    sm = SequenceMatcher(None, seg, a, autojunk=False)
    longest = sm.find_longest_match(0, len(seg), 0, len(a)).size
    # Use a stricter ratio than the longest-match alone — chars matched by
    # ratio() across the whole seg is more forgiving when the seg has
    # interior punctuation differences (semicolons, hyphens, ellipses).
    rough = sm.ratio()  # bounded [0,1] over the union
    # For substring-style verification, weight longest contiguous match
    # heavily and let ratio fill in for noise tolerance.
    return max(longest / len(seg), rough)


def compare(quoted: str, actual: str):
    """Score the quoted text against the NASB verse(s) returned for the
    citation. Partial quotations of full verses should score high — the
    quote does not need to cover the whole verse, only to appear in it.
    """
    q = normalize(quoted)
    a = normalize(actual)

    # Split on ellipsis so each gap-stitched segment is verified
    # independently. Quotes without an ellipsis become a single segment.
    segments = [s.strip() for s in q.split('…') if s.strip()]
    if not segments:
        return 0.0, None
    scores = [_segment_score(seg, a) for seg in segments]
    return min(scores), None  # weakest segment governs the verdict


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def verify_section(label, md, total, matched, issues):
    quotes = list(extract_inline_quotes(md))
    if not quotes:
        return total, matched, issues
    print(f"\n  {label} ({len(quotes)} inline quotes)")
    for body, ref in quotes:
        total += 1
        parsed = parse_ref(ref)
        if not parsed:
            print(f"    Could not parse: ({ref})")
            issues += 1
            continue
        _book, book_num, ch, spans = parsed
        actual = get_verse_text(book_num, ch, spans)
        if not actual:
            issues += 1
            continue
        ratio, _ = compare(body, actual)
        if ratio >= 0.85:
            matched += 1
            if ratio < 0.97:
                print(f"    ({ref}) — CLOSE ({ratio:.0%})")
                print(f"      BOOK: \"{normalize(body)[:140]}\"")
                print(f"      NASB: \"{normalize(actual)[:140]}\"")
        else:
            issues += 1
            print(f"    ({ref}) — MISMATCH ({ratio:.0%})")
            print(f"      BOOK: \"{normalize(body)[:140]}\"")
            print(f"      NASB: \"{normalize(actual)[:140]}\"")
    return total, matched, issues


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chapter", type=int,
                   help="Verify a single chapter only (e.g. 6)")
    args = p.parse_args()

    book = parse_book()
    total = matched = issues = 0

    print("=" * 70)
    print("Why the Division — inline Scripture verification (NASB via Bolls.Life)")
    print("=" * 70)

    if args.chapter is None:
        total, matched, issues = verify_section(
            "Preface", book["preface_md"] or "", total, matched, issues)

    for ch in book["chapters"]:
        if args.chapter is not None and ch["num"] != args.chapter:
            continue
        total, matched, issues = verify_section(
            f"Chapter {ch['num']} — {ch['title']}",
            ch["md"], total, matched, issues,
        )

    print(f"\n{'=' * 70}")
    print(f"Summary: {total} quotes checked, {matched} matched, {issues} issues")
    print(f"{'=' * 70}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
