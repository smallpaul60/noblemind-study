#!/usr/bin/env python3
"""
Generate HTML online reading version of "Change the Mind, Change the Man"
for noblemind.study.

Generates:
  - index.html (Table of Contents)
  - chapter-01.html through chapter-10.html (Chapter pages)

Usage:
  python3 generate_html_book.py
"""

import os
import re
import html

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = SCRIPT_DIR

BOOK_TITLE = "Change the Mind, Change the Man"
AUTHOR = "Paul Hainline"
PROGRESS_KEY = "changeTheMindChangeTheMan_progress"
COPYRIGHT = "&copy; 2026 Paul Hainline. All rights reserved."
TOTAL_CHAPTERS = 10
PASSWORD = "freddie"

CHAPTERS = [
    {
        "num": 1,
        "title": "The Phone Call",
        "subtitle": "The moment everything splits into before and after.",
        "file": "chapter01_the_phone_call.md",
    },
    {
        "num": 2,
        "title": "The Progression",
        "subtitle": "How the mind turns &mdash; one step at a time.",
        "file": "chapter02_the_progression.md",
    },
    {
        "num": 3,
        "title": "Where Did We Go Wrong?",
        "subtitle": "The question that keeps the family awake &mdash; and the answer no one wants to hear.",
        "file": "chapter03_where_did_we_go_wrong.md",
    },
    {
        "num": 4,
        "title": "All of the Imprisoned Are Not in Prison",
        "subtitle": "Not every prison has walls you can see.",
        "file": "chapter04_imprisoned.md",
    },
    {
        "num": 5,
        "title": "Love That Says No",
        "subtitle": "What if helping is the very thing that is hurting them?",
        "file": "chapter05_love_that_says_no.md",
    },
    {
        "num": 6,
        "title": "THINK!",
        "subtitle": "Think. Think. Think.",
        "file": "chapter06_think.md",
    },
    {
        "num": 7,
        "title": "Coming to Himself",
        "subtitle": "True repentance has feet.",
        "file": "chapter07_coming_to_himself.md",
    },
    {
        "num": 8,
        "title": "The Father Ran",
        "subtitle": "He did not wait for the speech.",
        "file": "chapter08_the_father_ran.md",
    },
    {
        "num": 9,
        "title": "The Long Road",
        "subtitle": "Recovery is not a moment. It is a road made of mornings.",
        "file": "chapter09_the_long_road.md",
    },
    {
        "num": 10,
        "title": "The God Who Finds You",
        "subtitle": "Come to Me, all who are weary and heavy-laden.",
        "file": "chapter10_the_god_who_finds_you.md",
    },
]

NUM_WORDS = [
    "One", "Two", "Three", "Four", "Five",
    "Six", "Seven", "Eight", "Nine", "Ten",
]

PASSWORD_JS = """<script>
(function() {
  if (sessionStorage.getItem('ctm_auth') === 'granted') return;
  var attempts = parseInt(sessionStorage.getItem('ctm_attempts') || '0');
  if (attempts >= 3) {
    window.location.href = '/index.html';
    return;
  }
  var p = prompt('This book is currently in review.\\nPlease enter the access code:');
  if (p && p.toLowerCase().trim() === 'freddie') {
    sessionStorage.setItem('ctm_auth', 'granted');
    sessionStorage.removeItem('ctm_attempts');
  } else {
    sessionStorage.setItem('ctm_attempts', String(attempts + 1));
    window.location.href = '/index.html';
  }
})();
</script>"""


# ---------------------------------------------------------------------------
# Color scheme constants
# ---------------------------------------------------------------------------
ACCENT = "#3B9AE8"
ACCENT_RGB = "59, 154, 232"
ACCENT_SECONDARY = "#E8A848"
ACCENT_SECONDARY_RGB = "232, 168, 72"


def smart_quotes(text):
    """Convert straight quotes and other chars to HTML entities.

    Must be called BEFORE HTML tags are inserted (bold/italic),
    so that tag characters don't interfere with quote detection.
    """
    # Em dashes
    text = text.replace(" — ", " &mdash; ")
    text = text.replace(" -- ", " &mdash; ")
    # En dashes in ranges like 3:13-14
    text = re.sub(r'(\d)-(\d)', r'\1&ndash;\2', text)

    # Process quotes character by character to handle nesting correctly
    result = []
    i = 0
    in_double = False
    in_single = False
    while i < len(text):
        ch = text[i]

        if ch == '"':
            # Look at context to decide opening vs closing
            before = text[i-1] if i > 0 else ' '
            after = text[i+1] if i + 1 < len(text) else ' '

            if before in ' \n\t([{' or i == 0:
                result.append('&ldquo;')
                in_double = True
            elif after in ' \n\t.,;:!?)]}' or i == len(text) - 1:
                result.append('&rdquo;')
                in_double = False
            elif in_double:
                result.append('&rdquo;')
                in_double = False
            else:
                result.append('&ldquo;')
                in_double = True

        elif ch == "'":
            before = text[i-1] if i > 0 else ' '
            after = text[i+1] if i + 1 < len(text) else ' '

            # Apostrophe: letter before AND letter after
            if before.isalpha() and after.isalpha():
                result.append('&rsquo;')
            # Closing: after letter/punctuation, before space/punctuation/end/quote
            elif before.isalnum() or before in '.!?,;:)':
                result.append('&rsquo;')
            # Opening: before letter
            elif after.isalpha() or after == '"':
                result.append('&lsquo;')
            elif in_single:
                result.append('&rsquo;')
                in_single = False
            else:
                result.append('&lsquo;')
                in_single = True
        else:
            result.append(ch)

        i += 1

    return ''.join(result)


def process_inline(text):
    """Process inline markdown: bold, italic, and smart quotes.

    Smart quotes are applied FIRST (before HTML tags are inserted)
    to avoid tag characters interfering with quote direction detection.
    """
    # Smart quotes first (before HTML tags)
    text = smart_quotes(text)
    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic: *text*
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


def parse_markdown_chapters_1_4(lines):
    """Parse chapters 1-4 which use > blockquote syntax for scripture."""
    content_blocks = []
    i = 0

    # Skip header lines (# **Chapter N**, # **Title**, ## *subtitle*)
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('# ') or line.startswith('## '):
            i += 1
            continue
        if line == '':
            i += 1
            continue
        break

    while i < len(lines):
        line = lines[i].strip()

        # Empty line
        if line == '':
            i += 1
            continue

        # Divider
        if re.match(r'^[•·]\s+[•·]\s+[•·]$', line) or line in ('• • •', '•  •  •', '•   •   •'):
            content_blocks.append(('divider', None))
            i += 1
            continue

        # Blockquote (scripture) - starts with >
        if line.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                bq_line = lines[i].strip()[1:].strip()  # Remove '>'
                if bq_line:
                    bq_lines.append(bq_line)
                i += 1

            # Parse blockquote content: find citation line
            quote_text = []
            citation = None
            for bl in bq_lines:
                if bl.startswith('— ') or bl.startswith('- ') or bl.startswith('&mdash;'):
                    citation = bl.lstrip('— ').lstrip('- ').lstrip('&mdash; ')
                else:
                    quote_text.append(bl)

            raw_quote = ' '.join(quote_text)
            # Strip wrapping italic markers from scripture quotes
            raw_quote = re.sub(r'^\*(.+)\*$', r'\1', raw_quote.strip())
            raw_quote = raw_quote.strip()
            quote_html = process_inline(raw_quote)
            if citation:
                citation = process_inline(citation)

            content_blocks.append(('scripture', (quote_html, citation)))
            continue

        # Regular paragraph
        para = line
        i += 1
        # Collect continuation lines (non-empty, non-special)
        while i < len(lines):
            next_line = lines[i].strip()
            if next_line == '' or next_line.startswith('>') or next_line.startswith('#') or \
               re.match(r'^[•·]\s+[•·]\s+[•·]$', next_line) or next_line in ('• • •', '•  •  •', '•   •   •'):
                break
            para += ' ' + next_line
            i += 1

        content_blocks.append(('paragraph', process_inline(para)))

    return content_blocks


def parse_markdown_chapters_5_10(lines):
    """Parse chapters 5-10 which use *"quoted text"* / — Reference pattern for scripture."""
    content_blocks = []
    i = 0

    # Skip header lines
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('# ') or line.startswith('## '):
            i += 1
            continue
        if line == '':
            i += 1
            continue
        break

    while i < len(lines):
        line = lines[i].strip()

        # Empty line
        if line == '':
            i += 1
            continue

        # Divider
        if re.match(r'^[•·]\s+[•·]\s+[•·]$', line) or line in ('• • •', '•  •  •', '•   •   •'):
            content_blocks.append(('divider', None))
            i += 1
            continue

        # Scripture blockquote detection:
        # Pattern 1: *"quoted text"* followed by — Reference on next line
        # Pattern 2: A line that is a quoted passage (starts with *") followed by citation
        if line.startswith('*"') or line.startswith('*\u201c'):
            # Collect all lines of the quote
            quote_lines = [line]
            i += 1
            # Continue collecting lines that are part of the same quote or citation
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line == '':
                    i += 1
                    # Check if next non-empty line is a citation
                    while i < len(lines) and lines[i].strip() == '':
                        i += 1
                    if i < len(lines) and (lines[i].strip().startswith('— ') or lines[i].strip().startswith('— ')):
                        quote_lines.append(lines[i].strip())
                        i += 1
                    break
                elif next_line.startswith('— ') or next_line.startswith('— '):
                    quote_lines.append(next_line)
                    i += 1
                    break
                else:
                    quote_lines.append(next_line)
                    i += 1

            # Parse: separate quote text from citation
            citation = None
            text_parts = []
            for ql in quote_lines:
                if ql.startswith('— ') or ql.startswith('— '):
                    citation = ql.lstrip('— ').lstrip('— ').strip()
                else:
                    text_parts.append(ql)

            raw_quote = ' '.join(text_parts)
            # Strip wrapping italic markers from scripture quotes
            raw_quote = re.sub(r'^\*(.+)\*$', r'\1', raw_quote.strip())
            raw_quote = raw_quote.strip()
            quote_html = process_inline(raw_quote)
            if citation:
                citation = process_inline(citation)

            content_blocks.append(('scripture', (quote_html, citation)))
            continue

        # Regular paragraph
        para = line
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if next_line == '' or next_line.startswith('#') or \
               re.match(r'^[•·]\s+[•·]\s+[•·]$', next_line) or \
               next_line in ('• • •', '•  •  •', '•   •   •') or \
               next_line.startswith('*"') or next_line.startswith('*\u201c'):
                break
            # Check if this line is a citation for a preceding inline quote
            if next_line.startswith('— ') or next_line.startswith('— '):
                break
            para += ' ' + next_line
            i += 1

        content_blocks.append(('paragraph', process_inline(para)))

    return content_blocks


def render_content_blocks(blocks):
    """Render parsed content blocks to HTML."""
    html_parts = []
    for block_type, data in blocks:
        if block_type == 'divider':
            html_parts.append('        <div class="divider">&bull; &nbsp; &bull; &nbsp; &bull;</div>')
        elif block_type == 'scripture':
            quote_html, citation = data
            html_parts.append('        <blockquote class="scripture">')
            html_parts.append(f'          <p>{quote_html}</p>')
            if citation:
                html_parts.append(f'          <cite>&mdash; {citation}</cite>')
            html_parts.append('        </blockquote>')
        elif block_type == 'paragraph':
            html_parts.append(f'        <p>{data}</p>')
    return '\n\n'.join(html_parts)


def get_chapter_css():
    """Return the full inline CSS for chapter pages."""
    return f"""    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #b0c0d0;
      --text-muted: #708898;
      --accent: {ACCENT};
      --accent-glow: rgba({ACCENT_RGB}, 0.4);
      --accent-soft: rgba({ACCENT_RGB}, 0.12);
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
        radial-gradient(circle at top, rgba({ACCENT_RGB},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_RGB},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15),
        0 0 80px rgba({ACCENT_RGB},0.2);
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
      background: radial-gradient(ellipse at top, rgba({ACCENT_RGB},0.04), transparent 70%);
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
      background: radial-gradient(circle at top, rgba({ACCENT_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_RGB},0.4);
    }}
    .nav-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
      padding: 14px 18px;
      background: rgba({ACCENT_RGB},0.04);
      border-radius: 12px;
      border: 1px solid rgba({ACCENT_RGB},0.12);
      position: relative;
      z-index: 1;
    }}
    .nav-controls a, .nav-controls select {{
      color: var(--text-primary);
      text-decoration: none;
      padding: 8px 14px;
      border-radius: 8px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba({ACCENT_RGB},0.25);
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
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%233B9AE8' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      padding-right: 30px;
    }}
    .nav-controls select option {{
      background: var(--bg-dark);
      color: var(--text-primary);
    }}
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
      border-bottom: 1px solid rgba({ACCENT_RGB},0.2);
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
    .subtitle {{
      font-size: 1.1rem;
      color: var(--text-secondary);
      font-style: italic;
      margin-bottom: 8px;
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
    .divider {{
      text-align: center;
      margin: 28px 0;
      color: var(--text-muted);
      opacity: 0.4;
    }}
    .mark-complete {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin: 30px 0 10px;
      padding: 12px;
      background: rgba({ACCENT_RGB},0.06);
      border: 1px solid rgba({ACCENT_RGB},0.2);
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.3s;
      user-select: none;
    }}
    .mark-complete:hover {{
      border-color: var(--accent);
      background: rgba({ACCENT_RGB},0.1);
    }}
    .mark-complete.completed {{
      background: rgba({ACCENT_RGB},0.12);
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
      border-top: 1px solid rgba({ACCENT_RGB},0.15);
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
      h1 {{ color: #2874A6; text-shadow: none; font-size: 18pt; }}
      .content p {{ color: #333; }}
      blockquote.scripture {{ background: #f9f9f9; border-left-color: #D4A848; }}
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


def build_chapter_select(current_num):
    """Build the chapter dropdown selector."""
    options = ['          <option value="">Jump to...</option>']
    for ch in CHAPTERS:
        selected = ' selected' if ch['num'] == current_num else ''
        # Use plain title for option (decode entities for display)
        title = ch['title']
        options.append(f'          <option value="chapter-{ch["num"]:02d}.html"{selected}>Ch {ch["num"]}: {title}</option>')
    return '\n'.join(options)


def generate_chapter_html(chapter_info, content_html):
    """Generate the full HTML for a chapter page."""
    num = chapter_info['num']
    title = chapter_info['title']
    subtitle = chapter_info['subtitle']
    num_word = NUM_WORDS[num - 1].upper()

    # Prev/next navigation
    if num == 1:
        prev_link = '<a href="index.html">&larr; Table of Contents</a>'
    else:
        prev_ch = CHAPTERS[num - 2]
        prev_link = f'<a href="chapter-{num-1:02d}.html">&larr; Ch {num-1}: {prev_ch["title"]}</a>'

    if num == TOTAL_CHAPTERS:
        next_link = '<a href="index.html">Table of Contents &rarr;</a>'
    else:
        next_ch = CHAPTERS[num]
        next_link = f'<a href="chapter-{num+1:02d}.html">Ch {num+1}: {next_ch["title"]} &rarr;</a>'

    # Arrow key navigation
    if num == 1:
        left_target = 'index.html'
    else:
        left_target = f'chapter-{num-1:02d}.html'

    if num == TOTAL_CHAPTERS:
        right_target = 'index.html'
        right_disabled = False
    else:
        right_target = None  # use footer nav click

    subtitle_html = ''
    if subtitle:
        subtitle_html = f'\n        <p class="subtitle">{subtitle}</p>'

    chapter_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chapter {num}: {title} | {BOOK_TITLE}</title>
  <style>
{get_chapter_css()}
  </style>
</head>
<body>
  {PASSWORD_JS}
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          {BOOK_TITLE}
        </a>
        <select id="chapter-select" onchange="goToChapter(this.value)">
{build_chapter_select(num)}
        </select>
      </nav>

      <header>
        <p class="chapter-num">CHAPTER {num_word}</p>
        <h1>{title}</h1>{subtitle_html}
      </header>

      <div class="content">
{content_html}
      </div>

      <div id="mark-complete" class="mark-complete" onclick="toggleComplete()">
        <span class="check"></span>
        <span>Mark Chapter Complete</span>
      </div>

      <footer>
        <div class="footer-nav">
          {prev_link}
          {next_link}
        </div>
        <p class="copyright">{BOOK_TITLE} {COPYRIGHT}<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var PROGRESS_KEY = '{PROGRESS_KEY}';
    var CH_NUM = {num};

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}

    function markVisited() {{
      var p = loadProgress();
      if (!p['ch' + CH_NUM]) p['ch' + CH_NUM] = 'visited';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
    }}

    function toggleComplete() {{
      var p = loadProgress();
      var key = 'ch' + CH_NUM;
      p[key] = p[key] === 'complete' ? 'visited' : 'complete';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
      updateCompleteBtn();
    }}

    function updateCompleteBtn() {{
      var p = loadProgress();
      var btn = document.getElementById('mark-complete');
      if (!btn) return;
      var done = p['ch' + CH_NUM] === 'complete';
      btn.className = 'mark-complete' + (done ? ' completed' : '');
      btn.querySelector('.check').textContent = done ? '\\u2713' : '';
      btn.querySelector('span:last-child').textContent = done ? 'Chapter Complete' : 'Mark Chapter Complete';
    }}

    function goToChapter(val) {{
      if (val) window.location.href = val;
    }}

    document.addEventListener('keydown', function(e) {{
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
      if (e.key === 'ArrowLeft') {{
        window.location.href = '{left_target}';
      }} else if (e.key === 'ArrowRight') {{
        var next = document.querySelector('.footer-nav a:last-child');
        if (next && !next.classList.contains('disabled')) next.click();
      }}
    }});

    document.addEventListener('DOMContentLoaded', function() {{
      markVisited();
      updateCompleteBtn();
    }});
  </script>
  <script src="/nm-beacon.js" defer></script>
</body>
</html>"""

    return chapter_html


def generate_index_html():
    """Generate the Table of Contents index.html."""
    chapter_cards = []
    for ch in CHAPTERS:
        subtitle_html = ''
        if ch['subtitle']:
            subtitle_html = f'\n            <span class="lesson-subtitle">{ch["subtitle"]}</span>'
        chapter_cards.append(f"""          <a href="chapter-{ch['num']:02d}.html" class="lesson-card" data-ch="{ch['num']}">
            <span class="lesson-num">Chapter {ch['num']}</span>
            <div class="lesson-title">{ch['title']}</div>{subtitle_html}
            <span class="progress-dot" id="dot-{ch['num']}"></span>
          </a>""")

    cards_html = '\n'.join(chapter_cards)

    index_html = f"""<!DOCTYPE html>
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
      --text-secondary: #b0c0d0;
      --text-muted: #708898;
      --accent: {ACCENT};
      --accent-glow: rgba({ACCENT_RGB}, 0.4);
      --accent-soft: rgba({ACCENT_RGB}, 0.12);
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
        radial-gradient(circle at top, rgba({ACCENT_RGB},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_SECONDARY_RGB},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({ACCENT_RGB},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({ACCENT_SECONDARY_RGB},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({ACCENT_RGB},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({ACCENT_SECONDARY_RGB},0.15),
        0 0 80px rgba({ACCENT_RGB},0.2);
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
      background: radial-gradient(ellipse at top, rgba({ACCENT_RGB},0.04), transparent 70%);
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
      background: radial-gradient(circle at top, rgba({ACCENT_RGB},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({ACCENT_RGB},0.4);
    }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba({ACCENT_RGB},0.2);
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
    .download-btn {{
      display: inline-block;
      margin-top: 10px;
      margin-left: 10px;
      padding: 10px 20px;
      background: rgba(100,100,100,0.1);
      border: 1px solid rgba(100,100,100,0.3);
      border-radius: 8px;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.9rem;
      cursor: not-allowed;
      opacity: 0.5;
    }}
    .progress-bar {{
      margin: 20px 0;
      padding: 14px 18px;
      background: rgba({ACCENT_RGB},0.04);
      border: 1px solid rgba({ACCENT_RGB},0.12);
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
    .front-matter {{
      margin-bottom: 28px;
      position: relative;
      z-index: 1;
    }}
    .front-matter .section-header h2 {{
      font-size: 1.3rem;
      color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
      margin-bottom: 14px;
    }}
    .fm-card {{
      display: block;
      padding: 14px 18px;
      margin-bottom: 10px;
      background: rgba(0,0,0,0.2);
      border-radius: 10px;
      border: 1px solid rgba({ACCENT_SECONDARY_RGB}, 0.15);
      text-decoration: none;
      color: var(--text-primary);
      transition: all 0.3s;
      cursor: pointer;
    }}
    .fm-card:hover {{
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
      transform: translateY(-2px);
    }}
    .fm-card-title {{
      color: var(--accent-secondary);
      font-weight: 600;
      font-size: 0.95rem;
    }}
    .fm-card-preview {{
      color: var(--text-muted);
      font-size: 0.8rem;
      font-style: italic;
      margin-top: 4px;
    }}
    .fm-content {{
      display: none;
      padding: 18px 20px;
      margin-top: -1px;
      margin-bottom: 10px;
      background: rgba(0,0,0,0.15);
      border: 1px solid rgba({ACCENT_SECONDARY_RGB}, 0.1);
      border-radius: 0 0 10px 10px;
      color: var(--text-secondary);
      font-size: 0.92rem;
      line-height: 1.7;
    }}
    .fm-content.open {{ display: block; }}
    .fm-card.open {{
      border-radius: 10px 10px 0 0;
      border-bottom-color: transparent;
    }}
    .fm-content p {{ margin-bottom: 10px; }}
    .fm-content h3 {{
      color: var(--text-primary);
      font-size: 1rem;
      margin: 14px 0 6px;
    }}
    .fm-content h3:first-child {{ margin-top: 0; }}
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
      border: 1px solid rgba({ACCENT_RGB},0.12);
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
    .lesson-subtitle {{
      color: var(--text-muted);
      font-size: 0.8rem;
      font-style: italic;
    }}
    .progress-dot {{
      position: absolute;
      top: 12px;
      right: 14px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 2px solid rgba({ACCENT_RGB},0.3);
      transition: all 0.3s;
    }}
    .progress-dot.visited {{
      border-color: var(--accent);
      background: rgba({ACCENT_RGB},0.3);
    }}
    .progress-dot.complete {{
      border-color: var(--accent);
      background: var(--accent);
    }}
    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba({ACCENT_RGB},0.15);
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
      .download-btn {{ padding: 10px 16px; min-height: 44px; display: inline-flex; align-items: center; margin-left: 0; }}
      .progress-bar {{ padding: 12px 14px; }}
      .section-header h2 {{ font-size: 1.15rem; }}
      .lesson-grid {{ grid-template-columns: 1fr; gap: 10px; }}
      .lesson-card {{ padding: 14px 16px; min-height: 44px; }}
    }}
  </style>
</head>
<body>
  {PASSWORD_JS}
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <header>
        <h1>{BOOK_TITLE}</h1>
        <p class="subtitle">&ldquo;If you change a person&rsquo;s mind, you change everything about them.&rdquo;</p>
        <p class="author" style="font-size: 0.85rem; margin-bottom: 8px;">&mdash; Freddie Anderson</p>
        <p class="author">{AUTHOR}</p>
        <p class="stats">
          <span>{TOTAL_CHAPTERS}</span> Chapters
        </p>
        <a href="../books.html" class="return-link">&larr; Return to Books</a>
        <span class="download-btn">PDF download coming soon</span>
      </header>

      <div class="progress-bar">
        <div class="label">
          <span>Reading Progress</span>
          <span id="progress-text">0 / {TOTAL_CHAPTERS} chapters</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
      </div>

      <section class="front-matter">
        <div class="section-header">
          <h2>Front Matter</h2>
        </div>

        <div class="fm-card" onclick="toggleFM('dedication')">
          <span class="fm-card-title">Dedication</span>
          <div class="fm-card-preview">To Freddie Anderson &mdash; the preacher who never answered a question without opening the Bible first.</div>
        </div>
        <div class="fm-content" id="dedication">
          <p><em>To Freddie Anderson &mdash; the preacher who never answered a question without opening the Bible first.</em></p>
          <p>When I had spent years trying to fill the emptiness with everything but God &mdash; self-help books, the wisdom of man, my own reasoning &mdash; it was Freddie who showed me something I had never seen before. Not a system. Not a tradition. A method: <em>&ldquo;That&rsquo;s a good question &mdash; let&rsquo;s see what the Bible says about it.&rdquo;</em></p>
          <p>And then he would actually let the Bible answer.</p>
          <p>He taught me how to think. How to read a passage and let it speak for itself. How to recognize error &mdash; not by memorizing someone else&rsquo;s arguments, but by knowing the text well enough to see where the teaching departed from it. He taught me that if you change a person&rsquo;s mind, you change everything about them &mdash; and if you don&rsquo;t change their mind, you change nothing about them.</p>
          <p>That principle &mdash; <em>change the mind, change the man</em> &mdash; is not just the title of this book. It is the story of my life.</p>
          <p>This book exists because God put Freddie Anderson in my path. And while God could have used anyone, He used him. And I am grateful.</p>
        </div>

        <div class="fm-card" onclick="toggleFM('authors-disclaimer')">
          <span class="fm-card-title">Author&rsquo;s Disclaimer</span>
          <div class="fm-card-preview">What this book is &mdash; and what it is not.</div>
        </div>
        <div class="fm-content" id="authors-disclaimer">
          <h3>What This Book Is Not</h3>
          <p>The author holds no degree in clinical psychology, no formal psychological training, and makes no claims of such. This is not a book of psychological principles. Neither is it a book of platitudes or clich&eacute;s. We don&rsquo;t flinch when it comes to the hard questions, and we don&rsquo;t offer easy answers where honest ones are needed.</p>
          <h3>What This Book Is</h3>
          <p>This is a straightforward examination of what God&rsquo;s Word has to say about faith, hope, and love &mdash; and about overcoming the trials and temptations that come in many forms &mdash; applied directly to the reality of addiction and its aftermath.</p>
          <p>It is also, where it serves as necessary background, about my own personal journey through addiction and the devastating consequences it brings &mdash; not only to the addict&rsquo;s family, but to every life it touches.</p>
          <p>It is about traveling <em>through the valley</em> &mdash; for everyone involved &mdash; and the realization that the Shepherd is already there, walking with you. And that <em>&ldquo;through&rdquo;</em> does not mean <em>&ldquo;stuck.&rdquo;</em> There is an opening at the other end.</p>
          <p>So whether you are the one struggling with addiction, a family member, a friend, or perhaps even a victim of another person&rsquo;s choices &mdash; it is my hope and prayer that this journey through Scripture will give you real answers. And that maybe, just maybe, there will come understanding, forgiveness, and restoration.</p>
        </div>

        <div class="fm-card" onclick="toggleFM('legal-disclaimer')">
          <span class="fm-card-title">Legal Disclaimer</span>
          <div class="fm-card-preview">Important information about the nature of this book&rsquo;s content.</div>
        </div>
        <div class="fm-content" id="legal-disclaimer">
          <p>The information contained in this book is provided for spiritual encouragement and biblical study purposes only. It is not intended as a substitute for professional medical advice, clinical diagnosis, psychological counseling, or any form of licensed treatment for substance abuse, addiction, or mental health conditions.</p>
          <p>The author is not a licensed physician, psychologist, psychiatrist, counselor, therapist, or clinical treatment provider. Nothing in this book should be construed as medical advice, psychological advice, or a recommendation to delay, discontinue, or forgo professional treatment of any kind.</p>
          <p>If you or someone you know is struggling with addiction, substance abuse, or a mental health crisis, please seek the help of a qualified medical or mental health professional immediately. In the event of a medical emergency, contact your local emergency services or call 911.</p>
          <p>The personal experiences shared in this book reflect one individual&rsquo;s journey and are not presented as representative of all experiences with addiction or recovery. Individual results and circumstances vary, and no specific outcome is promised or guaranteed.</p>
          <p>Scripture quotations are taken from the New American Standard Bible&reg; (NASB), Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation. Used by permission. All rights reserved. (www.lockman.org)</p>
        </div>
      </section>

      <section class="chapter-section">
        <div class="section-header">
          <h2>Chapters</h2>
        </div>
        <div class="lesson-grid">
{cards_html}
        </div>
      </section>

      <footer>
        <p class="copyright">{BOOK_TITLE} {COPYRIGHT}<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var TOTAL_CHAPTERS = {TOTAL_CHAPTERS};
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

    function toggleFM(id) {{
      var content = document.getElementById(id);
      var card = content.previousElementSibling;
      var isOpen = content.classList.contains('open');
      // Close all
      document.querySelectorAll('.fm-content').forEach(function(el) {{ el.classList.remove('open'); }});
      document.querySelectorAll('.fm-card').forEach(function(el) {{ el.classList.remove('open'); }});
      // Open this one if it was closed
      if (!isOpen) {{
        content.classList.add('open');
        card.classList.add('open');
      }}
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      updateProgressUI();
    }});
  </script>
  <script src="/nm-beacon.js" defer></script>
</body>
</html>"""

    return index_html


def main():
    print(f"Generating HTML book: {BOOK_TITLE}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Generate index.html
    index_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(generate_index_html())
    print(f"  Generated: index.html")

    # Generate chapter pages
    for ch in CHAPTERS:
        md_path = os.path.join(SCRIPT_DIR, ch['file'])
        if not os.path.exists(md_path):
            print(f"  WARNING: {ch['file']} not found, skipping chapter {ch['num']}")
            continue

        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        lines = md_content.split('\n')

        # Chapters 1-4 use > blockquote syntax
        # Chapters 5-10 use *"text"* / — Reference syntax
        if ch['num'] <= 4:
            blocks = parse_markdown_chapters_1_4(lines)
        else:
            blocks = parse_markdown_chapters_5_10(lines)

        content_html = render_content_blocks(blocks)
        chapter_html = generate_chapter_html(ch, content_html)

        filename = f"chapter-{ch['num']:02d}.html"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chapter_html)
        print(f"  Generated: {filename} ({len(blocks)} content blocks)")

    print()
    print("Done! All files generated successfully.")
    print(f"  - index.html")
    for i in range(1, TOTAL_CHAPTERS + 1):
        print(f"  - chapter-{i:02d}.html")


if __name__ == '__main__':
    main()
