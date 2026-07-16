# Noble Mind Study — Book Preparation & Publication Guide

A comprehensive reference for preparing books from source content through digital publication and Lulu print-on-demand.

---

## Table of Contents

1. [Overview & Workflow](#overview--workflow)
2. [Source Content & Chapter Structure](#source-content--chapter-structure)
3. [HTML Chapter File Conventions](#html-chapter-file-conventions)
4. [Index Page (Table of Contents)](#index-page-table-of-contents)
5. [Regular Downloadable PDF](#regular-downloadable-pdf)
6. [Lulu Interior PDF](#lulu-interior-pdf)
7. [Lulu Cover PDF](#lulu-cover-pdf)
8. [EPUB Generation](#epub-generation)
9. [Service Worker & Deployment](#service-worker--deployment)
10. [Editorial Standards](#editorial-standards)
11. [Font Setup](#font-setup)
12. [Python Dependencies](#python-dependencies)
13. [Quick Reference Commands](#quick-reference-commands)

---

## Overview & Workflow

Each book follows this pipeline:

```
Source Content (DOCX/MD/TXT)
    |
    v
HTML Chapter Files (one per chapter, web-readable)
    |
    v
index.html (table of contents / navigation page)
    |
    +---> Regular PDF (for download from website)
    +---> Lulu Interior PDF (for print-on-demand)
    +---> Lulu Cover PDF (for print-on-demand)
    +---> EPUB (optional, for e-readers)
    +---> Deploy to VPS (rsync + IPFS + IPNS)
```

### Directory Structure

Each book lives in its own directory under the project root:

```
noblemind-study/
  BookName/
    index.html              # Navigation / table of contents page
    foreword.html           # (optional) front matter
    authors-note.html       # (optional) front matter
    chapter-01.html         # Chapter files
    chapter-02.html
    ...
    scripture-index.html    # (optional) back matter
    generate_pdf.py         # Regular PDF generator
    generate_lulu_interior.py   # Lulu interior PDF generator
    generate_cover.py       # Lulu cover PDF generator
    BookName.pdf            # Generated regular PDF
    BookName_Lulu_Interior.pdf  # Generated Lulu interior
    BookName_Cover.pdf      # Generated Lulu cover
    cover-template.pdf      # Lulu's cover template (download from Lulu)
```

---

## Source Content & Chapter Structure

### File Naming Convention

- **Standard chapters:** `chapter-01.html` through `chapter-NN.html` (zero-padded)
- **Front matter:** `foreword.html`, `introduction.html`, `authors-note.html`, `front-matter.html`
- **Back matter:** `conclusion.html`, `scripture-index.html`
- **Appendices:** `appendix-a.html`, `appendix-b.html`, etc.

### Chapter Metadata

Each generator script maintains a `CHAPTER_TITLES` dictionary mapping filenames to metadata:

```python
CHAPTER_TITLES = {
    "foreword.html": ("Foreword", None, None),
    "chapter-01.html": ("Chapter Title Here", "Chapter 1", "Part I: Part Title"),
    "chapter-02.html": ("Another Title", "Chapter 2", "Part I: Part Title"),
    # ...
}
```

Each entry is a tuple: `(title, chapter_number_label, part_subtitle)`
- `title`: The chapter's display title
- `chapter_number_label`: "Chapter N" or `None` for unnumbered sections
- `part_subtitle`: "Part N: Title" or `None` if not in a multi-part structure

---

## HTML Chapter File Conventions

### Content Elements Extracted for PDF

The PDF generators use BeautifulSoup to extract content from the `<div class="content">` element. The following elements are preserved:

| Element | CSS Class | Purpose |
|---------|-----------|---------|
| `<p>` | — | Body paragraphs |
| `<h2>` | — | Section headings |
| `<h3>` | — | Sub-section headings |
| `<blockquote>` | `.scripture` | Scripture quotations |
| `<div>` | `.principle-box` | Key principle callouts |
| `<section>` | `.epigraph` | Opening quotations/epigraphs |
| `<div>` | `.divider` | Section dividers (`* * *`) |
| `<blockquote>` | (plain) | General block quotes |

### Elements Excluded from PDF

These are stripped during extraction (web-only navigation elements):

- `.nav-controls` — Chapter navigation buttons
- `.mark-complete` — Progress tracking buttons
- `.footer-nav` — Footer navigation links

### Content Extraction Function

```python
def extract_content(filepath):
    """Extract the body content from a chapter HTML file."""
    soup = BeautifulSoup(filepath.read_text(encoding="utf-8"), "html.parser")
    content_div = soup.find("div", class_="content")
    if not content_div:
        return ""

    parts = []
    for el in content_div.children:
        if hasattr(el, "name") and el.name:
            # Skip nav controls, mark-complete buttons, footers
            if el.get("class") and any(
                c in el.get("class", [])
                for c in ["nav-controls", "mark-complete", "footer-nav"]
            ):
                continue

            if el.name == "div" and "divider" in el.get("class", []):
                parts.append('<div class="divider">*&emsp;*&emsp;*</div>')
            elif el.name == "blockquote" and "scripture" in el.get("class", []):
                parts.append(str(el))
            elif el.name == "div" and "principle-box" in el.get("class", []):
                parts.append(str(el))
            elif el.name == "section" and "epigraph" in el.get("class", []):
                parts.append(str(el))
            elif el.name in ("p", "h2", "h3", "blockquote"):
                parts.append(str(el))

    return "\n".join(parts)
```

---

## Index Page (Table of Contents)

Each book has an `index.html` with the NobleMind glassmorphism design:

- **Header:** Logo, title (h1), subtitle, author, stats (chapter count)
- **Navigation grid:** Chapter cards with number, title, part designation, hover effects
- **Download links:** PDF/EPUB buttons with file sizes
- **Footer:** Copyright, link back to noblemind.study
- **Color palette:** Varies by book (see theme variables in each book's CSS)
- **Analytics:** `<script src="/nm-core.js" defer></script>` in all pages

---

## Regular Downloadable PDF

**Tool:** WeasyPrint (Python)
**Font:** EB Garamond (all weights: regular, italic, bold, bold-italic)
**Output:** `BookName.pdf`

### Page Specifications

| Property | Value |
|----------|-------|
| Page size | 5.5" x 8.5" (Digest) |
| Top margin | 0.85" |
| Side margins | 0.75" (equal both sides) |
| Bottom margin | 0.9" |
| Body font size | 11pt |
| Line height | 1.55 |
| Text alignment | Justified |
| Text indent | 0.3" (first line of paragraphs) |
| Orphans/widows | 2 lines minimum |

### Page Numbering

- Arabic numerals, centered at bottom (`@bottom-center`)
- Font: EB Garamond, 9.5pt, color #333
- **No numbers on:** Title page (`:first`), copyright page, TOC page

### Front Matter Structure

1. **Title Page** (page 1)
   - `padding-top: 1.8in` (prevents overflow to page 2)
   - Title: 26pt bold, centered
   - Subtitle lines: 13pt, color #333
   - "Based on" attribution: 10pt italic, color #555, `margin-top: 0.5in`
   - Author: 14pt, `margin-top: 0.8in`

2. **Copyright Page** (page 2)
   - `padding-top: 3in` (prevents overflow)
   - 9.5pt, line-height 1.7, color #444, centered
   - Includes: title, copyright, source attribution, Bible version permissions, edition

3. **Table of Contents** (page 3)
   - "Contents" heading: 18pt bold
   - Part headers: 10.5pt bold, margin-top 16pt
   - Chapter entries: 10.5pt, line-height 1.8, indented 0.25" under parts

### Chapter Formatting

- Each chapter starts on a new page (`page-break-before: always`)
- **Chapter header** (centered):
  - Chapter number: 10pt, uppercase, letter-spacing 0.08em, color #555
  - Title: 20pt bold, color #1a1a1a
  - Part subtitle: 10.5pt italic, color #555
- **Section headings (h2):** 13pt bold, margin-top 0.3in, `page-break-after: avoid`
- **First paragraph** after chapter header, h2, divider, scripture, principle-box, or epigraph: no text-indent

### Special Elements

- **Scripture quotes:** Left-aligned italic, 10.5pt, indented 0.4" left, no border
- **Principle boxes:** 10.5pt, indented 0.3" both sides, 2pt solid #666 left border
- **Epigraphs:** Centered italic, 10.5pt, 0.5" margins
- **Dividers:** Centered, `* * *`, color #888, letter-spacing 0.15em

### CSS @font-face Declarations

```css
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Italic'), local('EB Garamond');
    font-weight: normal;
    font-style: italic;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold'), local('EB Garamond');
    font-weight: bold;
    font-style: normal;
}
@font-face {
    font-family: 'EB Garamond';
    src: local('EB Garamond Bold Italic'), local('EB Garamond');
    font-weight: bold;
    font-style: italic;
}
```

---

## Lulu Interior PDF

**Tool:** WeasyPrint (Python)
**Font:** EB Garamond (embedded)
**Output:** `BookName_Lulu_Interior.pdf`

### Key Differences from Regular PDF

The Lulu interior has **alternating gutter margins** for bound pages and **recto chapter starts**.

### Page Specifications

| Property | Value |
|----------|-------|
| Page size | 5.5" x 8.5" (Digest, no bleed) |
| Top margin | 0.75" |
| Bottom margin | 0.75" |
| Gutter (inside) margin | 0.75" |
| Outside margin | 0.625" |
| Body font size | 11pt |
| Line height | 1.55 |

### Alternating Margins (Facing Pages)

```css
/* Recto (right-hand, odd pages): gutter LEFT, outside RIGHT */
@page :right {
    margin-left: 0.75in;   /* gutter */
    margin-right: 0.625in; /* outside */
}

/* Verso (left-hand, even pages): gutter RIGHT, outside LEFT */
@page :left {
    margin-left: 0.625in;  /* outside */
    margin-right: 0.75in;  /* gutter */
}
```

### Chapter Starts on Recto (Right-Hand Pages)

```css
.chapter {
    break-before: right;
}

.toc-section {
    break-before: right;
}
```

This automatically inserts blank verso pages when needed so chapters always begin on odd-numbered (right-hand) pages.

### Page Numbering

- **Recto pages:** Bottom-right (`@bottom-right`)
- **Verso pages:** Bottom-left (`@bottom-left`)
- Font: EB Garamond, 9pt, color #333
- **No numbers on:** Title page, copyright page, TOC pages, blank inserted pages

```css
/* Named pages suppress numbering */
@page title-page {
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page copyright-page {
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

@page toc-page:right {
    @bottom-right { content: none; }
}

@page toc-page:left {
    @bottom-left { content: none; }
}

/* Auto-inserted blank pages */
@page :blank {
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}
```

### Named page assignments

```css
.title-page { page: title-page; }
.copyright-page { page: copyright-page; }
.toc-section { page: toc-page; }
```

### Keep Headings with Text

```css
.chapter-body h2 {
    page-break-after: avoid;
    break-after: avoid;
    orphans: 3;
    widows: 3;
}

blockquote.scripture {
    page-break-inside: avoid;
}

.principle-box {
    page-break-inside: avoid;
}

section.epigraph, .epigraph {
    page-break-inside: avoid;
}

.divider {
    page-break-before: avoid;
}
```

### Lulu Gutter Margin Guidelines

| Page Count | Minimum Gutter |
|------------|----------------|
| 1-60 pages | 0.375" |
| 61-150 pages | 0.625" |
| 151-400 pages | 0.75" |
| 401-600 pages | 0.875" |
| 600+ pages | 1.0" |

We use **0.75"** gutter for all books as it exceeds the minimum for most page counts.

---

## Lulu Cover PDF

**Tool:** ReportLab (Python)
**Font:** EB Garamond (TTF embedded via `pdfmetrics.registerFont`)
**Output:** `BookName_Cover.pdf`

### Getting the Right Dimensions

**Critical:** Lulu calculates cover dimensions based on your uploaded interior. The dimensions change with page count and binding type.

1. Upload your interior PDF to Lulu first
2. Download Lulu's cover template PDF for your specific book
3. Read the exact dimensions from the template
4. Use those dimensions in `generate_cover.py`

### Cover Template Specs (Hardcover with Dust Jacket Flaps)

These values come from Lulu's template. **They vary by page count.**

| Property | Description |
|----------|-------------|
| Total document size | Width x Height (with bleed) |
| Cover panel size | 5.75" x 8.75" (with bleed) — for 5.5x8.5 trim |
| Trim size | 5.5" x 8.5" |
| Spine width | Varies by page count |
| Bleed | 0.25" (top/bottom), 0.125" (sides of cover panels) |
| Safety margin | 0.5" inside trim |
| Flap dimension | 3.25" x 8.5" |
| Flap live area | 2.25" x 7.75" |

### Layout Formula (Left to Right)

```
[FLAP_FOLD] [BACK FLAP 3.25"] [BACK COVER 5.75"] [SPINE] [FRONT COVER 5.75"] [FRONT FLAP 3.25"] [FLAP_FOLD]
```

**Calculating FLAP_FOLD** (the fold margin on each side):

```
FLAP_FOLD = (DOC_W - 2*3.25" - 2*5.75" - SPINE_W) / 2
```

Example for 164-page book:
- DOC_W = 19.438", SPINE_W = 0.688"
- FLAP_FOLD = (19.438 - 6.5 - 11.5 - 0.688) / 2 = 0.375"

**Important:** The calculated FLAP_FOLD may need fine-tuning by ~0.0625" based on Lulu's preview. Start with the calculated value and adjust based on the visual preview.

### Zone Boundaries (Code Pattern)

```python
from reportlab.lib.pagesizes import inch

# Get these from Lulu's template for your specific book
DOC_W = 19.438 * inch   # Total document width
DOC_H = 9.25 * inch     # Total document height
SPINE_W = 0.688          # Spine width in inches

# Calculate flap fold (may need +-0.0625" fine-tuning)
FLAP_FOLD = ((19.438 - 2*3.25 - 2*5.75 - SPINE_W) / 2) * inch

# Zone boundaries from left edge
BACK_FLAP_LEFT = FLAP_FOLD
BACK_FLAP_RIGHT = FLAP_FOLD + 3.25 * inch

BACK_COVER_LEFT = BACK_FLAP_RIGHT
BACK_COVER_RIGHT = BACK_COVER_LEFT + 5.75 * inch

SPINE_LEFT = BACK_COVER_RIGHT
SPINE_RIGHT = SPINE_LEFT + SPINE_W * inch
SPINE_CENTER_X = (SPINE_LEFT + SPINE_RIGHT) / 2

FRONT_COVER_LEFT = SPINE_RIGHT
FRONT_COVER_RIGHT = FRONT_COVER_LEFT + 5.75 * inch

FRONT_FLAP_LEFT = FRONT_COVER_RIGHT
FRONT_FLAP_RIGHT = FRONT_FLAP_LEFT + 3.25 * inch

# Trim edges (0.125" inside bleed on each side of cover panels)
COVER_BLEED = 0.125 * inch
FRONT_TRIM_LEFT = FRONT_COVER_LEFT + COVER_BLEED
FRONT_TRIM_RIGHT = FRONT_COVER_RIGHT - COVER_BLEED
FRONT_CENTER_X = (FRONT_TRIM_LEFT + FRONT_TRIM_RIGHT) / 2

BACK_TRIM_LEFT = BACK_COVER_LEFT + COVER_BLEED
BACK_TRIM_RIGHT = BACK_COVER_RIGHT - COVER_BLEED
BACK_CENTER_X = (BACK_TRIM_LEFT + BACK_TRIM_RIGHT) / 2

# Vertical
V_BLEED = 0.25 * inch
TRIM_TOP = DOC_H - V_BLEED
TRIM_BOTTOM = V_BLEED
COVER_CENTER_Y = (TRIM_TOP + TRIM_BOTTOM) / 2

# Safety: keep text 0.5" inside trim
SAFETY = 0.5 * inch
```

### Design Pattern (Navy + Gold)

```python
from reportlab.lib.colors import Color

NAVY = Color(0.035, 0.082, 0.145)    # #091528 deep navy
GOLD = Color(0.769, 0.663, 0.306)    # #C4A94E warm gold
```

### Front Cover Text Positioning

Position text relative to `FRONT_CENTER_X` (horizontal) and `DOC_H` (vertical, measured from top):

```python
cx = FRONT_CENTER_X

# Title (two lines)
c.setFont("EBGaramond", 26)
c.drawCentredString(cx, DOC_H - 2.8 * inch, "TITLE LINE 1")
c.drawCentredString(cx, DOC_H - 3.25 * inch, "TITLE LINE 2")

# Subtitle
c.setFont("EBGaramond-Italic", 15)
c.drawCentredString(cx, DOC_H - 4.0 * inch, "Subtitle line 1")
c.drawCentredString(cx, DOC_H - 4.35 * inch, "Subtitle line 2")

# Author
c.setFont("EBGaramond", 17)
c.drawCentredString(cx, DOC_H - 5.6 * inch, "Author Name")
```

### Spine Text

Spine text reads top-to-bottom (270-degree rotation):

```python
c.saveState()
c.translate(SPINE_CENTER_X, COVER_CENTER_Y)
c.rotate(270)
c.setFont("EBGaramond", 11)
c.drawCentredString(0, 0, "BOOK TITLE IN ALL CAPS")
c.restoreState()
```

### Back Cover Text

Center text on `BACK_CENTER_X`. Use safety margins for blurb text:

```python
cx = BACK_CENTER_X
safe_left = BACK_TRIM_LEFT + SAFETY
safe_right = BACK_TRIM_RIGHT - SAFETY

# Back cover blurb as list of (font, size, text) tuples
# Use (None, 0, "") for paragraph spacers
lines = [
    ("EBGaramond", 11, "Opening hook line..."),
    (None, 0, ""),  # spacer
    ("EBGaramond", 10.5, "Body text paragraph..."),
]

y = DOC_H - 2.2 * inch
line_spacing = 16

for font, size, text in lines:
    if font is None:
        y -= line_spacing * 0.8
        continue
    c.setFont(font, size)
    c.drawCentredString(cx, y, text)
    y -= line_spacing

# Attribution at bottom
c.setFont("EBGaramond-Italic", 10)
c.drawCentredString(cx, TRIM_BOTTOM + 1.2 * inch, "Attribution text")
```

### Font Registration (ReportLab)

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = Path.home() / ".local/share/fonts"
pdfmetrics.registerFont(TTFont("EBGaramond", str(FONT_DIR / "EBGaramond.ttf")))
pdfmetrics.registerFont(TTFont("EBGaramond-Italic", str(FONT_DIR / "EBGaramond-Italic.ttf")))
```

---

## EPUB Generation

EPUBs have been generated for some books (BridgeMoments, ThroughTheValley). The process typically involves:

1. Extracting content from HTML chapter files (same extraction as PDF)
2. Building EPUB structure with metadata, TOC, and chapter XHTML files
3. Packaging as .epub (ZIP with specific structure)

---

## Service Worker & Deployment

### Adding a New Book to the Service Worker

When adding a new book, update `sw.js`:

1. **Add all chapter files** to the `CACHE_FILES` array:
   ```javascript
   '/BookName/index.html',
   '/BookName/chapter-01.html',
   '/BookName/chapter-02.html',
   // ... all chapters
   ```

2. **Bump the cache version** to force update:
   ```javascript
   const CACHE_NAME = 'noblemind-study-v80';  // increment
   ```

### Deployment to VPS

```bash
# Deploy website files (from project root)
./deploy.sh

# This runs:
# 1. rsync to VPS (excludes .git, *.py, console/)
# 2. IPFS pin on VPS Kubo node
# 3. IPNS publish
```

### Important: Cache Busting

When updating any cached file (HTML, PDF, etc.), **always bump the `sw.js` cache version**. Otherwise users with the old service worker will keep getting stale content from their cache.

---

## Editorial Standards

### Terminology Rules

- **No denominational titles:** Use "preacher" instead of "pastor" or "reverend". Remove "bishop" from denominational contexts (e.g., "Methodist bishop" becomes "Methodist").
- **No unwarranted inferences:** Don't add descriptors not present in the source text. Example: Luke 8:2-3 says women "were contributing to their support out of their private means" — do not add "wealthy" as an inference.
- **Scripture methodology:** "Scripture Interprets Scripture" (Churches of Christ tradition)
- **Preferred Bible translation:** NASB (New American Standard Bible)
- **Attribution:** Always attribute source material (e.g., "Based on *The Man of Galilee* by Atticus G. Haygood (1889)")

### Checking for Issues

Search all HTML chapter files for denominational terms:

```bash
grep -rni "pastor\|bishop\|reverend\|denomination" BookName/*.html
```

---

## Font Setup

### EB Garamond

The preferred font for all book PDFs. Must be installed locally for WeasyPrint and available as TTF for ReportLab.

**Font location:** `~/.local/share/fonts/`

**Required files:**
- `EBGaramond.ttf` (Regular)
- `EBGaramond-Italic.ttf` (Italic)
- `EBGaramond-Bold.ttf` (Bold) — referenced by WeasyPrint via `local('EB Garamond Bold')`
- `EBGaramond-BoldItalic.ttf` (Bold Italic)

**Install from Google Fonts:**
```bash
mkdir -p ~/.local/share/fonts
# Download EB Garamond from Google Fonts, extract TTFs to above directory
fc-cache -fv
```

---

## Python Dependencies

```bash
pip install weasyprint beautifulsoup4 reportlab
```

| Package | Purpose |
|---------|---------|
| `weasyprint` | HTML-to-PDF rendering (regular + Lulu interior) |
| `beautifulsoup4` | HTML parsing / content extraction |
| `reportlab` | Precise PDF generation (Lulu cover) |

---

## Quick Reference Commands

```bash
# Generate regular downloadable PDF
python3 BookName/generate_pdf.py

# Generate Lulu interior PDF
python3 BookName/generate_lulu_interior.py

# Generate Lulu cover PDF
python3 BookName/generate_cover.py

# Deploy to VPS
./deploy.sh

# Bump service worker cache (edit sw.js, increment version number)
```

### Creating Generator Scripts for a New Book

1. Copy `generate_pdf.py` from an existing book
2. Update `CHAPTERS` list with your chapter filenames
3. Update `CHAPTER_TITLES` dictionary with your metadata
4. Update `OUTPUT` filename
5. Update title page content in `build_full_html()`
6. Update copyright page content
7. Repeat for `generate_lulu_interior.py` and `generate_cover.py`

For the cover script, remember to:
- Upload your interior PDF to Lulu first
- Download Lulu's cover template
- Read exact dimensions from the template
- Calculate `FLAP_FOLD` and fine-tune based on Lulu's preview

---

## Troubleshooting

### Title/Copyright Page Overflow
If content flows to an extra page, reduce `padding-top`:
- Title page: start with 1.8in, reduce if needed
- Copyright page: start with 3in, reduce if needed

### Service Worker Serving Stale Content
Bump the `CACHE_NAME` version in `sw.js`. Users may need to close all tabs and reopen.

### Lulu Cover Text Off-Center
The calculated `FLAP_FOLD` may need adjustment of ~0.0625" (1/16"). Upload to Lulu, check the preview with guides turned on, and adjust if text appears shifted left or right.

### Lulu Rejects Cover Dimensions
Lulu recalculates required dimensions each time you update the interior. Always re-download the cover template after any interior change and update `DOC_W`, `DOC_H`, and spine width accordingly.

### Headings Stranded at Page Bottom
Ensure these CSS rules are in place:
```css
.chapter-body h2 {
    page-break-after: avoid;
    break-after: avoid;
}
```
