#!/usr/bin/env python3
"""
audio_text_converter.py — TTS preparation tool for NobleMind.Study books

Converts manuscript files (markdown or plain text) into TTS-ready plain text:
- Bible references converted to spoken form (e.g., "Genesis 16:13" -> "Genesis sixteen, verse thirteen")
- Numbered books spelled out (e.g., "1 Samuel" -> "First Samuel")
- Numbers in references converted to words
- Chapter/verse ranges converted ("verses one through four", "verses one and two")
- Markdown formatting stripped (headers, bold, italic, horizontal rules, links)
- Chapter heading split (e.g., "# Title — Chapter 3" -> two lines, with "Chapter Three.")
- Custom phonetic name replacements applied (configurable below)

USAGE:
    python audio_text_converter.py input.md
        -> writes input-AUDIO.txt next to the input

    python audio_text_converter.py input.md output.txt
        -> writes to the specified output file

    python audio_text_converter.py input_dir/
        -> converts every .md and .txt file in the directory

    python audio_text_converter.py input_dir/ output_dir/
        -> writes the converted files into output_dir/

CUSTOMIZATION:
    Edit NAME_REPLACEMENTS below to add phonetic spellings for any names
    or terms that get mangled by your TTS engine. Replacements are
    case-sensitive and applied as whole words.
"""

import re
import sys
from pathlib import Path

# =============================================================================
# CUSTOMIZE THIS PER BOOK
# =============================================================================
# Phonetic spellings for names/terms that TTS engines tend to mispronounce.
# Add or remove entries as needed for each book. Keys are case-sensitive.
NAME_REPLACEMENTS = {
    # Hebrew/Greek phrases
    "El Roi": "El Ro-ee",

    # Names commonly mangled by TTS
    "Jochebed":  "Jock-eh-bed",
    "Elkanah":   "El-kah-nah",
    "Peninnah":  "Pen-in-nah",
    "Orpah":     "Or-pah",       # avoids "Oprah" misread
    "Boaz":      "Bo-az",        # avoids "boats"
    "Obed":      "O-bed",
    "Rahab":     "Ray-hab",
    "Salmon":    "Sal-mone",     # avoids the fish
    "Mordecai":  "Mor-deh-kai",
    "Haman":     "Hay-man",
    "Susa":      "Soo-sah",
}

# =============================================================================
# Bible book names (used for reference detection)
# =============================================================================
BOOK_NAMES = (
    "Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|"
    "Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|"
    "Ecclesiastes|Song of Solomon|Song of Songs|Isaiah|Jeremiah|Lamentations|"
    "Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|"
    "Zephaniah|Haggai|Zechariah|Malachi|"
    "Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|"
    "Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|"
    "Hebrews|James|Peter|Jude|Revelation"
)

NUMBER_PREFIX_WORDS = {"1": "First", "2": "Second", "3": "Third"}


# =============================================================================
# Number to words (handles 0-999 — sufficient for any chapter or verse number)
# =============================================================================
def number_to_words(n):
    """Convert an integer (0-999) to its spelled-out form."""
    if n == 0:
        return "zero"

    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
            "eighty", "ninety"]

    if n < 20:
        return ones[n]
    if n < 100:
        if n % 10 == 0:
            return tens[n // 10]
        return tens[n // 10] + "-" + ones[n % 10]
    if n < 1000:
        result = ones[n // 100] + " hundred"
        remainder = n % 100
        if remainder:
            result += " " + number_to_words(remainder)
        return result
    return str(n)  # fallback for unusually large numbers


# =============================================================================
# Bible reference conversion
# =============================================================================
def _book_spoken(prefix, book):
    """Turn '1 Samuel' into 'First Samuel'."""
    if prefix:
        num = prefix.strip()
        return f"{NUMBER_PREFIX_WORDS.get(num, num)} {book}"
    return book


# Verse references with mandatory verse number: "Genesis 16:13", "Psalm 139:1-4", "1 Samuel 1:6"
# The colon and verse number are required to avoid false matches like "Samuel 1900".
REFERENCE_PATTERN = re.compile(
    rf"(?P<prefix>[123]\s+)?(?P<book>{BOOK_NAMES})\s+"
    rf"(?P<chapter>\d+):"
    rf"(?P<verse_start>\d+)(?:[-\u2013](?P<verse_end>\d+))?",
    re.UNICODE
)

# Chapter ranges (no verse): "Exodus 3-14", "Esther 5-9"
CHAPTER_RANGE_PATTERN = re.compile(
    rf"(?P<prefix>[123]\s+)?(?P<book>{BOOK_NAMES})\s+"
    rf"(?P<ch_start>\d+)[-\u2013](?P<ch_end>\d+)(?!:)",
    re.UNICODE
)


def convert_reference(match):
    """Convert a single verse or verse range to spoken form."""
    book_spoken = _book_spoken(match.group("prefix"), match.group("book"))
    chapter_words = number_to_words(int(match.group("chapter")))
    verse_start = int(match.group("verse_start"))
    verse_end = match.group("verse_end")

    start_words = number_to_words(verse_start)

    if verse_end is None:
        return f"{book_spoken} {chapter_words}, verse {start_words}"

    end = int(verse_end)
    end_words = number_to_words(end)

    if end - verse_start == 1:
        return f"{book_spoken} {chapter_words}, verses {start_words} and {end_words}"
    return f"{book_spoken} {chapter_words}, verses {start_words} through {end_words}"


def convert_chapter_range(match):
    """'Exodus 3-14' -> 'Exodus chapters three through fourteen'."""
    book_spoken = _book_spoken(match.group("prefix"), match.group("book"))
    start_words = number_to_words(int(match.group("ch_start")))
    end_words = number_to_words(int(match.group("ch_end")))
    return f"{book_spoken} chapters {start_words} through {end_words}"


# =============================================================================
# Parenthetical reference handling — strips parens, normalizes period placement
# =============================================================================
PAREN_REF_PATTERN = re.compile(
    rf"\s*\(\s*((?:[123]\s+)?(?:{BOOK_NAMES})[^)]+?)\s*\)\.?",
    re.UNICODE
)


def convert_paren_ref(match):
    """(Genesis 16:13) and any trailing period -> '. Genesis sixteen, verse thirteen.'"""
    inner = match.group(1)
    inner = CHAPTER_RANGE_PATTERN.sub(convert_chapter_range, inner)
    inner = REFERENCE_PATTERN.sub(convert_reference, inner)
    return f". {inner}."


# =============================================================================
# Heading processing (run BEFORE strip_markdown)
# =============================================================================
def process_headings(text):
    """Split em-dash titles, spell out 'Chapter N', ensure heading lines end with a period."""

    # Split "# Title — Subtitle" into two heading lines.
    def split_h1(m):
        before, after = m.group(1).strip(), m.group(2).strip()
        # If the second half is "Chapter N", spell the number.
        chap = re.match(r"Chapter\s+(\d+)\s*$", after)
        if chap:
            after = f"Chapter {number_to_words(int(chap.group(1))).capitalize()}"
        return f"# {before}.\n\n# {after}."

    # Use [ \t] (not \s) so we don't accidentally consume the trailing newline
    # of the heading line — that would eat the blank line before the next heading.
    text = re.sub(r"^#[ \t]+(.+?)[ \t]+\u2014[ \t]+(.+?)[ \t]*$", split_h1, text, flags=re.MULTILINE)

    # Spell out any remaining "Chapter <digits>" anywhere in the text.
    text = re.sub(
        r"\bChapter\s+(\d+)\b",
        lambda m: f"Chapter {number_to_words(int(m.group(1))).capitalize()}",
        text,
    )

    # Normalize a heading line: replace internal ": " with ". ", ensure terminal period.
    def ensure_period(m):
        hashes, content = m.group(1), m.group(2).rstrip()
        # In a heading, treat colons as sentence breaks for TTS rather than read "colon"
        content = content.replace(": ", ". ")
        if content and content[-1] not in ".!?":
            content += "."
        return f"{hashes} {content}"

    text = re.sub(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", ensure_period, text, flags=re.MULTILINE)
    return text


# =============================================================================
# Markdown stripping
# =============================================================================
def strip_markdown(text):
    """Remove common markdown formatting while preserving the prose."""
    # Code blocks (rare in prose, but just in case)
    text = re.sub(r"```[^\n]*\n.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Headers — strip the leading # markers, keep the text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Bold (** or __)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)

    # Italic (single * or _) — careful to skip word-internal underscores
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<![_\w])_([^_\n]+)_(?!_)", r"\1", text)

    # Horizontal rules
    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\*\*+\s*$", "", text, flags=re.MULTILINE)

    # Blockquote markers
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

    # Markdown links — keep the link text, drop the URL
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    return text


# =============================================================================
# Cleanup pass
# =============================================================================
def cleanup(text):
    """Final cleanup of the converted text."""
    # If a closing quote already ends a sentence (e.g., ?", !", ."), the period my
    # paren-replacement added right after the quote is redundant — remove it.
    # Allow 1-2 stacked quotes for nested cases like ?'" or .'"
    text = re.sub(r"([.!?])(['\"]{1,2})\. ", r"\1\2 ", text)
    text = re.sub(r"\.\s*\.", ".", text)    # collapse consecutive periods
    text = re.sub(r"  +", " ", text)         # collapse repeated spaces
    text = re.sub(r" +\n", "\n", text)       # remove trailing spaces
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse 3+ blank lines into 2
    return text.strip() + "\n"


# =============================================================================
# Main conversion pipeline
# =============================================================================
def convert(text):
    """Run the full conversion pipeline on a piece of text."""
    text = process_headings(text)                                  # 1. headings first
    text = strip_markdown(text)                                    # 2. strip markdown
    for name, replacement in NAME_REPLACEMENTS.items():            # 3. phonetic names
        text = re.sub(rf"\b{re.escape(name)}\b", replacement, text)
    text = PAREN_REF_PATTERN.sub(convert_paren_ref, text)          # 4. parenthetical refs
    text = CHAPTER_RANGE_PATTERN.sub(convert_chapter_range, text)  # 5. inline chapter ranges
    text = REFERENCE_PATTERN.sub(convert_reference, text)          # 6. inline verse refs
    text = cleanup(text)                                           # 7. cleanup
    return text


# =============================================================================
# File I/O
# =============================================================================
def convert_file(input_path, output_path=None):
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}-AUDIO.txt"
    else:
        output_path = Path(output_path)
    text = input_path.read_text(encoding="utf-8")
    output_path.write_text(convert(text), encoding="utf-8")
    return output_path


def convert_directory(input_dir, output_dir=None):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir) if output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    extensions = (".md", ".txt")
    files = [
        f for f in sorted(input_dir.iterdir())
        if f.is_file() and f.suffix.lower() in extensions and not f.stem.endswith("-AUDIO")
    ]

    converted = []
    for f in files:
        out = output_dir / f"{f.stem}-AUDIO.txt"
        out.write_text(convert(f.read_text(encoding="utf-8")), encoding="utf-8")
        converted.append(out)
        print(f"  + {f.name} -> {out.name}")
    return converted


# =============================================================================
# Command-line interface
# =============================================================================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_arg = Path(sys.argv[1])
    output_arg = sys.argv[2] if len(sys.argv) > 2 else None

    if not input_arg.exists():
        print(f"Error: '{input_arg}' does not exist.")
        sys.exit(1)

    if input_arg.is_dir():
        print(f"Converting all .md/.txt files in {input_arg}/...")
        converted = convert_directory(input_arg, output_arg)
        print(f"Done. Converted {len(converted)} file(s).")
    else:
        out = convert_file(input_arg, output_arg)
        print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
