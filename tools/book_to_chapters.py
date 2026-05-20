#!/usr/bin/env python3
"""
book_to_chapters.py — Convert a NobleMind Press PDF book into TTS-ready
chapter text files (one .txt per chapter).

Designed for Kokoro narration (no SSML), but works for any TTS that reads
plain text. Targets WeasyPrint-rendered PDFs from NobleMind Press where
chapter headings appear with a drop-cap (rendered by pdftotext as
"C HAPTER ONE", "C HAPTER T WO", etc.).

USAGE
    python3 book_to_chapters.py path/to/book.pdf output_dir/
    python3 book_to_chapters.py path/to/book.pdf output_dir/ --headers headers.txt

    --headers FILE   Optional file with one section header per line. If
                     provided, these are split off onto their own paragraphs
                     so the TTS engine pauses naturally between header and
                     body. If not provided, the script uses a heuristic to
                     detect them automatically.

REQUIREMENTS
    - pdftotext (poppler-utils):   apt install poppler-utils
                                   brew install poppler
    - Python 3.8+

OUTPUT
    Chapter_01.txt, Chapter_02.txt, ... in the output directory.

WHAT THIS SCRIPT DOES (TTS cleanup pipeline, in order)
    1. Find chapter boundaries via "C HAPTER ..." drop-cap artifact
    2. Strip form feeds, page numbers, and decorative dividers
    3. Detect section headers (heuristic or supplied list) and isolate them
    4. Reflow soft-wrapped lines into single-line paragraphs
    5. Repair sentences split across PDF page breaks
    6. Strip Greek/Hebrew foreign words, keeping the meaning
       e.g. 'in the Greek: edakrusen — He shed tears'
            -> 'in the Greek: He shed tears'
    7. Remove '(NASB)' translation tags (TTS reads them awkwardly)
    8. Replace 'v.' with 'verse' and 'vv.' with 'verses'
    9. Convert numbered books to ordinals
       '1 Corinthians' -> 'First Corinthians', '2 Samuel' -> 'Second Samuel', etc.
   10. Apply pronunciation overrides for mispronounced names
       'Job' -> 'Jobe' (extensible via the PRONUNCIATION_OVERRIDES dict)
   11. Spell out Scripture range references
       '2 Samuel 1:17-18' -> 'Second Samuel one, verses seventeen and eighteen'
       'Psalm 23:1-3'     -> 'Psalm twenty-three, verses one thru three'
       (Two-verse range uses 'and'; three or more uses 'thru'.
        Single refs like 'John 11:35' are left unchanged - TTS reads them fine.)
   12. Spell out standalone verse ranges
       'verses 23-24' -> 'verses twenty-three and twenty-four'
   13. Insert comma before parenthetical Scripture references for TTS pause
       'as we read (John 11:35).' -> 'as we read, (John 11:35).'
       (Skips parens that aren't Scripture refs, like '(see below)'.)
   14. Drop the 'Reflection Questions' section if present
   15. Add a period to any paragraph not ending with terminal punctuation
       (so the TTS engine pauses cleanly between paragraphs and headers)
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


# Words that may appear lowercase in a title-case heading.
TITLE_LOWERCASE_WORDS = {
    "a", "an", "the", "and", "but", "or", "nor", "for", "yet", "so",
    "as", "at", "by", "in", "of", "on", "to", "up", "via", "vs",
    "is", "if", "be",
}

# Endings that count as terminal punctuation (sentence-complete).
TERMINAL_CHARS = set('.!?"\u201d\u2019\')]:')


# ---------------------------------------------------------------------------
# Number-to-words (for Bible references read aloud)
# ---------------------------------------------------------------------------

_ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
_TEENS = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
          "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty",
         "sixty", "seventy", "eighty", "ninety"]


def number_to_words(n: int) -> str:
    """Convert integer 1-200 to spoken English words.
    Above 200, falls back to digits (Bible references rarely exceed this)."""
    if not isinstance(n, int) or n < 1 or n > 200:
        return str(n)
    if n < 10:
        return _ONES[n]
    if n < 20:
        return _TEENS[n - 10]
    if n < 100:
        if n % 10 == 0:
            return _TENS[n // 10]
        return f"{_TENS[n // 10]}-{_ONES[n % 10]}"
    if n == 100:
        return "one hundred"
    rest = n - 100
    return f"one hundred {number_to_words(rest)}"


# ---------------------------------------------------------------------------
# Pronunciation overrides for proper names that AI TTS commonly mispronounces.
# Add to this dictionary as listening tests reveal more.
# Matches whole words only (case-sensitive).
# ---------------------------------------------------------------------------

PRONUNCIATION_OVERRIDES = {
    "Job":     "Jobe",       # otherwise read as "job" (occupation)
    # Add more here as you discover them, e.g.:
    # "Habakkuk":   "Hab-uh-kuk",
    # "Methuselah": "Meh-thoo-seh-luh",
    # "Melchizedek":"Mel-kih-zeh-dek",
    # "Capernaum":  "Kuh-pur-nay-um",
    # "Gethsemane": "Geth-sem-uh-nee",
    # "Zacchaeus":  "Zah-kee-us",
}


# Numbered books: "1 Corinthians" -> "First Corinthians", etc.
NUMBERED_BOOKS_PATTERN = re.compile(
    r"\b([123])\s+(Samuel|Kings|Chronicles|Corinthians|Thessalonians|"
    r"Timothy|Peter|John)\b"
)
_ORDINALS = {"1": "First", "2": "Second", "3": "Third"}


def run_pdftotext(pdf_path: Path) -> str:
    """Extract text from a PDF using pdftotext (no -layout, for paragraph flow)."""
    try:
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout
    except FileNotFoundError:
        sys.exit("ERROR: pdftotext not found. Install poppler-utils.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"ERROR: pdftotext failed: {e.stderr}")


def find_chapter_boundaries(text: str) -> list[tuple[int, int]]:
    """Find the (start, end) character positions of each chapter in the text.

    Chapter headings are detected by the WeasyPrint drop-cap artifact:
    'C HAPTER ' followed by a chapter number word (ONE, T WO, THREE, etc.).

    Returns a list of (start, end) byte offsets, one per chapter.
    """
    # Match "C HAPTER " followed by uppercase letters and spaces (allowing
    # for drop-cap on the number word: "T WO", "T HREE", "E LEVEN", etc.)
    pattern = re.compile(r"C HAPTER\s+[A-Z][A-Z\s\-]*?(?=\n)", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        sys.exit("ERROR: No chapter headings found. Is this a NobleMind PDF?")

    # End-of-content markers that signal the last chapter is over.
    end_pattern = re.compile(
        r"^\s*(Scripture Index|Bibliography|Acknowledgments?|"
        r"About the Author|Appendix|Notes)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    boundaries = []
    for i, m in enumerate(matches):
        start = m.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            # Last chapter: ends at first end-marker after this point, or EOF
            end_match = end_pattern.search(text, pos=start)
            end = end_match.start() if end_match else len(text)
        boundaries.append((start, end))

    return boundaries


def normalize_chapter_heading(text: str) -> str:
    """Replace 'C HAPTER ONE' / 'C HAPTER T WO' style with 'Chapter One' etc."""
    # Match the heading line and rebuild it in normal title case.
    def fix(match):
        raw = match.group(0)
        # Strip "C HAPTER " prefix and collapse spaces in the number word
        rest = raw[len("C HAPTER"):].strip()
        # "T WO" -> "TWO", "E LEVEN" -> "ELEVEN" (but keep "TWENTY ONE" hyphenated)
        # Heuristic: if a single uppercase letter is followed by a space and more
        # uppercase letters, glue them together.
        rest = re.sub(r"\b([A-Z]) ([A-Z]+)", r"\1\2", rest)
        return f"Chapter {rest.title()}"

    return re.sub(r"C HAPTER\s+[A-Z][A-Z\s\-]*", fix, text)


def looks_like_header(line: str) -> bool:
    """Heuristic: does this line look like a section heading?"""
    line = line.strip()
    if not line or len(line) > 80:
        return False
    # No terminal punctuation
    if line[-1] in TERMINAL_CHARS or line[-1] in ",;":
        return False
    # First char must be uppercase letter
    if not line[0].isalpha() or not line[0].isupper():
        return False
    words = line.split()
    if not (1 <= len(words) <= 12):
        return False
    # Every word must either be capitalized or be a permitted lowercase word
    for word in words:
        clean = re.sub(r"[^\w]", "", word)
        if not clean:
            continue
        if clean[0].isupper():
            continue
        if clean.lower() in TITLE_LOWERCASE_WORDS:
            continue
        return False
    return True


def reflow_paragraphs(text: str, custom_headers: set[str] | None = None) -> list[str]:
    """Convert raw chapter text into a list of paragraphs, with section
    headers isolated as their own paragraphs."""
    text = text.replace("\f", "")
    lines = text.split("\n")

    # Drop standalone page numbers and decorative dividers
    lines = [ln for ln in lines if not re.fullmatch(r"\s*\d{1,3}\s*", ln)]
    lines = [ln for ln in lines if not re.fullmatch(r"\s*[\u2500\u2014\-_]+\s*", ln)]

    paragraphs = []
    current = []

    def flush():
        if current:
            paragraphs.append(" ".join(current))
            current.clear()

    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            flush()
            continue

        is_header = False
        if custom_headers is not None:
            # Strict mode: only use the user-supplied list
            if stripped in custom_headers:
                is_header = True
        else:
            # Heuristic mode: auto-detect
            if looks_like_header(stripped):
                is_header = True

        if is_header:
            flush()
            paragraphs.append(stripped)
        else:
            current.append(stripped)

    flush()

    # Collapse whitespace and drop empties
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in paragraphs]
    paragraphs = [p for p in paragraphs if p]
    return paragraphs


def repair_page_break_splits(paragraphs: list[str]) -> list[str]:
    """Merge paragraphs that were split mid-sentence by a PDF page break.

    Heuristic: if the previous paragraph ends with a plain word (no terminal
    punctuation, no closing paren, no digit) and isn't a header, join it with
    the next paragraph. We protect any paragraph 12 words or shorter from
    being joined with what follows it (it's likely a header).
    """
    if not paragraphs:
        return paragraphs

    def is_complete(p: str) -> bool:
        p = p.rstrip()
        if not p:
            return True
        last = p[-1]
        if last in TERMINAL_CHARS:
            return True
        if last.isdigit():
            return True
        return False

    def is_header(p: str) -> bool:
        return looks_like_header(p) or len(p.split()) <= 8

    merged = []
    i = 0
    while i < len(paragraphs):
        current = paragraphs[i]
        # Don't extend headers
        if is_header(current):
            merged.append(current)
            i += 1
            continue
        while (i + 1 < len(paragraphs)
               and not is_complete(current)
               and not is_header(paragraphs[i + 1])):
            current = current + " " + paragraphs[i + 1]
            i += 1
        merged.append(current)
        i += 1
    return merged


def apply_text_transformations(paragraphs: list[str]) -> list[str]:
    """Apply all the text-level rules learned from listening tests."""
    out = []
    for p in paragraphs:
        # 1. Strip Greek/Hebrew transliteration:
        # 'in the Greek: <foreign> — <meaning>' -> 'in the Greek: <meaning>'
        p = re.sub(
            r"(in the (?:Greek|Hebrew):\s*)"
            r"[A-Za-z\u00C0-\u017F\u0370-\u03FF\u0590-\u05FF]+\s*[—\-]\s*",
            r"\1",
            p,
            flags=re.IGNORECASE,
        )

        # 2. Remove (NASB) translation tags
        p = re.sub(r"\s*\(NASB\)", "", p)

        # 3. Verse-reference abbreviations: 'vv. 32' -> 'verses 32', 'v. 32' -> 'verse 32'
        # (Do 'vv.' first so 'v.' doesn't double-replace it.)
        p = re.sub(r"\bvv\.\s*(\d)", r"verses \1", p)
        p = re.sub(r"\bv\.\s*(\d)", r"verse \1", p)

        # 4. Numbered books: '1 Corinthians' -> 'First Corinthians', etc.
        p = NUMBERED_BOOKS_PATTERN.sub(
            lambda m: f"{_ORDINALS[m.group(1)]} {m.group(2)}",
            p,
        )

        # 5. Pronunciation overrides for proper names (case-sensitive, word boundary)
        for original, phonetic in PRONUNCIATION_OVERRIDES.items():
            p = re.sub(rf"\b{re.escape(original)}\b", phonetic, p)

        # 6. Scripture range references: 'Chapter:Verse-Verse' -> spoken form.
        # Examples: '23:1-3' -> 'twenty-three, verses one thru three'
        #           '1:17-18' -> 'one, verses seventeen and eighteen'
        # Two consecutive verses (gap of 1) use 'and'; three or more use 'thru'.
        def expand_scripture_range(match):
            chapter = int(match.group(1))
            start = int(match.group(2))
            end = int(match.group(3))
            joiner = "and" if (end - start) == 1 else "thru"
            return (f"{number_to_words(chapter)}, verses "
                    f"{number_to_words(start)} {joiner} {number_to_words(end)}")
        p = re.sub(
            r"\b(\d+):(\d+)\s*[-\u2013\u2014]\s*(\d+)\b",
            expand_scripture_range,
            p,
        )

        # 7. Standalone verse ranges: 'verse(s) X-Y' -> spoken form.
        def expand_verse_range(match):
            start = int(match.group(1))
            end = int(match.group(2))
            joiner = "and" if (end - start) == 1 else "thru"
            return f"verses {number_to_words(start)} {joiner} {number_to_words(end)}"
        p = re.sub(
            r"\bverses?\s+(\d+)\s*[-\u2013\u2014]\s*(\d+)\b",
            expand_verse_range,
            p,
        )

        # 8. Insert comma before parenthetical Scripture references for TTS pause.
        # Example: '...and ends here (Mark 1:5).' -> '...and ends here, (Mark 1:5).'
        # A 'Scripture parenthetical' is a paren whose content contains either
        # a chapter:verse digit pattern (single refs like '11:35') OR the word
        # 'verse'/'verses' (covers all transformed refs from rules 6 and 7).
        # Skips when the preceding char is already a pause character to avoid
        # double-pauses. This ignores parens with non-Scripture content like
        # '(see below)' or '(later)'.
        p = re.sub(
            r"([^\s,;:?!.\u2014\u2013])\s+"
            r"(?=\([^)]*(?:\d+:\d+|\bverses?\b)[^)]*\))",
            r"\1, ",
            p,
        )

        # 9. Collapse any double spaces created above
        p = re.sub(r" {2,}", " ", p).strip()
        if p:
            out.append(p)
    return out


def drop_reflection_questions(paragraphs: list[str]) -> list[str]:
    """Discard the 'Reflection Questions' header and everything after it."""
    out = []
    for p in paragraphs:
        if p.strip().rstrip(".") == "Reflection Questions":
            break
        out.append(p)
    return out


def add_terminal_periods(paragraphs: list[str]) -> list[str]:
    """For TTS pacing: any paragraph not ending in terminal punctuation gets
    a period. This includes section headers, lines ending with verse refs
    like 'John 11:35', etc. — the punctuation cues a clean pause."""
    out = []
    for p in paragraphs:
        p = p.rstrip()
        if not p:
            continue
        if p[-1] not in TERMINAL_CHARS:
            p = p + "."
        out.append(p)
    return out


def process_chapter(chapter_text: str, custom_headers: set[str] | None) -> str:
    """Run the full pipeline on a single chapter's raw text."""
    chapter_text = normalize_chapter_heading(chapter_text)
    paragraphs = reflow_paragraphs(chapter_text, custom_headers)
    paragraphs = repair_page_break_splits(paragraphs)
    paragraphs = apply_text_transformations(paragraphs)
    paragraphs = drop_reflection_questions(paragraphs)
    paragraphs = add_terminal_periods(paragraphs)
    return "\n\n".join(paragraphs) + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Convert a NobleMind Press PDF into TTS-ready chapter files.",
    )
    ap.add_argument("pdf", type=Path, help="Path to the book PDF.")
    ap.add_argument("output_dir", type=Path,
                    help="Directory to write Chapter_NN.txt files into.")
    ap.add_argument("--headers", type=Path, default=None,
                    help="Optional file with section headers (one per line).")
    args = ap.parse_args()

    if not args.pdf.is_file():
        sys.exit(f"ERROR: PDF not found: {args.pdf}")

    custom_headers = None
    if args.headers:
        if not args.headers.is_file():
            sys.exit(f"ERROR: Headers file not found: {args.headers}")
        custom_headers = {ln.strip() for ln in args.headers.read_text().splitlines()
                          if ln.strip()}

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting text from: {args.pdf}")
    full_text = run_pdftotext(args.pdf)

    boundaries = find_chapter_boundaries(full_text)
    print(f"Found {len(boundaries)} chapters.")

    for i, (start, end) in enumerate(boundaries, start=1):
        chapter_raw = full_text[start:end]
        chapter_clean = process_chapter(chapter_raw, custom_headers)
        out_path = args.output_dir / f"Chapter_{i:02d}.txt"
        out_path.write_text(chapter_clean, encoding="utf-8")
        words = len(chapter_clean.split())
        minutes = words / 160
        print(f"  Chapter {i:02d}: {words:>5,} words  (~{minutes:4.1f} min)  -> {out_path.name}")

    print(f"\nDone. Files written to: {args.output_dir}")


if __name__ == "__main__":
    main()
