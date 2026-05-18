#!/usr/bin/env python3
"""Verify word-count claims in NobleMind Press books.

When a chapter says something like "those three words" or "the first
four words" or "they added six words" near a quoted phrase, this tool
checks that the nearby phrase actually contains the claimed number of
words. Catches slips like claiming "four words" when the quoted phrase
is six.

If the claim qualifies the count by language (e.g. "two Aramaic words"
or "three Greek words"), the verifier skips it — original-language
counts are not checked against the English quotation.

Usage:
    python3 tools/verify_word_counts.py                       # all books
    python3 tools/verify_word_counts.py A_Good_Name           # one book
    python3 tools/verify_word_counts.py --book X --chapter 3  # one chapter

Detection rules:
    * A claim is a number-word ("one"-"twenty") immediately followed
      by "word(s)".
    * Open-ended uses ("in three words — what would you say?") are
      skipped via context hints (e.g. "what would they say").
    * For each remaining claim, the tool looks for a target phrase in
      this order:
        1. The next principle-box content
        2. The first sentence inside the next blockquote
        3. Multiple single-word italic spans within ~60 chars
           (counts spans, not words)
        4. The next single italic span
        5. The next "quoted phrase"
        6. The previous standalone sentence within ~300 chars
    * The target's words are counted (whitespace-split, punctuation
      ignored) and compared to the claim.
    * No target found within range -> SKIP, not FAIL.
"""

import os
import re
import sys
import argparse
import html as html_mod
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from verify_scripture import BOOK_DIRS  # noqa: E402

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}
NUMBER_PATTERN = "|".join(NUMBER_WORDS.keys())

CLAIM_RE = re.compile(
    rf'\b({NUMBER_PATTERN})\s+(words?)\b',
    re.IGNORECASE,
)

LANGUAGE_QUALIFIERS = (
    "aramaic", "hebrew", "greek", "latin",
    "in the original", "original language",
)

# When these substrings appear within ~80 chars of the claim, the count is
# open-ended (the author is asking the reader to summarize / describe /
# imagine, not pointing at a quoted phrase).
OPEN_ENDED_HINTS = (
    "what would they say",
    "what would you say",
    "what would he say",
    "what would she say",
    "what would your",
    "what would my",
    "describe your",
    "describe his",
    "describe her",
    "describe their",
    "describe my",
    "describe a",
    "describe the man",
    "describe the woman",
    "summed up in",
    "summarize",
    "sum up in",
)


def strip_html(text):
    text = re.sub(r"<[^>]+>", "", text)
    return html_mod.unescape(text)


def normalize_phrase(text):
    text = strip_html(text)
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("&ldquo;", '"').replace("&rdquo;", '"')
    text = text.replace("&mdash;", "—").replace("&ndash;", "–")
    text = text.strip()
    # strip surrounding quotes / italics markers
    text = text.strip("\"'`*")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_words(phrase):
    phrase = normalize_phrase(phrase)
    if not phrase:
        return 0
    # Tokens are whitespace-separated; hyphenated words count as one.
    tokens = [t for t in phrase.split() if re.search(r"[A-Za-z0-9]", t)]
    return len(tokens)


# ── Target-phrase finder ──────────────────────────────────────────


def _first_sentence(text):
    text = text.strip()
    m = re.match(r"^(.+?[\.!\?])\s", text)
    if m:
        return m.group(1)
    return text


def classify_claim(content, claim_start):
    """Inspect the words right before the claim to decide which direction
    and which kind of target the claim is pointing at.

    Returns one of:
        ("backward-sentence", None)  — "Those/These N words…"
        ("prev-bq-first", None)      — "the first N words of [prev blockquote]"
        ("prev-bq-last", None)       — "the last N words of [prev blockquote]"
        ("prev-bq-next", None)       — "the next N words…"
        ("forward", None)            — anything else; search forward
    """
    pre_window = strip_html(content[max(0, claim_start - 50) : claim_start]).strip().lower()
    if re.search(r"\b(those|these)\s*$", pre_window):
        return ("backward-sentence", None)
    m = re.search(r"\b(first|last|next)\s*$", pre_window)
    if m:
        return (f"prev-bq-{m.group(1)}", None)
    return ("forward", None)


def _prev_blockquote_html(content, claim_start):
    backward = content[max(0, claim_start - 2500) : claim_start]
    bq_matches = list(
        re.finditer(r"<blockquote[^>]*>(.*?)</blockquote>", backward, re.DOTALL)
    )
    if not bq_matches:
        return None
    last = bq_matches[-1]
    p = re.search(r"<p[^>]*>(.*?)</p>", last.group(1), re.DOTALL)
    raw = p.group(1) if p else last.group(1)
    return normalize_phrase(raw)


def _prev_sentence_in_paragraph_html(content, claim_start):
    para_start = content.rfind("<p", 0, claim_start)
    if para_start < 0:
        text_before = strip_html(content[max(0, claim_start - 250) : claim_start])
    else:
        tag_end = content.find(">", para_start)
        if tag_end < 0:
            tag_end = para_start
        text_before = strip_html(content[tag_end + 1 : claim_start])
    text_before = re.sub(r"\s+", " ", text_before).strip()
    sents = re.findall(r"([A-Z][^.!?]{0,80}[.!?])", text_before)
    return normalize_phrase(sents[-1]) if sents else None


def _short_period_run_before(content, claim_start, max_tokens=6):
    """Detect the 'X. Y. Z. — N words…' pattern: short period-terminated
    tokens (each 1-3 words) immediately before the claim.

    Returns (joined_phrase, token_count) or None.
    """
    pre = strip_html(content[max(0, claim_start - 250) : claim_start]).strip()
    pre = re.sub(r"\s+", " ", pre)
    # Strip trailing connectives like " — " that may precede the count
    pre = re.sub(r"[—–-]+\s*$", "", pre).strip()
    # Pull sentences from the right side
    sents = re.findall(r"([A-Z][a-z]{2,}\.)", pre[-150:])
    if not sents:
        return None
    # Only count consecutive ≤3-word sentences at the end of `pre`
    tail = pre[-150:]
    tokens = re.findall(r"([A-Z][a-z]{2,}\.)\s*", tail)
    if len(tokens) < 2:
        return None
    # Take last `max_tokens` only
    chosen = tokens[-max_tokens:]
    return (" ".join(chosen), len(chosen))


def _inner_quoted_phrase(blockquote_raw):
    """If the blockquote contains an inner '…' quote (e.g. direct speech
    inside narration), return that inner phrase. Otherwise return None.

    We deliberately avoid normalize_phrase here because it strips trailing
    apostrophes, which destroys the closing quote we need to match.
    """
    text = strip_html(blockquote_raw)
    text = html_mod.unescape(text)
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    candidates = re.findall(r"'([^'\n]{2,150})'", text)
    if not candidates:
        return None
    return candidates[-1].strip()


def _slice_by_count(phrase, count, slice_kind):
    words = phrase.split()
    if not words:
        return ""
    if slice_kind == "last":
        return " ".join(words[-count:])
    return " ".join(words[:count])


def find_target_html(content, claim_start, claim_end, claimed_count):
    """Find the most likely target phrase for an HTML claim.

    Returns (kind, phrase_text, word_count) or None.
    """
    kind, _ = classify_claim(content, claim_start)

    if kind.startswith("prev-bq-"):
        prev_bq = _prev_blockquote_html(content, claim_start)
        if prev_bq:
            slice_kind = kind.rsplit("-", 1)[-1]  # first / last / next
            sliced = _slice_by_count(prev_bq, claimed_count, slice_kind)
            return (kind, sliced, count_words(sliced))

    if kind == "backward-sentence":
        prev = _prev_sentence_in_paragraph_html(content, claim_start)
        if prev:
            return ("backward-sentence", prev, count_words(prev))

    # Detect "X. Y. Z. — N words..." pattern: consecutive short
    # period-terminated tokens immediately before the claim.
    run = _short_period_run_before(content, claim_start)
    if run is not None:
        phrase, token_count = run
        # Only trust this if the token-count matches the claim;
        # otherwise we'd be inventing a target.
        if token_count == claimed_count:
            return ("period-run", phrase, token_count)

    # Forward search — inline candidates win on proximity, then by kind.
    forward = content[claim_end : claim_end + 800]
    candidates = []  # (position, kind_label, phrase, count)

    # Multiple single-word italics close together within the same sentence
    em_matches = list(re.finditer(r"<em>([^<]+)</em>", forward[:200]))
    single_word_ems = [m for m in em_matches if len(strip_html(m.group(1)).split()) <= 1]
    if len(single_word_ems) >= 2:
        first_pos = single_word_ems[0].start()
        last_pos = single_word_ems[-1].end()
        if last_pos - first_pos < 80:
            labels = ", ".join(strip_html(m.group(1)).strip() for m in single_word_ems)
            candidates.append((first_pos, "multi-italic", labels, len(single_word_ems)))

    # principle-box, blockquote (close-range)
    pb = re.search(
        r'class="principle-box"[^>]*>.*?<p[^>]*>(.*?)</p>',
        forward[:500],
        re.DOTALL,
    )
    if pb:
        phrase = normalize_phrase(pb.group(1))
        first = _first_sentence(phrase)
        candidates.append((pb.start(), "principle-box", first, count_words(first)))

    bq = re.search(
        r"<blockquote[^>]*>.*?<p[^>]*>(.*?)</p>",
        forward[:500],
        re.DOTALL,
    )
    if bq:
        raw_bq = bq.group(1)
        phrase = normalize_phrase(raw_bq)
        # If the blockquote contains a nested '…' inner quote (direct
        # speech inside narration), prefer the inner phrase. Pass the
        # RAW HTML so the closing apostrophe survives.
        inner = _inner_quoted_phrase(raw_bq)
        chosen = inner if inner else _first_sentence(phrase)
        kind_label = "blockquote-inner" if inner else "blockquote"
        candidates.append((bq.start(), kind_label, chosen, count_words(chosen)))

    if em_matches:
        phrase = normalize_phrase(strip_html(em_matches[0].group(1)))
        if count_words(phrase) >= 1:
            candidates.append((em_matches[0].start(), "italic", phrase, count_words(phrase)))

    # Quoted phrases — but only AFTER stripping HTML attributes so we don't
    # match class names like "scripture" / "divider" / etc.
    forward_stripped = strip_html(forward[:500])
    q = re.search(r'["“]([^"”\n]{2,200})["”]', forward_stripped)
    if q:
        phrase = normalize_phrase(q.group(1))
        # Reject obvious HTML attribute / CSS class fragments.
        if not re.fullmatch(r"[a-z0-9_\-=]+", phrase) and " " in phrase:
            candidates.append((600, "quote", phrase, count_words(phrase)))

    if candidates:
        candidates.sort(key=lambda c: c[0])
        _, k, phrase, cnt = candidates[0]
        return (k, phrase, cnt)

    return None


def _prev_blockquote_md(content, claim_start):
    backward = content[max(0, claim_start - 2500) : claim_start]
    # Capture the last contiguous block of '> ' lines
    blocks = re.findall(r"((?:^>.*\n?)+)", backward, re.MULTILINE)
    if not blocks:
        return None
    raw = blocks[-1]
    # Strip leading '> ' and drop citation lines starting with em-dash
    lines = []
    for ln in raw.splitlines():
        ln = re.sub(r"^>\s?", "", ln).strip()
        if not ln:
            continue
        if re.match(r"^[—–\-]\s*[A-Za-z]", ln):
            continue  # citation
        lines.append(ln)
    if not lines:
        return None
    return normalize_phrase(" ".join(lines))


def _prev_sentence_md(content, claim_start):
    # Same paragraph = bounded by blank lines.
    backward_start = max(0, claim_start - 600)
    text_before = content[backward_start:claim_start]
    # Find the last blank-line boundary
    last_break = text_before.rfind("\n\n")
    if last_break >= 0:
        text_before = text_before[last_break + 2 :]
    text_before = re.sub(r"\s+", " ", text_before).strip()
    sents = re.findall(r"([A-Z][^.!?]{0,80}[.!?])", text_before)
    return normalize_phrase(sents[-1]) if sents else None


def find_target_md(content, claim_start, claim_end, claimed_count):
    """Find the most likely target phrase for a Markdown claim."""
    kind, _ = classify_claim(content, claim_start)

    if kind.startswith("prev-bq-"):
        prev_bq = _prev_blockquote_md(content, claim_start)
        if prev_bq:
            slice_kind = kind.rsplit("-", 1)[-1]
            sliced = _slice_by_count(prev_bq, claimed_count, slice_kind)
            return (kind, sliced, count_words(sliced))

    if kind == "backward-sentence":
        prev = _prev_sentence_md(content, claim_start)
        if prev:
            return ("backward-sentence", prev, count_words(prev))

    forward = content[claim_end : claim_end + 800]
    candidates = []

    em_matches = list(re.finditer(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", forward[:200]))
    single_word_ems = [m for m in em_matches if len(m.group(1).split()) <= 1]
    if len(single_word_ems) >= 2:
        first_pos = single_word_ems[0].start()
        last_pos = single_word_ems[-1].end()
        if last_pos - first_pos < 80:
            labels = ", ".join(m.group(1).strip() for m in single_word_ems)
            candidates.append((first_pos, "multi-italic", labels, len(single_word_ems)))

    bq = re.search(r"^\s*>\s*\*?[\"“]?([^*\n”\"]{4,250})", forward[:500], re.MULTILINE)
    if bq:
        phrase = normalize_phrase(bq.group(1))
        first = _first_sentence(phrase)
        candidates.append((bq.start(), "blockquote", first, count_words(first)))

    if em_matches:
        phrase = normalize_phrase(em_matches[0].group(1))
        candidates.append((em_matches[0].start(), "italic", phrase, count_words(phrase)))

    q = re.search(r'["“]([^"”\n]{2,200})["”]', forward[:500])
    if q:
        phrase = normalize_phrase(q.group(1))
        candidates.append((q.start(), "quote", phrase, count_words(phrase)))

    if candidates:
        candidates.sort(key=lambda c: c[0])
        _, k, phrase, cnt = candidates[0]
        return (k, phrase, cnt)

    return None


# ── Per-file scanning ─────────────────────────────────────────────


def is_open_ended(content, claim_start, claim_end):
    window = content[max(0, claim_start - 60) : claim_end + 60].lower()
    window = strip_html(window)
    return any(h in window for h in OPEN_ENDED_HINTS)


def has_language_qualifier(content, claim_start, claim_end):
    window = content[max(0, claim_start - 40) : claim_end + 40].lower()
    return any(q in window for q in LANGUAGE_QUALIFIERS)


def scan_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    is_html = filepath.suffix.lower() in {".html", ".htm"}
    findings = []

    for m in CLAIM_RE.finditer(content):
        claim_word = m.group(1).lower()
        claimed_count = NUMBER_WORDS[claim_word]

        if has_language_qualifier(content, m.start(), m.end()):
            continue
        if is_open_ended(content, m.start(), m.end()):
            continue

        if is_html:
            target = find_target_html(content, m.start(), m.end(), claimed_count)
        else:
            target = find_target_md(content, m.start(), m.end(), claimed_count)

        line_num = content[: m.start()].count("\n") + 1

        if target is None:
            continue  # no target found in range — skip

        kind, phrase, actual_count = target
        status = "OK" if actual_count == claimed_count else "MISMATCH"
        findings.append({
            "line": line_num,
            "claim": f"{claim_word} {m.group(2)}",
            "claimed_count": claimed_count,
            "actual_count": actual_count,
            "target_kind": kind,
            "target_phrase": phrase,
            "status": status,
        })

    return findings


# ── Per-book scanning ─────────────────────────────────────────────


def scan_book(book_dir, chapter_filter=None):
    book_path = PROJECT_DIR / book_dir
    if not book_path.exists():
        print(f"  Directory not found: {book_dir}")
        return 0, 0

    files = sorted(book_path.glob("chapter-*.html"))
    if not files:
        files = sorted(book_path.glob("chapter*.html"))
    if not files:
        files = sorted(book_path.glob("*Chapter*.md"))
        if not files:
            files = sorted(book_path.glob("*_Ch[0-9]*.md"))
        for fm_md in sorted(book_path.glob("*_FM_*.md")):
            if fm_md not in files:
                files.insert(0, fm_md)
        for app_md in sorted(book_path.glob("*_App*_*.md")):
            if app_md not in files:
                files.append(app_md)

    for extra in ("introduction.html", "conclusion.html",
                   "authors-note.html", "foreword.html"):
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

    total_claims = 0
    mismatches = 0

    for fp in files:
        findings = scan_file(fp)
        if not findings:
            continue
        mismatch_findings = [f for f in findings if f["status"] == "MISMATCH"]
        if not mismatch_findings:
            total_claims += len(findings)
            continue
        print(f"\n  {fp.name}")
        for f in mismatch_findings:
            print(
                f"    Line {f['line']}: claim \"{f['claim']}\" "
                f"({f['claimed_count']}) vs target [{f['target_kind']}] "
                f"\"{f['target_phrase'][:80]}\" "
                f"({f['actual_count']} word{'s' if f['actual_count'] != 1 else ''}) "
                f"— MISMATCH"
            )
        total_claims += len(findings)
        mismatches += len(mismatch_findings)

    return total_claims, mismatches


def main():
    ap = argparse.ArgumentParser(description="Verify word-count claims against quoted phrases")
    ap.add_argument("book", nargs="?")
    ap.add_argument("--chapter", type=int)
    args = ap.parse_args()

    books = [args.book] if args.book else BOOK_DIRS

    print("=" * 60)
    print("NobleMind Press — Word-Count Verification")
    print("Checking 'N words' claims against the phrases they point at")
    print("=" * 60)

    grand_claims = grand_mismatches = 0
    for book in books:
        print(f"\n{'─' * 60}")
        print(f"BOOK: {book}")
        print(f"{'─' * 60}")
        claims, miss = scan_book(book, args.chapter)
        if claims == 0:
            print("  No word-count claims with verifiable targets found.")
        elif miss == 0:
            print(f"  {claims} claim(s) checked, 0 mismatches.")
        else:
            print(f"\n  Summary: {claims} claim(s) checked, {miss} mismatch(es).")
        grand_claims += claims
        grand_mismatches += miss

    print(f"\n{'=' * 60}")
    print(f"OVERALL: {grand_claims} claims, {grand_mismatches} mismatches")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
