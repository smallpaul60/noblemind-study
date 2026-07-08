#!/usr/bin/env python3
"""Assemble the enhanced Strait Way collection + its searchable index into ONE
self-contained HTML file suitable for handing to the Henderson family website.

- Landing view = the existing searchable archive index.
- Each of the 57 issues is embedded as a hidden "issue view"; clicking an issue
  or article in the archive swaps to that issue (Back to Archive returns).
- Everything resolves in-file: no server, no external files, no build deps at runtime.
- Acts is a separate collection (Acts-Enhanced/) and is intentionally NOT included.
- Henderson-ready branding: Noble Mind nav link / canonical / OG tags removed;
  one quiet credit line kept in the footer.

Output: StraitWay-Enhanced/The_Strait_Way_Archive.html
"""
import json
import re
import pathlib
from bs4 import BeautifulSoup

SRC = pathlib.Path(__file__).resolve().parent.parent / "StraitWay-Enhanced"
OUT = SRC / "The_Strait_Way_Archive.html"
CANONICAL_ISSUE_STYLE = "strait-way-1999-01.html"  # the pretty-printed reference block

TAGLINE = '"Speaking the truth in love" — Ephesians 4:15'
GLOBAL_SELECTORS = {"*", "html", "body", "body::before", "body::after"}


# --------------------------------------------------------------------------- #
# tiny CSS helpers                                                            #
# --------------------------------------------------------------------------- #
def split_rules(css):
    """Split CSS into top-level (header, body) pairs, keeping nested @-blocks intact."""
    rules, header, i, n = [], "", 0, len(css)
    while i < n:
        c = css[i]
        if c == "{":
            depth, j = 1, i + 1
            while j < n and depth:
                if css[j] == "{":
                    depth += 1
                elif css[j] == "}":
                    depth -= 1
                j += 1
            rules.append((header.strip(), css[i + 1 : j - 1]))
            header, i = "", j
        else:
            header += c
            i += 1
    return rules


def scope_css(css, scope):
    """Prefix every selector with `scope`, except page-global element selectors.
    `:root` becomes the scope element so its custom properties stay contained."""
    out = []
    for sel, body in split_rules(css):
        if not sel:
            continue
        if sel.startswith("@media") or sel.startswith("@supports"):
            out.append(f"{sel} {{\n{scope_css(body, scope)}\n}}")
            continue
        if sel.startswith("@"):  # keyframes, font-face, etc. — leave alone
            out.append(f"{sel} {{{body}}}")
            continue
        parts = []
        for p in (s.strip() for s in sel.split(",")):
            if p == ":root":
                parts.append(scope)
            elif p in GLOBAL_SELECTORS:
                parts.append(p)  # page-level, keep unscoped
            else:
                parts.append(f"{scope} {p}")
        out.append(f"{', '.join(parts)} {{{body}}}")
    return "\n".join(out)


def norm(sel):
    return re.sub(r"\s+", " ", sel).strip()


# --------------------------------------------------------------------------- #
# gather styles                                                               #
# --------------------------------------------------------------------------- #
def style_of(path):
    m = re.search(r"<style>(.*?)</style>", path.read_text(), re.S)
    return m.group(1) if m else ""


def build_issue_stylesheet():
    """Canonical issue CSS + any extra selectors that only appear in some issues."""
    base = style_of(SRC / CANONICAL_ISSUE_STYLE)
    seen = {norm(sel) for sel, _ in split_rules(base)}
    extras = []
    for f in sorted(SRC.glob("strait-way-*.html")):
        for sel, body in split_rules(style_of(f)):
            key = norm(sel)
            if key and key not in seen:
                seen.add(key)
                extras.append(f"{sel} {{{body}}}")
    return base + "\n/* issue-specific extras */\n" + "\n".join(extras)


# --------------------------------------------------------------------------- #
# issue view assembly                                                         #
# --------------------------------------------------------------------------- #
HOME_SVG = ('<svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z">'
            "</path></svg>")


def slug_of(filename):
    return filename[:-5] if filename.endswith(".html") else filename


def namespace(piece, slug):
    """Prefix every id and in-page anchor within `piece` with the issue slug."""
    if piece.has_attr("id"):
        piece["id"] = f"{slug}-{piece['id']}"
    for el in piece.select("[id]"):
        el["id"] = f"{slug}-{el['id']}"
    for a in piece.select('a[href^="#"]'):
        a["href"] = f"#{slug}-{a['href'][1:]}"
    # neutralise stale links back to the old multi-file index
    for a in piece.select('a[href$="index.html"]'):
        a.replace_with(a.get_text())


def build_issue_view(issue):
    slug = slug_of(issue["filename"])
    soup = BeautifulSoup((SRC / issue["filename"]).read_text(), "html.parser")
    inner = soup.select_one(".glass-page-inner")

    nav = inner.find("nav", class_="nav-links")
    articles = inner.find_all("article", recursive=False)
    footer = soup.find("footer")

    # A handful of issues (2002-08..2002-12) shipped with articles that have no
    # id, and a nav bar left over from the January-1999 template (wrong labels,
    # dead anchors). Backfill ids from the article metadata (same order, counts
    # verified equal) and rebuild the nav when its links don't resolve.
    meta_articles = issue.get("articles", [])
    for i, art in enumerate(articles):
        if not art.get("id") and i < len(meta_articles):
            art["id"] = meta_articles[i]["id"]
    existing_ids = {a.get("id") for a in articles if a.get("id")}

    def nav_resolves(n):
        links = n.find_all("a") if n else []
        return bool(links) and all(
            a.get("href", "").startswith("#") and a["href"][1:] in existing_ids
            for a in links
        )

    if meta_articles and not nav_resolves(nav):
        if nav:
            nav.decompose()
        nav = soup.new_tag("nav", **{"class": "nav-links"})
        for a in meta_articles:
            link = soup.new_tag("a", href=f"#{a['id']}")
            link.string = a["title"]
            nav.append(link)

    out = BeautifulSoup("", "html.parser")
    section = out.new_tag("section", **{"class": "issue-view", "id": f"view-{slug}"})
    section["style"] = "display:none"
    wrapper = out.new_tag("div", **{"class": "glass-page-wrapper"})
    inner_div = out.new_tag("div", **{"class": "glass-page-inner"})

    header = BeautifulSoup(
        f'<header><h1 class="masthead">The Strait Way</h1>'
        f'<p class="tagline">{TAGLINE}</p>'
        f'<p class="issue-date">{issue["month_name"]} {issue["year"]}</p>'
        f'<a href="#/" class="home-link">{HOME_SVG} Back to Archive</a></header>',
        "html.parser",
    )
    inner_div.append(header)

    for piece in [nav, *articles, footer]:
        if piece is None:
            continue
        namespace(piece, slug)
        inner_div.append(piece)

    wrapper.append(inner_div)
    section.append(wrapper)
    out.append(section)
    return str(out)


# --------------------------------------------------------------------------- #
# archive (index) view + script                                              #
# --------------------------------------------------------------------------- #
def build_archive_view_and_script():
    html = (SRC / "index.html").read_text()
    body = re.search(r"<body>(.*?)<script>", html, re.S).group(1)
    script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)

    body_soup = BeautifulSoup(body, "html.parser")
    # drop the Noble Mind return link (Henderson-ready)
    rl = body_soup.select_one("a.return-link")
    if rl:
        rl.decompose()
    # quiet credit line in the archive footer
    footer = body_soup.find("footer")
    if footer:
        credit = BeautifulSoup(
            '<p class="credit">Enhanced digital edition prepared by Noble Mind Study'
            " · noblemind.study</p>",
            "html.parser",
        )
        footer.append(credit)

    archive = f'<div id="archive-view">{body_soup}</div>'

    # rewire the two generated links from separate-file hrefs to in-file hash routes
    script = script.replace(
        'title.innerHTML = `<a href="${issue.filename}">${issue.month_name} ${issue.year}</a>`;',
        'title.innerHTML = `<a class="issue-link" '
        'href="#/i/${issue.filename.replace(".html","")}">'
        '${issue.month_name} ${issue.year}</a>`;',
    )
    script = script.replace(
        'li.innerHTML = `<a href="${issue.filename}#${article.id}">${article.title}</a>` +',
        'li.innerHTML = `<a class="article-link" '
        'href="#/i/${issue.filename.replace(".html","")}/${article.id}">'
        '${article.title}</a>` +',
    )
    return archive, script


ROUTER_JS = r"""
    // ---- single-file view routing -------------------------------------------
    function showArchive() {
      document.getElementById('archive-view').style.display = '';
      document.querySelectorAll('.issue-view').forEach(v => v.style.display = 'none');
    }
    function showIssue(slug, articleId) {
      document.getElementById('archive-view').style.display = 'none';
      document.querySelectorAll('.issue-view').forEach(v => v.style.display = 'none');
      const view = document.getElementById('view-' + slug);
      if (!view) { showArchive(); return; }
      view.style.display = '';
      if (articleId) {
        const el = document.getElementById(slug + '-' + articleId);
        if (el) { el.scrollIntoView(); return; }
      }
      window.scrollTo(0, 0);
    }
    function route() {
      const h = location.hash;
      const m = h.match(/^#\/i\/([^\/]+)(?:\/(.+))?$/);
      if (m) {
        showIssue(decodeURIComponent(m[1]), m[2] ? decodeURIComponent(m[2]) : null);
      } else if (h === '' || h === '#' || h === '#/') {
        showArchive();
      }
      // any other hash (an in-issue anchor like #slug-editorial) is left to the
      // browser's native scroll; the current view stays as-is.
    }
    window.addEventListener('hashchange', route);
    window.addEventListener('DOMContentLoaded', route);
"""


# --------------------------------------------------------------------------- #
# assemble                                                                    #
# --------------------------------------------------------------------------- #
def main():
    meta = json.load(open(SRC / "metadata.json"))
    issues = meta["issues"]

    archive_css = scope_css(style_of(SRC / "index.html"), "#archive-view")
    issue_css = scope_css(build_issue_stylesheet(), ".issue-view")

    # page-level globals (background, reset) taken once from the index sheet
    page_globals = "\n".join(
        f"{sel} {{{body}}}"
        for sel, body in split_rules(style_of(SRC / "index.html"))
        if norm(sel) in GLOBAL_SELECTORS
    )

    archive_view, archive_script = build_archive_view_and_script()
    issue_views = "\n".join(build_issue_view(iss) for iss in issues)

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Strait Way — Newsletter Archive (1999–2003)</title>
  <meta name="description" content="The complete Strait Way newsletter archive (1999-2003). Speaking the truth in love — Ephesians 4:15. Searchable by year, author, or topic.">
  <style>
/* ============ page globals ============ */
{page_globals}
/* ============ archive (index) view ============ */
{archive_css}
/* ============ issue views ============ */
{issue_css}
/* ============ readability overrides ============ */
/* Some quotes sit as loose text directly in <blockquote> (no <p> wrapper), so
   the `blockquote p` colour never reaches them and they render dim. Colour the
   blockquote itself so every quoted line is high-contrast. */
.issue-view blockquote {{ color: var(--text-primary); }}
  </style>
</head>
<body>
{archive_view}
{issue_views}
  <script>
{archive_script}
{ROUTER_JS}
  </script>
</body>
</html>
"""
    OUT.write_text(doc)
    size_mb = OUT.stat().st_size / 1_000_000
    print(f"Wrote {OUT}")
    print(f"  {len(issues)} issues embedded · {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
