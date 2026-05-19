#!/usr/bin/env python3
"""Run the full per-chapter QA gate.

Runs the four NobleMind Press verifiers in sequence against a single book
(optionally a single chapter):

  1. verify_scripture.py   — NASB blockquote accuracy vs Bolls.Life
  2. check_language.py     — denominational / theological / churchy jargon
  3. verify_greek.py       — italicized Greek transliterations vs TR text
  4. verify_counts.py      — word counts, verse counts, chapter/attribute
                             counts vs the per-book outline

Each tool's full output is forwarded to stdout so you can inspect findings.
A final consolidated summary reports PASS/FAIL per stage.

Usage:
    python3 tools/qa_chapter.py TheLoveGodCallsUsTo --chapter 10
    python3 tools/qa_chapter.py TheLoveGodCallsUsTo            # all chapters
    python3 tools/qa_chapter.py --all                          # every book
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

STAGES = [
    ("Scripture (NASB)", "verify_scripture.py"),
    ("Language",         "check_language.py"),
    ("Greek (TR)",       "verify_greek.py"),
    ("Counts",           "verify_counts.py"),
]


def run_stage(script_name, book, chapter):
    cmd = [sys.executable, str(SCRIPT_DIR / script_name)]
    if book:
        cmd.append(book)
    if chapter is not None:
        cmd += ["--chapter", str(chapter)]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.stdout, proc.returncode


# Parse the "OVERALL: ... issues" / "... unverified" / "... flags" lines that
# each tool prints. We don't try to be clever — just pull the totals.
SUMMARY_PATTERNS = {
    "verify_scripture.py": re.compile(
        r"OVERALL:\s*(\d+)\s+quotes?,\s*(\d+)\s+matched,\s*(\d+)\s+issues?"
    ),
    "check_language.py": re.compile(
        r"OVERALL:\s*(\d+)\s+flags?"
    ),
    "verify_greek.py": re.compile(
        r"OVERALL:\s*(\d+)\s+candidates?,\s*(\d+)\s+verified,\s*(\d+)\s+unverified"
    ),
    "verify_counts.py": re.compile(
        r"OVERALL:\s*(\d+)\s+claims?,\s*(\d+)\s+mismatch(?:es)?,\s*(\d+)\s+warnings?"
    ),
}


def stage_status(script_name, output):
    pat = SUMMARY_PATTERNS[script_name]
    m = pat.search(output)
    if not m:
        return "?", "no summary parsed"

    if script_name == "verify_scripture.py":
        total, matched, issues = map(int, m.groups())
        if total == 0:
            return "n/a", "no quotes found"
        if issues == 0:
            return "PASS", f"{matched}/{total} matched, 0 issues"
        return "REVIEW", f"{matched}/{total} matched, {issues} issue(s) — partial quotes are usually false positives"

    if script_name == "check_language.py":
        (flags,) = map(int, m.groups())
        if flags == 0:
            return "PASS", "0 flags"
        return "REVIEW", f"{flags} flag(s)"

    if script_name == "verify_greek.py":
        total, verified, unverified = map(int, m.groups())
        if total == 0:
            return "n/a", "no Greek candidates"
        if unverified == 0:
            return "PASS", f"{verified}/{total} verified"
        return "FAIL", f"{verified}/{total} verified, {unverified} unverified"

    if script_name == "verify_counts.py":
        total, mismatches, warnings = map(int, m.groups())
        if total == 0 and warnings == 0:
            return "n/a", "no verifiable count claims"
        if mismatches == 0:
            suffix = f", {warnings} warning(s)" if warnings else ""
            return "PASS", f"{total} claim(s) clean{suffix}"
        return "FAIL", f"{mismatches} mismatch(es) of {total} claim(s)"

    return "?", "unknown stage"


def main():
    ap = argparse.ArgumentParser(description="Run NobleMind per-chapter QA")
    ap.add_argument("book", nargs="?", help="Book directory")
    ap.add_argument("--chapter", type=int, help="Chapter number")
    ap.add_argument("--all", action="store_true", help="Scan all configured books")
    args = ap.parse_args()

    if not args.book and not args.all:
        ap.error("specify a book directory, or pass --all")

    book = None if args.all else args.book

    print("#" * 60)
    print("# NobleMind Press — Chapter QA")
    if book:
        print(f"# Book: {book}" + (f" / Chapter {args.chapter}" if args.chapter else ""))
    else:
        print("# Scope: all configured books")
    print("#" * 60)

    results = []
    for label, script in STAGES:
        print(f"\n\n{'#' * 60}")
        print(f"# STAGE: {label}  ({script})")
        print("#" * 60)
        output, _ = run_stage(script, book, args.chapter)
        status, detail = stage_status(script, output)
        results.append((label, status, detail))

    print(f"\n\n{'=' * 60}")
    print("QA SUMMARY")
    print("=" * 60)
    width = max(len(l) for l, _, _ in results)
    overall_fail = False
    for label, status, detail in results:
        marker = {"PASS": "  ", "REVIEW": "??", "FAIL": "!!", "n/a": "--", "?": "??"}.get(status, "??")
        print(f"  [{marker}] {label.ljust(width)}  {status:7}  {detail}")
        if status == "FAIL":
            overall_fail = True

    print("=" * 60)
    if overall_fail:
        print("Overall: FAIL — at least one stage has unverified findings.")
        sys.exit(1)
    has_review = any(r[1] == "REVIEW" for r in results)
    if has_review:
        print("Overall: REVIEW — pass eyeball over the flagged items above.")
        sys.exit(0)
    print("Overall: PASS — all stages clean.")
    sys.exit(0)


if __name__ == "__main__":
    main()
