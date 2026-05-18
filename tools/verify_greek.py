#!/usr/bin/env python3
"""Verify Greek word studies in NobleMind Press books.

Scans HTML and Markdown chapter files for italicized transliterated Greek
words (e.g. *logizetai*, *agape*, *paraklētos*) that appear near a Scripture
citation, then confirms the transliterated word actually occurs in the cited
verse's Greek text (Textus Receptus, via Bolls.Life).

The goal is to catch hallucinated word studies — claims like "the Greek word
for X in this verse is Y" where Y is not actually present in the underlying
Greek. Strong's gloss is printed alongside the match for any word the lookup
can resolve.

Usage:
    python3 tools/verify_greek.py                       # check all books
    python3 tools/verify_greek.py TheLoveGodCallsUsTo   # check one book
    python3 tools/verify_greek.py --book X --chapter 10 # check one chapter

Detection rules:
    * Looks at `*word*` italics in Markdown and `<em>word</em>` / `<i>word</i>`
      in HTML.
    * Skips italics that are obviously English (whitelist words, common
      function words, anything that looks like a title or proper noun).
    * For each candidate, scans up to 8 lines above and below for a NASB
      Scripture citation. Verifies against every cited verse in that window.
    * A word passes if a 4-char transliterated stem appears in any cited
      verse's Greek text.

Greek source: Bolls.Life TR (Textus Receptus) — the same source the project
already trusts for NASB lookups, just the Greek side.
"""

import os
import re
import sys
import json
import time
import html as html_mod
import argparse
import unicodedata
from pathlib import Path
import urllib.request
import urllib.error

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

# Reuse the Bible book table from verify_scripture so we stay in lock-step.
sys.path.insert(0, str(SCRIPT_DIR))
from verify_scripture import (  # noqa: E402
    BIBLE_BOOKS,
    BOOK_DIRS,
    parse_reference,
    strip_html,
)

API_BASE_TR = "https://bolls.life/get-text/TR"
_greek_cache = {}


# ── Strong's lookup ──────────────────────────────────────────────────
_strongs_cache = None


def load_strongs():
    global _strongs_cache
    if _strongs_cache is None:
        path = PROJECT_DIR / "strongs.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _strongs_cache = json.load(f)
        else:
            _strongs_cache = {}
    return _strongs_cache


# ── Transliteration ──────────────────────────────────────────────────
# Map common Latin transliteration → unaccented Greek. This is intentionally
# loose: we only need a stem long enough to substring-match a verse. We strip
# accents and final-sigma variation on both sides before comparing.

_DIGRAPHS = [
    ("th", "θ"),
    ("ph", "φ"),
    ("ch", "χ"),
    ("ps", "ψ"),
    ("rh", "ρ"),
    ("ai", "αι"),
    ("ei", "ει"),
    ("oi", "οι"),
    ("ui", "υι"),
    ("ou", "ου"),
    ("au", "αυ"),
    ("eu", "ευ"),
    ("ē", "η"),
    ("ō", "ω"),
]

_SINGLES = {
    # NB: 'h' is intentionally absent — in standard Koine transliteration it
    # represents the rough breathing mark, which has no character in the
    # unaccented Greek text we substring-match against. So 'h' is dropped.
    # Eta is written 'ē' (with macron) in transliteration; the digraph table
    # handles that case above.
    "a": "α", "b": "β", "g": "γ", "d": "δ", "e": "ε",
    "z": "ζ", "i": "ι", "k": "κ", "l": "λ",
    "m": "μ", "n": "ν", "x": "ξ", "o": "ο", "p": "π",
    "r": "ρ", "s": "σ", "t": "τ", "u": "υ", "y": "υ",
    "w": "ω", "c": "κ", "f": "φ",
}


def transliterate(word):
    """Roughly convert a Latin transliteration to unaccented Greek.

    Returns a Greek string suitable for substring matching against the
    verse text (which we also strip of accents).
    """
    s = word.lower()
    for src, dst in _DIGRAPHS:
        s = s.replace(src, dst)
    out = []
    for ch in s:
        if ch in _SINGLES:
            out.append(_SINGLES[ch])
        elif "α" <= ch <= "ω":
            out.append(ch)
    return "".join(out)


def strip_accents(s):
    """Drop combining accents and normalize final-sigma to sigma."""
    nfd = unicodedata.normalize("NFD", s)
    no_marks = "".join(c for c in nfd if not unicodedata.combining(c))
    return no_marks.replace("ς", "σ").lower()


# ── Italic candidate extraction ──────────────────────────────────────
# Words that look like Greek but are usually English emphasis. We are
# generous on false positives — the verifier just reports SKIP for any
# candidate it can't resolve, which is cheaper than missing a hallucinated
# claim.
ENGLISH_STOPWORDS = {
    "love", "logos", "the", "and", "but", "not", "yes", "no", "for",
    "is", "in", "to", "of", "by", "as", "be", "or", "if", "so",
    "this", "that", "these", "those", "with", "from", "into",
    "very", "real", "true", "only", "what", "where", "why", "how",
    "paid", "free", "now", "today", "tomorrow", "yesterday",
    "ledger", "balance", "debt", "owed",
}


def looks_greek(word):
    """Heuristic: is this italic word plausibly a Greek transliteration?"""
    w = word.lower()
    if len(w) < 4 or len(w) > 25:
        return False
    if w in ENGLISH_STOPWORDS:
        return False
    if not re.fullmatch(r"[a-zēōăāīū'’\-]+", w):
        return False
    # accept anything alpha — final classification happens after we try the
    # Strong's lookup and a verse stem-match; unclassifiable italics get
    # silently skipped rather than reported as failures.
    return True


def has_greek_features(word):
    """Stronger test: does this word *look* like Greek rather than English?

    Used only as a tiebreaker — if Strong's misses and no verse matches,
    a word lacking these features is treated as English emphasis and
    skipped rather than reported as a failure.
    """
    w = word.lower()
    if re.search(r"(ph|ch|ps|th|rh|ē|ō)", w):
        return True
    if re.search(
        r"(etai$|omai$|izō$|omen$|ousin$|ousi$|omenoi$|ētēs$|ētos$|ētai$|ōs$|ōn$)",
        w,
    ):
        return True
    return False


def extract_candidates(content, filepath):
    """Return list of (word, line_number) candidates for Greek verification."""
    candidates = []

    if filepath.suffix == ".md":
        # Markdown italics: single * not preceded/followed by *
        pattern = re.compile(r"(?<!\*)\*([^\*\n]+?)\*(?!\*)")
    else:
        # HTML: <em>...</em>, <i>...</i>
        pattern = re.compile(r"<(?:em|i)>(.*?)</(?:em|i)>", re.IGNORECASE | re.DOTALL)

    for m in pattern.finditer(content):
        raw = m.group(1).strip()
        # strip surrounding punctuation
        raw = raw.strip(".,;:!?\"'()[]")
        if " " in raw or "\t" in raw:
            continue
        if not looks_greek(raw):
            continue
        line_num = content[: m.start()].count("\n") + 1
        candidates.append((raw, line_num))

    return candidates


# ── Citation neighborhood ────────────────────────────────────────────
CITATION_RE = re.compile(
    r"(?:^|[\s\(—–\-])"
    r"(\d?\s*[A-Za-z][A-Za-z]+\.?\s+\d+:\d+(?:\s*[\-–]\s*\d+)?)"
)


def references_near(content, line_num, radius=8):
    """Find Scripture references within `radius` lines of `line_num`."""
    lines = content.split("\n")
    lo = max(0, line_num - 1 - radius)
    hi = min(len(lines), line_num + radius)
    refs = []
    for i in range(lo, hi):
        for m in CITATION_RE.finditer(lines[i]):
            ref = m.group(1).strip()
            parsed = parse_reference(ref)
            if parsed and parsed[2] is not None:
                refs.append((ref, parsed))
    # de-dup keeping order
    seen = set()
    out = []
    for ref, parsed in refs:
        key = (parsed[0], parsed[1], parsed[2], parsed[3])
        if key in seen:
            continue
        seen.add(key)
        out.append((ref, parsed))
    return out


def fetch_greek(book_num, chapter, start_verse, end_verse):
    """Fetch TR Greek text for the given range. Returns concatenated text."""
    key = (book_num, chapter)
    if key not in _greek_cache:
        url = f"{API_BASE_TR}/{book_num}/{chapter}/"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "NobleMindGreek/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            _greek_cache[key] = {v["verse"]: v["text"] for v in data}
            time.sleep(0.3)
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            print(f"    API ERROR fetching Greek {book_num}/{chapter}: {e}")
            return None
    verses = _greek_cache[key]
    if start_verse is None:
        return " ".join(verses[v] for v in sorted(verses.keys()))
    parts = []
    for v in range(start_verse, end_verse + 1):
        if v in verses:
            parts.append(verses[v])
    return " ".join(parts).strip()


# ── Match logic ──────────────────────────────────────────────────────


def stem_for_match(transliterated, original_word):
    """Pick a stem long enough to be specific but short enough to survive
    inflection. Returns the first N chars of the unaccented Greek form."""
    base = strip_accents(transliterated)
    # Trim common verbal endings before matching
    for suffix in ("etai", "omai", "izei", "iz", "etai", "omen", "ousin", "ousi", "omeno", "ate"):
        if base.endswith(strip_accents(transliterate(suffix))):
            base = base[: -len(strip_accents(transliterate(suffix)))]
            break
    # Need at least 4 Greek chars to be specific
    if len(base) < 4:
        base = strip_accents(transliterate(original_word))[:5]
    return base[:6] if len(base) > 6 else base


def find_strongs_for_transliteration(word):
    """Best-effort Strong's lookup by pronunciation field."""
    strongs = load_strongs()
    if not strongs:
        return None
    target = re.sub(r"[^a-z]", "", word.lower())
    # The pronunciation field uses dashes and apostrophes; strip them.
    for code, entry in strongs.items():
        if not code.startswith("G"):
            continue
        pron = re.sub(r"[^a-z]", "", entry.get("pronunciation", "").lower())
        if pron == target:
            return code, entry
        # also try prefix match
        if pron.startswith(target[:5]) and len(target) >= 5:
            return code, entry
    return None


def verify_chapter(filepath):
    """Verify one chapter file. Returns (checked, passed, failed)."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    candidates = extract_candidates(content, filepath)
    if not candidates:
        return 0, 0, 0

    print(f"\n  {filepath.name} ({len(candidates)} Greek candidates)")

    checked = 0
    passed = 0
    failed = 0
    skipped = 0

    for word, line_num in candidates:
        refs = references_near(content, line_num)
        if not refs:
            skipped += 1
            continue

        tr = transliterate(word)
        stem = stem_for_match(tr, word)
        matched_in = None
        verse_samples = []

        for ref_text, parsed in refs:
            book_num, chap, sv, ev = parsed
            greek = fetch_greek(book_num, chap, sv, ev)
            if greek is None:
                continue
            stripped = strip_accents(greek)
            verse_samples.append((ref_text, greek))
            if stem and stem in stripped:
                matched_in = ref_text
                break

        strong = find_strongs_for_transliteration(word)
        strong_note = ""
        if strong:
            code, entry = strong
            gloss = entry.get("definition", "").split(";")[0].strip()
            strong_note = f" [{code} {entry.get('word','')} — {gloss[:80]}]"

        if matched_in:
            checked += 1
            passed += 1
            print(f"    Line {line_num}: *{word}* — VERIFIED in {matched_in}{strong_note}")
        elif not strong and not has_greek_features(word):
            # No Strong's hit, no Greek-form features, no verse match —
            # almost certainly an English emphasis italic, not a Greek claim.
            skipped += 1
        else:
            checked += 1
            failed += 1
            ref_list = ", ".join(r for r, _ in refs)
            print(f"    Line {line_num}: *{word}* — NOT FOUND in nearby refs ({ref_list}){strong_note}")
            print(f"      stem sought: {stem!r}")
            for r, g in verse_samples[:2]:
                print(f"      {r} Greek: {g[:120]}")

    if skipped:
        print(f"    ({skipped} italic candidate(s) had no nearby Scripture ref — skipped)")

    return checked, passed, failed


def scan_book(book_dir, chapter_filter=None):
    book_path = PROJECT_DIR / book_dir
    if not book_path.exists():
        print(f"  Directory not found: {book_dir}")
        return 0, 0, 0

    files = sorted(book_path.glob("chapter-*.html"))
    if not files:
        files = sorted(book_path.glob("chapter*.html"))
    if not files:
        files = sorted(book_path.glob("*Chapter*.md"))
        if not files:
            files = sorted(book_path.glob("*_Ch[0-9]*.md"))
        if not files:
            files = sorted(book_path.glob("*_Ch*.md"))
        for fm_md in sorted(book_path.glob("*_FM_*.md")):
            if fm_md not in files:
                files.insert(0, fm_md)
        for app_md in sorted(book_path.glob("*_App*_*.md")):
            if app_md not in files:
                files.append(app_md)

    for extra in ["introduction.html", "conclusion.html", "authors-note.html", "foreword.html"]:
        p = book_path / extra
        if p.exists() and p not in files:
            files.insert(0, p)

    if chapter_filter is not None:
        files = [
            f for f in files
            if f"chapter-{chapter_filter:02d}" in f.name.lower()
            or f"chapter{chapter_filter}" in f.name.lower()
            or f"_ch{chapter_filter}." in f.name.lower()
            or f"_ch{chapter_filter:02d}." in f.name.lower()
            or f"_ch{chapter_filter}_" in f.name.lower()
            or f"_ch{chapter_filter:02d}_" in f.name.lower()
        ]

    total = matched = issues = 0
    for fp in files:
        c, p, f = verify_chapter(fp)
        total += c
        matched += p
        issues += f
    return total, matched, issues


def main():
    parser = argparse.ArgumentParser(description="Verify Greek word studies against TR")
    parser.add_argument("book", nargs="?", help="Book directory to verify")
    parser.add_argument("--chapter", type=int, help="Specific chapter number")
    args = parser.parse_args()

    books = [args.book] if args.book else BOOK_DIRS

    print("=" * 60)
    print("NobleMind Press — Greek Word-Study Verification")
    print("Checking italicized transliterations against TR (Bolls.Life)")
    print("=" * 60)

    grand_total = grand_matched = grand_issues = 0
    for book in books:
        print(f"\n{'─' * 60}")
        print(f"BOOK: {book}")
        print(f"{'─' * 60}")
        t, m, i = scan_book(book, args.chapter)
        if t == 0:
            print("  No Greek candidates found.")
        else:
            print(f"\n  Summary: {t} candidates checked, {m} verified, {i} unverified")
        grand_total += t
        grand_matched += m
        grand_issues += i

    print(f"\n{'=' * 60}")
    print(f"OVERALL: {grand_total} candidates, {grand_matched} verified, {grand_issues} unverified")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
