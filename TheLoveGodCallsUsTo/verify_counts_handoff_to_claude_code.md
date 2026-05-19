# Specification: verify_counts.py

**Handoff document for Claude Code**
**Author:** Claude (Anthropic, web client) — drafted May 18, 2026
**Purpose:** Document the count-verification approach used to find and fix six numerical errors in *The Love God Calls Us To* (front matter, Ch. 1, Ch. 2), so the existing tooling can be extended.

---

## 1. The error pattern

AI-generated prose contains numerical assertions that read fluently but are wrong. The model has pattern-matched a count without performing one. The errors slip past human review because the surrounding prose is correct in tone, voice, and substance — the eye glides over a number that "feels right."

In this conversation, six such errors were found across three files:

| # | File | Stated | Actual | Type |
|---|------|--------|--------|------|
| 1 | Ch02 | "Wait for one another. **Five words**." | **Four words** | Word count of quoted phrase |
| 2 | Preface | "The chapter is small. **Six verses**, fifteen attributes." | **Thirteen verses** (1 Cor 13) | Bible chapter verse count |
| 3 | Ch01 | "The next **fifteen chapters**... They are **1 Corinthians 13:4–8**" | Fourteen chapters; 4–7 | Book outline / verse-range |
| 4 | Ch01 | "The next fifteen chapters are written for you" (redundant after #3 fix) | Rewrite | Internal consistency |
| 5 | Preface | "frame the **fifteen attribute chapters** between them" | **Fourteen** | Book outline |
| 6 | Preface | "**each one given a chapter of its own**" (15 attributes → 14 chapters) | Reword | Book outline (combined pair) |

The book has fourteen attribute chapters covering fifteen attributes because Chapter 11 takes up the verse-6 contrast pair (*does not rejoice in unrighteousness, but rejoices with the truth*) together as a single chapter.

---

## 2. Categories of countable claims to check

### 2.1 Word counts of quoted phrases (highest priority)

**Pattern:** A short quoted phrase immediately followed (within ~30 characters) by a number-of-words assertion.

Examples to catch:
- `"Wait for one another." Four words.`
- `"Five words"` following an italicized phrase
- `a three-word command`
- `These two words: "..."`

**Detection:** regex for `(?:"|\*)([^"\*]+)(?:"|\*)\s*[\.\,\—\-:]?\s*(\w+(?:-\w+)?)\s*words?`, then count words in the captured phrase, compare against the stated number.

**Auto-verifiable:** yes, fully.

### 2.2 Bible verse counts ("chapter X has Y verses")

**Pattern:** "N verses" near a biblical book/chapter reference, asserting how many verses are in a chapter or a range.

Examples to catch:
- "The chapter is small. Six verses..."
- "Just three verses..."
- "All twenty-one verses of..."

**Detection:** Requires a Bible verse-count table. Build a dict keyed by `(book, chapter)` returning verse count. For each `(N verses)` claim near a Bible reference, look up the actual count.

**Auto-verifiable:** yes, with a reference table (see §4.1).

### 2.3 Verse-range claims ("chapters cover verses X–Y")

**Pattern:** "1 Corinthians 13:X–Y" type claims that may not match what the chapter actually contains.

Examples to catch:
- "This is a book about 1 Corinthians 13:4–8" (when the book actually covers 12:31–13:13)
- "walked through one attribute at a time, 1 Corinthians 13:4–8" (when attributes are in 4–7)

**Detection:** harder. Requires either (a) a book outline declaring which verses each chapter covers, or (b) human flagging of every Bible range and a prompt to verify.

**Auto-verifiable:** partially. Best handled by maintaining a book-outline file (see §4.2) and checking every range against it.

### 2.4 Chapter / section counts within the book itself

**Pattern:** "the next N chapters," "N attribute chapters," "N sections."

Examples to catch:
- "The next fifteen chapters of this book..."
- "the fifteen attribute chapters between them"
- "each one given a chapter of its own"

**Detection:** Maintain a book outline (see §4.2) declaring chapter count, chapter types (front matter, opening, attribute, closing, appendix), and which attributes each attribute-chapter covers. Then check every "N chapters" claim against the outline.

**Auto-verifiable:** yes, with the outline file.

### 2.5 Attribute counts in 1 Corinthians 13

**Pattern:** "N attributes" in the 1 Cor 13 context.

The correct count is **fifteen** attributes in 1 Cor 13:4–7. Any other number is wrong.

**Auto-verifiable:** yes, with a single constant.

### 2.6 General number-noun pairs (catch-all)

**Pattern:** `(number) (noun)` patterns where the count might be wrong.

Examples to catch as warnings (not errors):
- "Three sentences..."
- "Two paragraphs..."
- "Seven nationalities..."

**Detection:** Find every `(\b(?:two|three|four|five|...|twenty|thirty|...)\s+\w+)` and flag for human review unless explicitly verifiable.

**Auto-verifiable:** no. Flag-for-review only.

---

## 3. Method I used (process, not just regex)

When sweeping the existing files, the process was:

1. **`grep` for likely count terms.** Search each file for `verses`, `chapters`, `words`, `attributes`, `times`, `facts`, `steps`, and the spelled-out numbers from "two" through "twenty" plus "thirty," "forty," "hundred," "thousand," etc.

2. **For each hit, ask: is this verifiable?**
   - Word count of a phrase → count the words in the phrase
   - Verse count of a Bible chapter → look up
   - Chapter count in the book → check against outline
   - Hyperbolic ("a thousand times") → acceptable; skip
   - Vague ("a few," "a handful") → acceptable; skip

3. **Count explicitly.** For word counts: split the phrase by whitespace, count the tokens. For verse counts: list the verses or check a reference. For chapter counts: list the chapters by number from the outline.

4. **Flag mismatches and suggest corrections.** Generate a report identifying each error with line number, the claimed count, the actual count, and a suggested replacement.

The script should automate steps 1–3 and produce the report in step 4 for human review.

---

## 4. Reference data needed

### 4.1 Bible verse-count table

A JSON or Python dict mapping `(book, chapter)` to verse count. Public-domain data; can be derived from the Bolls.Life API or any standard reference. Suggested structure:

```python
BIBLE_VERSE_COUNTS = {
    ("Genesis", 1): 31,
    ("Genesis", 2): 25,
    # ...
    ("1 Corinthians", 13): 13,
    # ...
    ("Revelation", 22): 21,
}
```

Build once, ship with the tool. Same book-name normalization as `verify_scripture.py` already uses.

### 4.2 Book outline file (one per book project)

A YAML or Python data structure declaring the book's chapter structure and verse coverage. For *The Love God Calls Us To*:

```python
BOOK_OUTLINE = {
    "title": "The Love God Calls Us To",
    "subtitle": "Walking Out 1 Corinthians 13",
    "passage": "1 Corinthians 12:31–13:13",
    "front_matter": [
        "Inscription",
        "Dedication",
        "Preface",
    ],
    "chapters": [
        {"num": 1, "type": "opening", "title": "The More Excellent Way",
         "verses": "1 Corinthians 12:31–13:3"},
        {"num": 2, "type": "attribute", "title": "Love Is Patient",
         "verses": "1 Corinthians 13:4a", "attributes": ["is patient"]},
        {"num": 3, "type": "attribute", "title": "Love Is Kind",
         "verses": "1 Corinthians 13:4b", "attributes": ["is kind"]},
        {"num": 4, "type": "attribute", "title": "Love Is Not Jealous",
         "verses": "1 Corinthians 13:4c", "attributes": ["is not jealous"]},
        {"num": 5, "type": "attribute", "title": "Love Does Not Brag",
         "verses": "1 Corinthians 13:4d", "attributes": ["does not brag"]},
        {"num": 6, "type": "attribute", "title": "Love Is Not Arrogant",
         "verses": "1 Corinthians 13:4e", "attributes": ["is not arrogant"]},
        {"num": 7, "type": "attribute", "title": "Love Does Not Act Unbecomingly",
         "verses": "1 Corinthians 13:5a", "attributes": ["does not act unbecomingly"]},
        {"num": 8, "type": "attribute", "title": "Love Does Not Seek Its Own",
         "verses": "1 Corinthians 13:5b", "attributes": ["does not seek its own"]},
        {"num": 9, "type": "attribute", "title": "Love Is Not Provoked",
         "verses": "1 Corinthians 13:5c", "attributes": ["is not provoked"]},
        {"num": 10, "type": "attribute",
         "title": "Love Does Not Take Into Account a Wrong Suffered",
         "verses": "1 Corinthians 13:5d",
         "attributes": ["does not take into account a wrong suffered"]},
        {"num": 11, "type": "attribute",
         "title": "Love Does Not Rejoice in Unrighteousness, but Rejoices With the Truth",
         "verses": "1 Corinthians 13:6",
         "attributes": ["does not rejoice in unrighteousness",
                        "rejoices with the truth"]},  # NOTE: combined pair
        {"num": 12, "type": "attribute", "title": "Love Bears All Things",
         "verses": "1 Corinthians 13:7a", "attributes": ["bears all things"]},
        {"num": 13, "type": "attribute", "title": "Love Believes All Things",
         "verses": "1 Corinthians 13:7b", "attributes": ["believes all things"]},
        {"num": 14, "type": "attribute", "title": "Love Hopes All Things",
         "verses": "1 Corinthians 13:7c", "attributes": ["hopes all things"]},
        {"num": 15, "type": "attribute", "title": "Love Endures All Things",
         "verses": "1 Corinthians 13:7d", "attributes": ["endures all things"]},
        {"num": 16, "type": "closing", "title": "Love Never Fails",
         "verses": "1 Corinthians 13:8–13"},
    ],
    "back_matter": ["Appendix A — What It Means to Obey the Gospel"],
}
```

Derived counts (computed at startup):
- `total_chapters` = 16
- `attribute_chapters` = 14 (types == "attribute")
- `total_attributes` = 15 (sum of len(attributes) for attribute chapters)
- `chapters_after(N)` = 16 − N
- `attribute_chapters_after(N)` = count of attribute chapters with num > N

This file is one-per-book and is the source of truth for any structural claim.

---

## 5. Working implementation (starting point)

```python
#!/usr/bin/env python3
"""verify_counts.py — find unverified numerical claims in book drafts.

Usage:
    python3 tools/verify_counts.py <file.md>
    python3 tools/verify_counts.py LoveGodCallsUsTo/Ch02.md
"""

import re
import sys
from pathlib import Path

# Spelled-out number words → integer
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000,
}

# Bible verse counts — load from JSON file in production
BIBLE_VERSE_COUNTS = {
    ("1 Corinthians", 13): 13,
    # ... full table loaded from data/bible_verses.json
}


def to_int(word_or_digit):
    """Convert 'five' or '5' to int 5."""
    s = word_or_digit.lower().strip()
    if s.isdigit():
        return int(s)
    return NUMBER_WORDS.get(s)


def count_words(phrase):
    """Count words in a quoted phrase, ignoring leading/trailing punctuation."""
    cleaned = re.sub(r'^[\s\W]+|[\s\W]+$', '', phrase)
    return len(cleaned.split())


def check_word_count_claims(content):
    """Find 'N words' claims following a quoted phrase and verify."""
    findings = []
    # Match: quoted phrase (in "..." or *...*) followed within ~30 chars by "N words"
    pattern = re.compile(
        r'(?:["\u201C]([^"\u201D]+)["\u201D]|\*([^\*]+)\*)\s*'
        r'[\.\,\—\-\:\;]?\s*'
        r'(\w+(?:-\w+)?)\s+words?\b',
        re.IGNORECASE
    )
    for m in pattern.finditer(content):
        phrase = m.group(1) or m.group(2)
        stated = to_int(m.group(3))
        if stated is None:
            continue
        actual = count_words(phrase)
        if stated != actual:
            line_num = content[:m.start()].count('\n') + 1
            findings.append({
                'line': line_num,
                'type': 'word_count',
                'phrase': phrase,
                'stated': stated,
                'actual': actual,
                'snippet': m.group(0),
            })
    return findings


def check_bible_verse_count_claims(content):
    """Find 'N verses' claims and verify against known chapter counts.
    
    Looks for patterns like '1 Corinthians 13' or 'the chapter' followed
    nearby by 'N verses'.
    """
    findings = []
    # Heuristic: find "<number> verses" claims, then look for a Bible
    # reference in surrounding context (within ~200 chars before).
    pattern = re.compile(
        r'\b(\w+)\s+verses?\b',
        re.IGNORECASE
    )
    # Bible reference pattern
    bible_ref = re.compile(
        r'\b(\d?\s*[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(\d+)(?::\d+)?\b'
    )
    for m in pattern.finditer(content):
        stated = to_int(m.group(1))
        if stated is None:
            continue
        # Search for a Bible reference in preceding ~200 chars
        context_start = max(0, m.start() - 200)
        context = content[context_start:m.start()]
        ref_matches = list(bible_ref.finditer(context))
        if not ref_matches:
            continue
        # Take the closest preceding reference
        last_ref = ref_matches[-1]
        book = last_ref.group(1).strip()
        chapter = int(last_ref.group(2))
        actual = BIBLE_VERSE_COUNTS.get((book, chapter))
        if actual is None:
            continue
        if stated != actual:
            line_num = content[:m.start()].count('\n') + 1
            findings.append({
                'line': line_num,
                'type': 'verse_count',
                'reference': f"{book} {chapter}",
                'stated': stated,
                'actual': actual,
                'snippet': m.group(0),
            })
    return findings


def check_outline_claims(content, outline):
    """Verify chapter-count claims against the book outline.
    
    Looks for 'next N chapters', 'N attribute chapters', etc.
    """
    findings = []
    total_chapters = len(outline["chapters"])
    attribute_chapters = sum(1 for c in outline["chapters"]
                             if c["type"] == "attribute")
    total_attributes = sum(len(c.get("attributes", []))
                           for c in outline["chapters"])
    
    # "N attribute chapters" or "N chapters of attributes"
    pattern_attr = re.compile(
        r'\b(\w+)\s+(?:attribute\s+chapters?|chapters?\s+of\s+attributes?)\b',
        re.IGNORECASE
    )
    for m in pattern_attr.finditer(content):
        stated = to_int(m.group(1))
        if stated is None:
            continue
        if stated != attribute_chapters:
            line_num = content[:m.start()].count('\n') + 1
            findings.append({
                'line': line_num,
                'type': 'attribute_chapter_count',
                'stated': stated,
                'actual': attribute_chapters,
                'snippet': m.group(0),
            })
    
    # "N attributes" in 1 Cor 13 context
    pattern_attrs = re.compile(r'\b(\w+)\s+attributes\b', re.IGNORECASE)
    for m in pattern_attrs.finditer(content):
        stated = to_int(m.group(1))
        if stated is None:
            continue
        if stated != total_attributes:
            line_num = content[:m.start()].count('\n') + 1
            findings.append({
                'line': line_num,
                'type': 'attribute_count',
                'stated': stated,
                'actual': total_attributes,
                'snippet': m.group(0),
            })
    
    return findings


def check_general_number_noun_pairs(content):
    """Catch-all: flag every spelled-out number+noun for human review.
    
    Produces a warning report, not an error report.
    """
    warnings = []
    number_words_re = '|'.join(NUMBER_WORDS.keys())
    pattern = re.compile(
        rf'\b({number_words_re})\s+(\w+)\b',
        re.IGNORECASE
    )
    for m in pattern.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        warnings.append({
            'line': line_num,
            'snippet': m.group(0),
            'number_word': m.group(1),
            'noun': m.group(2),
        })
    return warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: verify_counts.py <file.md>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    content = path.read_text(encoding='utf-8')
    
    # Run the high-confidence verifiers
    word_findings = check_word_count_claims(content)
    verse_findings = check_bible_verse_count_claims(content)
    
    # Load the book outline if available (alongside the file)
    outline_path = path.parent / "book_outline.py"
    outline_findings = []
    if outline_path.exists():
        # Import outline...
        # outline_findings = check_outline_claims(content, BOOK_OUTLINE)
        pass
    
    # Catch-all warnings
    warnings = check_general_number_noun_pairs(content)
    
    # Report
    errors = word_findings + verse_findings + outline_findings
    print(f"COUNT VERIFICATION — {path.name}")
    print("=" * 60)
    print(f"Errors found: {len(errors)}")
    print(f"Warnings (manual review): {len(warnings)}")
    print()
    
    for e in errors:
        print(f"  Line {e['line']}: [{e['type']}]")
        print(f"    Stated: {e['stated']}  |  Actual: {e['actual']}")
        print(f"    Snippet: \"{e['snippet']}\"")
        if e.get('phrase'):
            print(f"    Phrase: \"{e['phrase']}\"")
        if e.get('reference'):
            print(f"    Reference: {e['reference']}")
        print()
    
    if warnings:
        print(f"\n--- Warnings (review manually) ---")
        for w in warnings:
            print(f"  Line {w['line']}: \"{w['snippet']}\"")
    
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
```

---

## 6. Suggested integration with existing tooling

The existing `tools/` folder has `check_language.py` and `verify_scripture.py`. Add `verify_counts.py` alongside them, with the same interface conventions:

```bash
# Per file
python3 tools/verify_counts.py LoveGodCallsUsTo/Ch02.md

# Per book (walks all chapter files)
python3 tools/verify_counts.py LoveGodCallsUsTo

# All books
python3 tools/verify_counts.py
```

And update any orchestration script (if one exists) to run all three checkers in sequence on every draft:

1. `check_language.py` — denominational/worldly/imprecise language
2. `verify_scripture.py` — NASB quotation accuracy
3. `verify_counts.py` — numerical claim verification

---

## 7. What the script cannot catch (still needs human review)

- **Hyperbolic counts** ("a thousand times at weddings") — these are intentional and acceptable; the script should not flag them, but it cannot reliably distinguish hyperbole from literal claims without context. Suggested approach: maintain an allow-list of phrases.
- **Counts of things in a passage** ("Paul lists fifteen nationalities") — verifiable only if the script knows what passage and what the count refers to. Best handled by spot-check.
- **Approximate dates and durations** ("two thousand years," "forty years in the wilderness") — generally biblical or well-established; flag only if the user requests strict literal verification.
- **Compound claims** ("six verses and fifteen attributes") — the script can check each independently but should report them together if both appear close.

---

## 8. The standing rule

The principle behind the tool, written down so it does not erode:

> *Every numerical claim in our writing must be verified before it is stated. Word counts of quoted phrases, verse counts of biblical passages, chapter counts in the book, attribute counts, any countable assertion. AI pattern-matches counts that read fluently and slip past human review. The remedy is to count explicitly, every time. If verification is uncertain, generalize ("a handful of verses") rather than guess.*

This tool exists to enforce the rule the writer should already be following. The rule comes first; the tool is the safety net.

---

*End of specification. Claude Code — please integrate this into the tooling, derive the Bible verse-count table from the existing Bolls.Life calls, build out the per-book outline file format, and let me know what additional information would be useful from my side.*
