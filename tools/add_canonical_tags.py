#!/usr/bin/env python3
"""Add `<link rel="canonical" href="...">` to every public HTML page.

Without canonical tags, Google sees the same chapter at noblemind.study,
ipfs.noblemind.study, and ipfs.io/ipns/... and refuses to pick one — so
none get indexed. This script walks the same file set as gen_sitemap.py,
computes the canonical URL using the same rule, and inserts the tag in
<head> if it's missing.

Idempotent. Safe to re-run after deploys or after regenerating any book.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path('/home/smallpaul/noblemind-study')
BASE_URL = 'https://noblemind.study'

# Match gen_sitemap.py exactly so canonical and sitemap agree.
EXCLUDED_DIRS = {
    '.git', '.claude', 'console', '__pycache__', 'node_modules',
    'a_new_and_living_way',
    'strength_and_dignity',
    'ChangeTheMind_ChangeTheMan',
    'data',
    'tools',
    'archive',
    'admin',
}

EXCLUDED_FILES = {
    'set-admin.html',
}

CANONICAL_RE = re.compile(r'<link[^>]+rel=["\']canonical["\']', re.I)
NOINDEX_RE   = re.compile(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex', re.I)
HEAD_OPEN_RE = re.compile(r'<head\b[^>]*>', re.I)
TITLE_END_RE = re.compile(r'</title\s*>', re.I)
CHARSET_RE   = re.compile(r'<meta\s+charset[^>]*>', re.I)


def canonical_url_for(path: Path) -> str:
    rel = path.relative_to(ROOT)
    if rel.name == 'index.html' and rel.parent == Path('.'):
        return f'{BASE_URL}/'
    return f'{BASE_URL}/{rel.as_posix()}'


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return True
    if rel.name in EXCLUDED_FILES:
        return True
    name = rel.name
    if '.backup' in name or name.endswith('.bak'):
        return True
    if '_ocr_' in name or '_vaults' in name:
        return True
    return False


def insert_canonical(html: str, url: str) -> str | None:
    """Insert canonical tag inside <head>. Returns new HTML, or None if no
    <head> was found."""
    tag = f'<link rel="canonical" href="{url}">'

    # Prefer to insert right after </title> for readable head ordering.
    m = TITLE_END_RE.search(html)
    if m:
        return html[:m.end()] + '\n  ' + tag + html[m.end():]

    # Fall back to right after <meta charset>.
    m = CHARSET_RE.search(html)
    if m:
        return html[:m.end()] + '\n  ' + tag + html[m.end():]

    # Fall back to right after <head>.
    m = HEAD_OPEN_RE.search(html)
    if m:
        return html[:m.end()] + '\n  ' + tag + html[m.end():]

    return None


def main():
    added = 0
    already = 0
    noindex = 0
    nohead = 0
    skipped = 0

    for html_path in sorted(ROOT.rglob('*.html')):
        if should_skip(html_path):
            skipped += 1
            continue

        try:
            content = html_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            skipped += 1
            continue

        # Don't add canonical to noindex pages — pointless and possibly
        # contradictory.
        if NOINDEX_RE.search(content[:8192]):
            noindex += 1
            continue

        if CANONICAL_RE.search(content):
            already += 1
            continue

        url = canonical_url_for(html_path)
        new_content = insert_canonical(content, url)
        if new_content is None:
            nohead += 1
            print(f'  [no-head] {html_path.relative_to(ROOT)}')
            continue

        html_path.write_text(new_content, encoding='utf-8')
        added += 1

    print()
    print(f'Added canonical tag:     {added}')
    print(f'Already had canonical:   {already}')
    print(f'Skipped (noindex):       {noindex}')
    print(f'Skipped (no <head>):     {nohead}')
    print(f'Skipped (excluded):      {skipped}')


if __name__ == '__main__':
    main()
