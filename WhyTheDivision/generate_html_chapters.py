#!/usr/bin/env python3
"""Generate HTML chapter files + index + preface/part pages for
'Why the Division Among Brethren?'.

Theme: Forest green (#3F5F3F) primary + muted sage (#88a888) secondary
on the standard NobleMind dark glassmorphism page.

This booklet has no cover image (typographic only) and no epilogue —
Chapter 11 (For Further Study) is the final chapter.

Output files (all in this book directory):
  index.html              — book landing page with chapter grid
  preface.html            — preface page
  part-1.html .. part-4.html  — part intro pages
  chapter-01.html .. chapter-11.html — chapter pages
"""

from pathlib import Path

from _book_source import (
    parse_book, md_body_to_html,
    TITLE, SUBTITLE, AUTHOR,
)

BOOK_DIR = Path(__file__).parent

# Theme — earthy forest green + muted sage
ACCENT_PRIMARY       = "#3F5F3F"
ACCENT_SECONDARY     = "#88a888"
ACCENT_PRIMARY_RGB   = "63, 95, 63"
ACCENT_SECONDARY_RGB = "136, 168, 136"

PROGRESS_KEY = "whyTheDivision_progress"

INTRO_PARAGRAPHS = [
    "A position must stand or fall on what the Scriptures actually teach.",
    "More than seventy years ago, a division took place among the churches "
    "of Christ. Most of those who live with its consequences today have "
    "never had the division fairly explained to them. They have been given "
    "labels instead of arguments, and one side&rsquo;s case rather than "
    "both.",
    "This booklet does what too rarely gets done. It states both positions "
    "&mdash; institutional and non-institutional &mdash; in the way their "
    "best advocates would state them, walks the relevant Scriptures text "
    "by text, and lets the text carry the conclusion. Eleven chapters "
    "across four parts, written for the reader who wants to think for "
    "himself in front of the open Bible.",
    "The aim is not persuasion by rhetoric. The aim is to read the Book.",
]


# ============================================================================
# NAV DROPDOWN
# ============================================================================

def build_chapter_select(current_key, book):
    """current_key is one of:
      "preface"
      ("part", p_idx)
      ("chapter", num)
      None
    """
    options = ['<option value="">Jump to...</option>']
    sel = ' selected' if current_key == "preface" else ''
    options.append(f'<option value="preface.html"{sel}>Preface</option>')

    for p_idx, part in enumerate(book["parts"], start=1):
        part_key = ("part", p_idx)
        sel = ' selected' if current_key == part_key else ''
        options.append(
            f'<option value="part-{p_idx}.html"{sel}>'
            f'─ {part["label"]}: {part["title"]} ─</option>'
        )
        for ch in part["chapters"]:
            key = ("chapter", ch["num"])
            sel = ' selected' if current_key == key else ''
            options.append(
                f'<option value="chapter-{ch["num"]:02d}.html"{sel}>'
                f'Ch {ch["num"]}: {ch["title"]}</option>'
            )

    return "\n          ".join(options)


# ============================================================================
# SHARED CSS (reading pages)
# ============================================================================

def page_css():
    return f"""
    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #c8c0b4;
      --text-muted: #8a8070;
      --accent: {ACCENT_PRIMARY};
      --accent-glow: rgba({ACCENT_PRIMARY_RGB}, 0.4);
      --accent-soft: rgba({ACCENT_PRIMARY_RGB}, 0.12);
      --accent-secondary: {ACCENT_SECONDARY};
      --accent-secondary-glow: rgba({ACCENT_SECONDARY_RGB}, 0.3);
      --scripture-border: {ACCENT_SECONDARY};
      --glass-blur: blur(12px);
      --radius-card: 22px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Georgia, serif;
      background: var(--bg-dark); color: var(--text-primary);
      font-size: 1.1rem; line-height: 1.85;
      min-height: 100vh; padding: 30px 20px;
    }}
    body::before {{
      content: ""; position: fixed; inset: 0; z-index: 0;
      background:
        radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.08), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.06), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative; z-index: 10;
      border-radius: calc(var(--radius-card) + 4px); padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_PRIMARY_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.4), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_PRIMARY_RGB},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15),
        0 0 80px rgba({ACCENT_PRIMARY_RGB},0.2);
      max-width: 860px; width: 100%; margin: 0 auto;
    }}
    .glass-page-inner {{
      background: var(--bg-inner);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card);
      padding: 3rem 2.5rem;
      position: relative; overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }}
    .glass-page-inner::before {{
      content: "";
      position: absolute; top: 0; left: 0; right: 0;
      height: 150px;
      background: radial-gradient(ellipse at top, rgba({ACCENT_PRIMARY_RGB},0.05), transparent 70%);
      pointer-events: none;
    }}
    .glass-tab {{
      position: absolute; bottom: -12px; left: 50%;
      transform: translateX(-50%);
      width: 100px; height: 14px; border-radius: 999px;
      background: radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_PRIMARY_RGB},0.4);
    }}
    .nav-controls {{
      display: flex; justify-content: space-between; align-items: center;
      flex-wrap: wrap; gap: 12px;
      margin-bottom: 28px; padding: 14px 18px;
      background: rgba({ACCENT_PRIMARY_RGB},0.04);
      border-radius: 12px;
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.12);
      position: relative; z-index: 1;
    }}
    .nav-controls a, .nav-controls select {{
      color: var(--text-primary); text-decoration: none;
      padding: 8px 14px; border-radius: 8px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.25);
      font-size: 0.85rem; transition: all 0.3s;
    }}
    .nav-controls a:hover, .nav-controls select:hover {{
      border-color: var(--accent); box-shadow: 0 0 10px var(--accent-glow);
    }}
    .nav-controls select {{
      cursor: pointer; min-width: 220px;
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2388a888' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      padding-right: 30px;
    }}
    .nav-controls select option {{
      background: var(--bg-dark); color: var(--text-primary);
    }}
    .home-link {{
      display: inline-flex; align-items: center; gap: 6px;
      color: var(--accent-secondary); font-size: 0.85rem;
    }}
    .home-link svg {{ width: 14px; height: 14px; fill: currentColor; }}
    header {{
      text-align: center;
      margin-bottom: 32px; padding-bottom: 24px;
      border-bottom: 1px solid rgba({ACCENT_PRIMARY_RGB},0.2);
      position: relative; z-index: 1;
    }}
    h1 {{
      font-size: 2.2rem;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      margin-bottom: 6px; font-weight: 600;
    }}
    .chapter-num {{
      font-size: 1.05rem;
      color: var(--text-secondary);
      margin-bottom: 6px; letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .content {{ position: relative; z-index: 1; }}
    .content p {{
      margin-bottom: 16px;
      color: var(--text-secondary);
      text-align: justify;
    }}
    .content h2 {{
      font-size: 1.4rem; color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
      margin-top: 32px; margin-bottom: 14px;
    }}
    .content h3 {{
      font-size: 1.15rem; color: var(--accent);
      margin-top: 24px; margin-bottom: 10px;
    }}
    blockquote.scripture {{
      margin: 20px 0; padding: 16px 20px;
      background: rgba({ACCENT_SECONDARY_RGB},0.06);
      border-left: 3px solid var(--scripture-border);
      border-radius: 0 10px 10px 0;
      font-style: italic;
    }}
    blockquote.scripture p {{
      margin-bottom: 0; color: var(--text-primary);
    }}
    blockquote.scripture cite {{
      display: block; margin-top: 6px;
      color: var(--accent-secondary);
      font-style: normal; font-weight: 500; font-size: 0.9rem;
    }}
    .mark-complete {{
      display: flex; align-items: center; justify-content: center; gap: 10px;
      margin: 30px 0 10px; padding: 12px;
      background: rgba({ACCENT_PRIMARY_RGB},0.06);
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.2);
      border-radius: 10px; cursor: pointer; transition: all 0.3s;
      user-select: none;
    }}
    .mark-complete:hover {{
      border-color: var(--accent);
      background: rgba({ACCENT_PRIMARY_RGB},0.1);
    }}
    .mark-complete.completed {{
      background: rgba({ACCENT_PRIMARY_RGB},0.12);
      border-color: var(--accent);
    }}
    .mark-complete .check {{
      width: 22px; height: 22px; border-radius: 50%;
      border: 2px solid var(--accent);
      display: flex; align-items: center; justify-content: center;
      font-size: 0.8rem; color: transparent; transition: all 0.3s;
    }}
    .mark-complete.completed .check {{
      background: var(--accent); color: #0d0d0d;
    }}
    .mark-complete span:last-child {{
      color: var(--accent-secondary); font-weight: 600; font-size: 0.9rem;
    }}
    .part-intro-body {{
      font-style: italic;
      color: var(--text-secondary);
      max-width: 580px;
      margin: 10px auto 0;
      text-align: left;
      font-size: 1.05rem;
      line-height: 1.8;
    }}
    .part-intro-body p {{
      margin-bottom: 14px;
    }}
    footer {{
      margin-top: 40px; padding-top: 24px;
      border-top: 1px solid rgba({ACCENT_PRIMARY_RGB},0.15);
      text-align: center; position: relative; z-index: 1;
    }}
    .footer-nav {{
      display: flex; justify-content: space-between; margin-bottom: 20px;
    }}
    .footer-nav a {{
      color: var(--accent-secondary); text-decoration: none;
      padding: 10px 20px; border-radius: 8px;
      background: rgba({ACCENT_SECONDARY_RGB},0.08);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB},0.25);
      transition: all 0.3s; font-size: 0.9rem;
    }}
    .footer-nav a:hover {{
      background: rgba({ACCENT_SECONDARY_RGB},0.15);
      box-shadow: 0 0 10px var(--accent-secondary-glow);
    }}
    .footer-nav a.disabled {{ opacity: 0.35; pointer-events: none; }}
    .copyright {{
      color: var(--text-muted); font-size: 0.78rem; margin-top: 12px;
    }}
    .copyright a {{ color: var(--accent-secondary); text-decoration: none; }}
    @media print {{
      body {{ background: white; color: #333; padding: 0; font-size: 11pt; line-height: 1.5; }}
      body::before {{ display: none; }}
      .glass-page-wrapper {{ box-shadow: none; background: none; padding: 0; max-width: 100%; }}
      .glass-page-inner {{ background: white; padding: 0.5in; border-radius: 0; border: none; }}
      .glass-page-inner::before {{ display: none; }}
      .glass-tab, .nav-controls, .footer-nav, .mark-complete {{ display: none; }}
      header {{ border-bottom: 2px solid #333; }}
      h1 {{ color: {ACCENT_PRIMARY}; text-shadow: none; font-size: 18pt; }}
      .content p {{ color: #333; }}
      blockquote.scripture {{ background: #f9f9f9; border-left-color: {ACCENT_SECONDARY}; }}
      .copyright {{ color: #999; }}
      a {{ color: #333; text-decoration: none; }}
    }}
    @media (max-width: 900px) {{
      body {{ padding: 20px 12px; }}
      .glass-page-inner {{ padding: 2rem 1.8rem; }}
      h1 {{ font-size: 1.8rem; }}
    }}
    @media (max-width: 600px) {{
      html {{ -webkit-text-size-adjust: 100%; }}
      body {{ padding: 10px 6px; font-size: 1rem; line-height: 1.75; }}
      .glass-page-wrapper {{ border-radius: 16px; padding: 2px; }}
      .glass-page-inner {{ padding: 1.2rem 1rem; border-radius: 14px; }}
      .glass-page-inner::before {{ height: 80px; }}
      .glass-tab {{ width: 60px; height: 10px; bottom: -8px; }}
      .nav-controls {{ flex-direction: column; padding: 10px 12px; gap: 8px; }}
      .nav-controls a, .nav-controls select {{
        padding: 10px 14px; font-size: 0.9rem; min-height: 44px;
      }}
      .nav-controls select {{ width: 100%; }}
      header {{ margin-bottom: 20px; padding-bottom: 16px; }}
      h1 {{ font-size: 1.4rem; }}
      .chapter-num {{ font-size: 0.95rem; }}
      .content p {{ text-align: left; margin-bottom: 14px; }}
      blockquote.scripture {{ padding: 12px 14px; margin: 16px 0; }}
      .mark-complete {{ min-height: 44px; padding: 12px; }}
      footer {{ margin-top: 28px; }}
      .footer-nav {{ flex-direction: column; gap: 10px; }}
      .footer-nav a {{
        text-align: center; padding: 12px 20px; min-height: 44px;
        display: flex; align-items: center; justify-content: center;
      }}
    }}"""


# ============================================================================
# PAGE BUILDERS
# ============================================================================

def _page_frame(title, inner_html, chapter_select, prev_link, next_link,
                progress_key_name, progress_id, mark_complete_label,
                prev_kbd, next_kbd):
    if next_kbd:
        next_kbd_js = f"if (e.key === 'ArrowRight') window.location.href = '{next_kbd}';"
    else:
        next_kbd_js = ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{page_css()}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          {TITLE}
        </a>
        <select id="chapter-select" onchange="goToChapter(this.value)">
          {chapter_select}
        </select>
      </nav>

      {inner_html}

      <div class="mark-complete" id="mark-complete" onclick="toggleComplete()">
        <div class="check" id="check-icon">&check;</div>
        <span>{mark_complete_label}</span>
      </div>

      <footer>
        <div class="footer-nav">
          {prev_link}
          {next_link}
        </div>
        <p class="copyright">{TITLE} &copy; {AUTHOR} 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var PROGRESS_KEY = '{progress_key_name}';
    var CH = '{progress_id}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}
    function saveProgress(p) {{ localStorage.setItem(PROGRESS_KEY, JSON.stringify(p)); }}
    function toggleComplete() {{
      var p = loadProgress();
      p[CH] = p[CH] === 'complete' ? 'visited' : 'complete';
      saveProgress(p);
      updateUI();
    }}
    function updateUI() {{
      var p = loadProgress();
      var el = document.getElementById('mark-complete');
      if (p[CH] === 'complete') el.classList.add('completed');
      else el.classList.remove('completed');
    }}
    function goToChapter(url) {{ if (url) window.location.href = url; }}
    document.addEventListener('DOMContentLoaded', function() {{
      var p = loadProgress();
      if (!p[CH]) {{ p[CH] = 'visited'; saveProgress(p); }}
      updateUI();
    }});
    document.addEventListener('keydown', function(e) {{
      if (e.key === 'ArrowLeft') window.location.href = '{prev_kbd}';
      {next_kbd_js}
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


def build_preface_html(book):
    content = md_body_to_html(book["preface_md"])
    inner = f"""
      <header>
        <p class="chapter-num">Preface</p>
        <h1>{TITLE}</h1>
      </header>
      <div class="content">{content}</div>
    """
    chapter_select = build_chapter_select("preface", book)
    prev_link = '<a href="index.html">&larr; Contents</a>'
    next_link = f'<a href="part-1.html">Part One &rarr;</a>'
    return _page_frame(
        title=f"Preface | {TITLE}",
        inner_html=inner,
        chapter_select=chapter_select,
        prev_link=prev_link,
        next_link=next_link,
        progress_key_name=PROGRESS_KEY,
        progress_id="preface",
        mark_complete_label="Mark Preface Complete",
        prev_kbd="index.html",
        next_kbd="part-1.html",
    )


def build_part_html(part, p_idx, book):
    content = md_body_to_html(part["intro_md"])
    inner = f"""
      <header>
        <p class="chapter-num">{part['label']}</p>
        <h1>{part['title']}</h1>
      </header>
      <div class="part-intro-body">{content}</div>
    """
    chapter_select = build_chapter_select(("part", p_idx), book)

    if p_idx == 1:
        prev_url = "preface.html"
        prev_label = "Preface"
    else:
        last_ch = book["parts"][p_idx - 2]["chapters"][-1]["num"]
        prev_url = f"chapter-{last_ch:02d}.html"
        prev_label = f"Chapter {last_ch}"

    next_ch = part["chapters"][0]["num"]
    next_url = f"chapter-{next_ch:02d}.html"

    prev_link = f'<a href="{prev_url}">&larr; {prev_label}</a>'
    next_link = f'<a href="{next_url}">Chapter {next_ch} &rarr;</a>'

    return _page_frame(
        title=f"{part['label']}: {part['title']} | {TITLE}",
        inner_html=inner,
        chapter_select=chapter_select,
        prev_link=prev_link,
        next_link=next_link,
        progress_key_name=PROGRESS_KEY,
        progress_id=f"part{p_idx}",
        mark_complete_label=f"Mark {part['label']} Read",
        prev_kbd=prev_url,
        next_kbd=next_url,
    )


def _part_index_of(book, chapter_num):
    for p_idx, part in enumerate(book["parts"], start=1):
        for ch in part["chapters"]:
            if ch["num"] == chapter_num:
                return p_idx
    return None


def build_chapter_html(ch, book):
    content = md_body_to_html(ch["md"])
    inner = f"""
      <header>
        <p class="chapter-num">{ch['label']}</p>
        <h1>{ch['title']}</h1>
      </header>
      <div class="content">{content}</div>
    """
    chapter_select = build_chapter_select(("chapter", ch["num"]), book)

    all_chapters = book["chapters"]
    num = ch["num"]
    idx = next(i for i, c in enumerate(all_chapters) if c["num"] == num)

    # Prev: previous chapter (or this part's intro if it's the first chapter
    # of a non-first part), or part-1 intro if it's chapter 1.
    if idx == 0:
        prev_url = "part-1.html"
        prev_label = "Part One"
    else:
        prev_ch = all_chapters[idx - 1]
        part_of_prev = _part_index_of(book, prev_ch["num"])
        part_of_this = _part_index_of(book, num)
        if part_of_prev != part_of_this:
            prev_url = f"part-{part_of_this}.html"
            prev_label = book["parts"][part_of_this - 1]["label"]
        else:
            prev_url = f"chapter-{prev_ch['num']:02d}.html"
            prev_label = f"Chapter {prev_ch['num']}"

    # Next: next chapter, OR next part intro if crossing parts, OR
    # back to index if it's the last chapter (no epilogue in this book).
    if idx == len(all_chapters) - 1:
        next_url = "index.html"
        next_label = "Contents"
    else:
        next_ch = all_chapters[idx + 1]
        part_of_this = _part_index_of(book, num)
        part_of_next = _part_index_of(book, next_ch["num"])
        if part_of_next != part_of_this:
            next_url = f"part-{part_of_next}.html"
            next_label = book["parts"][part_of_next - 1]["label"]
        else:
            next_url = f"chapter-{next_ch['num']:02d}.html"
            next_label = f"Chapter {next_ch['num']}"

    prev_link = f'<a href="{prev_url}">&larr; {prev_label}</a>'
    next_link = f'<a href="{next_url}">{next_label} &rarr;</a>'

    return _page_frame(
        title=f"Chapter {num}: {ch['title']} | {TITLE}",
        inner_html=inner,
        chapter_select=chapter_select,
        prev_link=prev_link,
        next_link=next_link,
        progress_key_name=PROGRESS_KEY,
        progress_id=f"ch{num}",
        mark_complete_label="Mark Chapter Complete",
        prev_kbd=prev_url,
        next_kbd=next_url,
    )


# ============================================================================
# INDEX PAGE
# ============================================================================

def build_index_html(book):
    preface_card = f"""
      <a href="preface.html" class="lesson-card" data-pref>
        <span class="lesson-num">Preface</span>
        <div class="lesson-title">Read this first</div>
        <span class="progress-dot" id="dot-preface"></span>
      </a>
    """

    part_sections = ""
    total_chapters = len(book["chapters"])
    for p_idx, part in enumerate(book["parts"], start=1):
        part_cards = f"""
          <a href="part-{p_idx}.html" class="lesson-card lesson-card-part">
            <span class="lesson-num">{part['label']} intro</span>
            <div class="lesson-title">{part['title']}</div>
            <span class="progress-dot" id="dot-part{p_idx}"></span>
          </a>"""
        for ch in part["chapters"]:
            part_cards += f"""
          <a href="chapter-{ch['num']:02d}.html" class="lesson-card" data-ch="{ch['num']}">
            <span class="lesson-num">Chapter {ch['num']}</span>
            <div class="lesson-title">{ch['title']}</div>
            <span class="progress-dot" id="dot-ch{ch['num']}"></span>
          </a>"""
        part_sections += f"""
      <section class="chapter-section">
        <div class="section-header">
          <h2>{part['label']}: {part['title']}</h2>
        </div>
        <div class="lesson-grid">{part_cards}
        </div>
      </section>
        """

    intro_html = "\n".join(f"        <p>{p}</p>" for p in INTRO_PARAGRAPHS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents | {TITLE}</title>
  <style>
    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #c8c0b4;
      --text-muted: #8a8070;
      --accent: {ACCENT_PRIMARY};
      --accent-glow: rgba({ACCENT_PRIMARY_RGB}, 0.4);
      --accent-soft: rgba({ACCENT_PRIMARY_RGB}, 0.12);
      --accent-secondary: {ACCENT_SECONDARY};
      --accent-secondary-glow: rgba({ACCENT_SECONDARY_RGB}, 0.3);
      --glass-blur: blur(12px);
      --radius-card: 22px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Georgia, serif;
      background: var(--bg-dark); color: var(--text-primary);
      font-size: 1.1rem; line-height: 1.85;
      min-height: 100vh; padding: 30px 20px;
    }}
    body::before {{
      content: ""; position: fixed; inset: 0; z-index: 0;
      background:
        radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.08), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.06), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative; z-index: 10;
      border-radius: calc(var(--radius-card) + 4px); padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_PRIMARY_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.4), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_PRIMARY_RGB},0.2), transparent 55%);
      box-shadow: 0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15), 0 0 80px rgba({ACCENT_PRIMARY_RGB},0.2);
      max-width: 860px; width: 100%; margin: 0 auto;
    }}
    .glass-page-inner {{
      background: var(--bg-inner); backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card); padding: 3rem 2.5rem;
      position: relative; overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }}
    .glass-tab {{
      position: absolute; bottom: -12px; left: 50%;
      transform: translateX(-50%);
      width: 100px; height: 14px; border-radius: 999px;
      background: radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_PRIMARY_RGB},0.4);
    }}
    header {{
      text-align: center; margin-bottom: 32px; padding-bottom: 24px;
      border-bottom: 1px solid rgba({ACCENT_PRIMARY_RGB},0.2);
      position: relative; z-index: 1;
    }}
    h1 {{
      font-size: 2.0rem; color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      margin-bottom: 8px; font-weight: 600;
      padding: 0 0.5em;
    }}
    .subtitle {{
      font-size: 1.0rem; color: var(--text-secondary);
      font-style: italic; margin-bottom: 8px; padding: 0 1em;
    }}
    .author {{ font-size: 0.9rem; color: var(--text-muted); margin-bottom: 4px; }}
    .stats {{ margin-top: 12px; color: var(--text-secondary); font-size: 0.9rem; }}
    .stats span {{ color: var(--accent-secondary); font-weight: 600; }}
    .return-link {{
      display: inline-block; margin-top: 18px;
      padding: 10px 20px;
      background: rgba({ACCENT_SECONDARY_RGB},0.08);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB},0.25);
      border-radius: 8px;
      color: var(--accent-secondary); text-decoration: none;
      font-size: 0.9rem; transition: all 0.3s ease;
    }}
    .return-link:hover {{
      background: rgba({ACCENT_SECONDARY_RGB},0.15);
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
    }}
    .intro-blurb {{
      margin: 24px 0; padding: 22px 24px;
      background: rgba({ACCENT_PRIMARY_RGB},0.04);
      border-radius: 14px;
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.15);
      position: relative; z-index: 1;
    }}
    .intro-blurb p {{
      color: var(--text-secondary);
      margin-bottom: 14px; text-align: justify;
      font-size: 1rem; line-height: 1.75;
    }}
    .intro-blurb p:first-child {{
      color: var(--accent-secondary);
      font-style: italic;
      text-align: center;
      font-size: 1.1rem;
    }}
    .intro-blurb p:last-child {{ margin-bottom: 0; }}
    .progress-bar {{
      margin: 20px 0; padding: 14px 18px;
      background: rgba({ACCENT_PRIMARY_RGB},0.04);
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.12);
      border-radius: 12px;
      position: relative; z-index: 1;
    }}
    .progress-bar .label {{
      color: var(--text-muted); font-size: 0.85rem;
      margin-bottom: 8px;
      display: flex; justify-content: space-between;
    }}
    .progress-bar .label span {{ color: var(--accent-secondary); font-weight: 600; }}
    .progress-track {{
      height: 8px; background: rgba(0,0,0,0.3);
      border-radius: 4px; overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
      border-radius: 4px; transition: width 0.5s ease;
    }}
    .chapter-section {{
      margin-bottom: 32px; position: relative; z-index: 1;
    }}
    .section-header h2 {{
      font-size: 1.25rem; color: var(--accent-secondary);
      margin-bottom: 14px;
    }}
    .lesson-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
    }}
    .lesson-card {{
      display: block; position: relative;
      padding: 14px 18px;
      background: rgba(0,0,0,0.2);
      border-radius: 10px;
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.12);
      text-decoration: none; transition: all 0.3s;
    }}
    .lesson-card:hover {{
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
      transform: translateY(-2px);
    }}
    .lesson-card-part {{
      background: rgba({ACCENT_SECONDARY_RGB},0.08);
      border-color: rgba({ACCENT_SECONDARY_RGB},0.25);
    }}
    .lesson-card-part:hover {{ border-color: var(--accent-secondary); }}
    .lesson-num {{
      color: var(--accent-secondary); font-weight: 700; font-size: 0.85rem;
    }}
    .lesson-card-part .lesson-num {{ color: var(--accent-secondary); }}
    .lesson-title {{
      color: var(--text-primary); font-size: 0.95rem; margin: 4px 0;
    }}
    .progress-dot {{
      position: absolute; top: 12px; right: 14px;
      width: 10px; height: 10px; border-radius: 50%;
      border: 2px solid rgba({ACCENT_SECONDARY_RGB},0.3);
      transition: all 0.3s;
    }}
    .progress-dot.visited {{
      border-color: var(--accent-secondary);
      background: rgba({ACCENT_SECONDARY_RGB},0.3);
    }}
    .progress-dot.complete {{
      border-color: var(--accent-secondary);
      background: var(--accent-secondary);
    }}
    footer {{
      margin-top: 40px; padding-top: 24px;
      border-top: 1px solid rgba({ACCENT_PRIMARY_RGB},0.15);
      text-align: center; position: relative; z-index: 1;
    }}
    .copyright {{
      color: var(--text-muted); font-size: 0.78rem; margin-top: 12px;
    }}
    .copyright a {{ color: var(--accent-secondary); text-decoration: none; }}
    @media (max-width: 600px) {{
      html {{ -webkit-text-size-adjust: 100%; }}
      body {{ padding: 10px 6px; font-size: 1rem; line-height: 1.75; }}
      .glass-page-wrapper {{ border-radius: 16px; padding: 2px; }}
      .glass-page-inner {{ padding: 1.2rem 1rem; border-radius: 14px; }}
      .glass-tab {{ width: 60px; height: 10px; bottom: -8px; }}
      header {{ margin-bottom: 20px; padding-bottom: 16px; }}
      h1 {{ font-size: 1.4rem; }}
      .return-link {{ padding: 10px 16px; min-height: 44px; display: inline-flex; align-items: center; }}
      .progress-bar {{ padding: 12px 14px; }}
      .intro-blurb {{ padding: 16px 14px; }}
      .intro-blurb p {{ font-size: 0.95rem; text-align: left; }}
      .section-header h2 {{ font-size: 1.1rem; }}
      .lesson-grid {{ grid-template-columns: 1fr; gap: 10px; }}
      .lesson-card {{ padding: 14px 16px; min-height: 44px; }}
    }}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <header>
        <h1>{TITLE}</h1>
        <p class="subtitle">{SUBTITLE}</p>
        <p class="author">{AUTHOR}</p>
        <p class="stats">
          <span>{total_chapters}</span> Chapters &bull;
          <span>{len(book['parts'])}</span> Parts
        </p>
        <a href="../books.html" class="return-link">&larr; Return to Books</a>
      </header>

      <section class="intro-blurb">
{intro_html}
      </section>

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
          <h2>Before We Begin</h2>
        </div>
        <div class="lesson-grid">{preface_card}
        </div>
      </section>

      {part_sections}

      <footer>
        <p class="copyright">{TITLE} &copy; {AUTHOR} 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var TOTAL_CHAPTERS = {total_chapters};
    var CHAPTER_NUMS = {[ch['num'] for ch in book['chapters']]!r};
    var TOTAL_PARTS = {len(book['parts'])};
    var PROGRESS_KEY = '{PROGRESS_KEY}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}
    function applyDot(id, status) {{
      var dot = document.getElementById(id);
      if (!dot) return;
      if (status === 'complete') dot.className = 'progress-dot complete';
      else if (status === 'visited') dot.className = 'progress-dot visited';
    }}
    function updateProgressUI() {{
      var p = loadProgress();
      var complete = 0;
      CHAPTER_NUMS.forEach(function(n) {{
        var s = p['ch' + n];
        applyDot('dot-ch' + n, s);
        if (s === 'complete') complete++;
      }});
      applyDot('dot-preface', p['preface']);
      for (var i = 1; i <= TOTAL_PARTS; i++) {{
        applyDot('dot-part' + i, p['part' + i]);
      }}
      document.getElementById('progress-text').textContent =
        complete + ' / ' + TOTAL_CHAPTERS + ' chapters';
      document.getElementById('progress-fill').style.width =
        (complete / TOTAL_CHAPTERS * 100) + '%';
    }}
    document.addEventListener('DOMContentLoaded', updateProgressUI);
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f'Generating HTML chapter files for "{TITLE}"...')
    print(f"  Theme: Forest Green ({ACCENT_PRIMARY}) + Muted Sage ({ACCENT_SECONDARY})")

    book = parse_book()
    print(f"  Parsed: {len(book['chapters'])} chapters across "
          f"{len(book['parts'])} parts")

    print("  Writing index.html")
    (BOOK_DIR / "index.html").write_text(build_index_html(book), encoding='utf-8')

    print("  Writing preface.html")
    (BOOK_DIR / "preface.html").write_text(build_preface_html(book), encoding='utf-8')

    for p_idx, part in enumerate(book["parts"], start=1):
        out = f"part-{p_idx}.html"
        print(f"  Writing {out}: {part['label']} - {part['title']}")
        (BOOK_DIR / out).write_text(build_part_html(part, p_idx, book), encoding='utf-8')

    for ch in book["chapters"]:
        out = f"chapter-{ch['num']:02d}.html"
        print(f"  Writing {out}: {ch['title']}")
        (BOOK_DIR / out).write_text(build_chapter_html(ch, book), encoding='utf-8')

    print(f"\nDone. Wrote index + preface + {len(book['parts'])} parts + "
          f"{len(book['chapters'])} chapters.")


if __name__ == "__main__":
    main()
