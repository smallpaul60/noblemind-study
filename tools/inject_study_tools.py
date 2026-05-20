#!/usr/bin/env python3
"""Inject the /assets/study-tools.js script tag into every chapter HTML
across all book directories.

Idempotent: skips files that already include the script.
Safe to re-run any time new chapter files are added.

Usage:
    python3 tools/inject_study_tools.py
"""

import re
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

SCRIPT_TAG = '<script src="/assets/study-tools.js" defer></script>'

# Book directories that contain chapter HTML files
BOOK_DIRS = [
    "ANewAndLivingWay",
    "A_Good_Name",
    "before-i-formed-you",
    "BridgeMoments",
    "CanTheseBonesLive",
    "ChangeTheMind_ChangeTheMan",
    "FromTheBeginning",
    "OneDayCloserToHome",
    "StrengthAndDignity",
    "TheCharacterNoOneCouldInvent",
    "TheGodWhoShowedUp",
    "TheLastWeekOfTheLamb",
    "TheLoveGodCallsUsTo",
    "ThroughTheValley",
    "WhyDoYouDelay",
    "WhyTheDivision",
]

# Files we never inject into (TOC pages, audio pages, etc.)
SKIP = {"audio.html"}


def inject(path: Path) -> bool:
    """Add the script tag before </body>. Returns True if file was modified."""
    text = path.read_text(encoding="utf-8")
    if "study-tools.js" in text:
        return False
    # Insert before the closing </body>
    new_text, n = re.subn(
        r"(\s*)</body>",
        f"\n  {SCRIPT_TAG}\n\\1</body>",
        text,
        count=1,
    )
    if n == 0:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main():
    total_files = 0
    total_modified = 0
    for book in BOOK_DIRS:
        book_path = PROJECT_DIR / book
        if not book_path.exists():
            print(f"  (skip — not found: {book})")
            continue
        for html in sorted(book_path.glob("*.html")):
            if html.name in SKIP:
                continue
            total_files += 1
            if inject(html):
                total_modified += 1
        print(f"  {book}")
    print(f"\nProcessed {total_files} files, modified {total_modified}.")


if __name__ == "__main__":
    main()
