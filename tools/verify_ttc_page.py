#!/usr/bin/env python3
"""One-off verifier for inline NASB quotations on the test-this-claim page.

Reuses parse_reference / fetch_nasb_text / normalize_text / compare_texts
from tools/verify_scripture.py, but extracts inline "..." (Book Ch:vv, NASB)
patterns instead of blockquotes.

A quoted draft phrase is typically a substring of the full NASB verse(s), so
after the SequenceMatcher ratio, we fall back to a substring check (handling
ellipses) before declaring a mismatch.
"""

import re
import sys
from pathlib import Path

PROJECT = Path('/home/smallpaul/noblemind-study')
sys.path.insert(0, str(PROJECT / 'tools'))

from verify_scripture import (
    parse_reference,
    fetch_nasb_text,
    compare_texts,
    normalize_text,
)

import sys as _sys
_arg = _sys.argv[1] if len(_sys.argv) > 1 else 'infant-baptism-in-the-new-testament.html'
PAGE = PROJECT / 'test-this-claim' / _arg

content = PAGE.read_text(encoding='utf-8')

# Every inline "..." (Book Ch:vv, NASB) occurrence.
pattern = re.compile(r'"([^"]+)"\s*\(([^)]+,\s*NASB)\)', re.DOTALL)

matches = []
for m in pattern.finditer(content):
    quote = m.group(1)
    ref = m.group(2)
    line_num = content[:m.start()].count('\n') + 1
    matches.append((quote, ref, line_num))

print("=" * 70)
print(f"Verifying {len(matches)} inline NASB quotations via Bolls.Life")
print(f"Page: {PAGE.relative_to(PROJECT)}")
print("=" * 70)

total = len(matches)
matched = 0
issues = 0

def clean_ref(r):
    # Decode the entities used on the page, and drop the trailing period in
    # common abbreviations ("Matt.", "Rom.", "Gal.") so the shared tool's
    # parse_reference regex can match.
    r = r.replace('&ndash;', '-').replace('&mdash;', '-').replace('&nbsp;', ' ')
    r = re.sub(r'([A-Za-z])\.\s', r'\1 ', r)   # "Matt. 28:19" -> "Matt 28:19"
    r = re.sub(r'([A-Za-z])\.$', r'\1', r)     # trailing period
    return r

for quote_text, ref_text, line_num in matches:
    parsed = parse_reference(clean_ref(ref_text))
    if parsed is None:
        print(f"\n[line {line_num}] ? Could not parse reference: {ref_text!r}")
        issues += 1
        continue

    book_num, chapter, sv, ev = parsed
    nasb = fetch_nasb_text(book_num, chapter, sv, ev)
    if nasb is None:
        print(f"\n[line {line_num}] ! {ref_text} — API fetch failed")
        issues += 1
        continue

    ratio, diffs = compare_texts(quote_text, nasb)
    q_norm = normalize_text(quote_text)
    a_norm = normalize_text(nasb)

    # Subset check (partial-verse quotations). Then ellipsis-aware subset check.
    subset_match = q_norm.lower() in a_norm.lower()
    if not subset_match and '…' in q_norm:
        parts = [p.strip() for p in q_norm.split('…') if p.strip()]
        pos = 0
        ok = True
        for p in parts:
            idx = a_norm.lower().find(p.lower(), pos)
            if idx < 0:
                ok = False
                break
            pos = idx + len(p)
        subset_match = ok

    status = None
    if subset_match:
        matched += 1
        status = f"OK (substring match in NASB for {ref_text})"
    elif ratio >= 0.98:
        matched += 1
        status = f"OK ({ratio:.0%})"
    elif ratio >= 0.85:
        matched += 1
        status = f"CLOSE ({ratio:.0%}) — worth eyeballing"
    else:
        issues += 1
        status = f"MISMATCH ({ratio:.0%})"

    print(f"\n[line {line_num}] {ref_text}")
    print(f"    {status}")
    if not subset_match and ratio < 0.98:
        if diffs:
            # indent the diff block
            for dl in diffs.splitlines():
                print(f"    {dl}")
        print(f"    DRAFT: {q_norm[:180]}{'…' if len(q_norm) > 180 else ''}")
        print(f"    NASB : {a_norm[:180]}{'…' if len(a_norm) > 180 else ''}")

print("\n" + "=" * 70)
print(f"TOTAL: {total}  |  MATCHED: {matched}  |  ISSUES: {issues}")
print("=" * 70)
sys.exit(0 if issues == 0 else 1)
