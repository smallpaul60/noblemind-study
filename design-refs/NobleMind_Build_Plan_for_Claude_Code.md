# NobleMind.Study Build Plan

**For Claude Code execution. Paul approves each milestone before proceeding to the next.**

---

## Ground rules (read first)

1. **Do not invent Scripture.** Every Bible reference must be verified against the actual NASB text before inclusion. No reliance on memory or training defaults.
2. **Do not import post-apostolic vocabulary.** Consult the watchlist in `Bible_Study_Principles_Comprehensive_04-20-2026.md` (in the project files). If a term originated after the apostolic age, flag it rather than use it.
3. **Do not write doctrinal content without Paul's explicit approval.** Scaffolding, structure, metadata, and template work — yes. Substantive Biblical exposition on the test-this-claim pages — no. Leave marked TODOs and escalate.
4. **Every Scripture citation must include book, chapter, and verse.** Hard requirement. No "Paul says" or "the Gospels teach" without the reference.

---

## 0. Discovery

Before any code, inspect the repo and report:

- File structure — static HTML only, or a build system / static-site generator?
- Where does `principles.html` get its content — inline HTML, or loaded from a source file?
- Current state model in `Noble_Mind_Study_Tool_v2.html` — how is the user's working text stored and selected?
- Shared CSS / design tokens — are they centralized or per-page?
- Deployment pipeline — manual upload, Git push, or CI?

Report findings before proceeding to Milestone 1.

---

## 1. Extract Principles to a Canonical Source

Create `/data/principles.md` (or equivalent path that fits the existing structure). Populate verbatim from the current `principles.html`.

Update `principles.html` to load from this file — at runtime via fetch, or at build time if there is a build step. Result: one source of truth for the principles across the site and the tool.

**Acceptance:** editing `/data/principles.md` updates the rendered `principles.html` page and is readable by the tool's prompt-generation code.

---

## 2. Build the "Copy Berean Prompt" Feature

Add to `Noble_Mind_Study_Tool_v2.html` two buttons, clearly labeled, near the current study workspace:

- **Copy Passage Study Prompt** — active when a passage or reference is selected in the tool.
- **Copy Claim Audit Prompt** — accepts a pasted statement to test against Scripture.

**Behavior on click:**

1. Read the user's input (selected passage for button 1, pasted claim for button 2).
2. Build a prompt string using the template below, injecting the principles content from `/data/principles.md` and the user's input.
3. Write the result to the clipboard via the Clipboard API.
4. Show a confirmation: "Prompt copied — paste it into your AI."
5. Include a short hint near the buttons: "Works with ChatGPT, Claude, Gemini, Grok, or any AI chat."

**Passage Study prompt template:**

```
I am studying Scripture using the Noble Mind Study principles (below). Apply these principles to the following passage.

METHOD:
1. State what the passage actually says in plain language before interpreting.
2. Answer the Three Questions: Who is speaking? To whom? Under what circumstances?
3. Identify whether the passage is under the Old Covenant (Law of Moses) or the New Covenant (Law of Christ), and what the New Testament says on the subject.
4. Classify what is present: direct statement of fact, direct command, approved example, or necessary inference.
5. Cross-reference other Scripture on the same subject. Let clear passages illuminate difficult ones.
6. Use the NASB. Cite book, chapter, and verse for every reference.
7. Apply the phrase-testing discipline: do not use post-apostolic vocabulary (Trinity, sacrament, sinner's prayer, rapture, original sin, etc.). Use Scripture's own language.
8. Distinguish "the text explicitly states" from "the text necessarily implies."
9. Say "I don't know" where the text is not clear.

PRINCIPLES:
[full contents of /data/principles.md]

PASSAGE TO EXAMINE:
[user's selected text or reference]
```

**Claim Audit prompt template:** same PRINCIPLES and METHOD blocks, but the final section reads:

```
CLAIM TO EXAMINE AGAINST SCRIPTURE:
[user's pasted claim]

Identify where the claim matches Scripture, where it deviates, where it imports vocabulary or assumptions not in the text, and what passages bear on it. Show your work. Cite every passage by book, chapter, and verse.
```

**Acceptance:** button click on a real passage produces a clipboard-ready prompt that, when pasted into any AI chat, returns a principle-compliant study. Test end-to-end before marking complete.

---

## 3. Build the "Test-This-Claim" Page Template

Create a reusable template for topical study pages at path pattern `/test-this-claim/<slug>.html`.

**Required page structure:**

1. **Question headline** (H1) — the exact question a young seeker types into Google.
2. **One-sentence answer** below the headline, in plain language.
3. **"What does the text actually say?"** — direct Scripture references, quoted from NASB, cited as `Book Ch:vv (NASB)`.
4. **"The Three Questions"** — brief pass (Who is speaking? To whom? Under what circumstances?).
5. **"Cross-references"** — other Scriptures on the same subject, cited.
6. **"Conclusion"** — what the text establishes, what it does not address, what is inference vs. explicit statement.
7. **"Examine this yourself"** — link to the study tool with a pre-loaded prompt for this question, and a link to `/principles.html`.
8. **"Related studies"** — internal links to two or three other test-this-claim pages.

**Required metadata:**

- `<title>` = the exact question
- `<meta name="description">` = the one-sentence answer, under 160 characters
- OpenGraph title / description / image (1200×630)
- Twitter card tags
- Schema.org `QAPage` + `Question` + `AcceptedAnswer` structured data
- Canonical URL
- Mobile-responsive via existing site CSS

**Design notes:** match existing site aesthetic. Reading-width text column. Scripture blocks visually distinct (blockquote-style). Tool link prominent.

**Scaffold one example page:** `/test-this-claim/infant-baptism-in-the-new-testament.html`. Build structure, metadata, and layout. **Leave doctrinal content sections as marked TODOs awaiting Paul's approval.** Do not fill in the body content of sections 3 through 6 — that copy will be supplied or approved by Paul.

**Acceptance:** template renders correctly on desktop and mobile; structured data validates via Google's Rich Results Test; placeholder page exists at the path above with TODOs clearly marked.

---

## 4. Rework the Landing Page

Revise `index.html` to lead with demonstration, not description.

**New above-the-fold structure:**

1. Site title and the Acts 17:11 quote — keep as anchor.
2. One-sentence tagline: *"Study the Bible like it means what it says."*
3. A **Method Demo** block — pick one concrete question from the test-this-claim library (once the first page is approved), show three or four compressed steps of the method applied to it, with Scripture references. End with "See the full study →" linking to the corresponding page.
4. A primary CTA: "Bring your own question →" linking to the tool.

**Below the fold (simplified from current):**

- Short features list (kept but trimmed).
- Links to Principles, Study Tool, User Guide, Books.
- Psalm 119:105 footer quote — keep.

**Remove:** the generic "helps you create, organize, and study Bible lessons" phrasing. Replace with demonstration-forward copy.

**SEO metadata:** rewrite `<title>` and `<meta description>` to lead with the method rather than the tool category. Add OpenGraph and Twitter card tags for shareable previews.

**Acceptance:** a first-time visitor sees the method in action within ten seconds of landing. Mobile-friendly test passes. Structured data validates.

---

## 5. Content Rollout Queue

After the template is approved, queue the following test-this-claim pages. Each matches real search intent from young seekers testing inherited practices. Paul approves topic order and either supplies or approves the doctrinal content for each. Claude Code handles publication, linking, sitemap updates, and social previews.

Suggested first six:

1. Is infant baptism in the New Testament?
2. What does "saint" mean in the New Testament?
3. Does the New Testament authorize instrumental music in worship?
4. Is the "sinner's prayer" in the Bible?
5. What does the Bible say about baptism — sprinkling, pouring, or immersion?
6. Does the Bible teach inherited guilt (so-called "original sin")?

---

## 6. Technical Housekeeping

- Generate `/sitemap.xml` including all new pages and existing pages.
- Add or update `robots.txt` to allow all legitimate crawlers.
- Verify every new page: canonical URL, valid OpenGraph and Twitter tags, valid structured data.
- Run Lighthouse on the landing page and two test-this-claim pages. Target 95+ on Performance, Accessibility, Best Practices, and SEO. Report scores.

---

## Execution order

Milestone 0 (Discovery) → 1 (Principles source) → 2 (Berean Prompt button) → 3 (Template + one scaffolded page) → Paul approves and supplies content for the first test-this-claim page → 4 (Landing page rework, now able to demonstrate from a live page) → 5 (Content rollout) → 6 (Housekeeping, which can overlap with 5).

Milestones 2 and 3 are independent and can run in parallel if helpful.

---

*Build plan prepared in conjunction with Paul Hainline for NobleMind.Study. Apply the principles document strictly throughout.*
