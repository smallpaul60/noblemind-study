# Specification: categorical-claim checker (extension to verify_counts.py)

**Handoff document for Claude Code**
**Author:** Claude (Anthropic, web client) — drafted May 18, 2026
**Purpose:** Add a categorical/superlative-claim checker to the existing `verify_counts.py` tool. This extends the count verifier to catch a sibling category of error: overreaching superlatives that read fluently but cannot be defended.

---

## 1. The error pattern

The numerical-claim error already addressed by `verify_counts.py` has a twin: the *categorical claim.* Where numerical errors assert wrong counts ("five words" for a four-word phrase), categorical errors assert unverifiable superlatives:

- *the only place in Scripture where God speaks His own attributes aloud*
- *the most uncomfortable opening in the New Testament*
- *the most exalted chapter on love ever written*

These read fluently for the same reason wrong counts do: the surrounding prose is correct in tone, voice, and substance, and the eye glides over the assertion. They are dangerous in exactly the same way: a young reader takes *the only place* as fact, carries it into a Bible class, and is embarrassed when someone names another passage that meets the description.

The principle: any sentence containing *only, never, always, the first, the most, the single, no one else, uniquely* must be tested against whether the strict form can actually be defended. If it cannot, the sentence must be softened (*one of the most, among the, most fully, most concentrated*) until what remains is what can actually be argued from the text.

Unlike numerical claims, categorical claims usually cannot be auto-verified — the script cannot know whether 1 Corinthians 13 is *the most exalted chapter on love ever written.* So the categorical-claim checker is a **flagging tool for human review**, not an automatic error finder. Its job is to surface every superlative for the writer to confirm or soften.

---

## 2. Three real examples from the May 18, 2026 sweep

| File | Line | Original | Status |
|------|------|----------|--------|
| Ch02 | 40 | *the only place in Scripture where God Himself speaks His own attributes aloud in a single declaration* | **Softened** to *the most concentrated place in Scripture where God Himself names the moral attributes of His own being aloud.* (Isaiah 45:5–7, Isaiah 46:9–10, and Revelation 1:8 also have God speaking about Himself; *the only place* could not be defended.) |
| Ch01 | 17 | *the most uncomfortable opening in the New Testament* | **Softened** to *one of the most uncomfortable openings in the New Testament.* (Romans 1:18ff, Hebrews 6, 2 Peter 2, and Galatians 1 are all candidates.) |
| Ch10 | 8 | *the most exalted chapter on love ever written* | **Softened** to *one of the most exalted chapters on love ever written.* (Romans 8 and 1 John 4 have serious advocates.) |

One additional sweep result that was **left as written** — important as a contrast:

| File | Line | Phrase | Why kept |
|------|------|--------|----------|
| Ch02 | 32 | *the most sacred meal of the church* | The Lord's Supper is the only meal Christ commanded for the church. *The most sacred meal* is defensible by direct institution; no other meal competes in the category. |

The contrast matters: not every superlative is wrong. The job of the checker is to surface them all and let the writer decide.

---

## 3. Trigger patterns to flag

Word-boundary, case-insensitive. Each match produces a warning, not an error.

```python
CATEGORICAL_TRIGGERS = [
    r'\bthe\s+only\b',
    r'\bthe\s+first\b',
    r'\bthe\s+most\b',
    r'\bthe\s+single\b',
    r'\bthe\s+sole\b',
    r'\bthe\s+greatest\b',
    r'\bthe\s+best\b',
    r'\bthe\s+worst\b',
    r'\bnever\b',
    r'\balways\b',
    r'\bnone\b',
    r'\bno\s+one\s+(?:else|other|but)\b',
    r'\bunique(?:ly)?\b',
    r'\bsingular(?:ly)?\b',
    r'\bonly\s+(?:place|time|book|one|way|reason)\b',
    r'\bever\s+(?:written|spoken|said|done)\b',
    r'\bmost\s+(?:important|sacred|exalted|uncomfortable|concentrated|powerful)\b',
]
```

---

## 4. The allow-list strategy

Most categorical-trigger matches are not problems. To reduce noise, the checker maintains an allow-list of contexts where the superlative is acceptable. Three categories of allow:

### 4.1 Structural / numbered headings

Matches like *The first —* or *The first is* used as structural section labels in lists or numbered points. Pattern: `^\s*(\*\*)?The\s+(first|second|third|...)\b\s*[—\-:]`

### 4.2 Idiomatic non-claims

Phrases where the superlative is part of a fixed idiom and is not making a verifiable claim. Examples:
- *for the first time*
- *at the first hard week*
- *never give away your last penny* (rhetorical, not categorical)
- *for the first importance* (NASB phrasing in 1 Cor 15:3)

Pattern-allow these by matching surrounding context.

### 4.3 Defensible theological claims tied to specific Scripture

When the categorical claim is the direct teaching of a specific passage, it is defensible. Examples:
- *the only one of them that lasts* — referencing 1 Cor 13:8, 13 (love alone of faith/hope/love endures)
- *no one but Christ has ever loved this way* — defensible from the standard of 1 Cor 13:4-7 as Christ's perfect love
- *the only book ever written by the very God whose nature and works it describes* — defensible within the biblical worldview of inspiration (2 Tim 3:16)

These are harder to pattern-match. The simplest approach is a per-book allow-list file (e.g., `categorical_allowlist.txt`) that holds specific phrases pre-approved by the writer. The checker reads this file and skips matches whose surrounding text matches an allow-list entry.

### 4.4 Implementation note

The allow-list does not need to be sophisticated for the first pass. Start with regex-based exclusions for structural numbering and the most common idioms, then grow the per-phrase allow-list as the writer flags items they want suppressed in future runs.

---

## 5. Suggested integration

Extend `verify_counts.py` with a new function `check_categorical_claims(content)` that returns warnings, not errors. The reporting format should mirror the existing warnings output:

```
CATEGORICAL CLAIMS — Chapter 2
Rules: 17 trigger patterns | Allow-list: 12 entries
Flags (for review): 8
============================================================
  Line 14: "the first thing he says love is" → likely OK (structural)
  Line 32: "the most sacred meal of the church" → review (defended by Christ's institution)
  Line 40: "the most concentrated place in Scripture..." → review (softened from "the only place")
  Line 45: "never goes off at all" → likely OK (metaphor)
  ...
```

The "likely OK" / "review" hints can be derived from whether the match is suppressed by an allow-list rule. Matches that fall through to "review" status are the ones the writer should look at.

---

## 6. Working implementation

```python
import re
from pathlib import Path

CATEGORICAL_TRIGGERS = [
    (r'\bthe\s+only\b', 'the only'),
    (r'\bthe\s+first\b', 'the first'),
    (r'\bthe\s+most\s+\w+', 'the most X'),
    (r'\bthe\s+single\b', 'the single'),
    (r'\bthe\s+sole\b', 'the sole'),
    (r'\bthe\s+greatest\b', 'the greatest'),
    (r'\bnever\b', 'never'),
    (r'\balways\b', 'always'),
    (r'\bno\s+one\s+(?:else|other|but)\b', 'no one else/but'),
    (r'\bunique(?:ly)?\b', 'unique'),
    (r'\bonly\s+(?:place|time|book|one|way|reason)\b', 'only place/time/etc'),
    (r'\bever\s+(?:written|spoken|said|done)\b', 'ever written/spoken/etc'),
]

# Patterns that suppress a match as "likely OK"
ALLOW_PATTERNS = [
    # Structural numbered headings: "**The first —" or "**The first** —"
    (r'^\s*(?:\*\*)?The\s+(?:first|second|third|fourth|fifth)\b\s*(?:\*\*)?\s*[—\-:]',
     'structural numbering'),
    # Common idioms
    (r'\bfor\s+the\s+first\s+time\b', 'idiom: for the first time'),
    (r'\bat\s+the\s+first\b\s+\w+', 'idiom: at the first X'),
    (r'\bnever\s+(?:asks|stops|fails|forgets)\b', 'idiom: never asks/stops/etc'),
    # Direct Scripture quotation patterns (verses in italics or blockquote nearby)
    # ... extend per project
]

# Per-project phrase allow-list (loaded from file)
def load_phrase_allowlist(path):
    """Load a list of approved phrases from a text file (one per line)."""
    if not Path(path).exists():
        return []
    return [line.strip() for line in Path(path).read_text().splitlines()
            if line.strip() and not line.startswith('#')]


def check_categorical_claims(content, phrase_allowlist=None):
    """Find categorical/superlative claims and flag for review.
    
    Returns a list of warnings. Each warning indicates whether the match
    appears to be in an allow-list context ('likely OK') or requires
    human review.
    """
    if phrase_allowlist is None:
        phrase_allowlist = []
    
    warnings = []
    lines = content.split('\n')
    for line_num, line in enumerate(lines, 1):
        for pattern, label in CATEGORICAL_TRIGGERS:
            for m in re.finditer(pattern, line, re.IGNORECASE):
                # Capture surrounding context (~60 chars)
                start = max(0, m.start() - 30)
                end = min(len(line), m.end() + 30)
                context = line[start:end].strip()
                
                # Check allow-list patterns
                allowed_by = None
                for allow_pat, allow_reason in ALLOW_PATTERNS:
                    if re.search(allow_pat, line, re.IGNORECASE):
                        allowed_by = allow_reason
                        break
                
                # Check phrase allow-list
                if not allowed_by:
                    for phrase in phrase_allowlist:
                        if phrase.lower() in line.lower():
                            allowed_by = f'phrase allow-list: "{phrase}"'
                            break
                
                warnings.append({
                    'line': line_num,
                    'trigger': m.group(),
                    'label': label,
                    'context': context,
                    'status': 'likely OK' if allowed_by else 'review',
                    'allowed_by': allowed_by,
                })
    return warnings


def report_categorical(warnings, file_label='file'):
    review = [w for w in warnings if w['status'] == 'review']
    ok = [w for w in warnings if w['status'] == 'likely OK']
    
    print(f"CATEGORICAL CLAIMS — {file_label}")
    print(f"Total triggers: {len(warnings)}  |  "
          f"Likely OK: {len(ok)}  |  For review: {len(review)}")
    print('=' * 60)
    
    if review:
        print("\nFor review:")
        for w in review:
            print(f'  Line {w["line"]}: "{w["trigger"]}" [{w["label"]}]')
            print(f'    Context: ...{w["context"]}...')
    
    if ok:
        print(f"\n(Suppressed by allow-list: {len(ok)} matches — pass --verbose to see.)")
```

Add this as a callable function inside `verify_counts.py`, exposed via a `--categorical` flag or run automatically alongside count verification. Output goes to the same report.

---

## 7. The standing rule (also added to memory)

> *Verify categorical and superlative claims before stating them — "the only," "the first," "the most," "never," "always," "no one else," "uniquely." Same risk as numerical claims: they read fluently and slip past review. If the strict form cannot be defended, soften to "one of the most," "among the," "most fully," "most concentrated." Especially watch Bible-related categoricals (God-speaking passages, prophetic firsts, unique events). Treat every superlative as suspect until defensible from the text.*

---

## 8. What this tool cannot do (still needs human review)

- **Theological judgments** ("the only one of the three that lasts" — defensible from 1 Cor 13:13; the tool cannot know that)
- **Literary/aesthetic claims** ("the most exalted chapter on love" — no way to programmatically rank)
- **Subjective experience claims** ("the most uncomfortable opening" — depends on the reader)

The tool's job is to surface every superlative. The writer decides which stand and which soften. Over time, the per-project allow-list grows to cover the defensible ones, and the noise floor drops.

---

*End of specification. Claude Code — please integrate this as an extension to `verify_counts.py`, with the allow-list loaded from a per-project file (e.g., `LoveGodCallsUsTo/categorical_allowlist.txt`) so each book project can grow its own approved-phrase list as drafting proceeds.*
