#!/usr/bin/env python3
"""Generate /sitemap.xml and /robots.txt for noblemind.study.

Walks the project root for HTML files, excludes backups/drafts/admin/gated
content and any page carrying <meta name="robots" content="noindex">, then
emits an XML sitemap with per-section priority hints.
"""
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/home/smallpaul/noblemind-study')
BASE_URL = 'https://noblemind.study'

# Drafts / admin / gated books — exclude whole subtrees.
EXCLUDED_DIRS = {
    '.git', '.claude', 'console', '__pycache__', 'node_modules',
    'a_new_and_living_way',               # lowercase draft (superseded)
    'strength_and_dignity',               # lowercase draft (superseded)
    'ChangeTheMind_ChangeTheMan',         # password-gated online reader
    'data',                               # principles source, not a page
    'test-this-claim',                    # handled separately (noindex filter)
    'tools',                              # internal admin utilities (book-config-generator)
    'archive',                            # archived superseded books, not deployed
}

EXCLUDED_FILES = {
    'set-admin.html',                     # admin
}

# Priority / changefreq by path prefix. First match wins.
PRIORITY_RULES = [
    (lambda url: url == f'{BASE_URL}/',                              ('1.0', 'weekly')),
    (lambda url: url.startswith(f'{BASE_URL}/principles.html'),      ('0.9', 'monthly')),
    (lambda url: url.startswith(f'{BASE_URL}/Noble_Mind_Study_Tool'),('0.9', 'monthly')),
    (lambda url: url.startswith(f'{BASE_URL}/test-this-claim/'),     ('0.8', 'monthly')),
    (lambda url: url.startswith(f'{BASE_URL}/books.html'),           ('0.8', 'weekly')),
    (lambda url: url.startswith(f'{BASE_URL}/user-guide'),           ('0.7', 'monthly')),
    # Book chapters / front matter
    (lambda url: '/chapter-' in url or '/front-matter' in url
                  or '/foreword' in url or '/authors-note' in url
                  or '/introduction' in url or '/conclusion' in url
                  or '/preface' in url or '/appendix' in url
                  or '/acts-lesson-' in url or '/strait-way-' in url,  ('0.5', 'yearly')),
    # Book index pages
    (lambda url: url.endswith('/index.html'),                         ('0.7', 'monthly')),
    # Fallback
    (lambda url: True,                                                 ('0.5', 'yearly')),
]

def is_noindex(path: Path) -> bool:
    try:
        head = path.read_text(encoding='utf-8', errors='replace')[:8192]
    except OSError:
        return False
    return bool(re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', head, re.I))

def classify(url):
    for test, value in PRIORITY_RULES:
        if test(url):
            return value
    return ('0.5', 'yearly')

# Walk the top-level site
urls = []

def add(path: Path):
    rel = path.relative_to(ROOT)
    if rel.name == 'index.html' and rel.parent == Path('.'):
        url = f'{BASE_URL}/'
    else:
        url = f'{BASE_URL}/{rel.as_posix()}'
    mtime = path.stat().st_mtime
    lastmod = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime('%Y-%m-%d')
    prio, freq = classify(url)
    urls.append((url, lastmod, prio, freq))

for html in sorted(ROOT.rglob('*.html')):
    rel = html.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        continue
    if rel.name in EXCLUDED_FILES:
        continue
    if '.backup' in rel.name or rel.name.endswith('.bak'):
        continue
    # Skip files matching *_ocr_improved_*.html (legacy)
    if '_ocr_' in rel.name or '_vaults' in rel.name:
        continue
    if is_noindex(html):
        continue
    add(html)

# Separately handle /test-this-claim/ — we excluded the whole subtree above,
# so we re-add only the pages WITHOUT noindex.
for html in sorted((ROOT / 'test-this-claim').rglob('*.html')):
    if is_noindex(html):
        continue
    add(html)

# Deduplicate (shouldn't be any, but be safe)
seen = set()
unique = []
for u in urls:
    if u[0] not in seen:
        seen.add(u[0])
        unique.append(u)
urls = sorted(unique, key=lambda u: (-float(u[2]), u[0]))

# Emit sitemap.xml
out = ['<?xml version="1.0" encoding="UTF-8"?>']
out.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
for url, lastmod, prio, freq in urls:
    out.append('  <url>')
    out.append(f'    <loc>{url}</loc>')
    out.append(f'    <lastmod>{lastmod}</lastmod>')
    out.append(f'    <changefreq>{freq}</changefreq>')
    out.append(f'    <priority>{prio}</priority>')
    out.append('  </url>')
out.append('</urlset>')
out.append('')

sitemap_path = ROOT / 'sitemap.xml'
sitemap_path.write_text('\n'.join(out), encoding='utf-8')

# Emit robots.txt
robots = [
    '# noblemind.study — robots policy',
    '',
    'User-agent: *',
    'Allow: /',
    '',
    '# Admin / ops pages',
    'Disallow: /set-admin.html',
    '',
    '# API endpoints (analytics beacon)',
    'Disallow: /api/',
    '',
    '# Analytics console',
    'Disallow: /console',
    '',
    f'Sitemap: {BASE_URL}/sitemap.xml',
    '',
]
robots_path = ROOT / 'robots.txt'
robots_path.write_text('\n'.join(robots), encoding='utf-8')

# Summary
print(f'Wrote {sitemap_path.relative_to(ROOT)} — {len(urls)} URLs')
print(f'Wrote {robots_path.relative_to(ROOT)}')
print()
# Section breakdown
from collections import Counter
sections = Counter()
for u, _, _, _ in urls:
    # Trim to top-level directory
    path = u.replace(BASE_URL, '').strip('/')
    top = path.split('/')[0] if path else '(root)'
    sections[top] += 1
for section, count in sorted(sections.items(), key=lambda p: -p[1]):
    print(f'  {count:4d}  {section}')
