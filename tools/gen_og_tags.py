#!/usr/bin/env python3
"""Backfill Open Graph / Twitter card meta (+ canonical + description) into
content pages that lack them.

Idempotent and conservative:
  * Drives off sitemap.xml, so it only touches pages gen_sitemap.py already
    judged indexable (noindex pages and deploy-excluded drafts are absent).
  * Skips any page that already has an og:title (so the hand-authored key pages
    and the QAPage apologetics pages are left exactly as-is).
  * Only ADDS head meta — never alters body/doctrinal content. canonical and
    description are added only when missing.

og:description is derived from the page's own first substantive paragraph
(author prose), truncated at a word boundary — a summary snippet, not a Scripture
citation. Run AFTER gen_sitemap.py (it reads sitemap.xml). Re-running is safe.
"""
from __future__ import annotations
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://noblemind.study"
OG_IMAGE = f"{BASE_URL}/og-default.png"
OG_ALT = "Noble Mind Study — Test it against the text."
SITE_NAME = "Noble Mind Study"
DESC_MAX = 200

def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))

def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)

def first_paragraph(body: str) -> str:
    """First <p> that reads like a sentence (skip all-caps headings/short bits)."""
    for raw in re.findall(r"<p\b[^>]*>(.*?)</p>", body, re.S | re.I):
        text = html.unescape(strip_tags(raw))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 40:
            continue
        # skip styled headings like "CHAPTER THREE"
        if text == text.upper():
            continue
        return text
    return ""

def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return cut + "…"

def url_to_path(url: str) -> Path | None:
    if not url.startswith(BASE_URL):
        return None
    rel = url[len(BASE_URL):].lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return ROOT / rel

def build_block(title: str, desc: str, url: str, has_desc: bool, has_canon: bool) -> str:
    L = ["  <!-- SEO: social card (auto, tools/gen_og_tags.py) -->"]
    if not has_canon:
        L.append(f'  <link rel="canonical" href="{esc(url)}">')
    if not has_desc and desc:
        L.append(f'  <meta name="description" content="{esc(desc)}">')
    og_desc = desc or title
    L += [
        '  <meta property="og:type" content="article">',
        f'  <meta property="og:site_name" content="{esc(SITE_NAME)}">',
        f'  <meta property="og:title" content="{esc(title)}">',
        f'  <meta property="og:description" content="{esc(og_desc)}">',
        f'  <meta property="og:url" content="{esc(url)}">',
        f'  <meta property="og:image" content="{OG_IMAGE}">',
        '  <meta property="og:image:width" content="1200">',
        '  <meta property="og:image:height" content="630">',
        f'  <meta property="og:image:alt" content="{esc(OG_ALT)}">',
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="twitter:title" content="{esc(title)}">',
        f'  <meta name="twitter:description" content="{esc(truncate(og_desc, 180))}">',
        f'  <meta name="twitter:image" content="{OG_IMAGE}">',
    ]
    return "\n".join(L) + "\n"

# --- gather indexable pages from the sitemap ---
sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", sitemap)

modified = skipped_og = skipped_other = 0
for url in urls:
    path = url_to_path(url)
    if path is None or not path.is_file():
        skipped_other += 1
        continue
    doc = path.read_text(encoding="utf-8")
    if re.search(r'property=["\']og:title["\']', doc, re.I):
        skipped_og += 1
        continue
    m_head = re.search(r"</head\s*>", doc, re.I)
    m_title = re.search(r"<title[^>]*>(.*?)</title>", doc, re.S | re.I)
    if not m_head or not m_title:
        skipped_other += 1
        continue
    title = re.sub(r"\s+", " ", html.unescape(strip_tags(m_title.group(1)))).strip()
    body = doc[m_head.end():]
    desc = truncate(first_paragraph(body), DESC_MAX)
    has_desc = bool(re.search(r'name=["\']description["\']', doc, re.I))
    has_canon = bool(re.search(r'rel=["\']canonical["\']', doc, re.I))
    block = build_block(title, desc, url, has_desc, has_canon)
    doc = doc[:m_head.start()] + block + doc[m_head.start():]
    path.write_text(doc, encoding="utf-8")
    modified += 1

print(f"gen_og_tags: {modified} pages updated, "
      f"{skipped_og} already had OG, {skipped_other} skipped (no file/head/title).")
