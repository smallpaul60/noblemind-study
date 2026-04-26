# Hand-off to Claude Code — AI Guidance Note Near the Berean Prompt Buttons

Paul has observed that ChatGPT cuts out mid-response when the principle-loaded prompts reach certain passages (specifically 1 Peter 3:21 in repeated runs on the "is baptism necessary for salvation" question). The block appears to be a content-policy classifier, not a training issue. Claude, Grok, and Gemini have handled the same prompts without refusal.

Users need practical guidance so that when they paste a prompt and an AI declines, they know to try another rather than assume the tool isn't working or give up on the question.

## What to add

In `Noble_Mind_Study_Tool_v2.html`, add a small informational note directly beneath the two Berean Prompt buttons (Copy Passage Study Prompt, Copy Claim Audit Prompt). The note should be visually subtle — smaller text, muted color matching the existing "Works with ChatGPT, Claude, Gemini, Grok, or any AI chat" hint if that hint still exists, or replacing it if it does.

## Exact text

> Works with any AI chat. Based on user observations, Claude, Grok, and Gemini engage most consistently with these principle-loaded prompts. ChatGPT sometimes declines to quote specific passages mid-response — if that happens, try another AI.

## Implementation notes

- Style: small text (roughly 0.85em), muted foreground (same tone as existing helper text on the tool page). Not a warning box, not an alert — just a quiet note.
- Placement: directly below the two buttons, above any other content. The user should see it when they're about to use the buttons, not buried further down.
- Mobile: confirm it reads cleanly at phone width. Wrap as needed; do not let it force horizontal scroll.
- If the existing "Works with ChatGPT, Claude, Gemini, Grok, or any AI chat" line is still in place, replace it with the new note rather than stacking two similar lines.
- No icon. No bolding. No link. Just text.

## What NOT to do

- Do not frame this as a complaint about ChatGPT. The tone is practical guidance, not criticism.
- Do not list ChatGPT as unsupported or incompatible. It works for many questions; it just declines on some.
- Do not add a "recommended AI" ranking or badge. The note is observation, not endorsement.
- Do not expand this into a longer explanation on the tool page. If Paul later wants a fuller write-up about why some AIs refuse, that belongs on a separate FAQ or blog-style page, not in the tool UI.

## Housekeeping

- Bump `sw.js` version.
- No changes to any test-this-claim page, the landing page, or any doctrinal content.
- No other files should be modified.

If anything about the placement or wording feels off once it's in the page, stop and flag it before deploying. Paul will eyeball it and approve.

---

*Small change, clear purpose. The goal is that a user who hits a ChatGPT refusal knows immediately that the fix is to try another AI rather than abandon the question.*
