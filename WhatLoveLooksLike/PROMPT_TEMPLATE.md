# What Love Looks Like — Locked Prompt Template

Use this template for every one of the 13 panels. The **LOCKED VISUAL LANGUAGE** block at the bottom never changes — it is what makes 13 separate generations read as one installation. Only the **VARIABLE BLOCKS** at the top change per panel.

Reference winner: Gemini's `love-is-patient_gemini.png`. Hold every future panel to that level of polish.

---

## Wardrobe vocabulary (catalog-wide)

Pull each teen's outfit from this palette so the wall looks unified:

- **Warm base**: soft mustard cardigan or sweater · cream / off-white t-shirt or blouse · warm tan or khaki pants
- **Earth accents**: weathered denim · soft chocolate brown jacket · faded olive flannel
- **Deep accent (sparingly, one teen per panel max)**: deep burgundy hoodie · navy blue zip-up · forest green sweater
- **Cool contrast**: muted blue-green ("dusty teal") blouse · pale slate gray tee
- **Avoid**: pure white, pure black, pure red, neon anything, bold logos or graphics, modern athleisure brands

**Modesty (church classroom context)** — the wall hangs in a junior-high / high-school classroom at a church building, so every teen is dressed conservatively:

- Girls: full-coverage tops (no spaghetti straps, no low necklines, no bare midriffs, no off-the-shoulder); pants, jeans, or knee-length-or-longer skirts/dresses (no short-shorts, no mini-skirts, no skin-tight leggings as outerwear)
- Boys: shirts on (no muscle shirts, no bare chests); pants or longer shorts (no skin-tight athletic wear)
- Both: nothing form-fitting in a way that would draw attention to the body

This isn't a dress-code lecture — it's a "this image needs to be at home in a Christian education classroom" filter. Every wardrobe note in a panel prompt should pass that test.

Demographic mix: vary teens deliberately across the 13 panels — boys and girls, different ethnicities, different builds. The wall should look like a body of Christ, not one teen in different outfits.

---

## TEMPLATE (fill in the brackets per panel)

```
Photorealistic image of [TEEN(S) DESCRIPTION — age, gender, ethnicity,
hair, build]. [PRIMARY ACTION — what they are doing in one clear
sentence, present-tense, action moment not posed shot].

[BODY LANGUAGE DETAIL — specific posture, gesture, hand position,
where the body weight is, where the eyes are looking. Two to four
sentences. Be precise — the prompt has to do the directing because
the model can't read intent].

[EXPRESSION — one short clause. "small warm smile, brief eye contact"
or "calm focused face, eyes on the work" or "easy and unselfconscious".
Avoid grand emotion words. Read like a director's note, not a feeling].

[SECONDARY SUBJECT(S) IF ANY — same level of detail. Where they are,
what they're doing, what they look like, what their body is doing].

Modest everyday clothing: [TEEN 1 OUTFIT FROM WARDROBE VOCABULARY];
[TEEN 2 OUTFIT IF APPLICABLE]. No bold logos, no athletic brands.

Setting: [LOCATION — school hallway, kitchen, front porch, sports
sideline, cafeteria, classroom, park, neighborhood street]. [3-5
specific environmental details that anchor the scene — what's on
the walls, what's on the floor, what's visible through a window,
what time of day it is].

Background: [WHAT IS HAPPENING IN THE BACKGROUND — usually a few
softly out-of-focus people or environmental cues that make the
location feel real, not staged].

──── LOCKED VISUAL LANGUAGE — DO NOT MODIFY ────

Lighting: late afternoon golden-hour sunlight, warm directional
light, long soft shadows. No harsh midday sun, no fluorescent
overhead, no blue-white indoor light.

Palette: warm golds, cream, soft mustard, weathered denim, deep
burgundy or navy as a single accent, muted blue-green for cool
contrast, warm earth tones throughout. No saturated reds, no neon,
no high-key fashion-magazine color.

Composition: RESERVE the entire upper 35% of the frame as empty
negative space for verse text overlay. This zone must contain only
softly out-of-focus background — empty sky, blurred ceiling,
distant wall, or window light — never any head, hand, body, object,
or in-focus detail. Position every subject so their highest point
(top of head, raised hand, etc.) sits BELOW that upper 35% line.
Frame the shot wider or step the camera back if necessary to
achieve this. Subjects grounded in the lower two-thirds.

Negative content: no text on signs, papers, banners, or screens.
No brand logos, no school mascots, no team names. No phones, no
laptops on screen. No watermarks. No floating debris or background
clutter. No nudity of any kind — if drawings, paintings, sculptures,
or figure studies appear in the scene, every depicted figure must be
fully clothed.

Camera: shot on medium-format camera, 50mm lens equivalent, shallow
depth of field on the primary subject's face, natural film grain,
soft skin tones, no over-sharpening, no HDR halos.

Aspect ratio: 4:3, portrait orientation.
```

---

## Worked example — Panel 2: Love is kind (using Paul's existing prompt)

The prompt you already wrote *is* the template fully filled in. Annotated against the slots:

| Slot | What you wrote |
|---|---|
| TEEN 1 | "Black teenage boy, around 16 years old" |
| PRIMARY ACTION | "standing to the side of an open classroom doorway in a school hallway, holding the door open for a white teenage girl, around 15, whose hands are full" |
| BODY LANGUAGE | "He stands against the hallway wall just to the right of the doorway, his right arm extended back to hold the door open behind him, his body turned sideways so that the path through the doorway is completely clear. The doorway opening itself is empty — no part of him is in it." |
| EXPRESSION (1) | "His expression is easy and unselfconscious — a small warm smile, brief eye contact with the girl, no fanfare." |
| SECONDARY SUBJECT | "The girl is approaching the doorway with her body and feet angled toward the classroom, in the act of turning to step through into the room … She is carrying a stack of textbooks braced against her chest with both arms, a binder balanced on top, a water bottle tucked under one elbow." |
| EXPRESSION (2) | "Her expression is a little surprised and grateful, mouth just opening to say thank you." |
| WARDROBE | "deep burgundy hoodie over a cream t-shirt and jeans; the girl in a soft mustard cardigan over a muted blue-green blouse" |
| SETTING + DETAIL | "school hallway with lockers along one wall, late afternoon golden sunlight angling in through a window at the far end of the corridor, casting long warm shadows across the polished floor" + "Through the open doorway, the classroom interior is visible: rows of desks, a whiteboard on the far wall, warm interior light. The door is a standard classroom door with a glass panel and a room number plate." |
| BACKGROUND | "a few other students walking in the distance, softly out of focus" |
| **LOCKED BLOCK** | "Palette: warm golds, cream, deep burgundy accent, muted blue-green, weathered locker metal. No text on signs or papers, no logos, no school mascots, no phones, no watermarks visible. Clean negative space in the upper third of the frame for later text overlay. Shot on medium-format camera, 50mm lens, shallow depth of field, natural film grain. 4:3 aspect ratio, portrait orientation." |

Notice: every locked-block element is already in your prompt. Future panels just swap the variable blocks while keeping the locked block byte-for-byte identical.

---

## Per-panel checklist before generating

- [ ] Wardrobe pulled from the catalog vocabulary — no off-palette colors
- [ ] Demographics intentional and varied from the previous panel
- [ ] Body language is *specific* (where the hand is, where the eyes go) — not generic
- [ ] Expression is a director's note, not a feeling word
- [ ] Background has 1-2 anchoring details, not vague "school setting"
- [ ] Negative-content rules included verbatim
- [ ] Locked visual-language block pasted byte-for-byte
- [ ] Upper third is clear of subject for text overlay

---

## After generation

- [ ] Top third clear enough for text overlay? If not, regenerate or crop.
- [ ] Watermark in the corner? If using Gemini, crop or use a different model.
- [ ] Lighting matches the previous panels? Hold the wall together visually — if a panel comes out too cool or too dark, regenerate.
- [ ] Save as `panel-NN_love-is-XXX_modelname.png` so the file pile stays organized.
