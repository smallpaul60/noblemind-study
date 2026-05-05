#!/usr/bin/env python3
"""
One-shot helper for inserting new chapter 9 into Strength and Dignity.

Renames already done by hand (git mv chapter-13 -> chapter-14, etc).
This script:
  - Updates each renamed chapter file (now 10-14): title, canonical, chapter-num word,
    footer-nav prev/next, CH_NUM, and chapter-select dropdown.
  - Updates chapter-08, introduction, conclusion, scripture-index, new chapter-09:
    chapter-select dropdown only, plus chapter-08 next-nav, conclusion prev-nav.

Run once. Idempotent? No. Safe to commit & rerun on a fresh checkout — but don't
double-run on the same files; the chapter-num word replacements would slide.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "StrengthAndDignity"

WORD = {
    1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX", 7: "SEVEN",
    8: "EIGHT", 9: "NINE", 10: "TEN", 11: "ELEVEN", 12: "TWELVE", 13: "THIRTEEN",
    14: "FOURTEEN",
}

# Canonical 14-chapter dropdown rows in order (option_value, label)
ROWS = [
    ("",                       "Jump to..."),
    ("introduction.html",      "Introduction: Nobody Told You This"),
    ("chapter-01.html",        "Ch 1: Your Name Is Your Most Valuable Asset"),
    ("chapter-02.html",        "Ch 2: The Woman in the Mirror"),
    ("chapter-03.html",        "Ch 3: When Nobody's Watching"),
    ("chapter-04.html",        "Ch 4: Made On Purpose, For a Purpose"),
    ("chapter-05.html",        "Ch 5: The Relationship You Need Most"),
    ("chapter-06.html",        "Ch 6: The Bible Isn't What You Think"),
    ("chapter-07.html",        "Ch 7: Putting Down the Phone"),
    ("chapter-08.html",        "Ch 8: He Is Somebody's Son"),
    ("chapter-09.html",        "Ch 9: What to Expect from a Young Man"),
    ("chapter-10.html",        "Ch 10: The Friends You Choose"),
    ("chapter-11.html",        "Ch 11: Honor Your Father and Mother"),
    ("chapter-12.html",        "Ch 12: Work Like It Matters"),
    ("chapter-13.html",        "Ch 13: Money Will Test Your Character"),
    ("chapter-14.html",        "Ch 14: The Church Is Not Optional"),
    ("conclusion.html",        "Conclusion: Your Move"),
    ("scripture-index.html",   "Scripture Index"),
]

# Full chapter titles (for footer-nav labels)
CHAPTER_TITLES = {
    1:  "Your Name Is Your Most Valuable Asset",
    2:  "The Woman in the Mirror Isn&rsquo;t the Whole Story",
    3:  "When Nobody&rsquo;s Watching Becomes When Everybody&rsquo;s Watching",
    4:  "You Were Made On Purpose, For a Purpose",
    5:  "The Relationship You Actually Need Most",
    6:  "The Bible Isn&rsquo;t What You Think It Is",
    7:  "Putting Down the Phone Long Enough to Hear Something True",
    8:  "He Is Somebody&rsquo;s Son",
    9:  "What to Expect from a Young Man Who Fears God",
    10: "The Friends You Choose Will Choose Your Future",
    11: "Honor Your Father and Mother (Even When It&rsquo;s Hard)",
    12: "Work Like It Matters Because It Does",
    13: "Money Will Test Your Character",
    14: "The Church Is Not Optional",
}


def build_dropdown(selected_value: str) -> str:
    """Build the canonical chapter-select <option> block, indented, with one
    `selected` attribute on the row whose value matches `selected_value`."""
    indent = " " * 12  # matches existing files
    lines = []
    for value, label in ROWS:
        sel = " selected" if value == selected_value else ""
        if value == "":
            lines.append(f'{indent}<option value="">{label}</option>')
        else:
            lines.append(f'{indent}<option value="{value}"{sel}>{label}</option>')
    return "\n".join(lines)


# Regex matches the entire <select id="chapter-select"> ... </select> block,
# capturing the opening tag (with handler) so we keep it intact.
SELECT_BLOCK = re.compile(
    r'(<select id="chapter-select"[^>]*>)\s*'
    r'(?:.*?)'
    r'(\s*</select>)',
    re.DOTALL,
)


def rewrite_dropdown(html: str, selected_value: str) -> str:
    new_inner = build_dropdown(selected_value)
    return SELECT_BLOCK.sub(
        lambda m: f"{m.group(1)}\n{new_inner}\n          {m.group(2).lstrip()}",
        html,
        count=1,
    )


def renumber_chapter(path: Path, new_num: int):
    """Renumber a chapter file that was previously chapter (new_num - 1)."""
    old_num = new_num - 1
    html = path.read_text(encoding="utf-8")

    # 1. <title>
    html = html.replace(
        f"CHAPTER {WORD[old_num]}: ",
        f"CHAPTER {WORD[new_num]}: ",
    )
    # 2. canonical URL
    html = html.replace(
        f'href="https://noblemind.study/StrengthAndDignity/chapter-{old_num:02d}.html"',
        f'href="https://noblemind.study/StrengthAndDignity/chapter-{new_num:02d}.html"',
    )
    # 3. chapter-num element
    html = html.replace(
        f'<p class="chapter-num">CHAPTER {WORD[old_num]}</p>',
        f'<p class="chapter-num">CHAPTER {WORD[new_num]}</p>',
    )
    # 4. CH_NUM in script
    html = re.sub(
        r"const CH_NUM = \d+;",
        f"const CH_NUM = {new_num};",
        html,
        count=1,
    )
    # 5. footer-nav prev/next links — rebuild
    prev_num = new_num - 1
    next_num = new_num + 1
    prev_label = CHAPTER_TITLES[prev_num]
    if next_num <= 14:
        next_link = f'<a href="chapter-{next_num:02d}.html">Ch {next_num}: {CHAPTER_TITLES[next_num]} &rarr;</a>'
    else:
        next_link = f'<a href="conclusion.html">Conclusion: Your Move &rarr;</a>'
    new_footer = (
        f'        <div class="footer-nav">\n'
        f'          <a href="chapter-{prev_num:02d}.html">&larr; Ch {prev_num}: {prev_label}</a>\n'
        f'          {next_link}\n'
        f'        </div>'
    )
    html = re.sub(
        r'\s*<div class="footer-nav">.*?</div>',
        "\n" + new_footer,
        html,
        count=1,
        flags=re.DOTALL,
    )
    # 6. dropdown
    html = rewrite_dropdown(html, f"chapter-{new_num:02d}.html")

    path.write_text(html, encoding="utf-8")
    print(f"  renumbered {path.name}: ch{old_num} -> ch{new_num}")


def update_dropdown_only(path: Path, selected_value: str):
    html = path.read_text(encoding="utf-8")
    html = rewrite_dropdown(html, selected_value)
    path.write_text(html, encoding="utf-8")
    print(f"  rebuilt dropdown in {path.name} (selected={selected_value})")


def update_chapter_08_next_nav(path: Path):
    html = path.read_text(encoding="utf-8")
    # Replace the chapter-08 next link target & label
    html = re.sub(
        r'<a href="chapter-09\.html">Ch 9: [^<]*&rarr;</a>',
        '<a href="chapter-09.html">Ch 9: What to Expect from a Young Man Who Fears God &rarr;</a>',
        html,
        count=1,
    )
    path.write_text(html, encoding="utf-8")
    print(f"  updated chapter-08 next-nav -> new Ch 9")


def update_conclusion_prev_nav(path: Path):
    html = path.read_text(encoding="utf-8")
    # Conclusion's prev link points to the last book chapter.
    html = re.sub(
        r'<a href="chapter-13\.html">&larr; Ch 13: [^<]+</a>',
        f'<a href="chapter-14.html">&larr; Ch 14: {CHAPTER_TITLES[14]}</a>',
        html,
        count=1,
    )
    path.write_text(html, encoding="utf-8")
    print(f"  updated conclusion prev-nav -> Ch 14")


def main():
    print("Renumbering renamed chapter files (now 10-14):")
    for new_num in range(10, 15):
        renumber_chapter(ROOT / f"chapter-{new_num:02d}.html", new_num)

    print("\nRebuilding dropdown in remaining files:")
    update_dropdown_only(ROOT / "chapter-08.html", "chapter-08.html")
    update_dropdown_only(ROOT / "introduction.html", "introduction.html")
    update_dropdown_only(ROOT / "conclusion.html", "conclusion.html")
    update_dropdown_only(ROOT / "scripture-index.html", "scripture-index.html")

    print("\nWiring nav around new ch9:")
    update_chapter_08_next_nav(ROOT / "chapter-08.html")
    update_conclusion_prev_nav(ROOT / "conclusion.html")

    print("\nDone.")


if __name__ == "__main__":
    main()
