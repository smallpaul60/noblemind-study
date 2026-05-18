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
    # ── Worldly relationship constructs ───────────────────────────
    (r'\bher wife\b', 'worldly construct',
     'Same-sex marriage construct. Marriage is one man and one woman '
     '(Genesis 2:24, Matthew 19:4-6, Ephesians 5:22-33).'),

    (r'\bhis husband\b', 'worldly construct',
     'Same-sex marriage construct. Marriage is one man and one woman '
     '(Genesis 2:24, Matthew 19:4-6, Ephesians 5:22-33).'),

    (r'\bsame[- ]?sex\s+(?:marriage|couple|union|partner|relationship|spouse|wedding)\b',
     'worldly construct',
     'Cultural construct contradicting biblical marriage. Flag for '
     'review — may appear legitimately only when explicitly contrasting '
     'with the biblical definition.'),

    (r'\bgay\s+(?:marriage|couple|wedding|union)\b', 'worldly construct',
     'Cultural construct contradicting biblical marriage. Flag for review.'),

    (r'\bnon[- ]?binary\b', 'worldly construct',
     'Cultural construct. Scripture identifies two sexes: male and '
     'female (Genesis 1:27).'),

    (r'\btransgender(?:ed|ism)?\b', 'worldly construct',
     'Cultural construct. Flag for review — handle in light of '
     'Genesis 1:27.'),

    (r'\b(?:preferred|chosen|self[- ]?identified)\s+pronouns?\b',
     'worldly construct',
     'Cultural construct. Flag for review.'),

    (r'\bgender\s+identity\b', 'worldly construct',
     'Cultural construct. Flag for review — discuss in light of '
     'Genesis 1:27.'),

    (r'\bassigned\s+(?:male|female)\s+at\s+birth\b', 'worldly construct',
     'Cultural construct. Sex is created, not assigned '
     '(Genesis 1:27, Psalm 139:13-16).'),

    (r'\bcis(?:gender)?\b', 'worldly construct',
     'Cultural construct presupposing the gender-identity framework. '
     'Flag for review.'),

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

    # ── Denominational terms — salvation framings ─────────────────
    (r'\bfaith[- ]alone\b', 'denominational',
     'Reformed/Baptist/evangelical sola fide framing. Use biblical '
     'language: "obey the gospel" (2 Thess 1:8, 1 Pet 4:17, Rom 10:16, '
     'Rom 6:17). The gospel is defined in 1 Cor 15:3-4.'),

    (r'\btrust[- ]?alone\b', 'denominational',
     'Reformed/Baptist/evangelical framing. Use biblical language: '
     '"obey the gospel" (2 Thess 1:8, 1 Pet 4:17).'),

    (r'\bjust\s+believe\b', 'denominational',
     'Reformed/Baptist/evangelical framing of salvation as bare mental '
     'assent. Use biblical language: "obey the gospel" (2 Thess 1:8).'),

    (r'\bturns?\s+from\s+sin\s+and\s+trusts?\b', 'denominational',
     'Reformed/Baptist/evangelical sola fide framing. Use biblical '
     'language: "obey the gospel" (2 Thess 1:8, 1 Pet 4:17). The full '
     'NT pattern includes hearing, believing, repenting, confessing, '
     'baptism, faithful obedience.'),

    (r'\bbelieves?\s+(?:in\s+)?(?:Jesus|Christ|Him)\s+and\s+(?:is|are|will\s+be)\s+saved\b',
     'denominational',
     'Faith-alone framing. The Bible\'s pattern of response is fuller '
     '(see Acts 2:38, Acts 22:16, Romans 6:3-4).'),

    (r'\b(?:lived|fulfilled)\s+the\s+(?:perfect\s+)?life\s+(?:you|we|they)\s+(?:could|couldn\'?t|never|have\s+not|cannot|can\'?t)\b',
     'denominational',
     'Reformed doctrine of Christ\'s active obedience imputed to '
     'believers. Not stated in Scripture in these terms. Use Paul\'s '
     'own gospel summary: 1 Cor 15:3-4.'),

    (r'\b(?:active|passive)\s+obedience\s+of\s+Christ\b', 'denominational',
     'Reformed theological term for the imputation framework. Not '
     'in Scripture in these terms.'),

    (r'\bimputed\s+righteousness\b', 'denominational',
     'Reformed technical term. Use biblical language for justification '
     '(Romans 3:21-26, Romans 4).'),

    (r'\balien\s+righteousness\b', 'denominational',
     'Reformed/Lutheran technical term. Not biblical language.'),

    (r'\bsola\s+(?:fide|gratia|scriptura|christus)\b', 'denominational',
     'Reformation Latin slogan. Not biblical language. Describe what '
     'is meant directly.'),

    (r'\b(?:ask\w*|invit\w*)\s+(?:Jesus|Christ|the\s+Lord)\s+into\s+(?:your|his|her|my|their)\s+heart\b',
     'denominational',
     'Not a Bible phrase. Use the NT response to the gospel '
     '(Acts 2:38, Romans 6:3-4).'),

    (r'\bgive\s+(?:your|his|her|my|their)\s+(?:heart|life)\s+to\s+(?:Jesus|Christ|the\s+Lord)\b',
     'denominational',
     'Not a Bible phrase. Use the NT response to the gospel '
     '(Acts 2:38, Romans 6:3-4).'),

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

    # ── Imprecise spiritual phrases ───────────────────────────────
    (r'\bwork(?:s|ing|ed)?\s+of\s+the\s+(?:Holy\s+)?Spirit\b',
     'imprecise spiritual',
     'Vague phrase without precise scriptural referent. Name '
     'specifically: "renewing of the mind" (Romans 12:2), "fruit of '
     'the Spirit" (Galatians 5:22), "indwelling of the Holy Spirit" '
     '(Romans 8:9), "sealed with the Holy Spirit" (Ephesians 1:13).'),

    (r'\bmove(?:s|d|ment)?\s+of\s+the\s+(?:Holy\s+)?Spirit\b',
     'imprecise spiritual',
     'Vague phrase, often associated with charismatic experience. '
     'Describe specifically what is meant.'),

    (r'\b(?:I|he|she|we|they)\s+(?:feel|felt|am|was|are|were|been)\s+led\b',
     'imprecise spiritual',
     'Subjective leading language. Scripture is the believer\'s guide '
     '(2 Timothy 3:16-17).'),

    (r'\bfeeling\s+led\b', 'imprecise spiritual',
     'Subjective leading language. Scripture is the believer\'s guide '
     '(2 Timothy 3:16-17).'),

    (r'\bthe\s+anointing\b', 'imprecise spiritual',
     'Charismatic phrase without precise NT referent for the ordinary '
     'believer. Avoid unless quoting OT priestly/kingly anointing or '
     'specific NT use (1 John 2:20, 27).'),

    (r'\banointed\s+(?:preacher|man\s+of\s+God|teaching|sermon|message|service|worship|leader)\b',
     'imprecise spiritual',
     'Charismatic usage. Avoid.'),

    (r'\b(?:God|the\s+Lord)\s+laid\s+(?:it|this|that|something)\s+on\s+(?:my|his|her|their)\s+heart\b',
     'imprecise spiritual',
     'Subjective revelation claim. Scripture is the authority '
     '(2 Timothy 3:16-17, Hebrews 1:1-2).'),

    (r'\blaid\s+(?:it|this|that)\s+on\s+(?:my|his|her|their)\s+heart\b',
     'imprecise spiritual',
     'Subjective revelation claim. Scripture is the authority.'),

    (r'\b(?:God|the\s+Lord|the\s+Spirit)\s+(?:told|said\s+to|spoke\s+to|whispered\s+to)\s+(?:me|him|her|us|them)\b',
     'imprecise spiritual',
     'Subjective revelation claim. God has spoken finally in His Son '
     'through the completed Word (Hebrews 1:1-2).'),

    (r'\bhearing\s+from\s+(?:God|the\s+Lord)\b', 'imprecise spiritual',
     'Subjective revelation language. God speaks through His '
     'completed Word (Hebrews 1:1-2).'),

    (r'\bword\s+from\s+(?:God|the\s+Lord)\b', 'imprecise spiritual',
     'Suggests personal prophecy/subjective revelation. Scripture is '
     'the completed Word (Hebrews 1:1-2). Flag for review.'),

    (r'\bpraying\s+through\b', 'imprecise spiritual',
     'Pentecostal/charismatic phrase. Describe what is meant directly.'),

    (r'\bclaim(?:ing|ed|s)?\s+(?:the\s+)?(?:promise|victory|healing|breakthrough)\b',
     'imprecise spiritual',
     'Word-of-faith / charismatic phrase. Avoid.'),

    (r'\bsoak(?:ing)?\s+in\s+(?:the\s+)?(?:Spirit|presence|glory)\b',
     'imprecise spiritual',
     'Charismatic experiential phrase. Avoid.'),

    (r'\bslain\s+in\s+the\s+Spirit\b', 'imprecise spiritual',
     'Charismatic/Pentecostal phenomenon. Not in Scripture.'),

    (r'\bspirit[- ]?filled\b', 'imprecise spiritual',
     'Often used in charismatic sense. The Bible uses "filled with the '
     'Spirit" with specific contextual meanings — flag for review '
     '(Ephesians 5:18, Acts 2:4, 4:31).'),

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
    "TheLoveGodCallsUsTo",
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
        if not files:
            files = sorted(book_path.glob("*_Ch[0-9]*.md"))
        for extra_md in sorted(book_path.glob("*Introduction*.md")):
            if extra_md not in files:
                files.insert(0, extra_md)
        for extra_md in sorted(book_path.glob("*Conclusion*.md")):
            if extra_md not in files:
                files.append(extra_md)
        for fm_md in sorted(book_path.glob("*_FM_*.md")):
            if fm_md not in files:
                files.insert(0, fm_md)
        for app_md in sorted(book_path.glob("*_App*_*.md")):
            if app_md not in files:
                files.append(app_md)

    # Also check intro, conclusion, etc. (HTML)
    for extra in ["introduction.html", "conclusion.html", "authors-note.html",
                   "foreword.html", "index.html"]:
        extra_path = book_path / extra
        if extra_path.exists() and extra_path not in files:
            files.insert(0, extra_path)

    if chapter_filter is not None:
        files = [f for f in files
                 if f"chapter-{chapter_filter:02d}" in f.name.lower()
                 or f"chapter{chapter_filter}" in f.name.lower()
                 or f"_ch{chapter_filter}." in f.name.lower()
                 or f"_ch{chapter_filter:02d}." in f.name.lower()
                 or f"_ch{chapter_filter}_" in f.name.lower()
                 or f"_ch{chapter_filter:02d}_" in f.name.lower()]

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
