#!/usr/bin/env python3
"""Verify Scripture quotations in NobleMind Press books against the NASB text.

Scans HTML chapter files for scripture blockquotes, extracts the quoted text
and citation reference, fetches the actual NASB text from the Bolls.Life API,
and reports any differences.

Usage:
    python3 verify_scripture.py                    # verify all books
    python3 verify_scripture.py ANewAndLivingWay   # verify one book
    python3 verify_scripture.py --book BridgeMoments --chapter 3  # one chapter
"""

import os
import re
import sys
import json
import time
import html as html_mod
import argparse
from pathlib import Path
from difflib import SequenceMatcher
import urllib.request
import urllib.error

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

# Bolls.Life API
API_BASE = "https://bolls.life/get-text/NASB"

# Book name to Bolls.Life book number mapping
BIBLE_BOOKS = {
    "genesis": 1, "gen": 1, "ge": 1,
    "exodus": 2, "exod": 2, "exo": 2, "ex": 2,
    "leviticus": 3, "lev": 3, "le": 3,
    "numbers": 4, "num": 4, "nu": 4,
    "deuteronomy": 5, "deut": 5, "deu": 5, "dt": 5,
    "joshua": 6, "josh": 6, "jos": 6,
    "judges": 7, "judg": 7, "jdg": 7,
    "ruth": 8, "rut": 8, "ru": 8,
    "1 samuel": 9, "1samuel": 9, "1 sam": 9, "1sam": 9,
    "2 samuel": 10, "2samuel": 10, "2 sam": 10, "2sam": 10,
    "1 kings": 11, "1kings": 11, "1 kgs": 11, "1kgs": 11,
    "2 kings": 12, "2kings": 12, "2 kgs": 12, "2kgs": 12,
    "1 chronicles": 13, "1chronicles": 13, "1 chr": 13, "1chr": 13,
    "2 chronicles": 14, "2chronicles": 14, "2 chr": 14, "2chr": 14,
    "ezra": 15, "ezr": 15,
    "nehemiah": 16, "neh": 16, "ne": 16,
    "esther": 17, "est": 17, "esth": 17,
    "job": 18,
    "psalms": 19, "psalm": 19, "psa": 19, "ps": 19,
    "proverbs": 20, "prov": 20, "pro": 20, "pr": 20,
    "ecclesiastes": 21, "eccl": 21, "ecc": 21, "eccles": 21,
    "song of solomon": 22, "song": 22, "sos": 22, "song of songs": 22,
    "isaiah": 23, "isa": 23, "is": 23,
    "jeremiah": 24, "jer": 24, "je": 24,
    "lamentations": 25, "lam": 25, "la": 25,
    "ezekiel": 26, "ezek": 26, "eze": 26,
    "daniel": 27, "dan": 27, "da": 27,
    "hosea": 28, "hos": 28, "ho": 28,
    "joel": 29, "joe": 29,
    "amos": 30, "amo": 30, "am": 30,
    "obadiah": 31, "obad": 31, "ob": 31,
    "jonah": 32, "jon": 32,
    "micah": 33, "mic": 33, "mi": 33,
    "nahum": 34, "nah": 34, "na": 34,
    "habakkuk": 35, "hab": 35,
    "zephaniah": 36, "zeph": 36, "zep": 36,
    "haggai": 37, "hag": 37, "hg": 37,
    "zechariah": 38, "zech": 38, "zec": 38,
    "malachi": 39, "mal": 39,
    "matthew": 40, "matt": 40, "mat": 40, "mt": 40,
    "mark": 41, "mrk": 41, "mk": 41, "mar": 41,
    "luke": 42, "luk": 42, "lk": 42,
    "john": 43, "joh": 43, "jn": 43,
    "acts": 44, "act": 44, "ac": 44,
    "romans": 45, "rom": 45, "ro": 45,
    "1 corinthians": 46, "1corinthians": 46, "1 cor": 46, "1cor": 46,
    "2 corinthians": 47, "2corinthians": 47, "2 cor": 47, "2cor": 47,
    "galatians": 48, "gal": 48, "ga": 48,
    "ephesians": 49, "eph": 49, "ep": 49,
    "philippians": 50, "phil": 50, "php": 50,
    "colossians": 51, "col": 51,
    "1 thessalonians": 52, "1thessalonians": 52, "1 thess": 52, "1thess": 52, "1 th": 52,
    "2 thessalonians": 53, "2thessalonians": 53, "2 thess": 53, "2thess": 53, "2 th": 53,
    "1 timothy": 54, "1timothy": 54, "1 tim": 54, "1tim": 54,
    "2 timothy": 55, "2timothy": 55, "2 tim": 55, "2tim": 55,
    "titus": 56, "tit": 56,
    "philemon": 57, "phm": 57, "philem": 57,
    "hebrews": 58, "heb": 58,
    "james": 59, "jas": 59, "jam": 59,
    "1 peter": 60, "1peter": 60, "1 pet": 60, "1pet": 60, "1 pe": 60,
    "2 peter": 61, "2peter": 61, "2 pet": 61, "2pet": 61, "2 pe": 61,
    "1 john": 62, "1john": 62, "1 jn": 62, "1jn": 62,
    "2 john": 63, "2john": 63, "2 jn": 63, "2jn": 63,
    "3 john": 64, "3john": 64, "3 jn": 64, "3jn": 64,
    "jude": 65, "jud": 65,
    "revelation": 66, "rev": 66, "re": 66, "apocalypse": 66,
}

# Books to scan — directories containing chapter HTML files
BOOK_DIRS = [
    "ANewAndLivingWay",
    "BridgeMoments",
    "FromTheBeginning",
    "ChangeTheMind_ChangeTheMan",
    "OneDayCloserToHome",
    "StrengthAndDignity",
    "TheCharacterNoOneCouldInvent",
    "TheGodWhoShowedUp",
    "ThroughTheValley",
    "YourNameMeansEverything",
]

# Cache for API responses to avoid redundant calls
_api_cache = {}


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    return text


def normalize_text(text):
    """Normalize text for comparison: strip quotes, punctuation variance, whitespace."""
    text = strip_html(text)
    # Strip markdown bold/italic markers
    text = re.sub(r'\*{1,3}', '', text)
    # Decode common HTML entities
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('&ldquo;', '"').replace('&rdquo;', '"')
    text = text.replace('&lsquo;', "'").replace('&rsquo;', "'")
    text = text.replace('&mdash;', '—').replace('&ndash;', '–')
    text = text.replace('&amp;', '&')
    text = text.replace('&hellip;', '…')
    # Remove surrounding quotes
    text = text.strip()
    text = text.strip('""\u201c\u201d')
    text = text.strip()
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Normalize ellipses and trailing punctuation for comparison
    text = text.replace('. . .', '…').replace('...', '…')
    return text.strip()


def parse_reference(ref_text):
    """Parse a scripture reference like 'Romans 12:1-2' or '1 John 3:16-18'.

    Returns (book_num, chapter, start_verse, end_verse) or None.
    """
    ref_text = strip_html(ref_text).strip()
    # Remove leading dash/mdash and translation markers
    ref_text = ref_text.lstrip('—–- ')
    ref_text = re.sub(r'\s*\((?:NASB|KJV|ESV|NIV|NLT|NKJV|LSB)\)\s*$', '', ref_text)
    ref_text = re.sub(r',?\s*(?:NASB|KJV|ESV|NIV|NLT|NKJV|LSB)\s*$', '', ref_text)
    ref_text = ref_text.strip()

    # Match patterns like "Romans 12:1-2", "1 John 3:16", "Psalm 23:4"
    # Also handle "Romans 12:1–2" with en-dash, and "Psalm 22:22, 24" with comma verses
    # For comma-separated verses like "22:22, 24", just use the range from first to last
    ref_text = re.sub(r':(\d+),\s*(\d+)$', r':\1-\2', ref_text)
    # Handle "22:1, 3-4" style — use full range
    ref_text = re.sub(r':(\d+),\s*(\d+)\s*[–\-]\s*(\d+)$', r':\1-\3', ref_text)
    m = re.match(
        r'^(\d?\s*[A-Za-z][A-Za-z\s]+?)\s+(\d+):(\d+)(?:\s*[–\-]\s*(\d+))?$',
        ref_text
    )
    if not m:
        # Try chapter-only reference like "Psalm 23"
        m2 = re.match(r'^(\d?\s*[A-Za-z][A-Za-z\s]+?)\s+(\d+)$', ref_text)
        if m2:
            book_name = m2.group(1).strip().lower()
            chapter = int(m2.group(2))
            book_num = BIBLE_BOOKS.get(book_name)
            if book_num:
                return (book_num, chapter, None, None)
        return None

    book_name = m.group(1).strip().lower()
    chapter = int(m.group(2))
    start_verse = int(m.group(3))
    end_verse = int(m.group(4)) if m.group(4) else start_verse

    book_num = BIBLE_BOOKS.get(book_name)
    if not book_num:
        # Try without trailing 's' (e.g., "Psalms" -> "psalm")
        book_num = BIBLE_BOOKS.get(book_name.rstrip('s'))
    if not book_num:
        return None

    return (book_num, chapter, start_verse, end_verse)


def fetch_nasb_text(book_num, chapter, start_verse, end_verse):
    """Fetch NASB text from Bolls.Life API. Returns combined verse text."""
    cache_key = (book_num, chapter)
    if cache_key not in _api_cache:
        url = f"{API_BASE}/{book_num}/{chapter}/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NobleMindVerify/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            _api_cache[cache_key] = {v['verse']: v['text'] for v in data}
            time.sleep(0.3)  # Be polite to the API
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            print(f"    API ERROR fetching {book_num}/{chapter}: {e}")
            return None

    verses = _api_cache[cache_key]

    if start_verse is None:
        # Whole chapter requested
        parts = [strip_html(verses[v]) for v in sorted(verses.keys())]
    else:
        parts = []
        for v in range(start_verse, end_verse + 1):
            if v in verses:
                parts.append(strip_html(verses[v]))
            else:
                parts.append(f"[verse {v} not found]")

    return ' '.join(parts).strip()


def extract_scripture_quotes(content, filepath):
    """Extract all scripture blockquotes from an HTML or Markdown file.

    Returns list of (quoted_text, reference_text, line_number) tuples.
    """
    quotes = []

    if filepath.suffix == '.md':
        return extract_scripture_quotes_md(content, filepath)

    # HTML: <blockquote class="scripture">...<p>text</p>...<cite>ref</cite>...</blockquote>
    bq_pattern = re.compile(
        r'<blockquote\s+class="scripture">(.*?)</blockquote>',
        re.DOTALL
    )

    for bq_match in bq_pattern.finditer(content):
        bq_content = bq_match.group(1)
        line_num = content[:bq_match.start()].count('\n') + 1

        p_texts = re.findall(r'<p>(.*?)</p>', bq_content, re.DOTALL)
        cite_match = re.search(r'<cite>(.*?)</cite>', bq_content, re.DOTALL)

        if p_texts and cite_match:
            quote_text = ' '.join(p_texts)
            ref_text = cite_match.group(1)
            quotes.append((quote_text, ref_text, line_num))

    return quotes


def extract_scripture_quotes_md(content, filepath):
    """Extract scripture blockquotes from Markdown files.

    Looks for patterns like:
        > "quoted text"
        > — Reference 1:2

    or multi-line:
        > "quoted text
        > continued text"
        > — Reference 1:2-3
    """
    quotes = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for blockquote lines starting with >
        if line.startswith('>'):
            bq_lines = []
            start_line = i + 1  # 1-indexed

            # Collect all consecutive > lines
            while i < len(lines) and lines[i].strip().startswith('>'):
                bq_line = lines[i].strip()[1:].strip()  # Remove '>'
                if bq_line:
                    bq_lines.append(bq_line)
                i += 1

            # Separate quote text from citation
            quote_parts = []
            ref_text = None

            # First, check if any line contains both quote and citation on the same line
            # e.g.: *"quoted text"* — **Genesis 1:1, NASB**
            expanded_lines = []
            for bl in bq_lines:
                # Split on em-dash that separates quote from citation
                split_match = re.split(r'\s*[—–]\s*(?=\*{0,2}\d?\s*[A-Za-z])', bl, maxsplit=1)
                if len(split_match) == 2 and split_match[0].strip():
                    expanded_lines.append(split_match[0].strip())
                    expanded_lines.append('— ' + split_match[1].strip())
                else:
                    expanded_lines.append(bl)

            for bl in expanded_lines:
                # Strip markdown bold/italic markers for detection
                bl_stripped = re.sub(r'\*{1,2}', '', bl).strip()
                # Citation line starts with — or - followed by a book name
                if re.match(r'^[—–\-]\s*\d?\s*[A-Za-z]', bl_stripped):
                    ref_text = bl_stripped
                elif bl_stripped.startswith('— ') or bl_stripped.startswith('– '):
                    ref_text = bl_stripped
                else:
                    quote_parts.append(bl)

            if quote_parts and ref_text:
                quote_text = ' '.join(quote_parts)
                quotes.append((quote_text, ref_text, start_line))
        else:
            i += 1

    return quotes


def compare_texts(quoted, actual):
    """Compare quoted text against actual NASB text.

    Returns (similarity_ratio, differences_description).
    """
    q = normalize_text(quoted)
    a = normalize_text(actual)

    # Check if the quote is a subset (partial quote with ellipsis)
    # Many quotes omit parts with "..."
    ratio = SequenceMatcher(None, q.lower(), a.lower()).ratio()

    if q.lower() == a.lower():
        return (1.0, None)

    # Build a readable diff
    diffs = []
    s = SequenceMatcher(None, q, a)
    for op, i1, i2, j1, j2 in s.get_opcodes():
        if op == 'equal':
            continue
        elif op == 'replace':
            diffs.append(f'  BOOK: "{q[i1:i2]}"')
            diffs.append(f'  NASB: "{a[j1:j2]}"')
        elif op == 'insert':
            diffs.append(f'  MISSING from book: "{a[j1:j2]}"')
        elif op == 'delete':
            diffs.append(f'  EXTRA in book: "{q[i1:i2]}"')

    return (ratio, '\n'.join(diffs) if diffs else None)


def scan_book(book_dir, chapter_filter=None):
    """Scan all chapter files in a book directory and verify scripture quotes."""
    book_path = PROJECT_DIR / book_dir
    if not book_path.exists():
        print(f"  Directory not found: {book_dir}")
        return 0, 0, 0

    # Find chapter files — HTML first, then Markdown
    chapter_files = sorted(book_path.glob("chapter-*.html"))
    if not chapter_files:
        chapter_files = sorted(book_path.glob("chapter*.html"))
    if not chapter_files:
        # Try markdown files with various naming patterns
        chapter_files = sorted(book_path.glob("*Chapter*.md"))
        if not chapter_files:
            chapter_files = sorted(book_path.glob("*_Ch[0-9]*.md"))
        if not chapter_files:
            chapter_files = sorted(book_path.glob("*_Ch*.md"))
        # Also include Introduction.md
        for extra_md in sorted(book_path.glob("*Introduction.md")):
            if extra_md not in chapter_files:
                chapter_files.insert(0, extra_md)

    # Also check introduction, conclusion, etc. (HTML)
    for extra in ["introduction.html", "conclusion.html", "authors-note.html", "foreword.html"]:
        extra_path = book_path / extra
        if extra_path.exists() and extra_path not in chapter_files:
            chapter_files.insert(0, extra_path)

    if chapter_filter is not None:
        chapter_files = [f for f in chapter_files
                         if f"chapter-{chapter_filter:02d}" in f.name.lower()
                         or f"chapter{chapter_filter}" in f.name.lower()
                         or f"_ch{chapter_filter}." in f.name.lower()
                         or f"_ch{chapter_filter:02d}." in f.name.lower()]

    total = 0
    matched = 0
    issues = 0

    for chapter_file in chapter_files:
        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        quotes = extract_scripture_quotes(content, chapter_file)
        if not quotes:
            continue

        print(f"\n  {chapter_file.name} ({len(quotes)} quotes)")

        for quote_text, ref_text, line_num in quotes:
            total += 1
            parsed = parse_reference(ref_text)

            if parsed is None:
                print(f"    Line {line_num}: Could not parse reference: {strip_html(ref_text)}")
                issues += 1
                continue

            book_num, chapter, start_verse, end_verse = parsed

            if start_verse is None:
                print(f"    Line {line_num}: {strip_html(ref_text)} — whole chapter ref, skipping")
                continue

            nasb_text = fetch_nasb_text(book_num, chapter, start_verse, end_verse)
            if nasb_text is None:
                print(f"    Line {line_num}: {strip_html(ref_text)} — API fetch failed")
                issues += 1
                continue

            ratio, diffs = compare_texts(quote_text, nasb_text)

            if ratio >= 0.98:
                matched += 1
                # Still show if not perfect
                if ratio < 1.0:
                    print(f"    Line {line_num}: {strip_html(ref_text)} — OK (minor variance, {ratio:.0%})")
            elif ratio >= 0.85:
                matched += 1
                print(f"    Line {line_num}: {strip_html(ref_text)} — CLOSE ({ratio:.0%})")
                if diffs:
                    print(diffs)
                issues += 1
            else:
                print(f"    Line {line_num}: {strip_html(ref_text)} — MISMATCH ({ratio:.0%})")
                if diffs:
                    print(diffs)
                print(f"      BOOK: \"{normalize_text(quote_text)[:120]}...\"")
                print(f"      NASB: \"{normalize_text(nasb_text)[:120]}...\"")
                issues += 1

    return total, matched, issues


def main():
    parser = argparse.ArgumentParser(description="Verify scripture quotes against NASB")
    parser.add_argument("book", nargs="?", help="Book directory to verify (default: all)")
    parser.add_argument("--chapter", type=int, help="Specific chapter number to verify")
    args = parser.parse_args()

    books = [args.book] if args.book else BOOK_DIRS

    grand_total = 0
    grand_matched = 0
    grand_issues = 0

    print("=" * 60)
    print("NobleMind Press — Scripture Verification Tool")
    print("Comparing quoted text against NASB (via Bolls.Life API)")
    print("=" * 60)

    for book in books:
        print(f"\n{'─' * 60}")
        print(f"BOOK: {book}")
        print(f"{'─' * 60}")

        total, matched, issues = scan_book(book, args.chapter)

        if total > 0:
            print(f"\n  Summary: {total} quotes checked, {matched} matched, {issues} issues")
        else:
            print(f"  No scripture quotes found.")

        grand_total += total
        grand_matched += matched
        grand_issues += issues

    print(f"\n{'=' * 60}")
    print(f"OVERALL: {grand_total} quotes, {grand_matched} matched, {grand_issues} issues")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
