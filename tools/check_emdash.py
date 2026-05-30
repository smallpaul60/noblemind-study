#!/usr/bin/env python3
"""Em-dash density checker for long-form prose.

AI-assisted writing tends toward em-dash overuse — this tool reports
every em-dash in a manuscript with surrounding context and a syntactic
classification, so a human reviewer can decide each one (replace with
comma, semicolon, period, parentheses; or keep deliberately).

Reports density per chapter (em-dashes per 1,000 words) and flags
high-density files. Does NOT auto-edit — em-dashes have legitimate
uses (emphatic interruption, rhetorical breath, dialogue cut-off) and
the call belongs to the author.

Usage:
    python3 tools/check_emdash.py /path/to/manuscript_dir
    python3 tools/check_emdash.py /path/to/manuscript_dir --chapter Ch5
    python3 tools/check_emdash.py /path/to/manuscript_dir --summary
    python3 tools/check_emdash.py /path/to/manuscript_dir --out report.txt

Note on dash characters:
    em-dash (—, U+2014) — what this tool flags
    en-dash (–, U+2013) — used in ranges (Gen 12:1–3); NOT flagged
    hyphen (-)         — not flagged
    double-hyphen (--) — flagged as a likely em-dash stand-in
"""

import re
import argparse
from pathlib import Path
import sys

# What we flag: U+2014 em-dash, and double-hyphens that aren't inside longer runs
EMDASH_RE = re.compile(r'—|(?<!-)--(?!-)')

CONTEXT_CHARS = 70

# Files in the manuscript directory we skip (handoff/principles/outline)
SKIP_NAMES = ('HANDOFF', 'PRINCIPLES', 'Outline', 'Comprehensive', 'README')


def classify(text, pos, match_len):
    """Best-effort classification of the em-dash by syntactic role.
    Returns (category, suggested_replacement)."""
    before = text[max(0, pos - 120):pos]
    after = text[pos + match_len:pos + match_len + 120]

    # 1. Surrounded by digits — Scripture range or date range. Should be en-dash.
    if re.search(r'\d\s*$', before) and re.match(r'\s*\d', after):
        return ("numeric range (should be en-dash)", "en-dash (–)")

    # 2. End of paragraph / followed by quote-close / followed by nothing
    if re.match(r'\s*["\'"”’]?\s*$|^\s*\n\s*\n', after):
        return ("trailing (line-end)", "period (.) or ellipsis (...)")

    # 3. Look for a paired em-dash within next ~150 chars → parenthetical phrase
    paired = EMDASH_RE.search(after[:200])
    if paired:
        return ("parenthetical (paired em-dashes)", "commas or parentheses")

    # 4. Next clause starts with capital → likely sentence-break candidate
    if re.match(r'\s*[A-Z]', after):
        return ("clause break (next word capitalized)", "period (.) or semicolon (;)")

    # 5. Default: connecting two clauses
    return ("clause connector", "comma (,) or semicolon (;)")


def scan_file(filepath: Path):
    text = filepath.read_text()
    # Strip Markdown headings/bold/italic markers for the word count
    word_text = re.sub(r'[*_#`>\[\]\(\)!]', ' ', text)
    word_count = len(re.findall(r'\b\w+\b', word_text))

    findings = []
    for m in EMDASH_RE.finditer(text):
        pos = m.start()
        match_len = len(m.group())
        line_num = text[:pos].count('\n') + 1

        # Build a one-line context with the em-dash highlighted by «»
        ctx_start = max(0, pos - CONTEXT_CHARS)
        ctx_end = min(len(text), pos + match_len + CONTEXT_CHARS)
        before_ctx = text[ctx_start:pos].replace('\n', ' ').strip()
        after_ctx = text[pos + match_len:ctx_end].replace('\n', ' ').strip()
        context = f"{before_ctx} «{m.group()}» {after_ctx}"

        category, suggestion = classify(text, pos, match_len)
        findings.append({
            'line': line_num,
            'context': context,
            'category': category,
            'suggestion': suggestion,
        })

    return word_count, findings


def density_marker(per_1000):
    if per_1000 >= 15: return "🔴"
    if per_1000 >= 10: return "🟠"
    if per_1000 >= 5:  return "🟡"
    return "  "


def main():
    p = argparse.ArgumentParser(description="Em-dash density checker for long-form prose")
    p.add_argument("path", help="Directory containing the manuscript (.md files)")
    p.add_argument("--chapter", help="Filter to files whose name contains this string")
    p.add_argument("--summary", action="store_true", help="Density-only; no per-occurrence detail")
    p.add_argument("--max-detail", type=int, default=100, help="Cap detail lines per file (default 100)")
    p.add_argument("--out", help="Write report to file instead of stdout")
    args = p.parse_args()

    book_path = Path(args.path).expanduser().resolve()
    if not book_path.is_dir():
        print(f"Not a directory: {book_path}", file=sys.stderr)
        return 1

    files = sorted(book_path.glob("*.md"))
    files = [f for f in files if not any(s in f.name for s in SKIP_NAMES)]
    if args.chapter:
        files = [f for f in files if args.chapter.lower() in f.name.lower()]

    out = open(args.out, 'w') if args.out else sys.stdout
    def w(s=""): print(s, file=out)

    w("=" * 78)
    w(f"Em-dash density check: {book_path}")
    w(f"Threshold guide: 🟡 5-9 / 🟠 10-14 / 🔴 15+ em-dashes per 1,000 words")
    w("=" * 78)

    grand_total_em = 0
    grand_total_words = 0

    for filepath in files:
        word_count, findings = scan_file(filepath)
        density = (len(findings) / word_count * 1000) if word_count else 0
        grand_total_em += len(findings)
        grand_total_words += word_count

        marker = density_marker(density)
        w(f"\n{marker} {filepath.name}")
        w(f"   {len(findings):4d} em-dash / {word_count:5d} words = {density:5.1f} per 1,000")

        if not args.summary and findings:
            w("")
            for i, f in enumerate(findings[:args.max_detail], 1):
                w(f"   {i:3d}. Line {f['line']:4d}  [{f['category']}]")
                w(f"        → {f['suggestion']}")
                w(f"        {f['context']}")
            if len(findings) > args.max_detail:
                w(f"   ... and {len(findings) - args.max_detail} more (raise --max-detail to see all)")

    overall = (grand_total_em / grand_total_words * 1000) if grand_total_words else 0
    w("\n" + "=" * 78)
    w(f"TOTAL: {grand_total_em} em-dashes across {grand_total_words} words = {overall:.1f} per 1,000")
    w("=" * 78)

    if args.out:
        out.close()
        print(f"Report written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
