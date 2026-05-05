# Claude Code Build Handoff: *A Good Name* — Update Cycle

**Project:** *Your Name Means Everything: A Good Name* (young men's book)
**Author:** Paul Hainline / NobleMind Press
**What this handoff covers:** Integration of corrected Chapter 6, insertion of new Chapter 9, renumbering of all subsequent chapters, cross-reference patches, ToC update, Scripture Index update, and rebuild of all downstream artifacts (interior PDF, online HTML, sw.js, cover spine).

---

## 1. Source Files in the Project

All source files live in the *A Good Name* Claude Project:

| File | Status | Action |
|------|--------|--------|
| `YourNameMeansEverything_Chapter1.docx` | Unchanged | Use as-is |
| `YourNameMeansEverything_Chapters1-2.docx` | Unchanged | Use as-is |
| `YourNameMeansEverything_Chapter2.docx` | Unchanged | Use as-is |
| `YourNameMeansEverything_Chapter3.docx` | Unchanged | Use as-is |
| `YourNameMeansEverything_Chapter4.docx` | Unchanged | Use as-is |
| `YourNameMeansEverything_Chapter5.docx` | Unchanged | Use as-is |
| **`YourNameMeansEverything_Chapter6.docx`** | **Corrected** | **Replace previous Ch 6 with this corrected version. No renumbering, no title change — same chapter slot, updated content.** |
| `YourNameMeansEverything_Chapter7.docx` | Unchanged | Use as-is |
| `YourNameMeansEverything_Chapter8.docx` | Unchanged | Use as-is |
| **`AGoodName_Chapter9.docx`** *(NEW — separate upload)* | **New** | **Insert as Chapter 9. Title: "What to Expect from a Young Woman Who Fears God."** |
| `YourNameMeansEverything_Chapter9.docx` | Renumbered | Becomes **Chapter 10** ("The Friends You Choose") |
| `YourNameMeansEverything_Chapter10.docx` | Renumbered + patched | Becomes **Chapter 11** ("Honor Your Father and Mother"). See §4 for required text patches. |
| `YourNameMeansEverything_Chapter11.docx` | Renumbered | Becomes **Chapter 12** ("Work Like It Matters Because It Does") |
| `YourNameMeansEverything_Chapter12.docx` | Renumbered | Becomes **Chapter 13** ("Money Will Test Your Character") |
| `YourNameMeansEverything_Chapter13.docx` | Renumbered | Becomes **Chapter 14** ("The Church Is Not Optional") |
| `YourNameMeansEverything_Conclusion.docx` | Patched | See §4 for required text patch. |

---

## 2. Renumbering Map

Apply in **reverse order** to avoid clobbering:

| Old Chapter | New Chapter | Title |
|-------------|-------------|-------|
| 13 | **14** | The Church Is Not Optional |
| 12 | **13** | Money Will Test Your Character |
| 11 | **12** | Work Like It Matters Because It Does |
| 10 | **11** | Honor Your Father and Mother |
| 9 | **10** | The Friends You Choose |
| — | **9 (NEW)** | What to Expect from a Young Woman Who Fears God |
| 8 | 8 (unchanged) | She Is Somebody's Daughter |

Every chapter heading inside each renumbered file must be updated (e.g., "CHAPTER NINE" → "CHAPTER TEN" in the file that becomes Ch 10, and so on through Ch 14). The internal Roman-/word-form chapter numbers in headings must match the new numbering.

---

## 3. New Part Structure

| Part | Chapters |
|------|----------|
| Part One: Who You Are | 1–4 |
| Part Two: Who God Is | 5–7 |
| **Part Three: How You Treat People** | **8–11** *(was 8–10)* |
| Part Four: How You Build a Life | 12–14 *(was 11–13)* |

Part Three now has four chapters instead of three. Part Four chapter numbers shift accordingly.

---

## 4. Required Text Patches (Cross-References & Recaps)

Three files need text-level edits beyond simple renumbering. Each is a small, surgical insert/replace.

### 4.1 Chapter 11 (formerly Chapter 10) — "Honor Your Father and Mother"

**File:** the file currently named `YourNameMeansEverything_Chapter10.docx`, now Chapter 11.

**Patch A — Internal cross-reference (Daniel section)**

In the section near the end titled **"What Honor Builds in a Man"**, find this paragraph:

> "We talked in Chapter 2 about integrity --- being the same man in every room. We talked in **Chapter 9** about the friends who shape your future. But before your friends shaped you, your parents shaped you."

Replace **"Chapter 9"** with **"Chapter 10"**. (The friends chapter has shifted from 9 to 10.)

**Patch B — Part Three opening recap (in "The Hardest and Best Decision" section)**

Find this paragraph:

> "This chapter sits at the close of Part Three of this book --- the section about how you treat people. We have talked about how you treat the young women in your life. We have talked about how you choose your friends. And now we have talked about how you treat the people who were there first..."

**Insert** one sentence after *"We have talked about how you treat the young women in your life."* The new full paragraph reads:

> "This chapter sits at the close of Part Three of this book --- the section about how you treat people. We have talked about how you treat the young women in your life. **We have talked about what to look for in a young woman who fears God.** We have talked about how you choose your friends. And now we have talked about how you treat the people who were there first..."

**Patch C — Part Three climax (a few paragraphs later, same section)**

Find this paragraph:

> "This is where Part Three has been leading. How you treat the young woman in your life reveals what you think about the image of God. How you choose your friends reveals what you value. And how you honor your parents reveals whether you trust the God who told you to."

**Insert** one sentence as the new second beat (between the "treat the young woman" line and the "choose your friends" line). The new full paragraph reads:

> "This is where Part Three has been leading. How you treat the young woman in your life reveals what you think about the image of God. **What you look for in a young woman reveals whether God's standard is your standard.** How you choose your friends reveals what you value. And how you honor your parents reveals whether you trust the God who told you to."

### 4.2 Conclusion — "Your Move"

**File:** `YourNameMeansEverything_Conclusion.docx`

**Patch — Running summary near the top**

Find this paragraph:

> "Everything you have read in these pages --- about your name, your heart, your integrity, your God, your Bible, your attention, how you treat women, how you choose friends, how you honor your parents, how you work, how you handle money, and why the church is not optional --- all of it leads to a single question."

**Insert** the phrase **"what to look for in a young woman who fears God,"** after *"how you treat women,"* and before *"how you choose friends,"*. The new full paragraph reads:

> "Everything you have read in these pages --- about your name, your heart, your integrity, your God, your Bible, your attention, how you treat women, **what to look for in a young woman who fears God,** how you choose friends, how you honor your parents, how you work, how you handle money, and why the church is not optional --- all of it leads to a single question."

### 4.3 No other cross-references should need patching

I scanned every chapter for "Chapter N" type cross-references. The only one that became stale due to renumbering is the Chapter 11 / Daniel passage above (Patch A). If anything else turns up during the build, flag it and pause.

---

## 5. Table of Contents Update

The current ToC reads:

```
Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . 7
PART ONE: Who You Are . . . . . . . . . . . . . . . 15
1. Your Name Is Your Most Valuable Asset . . . 17
2. The Man in the Mirror . . . . . . . . . . . . . . . . 31
3. When Nobody's Watching . . . . . . . . . . . . . 45
4. You Were Made On Purpose . . . . . . . . . . . 61
PART TWO: Who God Is . . . . . . . . . . . . . . . . 75
5. The Relationship You Actually Need Most . . 77
6. The Bible Isn't What You Think It Is . . . . . . 91
7. Putting Down the Phone . . . . . . . . . . . . . 107
PART THREE: How You Treat People . . . . . . 125
8. She Is Somebody's Daughter . . . . . . . . . . 127
9. The Friends You Choose . . . . . . . . . . . . . 143
10. Honor Your Father and Mother . . . . . . . 159
PART FOUR: How You Build a Life . . . . . . . 179
11. Work Like It Matters Because It Does . . . 181
12. Money Will Test Your Character . . . . . . . 201
13. The Church Is Not Optional . . . . . . . . . . 219
Conclusion: Your Move . . . . . . . . . . . . . . . . 237
Scripture Index . . . . . . . . . . . . . . . . . . . . . . 253
```

The new ToC should read (page numbers to be recalculated after final layout — Ch 6 corrections may also shift pagination):

```
Introduction
PART ONE: Who You Are
  1. Your Name Is Your Most Valuable Asset
  2. The Man in the Mirror
  3. When Nobody's Watching
  4. You Were Made On Purpose
PART TWO: Who God Is
  5. The Relationship You Actually Need Most
  6. The Bible Isn't What You Think It Is
  7. Putting Down the Phone
PART THREE: How You Treat People
  8. She Is Somebody's Daughter
  9. What to Expect from a Young Woman Who Fears God   ← NEW
  10. The Friends You Choose
  11. Honor Your Father and Mother
PART FOUR: How You Build a Life
  12. Work Like It Matters Because It Does
  13. Money Will Test Your Character
  14. The Church Is Not Optional
Conclusion: Your Move
Scripture Index
```

After interior layout is complete, regenerate the page numbers from actual page positions and update the ToC entries.

---

## 6. Scripture Index Update

The Scripture Index needs two kinds of updates:

### 6.1 Page-number shifts for existing entries
Every Scripture reference cited in old Chapters 9–13 (now Chapters 10–14) needs its page numbers shifted to the new positions. The Conclusion's Scripture references also shift because Chapter 6's correction may change page count and the new Chapter 9 will push everything in Part Three and Part Four later.

Regenerate the entire Scripture Index from the final laid-out interior PDF rather than trying to patch entry by entry.

### 6.2 New entries from Chapter 9
Add these references, all from the new Chapter 9:

- **Proverbs 31:30** *(quoted twice — opening "The Heart vs. the Surface" and closing scripture block)*
- **Proverbs 31:1**
- **Proverbs 31:10–31** *(For Further Study)*
- **Proverbs 12:4**
- **Proverbs 19:14**
- **Proverbs 7:22–23**
- **Proverbs 7:27**
- **Proverbs 9:13–15**
- **Proverbs 21:9**
- **Proverbs 25:24**
- **1 Peter 3:3–4**
- **1 Peter 3:1–6** *(For Further Study)*
- **Ruth 1:16–17** *(quoted in chapter; also For Further Study)*
- **1 Samuel 1:27–28**
- **1 Samuel 1** *(For Further Study)*
- **Galatians 5:22–23** *(quoted in chapter; also For Further Study)*
- **Luke 6:45**
- **1 Timothy 5:1–2** *(already in index from Ch 8; add the new Ch 9 page reference as an additional locator)*

---

## 7. Build Order

To avoid stepping on the build's own toes, do the work in this order:

1. **Replace Ch 6 source** with the corrected version (no renumbering — same slot).
2. **Apply renumbering in reverse**: Ch 13→14 first, then 12→13, 11→12, 10→11, 9→10. Update each chapter's internal heading text ("CHAPTER NINE" → "CHAPTER TEN" etc.) as part of each rename.
3. **Insert new Chapter 9** (`AGoodName_Chapter9.docx`) into the slot.
4. **Apply text patches** from §4: Chapter 11 (Patches A, B, C) and Conclusion (one phrase insert).
5. **Rebuild interior PDF** with all updated chapters in the correct order.
6. **Recalculate ToC page numbers** from the rebuilt PDF and update the ToC page.
7. **Regenerate Scripture Index** from the rebuilt PDF.
8. **Rebuild final interior PDF** with the updated ToC and Scripture Index pages.
9. **Update online HTML files** at noblemind.study to match: replace Ch 6, insert new Ch 9, renumber files for Ch 10–14, apply the same text patches to Ch 11 and Conclusion HTML, regenerate the online ToC and Scripture Index pages.
10. **Update `sw.js`** (service worker) to include the new Chapter 9 file in the cache list and update any chapter URLs that changed due to renumbering.
11. **Recalculate spine width** based on the new total page count of the rebuilt interior PDF. Update the cover PDF (`YourNameMeansEverything_Cover.pdf`) with the corrected spine width and re-upload to IngramSpark.

---

## 8. Notes & Gotchas

- **No promotional add-ons.** This is a NobleMind Press book — free to read online, distributed in print at cost. Do not enable IngramSpark paid promotional features.
- **NASB throughout.** All Scripture in the new Chapter 9 is NASB. Match the citation style used in existing chapters (em-dash, citation, "(NASB)").
- **Smart quotes and em-dashes.** The new chapter uses curly quotes (`\u201C \u201D \u2018 \u2019`) and em-dashes (`\u2014`) throughout. Preserve them through any HTML conversion.
- **Formatting spec for new Chapter 9** (already applied in `AGoodName_Chapter9.docx`, but confirm on integration): 7920×12240 DXA (5.5×8.5 digest), Georgia, gold `8B7355`, navy `1A1A1A`, blue-gray `2C3E50`, body 24pt half-points, line spacing 360 auto, chapter title 44pt half-points, `SectionType.ODD_PAGE`. Gold rule under chapter header, gray rule above each section header, gold bullets, gold-bordered closing scripture block.
- **Validate after each major step** with `python3 /mnt/skills/public/docx/scripts/office/validate.py <file>`.
- **Working directory pattern:** keep working files in `/home/claude/`; final outputs go to `/mnt/user-data/outputs/` only at the end (the outputs dir clears unpredictably).
- **If anything is unclear or a patch doesn't find its target string exactly,** stop and surface the discrepancy rather than guessing. The text patches in §4 are quoted verbatim from the existing files — if a target string isn't found, something has shifted that needs human review.

---

## 9. Final Deliverables

When the build is complete, hand back:

1. Final `YourNameMeansEverything_Interior.pdf` (rebuilt, paginated, with updated ToC and Scripture Index)
2. Final `YourNameMeansEverything_Cover.pdf` (with recalculated spine width)
3. Updated HTML files for all chapters at noblemind.study
4. Updated online ToC and Scripture Index pages
5. Updated `sw.js` reflecting the new file list
6. A brief build log noting:
   - Final page count
   - Spine width used
   - Any patches that did not find their target verbatim and how they were resolved
   - Any cross-references discovered during the build that this handoff didn't anticipate
