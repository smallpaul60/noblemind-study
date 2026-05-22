#!/usr/bin/env python3
"""Harvest Greek/Hebrew transliterations from chapter HTML and propose
Strong's-number mappings for review.

Reads:
  - assets/study-tools.js    (existing STRONGS_LOOKUP — skip these)
  - BDBT.json                (14,197 Strong's entries with transliterations)
  - <book>/chapter-*.html    (every book's chapters)

Outputs a ranked report:
  candidate word → proposed Strong's number, lexeme, short definition
                   plus frequency across books and first occurrence

Usage:
    python3 tools/find_greek_hebrew_terms.py
    python3 tools/find_greek_hebrew_terms.py --include-singletons
    python3 tools/find_greek_hebrew_terms.py --include-phrases  # also scan multi-word italics
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BDBT_PATH = ROOT / "BDBT.json"
JS_PATH = ROOT / "assets" / "study-tools.js"

BOOK_DIRS = [
    "TheLoveGodCallsUsTo", "FromTheBeginning", "BridgeMoments", "ANewAndLivingWay",
    "ChangeTheMind_ChangeTheMan", "TheLastWeekOfTheLamb", "TheGodWhoShowedUp",
    "WhyTheDivision", "WhyDoYouDelay", "CanTheseBonesLive", "OneDayCloserToHome",
    "before-i-formed-you", "A_Good_Name", "StrengthAndDignity", "ThroughTheValley",
    "TheCharacterNoOneCouldInvent",
]

# English emphasis words we never want to flag, even if they look Greek-ish
STOP_WORDS = set("""
the a an and or but for nor so yet to of in on at by with from up out as is are was were be been being
have has had do does did this that these those it its his her she he their them they we us our you your my mine
not no yes when where why how what who which whose whom if then else than because since while until
all any some none every each both either neither such same other different new own once before after about
will would shall should can could may might must ought said see saw seen go went gone come came
make made take took taken give gave given know knew known think thought let still also too then now
only just very really truly more most less least almost nearly maybe perhaps even ever never always sometimes
toward towards through throughout against among amid amidst between within without inside outside
big small good bad great old young high low long short hot cold open closed dead alive
love loved kind patient hope faith trust grace truth peace joy life death light dark good evil sin sins
father mother brother sister son daughter friend friends enemy enemies king kings priest priests prophet prophets servant servants
god lord jesus christ spirit holy heaven hell day night word words name names house houses
believer believers church churches saint saints disciple disciples apostle apostles into first today
plus right person forever perfect seed ours mind found becomes long-tempered fitting easily provoked
bears believed partial complete method formed real impossible buried response second third torn living
richly away whether burden vehicle structure recipients anyone ordered joined became imperishable eternal producing
ambition despite describe invent strong weak ruin lovingkindness kindness cruel forgetting zealous jealousy envy
glad bitter ahead behind nowhere therefore knowledge appeared chairos chronos
hyperbole hyperboles especially seriously yet still even however moreover furthermore consequently
nice short-tempered new-and-living scaffolding analogous figurative literal
parallel parallels precise precision exact picture pictures image images
makros thumos temper anger passion heat
""".split())

# Words I know are book titles or proper nouns that BDBT will match but shouldn't auto-link
SKIP_AS_PROPER_NOUN = set("""
apollos isaiah jeremiah daniel ezekiel matthew mark luke john peter paul james
moses abraham isaac jacob joseph david solomon noah adam eve eden
egypt israel judah jerusalem bethlehem nazareth galilee jordan
satan devil pharaoh caesar herod pilate
ophrah midian babylon
""".split())


def strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def normalize(s: str) -> str:
    """Lowercase, strip diacritics, keep letters and apostrophe."""
    s = strip_diacritics(s.lower())
    s = re.sub(r"[^a-z']", "", s)
    return s


def match_key(s: str) -> str:
    """Aggressive normalization for matching purposes.
    Greek upsilon ↔ u; drop apostrophes (alef/ayin markers)."""
    n = normalize(s)
    return n.replace("y", "u").replace("'", "")


def load_already_mapped() -> set:
    text = JS_PATH.read_text()
    m = re.search(r"const STRONGS_LOOKUP = \{(.*?)\};", text, re.DOTALL)
    if not m:
        return set()
    keys = re.findall(r'"([^"]+)"\s*:\s*"(G\d+|H\d+)"', m.group(1))
    return {match_key(k) for k, _ in keys}


def build_bdbt_index():
    """Map every BDBT entry's transliteration variants → list of entry dicts."""
    with open(BDBT_PATH) as f:
        data = json.load(f)
    idx = defaultdict(list)
    for e in data:
        translit = (e.get("transliteration") or "").strip()
        topic = (e.get("topic") or "").strip()
        if not translit or not topic:
            continue
        entry = {
            "topic": topic,
            "lexeme": e.get("lexeme", "") or "",
            "translit": translit,
            "short_def": (e.get("short_definition") or "")[:50],
        }
        # Several keys to absorb common variation
        for k in {match_key(translit), normalize(translit), normalize(translit).replace("'", "")}:
            if k:
                idx[k].append(entry)
    return idx


EM_RE = re.compile(r"<em[^>]*>([^<]+)</em>|<i[^>]*>([^<]+)</i>", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-zÀ-ÿ']+")


def harvest(include_phrases: bool):
    counter = Counter()
    contexts = {}
    for book in BOOK_DIRS:
        bp = ROOT / book
        if not bp.exists():
            continue
        for html in sorted(bp.glob("chapter-*.html")):
            text = html.read_text(encoding="utf-8", errors="ignore")
            for m in EM_RE.finditer(text):
                content = (m.group(1) or m.group(2) or "").strip().rstrip(".,;:!?")
                if not content:
                    continue
                # Single-word italics — primary signal
                if " " not in content:
                    candidates = [content]
                elif include_phrases:
                    # Multi-word italics — each word becomes a candidate
                    candidates = WORD_RE.findall(content)
                else:
                    continue
                for raw in candidates:
                    if len(raw) < 3 or len(raw) > 30:
                        continue
                    counter[raw] += 1
                    contexts.setdefault(raw, f"{book}/{html.name}")
    return counter, contexts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-singletons", action="store_true",
                        help="Show candidates that appear only once (noisier).")
    parser.add_argument("--include-phrases", action="store_true",
                        help="Also scan inside multi-word italics word-by-word.")
    parser.add_argument("--show-no-match", action="store_true",
                        help="Also list candidates that didn't match BDBT.")
    args = parser.parse_args()

    print("Loading BDBT…")
    bdbt = build_bdbt_index()
    print(f"  → {sum(len(v) for v in bdbt.values()):,} entries indexed under {len(bdbt):,} keys.")

    already = load_already_mapped()
    print(f"  → {len(already):,} normalized keys already in STRONGS_LOOKUP.")

    counter, contexts = harvest(include_phrases=args.include_phrases)
    print(f"  → {sum(counter.values()):,} italic occurrences, {len(counter):,} distinct words.\n")

    # Categorize
    matched = []  # (word, count, [entries], first_seen)
    unmatched = []

    for word, count in counter.most_common():
        norm = normalize(word)
        if not norm or norm in STOP_WORDS or norm in SKIP_AS_PROPER_NOUN:
            continue
        mkey = match_key(word)
        if not mkey or mkey in already:
            continue
        entries = bdbt.get(mkey) or bdbt.get(mkey.replace("'", ""))
        if entries:
            matched.append((word, count, entries[:3], contexts[word]))
        else:
            unmatched.append((word, count, contexts[word]))

    print("=" * 80)
    print(f"NEW MATCHES — {len(matched)} candidates with a confident Strong's mapping")
    print("=" * 80)
    strongs_label = "Strong's"
    print(f"{'count':>5}  {'transliteration':25}  {strongs_label:9}  {'lexeme':15}  short def")
    print("-" * 80)
    for word, count, entries, ctx in matched:
        if count < 2 and not args.include_singletons:
            continue
        e = entries[0]
        print(f"{count:5}× {word:25}  {e['topic']:9}  {e['lexeme']:15}  {e['short_def']}")
        if len(entries) > 1:
            for alt in entries[1:]:
                print(f"      {'':25}  also {alt['topic']:5}  {alt['lexeme']:15}  {alt['short_def']}")
        print(f"      first seen: {ctx}")

    print()
    print("=" * 80)
    print(f"Already-mapped + stop-listed terms filtered out.")
    print(f"Unmatched candidates: {len(unmatched)} (likely English emphasis or proper nouns).")
    if args.show_no_match:
        print(f"\nUnmatched (sorted by frequency):")
        for word, count, ctx in unmatched:
            if count < 2 and not args.include_singletons:
                continue
            print(f"  {count:3}× {word:25}  ({ctx})")


if __name__ == "__main__":
    main()
