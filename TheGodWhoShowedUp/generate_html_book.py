#!/usr/bin/env python3
"""Generate HTML chapter files for The God Who Showed Up.

Reads markdown source files and generates glassmorphism-themed HTML chapters
matching the NobleMind Study book format.
"""

import re
import html
from pathlib import Path

BOOK_DIR = Path(__file__).parent

# --- Book metadata ---
BOOK_TITLE = "The God Who Showed Up"
BOOK_SUBTITLE = "What His Names Reveal About Who He Is"
AUTHORS = "Paul &amp; Pam Hainline"
COPYRIGHT_YEAR = "2026"

# --- Color theme: Warm amber gold + deep teal ---
ACCENT = "#D4A854"         # warm amber gold
ACCENT_RGB = "212,168,84"
ACCENT_SECONDARY = "#4A8B8C"  # deep teal
ACCENT_SEC_RGB = "74,139,140"

# --- Chapter definitions ---
CHAPTERS = [
    {
        "md": "TheGodWhoShowedUp_Introduction.md",
        "html": "introduction.html",
        "label": "Introduction",
        "title": "What\u2019s In A Name?",
        "part": None,
        "skip_header_lines": 7,  # Skip title/author/copyright block
        "start_after": "## Introduction: What's In A Name?",
    },
    {
        "md": "TheGodWhoShowedUp_Chapter1.md",
        "html": "chapter-01.html",
        "label": "Chapter 1",
        "title": "Elohim \u2014 The God Who Was Already There",
        "part": "Part I: The God Who Hears",
    },
    {
        "md": "TheGodWhoShowedUp_Chapter2.md",
        "html": "chapter-02.html",
        "label": "Chapter 2",
        "title": "El Roi \u2014 The God Who Sees",
        "part": None,
    },
    {
        "md": "TheGodWhoShowedUp_Chapter3.md",
        "html": "chapter-03.html",
        "label": "Chapter 3",
        "title": "El Shaddai \u2014 God Almighty",
        "part": None,
    },
    {
        "md": "TheGodWhoShowedUp_Chapter4.md",
        "html": "chapter-04.html",
        "label": "Chapter 4",
        "title": "Jehovah Jireh \u2014 The Lord Will Provide",
        "part": "Part II: When the Veil Still Stood",
    },
    {
        "md": "TheGodWhoShowedUp_Chapter5.md",
        "html": "chapter-05.html",
        "label": "Chapter 5",
        "title": "Yahweh \u2014 The Self-Existent One",
        "part": None,
    },
    {
        "md": "TheGodWhoShowedUp_Chapter6.md",
        "html": "chapter-06.html",
        "label": "Chapter 6",
        "title": "Jehovah Rapha \u2014 The Lord Who Heals",
        "part": "Part III: The Veil Is Torn",
    },
    {
        "md": "TheGodWhoShowedUp_Chapter7.md",
        "html": "chapter-07.html",
        "label": "Chapter 7",
        "title": "Jehovah Nissi \u2014 The Lord Is My Banner",
        "part": None,
    },
    {
        "md": "TheGodWhoShowedUp_Chapter8.md",
        "html": "chapter-08.html",
        "label": "Chapter 8",
        "title": "Jehovah Shalom \u2014 The Lord Is Peace",
        "part": "Part IV: Through the Open Door",
    },
    {
        "md": "TheGodWhoShowedUp_Chapter9.md",
        "html": "chapter-09.html",
        "label": "Chapter 9",
        "title": "Jehovah Rohi \u2014 The Lord Is My Shepherd",
        "part": None,
    },
    {
        "md": "TheGodWhoShowedUp_Chapter10.md",
        "html": "chapter-10.html",
        "label": "Chapter 10",
        "title": "Jehovah Tsidkenu \u2014 The Lord Our Righteousness",
        "part": "Part V: The Life of Prayer",
    },
    {
        "md": "TheGodWhoShowedUp_Chapter11.md",
        "html": "chapter-11.html",
        "label": "Chapter 11",
        "title": "Jehovah Shammah \u2014 The Lord Is There",
        "part": None,
    },
    {
        "md": "TheGodWhoShowedUp_Chapter12.md",
        "html": "chapter-12.html",
        "label": "Chapter 12",
        "title": "Immanuel \u2014 God With Us",
        "part": None,
    },
    {
        "md": "TheGodWhoShowedUp_Conclusion.md",
        "html": "conclusion.html",
        "label": "Conclusion",
        "title": "He Is Still Showing Up",
        "part": None,
    },
]

# Chapter number labels for display
CHAPTER_NUMS = {
    "introduction.html": None,
    "chapter-01.html": "CHAPTER ONE",
    "chapter-02.html": "CHAPTER TWO",
    "chapter-03.html": "CHAPTER THREE",
    "chapter-04.html": "CHAPTER FOUR",
    "chapter-05.html": "CHAPTER FIVE",
    "chapter-06.html": "CHAPTER SIX",
    "chapter-07.html": "CHAPTER SEVEN",
    "chapter-08.html": "CHAPTER EIGHT",
    "chapter-09.html": "CHAPTER NINE",
    "chapter-10.html": "CHAPTER TEN",
    "chapter-11.html": "CHAPTER ELEVEN",
    "chapter-12.html": "CHAPTER TWELVE",
    "conclusion.html": None,
}


def md_to_html_content(md_text):
    """Convert markdown body text to HTML content."""
    lines = md_text.strip().split("\n")
    output = []
    in_blockquote = False
    bq_lines = []

    def flush_blockquote():
        nonlocal in_blockquote, bq_lines
        if bq_lines:
            # Determine if this is a scripture quote
            content = "\n".join(bq_lines)
            is_scripture = any(c in content for c in ["\u2014", "—", "–"]) and any(
                book in content for book in [
                    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
                    "Joshua", "Judges", "Ruth", "Samuel", "Kings", "Chronicles",
                    "Ezra", "Nehemiah", "Esther", "Job", "Psalm", "Proverbs",
                    "Ecclesiastes", "Song", "Isaiah", "Jeremiah", "Lamentations",
                    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah",
                    "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
                    "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John",
                    "Acts", "Romans", "Corinthians", "Galatians", "Ephesians",
                    "Philippians", "Colossians", "Thessalonians", "Timothy",
                    "Titus", "Philemon", "Hebrews", "James", "Peter", "Jude",
                    "Revelation", "NASB",
                ]
            )
            cls = ' class="scripture"' if is_scripture else ""

            # Split into quote text and citation
            quote_parts = []
            cite_part = None
            for bl in bq_lines:
                # Check if line is a citation (starts with — or em dash)
                stripped = bl.strip()
                if stripped.startswith("\u2014") or stripped.startswith("—") or stripped.startswith("--"):
                    cite_part = stripped
                elif stripped.startswith("\u2013"):  # en-dash
                    cite_part = stripped
                else:
                    quote_parts.append(bl)

            output.append(f"        <blockquote{cls}>")
            for qp in quote_parts:
                processed = inline_format(qp.strip())
                if processed:
                    output.append(f"          <p>{processed}</p>")
            if cite_part:
                output.append(f"          <cite>{inline_format(cite_part.strip())}</cite>")
            output.append("        </blockquote>")
            bq_lines = []
        in_blockquote = False

    for line in lines:
        stripped = line.strip()

        # Skip chapter headings (already handled by template)
        if stripped.startswith("# ") and not stripped.startswith("## "):
            continue
        if stripped.startswith("## ") and lines.index(line) < 5:
            continue

        # Horizontal rule / section divider
        if stripped == "---":
            if not in_blockquote:
                continue  # Skip top-of-file rules
            flush_blockquote()
            continue

        # Asterisk dividers
        if stripped in (r"\* \* \*", "* * *", "\\* \\* \\*", "***"):
            flush_blockquote()
            output.append('        <div class="divider">\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500</div>')
            continue

        # Blockquote lines
        if stripped.startswith("> "):
            if not in_blockquote:
                flush_blockquote()
                in_blockquote = True
            bq_lines.append(stripped[2:])
            continue
        elif stripped == ">" and in_blockquote:
            bq_lines.append("")
            continue
        elif in_blockquote and not stripped.startswith(">"):
            flush_blockquote()

        # Empty line
        if not stripped:
            continue

        # Section headers (plain text that acts as a subheading)
        # In the markdown, these appear as plain lines after \* \* \* dividers
        # We detect them by context: short lines that aren't paragraphs
        if stripped.startswith("## "):
            flush_blockquote()
            header_text = inline_format(stripped[3:])
            output.append(f"        <h2>{header_text}</h2>")
            continue

        # Italicized section headers (like *The Veil*)
        if re.match(r"^\*[^*]+\*$", stripped) and len(stripped) < 80:
            inner = stripped[1:-1]
            output.append(f"        <h3><em>{html_escape(inner)}</em></h3>")
            continue

        # Plain section headers (short lines, no period, likely a header)
        if (len(stripped) < 60 and not stripped.endswith(".")
                and not stripped.endswith("?") and not stripped.endswith("!")
                and not stripped.endswith('"') and not stripped.endswith("\u201d")
                and not stripped.startswith("*") and not stripped.startswith('"')
                and not stripped.startswith("\u201c")
                and not any(c in stripped for c in [","])
                and stripped[0].isupper()
                and not stripped.startswith("Related name")
                and "—" not in stripped[:5]):
            # Check if it looks like a section header vs a short paragraph
            words = stripped.split()
            if len(words) <= 10 and not any(stripped.startswith(w) for w in [
                "This", "That", "The ", "And ", "But ", "He ", "She ", "It ",
                "If ", "When", "What", "How", "Why", "Not ", "No ", "Every",
                "A ", "An ", "In ", "On ", "For ", "With", "From", "Your",
                "Their", "Our", "His ", "Her ", "Its ", "We ", "You ", "They",
                "There", "Here", "Now", "Then", "So ", "Yet ", "Still",
                "Before", "After", "Each", "Some", "All ", "None", "Most",
            ]):
                output.append(f"        <h2>{inline_format(stripped)}</h2>")
                continue

        # Regular paragraph
        flush_blockquote()
        output.append(f"        <p>{inline_format(stripped)}</p>")

    flush_blockquote()
    return "\n".join(output)


def inline_format(text):
    """Convert inline markdown formatting to HTML."""
    # Escape HTML entities first (but preserve already-escaped ones)
    text = html_escape(text)

    # Bold+italic: ***text*** or ___text___
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)

    # Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # Italic: *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

    # Handle escaped asterisks
    text = text.replace(r"\*", "*")

    return text


def html_escape(text):
    """Escape HTML special characters, preserving entities."""
    # Don't double-escape existing entities
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Restore common entities
    text = text.replace("&amp;mdash;", "&mdash;")
    text = text.replace("&amp;ldquo;", "&ldquo;")
    text = text.replace("&amp;rdquo;", "&rdquo;")
    text = text.replace("&amp;lsquo;", "&lsquo;")
    text = text.replace("&amp;rsquo;", "&rsquo;")
    text = text.replace("&amp;amp;", "&amp;")
    text = text.replace("&amp;nbsp;", "&nbsp;")
    return text


def read_chapter_md(ch):
    """Read markdown file and extract the body content."""
    md_path = BOOK_DIR / ch["md"]
    if not md_path.exists():
        print(f"  WARNING: {ch['md']} not found!")
        return ""

    text = md_path.read_text(encoding="utf-8")

    # For the introduction, skip the title/copyright block
    if ch.get("start_after"):
        marker = ch["start_after"]
        idx = text.find(marker)
        if idx >= 0:
            text = text[idx + len(marker):]

    # For regular chapters, skip the # heading and ## subtitle
    lines = text.split("\n")
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and i < 5:
            start = i + 1
            continue
        if stripped.startswith("## ") and i < 5:
            start = i + 1
            continue
        if stripped == "---" and i < 6:
            start = i + 1
            continue
        if i > 5:
            break

    return "\n".join(lines[start:])


def build_nav_options(current_html):
    """Build the chapter select dropdown options."""
    opts = []
    for ch in CHAPTERS:
        selected = ' selected' if ch["html"] == current_html else ''
        short = ch["label"]
        if ch["label"] not in ("Introduction", "Conclusion"):
            short = f'{ch["label"]}: {ch["title"].split(" — ")[0] if " — " in ch["title"] else ch["title"]}'
        else:
            short = f'{ch["label"]}: {ch["title"]}'
        opts.append(f'            <option value="{ch["html"]}"{selected}>{short}</option>')
    return "\n".join(opts)


def build_footer_nav(idx):
    """Build prev/next navigation links."""
    prev_link = ""
    next_link = ""
    if idx > 0:
        prev_ch = CHAPTERS[idx - 1]
        prev_link = f'          <a href="{prev_ch["html"]}">&larr; {prev_ch["label"]}</a>'
    else:
        prev_link = '          <a href="index.html">&larr; Table of Contents</a>'

    if idx < len(CHAPTERS) - 1:
        next_ch = CHAPTERS[idx + 1]
        next_link = f'          <a href="{next_ch["html"]}">{next_ch["label"]} &rarr;</a>'
    else:
        next_link = '          <a href="index.html">Table of Contents &rarr;</a>'

    return prev_link, next_link


def get_epigraph(md_text, ch):
    """Extract the first blockquote as the chapter epigraph."""
    lines = md_text.strip().split("\n")
    bq_lines = []
    found_start = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("> ") and not found_start:
            found_start = True
            bq_lines.append(stripped[2:])
        elif stripped.startswith("> ") and found_start:
            bq_lines.append(stripped[2:])
        elif stripped == ">" and found_start:
            bq_lines.append("")
        elif found_start:
            break

    if not bq_lines:
        return "", ""

    quote_parts = []
    cite_part = ""
    for bl in bq_lines:
        s = bl.strip()
        if s.startswith("\u2014") or s.startswith("—") or s.startswith("--"):
            cite_part = s
        elif s.startswith("\u2013"):
            cite_part = s
        else:
            if s:
                quote_parts.append(s)

    quote = " ".join(quote_parts)
    # Clean up markdown formatting
    quote = re.sub(r"\*(.+?)\*", r"\1", quote)  # Remove italics markers
    quote = quote.strip('"').strip("\u201c").strip("\u201d")

    return quote, cite_part


def generate_chapter_html(ch, idx):
    """Generate a complete HTML file for one chapter."""
    md_body = read_chapter_md(ch)
    epigraph_quote, epigraph_cite = get_epigraph(md_body, ch)

    # Remove the epigraph from the body (first blockquote)
    body_lines = md_body.strip().split("\n")
    clean_lines = []
    skip_first_bq = True
    in_first_bq = False
    for line in body_lines:
        stripped = line.strip()
        if skip_first_bq and stripped.startswith("> "):
            in_first_bq = True
            continue
        elif skip_first_bq and stripped == ">" and in_first_bq:
            continue
        elif in_first_bq and not stripped.startswith(">"):
            in_first_bq = False
            skip_first_bq = False
            clean_lines.append(line)
        else:
            clean_lines.append(line)

    content_html = md_to_html_content("\n".join(clean_lines))
    nav_options = build_nav_options(ch["html"])
    prev_link, next_link = build_footer_nav(idx)

    chapter_num = CHAPTER_NUMS.get(ch["html"])
    ch_num_html = f'        <p class="chapter-num">{chapter_num}</p>' if chapter_num else ""

    # Part subtitle
    part_html = ""
    if ch.get("part"):
        part_html = f'        <p class="subtitle">{ch["part"]}</p>'

    # Epigraph
    epigraph_html = ""
    if epigraph_quote:
        epigraph_html = f"""
      <div class="epigraph">
        <blockquote>
          &ldquo;{html_escape(epigraph_quote)}&rdquo;
        </blockquote>
        <cite>{html_escape(epigraph_cite)}</cite>
      </div>"""

    ch_idx = idx + 1 if chapter_num else 0

    page_title = f"{ch['label']}: {ch['title']}" if ch['label'] not in (ch['title'],) else ch['title']

    return HTML_TEMPLATE.format(
        page_title=page_title,
        book_title=BOOK_TITLE,
        accent=ACCENT,
        accent_rgb=ACCENT_RGB,
        accent_sec=ACCENT_SECONDARY,
        accent_sec_rgb=ACCENT_SEC_RGB,
        nav_options=nav_options,
        chapter_num_html=ch_num_html,
        chapter_title=ch["title"],
        part_html=part_html,
        epigraph_html=epigraph_html,
        content_html=content_html,
        prev_link=prev_link,
        next_link=next_link,
        authors=AUTHORS,
        copyright_year=COPYRIGHT_YEAR,
        ch_idx=ch_idx,
    )


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title} | {book_title}</title>
  <style>
    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #c0b8a8;
      --text-muted: #8a8278;
      --accent: {accent};
      --accent-glow: rgba({accent_rgb}, 0.4);
      --accent-soft: rgba({accent_rgb}, 0.12);
      --accent-secondary: {accent_sec};
      --accent-secondary-glow: rgba({accent_sec_rgb}, 0.3);
      --scripture-border: {accent};
      --box-principle: {accent_sec};
      --box-principle-bg: rgba({accent_sec_rgb}, 0.08);
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
        radial-gradient(circle at top, rgba({accent_rgb},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({accent_sec_rgb},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({accent_rgb},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({accent_sec_rgb},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({accent_rgb},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({accent_sec_rgb},0.15),
        0 0 80px rgba({accent_rgb},0.2);
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
      background: radial-gradient(ellipse at top, rgba({accent_rgb},0.04), transparent 70%);
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
      background: radial-gradient(circle at top, rgba({accent_rgb},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({accent_rgb},0.4);
    }}
    .nav-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
      padding: 14px 18px;
      background: rgba({accent_rgb},0.04);
      border-radius: 12px;
      border: 1px solid rgba({accent_rgb},0.12);
      position: relative;
      z-index: 1;
    }}
    .home-link {{
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--accent);
      text-decoration: none;
      font-weight: 500;
      font-size: 0.9rem;
    }}
    .home-link svg {{ width: 18px; height: 18px; fill: var(--accent); }}
    .home-link:hover {{ color: var(--text-primary); }}
    .home-link:hover svg {{ fill: var(--text-primary); }}
    #chapter-select {{
      background: rgba(0,0,0,0.3);
      color: var(--text-primary);
      border: 1px solid rgba({accent_rgb},0.2);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 0.85rem;
      max-width: 320px;
      cursor: pointer;
    }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba({accent_rgb},0.2);
      position: relative;
      z-index: 1;
    }}
    .chapter-num {{
      font-size: 0.85rem;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 8px;
    }}
    h1 {{
      font-size: 1.9rem;
      color: var(--accent);
      text-shadow: 0 0 20px var(--accent-glow);
      font-weight: 600;
      line-height: 1.3;
      margin-bottom: 8px;
    }}
    .subtitle {{
      font-size: 0.95rem;
      color: var(--accent-secondary);
      font-style: italic;
    }}
    .epigraph {{
      text-align: center;
      margin: 0 auto 32px;
      max-width: 600px;
      padding: 24px;
      background: rgba({accent_rgb},0.04);
      border-radius: 14px;
      border: 1px solid rgba({accent_rgb},0.15);
      position: relative;
      z-index: 1;
    }}
    .epigraph blockquote {{
      font-style: italic;
      font-size: 1.05rem;
      color: var(--text-primary);
      line-height: 1.8;
      margin-bottom: 8px;
      border: none;
      padding: 0;
    }}
    .epigraph cite {{
      display: block;
      color: var(--accent);
      font-style: normal;
      font-weight: 500;
      font-size: 0.9rem;
    }}
    .content {{
      position: relative;
      z-index: 1;
    }}
    .content p {{
      margin-bottom: 18px;
    }}
    .content h2 {{
      font-size: 1.35rem;
      color: var(--accent);
      text-shadow: 0 0 10px var(--accent-glow);
      margin: 36px 0 16px;
      font-weight: 600;
    }}
    .content h3 {{
      font-size: 1.15rem;
      color: var(--accent-secondary);
      margin: 28px 0 14px;
      font-weight: 600;
    }}
    .content blockquote {{
      margin: 24px 0;
      padding: 20px 24px;
      background: rgba({accent_rgb},0.04);
      border-left: 3px solid var(--scripture-border);
      border-radius: 0 12px 12px 0;
      font-style: italic;
      color: var(--text-primary);
    }}
    .content blockquote.scripture {{
      border-left-color: var(--accent);
    }}
    .content blockquote p {{
      margin-bottom: 8px;
    }}
    .content blockquote cite {{
      display: block;
      margin-top: 8px;
      font-style: normal;
      font-weight: 600;
      color: var(--accent);
      font-size: 0.9rem;
    }}
    .divider {{
      text-align: center;
      margin: 32px 0;
      color: rgba({accent_rgb},0.3);
      letter-spacing: 0.3em;
      font-size: 0.85rem;
    }}
    .principle-box {{
      margin: 24px 0;
      padding: 20px 24px;
      background: var(--box-principle-bg);
      border: 1px solid rgba({accent_sec_rgb},0.2);
      border-radius: 12px;
      text-align: center;
    }}
    .reflection {{
      margin-top: 36px;
      padding: 24px;
      background: rgba({accent_sec_rgb},0.04);
      border-radius: 14px;
      border: 1px solid rgba({accent_sec_rgb},0.15);
    }}
    .reflection h3 {{
      font-size: 1.1rem;
      color: var(--accent-secondary);
      margin-bottom: 14px;
    }}
    .reflection-question {{
      margin-bottom: 12px;
    }}
    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba({accent_rgb},0.15);
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
      font-size: 0.9rem;
      padding: 8px 0;
      transition: color 0.3s;
    }}
    .footer-nav a:hover {{ color: var(--accent); }}
    .copyright {{
      text-align: center;
      color: var(--text-muted);
      font-size: 0.78rem;
      margin-top: 12px;
    }}
    .copyright a {{ color: var(--accent-secondary); text-decoration: none; }}
    .mark-complete {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin: 24px auto 0;
      padding: 12px 24px;
      background: rgba({accent_rgb},0.06);
      border: 1px solid rgba({accent_rgb},0.2);
      border-radius: 10px;
      cursor: pointer;
      color: var(--text-secondary);
      font-size: 0.9rem;
      transition: all 0.3s;
      user-select: none;
      position: relative;
      z-index: 1;
    }}
    .mark-complete:hover {{
      background: rgba({accent_rgb},0.12);
      border-color: var(--accent);
      color: var(--accent);
    }}
    .mark-complete.done {{
      background: rgba({accent_rgb},0.15);
      border-color: var(--accent);
      color: var(--accent);
    }}
    .mark-complete .check {{
      width: 18px;
      height: 18px;
      border: 2px solid currentColor;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
    }}
    .mark-complete.done .check::after {{ content: "\\2713"; }}
    @media (max-width: 600px) {{
      html {{ -webkit-text-size-adjust: 100%; }}
      body {{ padding: 10px 6px; font-size: 1rem; line-height: 1.75; }}
      .glass-page-wrapper {{ border-radius: 16px; padding: 2px; }}
      .glass-page-inner {{ padding: 1.2rem 1rem; border-radius: 14px; }}
      .glass-tab {{ width: 60px; height: 10px; bottom: -8px; }}
      .nav-controls {{ padding: 10px 12px; }}
      #chapter-select {{ max-width: 200px; font-size: 0.8rem; }}
      h1 {{ font-size: 1.5rem; }}
      .content blockquote {{ padding: 14px 16px; }}
      .footer-nav a {{ padding: 12px 0; min-height: 44px; display: flex; align-items: center; }}
    }}
  </style>
</head>
<body>
  <div class="glass-page-wrapper">
    <div class="glass-page-inner">

      <nav class="nav-controls">
        <a href="index.html" class="home-link">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          {book_title}
        </a>
          <select id="chapter-select" onchange="goToChapter(this.value)">
            <option value="">Jump to...</option>
{nav_options}
          </select>
      </nav>

      <header>
{chapter_num_html}
        <h1>{chapter_title}</h1>
{part_html}
      </header>
{epigraph_html}
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
        <p class="copyright">{book_title} &copy; {copyright_year} {authors}. All Rights Reserved.<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    function goToChapter(val) {{
      if (val) window.location.href = val;
    }}

    var PROGRESS_KEY = 'theGodWhoShowedUp_progress';
    var CH_NUM = {ch_idx};

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}

    function markVisited() {{
      if (CH_NUM === 0) return;
      var p = loadProgress();
      if (!p['ch' + CH_NUM]) p['ch' + CH_NUM] = 'visited';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
    }}

    function toggleComplete() {{
      if (CH_NUM === 0) return;
      var p = loadProgress();
      var key = 'ch' + CH_NUM;
      p[key] = p[key] === 'complete' ? 'visited' : 'complete';
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
      updateCompleteBtn();
    }}

    function updateCompleteBtn() {{
      if (CH_NUM === 0) return;
      var p = loadProgress();
      var btn = document.getElementById('mark-complete');
      if (p['ch' + CH_NUM] === 'complete') {{
        btn.classList.add('done');
        btn.querySelector('span:last-child').textContent = 'Chapter Complete';
      }} else {{
        btn.classList.remove('done');
        btn.querySelector('span:last-child').textContent = 'Mark Chapter Complete';
      }}
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      markVisited();
      updateCompleteBtn();
    }});

    document.addEventListener('keydown', function(e) {{
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
      if (e.key === 'ArrowLeft') {{
        var prev = document.querySelector('.footer-nav a:first-child');
        if (prev) prev.click();
      }} else if (e.key === 'ArrowRight') {{
        var next = document.querySelector('.footer-nav a:last-child');
        if (next) next.click();
      }}
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


def generate_index():
    """Generate the book index/table of contents page."""
    chapter_cards = []
    current_part = None

    for ch in CHAPTERS:
        if ch.get("part") and ch["part"] != current_part:
            current_part = ch["part"]
            if chapter_cards:
                chapter_cards.append("        </div>\n      </section>\n")
            chapter_cards.append(f"""      <section class="chapter-section">
        <div class="section-header">
          <h2>{current_part}</h2>
        </div>
        <div class="lesson-grid">""")
        elif not current_part and not chapter_cards:
            chapter_cards.append("""      <section class="chapter-section">
        <div class="lesson-grid">""")

        ch_num = ""
        data_attr = ""
        dot_html = ""
        if ch["label"].startswith("Chapter"):
            num = ch["label"].split(" ")[1]
            ch_num = f'<span class="lesson-num">{ch["label"]}</span>'
            data_attr = f' data-ch="{num}"'
            dot_html = f'\n            <span class="progress-dot" id="dot-{num}"></span>'
        else:
            ch_num = f'<span class="lesson-num">{ch["label"]}</span>'

        # Short title for card (remove the em-dash subtitle for cleaner display)
        card_title = ch["title"]

        chapter_cards.append(f"""          <a href="{ch['html']}" class="lesson-card"{data_attr}>
            {ch_num}
            <div class="lesson-title">{card_title}</div>{dot_html}
          </a>""")

    chapter_cards.append("        </div>\n      </section>")

    cards_html = "\n".join(chapter_cards)

    return INDEX_TEMPLATE.format(
        book_title=BOOK_TITLE,
        book_subtitle=BOOK_SUBTITLE,
        accent=ACCENT,
        accent_rgb=ACCENT_RGB,
        accent_sec=ACCENT_SECONDARY,
        accent_sec_rgb=ACCENT_SEC_RGB,
        authors=AUTHORS,
        copyright_year=COPYRIGHT_YEAR,
        chapter_cards=cards_html,
    )


INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Table of Contents | {book_title}</title>
  <style>
    :root {{
      --bg-dark: #0d0d0d;
      --bg-inner: rgba(13, 15, 20, 0.96);
      --text-primary: #f0ece4;
      --text-secondary: #c0b8a8;
      --text-muted: #8a8278;
      --accent: {accent};
      --accent-glow: rgba({accent_rgb}, 0.4);
      --accent-soft: rgba({accent_rgb}, 0.12);
      --accent-secondary: {accent_sec};
      --accent-secondary-glow: rgba({accent_sec_rgb}, 0.3);
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
        radial-gradient(circle at top, rgba({accent_rgb},0.06), transparent 50%),
        radial-gradient(circle at bottom, rgba({accent_sec_rgb},0.04), transparent 50%);
      pointer-events: none;
    }}
    .glass-page-wrapper {{
      position: relative;
      z-index: 10;
      border-radius: calc(var(--radius-card) + 4px);
      padding: 3px;
      background:
        radial-gradient(circle at top left, rgba({accent_rgb},0.45), transparent 50%),
        radial-gradient(circle at top right, rgba({accent_sec_rgb},0.35), transparent 50%),
        radial-gradient(circle at bottom, rgba({accent_rgb},0.2), transparent 55%);
      box-shadow:
        0 0 50px rgba({accent_sec_rgb},0.15),
        0 0 80px rgba({accent_rgb},0.2);
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
      background: radial-gradient(ellipse at top, rgba({accent_rgb},0.04), transparent 70%);
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
      background: radial-gradient(circle at top, rgba({accent_rgb},0.85), rgba(13,13,13,1));
      box-shadow: 0 0 30px rgba({accent_rgb},0.4);
    }}
    header {{
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba({accent_rgb},0.2);
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
    .stats {{
      margin-top: 12px;
      color: var(--text-secondary);
      font-size: 0.9rem;
    }}
    .stats span {{ color: var(--accent); font-weight: 600; }}
    .return-link {{
      display: inline-block;
      margin-top: 18px;
      padding: 10px 20px;
      background: rgba({accent_sec_rgb},0.08);
      border: 1px solid rgba({accent_sec_rgb},0.25);
      border-radius: 8px;
      color: var(--accent-secondary);
      text-decoration: none;
      font-size: 0.9rem;
      transition: all 0.3s ease;
    }}
    .return-link:hover {{
      background: rgba({accent_sec_rgb},0.15);
      border-color: var(--accent-secondary);
      box-shadow: 0 0 15px var(--accent-secondary-glow);
    }}
    .key-verse {{
      margin: 24px 0;
      padding: 22px;
      background: rgba({accent_rgb},0.04);
      border-radius: 14px;
      text-align: center;
      border: 1px solid rgba({accent_rgb},0.15);
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
      background: rgba({accent_rgb},0.04);
      border: 1px solid rgba({accent_rgb},0.12);
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
      border: 1px solid rgba({accent_rgb},0.12);
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
      border: 2px solid rgba({accent_rgb},0.3);
      transition: all 0.3s;
    }}
    .progress-dot.visited {{ border-color: var(--accent); background: rgba({accent_rgb},0.3); }}
    .progress-dot.complete {{ border-color: var(--accent); background: var(--accent); }}
    footer {{
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid rgba({accent_rgb},0.15);
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
      .glass-tab {{ width: 60px; height: 10px; bottom: -8px; }}
      .return-link {{ padding: 10px 16px; min-height: 44px; display: inline-flex; align-items: center; }}
      h1 {{ font-size: 1.8rem; }}
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
        <h1>{book_title}</h1>
        <p class="subtitle">{book_subtitle}</p>
        <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px;">{authors}</p>
        <p class="stats">
          <span>12</span> Chapters &bull; Introduction &bull; Conclusion &bull; <span>5</span> Parts
        </p>
        <a href="../index.html" class="return-link">&larr; Return to Noble Mind Study</a>
      </header>

      <div class="hero-cover">
        <img src="cover_front.jpg" alt="The God Who Showed Up — book cover" loading="eager">
      </div>

      <section class="key-verse">
        <blockquote>
          &ldquo;Then Moses said to God, &lsquo;Behold, I am going to the sons of Israel, and I will say to them, &ldquo;The God of your fathers has sent me to you.&rdquo; Now they may say to me, &ldquo;What is His name?&rdquo; What shall I say to them?&rsquo; God said to Moses, &lsquo;I AM WHO I AM.&rsquo;&rdquo;
        </blockquote>
        <cite>&mdash; Exodus 3:13&ndash;14 (NASB)</cite>
      </section>

      <div class="progress-bar">
        <div class="label">
          <span>Study Progress</span>
          <span id="progress-text">0 / 12 chapters</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
      </div>

{chapter_cards}

      <footer>
        <p class="copyright">{book_title} &copy; {copyright_year} {authors}. All Rights Reserved.<br>
        Digitized for <a href="../index.html">NobleMind.Study</a></p>
      </footer>
    </div>
    <div class="glass-tab"></div>
  </div>
  <script>
    var PROGRESS_KEY = 'theGodWhoShowedUp_progress';

    function loadProgress() {{
      try {{ return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {{}}; }}
      catch(e) {{ return {{}}; }}
    }}

    function updateProgressUI() {{
      var p = loadProgress();
      var complete = 0;
      for (var i = 1; i <= 12; i++) {{
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
      document.getElementById('progress-text').textContent = complete + ' / 12 chapters';
      document.getElementById('progress-fill').style.width = (complete / 12 * 100) + '%';
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      updateProgressUI();
    }});
  </script>
  <script src="/nm-core.js" defer></script>
  <script src="/assets/study-tools.js" defer></script>
</body>
</html>"""


def main():
    print(f"Generating HTML book: {BOOK_TITLE}")
    print(f"  Theme: Gold ({ACCENT}) + Teal ({ACCENT_SECONDARY})")
    print()

    # Generate index
    print("  Generating: index.html")
    index_html = generate_index()
    (BOOK_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Generate chapters
    for idx, ch in enumerate(CHAPTERS):
        print(f"  Generating: {ch['html']} -> {ch['label']}: {ch['title']}")
        chapter_html = generate_chapter_html(ch, idx)
        (BOOK_DIR / ch["html"]).write_text(chapter_html, encoding="utf-8")

    print(f"\nGenerated {len(CHAPTERS) + 1} HTML files in {BOOK_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
