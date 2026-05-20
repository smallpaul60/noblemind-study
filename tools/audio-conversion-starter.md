# Starter Message — Audio Book Conversion

Use when opening a new chat to convert manuscript chapters into TTS-ready text.

---

## The message

> I'm converting **[BOOK TITLE]** into TTS-ready .txt files for [SoundTools / other voice-clone tool]. I have a Python script called `audio_text_converter.py` that handles the standard conversions. Before running it on this book, I need help building the `NAME_REPLACEMENTS` dictionary for names this book uses that TTS engines will mispronounce.
>
> [Attach or paste the manuscript chapters]

That's the whole opener. Memory will fill in the rest.

---

## What the script already handles

- Bible references → spoken form (`Genesis 16:13` → `Genesis sixteen, verse thirteen`)
- Numbered books → spelled out (`1 Samuel` → `First Samuel`)
- Verse ranges: `1-2` → "verses one and two"; `1-4` → "verses one through four"
- Chapter ranges with no verse: `Exodus 3-14` → "Exodus chapters three through fourteen"
- Strips markdown (headers, bold, italic, horizontal rules, links)
- Splits chapter title headings (`# Title — Chapter 3` → two lines, with `Chapter Three.`)
- Removes parens around references and normalizes period placement
- Applies the `NAME_REPLACEMENTS` dictionary (the per-book customization)

## What to ask Claude to do

1. Read through the manuscript and flag any names likely to be mispronounced
2. Propose phonetic spellings to add to `NAME_REPLACEMENTS`
3. Spot-check the converted output for anything awkward
4. Help with edge cases the script doesn't handle (resource lists, URLs, phone numbers, unusual abbreviations)

## Conventions baked into the workflow

- NASB throughout
- Em-dashes preserved (TTS treats them as natural pauses)
- Phone numbers in resource sections read digit-by-digit (`one eight hundred...`)
- URLs read with "dot" (`care-net dot org`)
- Sentence-ending colons in body prose may need to be changed to periods if TTS reads them awkwardly — spot-check
- Source paragraph structure is preserved; if a reference at the end of a paragraph reads better with a manual break afterward, add it by hand

## Phonetic patterns that reuse across books

Hebrew names with vowel clusters that TTS misreads:
- `Jochebed → Jock-eh-bed`
- `Elkanah → El-kah-nah`
- `Peninnah → Pen-in-nah`
- `Mordecai → Mor-deh-kai`
- `Habakkuk` (likely will need one)

Names that collide with common English words:
- `Boaz → Bo-az` (not "boats")
- `Orpah → Or-pah` (not "Oprah")
- `Salmon → Sal-mone` (not the fish)
- `Haman → Hay-man`

Two-word Hebrew phrases:
- `El Roi → El Ro-ee`
- Anything else of the form `El [name]`, `Yahweh [name]`, etc., probably needs a phonetic version

When in doubt, drop the name into a TTS preview and listen. If the engine handles it cleanly, leave it out of the dictionary — every entry adds maintenance.
