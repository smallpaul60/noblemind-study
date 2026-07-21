#!/usr/bin/env python3
"""Generate HTML chapter files and index page for From the Beginning.

Theme: Deep blue (#1B3A6B) + Cream/warm white (#F5E6C8)
Target audience: Young readers, seekers, people new to the Bible.
"""

import re
from pathlib import Path
import markdown

BOOK_DIR = Path(__file__).parent

CHAPTERS = [
    ("FromTheBeginning_Ch1.md",  1,  "Not an Accident"),
    ("FromTheBeginning_Ch2.md",  2,  "Made in His Image"),
    ("FromTheBeginning_Ch3.md",  3,  "What Went Wrong"),
    ("FromTheBeginning_Ch4.md",  4,  "The Long Promise"),
    ("FromTheBeginning_Ch5.md",  5,  "The Man Who Changed Everything"),
    ("FromTheBeginning_Ch6.md",  6,  "The Death That Paid the Debt"),
    ("FromTheBeginning_Ch7.md",  7,  "The Empty Tomb"),
    ("FromTheBeginning_Ch8.md",  8,  "So What Do I Do Now?"),
    ("FromTheBeginning_Ch9.md",  9,  "What Happens Next?"),
    ("FromTheBeginning_Ch10.md", 10, "The Life That Follows"),
]

PARTS = {
    1: ("Part One", "The Foundation", "Who is God, and why do you matter?"),
    5: ("Part Two", "The Turning Point", "Who is Jesus, and what did He do?"),
    8: ("Part Three", "The Response", "What does God ask you to do?"),
}

CHAPTER_WORDS = [
    "ONE", "TWO", "THREE", "FOUR", "FIVE",
    "SIX", "SEVEN", "EIGHT", "NINE", "TEN",
]

# Deep blue + warm cream theme
ACCENT_PRIMARY = "#4A7EC2"        # Warm medium blue
ACCENT_SECONDARY = "#D4A848"      # Warm gold/amber
ACCENT_PRIMARY_RGB = "74, 126, 194"
ACCENT_SECONDARY_RGB = "212, 168, 72"

TOTAL = len(CHAPTERS)
PROGRESS_KEY = "fromTheBeginning_progress"


def convert_md_to_html(md_text):
    """Convert chapter markdown to HTML content."""
    # Remove the H1 heading
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()

    html = markdown.markdown(md_text, extensions=['smarty'])

    # Convert scripture blockquotes
    def convert_scripture_bq(match):
        inner = match.group(1).strip()
        inner = re.sub(r'^<p>(.*)</p>$', r'\1', inner, flags=re.DOTALL).strip()

        parts = re.split(r'\s*[—–]\s*(?=<strong>)', inner, maxsplit=1)
        if len(parts) == 2:
            quote_text = parts[0].strip()
            cite_text = parts[1].strip()
            quote_text = re.sub(r'^<em>(.*)</em>$', r'\1', quote_text, flags=re.DOTALL)
            # Strip smart quotes in both unicode and HTML entity form
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

    return html


def build_chapter_select(current_ch):
    """Build the chapter dropdown select."""
    options = ['<option value="">Jump to...</option>']
    options.append(
        f'<option value="dedication.html"{"" if current_ch else " selected"}>To the Seeker</option>'
    )
    for _, num, title in CHAPTERS:
        sel = ' selected' if num == current_ch else ''
        options.append(
            f'<option value="chapter-{num:02d}.html"{sel}>Ch {num}: {title}</option>'
        )
    return "\n          ".join(options)


def build_chapter_html(md_file, ch_num, title):
    """Generate a complete chapter HTML page."""
    md_text = (BOOK_DIR / md_file).read_text(encoding='utf-8')
    content_html = convert_md_to_html(md_text)
    ch_word = CHAPTER_WORDS[ch_num - 1]

    chapter_select = build_chapter_select(ch_num)

    # Navigation links
    if ch_num > 1:
        prev_link = f'<a href="chapter-{ch_num-1:02d}.html">&larr; Previous Chapter</a>'
    else:
        prev_link = '<a href="dedication.html">&larr; To the Seeker</a>'
    next_link = f'<a href="chapter-{ch_num+1:02d}.html">Next Chapter &rarr;</a>' if ch_num < TOTAL else '<a class="disabled">Last Chapter</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chapter {ch_num}: {title} | From the Beginning</title>
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
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%234A7EC2' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
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
    .mark-complete {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin: 30px 0 10px;
      padding: 12px;
      background: rgba({ACCENT_PRIMARY_RGB},0.06);
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.2);
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.3s;
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
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: 2px solid var(--accent);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      color: transparent;
      transition: all 0.3s;
    }}
    .mark-complete.completed .check {{
      background: var(--accent);
      color: #0d0d0d;
    }}
    .mark-complete span:last-child {{
      color: var(--accent);
      font-weight: 600;
      font-size: 0.9rem;
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
      .glass-tab, .nav-controls, .footer-nav, .mark-complete {{ display: none; }}
      header {{ border-bottom: 2px solid #333; }}
      h1 {{ color: #1B3A6B; text-shadow: none; font-size: 18pt; }}
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
      .nav-controls a, .nav-controls select {{ padding: 10px 14px; font-size: 0.9rem; min-height: 44px; }}
      .nav-controls select {{ width: 100%; }}
      header {{ margin-bottom: 20px; padding-bottom: 16px; }}
      h1 {{ font-size: 1.4rem; }}
      .chapter-num {{ font-size: 0.95rem; }}
      .content p {{ text-align: left; margin-bottom: 14px; }}
      blockquote.scripture {{ padding: 12px 14px; margin: 16px 0; }}
      .mark-complete {{ min-height: 44px; padding: 12px; }}
      footer {{ margin-top: 28px; }}
      .footer-nav {{ flex-direction: column; gap: 10px; }}
      .footer-nav a {{ text-align: center; padding: 12px 20px; min-height: 44px; display: flex; align-items: center; justify-content: center; }}
    }}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          From the Beginning
        </a>
        <select id="chapter-select" aria-label="go to chapter" onchange="goToChapter(this.value)">
          {chapter_select}
        </select>
      </nav>

      <header>
        <p class="chapter-num">CHAPTER {ch_word}</p>
        <h1>{title}</h1>
      </header>

      <div class="content">
        {content_html}
      </div>

      <div class="mark-complete" id="mark-complete" onclick="toggleComplete()">
        <div class="check" id="check-icon">&check;</div>
        <span>Mark Chapter Complete</span>
      </div>

      <footer>
        <div class="footer-nav">
          {prev_link}
          {next_link}
        </div>
        <p class="copyright">From the Beginning &copy; Paul &amp; Pam Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var PROGRESS_KEY = '{PROGRESS_KEY}';
    var CH = {ch_num};

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}
    function saveProgress(p) {{ localStorage.setItem(PROGRESS_KEY, JSON.stringify(p)); }}

    function toggleComplete() {{
      var p = loadProgress();
      var key = 'ch' + CH;
      if (p[key] === 'complete') {{
        p[key] = 'visited';
      }} else {{
        p[key] = 'complete';
      }}
      saveProgress(p);
      updateUI();
    }}

    function updateUI() {{
      var p = loadProgress();
      var el = document.getElementById('mark-complete');
      if (p['ch' + CH] === 'complete') {{
        el.classList.add('completed');
      }} else {{
        el.classList.remove('completed');
      }}
    }}

    function goToChapter(url) {{
      if (url) window.location.href = url;
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      var p = loadProgress();
      if (!p['ch' + CH]) {{
        p['ch' + CH] = 'visited';
        saveProgress(p);
      }}
      updateUI();
    }});

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'ArrowLeft') window.location.href = '{f"chapter-{ch_num-1:02d}.html" if ch_num > 1 else "index.html"}';
      if (e.key === 'ArrowRight' && {ch_num} < {TOTAL}) window.location.href = 'chapter-{ch_num+1:02d}.html';
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


def build_index_html():
    """Generate the book landing page."""
    # Build chapter grid sections
    part_sections = []
    current_part_chapters = []
    current_part_header = None

    for md_file, ch_num, title in CHAPTERS:
        if ch_num in PARTS:
            # Flush previous part
            if current_part_header and current_part_chapters:
                part_sections.append((current_part_header, current_part_chapters))
            part_num, part_title, part_subtitle = PARTS[ch_num]
            current_part_header = f"{part_num}: {part_title}"
            current_part_chapters = []

        current_part_chapters.append((ch_num, title))

    if current_part_header and current_part_chapters:
        part_sections.append((current_part_header, current_part_chapters))

    sections_html = ""
    for header, chapters in part_sections:
        cards = ""
        for ch_num, title in chapters:
            cards += f"""
          <a href="chapter-{ch_num:02d}.html" class="lesson-card" data-ch="{ch_num}">
            <span class="lesson-num">Chapter {ch_num}</span>
            <div class="lesson-title">{title}</div>
            <span class="progress-dot" id="dot-{ch_num}"></span>
          </a>"""

        sections_html += f"""
      <section class="chapter-section">
        <div class="section-header">
          <h2>{header}</h2>
        </div>
        <div class="lesson-grid">{cards}
        </div>
      </section>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents | From the Beginning</title>
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
      .hero-cover {{
      text-align: center;
      margin: 28px 0 8px;
      position: relative;
      z-index: 1;
    }}
    .hero-cover img {{
      max-width: 280px;
      width: 100%;
      height: auto;
      border-radius: 6px;
      box-shadow:
        0 8px 32px rgba(0,0,0,0.5),
        0 0 60px var(--accent-soft);
      border: 1px solid var(--accent-soft);
    }}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <header>
        <h1>From the Beginning</h1>
        <p class="subtitle">The Gospel from the Ground Up</p>
        <p class="author">Paul &amp; Pam Hainline</p>
        <p class="stats">
          <span>10</span> Chapters &bull; <span>3</span> Parts
        </p>
        <a href="../books.html" class="return-link">&larr; Return to Books</a>
      </header>

      <div class="hero-cover">
        <img src="cover_front.jpg" alt="From the Beginning — book cover" loading="eager">
      </div>

      <section class="key-verse">
        <blockquote>
          &ldquo;In the beginning God created the heavens and the earth.&rdquo;
        </blockquote>
        <cite>&mdash; Genesis 1:1 (NASB)</cite>
      </section>

      <div class="progress-bar">
        <div class="label">
          <span>Reading Progress</span>
          <span id="progress-text">0 / {TOTAL} chapters</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
      </div>

      <section class="chapter-section">
        <div class="lesson-grid">
          <a href="dedication.html" class="lesson-card">
            <span class="lesson-num">Foreword</span>
            <div class="lesson-title">To the Seeker</div>
          </a>
        </div>
      </section>

      {sections_html}

      <footer>
        <p class="copyright">From the Beginning &copy; Paul &amp; Pam Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var TOTAL_CHAPTERS = {TOTAL};
    var PROGRESS_KEY = '{PROGRESS_KEY}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}

    function updateProgressUI() {{
      var p = loadProgress();
      var complete = 0;
      for (var i = 1; i <= TOTAL_CHAPTERS; i++) {{
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
      document.getElementById('progress-text').textContent = complete + ' / ' + TOTAL_CHAPTERS + ' chapters';
      document.getElementById('progress-fill').style.width = (complete / TOTAL_CHAPTERS * 100) + '%';
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      updateProgressUI();
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


def build_dedication_html():
    """Generate the 'To the Seeker' dedication/foreword page."""
    md_text = (BOOK_DIR / "FromTheBeginning_Dedication.md").read_text(encoding='utf-8')
    # Remove the H1 heading — we'll use our own
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    content_html = markdown.markdown(md_text, extensions=['smarty'])

    # Convert any scripture blockquotes same as chapters
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

    content_html = re.sub(
        r'<blockquote>\s*(.*?)\s*</blockquote>',
        convert_scripture_bq,
        content_html,
        flags=re.DOTALL
    )

    chapter_select = build_chapter_select(0)  # 0 = not a chapter, dedication selected

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>To the Seeker | From the Beginning</title>
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
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%234A7EC2' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
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
    .content {{ position: relative; z-index: 1; }}
    .content p {{
      margin-bottom: 16px;
      color: var(--text-secondary);
      text-align: justify;
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
    .signature {{
      text-align: right;
      margin-top: 24px;
      color: var(--accent-secondary);
      font-style: italic;
      font-size: 1.05rem;
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
      .glass-tab, .nav-controls {{ display: none; }}
      header {{ border-bottom: 2px solid #333; }}
      h1 {{ color: #1B3A6B; text-shadow: none; font-size: 18pt; }}
      .content p {{ color: #333; }}
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
      .content p {{ text-align: left; margin-bottom: 14px; }}
      blockquote.scripture {{ padding: 12px 14px; margin: 16px 0; }}
      footer {{ margin-top: 28px; }}
      .footer-nav {{ flex-direction: column; gap: 10px; }}
      .footer-nav a {{ text-align: center; padding: 12px 20px; min-height: 44px; display: flex; align-items: center; justify-content: center; }}
    }}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          From the Beginning
        </a>
        <select id="chapter-select" aria-label="go to chapter" onchange="goToChapter(this.value)">
          {chapter_select}
        </select>
      </nav>

      <header>
        <h1>To the Seeker</h1>
      </header>

      <div class="content">
        {content_html}
      </div>

      <footer>
        <div class="footer-nav">
          <a href="index.html">&larr; Table of Contents</a>
          <a href="chapter-01.html">Chapter One &rarr;</a>
        </div>
        <p class="copyright">From the Beginning &copy; Paul &amp; Pam Hainline 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    function goToChapter(url) {{ if (url) window.location.href = url; }}
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


def main():
    print('Generating HTML chapter files for "From the Beginning"...')
    print(f"  Theme: Deep Blue ({ACCENT_PRIMARY}) + Warm Gold ({ACCENT_SECONDARY})")
    print()

    # Generate index page
    print("Generating index.html (book landing page)...")
    index_html = build_index_html()
    (BOOK_DIR / "index.html").write_text(index_html, encoding='utf-8')

    # Generate dedication page
    print("Generating dedication.html (To the Seeker)...")
    dedication_html = build_dedication_html()
    (BOOK_DIR / "dedication.html").write_text(dedication_html, encoding='utf-8')

    # Generate chapter files
    for md_file, ch_num, title in CHAPTERS:
        out_file = f"chapter-{ch_num:02d}.html"
        print(f"  {out_file}: {title}")
        chapter_html = build_chapter_html(md_file, ch_num, title)
        (BOOK_DIR / out_file).write_text(chapter_html, encoding='utf-8')

    print(f"\nGenerated {TOTAL} chapter files + dedication.html + index.html")
    print("Done.")


if __name__ == "__main__":
    main()
