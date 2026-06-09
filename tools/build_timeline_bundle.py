#!/usr/bin/env python3
"""
Build a self-contained, OFFLINE copy of the Old Testament Timeline and all
of its deep-dive spokes, zipped for download from the timeline page.

The result (old-testament-timeline/Old_Testament_Timeline_Interactive.zip)
unzips to a folder a non-technical person can open with a double-click and
use with no internet and no NobleMind app around it:

  Old_Testament_Timeline_Interactive/
    Open the Timeline.html        <- friendly landing page
    _assets/fonts.css             <- the two fonts, embedded as base64
    old-testament-timeline/       <- the interactive timeline + its PDF
    the-prophecies/  the-stones-cry-out/ (+img)  ...all 15 spokes...

What it does to each page:
  * the Google-Fonts @import is repointed at the bundled _assets/fonts.css
    so the typography is correct with no internet,
  * root-absolute app links (href="/...", e.g. the NobleMind back-link and
    the Last-Week-of-the-Lamb book links) are rewritten to
    https://noblemind.study/... so they still work *if* the reader is
    online, and never dead-end offline,
  * the timeline's own "Download interactive" button is stripped from the
    bundled copy (it would point at a zip that isn't inside the zip).

Reader PDFs are included (they're small); the big internal planning PDFs
and all .md notes are left out.

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
# Embedded-font CSS is cached here and committed, so deploy never depends on
# Google Fonts being reachable. Delete it to force a refetch.
FONT_CACHE = ROOT / "tools" / "timeline_bundle_fonts.css"
HUB = "old-testament-timeline"
BUNDLE_NAME = "Old_Testament_Timeline_Interactive"
OUTPUT_ZIP = ROOT / HUB / f"{BUNDLE_NAME}.zip"

# Hub + every spoke the timeline deep-dives into.
SPOKES = [
    "the-prophecies", "the-stones-cry-out", "the-covenants", "the-tabernacle",
    "the-lamb-god-provides", "the-kinsman-redeemer", "the-day-of-atonement",
    "the-appointed-times", "the-promise-threads", "the-divided-kingdom",
    "the-united-kingdom", "the-threefold-promise", "the-preserved-line",
    "why-babel", "genesis-genealogy",
]

FONTS_CSS2 = ("https://fonts.googleapis.com/css2?"
              "family=IM+Fell+English:ital@0;1&"
              "family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap")
# A modern browser UA makes Google serve woff2 (not ttf).
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

GOOGLE_IMPORT_RE = re.compile(
    r"@import\s+url\((['\"])https://fonts\.googleapis\.com[^'\"]*\1\);")
# Root-absolute app links, both HTML-attribute (href="/x") and JS-object
# (href: "/x") forms, so links defined in the timeline's JS consts get
# repointed at the live site too.
ROOT_ABS_RE = re.compile(r'((?:href|src)\s*[=:]\s*")/(?!/)')
# the whole header "Download interactive" anchor, however phrased
INTERACTIVE_ANCHOR_RE = re.compile(
    r'\s*<a[^>]*Old_Testament_Timeline_Interactive\.zip[^>]*>.*?</a>', re.S)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def build_fonts_css() -> str:
    """Return @font-face CSS with each woff2 inlined as base64.
    Uses the committed cache if present (so deploy never needs Google);
    otherwise fetches, embeds, and writes the cache."""
    if FONT_CACHE.exists() and FONT_CACHE.stat().st_size > 5000:
        print(f"  fonts: using cached {FONT_CACHE.name}")
        return FONT_CACHE.read_text(encoding="utf-8")
    css = fetch(FONTS_CSS2).decode("utf-8")
    blocks = re.split(r"(?=/\*\s)", css)  # split on the /* subset */ comments
    out = []
    kept = 0
    for blk in blocks:
        m = re.match(r"/\*\s*([a-z0-9-]+)\s*\*/", blk)
        subset = m.group(1) if m else ""
        if subset and subset not in ("latin", "latin-ext"):
            continue
        url_m = re.search(r"src:\s*url\((https://[^)]+\.woff2)\)", blk)
        if not url_m:
            out.append(blk)
            continue
        data = fetch(url_m.group(1))
        b64 = base64.b64encode(data).decode("ascii")
        blk = blk.replace(
            url_m.group(1),
            f"data:font/woff2;base64,{b64}")
        out.append(blk)
        kept += 1
    if kept == 0:
        raise RuntimeError("No woff2 faces embedded — font fetch failed.")
    result = "".join(out)
    FONT_CACHE.write_text(result, encoding="utf-8")
    print(f"  fonts: embedded {kept} woff2 faces (cached to {FONT_CACHE.name})")
    return result


def process_html(text: str, fonts_href: str, is_hub: bool) -> str:
    text = GOOGLE_IMPORT_RE.sub(f"@import url('{fonts_href}');", text)
    text = ROOT_ABS_RE.sub(r"\1https://noblemind.study/", text)
    if is_hub:
        text = INTERACTIVE_ANCHOR_RE.sub("", text)
    return text


def copy_dir(src: Path, dst: Path):
    """Copy a spoke/hub dir: index.html + reader PDF + img/ only.
    Skip .md notes, the big internal PDFs, and the bundle zip itself."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_dir():
            if item.name == "img":
                shutil.copytree(item, dst / item.name, dirs_exist_ok=True)
            continue
        if item.suffix == ".md":
            continue
        if item.name == OUTPUT_ZIP.name:
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
<title>Open the Old Testament Timeline</title>
<style>
  @import url('_assets/fonts.css');
  :root {{ --parchment:#F5EDD6; --ink:#2A1A05; --sepia:#6B4C1A;
           --sepia-light:#A07840; --gold:#C4A44A; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Crimson Text',Georgia,serif; background:var(--parchment);
          color:var(--ink); min-height:100vh; display:flex; align-items:center;
          justify-content:center; padding:40px 20px; }}
  .card {{ max-width:680px; text-align:center; }}
  h1 {{ font-family:'IM Fell English',Georgia,serif; color:var(--sepia);
        font-size:clamp(30px,5vw,52px); line-height:1.15; }}
  h2 {{ font-family:'IM Fell English',Georgia,serif; font-style:italic;
        color:var(--sepia-light); font-weight:normal; margin-top:8px;
        font-size:clamp(15px,2.4vw,22px); }}
  p {{ margin:18px auto 0; max-width:560px; line-height:1.7; font-size:16px;
       color:#3A2A12; }}
  .open {{ display:inline-block; margin-top:30px; padding:14px 34px;
           background:var(--sepia); color:var(--parchment); text-decoration:none;
           font-family:'IM Fell English',Georgia,serif; font-size:20px;
           border-radius:6px; letter-spacing:0.5px; transition:background .2s; }}
  .open:hover {{ background:var(--sepia-light); }}
  .spokes {{ margin-top:34px; display:flex; flex-wrap:wrap; gap:8px 14px;
             justify-content:center; }}
  .spokes a {{ color:var(--sepia); font-size:13.5px; text-decoration:none;
               border-bottom:1px dotted var(--sepia-light); }}
  .spokes a:hover {{ color:var(--ink); }}
  .note {{ margin-top:34px; font-size:12.5px; color:var(--sepia-light);
           font-style:italic; line-height:1.6; border-top:1px solid #E8D9B5;
           padding-top:16px; }}
  .note a {{ color:inherit; }}
</style>
</head>
<body>
  <div class="card">
    <h1>The Old Testament Timeline</h1>
    <h2>From Creation to Malachi &mdash; the unfolding of God&rsquo;s plan</h2>
    <p>This is the complete interactive timeline and all of its deep-dive
       studies, packaged to run on your own computer. No internet, no app,
       no install &mdash; just open it.</p>
    <a class="open" href="{hub}/index.html">Open the Timeline &rarr;</a>
    <div class="spokes">{spoke_links}</div>
    <div class="note">
      Works fully offline. Links to the wider Noble Mind Study site (and the
      companion books) open online when you have a connection.<br>
      From <a href="https://noblemind.study/">noblemind.study</a> &middot;
      free to share.
    </div>
  </div>
</body>
</html>
"""


def spoke_title(slug: str) -> str:
    return slug.replace("-", " ").title().replace("Of", "of").replace("The ", "The ")


def main():
    staging_parent = ROOT / "tools" / "_bundle_build"
    if staging_parent.exists():
        shutil.rmtree(staging_parent)
    bundle = staging_parent / BUNDLE_NAME
    bundle.mkdir(parents=True)

    print("Building offline timeline bundle…")
    fonts_css = build_fonts_css()
    assets = bundle / "_assets"
    assets.mkdir()
    (assets / "fonts.css").write_text(fonts_css, encoding="utf-8")

    all_dirs = [HUB] + SPOKES
    for slug in all_dirs:
        src = ROOT / slug
        if not (src / "index.html").exists():
            print(f"  WARN: {slug} has no index.html, skipping")
            continue
        dst = bundle / slug
        copy_dir(src, dst)
        # depth-1 dirs reach the shared fonts via ../_assets/
        html = (dst / "index.html").read_text(encoding="utf-8")
        html = process_html(html, "../_assets/fonts.css", is_hub=(slug == HUB))
        (dst / "index.html").write_text(html, encoding="utf-8")

    # Landing page (root → _assets/fonts.css)
    links = " &middot; ".join(
        f'<a href="{s}/index.html">{spoke_title(s)}</a>' for s in SPOKES)
    (bundle / "Open the Timeline.html").write_text(
        LANDING.format(hub=HUB, spoke_links=links), encoding="utf-8")

    # Zip (containing folder at top level)
    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(staging_parent))

    size_mb = OUTPUT_ZIP.stat().st_size / 1e6
    nfiles = sum(1 for _ in bundle.rglob("*") if _.is_file())
    shutil.rmtree(staging_parent)
    print(f"  wrote {OUTPUT_ZIP.relative_to(ROOT)} "
          f"({size_mb:.1f} MB, {nfiles} files, {len(all_dirs)} pages)")


if __name__ == "__main__":
    sys.exit(main())
