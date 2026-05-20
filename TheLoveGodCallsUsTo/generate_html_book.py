#!/usr/bin/env python3
"""Generate the online HTML chapter pages for The Love God Calls Us To.

Writes one dark-theme glass-page HTML file per section to the book
directory (dedication.html, preface.html, chapter-01.html ... chapter-16.html,
appendix-a.html) plus an index.html chapter-list page.

The online edition uses the GENERAL dedication only. The class edition
is for print gifts to students, not for the public website.

Usage:
    python3 generate_html_book.py
"""

import argparse
from pathlib import Path

import _book_source as bs

BOOK_DIR = Path(__file__).parent

# Accent palette for The Love God Calls Us To:
#   primary  warm red (love / scripture borders / links)
#   secondary  warm gold (highlights)
ACCENT_PRIMARY = "#C4513F"
ACCENT_PRIMARY_GLOW = "rgba(196, 81, 63, 0.4)"
ACCENT_SECONDARY = "#C4A854"
ACCENT_SECONDARY_GLOW = "rgba(196, 168, 84, 0.35)"


PAGE_CSS = f"""
:root {{
  --bg-dark: #0d0d0d;
  --bg-inner: rgba(13, 15, 20, 0.96);
  --text-primary: #f0ece4;
  --text-secondary: #c0b8a8;
  --text-muted: #8a8278;
  --accent: {ACCENT_PRIMARY};
  --accent-glow: {ACCENT_PRIMARY_GLOW};
  --accent-secondary: {ACCENT_SECONDARY};
  --accent-secondary-glow: {ACCENT_SECONDARY_GLOW};
  --scripture-border: {ACCENT_PRIMARY};
  --radius-card: 22px;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Segoe UI', Georgia, serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  font-size: 1.1rem;
  line-height: 1.85;
  min-height: 100vh;
  padding: 30px 20px;
}}
body::before {{
  content: "";
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0;
  background:
    radial-gradient(circle at top, rgba(196,81,63,0.06), transparent 50%),
    radial-gradient(circle at bottom, rgba(196,168,84,0.05), transparent 50%);
  pointer-events: none;
}}
.glass-page-wrapper {{
  position: relative;
  z-index: 10;
  border-radius: calc(var(--radius-card) + 4px);
  padding: 3px;
  background:
    radial-gradient(circle at top left, rgba(196,81,63,0.45), transparent 50%),
    radial-gradient(circle at top right, rgba(196,168,84,0.35), transparent 50%),
    radial-gradient(circle at bottom, rgba(196,81,63,0.20), transparent 55%);
  box-shadow:
    0 0 50px rgba(196,168,84,0.15),
    0 0 80px rgba(196,81,63,0.18);
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
}}
.glass-page-inner {{
  background: var(--bg-inner);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: var(--radius-card);
  padding: 3rem 2.5rem;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(148,163,184,0.15);
}}
.nav-controls {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px; margin: -3rem -2.5rem 2rem -2.5rem;
  background: rgba(0,0,0,0.25);
  border-bottom: 1px solid rgba(148,163,184,0.12);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
}}
.home-link {{
  color: var(--text-secondary); text-decoration: none;
  font-size: 0.9rem; letter-spacing: 0.04em;
  display: inline-flex; align-items: center; gap: 8px;
}}
.home-link svg {{ width: 16px; height: 16px; fill: currentColor; }}
.home-link:hover {{ color: var(--accent); }}
#chapter-select {{
  background: rgba(0,0,0,0.5); color: var(--text-primary);
  border: 1px solid rgba(148,163,184,0.25); border-radius: 6px;
  padding: 6px 10px; font-size: 0.85rem; max-width: 260px;
  font-family: inherit;
}}
header {{ text-align: center; margin-bottom: 2.5rem; }}
header .chapter-num {{
  font-variant: small-caps; letter-spacing: 0.25em;
  color: var(--accent-secondary); font-size: 0.85rem;
  margin-bottom: 0.7rem;
}}
header h1 {{
  font-family: 'Cardo', Georgia, serif;
  font-size: clamp(1.7rem, 3.5vw, 2.3rem);
  font-weight: 700; line-height: 1.2; color: var(--text-primary);
  letter-spacing: 0.01em;
}}
.epigraph {{
  margin: 2rem 1rem 2.5rem 1rem; text-align: center;
  font-style: italic; color: var(--text-secondary);
  font-family: 'Cardo', Georgia, serif;
  border-top: 1px solid rgba(148,163,184,0.18);
  border-bottom: 1px solid rgba(148,163,184,0.18);
  padding: 1.2rem 0;
}}
.epigraph blockquote {{
  margin: 0 0 0.5rem 0; border: none; padding: 0;
  font-size: 1.05rem; line-height: 1.55;
}}
.epigraph blockquote p {{ margin: 0; }}
.epigraph blockquote cite {{
  display: block; margin-top: 0.4rem;
  font-style: normal; font-variant: small-caps;
  letter-spacing: 0.05em; color: var(--accent);
  font-size: 0.85rem;
}}
.content {{ font-family: 'Cardo', Georgia, serif; font-size: 1.05rem; }}
.content p {{ margin-bottom: 1.1rem; }}
.content h2 {{
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.35rem; color: var(--accent-secondary);
  margin-top: 2rem; margin-bottom: 0.8rem;
  border-bottom: 1px solid rgba(196,168,84,0.25);
  padding-bottom: 0.3rem;
}}
.content h3 {{
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.15rem; color: var(--text-primary);
  margin-top: 1.5rem; margin-bottom: 0.5rem;
  font-weight: 700;
}}
.content blockquote {{
  margin: 1.3rem 1rem; padding: 0.8rem 1.1rem;
  border-left: 2px solid var(--scripture-border);
  background: rgba(196,81,63,0.06);
  border-radius: 0 4px 4px 0;
  font-style: italic; color: var(--text-secondary);
}}
.content blockquote p {{ margin-bottom: 0.4rem; }}
.content blockquote.scripture cite {{
  display: block; margin-top: 0.5rem; font-style: normal;
  font-variant: small-caps; letter-spacing: 0.05em;
  color: var(--accent); font-size: 0.85rem;
}}
.content blockquote cite {{
  display: block; margin-top: 0.5rem; font-style: normal;
  font-variant: small-caps; letter-spacing: 0.05em;
  color: var(--accent); font-size: 0.85rem;
}}
.content .divider {{
  text-align: center; margin: 2rem 0;
  color: var(--text-muted); letter-spacing: 0.3em;
}}
.content .reflection {{
  margin-top: 2.5rem; padding-top: 1.5rem;
  border-top: 1px solid rgba(148,163,184,0.18);
}}
.content .reflection-header {{ text-align: center; margin-bottom: 1rem; }}
.content .reflection-header h3 {{
  font-variant: small-caps; letter-spacing: 0.2em;
  color: var(--accent-secondary); border: none;
}}
.content .reflection-body p {{ margin-bottom: 1rem; }}
.footer-nav {{
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 3rem; padding-top: 1.5rem;
  border-top: 1px solid rgba(148,163,184,0.18);
}}
.footer-nav a {{
  color: var(--accent); text-decoration: none;
  font-size: 0.95rem; padding: 8px 0;
}}
.footer-nav a:hover {{ color: var(--accent-secondary); }}
.footer-nav .spacer {{ flex: 1; }}
@media (max-width: 600px) {{
  body {{ padding: 10px 6px; font-size: 1rem; }}
  .glass-page-inner {{ padding: 1.2rem 1rem; }}
  .nav-controls {{ flex-direction: column; gap: 8px; align-items: stretch; }}
  #chapter-select {{ max-width: 100%; }}
  header h1 {{ font-size: 1.5rem; }}
}}
"""

INDEX_CSS = PAGE_CSS + """
.book-title { text-align: center; margin-bottom: 1rem; }
.book-title h1 {
  font-family: 'Cardo', Georgia, serif;
  font-size: 2.1rem; font-weight: 700;
  color: var(--text-primary); margin-bottom: 0.3rem;
}
.book-title .subtitle {
  font-style: italic; color: var(--accent-secondary);
  font-size: 1.05rem; margin-bottom: 0.4rem;
}
.book-title .author {
  font-variant: small-caps; letter-spacing: 0.18em;
  color: var(--text-secondary); font-size: 0.9rem;
}
.toc-list { list-style: none; padding: 0; margin: 1.5rem 0; }
.toc-list li {
  margin: 0.4rem 0;
  border-bottom: 1px dashed rgba(148,163,184,0.12);
}
.toc-list li a {
  display: flex; justify-content: space-between;
  padding: 0.6rem 0.4rem;
  text-decoration: none; color: var(--text-primary);
  font-family: 'Cardo', Georgia, serif;
}
.toc-list li a:hover { background: rgba(196,168,84,0.06); color: var(--accent-secondary); }
.toc-list li .toc-label { color: var(--accent); font-variant: small-caps; letter-spacing: 0.1em; font-size: 0.85rem; min-width: 90px; }
.toc-list li .toc-title { flex: 1; text-align: left; padding-left: 1rem; }
.anchor-verse {
  text-align: center; font-style: italic; color: var(--text-secondary);
  font-family: 'Cardo', Georgia, serif;
  margin: 2rem 1rem; padding: 1rem 0;
  border-top: 1px solid rgba(148,163,184,0.18);
  border-bottom: 1px solid rgba(148,163,184,0.18);
}
.anchor-verse cite { display: block; margin-top: 0.4rem; font-style: normal; font-variant: small-caps; letter-spacing: 0.05em; color: var(--accent); font-size: 0.85rem; }
.intro-blurb { color: var(--text-secondary); font-family: 'Cardo', Georgia, serif; font-size: 1rem; line-height: 1.7; margin: 1.5rem 0; }
"""


def select_options(sections, current_slug):
    opts = ['<option value="">Jump to...</option>']
    for s in sections:
        sel = " selected" if s["slug"] == current_slug else ""
        opts.append(
            f'<option value="{s["slug"]}.html"{sel}>{select_label(s)}</option>'
        )
    return "\n        ".join(opts)


def select_label(section):
    if section["label_meta"].startswith("Chapter"):
        return f'{section["label_meta"]}: {section["title_meta"]}'
    if section["label_meta"].startswith("Appendix"):
        return f'{section["label_meta"]}: {section["title_meta"]}'
    if section["label_meta"] == "Inscription & Dedication":
        return "Dedication"
    return section["title_meta"]


def nav_links(sections, idx):
    prev_html = '<div></div>'
    next_html = '<div></div>'
    if idx > 0:
        prev = sections[idx - 1]
        prev_html = f'<a href="{prev["slug"]}.html">&larr; {select_label(prev)}</a>'
    if idx < len(sections) - 1:
        nxt = sections[idx + 1]
        next_html = f'<a href="{nxt["slug"]}.html">{select_label(nxt)} &rarr;</a>'
    return prev_html, next_html


def build_chapter_page(section, idx, sections):
    select_html = select_options(sections, section["slug"])
    prev_html, next_html = nav_links(sections, idx)
    label = select_label(section).split(":")[0] if ":" in select_label(section) else section["label_meta"]

    epigraph = ""
    if section["epigraph_html"]:
        # Convert scripture blockquote to epigraph layout
        eg = section["epigraph_html"].replace(
            '<blockquote class="scripture">',
            '<blockquote>'
        )
        epigraph = f'<div class="epigraph">{eg}</div>'

    page_title = select_label(section)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title} | {bs.TITLE}</title>
  <link rel="canonical" href="https://noblemind.study/TheLoveGodCallsUsTo/{section["slug"]}.html">
  <link href="https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          {bs.TITLE}
        </a>
        <select id="chapter-select" onchange="if(this.value)window.location.href=this.value">
        {select_html}
        </select>
      </nav>

      <header>
        <p class="chapter-num">{label}</p>
        <h1>{section["title_meta"]}</h1>
      </header>

      {epigraph}

      <div class="content">
{section["body_html"]}
      </div>

      <div class="footer-nav">
        {prev_html}
        <div class="spacer"></div>
        {next_html}
      </div>

    </div>
  </div>
</body>
</html>"""


def build_index(sections):
    toc_items = []
    for s in sections:
        toc_items.append(
            f'<li><a href="{s["slug"]}.html">'
            f'<span class="toc-label">{s["label_meta"]}</span>'
            f'<span class="toc-title">{s["title_meta"]}</span>'
            '</a></li>'
        )
    toc_html = "\n        ".join(toc_items)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{bs.TITLE}</title>
  <link rel="canonical" href="https://noblemind.study/TheLoveGodCallsUsTo/index.html">
  <link href="https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  <style>{INDEX_CSS}</style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="/books.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          All Books
        </a>
      </nav>

      <div class="book-title">
        <h1>{bs.TITLE}</h1>
        <p class="subtitle">{bs.SUBTITLE}</p>
        <p class="author">{bs.AUTHOR}</p>
      </div>

      <div class="anchor-verse">
        {bs.ANCHOR_VERSE}
        <cite>{bs.ANCHOR_CITE}</cite>
      </div>

      <p class="intro-blurb">{bs.DESCRIPTION}</p>

      <ul class="toc-list">
        {toc_html}
      </ul>

    </div>
  </div>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    args = ap.parse_args()

    print("Loading sections (general edition for online reader)...")
    sections = bs.load_all_sections(class_edition=False)
    print(f"  Loaded {len(sections)} sections")

    print("Writing chapter HTML files...")
    for idx, s in enumerate(sections):
        out_path = BOOK_DIR / f"{s['slug']}.html"
        html = build_chapter_page(s, idx, sections)
        out_path.write_text(html, encoding="utf-8")
        print(f"  {out_path.name}")

    print("Writing index.html...")
    index_path = BOOK_DIR / "index.html"
    index_path.write_text(build_index(sections), encoding="utf-8")
    print(f"  {index_path.name}")

    print(f"\nWrote {len(sections) + 1} HTML files to {BOOK_DIR}/")


if __name__ == "__main__":
    main()
