# Noble Mind Study — Brand Refresh Handoff for Claude Code

## Context

The Noble Mind Study brand is being refreshed. The current site has a heavy emerald-neon aesthetic that reads "tech product" more than "Scripture study." The refreshed direction trades the neon glow for a literary, lamplit feel — dark backgrounds with a single warm gold accent, Cardo serif throughout, mono small-caps for citations.

## Files in this package

- `BRAND_BRIEF.md` — the source of truth. Colors, typography, voice, layout rules. **Read this first.**
- `hero-mockup.html` — standalone reference for the home page hero and method preview row.
- `study-page-mockup.html` — standalone reference for an individual study page (the "infant baptism" example).

The two HTML files are pixel-faithful targets. They use Cardo via `@fontsource` on jsDelivr and inline styles. **Your job is to translate this aesthetic into the actual site codebase** — not to copy these files verbatim, but to refactor the production CSS, components, and templates so that pages built from them look like these references.

---

## Phased plan — do not write production code on the first pass

### Phase 0 — Recon (do this first, do not skip)

Before touching anything:

1. Read the current site structure. Tell me which files define:
   - Global styles (CSS variables, base styles, font loading)
   - The home page hero
   - A study page template
   - Reusable components (Scripture blocks, citations, section headings, the "Answer" block — if any of these are componentized today)
2. Identify every place the current "neon green glow" treatment lives — `box-shadow`, `text-shadow`, neon green hex values, heavy gradients, halos, blurs.
3. Identify the current font stack and how it's loaded.
4. Report back: a short audit document. **No code changes yet.**

### Phase 1 — Design tokens

Once we agree on the audit, the first code change is the design system itself:

1. Define CSS custom properties for the new palette (see `BRAND_BRIEF.md` § Color Palette).
2. Set up the font loading for Cardo (400, 400-italic, 700) via `@fontsource` on jsDelivr or self-hosted equivalents.
3. Define typography utility classes or component styles for: Scripture block, citation, section heading, section number, em-dash list item, answer block.
4. Replace existing neon-green tokens with the new palette where safe. Where it's not (custom components, one-offs), flag for Phase 2.

### Phase 2 — Apply to pages

Refactor the home hero and one study page to match the references. Do this **one page at a time**. After each page:

- Stop.
- Show me a screenshot or describe what changed.
- Wait for sign-off before moving to the next page.

### Phase 3 — Component sweep

Once two pages match the references, go through the remaining pages applying the same component patterns. Flag any page where the design doesn't translate cleanly.

---

## Hard rules

- **No neon glow** anywhere. The brand uses one thin gold hairline (`rgba(212, 162, 76, 0.18)`) at most. If you find yourself adding `box-shadow` for "atmosphere," stop.
- **Reading column max 540px** on study pages. Long lines are forbidden.
- **Scripture quotes always get the gold left rule + italic Cardo treatment.** Never plain block quotes. Never embedded inline in prose without the rule.
- **Citations always go in mono small caps + lamplight gold.** Format: `MATT. 28:19 · NASB`. This is a brand signature — every verse reference, every page.
- **Sentence case in body prose and headings.** ALL CAPS only for the small editorial labels and citations (where small-caps tracking *is* the style).
- **Berean green (`#4FB286`) is reserved.** Use it only for the section markers (`01`, `02`, `03`, `04`) and small editorial kickers like "A Study · No. 14 · Baptism." Never use it as a general accent or link color.
- **Lamplight gold (`#D4A24C`) is the only accent.** Citations, thin rules, the verdict word in the answer block, primary CTAs.

## Voice rules (for any copy generated during the refresh)

- Direct. Short sentences.
- Never twist Scripture to fit a conclusion.
- "I don't know" is a valid answer when the text doesn't say.
- Treat the reader as a sincere student, not a target.

## Working agreement

- **Branch first.** Don't refactor on `main`. Use a `brand/refresh-2026` branch or similar.
- **Commit per phase.** Phase 0 = no commits. Phase 1 = one commit for tokens, one for fonts, one for utility classes. Phase 2 = one commit per page.
- **When stuck, propose options.** If a current page has structural decisions that don't translate (e.g., a layout that depended on green-glow panels for visual hierarchy), don't force it. Stop and propose two or three options with tradeoffs.

---

## First message to Claude Code

When you're ready to begin, paste this:

> I'm refreshing the Noble Mind Study brand. Read `BRAND_BRIEF.md`, `hero-mockup.html`, and `study-page-mockup.html` in this folder — those are the target visual direction.
>
> Start with Phase 0 only: audit the current site structure and report back. Do not write any code yet.
