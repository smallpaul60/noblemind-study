#!/usr/bin/env python3
"""Build a static full-text search index for every book in the catalog.

Walks each book directory, parses each chapter / preface / dedication /
appendix HTML file, extracts plain text, and writes a single
/search_index.json that the books.html search UI loads on demand.

Usage:
    python3 tools/build_search_index.py

Re-run any time chapters change. Output is search_index.json at the
project root.
"""

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT_DIR / "search_index.json"

# Per-book human title + thumbnail path used in search-result cards.
# (Extracted by hand from books.html so the index is self-contained.)
BOOKS = [
    ("ANewAndLivingWay", "A New and Living Way",
     "ANewAndLivingWay/cover_thumb.jpg"),
    ("A_Good_Name", "Your Name Means Everything: A Good Name",
     "A_Good_Name/cover_thumb.jpg"),
    ("before-i-formed-you", "Before I Formed You",
     "before-i-formed-you/cover_thumb.jpg"),
    ("BridgeMoments", "Bridge Moments",
     "BridgeMoments/cover_thumb.jpg"),
    ("CanTheseBonesLive", "Can These Bones Live?",
     "CanTheseBonesLive/cover_thumb.jpg"),
    ("ChangeTheMind_ChangeTheMan", "Change the Mind, Change the Man",
     "ChangeTheMind_ChangeTheMan/cover_thumb.jpg"),
    ("FromTheBeginning", "From the Beginning",
     "FromTheBeginning/cover_thumb.jpg"),
    ("OneDayCloserToHome", "One Day Closer to Home",
     "OneDayCloserToHome/cover_thumb.jpg"),
    ("StrengthAndDignity", "Your Name Means Everything: Strength and Dignity",
     "StrengthAndDignity/cover_thumb.jpg"),
    ("TheCharacterNoOneCouldInvent", "The Character No One Could Invent",
     "TheCharacterNoOneCouldInvent/cover_thumb.jpg"),
    ("TheGodWhoShowedUp", "The God Who Showed Up",
     "TheGodWhoShowedUp/cover_thumb.jpg"),
    ("TheLastWeekOfTheLamb", "The Last Week of the Lamb",
     "TheLastWeekOfTheLamb/cover_thumb.jpg"),
    ("TheLoveGodCallsUsTo", "The Love God Calls Us To",
     "TheLoveGodCallsUsTo/cover_thumb.jpg"),
    ("ThroughTheValley", "Through the Valley",
     "ThroughTheValley/cover_thumb.jpg"),
    ("WhyDoYouDelay", "Why Do You Delay?",
     "WhyDoYouDelay/cover_thumb.jpg"),
    ("WhyTheDivision", "Why the Division Among Brethren?",
     "WhyTheDivision/cover_thumb.jpg"),
]

# Files NOT to index inside a book directory (TOCs, audio pages, etc.)
SKIP_FILES = {"index.html", "audio.html"}


def extract_chapter_meta(soup, fallback_filename):
    """Pull the chapter label + title from the page header."""
    label = ""
    title = ""

    # Try a <header> with a chapter-num + h1 pattern (TGWSU / TLGCUT style)
    header = soup.find("header")
    if header:
        num_el = header.find(class_="chapter-num") or header.find(class_="chapter-label")
        h1 = header.find("h1")
        if num_el:
            label = num_el.get_text(strip=True)
        if h1:
            title = h1.get_text(strip=True)

    # Fall back to the document <title>
    if not title:
        t = soup.find("title")
        if t:
            title = t.get_text(strip=True).split("|")[0].strip()

    # Fall back to the filename as a label
    if not label:
        m = re.search(r"chapter[-_]?(\d+)", fallback_filename)
        if m:
            label = f"Chapter {int(m.group(1))}"
        elif "preface" in fallback_filename:
            label = "Preface"
        elif "dedication" in fallback_filename or "inscription" in fallback_filename:
            label = "Dedication"
        elif "appendix" in fallback_filename:
            label = "Appendix"
        elif "introduction" in fallback_filename:
            label = "Introduction"
        elif "conclusion" in fallback_filename:
            label = "Conclusion"
        elif "foreword" in fallback_filename:
            label = "Foreword"
        elif "authors-note" in fallback_filename:
            label = "Author's Note"
        elif "front-matter" in fallback_filename:
            label = "Front Matter"
        elif "scripture-index" in fallback_filename:
            label = "Scripture Index"

    return label, title


def extract_body_text(soup):
    """Pull readable text out of the chapter content area."""
    # Prefer the explicit content container most book templates use
    container = (soup.find(class_="content")
                 or soup.find(class_="glass-page-inner")
                 or soup.find("article")
                 or soup.body)
    if not container:
        return ""

    # Drop nav, scripts, styles, footers, and the chapter select dropdown
    for el in container.find_all(
        ["nav", "script", "style", "footer", "select", "button"]
    ):
        el.decompose()

    text = container.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text


def collect_book_entries(book_dir, book_title, thumb):
    book_path = PROJECT_DIR / book_dir
    if not book_path.exists():
        return []

    entries = []
    for html_path in sorted(book_path.glob("*.html")):
        if html_path.name in SKIP_FILES:
            continue
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
        label, title = extract_chapter_meta(soup, html_path.name)
        text = extract_body_text(soup)
        if not text or len(text) < 100:
            # Skip near-empty pages (e.g. TOCs that slipped past the SKIP_FILES filter)
            continue
        entries.append({
            "book": book_title,
            "thumb": thumb,
            "label": label or "",
            "title": title or html_path.stem,
            "url": f"{book_dir}/{html_path.name}",
            "text": text,
        })
    return entries


def main():
    print("Building search index...")
    all_entries = []
    for book_dir, book_title, thumb in BOOKS:
        entries = collect_book_entries(book_dir, book_title, thumb)
        all_entries.extend(entries)
        total_chars = sum(len(e["text"]) for e in entries)
        print(f"  {book_dir:32s}  {len(entries):3d} pages, {total_chars:,} chars")

    OUTPUT.write_text(json.dumps(all_entries, ensure_ascii=False), encoding="utf-8")
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"\nWrote {OUTPUT.relative_to(PROJECT_DIR)}  ({len(all_entries)} pages, {size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
