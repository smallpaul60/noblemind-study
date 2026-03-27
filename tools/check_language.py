#!/usr/bin/env python3
"""Check NobleMind Press books for denominational, theological, or religious
jargon that should be replaced with plain Bible language.

Scans HTML and Markdown chapter files for flagged words and phrases,
reports each occurrence with line number and surrounding context.

Usage:
    python3 tools/check_language.py                          # check all books
    python3 tools/check_language.py ANewAndLivingWay         # check one book
    python3 tools/check_language.py --chapter 6 ChangeTheMind_ChangeTheMan  # one chapter

The word list is maintained in this file. Add new terms as they are discovered.
Each entry includes the flagged term, the category, and a suggested replacement
or explanation of why it should be avoided.
"""

import os
import re
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

# ─────────────────────────────────────────────────────────────────────
# FLAGGED TERMS
#
# Each entry: (pattern, category, reason/suggestion)
#
# pattern:    regex pattern (case-insensitive by default)
# category:   "denominational", "theological jargon", "religious jargon",
#             "title", or "preference"
# reason:     why it's flagged and what to use instead
#
# NOTE: Some words are legitimate in certain contexts (e.g., "pastor"
# when quoting Ephesians 4:11 or discussing the biblical role of an
# elder). The script flags ALL occurrences so you can review each one
# in context and decide whether it needs to change.
# ─────────────────────────────────────────────────────────────────────

FLAGGED_TERMS = [
    # ── Denominational terms ──────────────────────────────────────
    (r'\btrinity\b', 'denominational',
     'Not a Bible word. Describe the concept directly: Father, Son, and Holy Spirit.'),

    (r'\boriginal sin\b', 'denominational',
     'Not a Bible phrase. Describe what the text says about sin entering the world (Romans 5:12).'),

    (r'\btotal depravity\b', 'denominational',
     'Calvinist doctrinal term. Let the text speak for itself.'),

    (r'\birresistible grace\b', 'denominational',
     'Calvinist doctrinal term. Not in Scripture.'),

    (r'\bunconditional election\b', 'denominational',
     'Calvinist doctrinal term. Not in Scripture.'),

    (r'\blimited atonement\b', 'denominational',
     'Calvinist doctrinal term. Not in Scripture.'),

    (r'\bperseverance of the saints\b', 'denominational',
     'Calvinist doctrinal term. Discuss faithfulness using Hebrews 3:14, Revelation 2:10, etc.'),

    (r'\bonce saved,?\s*always saved\b', 'denominational',
     'Not a Bible phrase. Let passages like Hebrews 6:4-6, 2 Peter 2:20-22 speak.'),

    (r"\bsinner'?s prayer\b", 'denominational',
     'Not found in Scripture. The NT pattern is hear, believe, repent, confess, be baptized.'),

    (r'\baccept Jesus into your heart\b', 'denominational',
     'Not a Bible phrase. Use the NT response to the gospel: Acts 2:38, Romans 6:3-4, etc.'),

    (r'\baltar call\b', 'denominational',
     'Not found in Scripture. A practice, not a Bible concept.'),

    (r'\braptured?\b', 'denominational',
     'The word "rapture" is not in the Bible. Use "caught up" (1 Thessalonians 4:17) if referencing that passage.'),

    (r'\bdispensation(?:al(?:ism|ist)?)?\b', 'denominational',
     'Theological framework term. If quoting Ephesians 1:10 or 3:2, the word is "stewardship" or "administration" in the NASB.'),

    (r'\bpremillennial(?:ism|ist)?\b', 'denominational',
     'Eschatological system term. Let Revelation and other texts speak for themselves.'),

    (r'\bpostmillennial(?:ism|ist)?\b', 'denominational',
     'Eschatological system term.'),

    (r'\bamillennial(?:ism|ist)?\b', 'denominational',
     'Eschatological system term.'),

    (r'\bcatechism\b', 'denominational',
     'Catholic/denominational instruction term.'),

    (r'\bsacrament(?:s|al)?\b', 'denominational',
     'Denominational term. Use the Bible words: baptism, the Lord\'s Supper.'),

    (r'\beucharist\b', 'denominational',
     'Catholic/Orthodox term. Use "the Lord\'s Supper" (1 Corinthians 11:20).'),

    (r'\bholy communion\b', 'denominational',
     'Denominational term. Use "the Lord\'s Supper" or "communion" as in 1 Corinthians 10:16.'),

    (r'\blent\b', 'denominational',
     'Not a Bible observance. Flag for review — may be legitimate if discussing history.'),

    (r'\badvent\b', 'denominational',
     'Denominational calendar term. Flag for review.'),

    (r'\bpurgatory\b', 'denominational',
     'Catholic doctrine. Not in Scripture.'),

    (r'\brosary\b', 'denominational',
     'Catholic practice. Not in Scripture.'),

    (r'\bsecondary matters?\b', 'denominational',
     'Imports a ranking system for Scripture. The Bible does not distinguish primary vs secondary matters.'),

    # ── Denominational titles ─────────────────────────────────────
    (r'\bpastor(?!al|s of)\b(?!\s+(?:the|a|this|that|their|his|her|our)\s+(?:sheep|flock|herd))',
     'title',
     'Denominational title for the preacher/minister. In the NT, "pastor" (poimen) means shepherd '
     'and refers to an elder/overseer (Ephesians 4:11, Acts 20:28). Use "preacher," "evangelist," '
     'or "elder" depending on the role. Exception: when discussing the biblical role of shepherding.'),

    (r'\beverend\b', 'title',
     'Denominational title. Not a Bible title for any church leader.'),

    (r'\bFather\s+(?:John|James|Michael|Patrick|Thomas|Peter|Paul|Joseph|David|Mark|Luke|Matthew|Stephen|Robert|William|Richard|Andrew|Daniel|Anthony|Francis|Benedict|Augustine)\b',
     'title',
     'Catholic title (Father + Name). Matthew 23:9. Use the person\'s name without the title.'),

    (r'\bbishop\b', 'title',
     'Denominational title (Catholic/Anglican/etc). The NASB translates episkopos as "overseer." '
     'Use "overseer" or "elder."'),

    (r'\barchbishop\b', 'title',
     'Denominational title. Not in Scripture.'),

    (r'\bcardinal\b', 'title',
     'Catholic title. Not in Scripture.'),

    (r'\bpope\b', 'title',
     'Catholic title. Not in Scripture.'),

    (r'\bvicar\b', 'title',
     'Denominational title. Not in Scripture.'),

    (r'\bdeacon(?:ess)?\b', 'title',
     'Flag for review. "Deacon" is a Bible word (1 Timothy 3:8-13, Philippians 1:1) — '
     'make sure it is used in the biblical sense, not the denominational sense.'),

    # ── Theological jargon ────────────────────────────────────────
    (r'\btheophany\b', 'theological jargon',
     'Academic theology term. Say "God appeared" or "God showed up" or "God revealed Himself."'),

    (r'\bchristophany\b', 'theological jargon',
     'Academic term. Say "an appearance of Christ before His incarnation" or describe directly.'),

    (r'\bpneumatology\b', 'theological jargon',
     'Academic term for the study of the Holy Spirit. Just discuss the Holy Spirit directly.'),

    (r'\bsoteriology\b', 'theological jargon',
     'Academic term for the study of salvation. Just discuss salvation directly.'),

    (r'\beschatology\b', 'theological jargon',
     'Academic term for the study of last things. Say "what the Bible teaches about the end" or similar.'),

    (r'\bhermeneutic(?:s|al)?\b', 'theological jargon',
     'Academic term for interpretation method. Say "how to read/interpret the Bible" or "principles for Bible study."'),

    (r'\bexeges(?:is|etical)\b', 'theological jargon',
     'Academic term. Say "careful study of the text" or "what the text says."'),

    (r'\beisegesis\b', 'theological jargon',
     'Academic term. Say "reading into the text what is not there."'),

    (r'\bsystematic theology\b', 'theological jargon',
     'Academic discipline name. Describe what you mean directly.'),

    (r'\bprolegomena\b', 'theological jargon',
     'Academic term. Use "introduction" or "preliminary discussion."'),

    (r'\bhamartiology\b', 'theological jargon',
     'Academic term for the study of sin. Just discuss sin directly.'),

    (r'\btheodicy\b', 'theological jargon',
     'Academic/philosophical term. Say "the question of why God allows suffering" or describe directly.'),

    (r'\bontological\b', 'theological jargon',
     'Philosophical term. Describe what you mean in plain language.'),

    (r'\bteleological\b', 'theological jargon',
     'Philosophical term. Describe what you mean in plain language.'),

    (r'\bcosmological\b', 'theological jargon',
     'Philosophical term. Describe what you mean in plain language.'),

    (r'\bpericope\b', 'theological jargon',
     'Academic term for a passage of Scripture. Say "passage" or "section."'),

    (r'\bredaction\b', 'theological jargon',
     'Academic term from textual criticism. Avoid unless discussing the topic directly.'),

    (r'\bcanonical\b', 'theological jargon',
     'May be appropriate in some contexts. Flag for review — consider "books of the Bible" or similar.'),

    # ── Religious jargon / churchy language ───────────────────────
    (r'\bquiet time\b', 'religious jargon',
     'Christian subculture phrase. Say "prayer" or "time in the Word" or describe directly.'),

    (r'\bdevotional\b', 'religious jargon',
     'Flag for review. May be fine in context, but can carry denominational connotations.'),

    (r'\bbackslid(?:den|e|ing)?\b', 'religious jargon',
     'Not a Bible word in most translations. Describe what happened: "turned away," "fell away," etc.'),

    (r'\bunchurched\b', 'religious jargon',
     'Modern church-growth term. Not a Bible word.'),

    (r'\bseeker[- ]?sensitive\b', 'religious jargon',
     'Church-growth movement term. Not a Bible concept.'),

    (r'\bdo life together\b', 'religious jargon',
     'Modern church catchphrase. Say what you mean directly.'),

    (r'\bgod[- ]?moment\b', 'religious jargon',
     'Christian subculture phrase. Describe what happened directly.'),

    (r'\bjourneying\b', 'religious jargon',
     'Flag for review. Often overused in modern Christian writing.'),

    (r'\bunpacking?\b', 'religious jargon',
     'Overused metaphor in sermons/books. Say "examining," "studying," "looking at."'),

    (r'\bleaning into\b', 'religious jargon',
     'Modern catchphrase. Say what you mean directly.'),

    (r'\bbroken(?:ness)?\b(?=\s+(?:before|in|by|from)\s+(?:God|the Lord|Christ|Him))',
     'religious jargon',
     'Flag for review. "Brokenness before God" is a modern phrase. Consider "humility," '
     '"contrition," or let the text use its own language (Psalm 51:17).'),

    (r'\bdo life\b', 'religious jargon',
     'Modern church catchphrase. Say what you mean directly.'),
]

# ── Books to scan ─────────────────────────────────────────────────
BOOK_DIRS = [
    "ANewAndLivingWay",
    "BridgeMoments",
    "ChangeTheMind_ChangeTheMan",
    "OneDayCloserToHome",
    "StrengthAndDignity",
    "TheCharacterNoOneCouldInvent",
    "TheGodWhoShowedUp",
    "ThroughTheValley",
    "YourNameMeansEverything",
]


def strip_html(text):
    """Remove HTML tags."""
    return re.sub(r'<[^>]+>', '', text)


def scan_file(filepath, terms):
    """Scan a single file for flagged terms. Returns list of findings."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # For HTML files, work with stripped text but keep line mapping
    lines = content.split('\n')
    findings = []

    for line_num, line in enumerate(lines, 1):
        # Strip HTML for matching but keep original for display
        plain = strip_html(line)
        if not plain.strip():
            continue

        for pattern, category, reason in terms:
            for match in re.finditer(pattern, plain, re.IGNORECASE):
                # Get context around the match
                start = max(0, match.start() - 40)
                end = min(len(plain), match.end() + 40)
                context = plain[start:end].strip()
                if start > 0:
                    context = '...' + context
                if end < len(plain):
                    context = context + '...'

                findings.append({
                    'line': line_num,
                    'term': match.group(),
                    'category': category,
                    'reason': reason,
                    'context': context,
                })

    return findings


def scan_book(book_dir, chapter_filter=None):
    """Scan all chapter files in a book directory."""
    book_path = PROJECT_DIR / book_dir
    if not book_path.exists():
        print(f"  Directory not found: {book_dir}")
        return 0

    # Find files — HTML first, then Markdown
    files = sorted(book_path.glob("chapter-*.html"))
    if not files:
        files = sorted(book_path.glob("chapter*.html"))
    if not files:
        files = sorted(book_path.glob("*Chapter*.md"))
        for extra_md in sorted(book_path.glob("*Introduction*.md")):
            if extra_md not in files:
                files.insert(0, extra_md)
        for extra_md in sorted(book_path.glob("*Conclusion*.md")):
            if extra_md not in files:
                files.append(extra_md)

    # Also check intro, conclusion, etc. (HTML)
    for extra in ["introduction.html", "conclusion.html", "authors-note.html",
                   "foreword.html", "index.html"]:
        extra_path = book_path / extra
        if extra_path.exists() and extra_path not in files:
            files.insert(0, extra_path)

    if chapter_filter is not None:
        files = [f for f in files
                 if f"chapter-{chapter_filter:02d}" in f.name.lower()
                 or f"chapter{chapter_filter}" in f.name.lower()]

    total_findings = 0

    for filepath in files:
        findings = scan_file(filepath, FLAGGED_TERMS)
        if not findings:
            continue

        print(f"\n  {filepath.name} ({len(findings)} flags)")
        for f in findings:
            print(f"    Line {f['line']}: \"{f['term']}\" [{f['category']}]")
            print(f"      Context: {f['context']}")
            print(f"      Note: {f['reason']}")

        total_findings += len(findings)

    return total_findings


def main():
    parser = argparse.ArgumentParser(
        description="Check books for denominational/theological/religious jargon")
    parser.add_argument("book", nargs="?", help="Book directory to check (default: all)")
    parser.add_argument("--chapter", type=int, help="Specific chapter number to check")
    args = parser.parse_args()

    books = [args.book] if args.book else BOOK_DIRS

    print("=" * 60)
    print("NobleMind Press — Language Check")
    print("Scanning for denominational, theological, and religious jargon")
    print("=" * 60)

    grand_total = 0

    for book in books:
        print(f"\n{'─' * 60}")
        print(f"BOOK: {book}")
        print(f"{'─' * 60}")

        total = scan_book(book, args.chapter)

        if total > 0:
            print(f"\n  Total flags: {total}")
        else:
            print(f"  Clean — no flagged terms found.")

        grand_total += total

    print(f"\n{'=' * 60}")
    print(f"OVERALL: {grand_total} flags across all scanned books")
    print(f"NOTE: Not all flags require changes. Review each in context.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
