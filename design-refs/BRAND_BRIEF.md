# Noble Mind Study — Brand Brief

## Positioning

A Scripture-first study tool for people who want to test claims against the text, not against tradition. Built on the Berean principle: receive the word eagerly, then examine the Scriptures to see if it's so.

## Tagline

**Test it against the text.**

*Alternate: Read the Bible like it means what it says.*

## Voice

Direct. Unhurried. Confident without being combative. Treats the reader as a sincere student. Says "I don't know" when the text doesn't answer. Never twists Scripture to fit a conclusion. Short sentences. Active verbs. No filler. Sentence case in body prose; small-caps tracking only for editorial labels and citations.

## Audience

Thinking believers, honest seekers, and anyone who has been told "the Bible says..." and wondered whether it actually does.

## Method (the spine — every study follows this shape)

| Step | Section |
|------|---------|
| 01 | What the text actually says |
| 02 | The pattern Scripture gives |
| 03 | What the text does NOT do |
| 04 | Answer — with citations, in NASB |

## Visual Direction

Mood: a quiet study at night. Lamp on the desk. Open Bible. Not a dashboard. Not a chapel. A workspace for careful reading.

Reduce glow effects to near-zero. One thin gold hairline is enough; the dark itself does the work.

## Color Palette

| Role | Name | Hex |
|------|------|-----|
| Background | Ink | `#0A0E14` |
| Primary text | Parchment | `#F2EBDC` |
| Body text | Muted warm | `#E8E2D2` |
| Accent | Lamplight gold | `#D4A24C` |
| Secondary | Berean green | `#4FB286` |
| Captions/meta | Vellum | `#8A8578` |

**Color usage rules:**

- **Lamplight gold** — citations, thin rules, the verdict word in answers, primary CTAs.
- **Berean green** — section markers (01–04) and editorial kickers only. Never neon. Never used as a general accent.
- **Vellum** — taglines, italic asides, footers.

## Typography

**All serif content: Cardo**
- Wordmark / headlines: Cardo Bold (700)
- Scripture quotes: Cardo Italic (400), parchment color, indented with thin gold left rule
- Body prose: Cardo Regular (400)
- Section headings: Cardo Bold (700), sentence case

**Citations and labels: System monospace**
- Small-caps treatment (uppercase + 0.22em letter-spacing)
- ~10–11px, lamplight gold
- Format: `MATT. 28:19 · NASB`

**Section numerals: Same monospace, in Berean green**
- `01` `02` `03` `04`

## Layout Principles

- Generous margins. The reader is studying, not scrolling.
- Reading column: 680px max on desktop. Clamps to viewport on narrow screens. Past ~740px, study prose starts reading like a blog post.
- Scripture indents and shifts to italic with a thin gold left rule — visually distinct from commentary at all times.
- One accent color per section, not three.
- The crest appears small. The text is the hero.
- Em-dash bullets (`—`) for lists, in lamplight gold.
- The "Answer" block always closes a study: gold left rule, faint gold tint behind text, verdict word in gold.

## What We Are Not

- A devotional app
- A commentary aggregator
- A denominational platform
- A feelings-first experience
- AI explaining the Bible to you. The tool helps you examine it.

## Anchor Verse

Acts 17:11 — the noble-minded Bereans examined the Scriptures daily to see whether these things were so. That's the whole brand. Every study page closes with this verse, in small-caps gold.

## Scripture accuracy

Every Scripture quotation on any NobleMind surface — site, book, mockup, social post — must be cross-checked against the actual NASB text before publishing.

- **Verbatim or paraphrase, never both.** A line is either an exact NASB quote with its citation, or clearly framed as paraphrase / editorial language. There is no middle ground. *"Examine the Scriptures daily to see whether these things are so."* with `Acts 17:11 · NASB` underneath is a violation: the verse uses *examining*, not *Examine*, and *were*, not *are*.
- **The citation format is reserved for verbatim.** The mono small-caps gold citation (`Acts 17:11 · NASB`) marks a direct NASB quote. Paraphrase or commentary takes no citation, or labels itself as paraphrase.
- **Partial quotes are fine** as long as the words quoted are exact NASB text. *"…examining the Scriptures daily to see whether these things were so."* with `Acts 17:11 · NASB` is correct; the words are NASB.

Paraphrase is not Scripture.

## Scope

- **Editorial pages** (`index.html`, `principles.html`, `books.html`, `user-guide.html`, `test-this-claim/*.html`) are reading surfaces. They follow this brief in full — Cardo serif, 540px reading column, lamplight-gold accents, Berean green reserved for section markers.
- **Workspace surface** — `Noble_Mind_Study_Tool_v2.html` is a workspace, not a reading surface. It keeps its sans-serif UI for dense panels and controls. From this brief it inherits only: the Ink background, Lamplight gold for primary buttons and active states, the citation format (mono small-caps + gold) wherever Scripture references appear in output. Berean green is retired as a general accent here too.
- **Books own their accent** — per-book chapter pages (`ThroughTheValley/`, `OneDayCloserToHome/`, etc.) keep their warm per-book accents within the NobleMind palette, the way real book covers do. Only the site chrome around them uses Lamplight gold. Books are out of scope for this refresh.
