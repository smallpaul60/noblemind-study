#!/usr/bin/env python3
"""Download ASV / BSB / YLT from scrollmapper, convert to flat array format
matching KJV.json (so existing study-tools.js code works identically), and
write to project root.

Idempotent. Run once or whenever scrollmapper updates.
"""
import json
import sys
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

# Map book name → number (KJV order, 1-66). Handles common name variants.
BOOK_NUM = {
    "Genesis":1,"Exodus":2,"Leviticus":3,"Numbers":4,"Deuteronomy":5,
    "Joshua":6,"Judges":7,"Ruth":8,
    "1 Samuel":9,"I Samuel":9,"1Samuel":9,
    "2 Samuel":10,"II Samuel":10,"2Samuel":10,
    "1 Kings":11,"I Kings":11,"1Kings":11,
    "2 Kings":12,"II Kings":12,"2Kings":12,
    "1 Chronicles":13,"I Chronicles":13,"1Chronicles":13,
    "2 Chronicles":14,"II Chronicles":14,"2Chronicles":14,
    "Ezra":15,"Nehemiah":16,"Esther":17,"Job":18,
    "Psalms":19,"Psalm":19,
    "Proverbs":20,"Ecclesiastes":21,
    "Song of Solomon":22,"Song of Songs":22,"Canticles":22,
    "Isaiah":23,"Jeremiah":24,"Lamentations":25,"Ezekiel":26,"Daniel":27,
    "Hosea":28,"Joel":29,"Amos":30,"Obadiah":31,"Jonah":32,
    "Micah":33,"Nahum":34,"Habakkuk":35,"Zephaniah":36,"Haggai":37,
    "Zechariah":38,"Malachi":39,
    "Matthew":40,"Mark":41,"Luke":42,"John":43,"Acts":44,"Romans":45,
    "1 Corinthians":46,"I Corinthians":46,"1Corinthians":46,
    "2 Corinthians":47,"II Corinthians":47,"2Corinthians":47,
    "Galatians":48,"Ephesians":49,"Philippians":50,"Colossians":51,
    "1 Thessalonians":52,"I Thessalonians":52,"1Thessalonians":52,
    "2 Thessalonians":53,"II Thessalonians":53,"2Thessalonians":53,
    "1 Timothy":54,"I Timothy":54,"1Timothy":54,
    "2 Timothy":55,"II Timothy":55,"2Timothy":55,
    "Titus":56,"Philemon":57,"Hebrews":58,"James":59,
    "1 Peter":60,"I Peter":60,"1Peter":60,
    "2 Peter":61,"II Peter":61,"2Peter":61,
    "1 John":62,"I John":62,"1John":62,
    "2 John":63,"II John":63,"2John":63,
    "3 John":64,"III John":64,"3John":64,
    "Jude":65,"Revelation":66,"Revelation of John":66,
}

SOURCES = [
    ("ASV", "https://raw.githubusercontent.com/scrollmapper/bible_databases/2025/formats/json/ASV.json"),
    ("BSB", "https://raw.githubusercontent.com/scrollmapper/bible_databases/2025/formats/json/BSB.json"),
    ("YLT", "https://raw.githubusercontent.com/scrollmapper/bible_databases/2025/formats/json/YLT.json"),
]

def convert(code, url):
    print(f"[{code}] downloading from {url}")
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    flat = []
    skipped_books = set()
    for book in data.get("books", []):
        name = book.get("name", "")
        bnum = BOOK_NUM.get(name)
        if not bnum:
            skipped_books.add(name)
            continue
        for ch in book.get("chapters", []):
            cnum = ch.get("chapter")
            for v in ch.get("verses", []):
                vnum = v.get("verse")
                text = (v.get("text") or "").strip()
                if not text or cnum is None or vnum is None: continue
                flat.append({"book": bnum, "chapter": cnum, "verse": vnum, "text": text})
    if skipped_books:
        print(f"[{code}] skipped books: {sorted(skipped_books)}")
    out_path = PROJECT / f"{code}.json"
    # Minified (no indent) to save bytes
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, separators=(",", ":"))
    size = out_path.stat().st_size
    print(f"[{code}] wrote {len(flat):,} verses to {out_path.name} ({size/1024/1024:.2f} MB)")

def main():
    for code, url in SOURCES:
        try:
            convert(code, url)
        except Exception as e:
            print(f"[{code}] FAILED: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
