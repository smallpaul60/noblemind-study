#!/usr/bin/env python3
"""Generate HTML chapter files and index page for Can These Bones Live?

Theme: Warm gold (#C69B56) + Warm stone/slate (#9B9486)
Matches the physical book cover palette (warm earth / bone / gold).
"""

import re
from pathlib import Path
import markdown

BOOK_DIR = Path(__file__).parent

CHAPTERS = [
    ("chapter1-can-these-bones-live.md",   1,  "The Valley"),
    ("chapter2-can-these-bones-live.md",   2,  "Dust and Breath"),
    ("chapter3-can-these-bones-live.md",   3,  "When the Word Goes Silent"),
    ("chapter4-can-these-bones-live.md",   4,  "Destroyed for Lack of Knowledge"),
    ("chapter5-can-these-bones-live.md",   5,  "The Book Lost in the Temple"),
    ("chapter6-can-these-bones-live.md",   6,  "Prophesy to These Bones"),
    ("chapter7-can-these-bones-live.md",   7,  "Breathe on These Slain"),
    ("chapter8-can-these-bones-live.md",   8,  "A Rushing Mighty Wind"),
    ("chapter9-can-these-bones-live.md",   9,  "The Israel of God"),
    ("chapter10-can-these-bones-live.md", 10,  "Letters to the Dead"),
    ("chapter11-can-these-bones-live.md", 11,  "Can These Bones Live?"),
]

APPENDICES = [
    ("Appendix_A_Authors-Note.md",           "A", "Appendix A", "A Note from the Author"),
    ("Appendix_B_The_Pattern_at_a_Glance.md", "B", "Appendix B", "The Pattern at a Glance"),
]

CHAPTER_WORDS = [
    "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX",
    "SEVEN", "EIGHT", "NINE", "TEN", "ELEVEN",
]

# Warm earth / bone / gold theme (matches cover)
ACCENT_PRIMARY = "#C69B56"        # Warm gold
ACCENT_SECONDARY = "#9B9486"      # Warm stone/slate
ACCENT_PRIMARY_RGB = "198, 155, 86"
ACCENT_SECONDARY_RGB = "155, 148, 134"

TOTAL = len(CHAPTERS)
PROGRESS_KEY = "canTheseBonesLive_progress"

BOOK_TITLE = "Can These Bones Live?"
BOOK_SUBTITLE = "How the Word and the Spirit Make Dead Things Live"
BOOK_AUTHOR = "Paul Hainline"

# Index page intro blurb (from generate_lulu_paperback_cover.py body_paragraphs)
INTRO_PARAGRAPHS = [
    "God showed Ezekiel a valley of dry bones and asked the one question only God can answer: can these live?",
    "The answer, then and now, is the same \u2014 and it comes by the same means. The word of God gives form. The Spirit of God gives life. Together, and only together, they make dead things stand.",
    "This book traces that single pattern through the whole Bible, from the dust of Eden to the rushing wind of Pentecost, from the valley of bones to the seven letters Christ dictated to His own church. At every scale \u2014 creation, restoration, new birth, conversion \u2014 the mechanism is the same. Where the word goes silent or the breath is withheld, the bones dry out. Where both are present, the dead rise.",
    "Eleven chapters. One question. One pattern. One God who has been doing this from the beginning.",
]


# ============================================================================
# SCRIPTURE DETECTION (ported from generate_lulu_interior.py)
# ============================================================================

BIBLE_BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
    "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]
_BOOK_ALT = "|".join(
    re.escape(b) for b in sorted(BIBLE_BOOK_ORDER, key=len, reverse=True)
)

# Matches a whole paragraph that is a single quoted Scripture citation,
# e.g.  "Our bones are dried up..." (Ezekiel 37:11).
SCRIPTURE_PARA_RE = re.compile(
    r'^\s*["\u201c\u201d](.+)["\u201c\u201d]\s+'
    r'\(((?:' + _BOOK_ALT + r')\s+\d+(?::\d+(?:\s*[\u2013\u2014-]\s*\d+)?)?)\)'
    r'\.?\s*$'
)

# After markdown conversion, lift the trailing `(Book C:V).` out of the
# blockquote paragraph and render it as a <cite> attribution with class="scripture".
CITE_IN_BLOCKQUOTE_RE = re.compile(
    r'<blockquote>\s*<p>(.*?)\s*\(((?:' + _BOOK_ALT
    + r')\s+\d+(?::\d+(?:\s*[\u2013\u2014-]\s*\d+)?)?)\)\.?\s*</p>\s*</blockquote>',
    re.DOTALL,
)


def promote_scripture_paragraphs(md_text):
    """Rewrite standalone Scripture-quote paragraphs as Markdown blockquotes."""
    paragraphs = re.split(r'\n\s*\n', md_text)
    out = []
    for para in paragraphs:
        stripped = para.strip()
        if stripped and SCRIPTURE_PARA_RE.match(stripped):
            out.append("> " + stripped)
        else:
            out.append(para)
    return "\n\n".join(out)


def lift_citation_to_cite(html):
    """Convert <blockquote><p>"quote" (Ref).</p></blockquote> to styled scripture block."""
    def _sub(m):
        quote = m.group(1).strip()
        cite = m.group(2).strip()
        # Strip surrounding smart/straight quotes if present
        quote = quote.strip()
        quote = re.sub(r'^(&ldquo;|&rdquo;|&lsquo;|&rsquo;|[\u201c\u201d"])+', '', quote)
        quote = re.sub(r'(&ldquo;|&rdquo;|&lsquo;|&rsquo;|[\u201c\u201d"])+$', '', quote)
        return (
            f'<blockquote class="scripture">'
            f'<p>&ldquo;{quote}&rdquo;</p>'
            f'<cite>&mdash; {cite}</cite>'
            f'</blockquote>'
        )
    return CITE_IN_BLOCKQUOTE_RE.sub(_sub, html)


# ============================================================================
# MARKDOWN CONVERSION
# ============================================================================

def convert_md_to_html(md_text):
    """Convert chapter/appendix markdown to HTML content."""
    # Remove first H1 and first H2 (we render the title header ourselves)
    md_text = re.sub(r'^#\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()
    md_text = re.sub(r'^##\s+.*$', '', md_text, count=1, flags=re.MULTILINE).strip()

    md_text = promote_scripture_paragraphs(md_text)
    html = markdown.markdown(md_text, extensions=['smarty', 'tables'])
    html = lift_citation_to_cite(html)
    return html


# ============================================================================
# CHAPTER DROPDOWN
# ============================================================================

def build_chapter_select(current_key):
    """Build the chapter dropdown select.

    current_key may be an int chapter number, or a string like 'A' / 'B' for
    appendices, or None for the index page.
    """
    options = ['<option value="">Jump to...</option>']
    for _, num, title in CHAPTERS:
        sel = ' selected' if current_key == num else ''
        options.append(
            f'<option value="chapter-{num:02d}.html"{sel}>Ch {num}: {title}</option>'
        )
    # Appendix separator (disabled placeholder option)
    options.append('<option value="" disabled>\u2500 Appendices \u2500</option>')
    for _filename, letter, _label, title in APPENDICES:
        sel = ' selected' if current_key == letter else ''
        options.append(
            f'<option value="appendix-{letter}.html"{sel}>Appendix {letter}: {title}</option>'
        )
    return "\n          ".join(options)


# ============================================================================
# SHARED CSS (chapter + appendix pages)
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
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23C69B56' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
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
      letter-spacing: 0.08em;
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
    }}"""


# ============================================================================
# CHAPTER PAGE
# ============================================================================

def build_chapter_html(md_file, ch_num, title):
    """Generate a complete chapter HTML page."""
    md_text = (BOOK_DIR / md_file).read_text(encoding='utf-8')
    content_html = convert_md_to_html(md_text)
    ch_word = CHAPTER_WORDS[ch_num - 1]

    chapter_select = build_chapter_select(ch_num)

    # Navigation links
    if ch_num > 1:
        prev_link = f'<a href="chapter-{ch_num-1:02d}.html">&larr; Previous Chapter</a>'
        prev_kbd = f"chapter-{ch_num-1:02d}.html"
    else:
        prev_link = '<a href="index.html">&larr; Contents</a>'
        prev_kbd = "index.html"

    if ch_num < TOTAL:
        next_link = f'<a href="chapter-{ch_num+1:02d}.html">Next Chapter &rarr;</a>'
        next_kbd = f"chapter-{ch_num+1:02d}.html"
    else:
        # Final chapter -> Appendix A
        next_link = '<a href="appendix-A.html">Appendix A &rarr;</a>'
        next_kbd = "appendix-A.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chapter {ch_num}: {title} | {BOOK_TITLE}</title>
  <style>{page_css()}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          {BOOK_TITLE}
        </a>
        <select id="chapter-select" onchange="goToChapter(this.value)">
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
        <p class="copyright">{BOOK_TITLE} &copy; {BOOK_AUTHOR} 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var PROGRESS_KEY = '{PROGRESS_KEY}';
    var CH = 'ch{ch_num}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}
    function saveProgress(p) {{ localStorage.setItem(PROGRESS_KEY, JSON.stringify(p)); }}

    function toggleComplete() {{
      var p = loadProgress();
      if (p[CH] === 'complete') {{
        p[CH] = 'visited';
      }} else {{
        p[CH] = 'complete';
      }}
      saveProgress(p);
      updateUI();
    }}

    function updateUI() {{
      var p = loadProgress();
      var el = document.getElementById('mark-complete');
      if (p[CH] === 'complete') {{
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
      if (!p[CH]) {{
        p[CH] = 'visited';
        saveProgress(p);
      }}
      updateUI();
    }});

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'ArrowLeft') window.location.href = '{prev_kbd}';
      if (e.key === 'ArrowRight') window.location.href = '{next_kbd}';
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


# ============================================================================
# APPENDIX PAGE
# ============================================================================

def build_appendix_html(md_file, letter, label, title, idx):
    """Generate an appendix HTML page. idx is 0-based index into APPENDICES."""
    md_text = (BOOK_DIR / md_file).read_text(encoding='utf-8')
    content_html = convert_md_to_html(md_text)
    chapter_select = build_chapter_select(letter)

    # Previous link
    if idx == 0:
        # Appendix A -> back to last chapter
        prev_link = f'<a href="chapter-{TOTAL:02d}.html">&larr; Chapter {TOTAL}</a>'
        prev_kbd = f"chapter-{TOTAL:02d}.html"
    else:
        prev_letter = APPENDICES[idx - 1][1]
        prev_link = f'<a href="appendix-{prev_letter}.html">&larr; Appendix {prev_letter}</a>'
        prev_kbd = f"appendix-{prev_letter}.html"

    # Next link
    if idx < len(APPENDICES) - 1:
        next_letter = APPENDICES[idx + 1][1]
        next_link = f'<a href="appendix-{next_letter}.html">Appendix {next_letter} &rarr;</a>'
        next_kbd = f"appendix-{next_letter}.html"
    else:
        next_link = '<a class="disabled">The End</a>'
        next_kbd = ""

    progress_id = f"ap{letter}"

    next_script_line = f"if (e.key === 'ArrowRight') window.location.href = '{next_kbd}';" if next_kbd else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{label}: {title} | {BOOK_TITLE}</title>
  <style>{page_css()}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          {BOOK_TITLE}
        </a>
        <select id="chapter-select" onchange="goToChapter(this.value)">
          {chapter_select}
        </select>
      </nav>

      <header>
        <p class="chapter-num">{label.upper()}</p>
        <h1>{title}</h1>
      </header>

      <div class="content">
        {content_html}
      </div>

      <div class="mark-complete" id="mark-complete" onclick="toggleComplete()">
        <div class="check" id="check-icon">&check;</div>
        <span>Mark Complete</span>
      </div>

      <footer>
        <div class="footer-nav">
          {prev_link}
          {next_link}
        </div>
        <p class="copyright">{BOOK_TITLE} &copy; {BOOK_AUTHOR} 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var PROGRESS_KEY = '{PROGRESS_KEY}';
    var CH = '{progress_id}';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}
    function saveProgress(p) {{ localStorage.setItem(PROGRESS_KEY, JSON.stringify(p)); }}

    function toggleComplete() {{
      var p = loadProgress();
      if (p[CH] === 'complete') {{
        p[CH] = 'visited';
      }} else {{
        p[CH] = 'complete';
      }}
      saveProgress(p);
      updateUI();
    }}

    function updateUI() {{
      var p = loadProgress();
      var el = document.getElementById('mark-complete');
      if (p[CH] === 'complete') {{
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
      if (!p[CH]) {{
        p[CH] = 'visited';
        saveProgress(p);
      }}
      updateUI();
    }});

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'ArrowLeft') window.location.href = '{prev_kbd}';
      {next_script_line}
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


# ============================================================================
# INDEX PAGE
# ============================================================================

def build_index_html():
    """Generate the book landing / table-of-contents page."""
    # Chapter cards
    chapter_cards = ""
    for _md_file, ch_num, title in CHAPTERS:
        chapter_cards += f"""
          <a href="chapter-{ch_num:02d}.html" class="lesson-card" data-ch="{ch_num}">
            <span class="lesson-num">Chapter {ch_num}</span>
            <div class="lesson-title">{title}</div>
            <span class="progress-dot" id="dot-ch{ch_num}"></span>
          </a>"""

    # Appendix cards
    appendix_cards = ""
    for _md_file, letter, label, title in APPENDICES:
        appendix_cards += f"""
          <a href="appendix-{letter}.html" class="lesson-card" data-ap="{letter}">
            <span class="lesson-num">{label}</span>
            <div class="lesson-title">{title}</div>
            <span class="progress-dot" id="dot-ap{letter}"></span>
          </a>"""

    intro_html = "\n".join(f"        <p>{p}</p>" for p in INTRO_PARAGRAPHS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents | {BOOK_TITLE}</title>
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
    .intro-blurb {{
      margin: 24px 0;
      padding: 22px 24px;
      background: rgba({ACCENT_PRIMARY_RGB},0.04);
      border-radius: 14px;
      border: 1px solid rgba({ACCENT_PRIMARY_RGB},0.15);
      position: relative;
      z-index: 1;
    }}
    .intro-blurb p {{
      color: var(--text-secondary);
      margin-bottom: 14px;
      text-align: justify;
      font-size: 1rem;
      line-height: 1.75;
    }}
    .intro-blurb p:last-child {{
      margin-bottom: 0;
      text-align: center;
      color: var(--accent);
      font-style: italic;
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
      .intro-blurb {{ padding: 16px 14px; }}
      .intro-blurb p {{ font-size: 0.95rem; text-align: left; }}
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
        <h1>{BOOK_TITLE}</h1>
        <p class="subtitle">{BOOK_SUBTITLE}</p>
        <p class="author">{BOOK_AUTHOR}</p>
        <p class="stats">
          <span>{TOTAL}</span> Chapters &bull; <span>{len(APPENDICES)}</span> Appendices
        </p>
        <a href="../books.html" class="return-link">&larr; Return to Books</a>
      </header>

      <section class="intro-blurb">
{intro_html}
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
        <div class="section-header">
          <h2>Chapters</h2>
        </div>
        <div class="lesson-grid">{chapter_cards}
        </div>
      </section>

      <section class="chapter-section">
        <div class="section-header">
          <h2>Appendices</h2>
        </div>
        <div class="lesson-grid">{appendix_cards}
        </div>
      </section>

      <footer>
        <p class="copyright">{BOOK_TITLE} &copy; {BOOK_AUTHOR} 2026<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var TOTAL_CHAPTERS = {TOTAL};
    var APPENDIX_LETTERS = {[letter for _, letter, _, _ in APPENDICES]!r};
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
      for (var i = 1; i <= TOTAL_CHAPTERS; i++) {{
        var status = p['ch' + i];
        applyDot('dot-ch' + i, status);
        if (status === 'complete') complete++;
      }}
      for (var j = 0; j < APPENDIX_LETTERS.length; j++) {{
        var letter = APPENDIX_LETTERS[j];
        applyDot('dot-ap' + letter, p['ap' + letter]);
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


# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f'Generating HTML chapter files for "{BOOK_TITLE}"...')
    print(f"  Theme: Warm Gold ({ACCENT_PRIMARY}) + Warm Stone ({ACCENT_SECONDARY})")
    print()

    # Index page
    print("Generating index.html (book landing page)...")
    index_html = build_index_html()
    (BOOK_DIR / "index.html").write_text(index_html, encoding='utf-8')

    # Chapter files
    for md_file, ch_num, title in CHAPTERS:
        out_file = f"chapter-{ch_num:02d}.html"
        print(f"  {out_file}: {title}")
        chapter_html = build_chapter_html(md_file, ch_num, title)
        (BOOK_DIR / out_file).write_text(chapter_html, encoding='utf-8')

    # Appendix files
    for idx, (md_file, letter, label, title) in enumerate(APPENDICES):
        out_file = f"appendix-{letter}.html"
        print(f"  {out_file}: {label} \u2014 {title}")
        appendix_html = build_appendix_html(md_file, letter, label, title, idx)
        (BOOK_DIR / out_file).write_text(appendix_html, encoding='utf-8')

    print(f"\nGenerated {TOTAL} chapters + {len(APPENDICES)} appendices + index.html")
    print("Done.")


if __name__ == "__main__":
    main()
