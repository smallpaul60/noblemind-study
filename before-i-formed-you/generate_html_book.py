#!/usr/bin/env python3
"""Generate HTML chapter files and index page for Before I Formed You.

Theme: Warm gold (#C4A060) + Sage green (#8B9B7A)
Target audience: Women facing an unexpected pregnancy.
"""

import re
from pathlib import Path
import markdown

BOOK_DIR = Path(__file__).parent

# (md_file, chapter_label, title, output_file)
PAGES = [
    ("preface-before-i-formed-you.md", None, "Preface", "preface.html"),
    ("chapter1-before-i-formed-you.md", "Chapter One", "El Roi: The God Who Sees You", "chapter-01.html"),
    ("chapter2-before-i-formed-you.md", "Chapter Two", "Fearfully and Wonderfully Made", "chapter-02.html"),
    ("chapter3-before-i-formed-you.md", "Chapter Three", "A Basket in the River", "chapter-03.html"),
    ("chapter4-before-i-formed-you.md", "Chapter Four", "A Prayer Through Tears", "chapter-04.html"),
    ("chapter5-before-i-formed-you.md", "Chapter Five", "Gleaning at the Edges", "chapter-05.html"),
    ("chapter6-before-i-formed-you.md", "Chapter Six", "The Least Likely", "chapter-06.html"),
    ("chapter7-before-i-formed-you.md", "Chapter Seven", "Be It Done to Me", "chapter-07.html"),
    ("chapter8-before-i-formed-you.md", "Chapter Eight", "For Such a Time as This", "chapter-08.html"),
    ("closing-before-i-formed-you.md", None, "You Are Not Alone", "closing.html"),
]

TOTAL_CHAPTERS = 8  # numbered chapters only (for progress tracking)

# Warm gold + sage green theme
ACCENT_PRIMARY = "#C4A060"          # Warm gold
ACCENT_SECONDARY = "#8B9B7A"       # Sage green (reeds)
ACCENT_PRIMARY_RGB = "196, 160, 96"
ACCENT_SECONDARY_RGB = "139, 155, 122"

PROGRESS_KEY = "beforeIFormedYou_progress"


def convert_md_to_html(md_text):
    """Convert chapter markdown to HTML content, stripping H1 and H2 headings."""
    # Remove the H1 heading (e.g. "# Before I Formed You -- Chapter 1")
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    # Remove the H2 heading (e.g. "## El Roi: The God Who Sees You")
    md_text = re.sub(r'^##\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()

    html = markdown.markdown(md_text, extensions=['smarty'])

    # Convert markdown blockquotes to styled scripture blockquotes
    def convert_scripture_bq(match):
        inner = match.group(1).strip()
        inner = re.sub(r'^<p>(.*)</p>$', r'\1', inner, flags=re.DOTALL).strip()

        parts = re.split(r'\s*[—–]\s*(?=<strong>)', inner, maxsplit=1)
        if len(parts) == 2:
            quote_text = parts[0].strip()
            cite_text = parts[1].strip()
            quote_text = re.sub(r'^<em>(.*)</em>$', r'\1', quote_text, flags=re.DOTALL)
            quote_text = quote_text.strip('\u201c\u201d"')
            quote_text = re.sub(r'^(&ldquo;|&rdquo;|&lsquo;|&rsquo;)+', '', quote_text)
            quote_text = re.sub(r'(&ldquo;|&rdquo;|&lsquo;|&rsquo;)+$', '', quote_text)
            cite_text = re.sub(r'</?strong>', '', cite_text)
            cite_text = re.sub(r',?\s*NASB\s*$', '', cite_text).strip()
            return (
                f'<blockquote class="scripture">'
                f'<p>&ldquo;{quote_text}&rdquo;</p>'
                f'<cite>&mdash; {cite_text}</cite>'
                f'</blockquote>'
            )
        return match.group(0)

    html = re.sub(
        r'<blockquote>\s*(.*?)\s*</blockquote>',
        convert_scripture_bq,
        html,
        flags=re.DOTALL
    )

    # Convert horizontal rules to decorative dividers
    html = re.sub(r'<hr\s*/?>', '<div class="divider">&#10045; &#10045; &#10045;</div>', html)

    return html


def build_chapter_select(current_file):
    """Build the chapter dropdown select."""
    options = ['<option value="">Jump to...</option>']
    for _, label, title, out_file in PAGES:
        sel = ' selected' if out_file == current_file else ''
        display = f"{label}: {title}" if label else title
        options.append(
            f'<option value="{out_file}"{sel}>{display}</option>'
        )
    return "\n          ".join(options)


def get_chapter_number(page_index):
    """Return the chapter number (1-8) for a given page index, or None."""
    _, label, _, _ = PAGES[page_index]
    if label and label.startswith("Chapter"):
        return page_index  # chapters are at indices 1-8
    return None


def build_chapter_css():
    """Return the full inline CSS for chapter pages."""
    return f"""    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #b8b0a2;
      --text-muted: #8a8278;
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
        radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_PRIMARY_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_PRIMARY_RGB},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15),
        0 0 80px rgba({ACCENT_PRIMARY_RGB},0.2);
      max-width: 860px;
      width: 100%;
      margin: 0 auto;
    }}
    .glass-page-inner {{
      background: var(--bg-inner);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card);
      padding: 3rem 2.5rem;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }}
    .glass-page-inner::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 150px;
      background: radial-gradient(ellipse at top, rgba({ACCENT_PRIMARY_RGB},0.04), transparent 70%);
      pointer-events: none;
    }}
    .glass-tab {{
      position: absolute;
      bottom: -12px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      border-radius: 999px;
      background: radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_PRIMARY_RGB},0.4);
    }}
    .nav-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
      padding: 14px 18px;
      background: rgba({ACCENT_PRIMARY_RGB},0.04);
      border-radius: 12px;
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.12);
      position: relative;
      z-index: 1;
    }}
    .nav-controls a, .nav-controls select {{
      color: var(--text-primary);
      text-decoration: none;
      padding: 8px 14px;
      border-radius: 8px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.25);
      font-size: 0.85rem;
      transition: all 0.3s;
    }}
    .nav-controls a:hover, .nav-controls select:hover {{
      border-color: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }}
    .nav-controls select {{
      cursor: pointer;
      min-width: 180px;
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23C4A060' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      padding-right: 30px;
    }}
    .nav-controls select option {{ background: var(--bg-dark); color: var(--text-primary); }}
    .home-link {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--accent-secondary);
      font-size: 0.85rem;
    }}
    .home-link svg {{ width: 14px; height: 14px; fill: currentColor; }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba({ACCENT_PRIMARY_RGB},0.2);
      position: relative;
      z-index: 1;
    }}
    h1 {{
      font-size: 2.2rem;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      margin-bottom: 6px;
      font-weight: 600;
    }}
    .chapter-num {{
      font-size: 1.05rem;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }}
    .content {{ position: relative; z-index: 1; }}
    .content p {{
      margin-bottom: 16px;
      color: var(--text-secondary);
      text-align: justify;
    }}
    .content h2 {{
      font-size: 1.4rem;
      color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
      margin-top: 32px;
      margin-bottom: 14px;
    }}
    .content h3 {{
      font-size: 1.15rem;
      color: var(--accent);
      margin-top: 24px;
      margin-bottom: 10px;
    }}
    blockquote.scripture {{
      margin: 20px 0;
      padding: 16px 20px;
      background: rgba({ACCENT_SECONDARY_RGB},0.04);
      border-left: 3px solid var(--scripture-border);
      border-radius: 0 10px 10px 0;
      font-style: italic;
    }}
    blockquote.scripture p {{ margin-bottom: 0; color: var(--text-primary); }}
    blockquote.scripture cite {{
      display: block;
      margin-top: 6px;
      color: var(--accent);
      font-style: normal;
      font-weight: 500;
      font-size: 0.9rem;
    }}
    .divider {{
      text-align: center;
      margin: 28px 0;
      color: var(--text-muted);
      opacity: 0.4;
    }}
    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba({ACCENT_PRIMARY_RGB},0.15);
      text-align: center;
      position: relative;
      z-index: 1;
    }}
    .footer-nav {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
    }}
    .footer-nav a {{
      color: var(--accent-secondary);
      text-decoration: none;
      padding: 10px 20px;
      border-radius: 8px;
      background: rgba({ACCENT_SECONDARY_RGB},0.08);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB},0.25);
      transition: all 0.3s;
      font-size: 0.9rem;
    }}
    .footer-nav a:hover {{
      background: rgba({ACCENT_SECONDARY_RGB},0.15);
      box-shadow: 0 0 10px var(--accent-secondary-glow);
    }}
    .footer-nav a.disabled {{
      opacity: 0.35;
      pointer-events: none;
    }}
    .copyright {{
      color: var(--text-muted);
      font-size: 0.78rem;
      margin-top: 12px;
    }}
    .copyright a {{ color: var(--accent-secondary); text-decoration: none; }}
    @media print {{
      body {{ background: white; color: #333; padding: 0; font-size: 11pt; line-height: 1.5; }}
      body::before {{ display: none; }}
      .glass-page-wrapper {{ box-shadow: none; background: none; padding: 0; max-width: 100%; }}
      .glass-page-inner {{ background: white; padding: 0.5in; border-radius: 0; border: none; }}
      .glass-page-inner::before {{ display: none; }}
      .glass-tab, .nav-controls, .footer-nav {{ display: none; }}
      header {{ border-bottom: 2px solid #333; }}
      h1 {{ color: #8B6914; text-shadow: none; font-size: 18pt; }}
      .content p {{ color: #333; }}
      blockquote.scripture {{ background: #f9f9f9; border-left-color: #5a6b4a; }}
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
      .nav-controls a, .nav-controls select {{ padding: 10px 14px; font-size: 0.9rem; min-height: 44px; }}
      .nav-controls select {{ width: 100%; }}
      header {{ margin-bottom: 20px; padding-bottom: 16px; }}
      h1 {{ font-size: 1.4rem; }}
      .chapter-num {{ font-size: 0.95rem; }}
      .content p {{ text-align: left; margin-bottom: 14px; }}
      blockquote.scripture {{ padding: 12px 14px; margin: 16px 0; }}
      footer {{ margin-top: 28px; }}
      .footer-nav {{ flex-direction: column; gap: 10px; }}
      .footer-nav a {{ text-align: center; padding: 12px 20px; min-height: 44px; display: flex; align-items: center; justify-content: center; }}
    }}"""


def build_page_html(page_index):
    """Generate a complete chapter/page HTML file."""
    md_file, label, title, out_file = PAGES[page_index]
    md_text = (BOOK_DIR / md_file).read_text(encoding='utf-8')
    content_html = convert_md_to_html(md_text)
    chapter_select = build_chapter_select(out_file)

    # Header section
    if label:
        header_label = f'<p class="chapter-num">{label.upper()}</p>'
    else:
        header_label = ''

    # Navigation links
    if page_index > 0:
        prev_file = PAGES[page_index - 1][3]
        prev_title = PAGES[page_index - 1][2]
        prev_link = f'<a href="{prev_file}">&larr; {prev_title}</a>'
    else:
        prev_link = '<a href="index.html">&larr; Table of Contents</a>'

    if page_index < len(PAGES) - 1:
        next_file = PAGES[page_index + 1][3]
        next_title = PAGES[page_index + 1][2]
        next_link = f'<a href="{next_file}">{next_title} &rarr;</a>'
    else:
        next_link = '<a class="disabled">Last Page</a>'

    # Progress tracking script for numbered chapters
    ch_num = get_chapter_number(page_index)
    if ch_num is not None:
        progress_script = f"""
  <script>
    (function() {{
      var PROGRESS_KEY = '{PROGRESS_KEY}';
      var CH = {ch_num};
      try {{
        var p = JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}};
        if (!p['ch' + CH]) {{
          p['ch' + CH] = 'visited';
          localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
        }}
      }} catch(e) {{}}
    }})();
  </script>"""
    else:
        progress_script = ""

    # Page title for <title> tag
    if label:
        page_title = f"{label}: {title}"
    else:
        page_title = title

    css = build_chapter_css()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title} | Before I Formed You</title>
  <style>
{css}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">&larr; Table of Contents</a>
        <select onchange="if(this.value)location=this.value">
          {chapter_select}
        </select>
      </nav>

      <header>
        {header_label}
        <h1>{title}</h1>
      </header>

      <div class="content">
        {content_html}
      </div>

      <div class="nav-controls" style="margin-top:28px;">
        {prev_link}
        {next_link}
      </div>

      <footer>
        <p class="copyright">Before I Formed You &copy; Paul &amp; Pam Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>{progress_script}
  <script src="/nm-core.js" defer></script>
</body>
</html>"""


def build_index_html():
    """Generate the book landing/TOC page."""
    # Build chapter cards
    cards_html = ""
    for i, (_, label, title, out_file) in enumerate(PAGES):
        ch_num = get_chapter_number(i)
        if ch_num is not None:
            cards_html += f"""
          <a href="{out_file}" class="lesson-card" data-ch="{ch_num}">
            <span class="lesson-num">{label}</span>
            <div class="lesson-title">{title}</div>
            <span class="progress-dot" id="dot-{ch_num}"></span>
          </a>"""
        else:
            cards_html += f"""
          <a href="{out_file}" class="lesson-card">
            <span class="lesson-num">{label if label else title}</span>
            <div class="lesson-title">{title if label else ''}</div>
          </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents | Before I Formed You</title>
  <style>
    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #b8b0a2;
      --text-muted: #8a8278;
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
        radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_PRIMARY_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_PRIMARY_RGB},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15),
        0 0 80px rgba({ACCENT_PRIMARY_RGB},0.2);
      max-width: 860px;
      width: 100%;
      margin: 0 auto;
    }}
    .glass-page-inner {{
      background: var(--bg-inner);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-radius: var(--radius-card);
      padding: 3rem 2.5rem;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(148,163,184,0.15);
    }}
    .glass-page-inner::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 150px;
      background: radial-gradient(ellipse at top, rgba({ACCENT_PRIMARY_RGB},0.04), transparent 70%);
      pointer-events: none;
    }}
    .glass-tab {{
      position: absolute;
      bottom: -12px;
      left: 50%;
      transform: translateX(-50%);
      width: 100px;
      height: 14px;
      border-radius: 999px;
      background: radial-gradient(circle at top, rgba({ACCENT_PRIMARY_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_PRIMARY_RGB},0.4);
    }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba({ACCENT_PRIMARY_RGB},0.2);
      position: relative;
      z-index: 1;
    }}
    h1 {{
      font-size: 2.2rem;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      margin-bottom: 6px;
      font-weight: 600;
    }}
    .subtitle {{
      font-size: 1.1rem;
      color: var(--text-secondary);
      font-style: italic;
      margin-bottom: 8px;
    }}
    .author {{
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-bottom: 4px;
    }}
    .stats {{
      margin-top: 12px;
      color: var(--text-secondary);
      font-size: 0.9rem;
    }}
    .stats span {{
      color: var(--accent);
      font-weight: 600;
    }}
    .return-link {{
      display: inline-block;
      margin-top: 18px;
      padding: 10px 20px;
      background: rgba({ACCENT_SECONDARY_RGB},0.08);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB},0.25);
      border-radius: 8px;
      color: var(--accent-secondary);
      text-decoration: none;
      font-size: 0.9rem;
      transition: all 0.3s ease;
    }}
    .return-link:hover {{
      background: rgba({ACCENT_SECONDARY_RGB},0.15);
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
    }}
    .key-verse {{
      margin: 24px 0;
      padding: 22px;
      background: rgba({ACCENT_PRIMARY_RGB},0.04);
      border-radius: 14px;
      text-align: center;
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.15);
      position: relative;
      z-index: 1;
    }}
    .key-verse blockquote {{
      font-style: italic;
      font-size: 1.05rem;
      color: var(--text-primary);
      line-height: 1.8;
      margin-bottom: 10px;
    }}
    .key-verse cite {{
      color: var(--accent);
      font-style: normal;
      font-weight: 500;
    }}
    .progress-bar {{
      margin: 20px 0;
      padding: 14px 18px;
      background: rgba({ACCENT_PRIMARY_RGB},0.04);
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.12);
      border-radius: 12px;
      position: relative;
      z-index: 1;
    }}
    .progress-bar .label {{
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }}
    .progress-bar .label span {{ color: var(--accent); font-weight: 600; }}
    .progress-track {{
      height: 8px;
      background: rgba(0,0,0,0.3);
      border-radius: 4px;
      overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
      border-radius: 4px;
      transition: width 0.5s ease;
    }}
    .chapter-section {{
      margin-bottom: 32px;
      position: relative;
      z-index: 1;
    }}
    .section-header h2 {{
      font-size: 1.3rem;
      color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
      margin-bottom: 14px;
    }}
    .lesson-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
    }}
    .lesson-card {{
      display: block;
      position: relative;
      padding: 14px 18px;
      background: rgba(0,0,0,0.2);
      border-radius: 10px;
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.12);
      text-decoration: none;
      transition: all 0.3s;
    }}
    .lesson-card:hover {{
      border-color: var(--accent);
      box-shadow: 0 0 15px var(--accent-glow);
      transform: translateY(-2px);
    }}
    .lesson-num {{
      color: var(--accent);
      font-weight: 700;
      font-size: 0.85rem;
    }}
    .lesson-title {{
      color: var(--text-primary);
      font-size: 0.95rem;
      margin: 4px 0;
    }}
    .progress-dot {{
      position: absolute;
      top: 12px;
      right: 14px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 2px solid rgba({ACCENT_PRIMARY_RGB},0.3);
      transition: all 0.3s;
    }}
    .progress-dot.visited {{
      border-color: var(--accent);
      background: rgba({ACCENT_PRIMARY_RGB},0.3);
    }}
    .progress-dot.complete {{
      border-color: var(--accent);
      background: var(--accent);
    }}
    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba({ACCENT_PRIMARY_RGB},0.15);
      text-align: center;
      position: relative;
      z-index: 1;
    }}
    .copyright {{
      color: var(--text-muted);
      font-size: 0.78rem;
      margin-top: 12px;
    }}
    .copyright a {{ color: var(--accent-secondary); text-decoration: none; }}
    @media (max-width: 600px) {{
      html {{ -webkit-text-size-adjust: 100%; }}
      body {{ padding: 10px 6px; font-size: 1rem; line-height: 1.75; }}
      .glass-page-wrapper {{ border-radius: 16px; padding: 2px; }}
      .glass-page-inner {{ padding: 1.2rem 1rem; border-radius: 14px; }}
      .glass-page-inner::before {{ height: 80px; }}
      .glass-tab {{ width: 60px; height: 10px; bottom: -8px; }}
      header {{ margin-bottom: 20px; padding-bottom: 16px; }}
      h1 {{ font-size: 1.4rem; }}
      .return-link {{ padding: 10px 16px; min-height: 44px; display: inline-flex; align-items: center; }}
      .progress-bar {{ padding: 12px 14px; }}
      .key-verse {{ padding: 16px 14px; }}
      .key-verse blockquote {{ font-size: 0.95rem; }}
      .section-header h2 {{ font-size: 1.15rem; }}
      .lesson-grid {{ grid-template-columns: 1fr; gap: 10px; }}
      .lesson-card {{ padding: 14px 16px; min-height: 44px; }}
    }}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <header>
        <h1>Before I Formed You</h1>
        <p class="subtitle">What God Says to the Woman Holding This Book</p>
        <p class="author">Paul &amp; Pam Hainline</p>
        <p class="stats">
          <span>{TOTAL_CHAPTERS}</span> Chapters
        </p>
        <a href="../books.html" class="return-link">&larr; Return to Books</a>
      </header>

      <section class="key-verse">
        <blockquote>
          &ldquo;Before I formed you in the womb I knew you, before you were born I consecrated you.&rdquo;
        </blockquote>
        <cite>&mdash; Jeremiah 1:5 (NASB)</cite>
      </section>

      <div class="progress-bar">
        <div class="label">
          <span>Reading Progress</span>
          <span id="progress-text">0 / {TOTAL_CHAPTERS} chapters</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
      </div>

      <section class="chapter-section">
        <div class="lesson-grid">{cards_html}
        </div>
      </section>

      <footer>
        <p class="copyright">Before I Formed You &copy; Paul &amp; Pam Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var TOTAL = {TOTAL_CHAPTERS};
    var PROGRESS_KEY = '{PROGRESS_KEY}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}

    function updateProgress() {{
      var p = loadProgress();
      var done = 0;
      for (var i = 1; i <= TOTAL; i++) {{
        var dot = document.getElementById('dot-' + i);
        if (!dot) continue;
        var status = p['ch' + i];
        if (status === 'complete') {{
          dot.className = 'progress-dot complete';
          done++;
        }} else if (status === 'visited') {{
          dot.className = 'progress-dot visited';
        }}
      }}
      document.getElementById('progress-fill').style.width = (done / TOTAL * 100) + '%';
      document.getElementById('progress-text').textContent = done + ' / ' + TOTAL + ' chapters';
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      updateProgress();
    }});
  </script>
  <script src="/nm-core.js" defer></script>
</body>
</html>"""


def main():
    print('Generating HTML files for "Before I Formed You"...')
    print(f"  Theme: Warm Gold ({ACCENT_PRIMARY}) + Sage Green ({ACCENT_SECONDARY})")
    print()

    # Generate index page
    print("Generating index.html (table of contents)...")
    index_html = build_index_html()
    (BOOK_DIR / "index.html").write_text(index_html, encoding='utf-8')

    # Generate chapter/page files
    for i, (md_file, label, title, out_file) in enumerate(PAGES):
        display = f"{label}: {title}" if label else title
        print(f"  {out_file}: {display}")
        page_html = build_page_html(i)
        (BOOK_DIR / out_file).write_text(page_html, encoding='utf-8')

    print(f"\nGenerated {len(PAGES)} page files + index.html")
    print("Done.")


if __name__ == "__main__":
    main()
