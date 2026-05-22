#!/usr/bin/env python3
"""Generate "Gems of the Original Languages" — a living Hebrew/Greek
word-study companion to the Noble Mind Press books.

Reads:
  - assets/study-tools.js     STRONGS_LOOKUP (the curated transliteration→Strong's map)
  - BDBT.json                  scholarly transliteration + definition for every Strong's entry
  - <book>/chapter-*.html      every chapter — for verbatim excerpts where each word is taught

Writes:
  - WordStudies/index.html         cover + intro + theme grid + nav
  - WordStudies/preface.html       about the book + methodology
  - WordStudies/themes/*.html      one page per theme
  - WordStudies/lexicon.html       full A–Z lexicon with anchor IDs
  - WordStudies/by-strongs.html    same words sorted by Strong's number

Re-runnable. Adds new words automatically as the books grow.
"""
import html as html_mod
import json
import re
import sys
import unicodedata
from collections import defaultdict, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "WordStudies"
JS_PATH = ROOT / "assets" / "study-tools.js"
BDBT_PATH = ROOT / "BDBT.json"

BOOK_DIRS = [
    "TheLoveGodCallsUsTo", "FromTheBeginning", "BridgeMoments", "ANewAndLivingWay",
    "ChangeTheMind_ChangeTheMan", "TheLastWeekOfTheLamb", "TheGodWhoShowedUp",
    "WhyTheDivision", "WhyDoYouDelay", "CanTheseBonesLive", "OneDayCloserToHome",
    "before-i-formed-you", "A_Good_Name", "StrengthAndDignity", "ThroughTheValley",
    "TheCharacterNoOneCouldInvent",
]

# Pretty book titles for citation
BOOK_TITLES = {
    "TheLoveGodCallsUsTo": "The Love God Calls Us To",
    "FromTheBeginning": "From the Beginning",
    "BridgeMoments": "Bridge Moments",
    "ANewAndLivingWay": "A New and Living Way",
    "ChangeTheMind_ChangeTheMan": "Change the Mind, Change the Man",
    "TheLastWeekOfTheLamb": "The Last Week of the Lamb",
    "TheGodWhoShowedUp": "The God Who Showed Up",
    "WhyTheDivision": "Why the Division Among Brethren",
    "WhyDoYouDelay": "Why Do You Delay?",
    "CanTheseBonesLive": "Can These Bones Live?",
    "OneDayCloserToHome": "One Day Closer to Home",
    "before-i-formed-you": "Before I Formed You",
    "A_Good_Name": "A Good Name",
    "StrengthAndDignity": "Strength and Dignity",
    "ThroughTheValley": "Through the Valley",
    "TheCharacterNoOneCouldInvent": "The Character No One Could Invent",
}

# ─────────────────────────────────────────────────────────────────────────────
# Themes — curated. Each Strong's number can appear in multiple themes.
# ─────────────────────────────────────────────────────────────────────────────

THEMES = OrderedDict([
    ("names-of-god", {
        "title": "The Names of God",
        "subtitle": "What God reveals about Himself through the names He answers to",
        "intro": (
            "The Old Testament does not introduce God by abstract attributes — it introduces "
            "Him by name, and each name is given in a specific moment when His character has "
            "to be seen. Elohim creates. Yahweh covenants. El Shaddai sustains. "
            "Jehovah-Jireh provides where the knife was already raised. The New Testament names "
            "do not replace these — they fulfill them. Kyrios is Yahweh in Greek. Christos is "
            "the long-expected Anointed. Abba is the most intimate Aramaic word a Hebrew "
            "child could speak."
        ),
        "words": [
            "H430", "H3068", "H7706", "H7965", "H7200", "H7495", "H5251",
            "H8033", "H6664", "H7462", "H6005",
            "G5", "G2241", "G2962", "G5547",
        ],
    }),
    ("word-spirit-breath", {
        "title": "The Word, the Spirit, and the Breath",
        "subtitle": "The same pattern from Eden to Pentecost",
        "intro": (
            "From Genesis 2 forward, life follows a pattern: the body is formed first; then "
            "the breath is given. The Hebrew ruach and neshamah, the Greek pneuma and pnoe — "
            "these are not separate ideas but one observation, traced through every fresh "
            "moment of life in Scripture. The Word (logos) provides the structure; the Spirit "
            "(pneuma) gives the life. Bara — to create — is the verb behind both."
        ),
        "words": [
            "G3056", "G4151", "G4154", "G4157", "G1720",
            "H7307", "H5397", "H5301", "H1254", "H1961",
            "H2377", "H6485", "H7121",
        ],
    }),
    ("love", {
        "title": "Love and Its Companions",
        "subtitle": "The fifteen attributes of 1 Corinthians 13 — and the Hebrew chesed behind them",
        "intro": (
            "First Corinthians 13 is not abstract sentiment. Each clause is a different Greek "
            "verb or noun, each carrying its own definite meaning. Makrothumeo: a long fuse "
            "before anger. Chresteuomai: actively useful kindness. Zelos: jealousy or zeal — "
            "the same root, two directions. Stego: covering, bearing in silence. Hypomeno: "
            "remaining under load. The Hebrew chesed sits behind all of it — the steadfast "
            "loving-kindness God shows when He has no obligation to do so."
        ),
        "words": [
            "G26", "G25", "G3114", "G3117", "G2372",
            "G5541", "G5543", "G2206", "G2205", "G4068", "G5448",
            "G807", "G4976", "G3049", "G4722", "G3306",
            "G5278", "G5281", "G3947", "G3948", "G5046",
            "G4100", "G4103", "G1679",
            "H2617", "H6187",
        ],
    }),
    ("repentance-renewed-mind", {
        "title": "Repentance and the Renewed Mind",
        "subtitle": "Not regret — a fundamental change of how a person thinks",
        "intro": (
            "Metanoia is the New Testament word for repentance, and it is not the same as "
            "metamelomai — which is regret, the feeling of being sorry. Metanoia is meta + nous: "
            "an after-mind, a turned mind, a mind made new. It belongs in the same family of "
            "verbs as metamorphoo (transformed by the renewing of your mind), anakainosis "
            "(renewing), and ananeoo (made fresh). What it is not is mere remorse. What it "
            "is is a different intellect altogether."
        ),
        "words": [
            "G3341", "G3338", "G3563", "G3339", "G342", "G365",
            "G5426", "G3154", "G4645", "G539", "G1901", "G4649",
            "G3591", "G2666", "G1380",
        ],
    }),
    ("faith-hope-endurance", {
        "title": "Faith, Hope, and Endurance",
        "subtitle": "The verbs that hold the believer in place when the storm is loud",
        "intro": (
            "Hupomeno does not mean to grit one's teeth and bear it. It means to stay under "
            "the load that is on you because you know what produces. Pisteuo is not the "
            "first time you say yes — it is the continuous tense of trusting. Dioko is to "
            "pursue something the way an enemy would pursue you — wholehearted, sustained. "
            "Aphorao is what the writer of Hebrews tells us to do: fix the eyes off everything "
            "else and onto Jesus."
        ),
        "words": [
            "G4100", "G4103", "G1679",
            "G5278", "G5281", "G3306",
            "G1377", "G872", "G3973", "G3525",
            "G2675", "G4648", "G5343", "G3996", "G2390",
            "G2212", "G1573", "H7291",
        ],
    }),
    ("holiness-grace-praise", {
        "title": "Holiness, Grace, and Praise",
        "subtitle": "The vocabulary of standing before God",
        "intro": (
            "Hagios is the Greek word both for holiness and for the people who belong to a "
            "holy God — the saints. Charis is not earned favor; it is the unearned gift of "
            "God showing kindness where He has no obligation. Amen — borrowed straight from "
            "the Hebrew — is a verb of standing firm. Hosanna is the cry of a people who have "
            "waited too long: save now."
        ),
        "words": [
            "G40", "G5485", "G4678", "G281", "G5614",
            "G3842", "G4862", "G5456",
            "G1577", "G3954", "G5463", "G1941",
        ],
    }),
    ("time-and-eternal", {
        "title": "Time and the Eternal",
        "subtitle": "Two kinds of time, and the moment that breaks through",
        "intro": (
            "Greek has two words for time. Chronos is the clock. Kairos is the appointed "
            "moment — the precise hour the door opens. Skene is the tent — Israel's "
            "tabernacle, but also (in 2 Cor 5) the body the believer presently lives in. "
            "Kainos is new in kind. Neos is new in time. Atmis is a vapor that appears for "
            "a little while and then is gone. Telos is the end, but in the sense of the "
            "goal that everything has been moving toward."
        ),
        "words": [
            "G2540", "G2250", "G4340", "G822",
            "G4633", "G4372", "G2537", "G3501", "G5056",
            "G1805", "G4639",
        ],
    }),
    ("lords-prayer", {
        "title": "The Lord's Prayer",
        "subtitle": "A few unusual words in the prayer that Jesus taught",
        "intro": (
            "Three of the Greek words in the Lord's Prayer are unusual enough to deserve "
            "their own entry. Epiousios — the daily bread word — appears almost nowhere else "
            "in surviving Greek literature, and its precise sense has been debated since "
            "Jerome. Peirasmos — the testing — is the same word James uses when he says God "
            "tempts no one. Anaideia — shamelessness — is the trait of the friend at "
            "midnight in the parable Luke pairs with the Prayer."
        ),
        "words": ["G1967", "G3986", "G335", "G4342"],
    }),
    ("sin-guilt-confession", {
        "title": "Sin, Guilt, and Confession",
        "subtitle": "Words for what is broken and how it gets named",
        "intro": (
            "Homologeo is to say the same thing as God says — to confess is to agree. "
            "Adikia is unrighteousness. Asham (the Hebrew) is guilt, but it is also the "
            "specific Levitical sacrifice the guilty bring. Apate is deceit — the friendly "
            "kind that disguises itself. Skleruno is what happens to a heart that keeps "
            "refusing: it hardens."
        ),
        "words": [
            "G93", "G3670", "G3639", "G539", "G3154", "G4645", "G3996",
            "H817", "G692",
        ],
    }),
    ("way-and-walk", {
        "title": "The Way and the Walk",
        "subtitle": "Old Testament verbs of moving with God",
        "intro": (
            "Halak is the Hebrew verb for walking, and the Old Testament uses it to mean "
            "the whole life. Enoch walked with God. Noah walked with God. Derek is the road "
            "itself — the way that is chosen. Nagash is to approach. Qarov is to be near. "
            "These are not abstract spiritual ideas; they are the physical verbs of moving "
            "toward the One who first moved toward us."
        ),
        "words": [
            "H1980", "H1870", "H5066", "H7138", "H8104", "H2596",
            "G3611", "G3809", "G1128", "G4342",
            "G907", "G939", "H2142", "H8085",
        ],
    }),
    ("last-week-lamb", {
        "title": "The Last Week and the Lamb",
        "subtitle": "Words from the Passion and the Passover that anchors it",
        "intro": (
            "The Last Week of Jesus's life lands in the words Israel had been using since "
            "Exodus. Seh — the Passover lamb. Ayil — the ram caught in the thicket. "
            "Arbayim — \"between the two evenings,\" the precise hour the lamb is killed. "
            "Then in the Greek: paradidomi — handed over. Mastigoo — scourged. Tetelestai — "
            "It is finished. Eli, Eli, lama — the Aramaic cry from the cross."
        ),
        "words": [
            "H7716", "H352", "H6153", "H639", "H4055", "H6030", "H817", "H4899",
            "G3860", "G3146", "G5055", "G3947", "G3948",
            "G2241", "G2982",
        ],
    }),
    ("body-soul-whole-person", {
        "title": "Body, Soul, and the Whole Person",
        "subtitle": "How Scripture talks about who we are",
        "intro": (
            "Scripture's anthropology is integrated. Sarx and psyche — flesh and soul — are "
            "not opposed parts of a person but different angles on the same one. Iaomai is "
            "to heal — sometimes physically, sometimes more deeply. Morphe is the form a "
            "person takes; Christ took the morphe of a servant (Phil 2). Doulos is the "
            "servant Himself. Tselem (Hebrew) is image — the image God made man in."
        ),
        "words": [
            "G4561", "G5590", "G2390", "G3444", "G3996",
            "G1401", "G1402", "G3816",
            "H6754", "H7200", "H7203",
            "G1320",
        ],
    }),
    ("foundational-words", {
        "title": "Foundational Words",
        "subtitle": "The small Greek words that carry the structure",
        "intro": (
            "Greek thought rides on its prepositions. Kai (and) builds the sentence; "
            "hina (in order that) introduces purpose; pros (toward) describes relationship; "
            "syn (with) names participation. Eimi (I am) is the verb God uses for Himself. "
            "These are not glamorous words, but knowing them changes how the New Testament "
            "reads."
        ),
        "words": [
            "G2532", "G2443", "G4314", "G4862", "G1510",
            "G303", "G3844", "G5120", "G1854",
            "G575", "G4012", "G1909", "G3326", "G1519", "G5259",
            "G3123", "G2908",
        ],
    }),
])


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

def strip_diacritics(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def normalize_key(s):
    s = strip_diacritics(s.lower())
    s = re.sub(r"[^a-z']", "", s)
    return s

def load_strongs_lookup():
    """Return list of (translit, strongs_num) pairs from study-tools.js."""
    text = JS_PATH.read_text()
    m = re.search(r"const STRONGS_LOOKUP = \{(.*?)\};", text, re.DOTALL)
    if not m:
        sys.exit("could not find STRONGS_LOOKUP in study-tools.js")
    pairs = re.findall(r'"([^"]+)"\s*:\s*"(G\d+|H\d+)"', m.group(1))
    return pairs

def build_strongs_to_translits(pairs):
    """{strongs_num: [translit, ...]} — prefer ones with diacritics for display."""
    by_num = defaultdict(list)
    for translit, snum in pairs:
        by_num[snum].append(translit)
    # Pick the prettiest translit per Strong's (one with macrons/diacritics is preferable)
    for snum, tlist in by_num.items():
        # Score: has macron > has apostrophe > plain ASCII
        def score(t):
            has_macron = any(c in t for c in "ēōāīūôŏ")
            has_apos = "'" in t
            return (has_macron, has_apos)
        tlist.sort(key=score, reverse=True)
    return by_num

def load_bdbt():
    with open(BDBT_PATH) as f:
        return {e["topic"]: e for e in json.load(f)}

# ─────────────────────────────────────────────────────────────────────────────
# Harvest excerpts from chapter HTML
# ─────────────────────────────────────────────────────────────────────────────

PARA_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
EM_RE = re.compile(r"<em[^>]*>([^<]+)</em>|<i[^>]*>([^<]+)</i>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)

def pretty_chapter_label(filename):
    name = filename.replace(".html", "")
    m = re.match(r"^chapter-?0*(\d+)$", name, re.IGNORECASE)
    if m:
        return f"Chapter {m.group(1)}"
    return name.replace("-", " ").replace("_", " ").title()

def chapter_h1_title(html_text):
    m = H1_RE.search(html_text)
    if not m:
        return None
    txt = TAG_RE.sub("", m.group(1)).strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt or None

def clean_bdbt_definition(raw, snum):
    """Extract a clean human-readable definition from a BDBT entry.

    Greek (G-prefix) entries end with a Strong's gloss: 'Strong's: …'.
    Hebrew (H-prefix) entries lead with BDB Definition: a nested <ol>/<li>
    list of senses. We pull the Strong's gloss when available, otherwise
    flatten the BDB list to a comma-separated list of senses.
    """
    if not raw:
        return ""
    # Find the BDB Definition body (raw HTML up to next </ol>)
    if snum.startswith("H"):
        m = re.search(r"BDB Definition</b>:</p>\s*<ol[^>]*>(.+?)</ol>\s*<p\s*/>\s*Origin:", raw, re.DOTALL)
        if m:
            ol_html = m.group(1)
            senses = re.findall(r"<li[^>]*>([^<]+)</li>", ol_html)
            # Filter out parenthetical metadata-ish entries
            senses = [s.strip() for s in senses if s.strip() and not s.strip().startswith("(")]
            if senses:
                return "; ".join(senses)
    # Greek path or H fallback: pull Strong's: gloss
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    m = re.search(r"Strong['’]s:\s*(.+?)(?:\s*-\s*(?:Origin|TDNT|TWOT|Part)|$)", text)
    if m:
        out = m.group(1).strip(" .:")
        return re.sub(r"\s+", " ", out).strip(" .,;:—-")
    m2 = re.search(r"Definition:\s*(.+?)(?:\s*-\s*(?:Strong|Origin|TDNT|TWOT|Part)|$)", text)
    if m2:
        out = m2.group(1).strip(" .:")
        return re.sub(r"\s+", " ", out).strip(" .,;:—-")
    # Last resort: return short_definition only (handled by caller)
    return ""


def clean_paragraph_html(p_html):
    """Strip <p> wrappers, normalize whitespace. Preserve internal <em>/<strong>/<a>."""
    # Drop verse-citation-only artifacts and tools markup just in case
    # Remove any pre-existing nm-* classes (defensive — shouldn't be in source)
    txt = p_html.strip()
    # Strip our para-anchor (only added at runtime, but defensive)
    txt = re.sub(r'<a[^>]*class="nm-para-anchor"[^>]*>.*?</a>', "", txt, flags=re.IGNORECASE | re.DOTALL)
    # Collapse whitespace
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def has_word_match(text, translit_norms):
    """True if any of the translit-normalized words appears as an italic word in text."""
    for m in EM_RE.finditer(text):
        content = (m.group(1) or m.group(2) or "").strip().rstrip(".,;:!?")
        if not content:
            continue
        # Multi-word: check each word
        for word in re.findall(r"[A-Za-zÀ-ÿ']+", content):
            if normalize_key(word).replace("y", "u").replace("'", "") in translit_norms:
                return True
    return False

def harvest_excerpts(strongs_to_translits):
    """For each Strong's number, find every chapter that discusses it.
    Returns {snum: [{book_dir, chapter_file, chapter_label, chapter_title, paragraph_html}, ...]}."""
    excerpts = defaultdict(list)
    # Build lookup: normalized translit (y→u, no apos) → set of Strong's nums it could match
    translit_to_nums = defaultdict(set)
    for snum, tlist in strongs_to_translits.items():
        for t in tlist:
            k = normalize_key(t).replace("y", "u").replace("'", "")
            if k:
                translit_to_nums[k].add(snum)

    for book in BOOK_DIRS:
        bp = ROOT / book
        if not bp.exists():
            continue
        for html_file in sorted(bp.glob("chapter-*.html")):
            text = html_file.read_text(encoding="utf-8", errors="ignore")
            ch_title = chapter_h1_title(text)
            ch_label = pretty_chapter_label(html_file.name)
            # Find paragraphs that contain any italic match
            for p_match in PARA_RE.finditer(text):
                p_inner = p_match.group(1)
                # Find every italic in this paragraph, see which Strong's it matches
                matched_nums = set()
                for em in EM_RE.finditer(p_inner):
                    content = (em.group(1) or em.group(2) or "").strip().rstrip(".,;:!?")
                    if not content:
                        continue
                    for word in re.findall(r"[A-Za-zÀ-ÿ']+", content):
                        k = normalize_key(word).replace("y", "u").replace("'", "")
                        if k in translit_to_nums:
                            matched_nums.update(translit_to_nums[k])
                if not matched_nums:
                    continue
                p_clean = clean_paragraph_html(p_inner)
                # Skip very short paragraphs (probably captions/citations)
                plain_len = len(TAG_RE.sub("", p_clean))
                if plain_len < 40:
                    continue
                for snum in matched_nums:
                    excerpts[snum].append({
                        "book_dir": book,
                        "book_title": BOOK_TITLES.get(book, book),
                        "chapter_file": html_file.name,
                        "chapter_label": ch_label,
                        "chapter_title": ch_title,
                        "paragraph_html": p_clean,
                    })
    return excerpts

# ─────────────────────────────────────────────────────────────────────────────
# HTML emission
# ─────────────────────────────────────────────────────────────────────────────

# Brand color theme for this book — deep night with warm gold + scripture amber
COLORS = {
    "bg_dark": "#0d0d0d",
    "bg_inner": "rgba(13, 15, 20, 0.96)",
    "text_primary": "#f0ece4",
    "text_secondary": "#c0b8a8",
    "text_muted": "#8a8278",
    "accent": "#C4A864",           # warm gold (primary)
    "accent_glow": "rgba(196, 168, 84, 0.45)",
    "accent_secondary": "#A8442D", # scripture amber (warm red)
    "accent_secondary_glow": "rgba(168, 68, 45, 0.35)",
    "original": "#7BB0C9",         # cool indigo — for original Hebrew/Greek characters
}

PAGE_CSS = """
:root {
  --bg-dark: %(bg_dark)s;
  --bg-inner: %(bg_inner)s;
  --text-primary: %(text_primary)s;
  --text-secondary: %(text_secondary)s;
  --text-muted: %(text_muted)s;
  --accent: %(accent)s;
  --accent-glow: %(accent_glow)s;
  --accent-secondary: %(accent_secondary)s;
  --accent-secondary-glow: %(accent_secondary_glow)s;
  --original: %(original)s;
  --radius-card: 22px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', Georgia, serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  font-size: 1.1rem;
  line-height: 1.85;
  min-height: 100vh;
  padding: 30px 20px;
}
body::before {
  content: "";
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0;
  background:
    radial-gradient(circle at top, rgba(196,168,84,0.06), transparent 50%%),
    radial-gradient(circle at bottom, rgba(168,68,45,0.05), transparent 50%%);
  pointer-events: none;
}
.glass-page-wrapper {
  position: relative;
  z-index: 10;
  border-radius: calc(var(--radius-card) + 4px);
  padding: 3px;
  background:
    radial-gradient(circle at top left, rgba(196,168,84,0.45), transparent 50%%),
    radial-gradient(circle at top right, rgba(168,68,45,0.35), transparent 50%%),
    radial-gradient(circle at bottom, rgba(196,168,84,0.20), transparent 55%%);
  box-shadow:
    0 0 50px rgba(196,168,84,0.15),
    0 0 80px rgba(168,68,45,0.18);
  max-width: 920px;
  width: 100%%;
  margin: 0 auto;
}
.glass-page-inner {
  background: var(--bg-inner);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: var(--radius-card);
  padding: 3rem 2.5rem;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(148,163,184,0.15);
}
.nav-controls {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px;
  padding: 14px 20px; margin-bottom: 1.8rem;
  background: rgba(15,15,18, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(148,163,184,0.15);
}
.nav-controls a {
  color: var(--text-secondary); text-decoration: none;
  font-size: 0.9rem; letter-spacing: 0.04em;
  padding: 6px 10px; border-radius: 6px;
  transition: all 0.2s;
}
.nav-controls a:hover { color: var(--accent); background: rgba(196,168,84,0.08); }
.nav-controls .active { color: var(--accent); font-weight: 600; }
h1.title {
  font-family: 'Cardo', 'Times New Roman', serif;
  font-size: clamp(2.2rem, 4.5vw, 3.4rem);
  font-weight: 700;
  color: var(--accent);
  text-align: center;
  margin: 1.2rem 0 0.4rem;
  letter-spacing: 0.02em;
  text-shadow: 0 0 30px var(--accent-glow);
}
h1.title .original {
  display: block;
  font-size: 0.42em;
  letter-spacing: 0.3em;
  color: var(--original);
  font-weight: 400;
  margin-bottom: 0.8em;
  text-shadow: none;
}
.dek {
  font-family: 'Cardo', Georgia, serif;
  font-style: italic;
  text-align: center;
  color: var(--text-secondary);
  font-size: 1.15rem;
  margin: 0 auto 2.5rem;
  max-width: 640px;
  line-height: 1.5;
}
.section-heading {
  font-family: 'Cardo', Georgia, serif;
  font-size: 0.88rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--accent-secondary);
  text-align: center;
  margin: 3rem 0 1.4rem;
  font-weight: 700;
}
p.lead {
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.12rem;
  line-height: 1.75;
  color: var(--text-primary);
  text-align: center;
  max-width: 620px;
  margin: 0 auto 2rem;
}
p { margin-bottom: 1.05rem; }
p.body { font-family: 'Cardo', Georgia, serif; font-size: 1.05rem; }

/* Theme grid on landing */
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
  margin: 0 0 2rem;
}
.theme-card {
  display: block;
  padding: 16px 18px;
  background: rgba(196, 168, 84, 0.06);
  border: 1px solid rgba(196, 168, 84, 0.18);
  border-radius: 14px;
  text-decoration: none;
  color: inherit;
  transition: transform 0.2s, background 0.2s, border-color 0.2s;
}
.theme-card:hover {
  transform: translateY(-2px);
  background: rgba(196, 168, 84, 0.12);
  border-color: rgba(196, 168, 84, 0.5);
}
.theme-card .theme-num {
  display: inline-block;
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: var(--accent-secondary);
  margin-bottom: 4px;
}
.theme-card .theme-title {
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.18rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 6px;
}
.theme-card .theme-sub {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-style: italic;
  line-height: 1.4;
}
.theme-card .theme-count {
  display: inline-block;
  margin-top: 8px;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  text-transform: uppercase;
}

/* Theme page word list */
.theme-words {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin: 1.6rem 0;
}
.theme-word {
  padding: 12px 14px;
  background: rgba(0,0,0,0.25);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  transition: border-color 0.2s, background 0.2s;
}
.theme-word:hover { border-color: rgba(196, 168, 84, 0.5); }
.theme-word a { color: var(--accent); text-decoration: none; }
.theme-word a:hover { color: #FFEB82; }
.theme-word .tw-translit {
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.1rem;
  font-weight: 700;
}
.theme-word .tw-original {
  font-family: 'Cardo', 'Times New Roman', serif;
  font-size: 1.1rem;
  color: var(--original);
  margin-left: 8px;
}
.theme-word .tw-strongs {
  display: inline-block;
  margin-left: 6px;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  color: var(--accent-secondary);
  vertical-align: middle;
}
.theme-word .tw-def {
  margin-top: 4px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-style: italic;
}

/* Lexicon entries */
.lex-toc {
  margin: 1.2rem 0 2rem;
  text-align: center;
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.2rem;
  letter-spacing: 0.06em;
}
.lex-toc a {
  display: inline-block;
  padding: 2px 8px;
  margin: 2px;
  color: var(--accent);
  text-decoration: none;
  border-radius: 4px;
}
.lex-toc a:hover { background: rgba(196,168,84,0.18); }
.lex-toc .disabled { color: var(--text-muted); }

.lex-entry {
  margin: 1.6rem 0 2.4rem;
  padding: 1.4rem 1.5rem;
  background: rgba(0,0,0,0.22);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 14px;
  scroll-margin-top: 30px;
}
.lex-entry h2 {
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.65rem;
  font-weight: 700;
  margin-bottom: 0.15em;
  color: var(--accent);
}
.lex-entry .lex-original {
  font-family: 'Cardo', 'Times New Roman', serif;
  font-size: 1.6rem;
  color: var(--original);
  margin-right: 12px;
  display: inline-block;
}
.lex-entry .lex-meta {
  display: flex; flex-wrap: wrap; gap: 14px;
  font-size: 0.8rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  margin: 6px 0 14px;
  align-items: center;
}
.lex-entry .lex-meta .lex-strongs {
  display: inline-block;
  padding: 2px 10px;
  background: rgba(168, 68, 45, 0.2);
  color: var(--accent-secondary);
  border-radius: 4px;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.lex-entry .lex-pron { font-style: italic; }
.lex-entry .lex-def {
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.02rem;
  line-height: 1.6;
  color: var(--text-primary);
  padding-bottom: 12px;
  margin-bottom: 10px;
  border-bottom: 1px dotted rgba(196, 168, 84, 0.2);
}
.lex-entry .lex-themes {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-bottom: 14px;
}
.lex-entry .lex-themes a {
  color: var(--accent);
  text-decoration: none;
  margin-right: 8px;
}
.lex-entry .lex-themes a:hover { color: #FFEB82; }
.lex-entry .from-books {
  margin-top: 6px;
}
.lex-entry .from-books h3 {
  font-family: 'Cardo', Georgia, serif;
  font-size: 0.82rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--accent-secondary);
  margin-bottom: 10px;
}
.lex-entry blockquote {
  margin: 10px 0 12px;
  padding: 10px 16px;
  border-left: 3px solid var(--accent);
  background: rgba(196, 168, 84, 0.06);
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.02rem;
  line-height: 1.65;
  font-style: italic;
  color: var(--text-primary);
}
.lex-entry blockquote em { color: #FFEB82; font-style: italic; }
.lex-entry .lex-cite {
  display: block;
  margin-top: 6px;
  text-align: right;
  font-style: normal;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  color: var(--accent-secondary);
  text-transform: uppercase;
}
.lex-entry .lex-cite a {
  color: var(--accent-secondary);
  text-decoration: none;
}
.lex-entry .lex-cite a:hover { color: var(--accent); }
.lex-entry .also-in {
  font-size: 0.83rem;
  color: var(--text-secondary);
  font-style: italic;
  margin-top: 6px;
}
.lex-entry .also-in a {
  color: var(--accent);
  text-decoration: none;
}
.no-excerpts {
  font-size: 0.87rem;
  color: var(--text-muted);
  font-style: italic;
}

/* by-strongs page */
.strongs-table {
  width: 100%%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-family: 'Cardo', Georgia, serif;
}
.strongs-table th {
  text-align: left;
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-secondary);
  padding: 8px 10px;
  border-bottom: 1px solid rgba(168, 68, 45, 0.25);
}
.strongs-table td {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
  vertical-align: top;
}
.strongs-table td:first-child { color: var(--accent-secondary); font-weight: 700; letter-spacing: 0.06em; }
.strongs-table td a { color: var(--accent); text-decoration: none; }
.strongs-table td a:hover { color: #FFEB82; }
.strongs-table td .orig { color: var(--original); font-family: 'Cardo', 'Times New Roman', serif; }

/* Footer */
.book-footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  font-size: 0.83rem;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.7;
}
.book-footer a { color: var(--accent-secondary); text-decoration: none; }
.book-footer a:hover { color: var(--accent); }

@media (max-width: 700px) {
  body { padding: 16px 8px; }
  .glass-page-inner { padding: 2rem 1.4rem; }
  h1.title { font-size: 2rem; }
  .nav-controls { padding: 10px 12px; }
  .nav-controls a { padding: 4px 7px; font-size: 0.82rem; }
}
""" % COLORS


def h(s):
    return html_mod.escape(s or "", quote=True)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="canonical" href="https://noblemind.study/WordStudies/{filename}">
  <link href="https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  <style>{css}</style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">
      <div class="nav-controls">
        <a href="/index.html">← Home</a>
        <a href="index.html"{home_active}>Gems</a>
        <a href="preface.html"{preface_active}>Preface</a>
        <a href="lexicon.html"{lex_active}>Lexicon</a>
        <a href="by-strongs.html"{strongs_active}>By Strong's</a>
        <a href="/books.html">All Books</a>
      </div>
      {body}
    </div>
  </div>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>
"""

def render_page(filename, title, body, active=""):
    return PAGE_TEMPLATE.format(
        title=h(title),
        filename=h(filename),
        css=PAGE_CSS,
        home_active=' class="active"' if active == "home" else "",
        preface_active=' class="active"' if active == "preface" else "",
        lex_active=' class="active"' if active == "lex" else "",
        strongs_active=' class="active"' if active == "strongs" else "",
        body=body,
    )


def render_index(themes_meta, total_words, total_excerpts, all_books_count):
    cards = []
    for i, (slug, theme) in enumerate(themes_meta, 1):
        cards.append(f"""
        <a class="theme-card" href="themes/{h(slug)}.html">
          <div class="theme-num">{i:02d}</div>
          <div class="theme-title">{h(theme['title'])}</div>
          <div class="theme-sub">{h(theme['subtitle'])}</div>
          <div class="theme-count">{theme['word_count']} word{'s' if theme['word_count'] != 1 else ''}</div>
        </a>""")
    body = f"""
      <h1 class="title">
        <span class="original">אֱלֹהִים · λόγος · רוּחַ · ἀγάπη</span>
        Gems of the Original Languages
      </h1>
      <p class="dek">A Hebrew and Greek study companion to the Noble Mind Press books</p>

      <p class="lead">
        Every word study scattered across the Noble Mind Press catalog, gathered into a single
        living reference. Click any term to see the original Hebrew or Greek, its Strong's entry,
        and the verbatim passages from our books where the word is opened up.
      </p>

      <div class="section-heading">Part I — By Theme</div>
      <div class="theme-grid">
        {"".join(cards)}
      </div>

      <div class="section-heading">Part II — Alphabetical Lexicon</div>
      <p class="body" style="text-align:center; max-width:600px; margin: 0 auto 1.5rem;">
        The complete A–Z lexicon — every word in the table, with full definition and every passage
        where it appears in our books.
      </p>
      <p style="text-align:center;">
        <a class="theme-card" style="display:inline-block; max-width:320px; text-align:center; padding: 16px 24px;" href="lexicon.html">
          <div class="theme-title">Open the Lexicon →</div>
          <div class="theme-count">{total_words} entries · {total_excerpts} excerpts</div>
        </a>
      </p>

      <div class="section-heading">Part III — By Strong's Number</div>
      <p class="body" style="text-align:center; max-width:600px; margin: 0 auto 1.5rem;">
        Sorted by Strong's number — useful for cross-referencing against any Bible study tool
        that uses Strong's coding.
      </p>
      <p style="text-align:center;">
        <a class="theme-card" style="display:inline-block; max-width:320px; text-align:center; padding: 16px 24px;" href="by-strongs.html">
          <div class="theme-title">Strong's Cross-Reference →</div>
        </a>
      </p>

      <div class="book-footer">
        <p>
          Compiled from {all_books_count} Noble Mind Press books by Paul and Pam Hainline.
          All commentary excerpts are quoted verbatim with full citation.
          Original-language data from BDBT.
        </p>
        <p><a href="preface.html">Read the preface</a> for more on the methodology.</p>
      </div>
    """
    return render_page("index.html", "Gems of the Original Languages", body, active="home")


def render_preface():
    body = """
      <h1 class="title" style="font-size: 2.2rem;">Preface</h1>
      <p class="dek">A note on what this is and how it came to be.</p>

      <p class="body">
        Many of the Noble Mind Press books pause to open up the original Hebrew or Greek behind
        an English word. The Love God Calls Us To walks through every clause of 1 Corinthians 13
        with the underlying Greek. Change the Mind, Change the Man traces <em>metanoia</em>
        from Matthew to Hebrews. The God Who Showed Up follows the Hebrew names through which
        God reveals Himself in the Old Testament. Bridge Moments uses the Greek <em>argon</em>
        — idle, useless — to describe the kind of speech Colossians 4 warns against.
      </p>

      <p class="body">
        Each of those studies was done where the chapter needed it. None of them existed as a
        reference resource a reader could flip to. This book is the answer to that — a single
        place where every Hebrew and Greek word our books have ever opened up can be found,
        looked up, and read in the very paragraphs where the author taught it.
      </p>

      <div class="section-heading">A nod to the inspiration</div>
      <p class="body">
        The seed for this project was a small old book Paul has been trying to find in storage —
        something called <em>Gems in Greek</em>, by an author whose name he couldn't remember.
        The idea stuck though: pull the original-language insights out of where they were
        scattered and gather them as treasures in one place. So that is what this is — gems,
        not just from Greek but from Hebrew too, drawn out of the books that taught them.
      </p>

      <div class="section-heading">Methodology</div>
      <p class="body">
        Every entry is built automatically from three sources: the curated transliteration map
        we maintain in the site code, BDBT — the standard Strong's Hebrew &amp; Greek
        dictionary — and the chapter HTML of every book in the catalog. When a paragraph in
        any chapter italicizes a Greek or Hebrew word that we recognize, that paragraph is
        added to the word's lexicon entry, verbatim and fully cited.
      </p>
      <p class="body">
        Nothing is paraphrased. Nothing is summarized. The voice you read in every excerpt is
        Paul's (and where applicable Pam's) — the same prose, in the same order, with the same
        emphasis they put there in the original chapter. The only thing this book adds is the
        index, the cross-reference, and the structure.
      </p>

      <div class="section-heading">It will grow</div>
      <p class="body">
        Because the book is built from the books, every new chapter that opens up a new word —
        or studies an existing one in a new way — gets folded in the next time we re-build.
        The lexicon is not static. As the catalog grows, so will this companion. There is no
        edition to outdate. The version you are reading is always the current one.
      </p>

      <p class="body" style="text-align: center; margin-top: 2.5rem;">
        <a href="index.html" style="color: var(--accent); text-decoration: none; letter-spacing: 0.1em;">← Back to the cover</a>
      </p>
    """
    return render_page("preface.html", "Preface — Gems of the Original Languages", body, active="preface")


def render_theme(slug, theme, words_data, strongs_to_translits, bdbt, position):
    rows = []
    for snum in theme["words"]:
        translit_list = strongs_to_translits.get(snum, [])
        if not translit_list:
            continue
        primary_translit = translit_list[0]
        entry = bdbt.get(snum, {})
        lex = entry.get("lexeme", "—") or "—"
        short_def = (entry.get("short_definition") or "").strip()
        rows.append(f"""
        <div class="theme-word">
          <a href="../lexicon.html#{h(slug_for_word(snum, primary_translit))}">
            <span class="tw-translit">{h(primary_translit)}</span>
            <span class="tw-original">{h(lex)}</span>
            <span class="tw-strongs">{h(snum)}</span>
          </a>
          {f'<div class="tw-def">{h(short_def)}</div>' if short_def else ''}
        </div>""")
    body = f"""
      <h1 class="title" style="font-size: 2rem;">{h(theme['title'])}</h1>
      <p class="dek">{h(theme['subtitle'])}</p>

      <p class="body" style="font-family: 'Cardo', Georgia, serif; max-width: 680px; margin: 0 auto 2rem;">
        {h(theme['intro'])}
      </p>

      <div class="section-heading">Words in this theme</div>
      <div class="theme-words">
        {"".join(rows) if rows else '<p class="no-excerpts">No words assigned yet.</p>'}
      </div>

      <p style="text-align:center; margin-top: 2.5rem;">
        <a href="../index.html" style="color: var(--accent); text-decoration: none; letter-spacing: 0.1em;">
          ← Back to all themes
        </a>
      </p>
    """
    return render_page(f"themes/{slug}.html", f"{theme['title']} — Gems of the Original Languages", body)


def slug_for_word(snum, translit):
    """Anchor slug for a lexicon entry."""
    base = re.sub(r"[^a-z0-9]", "-", normalize_key(translit)).strip("-") or snum.lower()
    return f"{base}-{snum.lower()}"


def render_lexicon(words_data, strongs_to_translits, bdbt, excerpts, themes_meta):
    # Group entries by first letter of primary translit
    by_letter = defaultdict(list)
    word_to_themes = defaultdict(list)  # snum → [(slug, title), ...]
    for slug, theme in themes_meta:
        for snum in theme["words"]:
            word_to_themes[snum].append((slug, theme["title"]))

    for snum in words_data:
        translits = strongs_to_translits.get(snum, [])
        if not translits:
            continue
        primary = translits[0]
        first = normalize_key(primary)[0:1] or "?"
        by_letter[first.upper()].append((primary, snum))

    # Sort letters and entries
    for letter in by_letter:
        by_letter[letter].sort(key=lambda x: normalize_key(x[0]))

    letters_sorted = sorted(by_letter.keys())

    # Build TOC
    toc_html = '<div class="lex-toc">'
    for L in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if L in by_letter:
            toc_html += f'<a href="#letter-{L}">{L}</a>'
        else:
            toc_html += f'<span class="disabled">{L}</span>'
    toc_html += "</div>"

    # Build entries
    entries_html = []
    for L in letters_sorted:
        entries_html.append(f'<h2 id="letter-{L}" class="section-heading" style="margin-top: 2.4rem;">— {L} —</h2>')
        for primary, snum in by_letter[L]:
            entry = bdbt.get(snum, {})
            lex = entry.get("lexeme", "—") or "—"
            pron = entry.get("pronunciation", "")
            definition_clean = clean_bdbt_definition(entry.get("definition", ""), snum)
            short_def = (entry.get("short_definition") or "").strip()

            translit_variants = [t for t in strongs_to_translits.get(snum, []) if t != primary]
            variant_html = ""
            if translit_variants:
                variant_html = (
                    '<span class="lex-pron">' + h(", ".join(translit_variants[:4])) + "</span>"
                )

            # Themes this word appears in
            themes_for_this = word_to_themes.get(snum, [])
            themes_html = ""
            if themes_for_this:
                links = [f'<a href="themes/{h(s)}.html">{h(t)}</a>' for s, t in themes_for_this]
                themes_html = '<div class="lex-themes">In themes: ' + ", ".join(links) + "</div>"

            # Excerpts from the books
            book_excerpts = excerpts.get(snum, [])
            # Dedupe: same book+chapter+first-100-chars-of-text → keep one
            seen = set()
            uniq_excerpts = []
            for ex in book_excerpts:
                key = (ex["book_dir"], ex["chapter_file"],
                       re.sub(r"<[^>]+>", "", ex["paragraph_html"])[:120])
                if key in seen:
                    continue
                seen.add(key)
                uniq_excerpts.append(ex)

            # Limit to 3 primary excerpts shown; mention more in an "also in"
            shown = uniq_excerpts[:3]
            extra = uniq_excerpts[3:]

            excerpt_html_parts = []
            if shown:
                excerpt_html_parts.append('<div class="from-books"><h3>From our books</h3>')
                for ex in shown:
                    ch_title = ex["chapter_title"] or ""
                    label = ex["chapter_label"] + (f" — {ch_title}" if ch_title and ch_title != ex["chapter_label"] else "")
                    chapter_href = f"/{ex['book_dir']}/{ex['chapter_file']}"
                    excerpt_html_parts.append(f"""
                <blockquote>
                  <p>{ex['paragraph_html']}</p>
                  <span class="lex-cite"><a href="{h(chapter_href)}">{h(ex['book_title'])} · {h(label)}</a></span>
                </blockquote>""")
                if extra:
                    seen_ch = set()
                    also_links = []
                    for ex in extra:
                        key = (ex["book_dir"], ex["chapter_file"])
                        if key in seen_ch:
                            continue
                        seen_ch.add(key)
                        ch_title = ex["chapter_title"] or ""
                        label = ex["chapter_label"] + (f" — {ch_title}" if ch_title and ch_title != ex["chapter_label"] else "")
                        chapter_href = f"/{ex['book_dir']}/{ex['chapter_file']}"
                        also_links.append(f'<a href="{h(chapter_href)}">{h(ex["book_title"])} · {h(label)}</a>')
                    if also_links:
                        excerpt_html_parts.append(
                            '<div class="also-in">Also discussed in: ' + " · ".join(also_links) + "</div>"
                        )
                excerpt_html_parts.append("</div>")
            else:
                excerpt_html_parts.append('<p class="no-excerpts">No chapter excerpts found in the current build. This word is in the curated table but may not yet be italicized in any chapter prose.</p>')

            slug_id = slug_for_word(snum, primary)
            entries_html.append(f"""
      <div class="lex-entry" id="{h(slug_id)}">
        <h2>
          <span class="lex-original">{h(lex)}</span>
          {h(primary)}
        </h2>
        <div class="lex-meta">
          <span class="lex-strongs">{h(snum)}</span>
          {('<span class="lex-pron">' + h(pron) + '</span>') if pron else ''}
          {variant_html}
        </div>
        <div class="lex-def">{h(short_def + ('. ' if short_def else '') + definition_clean) if (short_def or definition_clean) else '—'}</div>
        {themes_html}
        {"".join(excerpt_html_parts)}
      </div>""")

    body = f"""
      <h1 class="title" style="font-size: 2.2rem;">Alphabetical Lexicon</h1>
      <p class="dek">{len(words_data)} entries · A–Z by scholarly transliteration</p>
      {toc_html}
      {"".join(entries_html)}
      <p style="text-align:center; margin-top: 2.5rem;">
        <a href="index.html" style="color: var(--accent); text-decoration: none; letter-spacing: 0.1em;">
          ← Back to the cover
        </a>
      </p>
    """
    return render_page("lexicon.html", "Lexicon — Gems of the Original Languages", body, active="lex")


def render_by_strongs(words_data, strongs_to_translits, bdbt):
    rows = []
    # Sort by language (G first, then H) then by number
    def sort_key(snum):
        prefix = snum[0]
        num = int(snum[1:])
        return (0 if prefix == "G" else 1, num)
    sorted_nums = sorted([s for s in words_data if strongs_to_translits.get(s)], key=sort_key)

    current_section = None
    for snum in sorted_nums:
        prefix = "Greek" if snum.startswith("G") else "Hebrew"
        if prefix != current_section:
            rows.append(f'<tr><td colspan="4"><h3 style="margin: 1.5rem 0 0.4rem; font-family: \'Cardo\', Georgia, serif; color: var(--accent); font-size: 1.3rem;">{prefix}</h3></td></tr>')
            rows.append('<tr><th>Strong\'s</th><th>Original</th><th>Transliteration</th><th>Short definition</th></tr>')
            current_section = prefix

        primary = strongs_to_translits[snum][0]
        entry = bdbt.get(snum, {})
        lex = entry.get("lexeme", "—") or "—"
        short = (entry.get("short_definition") or "").strip() or "—"
        slug_id = slug_for_word(snum, primary)
        rows.append(f'<tr><td>{h(snum)}</td><td class="orig">{h(lex)}</td><td><a href="lexicon.html#{h(slug_id)}">{h(primary)}</a></td><td>{h(short)}</td></tr>')

    body = f"""
      <h1 class="title" style="font-size: 2rem;">By Strong's Number</h1>
      <p class="dek">Sorted by Strong's number — Greek first, then Hebrew</p>
      <table class="strongs-table">
        {"".join(rows)}
      </table>
      <p style="text-align:center; margin-top: 2rem;">
        <a href="index.html" style="color: var(--accent); text-decoration: none; letter-spacing: 0.1em;">
          ← Back to the cover
        </a>
      </p>
    """
    return render_page("by-strongs.html", "By Strong's Number — Gems of the Original Languages", body, active="strongs")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("Loading STRONGS_LOOKUP from study-tools.js…")
    pairs = load_strongs_lookup()
    strongs_to_translits = build_strongs_to_translits(pairs)
    print(f"  → {len(strongs_to_translits)} distinct Strong's entries.")

    print("Loading BDBT…")
    bdbt = load_bdbt()
    print(f"  → {len(bdbt):,} BDBT entries.")

    print("Harvesting excerpts from book chapters…")
    excerpts = harvest_excerpts(strongs_to_translits)
    total_excerpts = sum(len(v) for v in excerpts.values())
    print(f"  → {total_excerpts} paragraph excerpts across {len([k for k,v in excerpts.items() if v])} words.")

    # Themes — populated word_count for the index card
    themes_meta = []
    for slug, theme in THEMES.items():
        present_words = [w for w in theme["words"] if w in strongs_to_translits]
        theme_for_render = dict(theme)
        theme_for_render["words"] = present_words
        theme_for_render["word_count"] = len(present_words)
        themes_meta.append((slug, theme_for_render))

    # Set of all snums covered by themes
    in_any_theme = {w for _, t in themes_meta for w in t["words"]}
    uncategorized = [s for s in strongs_to_translits if s not in in_any_theme]
    if uncategorized:
        print(f"  (note: {len(uncategorized)} Strong's entries not yet assigned to a theme — they will still show in the lexicon.)")

    print("Writing pages…")
    OUT.mkdir(exist_ok=True)
    (OUT / "themes").mkdir(exist_ok=True)

    # index.html
    (OUT / "index.html").write_text(render_index(themes_meta, len(strongs_to_translits), total_excerpts, len(BOOK_DIRS)), encoding="utf-8")
    print(f"  ✓ index.html")

    # preface.html
    (OUT / "preface.html").write_text(render_preface(), encoding="utf-8")
    print(f"  ✓ preface.html")

    # theme pages
    for i, (slug, theme) in enumerate(themes_meta, 1):
        (OUT / "themes" / f"{slug}.html").write_text(
            render_theme(slug, theme, strongs_to_translits, strongs_to_translits, bdbt, i),
            encoding="utf-8"
        )
        print(f"  ✓ themes/{slug}.html ({theme['word_count']} words)")

    # lexicon.html
    (OUT / "lexicon.html").write_text(
        render_lexicon(list(strongs_to_translits.keys()), strongs_to_translits, bdbt, excerpts, themes_meta),
        encoding="utf-8"
    )
    print(f"  ✓ lexicon.html ({len(strongs_to_translits)} entries)")

    # by-strongs.html
    (OUT / "by-strongs.html").write_text(
        render_by_strongs(list(strongs_to_translits.keys()), strongs_to_translits, bdbt),
        encoding="utf-8"
    )
    print(f"  ✓ by-strongs.html")

    print(f"\nDone. Open WordStudies/index.html in a browser to review.")


if __name__ == "__main__":
    main()
