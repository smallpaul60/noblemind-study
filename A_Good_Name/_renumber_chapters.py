#!/usr/bin/env python3
"""
Update internal references inside the renamed chapter files.

After `git mv` shifted old Ch 9-13 to new Ch 10-14, each renamed file
still carries its old chapter number in:
  - <title>CHAPTER NINE: ...</title>
  - <link rel="canonical" href=".../chapter-09.html">
  - <p class="chapter-num">CHAPTER NINE</p>
  - footer-nav prev/next links
  - <select> dropdown (will be rebuilt across ALL chapters in a later
    pass; here we just bump the `selected` option)
  - const CH_NUM = 9;

This script patches each of those, one renamed chapter at a time.
The non-renamed chapters (1-8) and the new Ch 9 are not touched here.

The dropdown is replaced with the FINAL state — same as the new ch9 —
so all 14 chapters end up with a consistent dropdown.
"""

import re
from pathlib import Path

BOOK_DIR = Path(__file__).parent

# old number -> (new number, new word, new title, prev_href_label, next_href_label)
# new word = "TEN", "ELEVEN", etc.
RENUMBERED = {
    10: ("TEN",      "The Friends You Choose Will Choose Your Future",   ("chapter-09.html", "Ch 9: What to Expect from a Young Woman Who Fears God"),  ("chapter-11.html", "Ch 11: Honor Your Father and Mother")),
    11: ("ELEVEN",   "Honor Your Father and Mother (Even When It’s Hard)", ("chapter-10.html", "Ch 10: The Friends You Choose"),                       ("chapter-12.html", "Ch 12: Work Like It Matters")),
    12: ("TWELVE",   "Work Like It Matters Because It Does",              ("chapter-11.html", "Ch 11: Honor Your Father and Mother"),                ("chapter-13.html", "Ch 13: Money Will Test Your Character")),
    13: ("THIRTEEN", "Money Will Test Your Character",                    ("chapter-12.html", "Ch 12: Work Like It Matters"),                        ("chapter-14.html", "Ch 14: The Church Is Not Optional")),
    14: ("FOURTEEN", "The Church Is Not Optional",                        ("chapter-13.html", "Ch 13: Money Will Test Your Character"),             None),
}

OLD_WORDS = {10:"NINE", 11:"TEN", 12:"ELEVEN", 13:"TWELVE", 14:"THIRTEEN"}

# Final dropdown — identical across every chapter file. The `selected`
# option is set per chapter via str.replace below.
DROPDOWN_OPTIONS = [
    ("",                       "Jump to..."),
    ("introduction.html",      "Introduction"),
    ("chapter-01.html",        "Ch 1: Your Name Is Your Most Valuable Asset"),
    ("chapter-02.html",        "Ch 2: The Man in the Mirror"),
    ("chapter-03.html",        "Ch 3: When Nobody's Watching"),
    ("chapter-04.html",        "Ch 4: Made On Purpose, For a Purpose"),
    ("chapter-05.html",        "Ch 5: The Relationship You Need Most"),
    ("chapter-06.html",        "Ch 6: The Bible Isn't What You Think"),
    ("chapter-07.html",        "Ch 7: Putting Down the Phone"),
    ("chapter-08.html",        "Ch 8: She Is Somebody's Daughter"),
    ("chapter-09.html",        "Ch 9: What to Expect from a Young Woman Who Fears God"),
    ("chapter-10.html",        "Ch 10: The Friends You Choose"),
    ("chapter-11.html",        "Ch 11: Honor Your Father and Mother"),
    ("chapter-12.html",        "Ch 12: Work Like It Matters"),
    ("chapter-13.html",        "Ch 13: Money Will Test Your Character"),
    ("chapter-14.html",        "Ch 14: The Church Is Not Optional"),
    ("conclusion.html",        "Conclusion: Your Move"),
    ("scripture-index.html",   "Scripture Index"),
]


def build_dropdown(selected_href: str) -> str:
    lines = ['          <select id="chapter-select" onchange="goToChapter(this.value)">']
    for href, label in DROPDOWN_OPTIONS:
        sel = ' selected' if href == selected_href else ''
        if href == "":
            lines.append(f'            <option value="">{label}</option>')
        else:
            lines.append(f'            <option value="{href}"{sel}>{label}</option>')
    lines.append('          </select>')
    return "\n".join(lines)


def patch_chapter(new_num: int):
    new_word, new_title, prev_nav, next_nav = RENUMBERED[new_num]
    old_word = OLD_WORDS[new_num]
    f = BOOK_DIR / f"chapter-{new_num:02d}.html"
    src = f.read_text(encoding="utf-8")

    # 1. <title>
    # Pattern matches the existing CHAPTER OLD_WORD: ... title
    src = re.sub(
        rf"<title>CHAPTER {old_word}: [^<]*</title>",
        f"<title>CHAPTER {new_word}: {new_title} | Your Name Means Everything: A Good Name</title>",
        src,
        count=1,
    )

    # 2. <link rel="canonical">
    old_href = f"https://noblemind.study/A_Good_Name/chapter-{new_num-1:02d}.html"  # old number was new_num - 1
    new_href = f"https://noblemind.study/A_Good_Name/chapter-{new_num:02d}.html"
    src = src.replace(f'href="{old_href}"', f'href="{new_href}"', 1)

    # 3. chapter-num
    src = re.sub(
        r'<p class="chapter-num">CHAPTER ' + old_word + r'</p>',
        f'<p class="chapter-num">CHAPTER {new_word}</p>',
        src,
        count=1,
    )

    # 4. CH_NUM constant
    src = re.sub(
        rf"const CH_NUM = {new_num - 1};",
        f"const CH_NUM = {new_num};",
        src,
        count=1,
    )

    # 5. Dropdown — replace the entire <select>...</select> with the final
    src = re.sub(
        r'\s*<select id="chapter-select".*?</select>',
        "\n" + build_dropdown(f"chapter-{new_num:02d}.html"),
        src,
        count=1,
        flags=re.DOTALL,
    )

    # 6. Footer-nav
    if next_nav is None:
        # Last chapter — next is conclusion
        next_block = '<a href="conclusion.html">Conclusion: Your Move &rarr;</a>'
    else:
        next_href, next_label = next_nav
        next_block = f'<a href="{next_href}">{next_label} &rarr;</a>'
    prev_href, prev_label = prev_nav
    nav_block = (
        '<div class="footer-nav">\n'
        f'          <a href="{prev_href}">&larr; {prev_label}</a>\n'
        f'          {next_block}\n'
        '        </div>'
    )
    src = re.sub(
        r'<div class="footer-nav">.*?</div>',
        nav_block,
        src,
        count=1,
        flags=re.DOTALL,
    )

    f.write_text(src, encoding="utf-8")
    print(f"Patched {f.name}: CHAPTER {old_word} -> CHAPTER {new_word}, CH_NUM={new_num}")


def patch_unrenumbered_dropdowns():
    """Update dropdown across chapters 1-8 + intro + conclusion + scripture-index
    so every page sees the new 14-chapter list with the right `selected` row."""
    pages = [
        ("introduction.html",     "introduction.html"),
        ("chapter-01.html",       "chapter-01.html"),
        ("chapter-02.html",       "chapter-02.html"),
        ("chapter-03.html",       "chapter-03.html"),
        ("chapter-04.html",       "chapter-04.html"),
        ("chapter-05.html",       "chapter-05.html"),
        ("chapter-06.html",       "chapter-06.html"),
        ("chapter-07.html",       "chapter-07.html"),
        ("chapter-08.html",       "chapter-08.html"),
        ("conclusion.html",       "conclusion.html"),
        ("scripture-index.html",  "scripture-index.html"),
    ]
    for fname, selected in pages:
        f = BOOK_DIR / fname
        if not f.exists():
            print(f"  (skip: {fname} not found)")
            continue
        src = f.read_text(encoding="utf-8")
        new_src = re.sub(
            r'\s*<select id="chapter-select".*?</select>',
            "\n" + build_dropdown(selected),
            src,
            count=1,
            flags=re.DOTALL,
        )
        if new_src != src:
            f.write_text(new_src, encoding="utf-8")
            print(f"  Updated dropdown in {fname}")
        else:
            print(f"  (no dropdown change in {fname})")


def patch_ch08_next_nav():
    """Ch 8 footer-nav previously pointed next to chapter-09.html (Friends).
    With the new Ch 9 ('What to Expect...') taking that slot, the label
    changes."""
    f = BOOK_DIR / "chapter-08.html"
    src = f.read_text(encoding="utf-8")
    src = re.sub(
        r'<div class="footer-nav">.*?</div>',
        '<div class="footer-nav">\n'
        '          <a href="chapter-07.html">&larr; Ch 7: Putting Down the Phone</a>\n'
        '          <a href="chapter-09.html">Ch 9: What to Expect from a Young Woman Who Fears God &rarr;</a>\n'
        '        </div>',
        src,
        count=1,
        flags=re.DOTALL,
    )
    f.write_text(src, encoding="utf-8")
    print("Patched chapter-08.html footer-nav -> next = new Ch 9")


def main():
    for n in (10, 11, 12, 13, 14):
        patch_chapter(n)
    print()
    patch_ch08_next_nav()
    print()
    patch_unrenumbered_dropdowns()


if __name__ == "__main__":
    main()
