#!/usr/bin/env python3
"""
Build self-contained, OFFLINE downloadable copies of the interactive
timelines, zipped for download from the books/timeline pages. Each zip
unzips to a folder a non-technical person can open with a double-click and
use with no internet and no NobleMind app around it.

Bundles built:
  * Old Testament Timeline  (hub + all 15 deep-dive spokes)
  * The Life of Christ       (timeline + the Land-of-Israel & Nativity maps)
  * The Church Christ Built  (timeline + the Missionary-Journeys map)

What it does to every page:
  * the Google-Fonts @import is repointed at the bundled _assets/fonts.css
    so the typography is correct with no internet,
  * root-absolute app links (href="/...") are rewritten to
    https://noblemind.study/... so they still work *if* online and never
    dead-end offline,
  * relative folder links (href="../x/") get index.html appended so they
    resolve under file://,
  * any in-page "Download interactive" button is stripped from the copy.

Reader PDFs are included (small); big internal PDFs and .md notes are not.
Usage:  python3 tools/build_timeline_bundle.py
"""

import base64
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_CACHE = ROOT / "tools" / "timeline_bundle_fonts.css"

SPOKES = [
    "the-prophecies", "the-stones-cry-out", "the-covenants", "the-tabernacle",
    "the-lamb-god-provides", "the-kinsman-redeemer", "the-day-of-atonement",
    "the-appointed-times", "the-promise-threads", "the-divided-kingdom",
    "the-united-kingdom", "the-threefold-promise", "the-preserved-line",
    "why-babel", "genesis-genealogy",
]

def spoke_title(slug):
    return slug.replace("-", " ").title().replace("Of", "of")

# ---- bundle configs ----
BUNDLES = [
    {
        "name": "Old_Testament_Timeline_Interactive",
        "out_subdir": "old-testament-timeline",
        "dirs": ["old-testament-timeline"] + SPOKES,
        "hub": "old-testament-timeline",
        "title": "The Old Testament Timeline",
        "sub": "From Creation to Malachi &mdash; the unfolding of God&rsquo;s plan",
        "intro": "This is the complete interactive timeline and all of its deep-dive "
                 "studies, packaged to run on your own computer. No internet, no app, "
                 "no install &mdash; just open it.",
        "links": [(f"{s}/index.html", spoke_title(s)) for s in SPOKES],
    },
    {
        "name": "The_Life_of_Christ_Interactive",
        "out_subdir": "the-life-of-christ",
        "dirs": ["the-life-of-christ"],
        "hub": "the-life-of-christ",
        "title": "The Life of Christ",
        "sub": "Emmanuel &mdash; God With Us &middot; the four Gospels, side by side",
        "intro": "The complete interactive timeline of the life of Jesus &mdash; all four "
                 "Gospels side by side &mdash; with its zoomable maps, packaged to run on "
                 "your own computer with no internet and no install.",
        "links": [("the-life-of-christ/land-of-israel.html", "The Land of Israel in the Days of Jesus"),
                  ("the-life-of-christ/nativity-route.html", "The Nativity &amp; the Flight to Egypt")],
    },
    {
        "name": "The_Church_Christ_Built_Interactive",
        "out_subdir": "the-church-christ-built",
        "dirs": ["the-church-christ-built"],
        "hub": "the-church-christ-built",
        "title": "The Church Christ Built",
        "sub": "The Acts of the Apostles &mdash; from Jerusalem to the ends of the earth",
        "intro": "The complete interactive timeline of the book of Acts &mdash; the gospel "
                 "spreading from Jerusalem to Rome &mdash; with the zoomable missionary-journey "
                 "maps, packaged to run on your own computer with no internet and no install.",
        "links": [("the-church-christ-built/journey-maps.html", "The Missionary Journeys map")],
    },
    {
        "name": "The_Apostle_Paul_Interactive",
        "out_subdir": "apostle-paul",
        "dirs": ["apostle-paul"],
        "hub": "apostle-paul",
        "title": "The Apostle Paul",
        "sub": "The whole life of the apostle &mdash; from Tarsus to the Roman martyrdom",
        "intro": "The complete interactive timeline of Paul&rsquo;s life and ministry &mdash; with "
                 "its six detailed sub-timelines (the conversion, Antioch, the Jerusalem visits, "
                 "Corinth, Ephesus, and the Roman years) &mdash; packaged to run on your own "
                 "computer with no internet and no install.",
        "links": [("apostle-paul/conversion.html", "Paul&rsquo;s Conversion in Three Tellings"),
                  ("apostle-paul/antioch.html", "Paul &amp; the Church at Antioch"),
                  ("apostle-paul/jerusalem-visits.html", "Paul&rsquo;s Five Visits to Jerusalem"),
                  ("apostle-paul/corinth.html", "Paul &amp; the Corinthian Church"),
                  ("apostle-paul/ephesus.html", "Paul &amp; the Ephesian Church"),
                  ("apostle-paul/roman-years.html", "Paul&rsquo;s Roman Years")],
    },
]

FONTS_CSS2 = ("https://fonts.googleapis.com/css2?"
              "family=IM+Fell+English:ital@0;1&"
              "family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

GOOGLE_IMPORT_RE = re.compile(
    r"@import\s+url\((['\"])https://fonts\.googleapis\.com[^'\"]*\1\);")
ROOT_ABS_RE = re.compile(r'((?:href|src)\s*[=:]\s*")/(?!/)')
DIR_INDEX_RE = re.compile(
    r'(href\s*[=:]\s*")(?!https?:|//|/|#|mailto:)([^"#?:]*?/)(")')


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def build_fonts_css():
    if FONT_CACHE.exists() and FONT_CACHE.stat().st_size > 5000:
        print(f"  fonts: using cached {FONT_CACHE.name}")
        return FONT_CACHE.read_text(encoding="utf-8")
    css = fetch(FONTS_CSS2).decode("utf-8")
    out, kept = [], 0
    for blk in re.split(r"(?=/\*\s)", css):
        m = re.match(r"/\*\s*([a-z0-9-]+)\s*\*/", blk)
        subset = m.group(1) if m else ""
        if subset and subset not in ("latin", "latin-ext"):
            continue
        url_m = re.search(r"src:\s*url\((https://[^)]+\.woff2)\)", blk)
        if not url_m:
            out.append(blk); continue
        b64 = base64.b64encode(fetch(url_m.group(1))).decode("ascii")
        out.append(blk.replace(url_m.group(1), f"data:font/woff2;base64,{b64}"))
        kept += 1
    if kept == 0:
        raise RuntimeError("No woff2 faces embedded — font fetch failed.")
    result = "".join(out)
    FONT_CACHE.write_text(result, encoding="utf-8")
    print(f"  fonts: embedded {kept} woff2 faces (cached to {FONT_CACHE.name})")
    return result


def process_html(text, fonts_href, strip_zip):
    text = GOOGLE_IMPORT_RE.sub(f"@import url('{fonts_href}');", text)
    text = ROOT_ABS_RE.sub(r"\1https://noblemind.study/", text)
    text = DIR_INDEX_RE.sub(r"\1\2index.html\3", text)
    if strip_zip:
        text = re.sub(r'\s*<a[^>]*' + re.escape(strip_zip) + r'[^>]*>.*?</a>', "", text, flags=re.S)
    return text


def copy_dir(src, dst, self_zip):
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_dir():
            if item.name == "img":
                shutil.copytree(item, dst / item.name, dirs_exist_ok=True)
            continue
        if item.suffix == ".md":
            continue
        if item.name.endswith("_Interactive.zip"):
            continue
        if item.suffix == ".pdf" and item.name in (
                "the-3-cycle-approach.pdf", "unfolding-of-gods-plan.pdf"):
            continue
        shutil.copy2(item, dst / item.name)


LANDING = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Open {title}</title>
<style>
  @import url('_assets/fonts.css');
  :root {{ --parchment:#F5EDD6; --ink:#2A1A05; --sepia:#6B4C1A; --sepia-light:#A07840; --gold:#C4A44A; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Crimson Text',Georgia,serif; background:var(--parchment); color:var(--ink);
          min-height:100vh; display:flex; align-items:center; justify-content:center; padding:40px 20px; }}
  .card {{ max-width:680px; text-align:center; }}
  h1 {{ font-family:'IM Fell English',Georgia,serif; color:var(--sepia); font-size:clamp(30px,5vw,52px); line-height:1.15; }}
  h2 {{ font-family:'IM Fell English',Georgia,serif; font-style:italic; color:var(--sepia-light);
        font-weight:normal; margin-top:8px; font-size:clamp(15px,2.4vw,22px); }}
  p {{ margin:18px auto 0; max-width:560px; line-height:1.7; font-size:16px; color:#3A2A12; }}
  .open {{ display:inline-block; margin-top:30px; padding:14px 34px; background:var(--sepia);
           color:var(--parchment); text-decoration:none; font-family:'IM Fell English',Georgia,serif;
           font-size:20px; border-radius:6px; letter-spacing:0.5px; transition:background .2s; }}
  .open:hover {{ background:var(--sepia-light); }}
  .spokes {{ margin-top:34px; display:flex; flex-wrap:wrap; gap:8px 14px; justify-content:center; }}
  .spokes a {{ color:var(--sepia); font-size:13.5px; text-decoration:none; border-bottom:1px dotted var(--sepia-light); }}
  .spokes a:hover {{ color:var(--ink); }}
  .note {{ margin-top:34px; font-size:12.5px; color:var(--sepia-light); font-style:italic; line-height:1.6;
           border-top:1px solid #E8D9B5; padding-top:16px; }}
  .note a {{ color:inherit; }}
</style>
</head>
<body>
  <div class="card">
    <h1>{title}</h1>
    <h2>{sub}</h2>
    <p>{intro}</p>
    <a class="open" href="{hub}/index.html">Open it &rarr;</a>
    <div class="spokes">{links}</div>
    <div class="note">
      Works fully offline. Links to the wider Noble Mind Study site (and the companion books)
      open online when you have a connection.<br>
      From <a href="https://noblemind.study/">noblemind.study</a> &middot; free to share.
    </div>
  </div>
</body>
</html>
"""


def build_bundle(cfg, fonts_css):
    name = cfg["name"]
    out_zip = ROOT / cfg["out_subdir"] / f"{name}.zip"
    staging_parent = ROOT / "tools" / "_bundle_build"
    if staging_parent.exists():
        shutil.rmtree(staging_parent)
    bundle = staging_parent / name
    bundle.mkdir(parents=True)
    (bundle / "_assets").mkdir()
    (bundle / "_assets" / "fonts.css").write_text(fonts_css, encoding="utf-8")

    for slug in cfg["dirs"]:
        src = ROOT / slug
        if not (src / "index.html").exists():
            print(f"  WARN: {slug} has no index.html, skipping"); continue
        dst = bundle / slug
        copy_dir(src, dst, name)
        # every .html in the dir (timeline + any map pages) gets processed
        for html_file in dst.glob("*.html"):
            html = html_file.read_text(encoding="utf-8")
            html = process_html(html, "../_assets/fonts.css", strip_zip=f"{name}.zip")
            html_file.write_text(html, encoding="utf-8")

    links = " &middot; ".join(f'<a href="{href}">{label}</a>' for href, label in cfg["links"])
    (bundle / f"Open {cfg['title']}.html").write_text(
        LANDING.format(title=cfg["title"], sub=cfg["sub"], intro=cfg["intro"],
                       hub=cfg["hub"], links=links), encoding="utf-8")

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(staging_parent))
    size_mb = out_zip.stat().st_size / 1e6
    nfiles = sum(1 for _ in bundle.rglob("*") if _.is_file())
    shutil.rmtree(staging_parent)
    print(f"  wrote {out_zip.relative_to(ROOT)} ({size_mb:.1f} MB, {nfiles} files, {len(cfg['dirs'])} pages)")


def main():
    print("Building offline timeline bundles…")
    fonts_css = build_fonts_css()
    for cfg in BUNDLES:
        build_bundle(cfg, fonts_css)


if __name__ == "__main__":
    sys.exit(main())
