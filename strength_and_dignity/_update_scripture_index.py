#!/usr/bin/env python3
"""
One-shot helper to update StrengthAndDignity/scripture-index.html for the
chapter 9 insertion:

  1. Renumber every existing (Ch 9..13) reference to (Ch 10..14).
  2. Insert new entries from the new chapter 9.
  3. Append "Ch 9" to 1 Timothy 5:1-2's existing (Ch 8).
"""

import re
from pathlib import Path

INDEX = Path(__file__).resolve().parents[1] / "StrengthAndDignity" / "scripture-index.html"

# --- Step 1: renumber chapters 9..13 -> 10..14 inside (Ch ...) ----------------

# Matches the chapter token inside a chapters span. We only ever match
# numbers, so "Ch 1" is safe — \b ensures we don't slide into "Ch 13".
def renumber_token(match):
    n = int(match.group(1))
    if 9 <= n <= 13:
        return f"Ch {n + 1}"
    return match.group(0)

CH_TOKEN = re.compile(r"\bCh (\d+)\b")


def renumber(html: str) -> str:
    # Only operate inside <span class="chapters">(...)</span> spans, just to be safe.
    span_pattern = re.compile(r'(<span class="chapters">)(\(.*?\))(</span>)')
    def fix(m):
        return m.group(1) + CH_TOKEN.sub(renumber_token, m.group(2)) + m.group(3)
    return span_pattern.sub(fix, html)


# --- Step 2: new entries to insert -------------------------------------------

# Each tuple: (book heading text, list of (ref, chapters) to insert).
# Insertion is ordered: we'll merge with existing entries and re-sort by
# starting verse where possible, but for a one-time insert we just place the
# new <li> in the right spot manually.

LI = '          <li><span class="ref">{ref}</span><span class="chapters">({chs})</span></li>'

INSERTS = {
    "Genesis": [
        # New Genesis 29 entries — go after Genesis 3:17-18
        ("Genesis 29:15&ndash;20", "Ch 9"),
        ("Genesis 29:20",          "Ch 9"),
    ],
    "Ruth": [
        # Existing Ruth section already has Ruth 1:16-17, Ruth 4:13-17, Ruth 4:15.
        # We need to merge Ch 9 into Ruth 1:16-17 (it'll already have been
        # renumbered if it had Ch 9 -> Ch 10 ... but it currently is Ch 1, Ch 9
        # which becomes Ch 1, Ch 10 after renumber — that's a regression because
        # the OLD Ch 9 reference (Friends) WAS legitimately referenced there.
        # We'll handle Ruth 1:16-17 manually below — it should keep "Ch 1, Ch 10"
        # and ALSO get a new "Ch 9" added — wait no, the OLD Ch 9 reference was
        # to Ruth 1:16-17 from the FRIENDS chapter. The Friends chapter is now
        # Ch 10, so renumbering "Ch 1, Ch 9" -> "Ch 1, Ch 10" is correct.
        # The new Chapter 9 (What to Expect) ALSO references Ruth 1 implicitly
        # but doesn't quote it — we only need to add Ruth 2:8, 2:9, 2:14-16, 3:11.
        ("Ruth 2:8",         "Ch 9"),
        ("Ruth 2:9",         "Ch 9"),
        ("Ruth 2:14&ndash;16", "Ch 9"),
        ("Ruth 3:11",        "Ch 9"),
    ],
    # New 2 Samuel section needed — insert between 1 Samuel and 1 Kings.
    "2 Samuel": [
        ("2 Samuel 13:1&ndash;22",   "Ch 9"),
        ("2 Samuel 13:12&ndash;13",  "Ch 9"),
    ],
    "Galatians": [
        # Galatians 5:22-23 — goes between any Gal 3 and Gal 6 entries
        ("Galatians 5:22&ndash;23", "Ch 9"),
    ],
    "Ephesians": [
        # 5:25-29 goes between 5:25 and 6:1-3
        ("Ephesians 5:25&ndash;29", "Ch 9"),
    ],
    # New 1 Thessalonians section — insert before 2 Thessalonians.
    "1 Thessalonians": [
        ("1 Thessalonians 4:3&ndash;7", "Ch 9"),
    ],
    "2 Timothy": [
        # 2:22 goes before 3:14-17
        ("2 Timothy 2:22", "Ch 9"),
    ],
    "1 Peter": [
        # 3:7 goes between 3:3-4 and (no later entries currently)
        ("1 Peter 3:7", "Ch 9"),
    ],
}


def insert_into_section(html: str, section: str, new_li_html: str, anchor_ref: str = None,
                         anchor_position: str = "after") -> str:
    """Insert new_li_html into the <ul class="scripture-list"> following the
    <h2>section</h2>, at a specific anchor (after/before the <li> matching
    anchor_ref). If anchor_ref is None, append before </ul>."""
    # Find the section's UL block
    section_pattern = re.compile(
        rf'(<h2>{re.escape(section)}</h2>\s*<ul class="scripture-list">)(.*?)(</ul>)',
        re.DOTALL,
    )
    m = section_pattern.search(html)
    if not m:
        raise ValueError(f"section not found: {section}")
    head, body, tail = m.group(1), m.group(2), m.group(3)
    if anchor_ref is None:
        new_body = body.rstrip() + "\n" + new_li_html + "\n        "
    else:
        anchor_pat = re.compile(
            rf'(\s*<li><span class="ref">{re.escape(anchor_ref)}</span>[^<]*<span class="chapters">[^<]*</span></li>)'
        )
        am = anchor_pat.search(body)
        if not am:
            raise ValueError(f"anchor not found in {section}: {anchor_ref}")
        anchor_html = am.group(0)
        if anchor_position == "after":
            insertion = anchor_html + "\n" + new_li_html
        else:
            insertion = new_li_html + "\n" + anchor_html.lstrip("\n")
        new_body = body.replace(anchor_html, insertion, 1)
    return html.replace(m.group(0), head + new_body + tail, 1)


def add_new_section_before(html: str, before_section: str, new_section_html: str) -> str:
    """Insert a new <h2>...</h2><ul>...</ul> block above an existing one."""
    pattern = re.compile(rf'(<h2>{re.escape(before_section)}</h2>)')
    m = pattern.search(html)
    if not m:
        raise ValueError(f"before-section not found: {before_section}")
    return html.replace(m.group(1), new_section_html + "\n        " + m.group(1), 1)


def main():
    html = INDEX.read_text(encoding="utf-8")

    # Step 1: renumber.
    html = renumber(html)

    # Step 2a: Genesis — add 29:15-20 and 29:20 after Genesis 3:17-18.
    html = insert_into_section(
        html, "Genesis",
        LI.format(ref="Genesis 29:15&ndash;20", chs="Ch 9"),
        anchor_ref="Genesis 3:17&ndash;18",
        anchor_position="after",
    )
    html = insert_into_section(
        html, "Genesis",
        LI.format(ref="Genesis 29:20", chs="Ch 9"),
        anchor_ref="Genesis 29:15&ndash;20",
        anchor_position="after",
    )

    # Step 2b: Ruth — add 2:8, 2:9, 2:14-16, 3:11 (in that order) after 1:16-17.
    html = insert_into_section(html, "Ruth",
        LI.format(ref="Ruth 2:8", chs="Ch 9"),
        anchor_ref="Ruth 1:16&ndash;17", anchor_position="after")
    html = insert_into_section(html, "Ruth",
        LI.format(ref="Ruth 2:9", chs="Ch 9"),
        anchor_ref="Ruth 2:8", anchor_position="after")
    html = insert_into_section(html, "Ruth",
        LI.format(ref="Ruth 2:14&ndash;16", chs="Ch 9"),
        anchor_ref="Ruth 2:9", anchor_position="after")
    html = insert_into_section(html, "Ruth",
        LI.format(ref="Ruth 3:11", chs="Ch 9"),
        anchor_ref="Ruth 2:14&ndash;16", anchor_position="after")

    # Step 2c: 2 Samuel — new section, insert before 1 Kings.
    new_2sam = (
        '<h2>2 Samuel</h2>\n'
        '        <ul class="scripture-list">\n'
        f'{LI.format(ref="2 Samuel 13:1&ndash;22", chs="Ch 9")}\n'
        f'{LI.format(ref="2 Samuel 13:12&ndash;13", chs="Ch 9")}\n'
        '        </ul>'
    )
    html = add_new_section_before(html, "1 Kings", new_2sam)

    # Step 2d: Galatians — insert 5:22-23 between 3:28 and 6:7-10.
    html = insert_into_section(html, "Galatians",
        LI.format(ref="Galatians 5:22&ndash;23", chs="Ch 9"),
        anchor_ref="Galatians 3:28", anchor_position="after")

    # Step 2e: Ephesians — insert 5:25-29 between 5:25 (now Ch 14) and 6:1-3.
    html = insert_into_section(html, "Ephesians",
        LI.format(ref="Ephesians 5:25&ndash;29", chs="Ch 9"),
        anchor_ref="Ephesians 5:25", anchor_position="after")

    # Step 2f: 1 Thessalonians — new section, insert before 2 Thessalonians.
    new_1thess = (
        '<h2>1 Thessalonians</h2>\n'
        '        <ul class="scripture-list">\n'
        f'{LI.format(ref="1 Thessalonians 4:3&ndash;7", chs="Ch 9")}\n'
        '        </ul>'
    )
    html = add_new_section_before(html, "2 Thessalonians", new_1thess)

    # Step 2g: 1 Timothy 5:1-2 — append Ch 9 to existing Ch 8.
    html = html.replace(
        '<li><span class="ref">1 Timothy 5:1&ndash;2</span><span class="chapters">(Ch 8)</span></li>',
        '<li><span class="ref">1 Timothy 5:1&ndash;2</span><span class="chapters">(Ch 8, Ch 9)</span></li>',
    )

    # Step 2h: 2 Timothy 2:22 — insert before 3:14-17.
    html = insert_into_section(html, "2 Timothy",
        LI.format(ref="2 Timothy 2:22", chs="Ch 9"),
        anchor_ref="2 Timothy 3:14&ndash;17", anchor_position="before")

    # Step 2i: 1 Peter 3:7 — insert after 3:3-4.
    html = insert_into_section(html, "1 Peter",
        LI.format(ref="1 Peter 3:7", chs="Ch 9"),
        anchor_ref="1 Peter 3:3&ndash;4", anchor_position="after")

    INDEX.write_text(html, encoding="utf-8")
    print("scripture-index.html updated.")


if __name__ == "__main__":
    main()
