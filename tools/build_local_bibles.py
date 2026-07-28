#!/usr/bin/env python3
"""
Prepare the local Bible data files the Study Tool searches offline.

Two jobs:

1. STRIP THE APOCRYPHA FROM KJV.json.
   The upstream Bolls KJV ships WITH the Apocrypha (81 books, 37,247 verses).
   This keeps the 66-book canon only, removing books 67-88 plus the Additions
   to Esther (Est 10:4-13 and Est 11-16), which are the Apocryphal tail of an
   otherwise canonical book.

2. CARRY THE 16 DISPUTED VERSES INTO ASV.json AND BSB.json, MARKED.
   The ASV and BSB translators judged 16 verses to be later additions and omit
   them. A word search over a text with holes is not exhaustive, and a student
   searching "believest with all thine heart" would be told Acts 8:37 does not
   exist. So the KJV reading is carried in and MARKED:

       variant = "disputed"   source = "KJV"

   Marked verses are NOT that translation's text and the UI must never present
   them as though they were — it shows the KJV wording and says the verse is
   absent from the manuscripts underlying the chosen translation.

   YLT already contains all 16 and needs nothing. KJV has them natively.

All four files end at 31,102 verses, the standard canonical count. That equality
is the oracle: if any file is off, the script fails rather than writing.

Idempotent — re-running detects already-carried verses and skips them. Re-run
this AFTER tools/convert_bible_translations.py, which regenerates ASV/BSB/YLT
from scrollmapper and would otherwise drop the carried verses.

Usage:  python3 tools/build_local_bibles.py [--force-download]
"""

import json
import os
import re
import shutil
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Cache lives OUTSIDE the repo on purpose: the web root is the repo root, so a
# 37 MB with-Apocrypha KJV cached under tools/ would deploy publicly by default.
CACHE = os.path.expanduser("~/.cache/noblemind-bibles")
CANONICAL_VERSE_COUNT = 31102

# The 16 verses the ASV and BSB omit as later additions. (book, chapter, verse)
# using the standard 1-66 numbering.
DISPUTED = [
    (40, 17, 21), (40, 18, 11), (40, 23, 14),
    (41, 7, 16), (41, 9, 44), (41, 9, 46), (41, 11, 26), (41, 15, 28),
    (42, 17, 36), (42, 23, 17),
    (43, 5, 4),
    (44, 8, 37), (44, 15, 34), (44, 24, 7), (44, 28, 29),
    (45, 16, 24),
]

# Translations that need the 16 carried in. KJV and YLT already have them.
NEEDS_CARRY = ["ASV", "BSB"]


def strip_strongs(text):
    """Remove <S>1234</S> tags entirely — leaving the tags to a generic
    tag-stripper would drop the brackets but strand the numbers in the prose."""
    text = re.sub(r"<S>\d+</S>", "", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_kjv(force=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "KJV.json")
    if os.path.exists(path) and not force:
        print(f"  KJV source: cached {path}")
    else:
        url = "https://bolls.life/static/translations/KJV.json"
        print(f"  KJV source: downloading {url} ...")
        urllib.request.urlretrieve(url, path)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def is_canonical(v):
    """True for the 66-book canon, excluding the Apocryphal tail of Esther."""
    if v["book"] > 66:
        return False
    if v["book"] == 17:                       # Esther
        if v["chapter"] > 10:
            return False                      # Est 11-16 = Additions
        if v["chapter"] == 10 and v["verse"] > 3:
            return False                      # Est 10:4-13 = Additions
    return True


def load(name):
    with open(os.path.join(REPO, f"{name}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def write(name, data):
    out = os.path.join(REPO, f"{name}.json")
    if os.path.exists(out):
        backup = out + ".backup"              # *.backup* is deploy-excluded
        if not os.path.exists(backup):
            shutil.copy2(out, backup)
            print(f"    backed up -> {os.path.basename(backup)}")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"    wrote {name}.json ({os.path.getsize(out) / 1048576:.1f} MB, {len(data)} verses)")


def check(name, data):
    if len(data) != CANONICAL_VERSE_COUNT:
        sys.exit(f"FAIL: {name} has {len(data)} verses, expected {CANONICAL_VERSE_COUNT}. Nothing written.")
    books = {v["book"] for v in data}
    if books != set(range(1, 67)):
        sys.exit(f"FAIL: {name} covers {len(books)} books, expected 66. Nothing written.")
    missing = [k for k in DISPUTED
               if not any(v["book"] == k[0] and v["chapter"] == k[1] and v["verse"] == k[2] for v in data)]
    if missing:
        sys.exit(f"FAIL: {name} is missing {len(missing)} disputed verses. Nothing written.")


def build():
    force = "--force-download" in sys.argv

    # ---- 1. KJV: strip the Apocrypha ---------------------------------------
    print("KJV — stripping the Apocrypha:")
    kjv_raw = fetch_kjv(force)
    kjv = [v for v in kjv_raw if is_canonical(v)]
    print(f"    {len(kjv_raw)} verses in -> {len(kjv)} canonical "
          f"({len(kjv_raw) - len(kjv)} Apocryphal removed)")
    check("KJV", kjv)

    # KJV text (Strong's stripped) is the source for the carried verses.
    kjv_text = {(v["book"], v["chapter"], v["verse"]): strip_strongs(v["text"])
                for v in kjv}

    # ---- 2. Carry the 16 into ASV and BSB ----------------------------------
    outputs = {"KJV": kjv}
    for name in NEEDS_CARRY:
        print(f"\n{name} — carrying in the disputed verses:")
        data = load(name)
        have = {(v["book"], v["chapter"], v["verse"]) for v in data}
        added = 0
        for key in DISPUTED:
            if key in have:
                continue                       # idempotent: already carried
            text = kjv_text.get(key)
            if not text:
                sys.exit(f"FAIL: {key} has no KJV text to carry. Nothing written.")
            b, c, v = key
            data.append({"book": b, "chapter": c, "verse": v, "text": text,
                         "variant": "disputed", "source": "KJV"})
            added += 1
        data.sort(key=lambda x: (x["book"], x["chapter"], x["verse"]))
        print(f"    {len(data) - added} verses in -> {len(data)} ({added} carried, marked disputed)")
        check(name, data)
        outputs[name] = data

    # ---- 3. YLT: verify only, it already has all 16 -------------------------
    print("\nYLT — verifying (already complete, not modified):")
    ylt = load("YLT")
    check("YLT", ylt)
    print(f"    {len(ylt)} verses, all 16 disputed present. No change needed.")

    # ---- 4. Write ------------------------------------------------------------
    print(f"\nOracle OK: every translation = {CANONICAL_VERSE_COUNT} verses across 66 books.")
    print("\nWriting:")
    for name, data in outputs.items():
        write(name, data)

    print("\nRemember: bump CACHE_NAME in sw.js — these are cache-first assets.")


if __name__ == "__main__":
    build()
