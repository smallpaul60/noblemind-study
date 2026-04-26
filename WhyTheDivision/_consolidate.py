#!/usr/bin/env python3
"""One-shot consolidator: merges Preface.md + Chapter_N_*.md into the
canonical why-the-division-book.md with Parts 1-4 structure.

After this script runs once and the canonical file is reviewed, it can
stay in the directory for re-runs (e.g. if a chapter source file is
edited) but it should not be treated as part of the build pipeline.
The build pipeline reads only why-the-division-book.md.
"""

import re
from pathlib import Path

DIR = Path(__file__).parent

TITLE = "Why the Division Among Brethren?"
SUBTITLE = "The Underlying Issue Between Institutional and Non-Institutional churches of Christ"
AUTHOR = "Paul Hainline"

PARTS = [
    ("Part One", "Background", [1, 2]),
    ("Part Two", "The Foundation", [3, 4, 5]),
    ("Part Three", "The Four Questions", [6, 7, 8, 9]),
    ("Part Four", "What It Means", [10, 11]),
]

CHAPTER_FILES = {
    1:  "Chapter_1_Why_This_Matters.md",
    2:  "Chapter_2_A_Short_History_of_the_Division.md",
    3:  "Chapter_3_The_Question_of_Authority.md",
    4:  "Chapter_4_The_Work_God_Gave_the_Church.md",
    5:  "Chapter_5_The_Church_and_the_Individual.md",
    6:  "Chapter_6_Church_Supported_Institutions.md",
    7:  "Chapter_7_The_Sponsoring_Church_Arrangement.md",
    8:  "Chapter_8_The_Treasury_and_Benevolence.md",
    9:  "Chapter_9_Fellowship_Halls_and_Social_Meals.md",
    10: "Chapter_10_Whats_Really_at_Stake.md",
    11: "Chapter_11_For_Further_Study.md",
}

# Canonical chapter titles (the heading we emit in the consolidated file).
# These are reviewed to remove stray subtitle text and to use the same
# wording the TOC will print.
CHAPTER_TITLES = {
    1:  "Why This Matters",
    2:  "A Short History of the Division",
    3:  "The Question of Authority",
    4:  "The Work God Gave the Church",
    5:  "The Church and the Individual",
    6:  "Church-Supported Institutions",
    7:  "The Sponsoring Church Arrangement",
    8:  "The Treasury and Benevolence",
    9:  "Fellowship Halls and Social Meals",
    10: "What's Really at Stake",
    11: "For Further Study",
}

PART_INTROS = {
    "Part One": (
        "The division among brethren did not begin in the 1950s. To "
        "understand the question that came to a head then, the reader "
        "has to begin earlier — and has to ask why the question matters "
        "now."
    ),
    "Part Two": (
        "Before any specific practice can be examined, three foundational "
        "matters have to be settled: how Scripture establishes authority, "
        "what work the local church has been given, and how that "
        "collective work is distinguished from the work of the individual "
        "Christian."
    ),
    "Part Three": (
        "The four chapters of this part take up, one at a time, the four "
        "specific questions on which the institutional and "
        "non-institutional positions divide. Each chapter follows the "
        "same shape: state the question, state both positions at full "
        "strength, walk the Scripture, and let the text carry the "
        "conclusion."
    ),
    "Part Four": (
        "The booklet closes by stepping back from the four specific "
        "questions to ask what is really at stake — and by directing "
        "the reader to the primary sources for further study."
    ),
}


def clean_chapter_body(text: str, num: int) -> str:
    """Strip the chapter source's preamble and trailer, demote H2 subsections
    to H3, and return the body markdown."""
    # Remove the leading H1 chapter heading line.
    text = re.sub(r'\A#\s+Chapter\s+\d+[^\n]*\n', '', text)
    # Remove the *From* booklet subtitle line that appears in each source file.
    text = re.sub(r'\A\s*\*From\*[^\n]*\n', '', text)
    # Remove a leading "---" separator (and surrounding blank lines).
    text = re.sub(r'\A\s*(?:---+\s*\n)+', '', text)
    # Remove the trailing "*— end of Chapter N —*" marker.
    text = re.sub(
        r'\n\s*\*\s*[—–-]\s*end of Chapter\s+\d+\s*[—–-]\s*\*\s*\Z',
        '', text,
    )
    # Remove a trailing "---" separator.
    text = re.sub(r'(?:\n\s*---+\s*)+\s*\Z', '', text)
    # Demote chapter subsections from ## to ###.
    text = re.sub(r'(?m)^##\s+', '### ', text)
    return text.strip()


def clean_preface_body(text: str) -> str:
    """Same idea as clean_chapter_body but for the preface."""
    text = re.sub(r'\A#\s+Preface\s*\n', '', text)
    text = re.sub(r'\A\s*(?:---+\s*\n)+', '', text)
    text = re.sub(r'(?:\n\s*---+\s*)+\s*\Z', '', text)
    text = re.sub(r'(?m)^##\s+', '### ', text)
    return text.strip()


def fix_part_references(body: str) -> str:
    """Chapter 1 originally said 'the chapters that follow in Part 1 lay down
    the hermeneutical foundation' — under the new four-part structure the
    foundation chapters are Part Two, not Part One. Patch the prose."""
    body = body.replace(
        "The chapters that follow in Part 1 lay down the hermeneutical foundation",
        "The chapters that follow in Part Two lay down the hermeneutical foundation",
    )
    body = body.replace("the specific questions in Part 3",
                        "the specific questions in Part Three")
    body = body.replace("Part 3 then takes the four specific questions",
                        "Part Three then takes the four specific questions")
    body = body.replace("Part 4 pulls the threads together",
                        "Part Four pulls the threads together")
    return body


def main():
    out = []

    out.append(f"# {TITLE}\n")
    out.append(f"*{SUBTITLE}*\n")
    out.append("---\n")

    out.append("## Contents\n")
    out.append("**Preface**\n")
    for label, title, ch_nums in PARTS:
        out.append(f"\n**{label.upper()} — {title}**")
        for n in ch_nums:
            out.append(f"- Chapter {n} — {CHAPTER_TITLES[n]}")
    out.append("")
    out.append("---\n")

    # Preface
    preface_text = (DIR / "Preface.md").read_text(encoding="utf-8")
    out.append("## Preface\n")
    out.append(clean_preface_body(preface_text))
    out.append("\n---\n")

    for label, title, ch_nums in PARTS:
        out.append(f"# {label} — {title}\n")
        out.append(PART_INTROS[label])
        out.append("\n---\n")
        for n in ch_nums:
            ch_text = (DIR / CHAPTER_FILES[n]).read_text(encoding="utf-8")
            body = clean_chapter_body(ch_text, n)
            if n == 1:
                body = fix_part_references(body)
            out.append(f"## Chapter {n} — {CHAPTER_TITLES[n]}\n")
            out.append(body)
            out.append("\n---\n")

    canonical = "\n".join(out).rstrip() + "\n"
    target = DIR / "why-the-division-book.md"
    target.write_text(canonical, encoding="utf-8")
    print(f"Wrote {target} ({len(canonical):,} chars, "
          f"{canonical.count(chr(10))} lines)")


if __name__ == "__main__":
    main()
