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
.mark-complete {{
  display: inline-flex; align-items: center; gap: 10px;
  margin: 2.5rem auto 0; padding: 12px 20px;
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(196,168,84,0.25);
  border-radius: 10px;
  color: var(--text-secondary); cursor: pointer;
  font-family: inherit; font-size: 0.9rem;
  transition: all 0.3s;
}}
.mark-complete:hover {{
  background: rgba(196,168,84,0.12);
  border-color: var(--accent); color: var(--accent);
}}
.mark-complete.done {{
  background: rgba(196,168,84,0.15);
  border-color: var(--accent); color: var(--accent);
}}
.mark-complete .check {{
  width: 18px; height: 18px;
  border: 2px solid currentColor;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem;
}}
.mark-complete.done .check::after {{ content: "\\2713"; }}
.mark-row {{ text-align: center; }}
.footer-nav {{
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 2rem; padding-top: 1.5rem;
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
header { text-align: center; margin-bottom: 1.5rem; padding-bottom: 1.2rem; border-bottom: 1px solid rgba(196,81,63,0.2); }
header h1 {
  font-family: 'Cardo', Georgia, serif;
  font-size: 2.2rem; font-weight: 700;
  color: var(--accent); text-shadow: 0 0 20px var(--accent-glow);
  margin-bottom: 0.3rem;
}
header .subtitle { font-style: italic; color: var(--text-secondary); font-size: 1.05rem; margin-bottom: 0.3rem; }
header .author { color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 0.5rem; }
header .stats { color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.4rem; }
header .stats span { color: var(--accent); font-weight: 600; }
.return-link {
  display: inline-block; margin-top: 1rem;
  padding: 8px 18px;
  background: rgba(196,168,84,0.08);
  border: 1px solid rgba(196,168,84,0.25);
  border-radius: 8px;
  color: var(--accent-secondary); text-decoration: none;
  font-size: 0.9rem;
}
.return-link:hover { background: rgba(196,168,84,0.15); border-color: var(--accent-secondary); box-shadow: 0 0 15px var(--accent-secondary-glow); }
.hero-cover { text-align: center; margin: 1.5rem 0 0.5rem; }
.hero-cover img {
  max-width: 280px; width: 100%;
  height: auto; border-radius: 6px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 60px rgba(196,168,84,0.12);
  border: 1px solid rgba(196,168,84,0.15);
}
.key-verse {
  margin: 1.5rem 0; padding: 1.4rem;
  background: rgba(196,81,63,0.06);
  border-radius: 14px;
  border: 1px solid rgba(196,81,63,0.15);
  text-align: center;
  font-family: 'Cardo', Georgia, serif;
}
.key-verse blockquote {
  font-style: italic; color: var(--text-primary);
  font-size: 1.05rem; line-height: 1.7; margin-bottom: 0.6rem;
  border: none; background: none; padding: 0;
}
.key-verse cite { color: var(--accent); font-style: normal; font-variant: small-caps; letter-spacing: 0.05em; font-weight: 500; }
.intro-blurb { color: var(--text-secondary); font-family: 'Cardo', Georgia, serif; font-size: 1rem; line-height: 1.7; margin: 1.5rem 0; }
.progress-bar {
  margin: 1.5rem 0; padding: 1rem 1.2rem;
  background: rgba(196,168,84,0.04);
  border: 1px solid rgba(196,168,84,0.12);
  border-radius: 12px;
}
.progress-bar .label { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; }
.progress-bar .label span { color: var(--accent); font-weight: 600; }
.progress-track { height: 8px; background: rgba(0,0,0,0.3); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-secondary)); border-radius: 4px; transition: width 0.5s ease; }
.chapter-section { margin-bottom: 2rem; }
.section-header h2 {
  font-family: 'Cardo', Georgia, serif;
  font-size: 1.25rem; color: var(--accent-secondary);
  margin-bottom: 0.7rem;
  font-weight: 700;
}
.section-header .verse-label {
  font-size: 0.78rem; font-variant: small-caps;
  letter-spacing: 0.18em; color: var(--accent);
  display: block; margin-bottom: 0.2rem;
}
.lesson-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.lesson-card {
  display: block; position: relative;
  padding: 14px 18px;
  background: rgba(0,0,0,0.2);
  border-radius: 10px;
  border: 1px solid rgba(196,168,84,0.12);
  text-decoration: none;
  transition: all 0.3s;
}
.lesson-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 15px var(--accent-glow);
  transform: translateY(-2px);
}
.lesson-num { color: var(--accent); font-weight: 700; font-size: 0.85rem; }
.lesson-title { color: var(--text-primary); font-size: 0.95rem; margin-top: 4px; font-family: 'Cardo', Georgia, serif; }
.progress-dot {
  position: absolute; top: 12px; right: 14px;
  width: 10px; height: 10px;
  border-radius: 50%;
  border: 2px solid rgba(196,168,84,0.3);
  transition: all 0.3s;
}
.progress-dot.visited { border-color: var(--accent); background: rgba(196,168,84,0.3); }
.progress-dot.complete { border-color: var(--accent); background: var(--accent); }
footer { margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(196,168,84,0.15); text-align: center; }
.copyright { color: var(--text-muted); font-size: 0.78rem; margin-top: 0.6rem; }
.copyright a { color: var(--accent-secondary); text-decoration: none; }
"""

# Verse-based chapter groupings. The book opens with Ch01 (verses 1-3,
# the "if I have not love" stakes), closes with Ch16 (verses 8-13,
# love never fails), and the 14 attribute chapters group under the
# verse each is anchored in.
CHAPTER_GROUPS = [
    {
        "verse_label": "Verses 1-3 — The Stakes",
        "title": "Opening",
        "chapter_slugs": ["chapter-01"],
    },
    {
        "verse_label": "Verse 4 — The First Five",
        "title": "Love is patient, kind, not jealous; love does not brag and is not arrogant",
        "chapter_slugs": ["chapter-02", "chapter-03", "chapter-04",
                          "chapter-05", "chapter-06"],
    },
    {
        "verse_label": "Verse 5 — The Four That Follow",
        "title": "Love does not act unbecomingly, does not seek its own, is not provoked, does not take into account a wrong suffered",
        "chapter_slugs": ["chapter-07", "chapter-08", "chapter-09", "chapter-10"],
    },
    {
        "verse_label": "Verse 6 — The Hinge",
        "title": "Love does not rejoice in unrighteousness, but rejoices with the truth",
        "chapter_slugs": ["chapter-11"],
    },
    {
        "verse_label": "Verse 7 — The Positive Four",
        "title": "Love bears all things, believes all things, hopes all things, endures all things",
        "chapter_slugs": ["chapter-12", "chapter-13", "chapter-14", "chapter-15"],
    },
    {
        "verse_label": "Verses 8-13 — The Eternal Weight",
        "title": "Closing",
        "chapter_slugs": ["chapter-16"],
    },
]


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
    import re as _re
    select_html = select_options(sections, section["slug"])
    prev_html, next_html = nav_links(sections, idx)
    label = section["label_meta"]

    epigraph = ""
    if section["epigraph_html"]:
        eg = section["epigraph_html"].replace(
            '<blockquote class="scripture">',
            '<blockquote>'
        )
        epigraph = f'<div class="epigraph">{eg}</div>'

    page_title = select_label(section)

    # Mark-complete button for actual chapters (Ch01-Ch16) only
    m = _re.search(r"Chapter (\d+)", label)
    mark_html = ""
    mark_script = ""
    if m:
        ch_num = int(m.group(1))
        mark_html = f"""
      <div class="mark-row">
        <button class="mark-complete" id="mark-complete-btn" data-ch="{ch_num}">
          <span class="check"></span>
          <span class="label">Mark Complete</span>
        </button>
      </div>"""
        mark_script = f"""
  <script>
    var PROGRESS_KEY = 'theLoveGodCallsUsTo_progress';
    var CH = {ch_num};
    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}
    function saveProgress(p) {{
      try {{ localStorage.setItem(PROGRESS_KEY, JSON.stringify(p)); }}
      catch(e) {{}}
    }}
    document.addEventListener('DOMContentLoaded', function() {{
      var p = loadProgress();
      var key = 'ch' + CH;
      // Mark as visited on landing if not already complete
      if (p[key] !== 'complete') {{
        p[key] = 'visited';
        saveProgress(p);
      }}
      var btn = document.getElementById('mark-complete-btn');
      if (!btn) return;
      if (p[key] === 'complete') {{
        btn.classList.add('done');
        btn.querySelector('.label').textContent = 'Completed';
      }}
      btn.addEventListener('click', function() {{
        var p = loadProgress();
        var key = 'ch' + CH;
        if (p[key] === 'complete') {{
          p[key] = 'visited';
          btn.classList.remove('done');
          btn.querySelector('.label').textContent = 'Mark Complete';
        }} else {{
          p[key] = 'complete';
          btn.classList.add('done');
          btn.querySelector('.label').textContent = 'Completed';
        }}
        saveProgress(p);
      }});
    }});
  </script>"""

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
{mark_html}

      <div class="footer-nav">
        {prev_html}
        <div class="spacer"></div>
        {next_html}
      </div>

    </div>
  </div>
  {mark_script}
</body>
</html>"""


def _card(section):
    """One lesson-card link for the chapter grid."""
    label = section["label_meta"]
    title = section["title_meta"]
    # Strip the leading "Chapter N" label to a tight short form for the lesson-num pill
    short_label = label
    dot_attr = ""
    # Only attribute chapters (Ch01-Ch16) get progress dots tied to their number
    import re as _re
    m = _re.search(r"Chapter (\d+)", label)
    if m:
        n = int(m.group(1))
        dot_attr = f' data-ch="{n}"'
        return (
            f'<a href="{section["slug"]}.html" class="lesson-card"{dot_attr}>'
            f'<span class="lesson-num">{label}</span>'
            f'<div class="lesson-title">{title}</div>'
            f'<span class="progress-dot" id="dot-{n}"></span>'
            '</a>'
        )
    # Non-chapter cards (Dedication, Preface, Appendix A) — no progress dot
    return (
        f'<a href="{section["slug"]}.html" class="lesson-card">'
        f'<span class="lesson-num">{label}</span>'
        f'<div class="lesson-title">{title}</div>'
        '</a>'
    )


def build_index(sections):
    by_slug = {s["slug"]: s for s in sections}
    fm_sections = [s for s in sections if s["slug"] in ("dedication", "preface")]
    appendix_sections = [s for s in sections if s["slug"].startswith("appendix-")]

    # Build the front-matter grid (Dedication + Preface)
    fm_cards = "\n          ".join(_card(s) for s in fm_sections)

    # Build the verse-grouped chapter sections
    chapter_section_html = []
    for group in CHAPTER_GROUPS:
        cards_html = "\n          ".join(
            _card(by_slug[slug]) for slug in group["chapter_slugs"]
            if slug in by_slug
        )
        chapter_section_html.append(f"""
      <section class="chapter-section">
        <div class="section-header">
          <span class="verse-label">{group["verse_label"]}</span>
          <h2>{group["title"]}</h2>
        </div>
        <div class="lesson-grid">
          {cards_html}
        </div>
      </section>""")
    chapter_sections = "\n".join(chapter_section_html)

    appendix_cards = "\n          ".join(_card(s) for s in appendix_sections)

    # Anchor verse for the key-verse box — wrap as blockquote + cite
    key_verse_html = f"""
      <section class="key-verse">
        <blockquote>{bs.ANCHOR_VERSE}</blockquote>
        <cite>{bs.ANCHOR_CITE}</cite>
      </section>"""

    total_chapters = 16

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents | {bs.TITLE}</title>
  <link rel="canonical" href="https://noblemind.study/TheLoveGodCallsUsTo/index.html">
  <link href="https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  <style>{INDEX_CSS}</style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <header>
        <h1>{bs.TITLE}</h1>
        <p class="subtitle">{bs.SUBTITLE}</p>
        <p class="author">{bs.AUTHOR}</p>
        <p class="stats"><span>{total_chapters}</span> Chapters &bull; Preface &bull; Dedication &bull; Appendix</p>
        <a href="/books.html" class="return-link">&larr; Return to All Books</a>
      </header>

      <div class="hero-cover">
        <img src="cover_front.jpg" alt="{bs.TITLE} — book cover" loading="eager">
      </div>

      {key_verse_html}

      <p class="intro-blurb">{bs.DESCRIPTION}</p>

      <div class="progress-bar">
        <div class="label">
          <span>Reading Progress</span>
          <span id="progress-text">0 / {total_chapters} chapters</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
      </div>

      <section class="chapter-section">
        <div class="section-header">
          <h2>Before You Begin</h2>
        </div>
        <div class="lesson-grid">
          {fm_cards}
        </div>
      </section>

      {chapter_sections}

      <section class="chapter-section">
        <div class="section-header">
          <h2>Appendix</h2>
        </div>
        <div class="lesson-grid">
          {appendix_cards}
        </div>
      </section>

      <footer>
        <p class="copyright">{bs.TITLE} &copy; {bs.YEAR} {bs.AUTHOR}. All Rights Reserved.<br>
        Published by <a href="/books.html">{bs.PUBLISHER}</a></p>
      </footer>

    </div>
  </div>
  <script>
    var PROGRESS_KEY = 'theLoveGodCallsUsTo_progress';
    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}
    function updateProgressUI() {{
      var p = loadProgress();
      var complete = 0;
      for (var i = 1; i <= {total_chapters}; i++) {{
        var dot = document.getElementById('dot-' + i);
        if (!dot) continue;
        var status = p['ch' + i];
        if (status === 'complete') {{
          dot.className = 'progress-dot complete';
          complete++;
        }} else if (status === 'visited') {{
          dot.className = 'progress-dot visited';
        }}
      }}
      var txt = document.getElementById('progress-text');
      var fill = document.getElementById('progress-fill');
      if (txt) txt.textContent = complete + ' / {total_chapters} chapters';
      if (fill) fill.style.width = (complete / {total_chapters} * 100) + '%';
    }}
    document.addEventListener('DOMContentLoaded', updateProgressUI);
  </script>
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
