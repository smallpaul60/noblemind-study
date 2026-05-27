# Berean Brief — for OT Timeline Spokes & Doctrinal Pages

**Read this BEFORE composing any prose for a spoke, study, or doctrinal
page. Read it again before committing.** Internal-only; excluded from deploy.

This is the forcing function for doctrinal integrity. Memory entries
record drift after it happens. This brief is meant to prevent it.

---

## The single guiding principle

**Walk the text as Scripture describes it. Cite NT correspondences only
where Scripture itself names them. Where Scripture is silent, say so.**

Inferences, traditional readings, denominational frames, and systematic
theology are all *additions* to the text. They may be true, partially
true, or wrong — but they are not the text. A Noble Mind Study spoke
shows the reader what Scripture says, with explicit chapter and verse,
and names its inferences as inferences.

---

## Banned denominational frames

Watch for these systems creeping in. Any spoke that imports one of these
frames is no longer a Berean walk through the text.

### Dispensationalism
- "The rapture" / "pre-tribulation rapture" / "the tribulation period"
- "Millennial reign" / "pre-millennial" / "amillennial" / "postmillennial"
- "Seven dispensations" or any numbered-ages scheme
- "Two peoples of God" (Israel vs. the church)
- "Earthly kingdom" vs. "spiritual kingdom" as distinct destinies
- Mapping the fall feasts of Lev 23 to the second coming
- "The Antichrist" as a specific end-times figure (the word appears in
  1 John 2:18, 22; 4:3; 2 John 7 only, never as a single end-times figure)
- "Israel" used to mean the modern political nation as fulfillment of
  OT promise

### Hebrew Roots / Sacred Name
- "Yahshua" / "Yahushua" naming for Jesus
- Prescriptive claims that Christians must keep the feasts, Sabbath,
  food laws
- "Restored church" / "Restoration movement" in the Sacred Name sense
- Treating the Hebrew calendar as the Christian liturgical calendar

### Reformed / Calvinist soteriology
- "TULIP"
- "Total depravity" / "Unconditional election" / "Limited atonement" /
  "Irresistible grace" / "Perseverance of the saints" (as the five points)
- "Doctrines of grace" (Reformed shorthand)
- "Decretal will" / "Two wills of God"
- "Elect" used to argue predestination-of-individuals soteriology
  (the word IS in Scripture — Matt 24:31, etc. — but used in this
  framework it carries the Calvinist baggage)

### Roman Catholic
- "Magisterium" / "the magisterium"
- "Pope" / "Papal" (as theological authority)
- "Apostolic succession" in the magisterial sense
- "Co-redemptrix" / Marian co-mediation
- "Purgatory"
- "The seven sacraments"

### Pentecostal / Charismatic specifics
- "Slain in the Spirit"
- "Word of faith" / "Health and wealth"
- "Tongues as the initial evidence"
- "Baptism in the Spirit" as a second blessing
- "Holy laughter"

### Sentimental Evangelical
- "Personal Lord and Savior" (not biblical phrasing)
- "Asking Jesus into your heart" (not biblical)
- "The sinner's prayer" (not biblical)
- "Accept Christ as your personal Savior"
- "Get saved" (colloquial / revivalist; not Acts language)
- Christmas/Easter cards framed as apostolic ("kindness took on a face")

### Tiered-truth language (already banned in `check_language.py`)
- "Essentials of the faith" / "Fundamentals of the faith"
- "Secondary matter" / "Secondary question" / "Secondary issue"
- "Non-essential"
- "In essentials unity, in non-essentials liberty"
- "Salvation issue"

---

## Pattern overstatements

Soften universal claims unless Scripture explicitly supports them.

- ❌ "God always..." / "God never..." / "in every case..." / "God has ever..."
- ✅ "Scripture shows..." / "Scripture records..."
- ❌ "And only together..." (implies a universal pairing not stated)
- ✅ Name the specific texts that make the connection.

---

## Methodological discipline for typological / fulfillment claims

When a spoke claims an OT picture is fulfilled in Christ:

1. **Is there an explicit NT citation of the OT text?** If yes (Matt 1:22
   "this happened to fulfill what was spoken by the prophet…"), state the
   citation by chapter and verse.
2. **Is there an apostolic application without explicit citation?** If
   yes (1 Cor 5:7 "Christ our Passover has been sacrificed" — applies
   Exodus 12 without quoting it), say so.
3. **Is the connection inferred from theological resonance?** Say *so
   explicitly*. Use language like "the resonance is striking" or "many
   readers have heard this echo" rather than "fulfills" or "is the
   fulfillment of".
4. **Does Scripture name no connection at all?** Say so — and resist the
   temptation to invent one. Trumpets (Lev 23:23–25) is the standing
   example: the trumpet at the resurrection (1 Cor 15:52) is not
   connected back to *Yom Teruah* by any NT writer.

---

## Pericope & textual integrity

- **Pericope adulterae (John 7:53–8:11)** — bracketed in modern critical
  editions. Do not build doctrinal arguments on it in Berean material.
  Use Mark 5:25–34, Luke 7:36–50, John 4, or Luke 19 for the same
  theological beats.
- **Longer ending of Mark (16:9–20)** — same. Don't anchor on it.
- **Mention textual uncertainty** when relevant, but distinguish:
  - Manuscript-level variants → must be flagged
  - Pastoral rhetorical compressions (e.g., "same crowd Hosanna→crucify")
    → acceptable usage

---

## Scripture quotation accuracy

- **NASB** is the default. Quoting NASB means quoting the actual text
  word-for-word. Near-quotes are not Scripture.
- Cross-check every verbatim Scripture quotation against the actual
  NASB text. Use the Bolls.Life API workflow if unsure.
- Citations with em-dashes: Bolls renders them as `--`.

---

## Pre-commit checklist for any new spoke or doctrinal page

Before committing:

1. Have you read this brief, this commit, top to bottom?
2. Run `python3 tools/check_language.py --spokes` (or the specific spoke).
   Review every flag. Zero findings is the goal; surviving findings must
   each have a defensible reason.
3. Search the file you wrote for the words "always", "never", "every",
   "only", "must", "fulfill" — and audit each occurrence.
4. Search for "rapture", "tribulation", "millennial", "elect",
   "predestined" — confirm these aren't used in their denominational
   senses.
5. Confirm: every NT fulfillment claim names its NT citation by chapter
   and verse. Every inferred connection is named as an inference.

---

## When in doubt

Pause. Ask the author. The cost of pausing is small; the cost of drift
is a Berean book or spoke that quietly imports somebody else's framework
into Paul's published work.
