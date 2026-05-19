#!/usr/bin/env python3
"""Verify numerical claims in NobleMind Press books.

Catches numerical assertions that read fluently but are wrong — the
class of error where an AI (or human) pattern-matches a count without
actually counting. Six categories of claim are checked:

  1. Word counts of quoted phrases
     ("those three words", "the first four words" — see detection
     rules below; this was the original tool, now category 1 of many).

  2. Bible verse counts
     ("the chapter is small — six verses" near a Bible reference;
     looked up against tools/data/bible_verse_counts.json, NASB).

  3. Verse-range claims
     ("walked through one attribute at a time, 1 Corinthians 13:4-8"
     when attributes are in 4-7); checked against the per-book
     outline file at <BookDir>/book_outline.py if present.

  4. Chapter / attribute counts within the book itself
     ("the next fifteen chapters", "fifteen attribute chapters"); also
     uses the per-book outline.

  5. Attribute counts in 1 Corinthians 13
     (a constant: fifteen; only flagged if the book outline marks the
     book as treating 1 Cor 13).

  6. General number-noun pairs (catch-all WARNINGS, not errors)
     ("three sentences", "two paragraphs" — printed only with the
     --warnings flag because most are correct).

Language qualifiers ("two Aramaic words", "three Greek words") cause
the word-count checker to skip — original-language counts are not
checked against the English quotation.

Per-book outline file (one per book project, lives in the book dir):
    <BookDir>/book_outline.py
    Exports:
        BOOK_OUTLINE = {
            "title": "...",
            "subtitle": "...",
            "passage": "1 Corinthians 12:31-13:13",
            "front_matter": [...],
            "chapters": [{"num": 1, "type": "opening|attribute|closing",
                          "title": "...", "verses": "1 Cor 13:4a",
                          "attributes": ["is patient"]}, ...],
            "back_matter": [...],
        }

Usage:
    python3 tools/verify_counts.py                       # all books
    python3 tools/verify_counts.py TheLoveGodCallsUsTo   # one book
    python3 tools/verify_counts.py X --chapter 3         # one chapter
    python3 tools/verify_counts.py X --warnings          # include cat 6

Word-count detection rules (category 1, original logic preserved):
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
import json
import argparse
import importlib.util
import html as html_mod
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = SCRIPT_DIR / "data"

sys.path.insert(0, str(SCRIPT_DIR))
from verify_scripture import BOOK_DIRS, BIBLE_BOOKS, parse_reference  # noqa: E402

# --- Number-word vocabularies ---
# WORD_COUNT_NUMBERS is the SHORT list used by the original word-count
# checker (a phrase longer than 20 words is vanishingly rare). Keeping
# it small holds down false positives on category 1.
WORD_COUNT_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}
# Backwards-compat alias for the original code below.
NUMBER_WORDS = WORD_COUNT_NUMBERS
NUMBER_PATTERN = "|".join(NUMBER_WORDS.keys())

# COUNT_NUMBERS is the LONGER list used by categories 2-5 (verse
# counts, chapter counts, attribute counts) where large numbers like
# "one hundred fifty psalms" or "thirty-five verses" are plausible.
TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
ONES = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9,
}
TEENS = {
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}
COUNT_NUMBERS = {**ONES, **TEENS, **TENS}
# Token pattern that matches a count word (digits OR English):
#   "13", "thirty-five", "one hundred fifty", "twenty"
COUNT_TOKEN_RE = re.compile(
    r"\b("
    r"\d+|"
    r"(?:one\s+hundred(?:\s+and)?\s+)?(?:" + "|".join(TENS) + r")(?:[-\s](?:" + "|".join(ONES) + r"))?|"
    r"(?:one\s+hundred(?:\s+and)?\s+)?(?:" + "|".join(TEENS) + r")|"
    r"(?:one\s+hundred(?:\s+and)?\s+)?(?:" + "|".join(ONES) + r")|"
    r"one\s+hundred(?:\s+and)?(?:\s+(?:" + "|".join(TENS) + r"))?(?:[-\s](?:" + "|".join(ONES) + r"))?|"
    r"hundred|thousand"
    r")\b",
    re.IGNORECASE,
)

CLAIM_RE = re.compile(
    rf'\b({NUMBER_PATTERN})\s+(words?)\b',
    re.IGNORECASE,
)

# --- Bible verse-count table (NASB) ---
# Keyed by "Book|Chapter" e.g. "1 Corinthians|13" -> 13.
# Built by tools/build_verse_counts.py from Bolls.Life NASB.
VERSE_COUNTS_FILE = DATA_DIR / "bible_verse_counts.json"
BIBLE_VERSE_COUNTS: dict[str, int] = {}
if VERSE_COUNTS_FILE.exists():
    BIBLE_VERSE_COUNTS = json.loads(VERSE_COUNTS_FILE.read_text(encoding="utf-8"))

# Canonical NASB book names — used to convert verify_scripture's
# numeric IDs back to a string for BIBLE_VERSE_COUNTS lookup.
# Built from BIBLE_BOOKS by taking the longest spelling per number.
_CANONICAL_BY_NUM: dict[int, str] = {}
for _name, _num in BIBLE_BOOKS.items():
    cur = _CANONICAL_BY_NUM.get(_num)
    # Prefer the multi-word, properly-capitalized spelling
    if cur is None or len(_name) > len(cur):
        _CANONICAL_BY_NUM[_num] = _name
# Title-case the canonical names so they match the build output
_CANONICAL_BY_NUM = {
    n: " ".join(w.capitalize() for w in name.split())
    for n, name in _CANONICAL_BY_NUM.items()
}

# Special chapter numbering for Song of Solomon / Song of Songs alias
# (verify_scripture maps both spellings to book 22; build_verse_counts
# wrote the key as "Song Of Solomon").


def parse_count(text: str):
    """Parse '5', 'thirteen', 'thirty-five', 'one hundred fifty', etc.
    Returns int or None if not parseable.
    """
    s = text.strip().lower().replace("-", " ").replace(" and ", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    parts = s.split()
    total = 0
    pending = 0
    for tok in parts:
        if tok in ONES:
            pending += ONES[tok]
        elif tok in TEENS:
            pending += TEENS[tok]
        elif tok in TENS:
            pending += TENS[tok]
        elif tok == "hundred":
            pending = (pending or 1) * 100
        elif tok == "thousand":
            pending = (pending or 1) * 1000
            total += pending
            pending = 0
        else:
            return None  # unknown token — bail
    return total + pending


# Generous claim pattern for categories 2-5: a count token followed by
# a unit noun. Uses COUNT_TOKEN_RE on the left, then a small set of
# verifiable units on the right.
CHAPTER_CLAIM_RE = re.compile(
    rf"\b({COUNT_TOKEN_RE.pattern[2:-2]})\s+"
    r"(verses?|chapters?|attribute\s+chapters?|attributes?|sections?)\b",
    re.IGNORECASE,
)

# Catch-all warning pattern (category 6). Matches "<number> <noun>"
# for any plausible noun — extremely permissive, expected to be noisy.
WARNING_PATTERN_RE = re.compile(
    rf"\b({COUNT_TOKEN_RE.pattern[2:-2]})\s+([a-z]{{3,}}s?)\b",
    re.IGNORECASE,
)

# Bible book name detection for category-2 lookups.
# We re-use verify_scripture's parser via context window.
BIBLE_REF_RE = re.compile(
    r"\b(\d?\s?[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s+(\d+)(?::\d+(?:[–—\-]\d+)?)?\b"
)

# Words that suggest the count is hyperbolic and should not be flagged.
HYPERBOLE_HINTS = (
    "thousand times",
    "thousand years",      # often biblical: "a thousand years as one day"
    "a thousand ",
    "a hundred ",
    "forty years",         # often biblical
    "forty days",
    "seven times",         # Matthew 18:21-22 etc.
    "seventy times",
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


# ── Book outline loader (categories 3, 4, 5) ──────────────────────


def load_book_outline(book_dir: Path):
    """Load <book_dir>/book_outline.py if present. Returns BOOK_OUTLINE dict or None."""
    outline_file = book_dir / "book_outline.py"
    if not outline_file.exists():
        return None
    spec = importlib.util.spec_from_file_location("book_outline", outline_file)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "BOOK_OUTLINE", None)


def outline_stats(outline: dict) -> dict:
    """Derive structural counts from a BOOK_OUTLINE dict."""
    if not outline:
        return {}
    chapters = outline.get("chapters", [])
    attribute_chapters = [c for c in chapters if c.get("type") == "attribute"]
    total_attributes = sum(len(c.get("attributes", [])) for c in attribute_chapters)
    is_1cor13 = "1 corinthians" in outline.get("passage", "").lower()
    return {
        "total_chapters": len(chapters),
        "attribute_chapters": len(attribute_chapters),
        "total_attributes": total_attributes,
        "is_1cor13_book": is_1cor13,
        "passage": outline.get("passage", ""),
    }


def chapters_after(outline: dict, n: int) -> int:
    chapters = outline.get("chapters", [])
    return sum(1 for c in chapters if c.get("num", 0) > n)


def attribute_chapters_after(outline: dict, n: int) -> int:
    chapters = outline.get("chapters", [])
    return sum(1 for c in chapters
               if c.get("num", 0) > n and c.get("type") == "attribute")


# ── Helpers shared across categories 2-6 ──────────────────────────


def _line_number(content: str, pos: int) -> int:
    return content[:pos].count("\n") + 1


def _looks_hyperbolic(content: str, span_start: int, span_end: int) -> bool:
    window = strip_html(content[max(0, span_start - 30):span_end + 30]).lower()
    return any(h in window for h in HYPERBOLE_HINTS)


def _canonical_book_for_lookup(raw_name: str):
    """Resolve a Bible book name to the canonical form used in BIBLE_VERSE_COUNTS."""
    key = raw_name.strip().lower()
    num = BIBLE_BOOKS.get(key)
    if num is None:
        num = BIBLE_BOOKS.get(key.rstrip("s"))
    if num is None:
        return None
    return _CANONICAL_BY_NUM.get(num)


# ── Category 2: Bible verse-count claims ──────────────────────────


def check_verse_count_claims(content: str):
    """Find 'N verses' claims near a Bible reference and verify against
    BIBLE_VERSE_COUNTS. Returns list of finding dicts.
    """
    findings = []
    if not BIBLE_VERSE_COUNTS:
        return findings

    plain = strip_html(content)
    # Build a position map: plain_index -> approximate original position.
    # We don't need exact alignment; for line-number reporting we use
    # the stripped text directly, since the input may be Markdown.
    pattern = re.compile(
        rf"\b({COUNT_TOKEN_RE.pattern[2:-2]})\s+verses?\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(plain):
        stated = parse_count(m.group(1))
        if stated is None:
            continue
        if _looks_hyperbolic(plain, m.start(), m.end()):
            continue

        # Look backward up to 250 chars for a Bible reference. The
        # claim "the chapter is small. Six verses" needs the Bible
        # reference to have been named earlier in the paragraph.
        context_start = max(0, m.start() - 250)
        context = plain[context_start:m.start()]
        refs = list(BIBLE_REF_RE.finditer(context))
        if not refs:
            continue
        last = refs[-1]
        canonical = _canonical_book_for_lookup(last.group(1))
        if canonical is None:
            continue
        try:
            chapter = int(last.group(2))
        except ValueError:
            continue

        actual = BIBLE_VERSE_COUNTS.get(f"{canonical}|{chapter}")
        if actual is None:
            continue
        if stated == actual:
            continue

        # If the claim refers to a verse range like "13:4-7" in the
        # nearby reference, skip — the count might be of the range.
        ref_text = last.group(0)
        if re.search(r":\d+[–—\-]\d+", ref_text):
            continue

        # Line number = count of newlines BEFORE the match in the
        # original (un-stripped) content. We approximate by searching
        # for the matched substring.
        snippet = m.group(0)
        orig_idx = content.find(snippet)
        line = _line_number(content, orig_idx if orig_idx >= 0 else m.start())

        findings.append({
            "category": "verse_count",
            "line": line,
            "reference": f"{canonical} {chapter}",
            "stated": stated,
            "actual": actual,
            "snippet": snippet,
        })
    return findings


# ── Category 3: Verse-range claims ────────────────────────────────


def check_verse_range_claims(content: str, outline: dict):
    """Flag Bible verse-range references that don't match the book's
    declared passage. E.g. claiming '1 Cor 13:4-8' when the book
    actually covers 1 Cor 13:4-7.
    """
    findings = []
    if not outline:
        return findings

    passage = outline.get("passage", "")
    # Parse the book's passage range. Only handle simple form:
    # "1 Corinthians 13:4-7" or "1 Corinthians 12:31-13:13".
    passage_parsed = parse_reference(passage)
    if not passage_parsed:
        return findings
    book_num, p_chapter, p_start, p_end = passage_parsed

    # Pull each Bible reference from content and check that any
    # explicit verse range is within the declared passage.
    plain = strip_html(content)
    for m in BIBLE_REF_RE.finditer(plain):
        raw_book = m.group(1).strip()
        ref_book_num = BIBLE_BOOKS.get(raw_book.lower()) or \
                       BIBLE_BOOKS.get(raw_book.lower().rstrip("s"))
        if ref_book_num != book_num:
            continue
        # Look for an explicit verse range immediately following the
        # chapter number, like "13:4-8".
        ref_text = m.group(0)
        rng = re.search(r":(\d+)[–—\-](\d+)", ref_text)
        if not rng:
            continue
        cited_start = int(rng.group(1))
        cited_end = int(rng.group(2))

        # If chapter matches and end of cited range exceeds the
        # passage's end verse, flag it.
        try:
            cited_chapter = int(m.group(2))
        except ValueError:
            continue
        if cited_chapter != p_chapter:
            continue
        if cited_end > p_end:
            line = _line_number(content, content.find(ref_text)
                                if content.find(ref_text) >= 0 else m.start())
            findings.append({
                "category": "verse_range",
                "line": line,
                "passage": passage,
                "cited": ref_text,
                "snippet": ref_text,
                "stated_end": cited_end,
                "actual_end": p_end,
            })
    return findings


# ── Category 4-5: chapter and attribute counts from outline ────────


def _infer_chapter_num_from_filename(filepath: Path):
    """Pull the chapter number out of a chapter filename. Returns int or None."""
    name = filepath.name.lower()
    m = (re.search(r"chapter[\-_]?(\d+)", name)
         or re.search(r"_ch(\d+)[_\.]", name)
         or re.search(r"_ch(\d+)$", name))
    if m:
        return int(m.group(1))
    return None


def check_outline_claims(content: str, outline: dict, current_chapter: int = None):
    """Verify 'N chapters', 'N attribute chapters', 'N attributes' etc.

    If current_chapter is provided, forward-looking claims like
    "the next N chapters" also accept the count of chapters remaining
    after current_chapter (total and attribute-only forms) as plausible.
    """
    findings = []
    if not outline:
        return findings
    stats = outline_stats(outline)

    plain = strip_html(content)

    def _flag(pos: int, snippet: str, category: str, stated: int, actual: int, note: str = ""):
        if stated == actual:
            return
        orig_idx = content.find(snippet)
        line = _line_number(content, orig_idx if orig_idx >= 0 else pos)
        findings.append({
            "category": category,
            "line": line,
            "stated": stated,
            "actual": actual,
            "snippet": snippet,
            "note": note,
        })

    # "N attribute chapters" / "N chapters of attributes"
    p1 = re.compile(
        rf"\b({COUNT_TOKEN_RE.pattern[2:-2]})\s+"
        r"(?:attribute\s+chapters?|chapters?\s+of\s+attributes?)\b",
        re.IGNORECASE,
    )
    for m in p1.finditer(plain):
        stated = parse_count(m.group(1))
        if stated is None:
            continue
        _flag(m.start(), m.group(0), "attribute_chapter_count",
              stated, stats["attribute_chapters"])

    # "N attributes" — only if the book is a 1 Cor 13 book
    if stats.get("is_1cor13_book"):
        p2 = re.compile(
            rf"\b({COUNT_TOKEN_RE.pattern[2:-2]})\s+attributes\b",
            re.IGNORECASE,
        )
        for m in p2.finditer(plain):
            stated = parse_count(m.group(1))
            if stated is None:
                continue
            _flag(m.start(), m.group(0), "attribute_count",
                  stated, stats["total_attributes"])

    # "the next N chapters", "the remaining N chapters"
    p3 = re.compile(
        rf"\bthe\s+(?:next|remaining|following|other)\s+"
        rf"({COUNT_TOKEN_RE.pattern[2:-2]})\s+chapters?\b",
        re.IGNORECASE,
    )
    for m in p3.finditer(plain):
        stated = parse_count(m.group(1))
        if stated is None:
            continue
        # Build the set of plausible vantage-point answers. Without a
        # current_chapter, we only know book-wide totals; with one, we
        # also know what's remaining from here.
        plausible_truths = {
            stats["total_chapters"],
            stats["attribute_chapters"],
            stats["total_chapters"] - 1,
            stats["attribute_chapters"] + 1,
        }
        if current_chapter is not None:
            plausible_truths |= {
                chapters_after(outline, current_chapter),
                attribute_chapters_after(outline, current_chapter),
                # The above MINUS the closing chapter — common when the
                # author means "the remaining attribute chapters."
                chapters_after(outline, current_chapter) - 1,
            }
        if stated in plausible_truths:
            continue
        # Surface the most-likely intended truths so the reader can
        # tell at a glance which one was meant.
        likely_parts = []
        if current_chapter is not None:
            likely_parts.append(
                f"attribute chapters after ch{current_chapter}="
                f"{attribute_chapters_after(outline, current_chapter)}"
            )
            likely_parts.append(
                f"chapters after ch{current_chapter}="
                f"{chapters_after(outline, current_chapter)}"
            )
        likely_parts.append(f"total_chapters={stats['total_chapters']}")
        likely_parts.append(f"attribute_chapters={stats['attribute_chapters']}")
        _flag(m.start(), m.group(0), "chapter_count_suspicious",
              stated, stats["total_chapters"],
              note="; ".join(likely_parts))
    return findings


# ── Category 6: catch-all warnings ────────────────────────────────


def check_general_warnings(content: str):
    """Flag every spelled-out or numeric count+noun pair for human review.
    Suppressed by default; printed only with --warnings.
    """
    warnings = []
    plain = strip_html(content)
    for m in WARNING_PATTERN_RE.finditer(plain):
        if _looks_hyperbolic(plain, m.start(), m.end()):
            continue
        stated = parse_count(m.group(1))
        if stated is None or stated <= 1:
            continue  # 'one X' is rarely a meaningful count claim
        line = _line_number(content,
                            content.find(m.group(0)) if content.find(m.group(0)) >= 0 else m.start())
        warnings.append({
            "category": "warning",
            "line": line,
            "stated": stated,
            "noun": m.group(2),
            "snippet": m.group(0),
        })
    return warnings


# ── Per-file scanning ─────────────────────────────────────────────


def is_open_ended(content, claim_start, claim_end):
    window = content[max(0, claim_start - 60) : claim_end + 60].lower()
    window = strip_html(window)
    return any(h in window for h in OPEN_ENDED_HINTS)


def has_language_qualifier(content, claim_start, claim_end):
    window = content[max(0, claim_start - 40) : claim_end + 40].lower()
    return any(q in window for q in LANGUAGE_QUALIFIERS)


def scan_file(filepath, outline=None, want_warnings=False):
    """Run all categories of count verification on a single file.

    Returns a dict with five lists:
        word_count_findings   — category 1 (word counts of phrases)
        verse_count_findings  — category 2 (Bible verse counts)
        verse_range_findings  — category 3 (verse ranges vs passage)
        outline_findings      — categories 4-5 (chapter/attribute counts)
        warnings              — category 6 (only if want_warnings)
    Each finding has a 'status' of OK / MISMATCH where applicable.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    is_html = filepath.suffix.lower() in {".html", ".htm"}
    result = {
        "word_count_findings": [],
        "verse_count_findings": [],
        "verse_range_findings": [],
        "outline_findings": [],
        "warnings": [],
    }

    # ── Category 1: word counts of quoted phrases ────────────────
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
            continue
        kind, phrase, actual_count = target
        status = "OK" if actual_count == claimed_count else "MISMATCH"
        result["word_count_findings"].append({
            "category": "word_count",
            "line": line_num,
            "claim": f"{claim_word} {m.group(2)}",
            "claimed_count": claimed_count,
            "actual_count": actual_count,
            "target_kind": kind,
            "target_phrase": phrase,
            "status": status,
        })

    # ── Categories 2-5 ────────────────────────────────────────────
    result["verse_count_findings"] = check_verse_count_claims(content)
    if outline:
        result["verse_range_findings"] = check_verse_range_claims(content, outline)
        current_ch = _infer_chapter_num_from_filename(filepath)
        result["outline_findings"] = check_outline_claims(
            content, outline, current_chapter=current_ch
        )

    # ── Category 6 (only on demand) ──────────────────────────────
    if want_warnings:
        result["warnings"] = check_general_warnings(content)

    return result


# ── Per-book scanning ─────────────────────────────────────────────


def _collect_book_files(book_path: Path):
    """Return the ordered list of chapter-like files to scan in a book."""
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
                  "authors-note.html", "foreword.html",
                  "preface.html"):
        p = book_path / extra
        if p.exists() and p not in files:
            files.insert(0, p)
    return files


def _filter_to_chapter(files, chapter_filter):
    return [
        f for f in files
        if f"chapter-{chapter_filter:02d}" in f.name.lower()
        or f"chapter{chapter_filter}" in f.name.lower()
        or f"_ch{chapter_filter}." in f.name.lower()
        or f"_ch{chapter_filter:02d}." in f.name.lower()
        or f"_ch{chapter_filter}_" in f.name.lower()
        or f"_ch{chapter_filter:02d}_" in f.name.lower()
    ]


def _print_word_count_mismatches(filename, findings):
    if not findings:
        return
    print(f"\n  {filename}  [word counts]")
    for f in findings:
        print(
            f"    Line {f['line']}: claim \"{f['claim']}\" "
            f"({f['claimed_count']}) vs target [{f['target_kind']}] "
            f"\"{f['target_phrase'][:80]}\" "
            f"({f['actual_count']} word{'s' if f['actual_count'] != 1 else ''}) "
            f"— MISMATCH"
        )


def _print_simple_mismatches(filename, findings, label):
    if not findings:
        return
    print(f"\n  {filename}  [{label}]")
    for f in findings:
        ref_or_passage = f.get("reference") or f.get("passage") or ""
        ref_part = f" ({ref_or_passage})" if ref_or_passage else ""
        cited = f.get("cited")
        if cited:
            print(f"    Line {f['line']}: cited \"{cited}\" extends to verse "
                  f"{f['stated_end']} but passage ends at {f['actual_end']}")
        else:
            stated = f.get("stated", "?")
            actual = f.get("actual", "?")
            print(f"    Line {f['line']}: stated {stated}, actual {actual}{ref_part}"
                  f" — snippet: \"{f['snippet']}\"")
            if f.get("note"):
                print(f"      note: {f['note']}")


def _print_warnings(filename, warnings):
    if not warnings:
        return
    print(f"\n  {filename}  [warnings — manual review]")
    for w in warnings:
        print(f"    Line {w['line']}: \"{w['snippet']}\"")


def scan_book(book_dir, chapter_filter=None, want_warnings=False):
    """Scan one book. Returns a dict of category totals."""
    book_path = PROJECT_DIR / book_dir
    if not book_path.exists():
        print(f"  Directory not found: {book_dir}")
        return {
            "word_claims": 0, "word_mismatches": 0,
            "verse_claims": 0, "verse_mismatches": 0,
            "range_mismatches": 0,
            "outline_mismatches": 0,
            "warnings": 0,
        }

    outline = load_book_outline(book_path)
    if outline:
        stats = outline_stats(outline)
        print(f"  outline: {stats['total_chapters']} chapters "
              f"({stats['attribute_chapters']} attribute, "
              f"{stats['total_attributes']} attributes total)"
              + (f"; passage {stats['passage']}" if stats['passage'] else ""))
    else:
        print(f"  no book_outline.py — outline-based checks skipped")

    files = _collect_book_files(book_path)
    if chapter_filter is not None:
        files = _filter_to_chapter(files, chapter_filter)

    totals = {
        "word_claims": 0, "word_mismatches": 0,
        "verse_claims": 0, "verse_mismatches": 0,
        "range_mismatches": 0,
        "outline_mismatches": 0,
        "warnings": 0,
    }

    for fp in files:
        r = scan_file(fp, outline=outline, want_warnings=want_warnings)

        wc_total = len(r["word_count_findings"])
        wc_miss = sum(1 for f in r["word_count_findings"] if f["status"] == "MISMATCH")
        vc_total = len(r["verse_count_findings"])
        rng_total = len(r["verse_range_findings"])
        out_total = len(r["outline_findings"])
        warn_total = len(r["warnings"])

        totals["word_claims"]       += wc_total
        totals["word_mismatches"]   += wc_miss
        totals["verse_claims"]      += vc_total  # only mismatches recorded
        totals["verse_mismatches"]  += vc_total
        totals["range_mismatches"]  += rng_total
        totals["outline_mismatches"] += out_total
        totals["warnings"]          += warn_total

        wc_misses = [f for f in r["word_count_findings"] if f["status"] == "MISMATCH"]
        _print_word_count_mismatches(fp.name, wc_misses)
        _print_simple_mismatches(fp.name, r["verse_count_findings"], "Bible verse counts")
        _print_simple_mismatches(fp.name, r["verse_range_findings"], "verse range vs passage")
        _print_simple_mismatches(fp.name, r["outline_findings"], "outline (chapters/attributes)")
        if want_warnings:
            _print_warnings(fp.name, r["warnings"])

    return totals


def main():
    ap = argparse.ArgumentParser(
        description="Verify numerical claims in NobleMind Press books "
                    "(word counts, verse counts, chapter/attribute counts).")
    ap.add_argument("book", nargs="?", help="Book directory (default: all)")
    ap.add_argument("--chapter", type=int, help="Specific chapter to scan")
    ap.add_argument("--warnings", action="store_true",
                    help="Include catch-all category-6 number+noun warnings")
    args = ap.parse_args()

    books = [args.book] if args.book else BOOK_DIRS

    print("=" * 60)
    print("NobleMind Press — Count Verification")
    print("Categories: word counts, Bible verse counts, "
          "outline (chapters/attributes), catch-all warnings")
    if not BIBLE_VERSE_COUNTS:
        print(f"  WARNING: {VERSE_COUNTS_FILE.relative_to(PROJECT_DIR)} not found — "
              f"Bible verse-count checks disabled.")
        print(f"  Build with: python3 tools/build_verse_counts.py")
    print("=" * 60)

    grand = {
        "word_claims": 0, "word_mismatches": 0,
        "verse_claims": 0, "verse_mismatches": 0,
        "range_mismatches": 0,
        "outline_mismatches": 0,
        "warnings": 0,
    }

    for book in books:
        print(f"\n{'─' * 60}")
        print(f"BOOK: {book}")
        print(f"{'─' * 60}")
        t = scan_book(book, chapter_filter=args.chapter, want_warnings=args.warnings)
        total_miss = (t["word_mismatches"] + t["verse_mismatches"]
                      + t["range_mismatches"] + t["outline_mismatches"])
        if total_miss == 0:
            print(f"\n  Clean: {t['word_claims']} word claim(s), "
                  f"0 verse-count issues, 0 outline issues.")
        else:
            print(f"\n  Summary: {t['word_mismatches']} word-count, "
                  f"{t['verse_mismatches']} verse-count, "
                  f"{t['range_mismatches']} range, "
                  f"{t['outline_mismatches']} outline mismatch(es).")
        for k in grand:
            grand[k] += t[k]

    total_mismatches = (grand["word_mismatches"] + grand["verse_mismatches"]
                        + grand["range_mismatches"] + grand["outline_mismatches"])

    print(f"\n{'=' * 60}")
    # Format consumed by qa_chapter.py's SUMMARY_PATTERNS regex.
    print(f"OVERALL: {grand['word_claims']} claims, "
          f"{total_mismatches} mismatches, "
          f"{grand['warnings']} warnings")
    print(f"  word claims checked: {grand['word_claims']} "
          f"({grand['word_mismatches']} mismatch(es))")
    print(f"  Bible verse counts:  {grand['verse_mismatches']} mismatch(es)")
    print(f"  verse ranges:        {grand['range_mismatches']} mismatch(es)")
    print(f"  outline (ch/attrs):  {grand['outline_mismatches']} mismatch(es)")
    print(f"{'=' * 60}")

    sys.exit(0 if total_mismatches == 0 else 1)


if __name__ == "__main__":
    main()
