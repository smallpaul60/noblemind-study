#!/usr/bin/env python3
"""One-time builder: derive tools/data/bible_verse_counts.json from Bolls.Life NASB.

Walks all 66 Bible books, fetches every chapter from the NASB endpoint,
records the verse count for each (book, chapter) pair, and writes the
result as a JSON file shipped with the verify_counts tool. Re-run only
if Bolls.Life data shifts (very rare) or if you want to refresh.

Rate-limited at 0.3 s per chapter, matching verify_scripture.py's
politeness setting. Total wall time: ~7 minutes for all 1,189 chapters.

Usage:
    python3 tools/build_verse_counts.py
    python3 tools/build_verse_counts.py --book "1 Corinthians"   # one book
    python3 tools/build_verse_counts.py --resume                 # skip done

Output: tools/data/bible_verse_counts.json
Schema: { "<canonical_book>|<chapter_num>": <verse_count>, ... }
        e.g. { "1 Corinthians|13": 13 }
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
OUTPUT_FILE = DATA_DIR / "bible_verse_counts.json"

API_BASE = "https://bolls.life/get-text/NASB"

# Canonical names + Bolls.Life book numbers + chapter counts.
# Chapter counts are well-known fixed values for the 66-book Protestant canon.
BIBLE_BOOKS = [
    # (canonical_name, bolls_book_number, chapter_count)
    ("Genesis", 1, 50),
    ("Exodus", 2, 40),
    ("Leviticus", 3, 27),
    ("Numbers", 4, 36),
    ("Deuteronomy", 5, 34),
    ("Joshua", 6, 24),
    ("Judges", 7, 21),
    ("Ruth", 8, 4),
    ("1 Samuel", 9, 31),
    ("2 Samuel", 10, 24),
    ("1 Kings", 11, 22),
    ("2 Kings", 12, 25),
    ("1 Chronicles", 13, 29),
    ("2 Chronicles", 14, 36),
    ("Ezra", 15, 10),
    ("Nehemiah", 16, 13),
    ("Esther", 17, 10),
    ("Job", 18, 42),
    ("Psalms", 19, 150),
    ("Proverbs", 20, 31),
    ("Ecclesiastes", 21, 12),
    ("Song of Solomon", 22, 8),
    ("Isaiah", 23, 66),
    ("Jeremiah", 24, 52),
    ("Lamentations", 25, 5),
    ("Ezekiel", 26, 48),
    ("Daniel", 27, 12),
    ("Hosea", 28, 14),
    ("Joel", 29, 3),
    ("Amos", 30, 9),
    ("Obadiah", 31, 1),
    ("Jonah", 32, 4),
    ("Micah", 33, 7),
    ("Nahum", 34, 3),
    ("Habakkuk", 35, 3),
    ("Zephaniah", 36, 3),
    ("Haggai", 37, 2),
    ("Zechariah", 38, 14),
    ("Malachi", 39, 4),
    ("Matthew", 40, 28),
    ("Mark", 41, 16),
    ("Luke", 42, 24),
    ("John", 43, 21),
    ("Acts", 44, 28),
    ("Romans", 45, 16),
    ("1 Corinthians", 46, 16),
    ("2 Corinthians", 47, 13),
    ("Galatians", 48, 6),
    ("Ephesians", 49, 6),
    ("Philippians", 50, 4),
    ("Colossians", 51, 4),
    ("1 Thessalonians", 52, 5),
    ("2 Thessalonians", 53, 3),
    ("1 Timothy", 54, 6),
    ("2 Timothy", 55, 4),
    ("Titus", 56, 3),
    ("Philemon", 57, 1),
    ("Hebrews", 58, 13),
    ("James", 59, 5),
    ("1 Peter", 60, 5),
    ("2 Peter", 61, 3),
    ("1 John", 62, 5),
    ("2 John", 63, 1),
    ("3 John", 64, 1),
    ("Jude", 65, 1),
    ("Revelation", 66, 22),
]

RATE_LIMIT_SEC = 0.3


def fetch_chapter_verse_count(book_num: int, chapter: int) -> int:
    url = f"{API_BASE}/{book_num}/{chapter}/"
    req = urllib.request.Request(url, headers={"User-Agent": "NobleMindBuildCounts/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return len(data)


def key_for(book_name: str, chapter: int) -> str:
    return f"{book_name}|{chapter}"


def main():
    ap = argparse.ArgumentParser(description="Build NASB verse-count table from Bolls.Life")
    ap.add_argument("--book", help="Build only one book (canonical name)")
    ap.add_argument("--resume", action="store_true",
                    help="Skip chapters already present in the output JSON")
    args = ap.parse_args()

    DATA_DIR.mkdir(exist_ok=True)

    existing = {}
    if args.resume and OUTPUT_FILE.exists():
        existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        print(f"Resuming — {len(existing)} chapters already cached.")

    books = BIBLE_BOOKS
    if args.book:
        books = [b for b in BIBLE_BOOKS if b[0].lower() == args.book.lower()]
        if not books:
            print(f"Unknown book: {args.book}")
            sys.exit(1)

    total_chapters = sum(c for _, _, c in books)
    done = 0
    failed = []

    for name, num, n_chapters in books:
        print(f"\n{name} (book {num}, {n_chapters} chapters)")
        for ch in range(1, n_chapters + 1):
            k = key_for(name, ch)
            if k in existing:
                done += 1
                continue
            try:
                count = fetch_chapter_verse_count(num, ch)
                existing[k] = count
                done += 1
                print(f"  {name} {ch}: {count} verses   ({done}/{total_chapters})")
            except (urllib.error.URLError, json.JSONDecodeError) as e:
                print(f"  {name} {ch}: FAILED — {e}")
                failed.append((name, ch))
            time.sleep(RATE_LIMIT_SEC)

        # Save after every book so a mid-run interrupt is recoverable.
        OUTPUT_FILE.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nDone. Wrote {len(existing)} entries to {OUTPUT_FILE.relative_to(SCRIPT_DIR.parent)}.")
    if failed:
        print(f"FAILED: {len(failed)} chapters — re-run with --resume to retry:")
        for name, ch in failed:
            print(f"  {name} {ch}")


if __name__ == "__main__":
    main()
