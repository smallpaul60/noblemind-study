# Old Testament Timeline — Spoke Plan

Internal planning doc for the deep-dive spokes that hang off the OT timeline
hub (`old-testament-timeline/index.html`). Each spoke is a self-contained
study artifact with its own visualization, anchored to 2–3 events in the
hub via the `DEEPDIVE_*` pattern already established (see the Genesis
Genealogy chart for the working reference implementation).

Excluded from deploy.

---

## The shape that works

The Genesis Genealogy chart established the working pattern:

1. **Self-contained study artifact** at a sibling URL
   (`noblemind.study/<slug>/`), not buried inside the hub directory.
2. **A specific visualization** that the prose of the hub timeline cannot
   convey — a chart, diagram, parallel-columns table, ritual sequence.
3. **Two or three anchor events** in the hub timeline carry a `deepDive:`
   field pointing to the spoke. Restraint matters: scatter the link too
   broadly and readers learn to ignore it.
4. **A back-link in the spoke** (`../old-testament-timeline/`) that
   returns cleanly. The forward and back paths must agree before deploy.
5. **Each anchor event's `secondary` field** can briefly preview what
   the spoke shows that the prose can't — a teaser that earns the click.

Every future spoke follows this same shape.

---

## Tier 1 — Build first

### 1. The Passover Lamb (Exodus 12)

**Shape:** A day-by-day ritual sequence visualization for the Nisan 10–14
week of the original Passover. Five sequential panels (one per day) showing
the Lord's instructions to Israel — select the lamb, examine it, kill it
at twilight on the 14th, apply the blood to the doorposts, eat it roasted
in haste. Each panel includes the Scripture (Exodus 12) and a Christological
cross-reference (the Lamb of God, 1 Cor 5:7, John 1:29, 1 Pet 1:18–19, and
notably the same Nisan 10 → 14 pattern observed in Christ's final week per
*The Last Week of the Lamb*).

**Anchor events:**
- The Passover (Phase 5, "The Passover; the firstborn struck; Israel goes out")

**Cross-link:** Could link to `TheLastWeekOfTheLamb/` book on the site so
the OT typology connects to its NT fulfillment study.

**Complexity:** *Small.* A single Scripture passage, a clear sequential
structure, ~5–7 panels of content. Probably the cleanest first build to
validate the spoke pattern in a new domain.

**Why it matters:** The Passover is the central typological pattern of
the entire Bible. Showing it as a sequence rather than a prose paragraph
makes the lamb-of-God parallel land visually.

### 2. The Tabernacle (Exodus 25–31, 35–40)

**Shape:** A floor-plan diagram showing the tabernacle courtyard, the holy
place, the holy of holies, and each piece of furniture (bronze altar,
laver, lampstand, table of showbread, altar of incense, ark of the
covenant, mercy seat). Each piece is clickable; clicking opens a small
side panel showing:
- What it was (description, dimensions, materials)
- Where it stood
- What it pictured (typology — Christ, the priesthood, the gospel)
- Scripture references (in Exodus for construction, in Hebrews for
  Christological fulfillment)

**Anchor events:**
- The tabernacle constructed; the cloud descends (Phase 5)
- The book of Leviticus; the priestly system (Phase 5)
- Optional: Solomon builds the temple (Phase 9) — the tabernacle pattern
  realized in stone

**Complexity:** *Medium.* The data is well-defined (Exodus gives exact
specifications). The design work is in the diagram — likely an SVG floor
plan with hotspots. Could be flat or could include a partial 3D
perspective. Either works.

**Why it matters:** Hebrews 8–10 treats the tabernacle as the type that
Christ's heavenly priesthood fulfills. Without a visual of the tabernacle,
the Hebrews argument is hard to follow. With one, it lands immediately.

---

## Tier 2 — Build after Tier 1 lands

### 3. The Covenants of God

**Shape:** A parallel-columns or expandable card view showing the major
covenants in chronological order. For each covenant:
- Name
- Parties (whom does God covenant with?)
- Date (or biblical event anchor)
- Promise (what God promises)
- Conditions (what is required of man, if anything)
- Sign (rainbow, circumcision, Sabbath, etc.)
- Texts (where the covenant is established and reaffirmed)
- Status (fulfilled / ongoing / inaugurated)

Five to seven covenants depending on how one counts:
- Edenic / Adamic (Gen 1–3)
- Noahic (Gen 9)
- Abrahamic (Gen 12, 15, 17)
- Sinai / Mosaic (Ex 19–24)
- Davidic (2 Sam 7)
- New (Jer 31; fulfilled in Christ)
- *Some count a "Land/Palestinian Covenant" (Deut 30) separately.*

**Anchor events:**
- The Noahic covenant: rainbow, meat, blood (Phase 2)
- The Abrahamic covenant cut (Phase 4)
- Sinai; the giving of the Law (Phase 5)
- The Davidic covenant: an eternal throne (Phase 9)
- Jeremiah: the New Covenant promise (Phase 11)

**Complexity:** *Medium.* The data fits a structured-table shape
naturally. Design challenge is making the chart show the *unfolding* —
each covenant doesn't replace the prior; it nests within and advances
it. A timeline-style horizontal axis with stacked covenants showing
their durations and overlaps could work well.

**Why it matters:** Covenant theology is the spine of Berean Bible
reading. A reader who can name the five covenants and place them in
order has a framework that organizes every doctrinal question.

### 4. The Day of Atonement (Leviticus 16)

**Shape:** A ritual-sequence visualization, similar in shape to the
Passover Lamb spoke but more complex. Likely overlaid on the tabernacle
diagram (re-using or referencing the tabernacle spoke). Step-by-step:
- The high priest's preparation (washing, linen garments)
- The bull for his own sin
- The two goats: one for the Lord, one for Azazel ("scapegoat")
- The lots cast
- The bull's blood into the holy of holies
- The Lord's-goat's blood into the holy of holies
- The blood on the altar of incense, the bronze altar
- The high priest's confession over the scapegoat
- The scapegoat sent into the wilderness
- The priest's bathing and second set of garments

Each step linked to its Christological fulfillment in Hebrews 9–10 and
Romans 3:25 (the propitiation, "mercy seat").

**Anchor events:**
- The book of Leviticus; the priestly system (Phase 5)
- *Sidebar from Tabernacle spoke when complete*

**Complexity:** *Medium-large.* Detail is intricate. Visual design
benefits from referencing the tabernacle diagram (so probably depends
on that spoke being built first).

**Why it matters:** The most theologically dense ritual in Israel's
calendar and the most extensive type-of-Christ in the OT. Hebrews 9
walks through this ritual at length. A visualization makes the prose
of Hebrews intelligible.

---

## Tier 3 — Ambitious, build last (or as standalone projects)

### 5. The Promise Threads

**Shape:** A multi-thread visualization tracing single promises across
the whole Bible. The seed promise of Gen 3:15 is the obvious central
thread: → Gen 12:3 → Gen 22:18 → Gen 49:10 → 2 Sam 7:12–16 → Isa 9:6–7
→ Isa 11 → Jer 23:5–6 → Mic 5:2 → Matt 1:1.

Other threads possible: land promise, the temple promise, the new
covenant promise, the Spirit promise (Joel 2 → Acts 2), the regathering
promise.

**Anchor events:** Spread across many phases — Gen 3:15 (Phase 1),
Abrahamic call (Phase 4), Jacob's blessing on Judah (Phase 4), Davidic
covenant (Phase 9), various prophets (Phase 10–11).

**Complexity:** *Large.* The design problem is the hardest of any
spoke listed here — how do you show multiple parallel threads through
30+ Scripture passages without becoming illegible? Options:
- A vertical scrolling layout where each thread is its own column
- An interactive thread-selector that highlights one thread at a time
- A "story-walk" sequence that lets the reader follow one promise from
  origin to fulfillment

**Why it matters:** The Berean reading method *is* tracing promises.
This spoke would teach the method by example. But it's the most
ambitious by far — best built after the simpler spokes have proven the
pattern.

### 6. The Kinsman-Redeemer (Ruth, Boaz, and Christ)

**Shape:** A typology-tracing study following the *go'el* (kinsman-redeemer)
pattern from the law of Leviticus through the book of Ruth into Christ.
Four to six episodes:

1. **The law of redemption** (Lev 25:25, 47–49) — the right and duty of
   the nearest kinsman to redeem land and family from loss.
2. **The threshing-floor scene** (Ruth 3) — Ruth at Boaz's feet, asking
   him to spread his garment over her: *redeem me.*
3. **The closer relative declines** (Ruth 4:1–6) — there is one nearer
   than Boaz; he could redeem but he will not, lest he ruin his own
   inheritance. Boaz steps forward in his place.
4. **The transaction at the gate** (Ruth 4:7–12) — Boaz takes the sandal,
   the witnesses bless him, the redemption is sealed.
5. **The typology becomes literal** (Ruth 4:13–22; Matt 1:5) — Ruth
   bears Obed, who is the father of Jesse, who is the father of David;
   Ruth's name stands in the genealogy of Christ. *The type and the
   fulfillment share a bloodline.*
6. **Christ our Kinsman-Redeemer** (Heb 2:14–17; Gal 4:4–5; 1 Pet
   1:18–19) — *since the children share in flesh and blood, He Himself
   likewise also partook of the same.* He had to become *kin* before
   He could redeem; He had to be willing as Boaz was; He bought us back
   with His own blood.

**Anchor events:**
- Book of Ruth (Phase 8, within The Judges)
- *Optional:* The law of redemption could be a sidebar tied to the
  Leviticus event (Phase 5)

**Complexity:** *Small-to-medium.* Single book of focus with NT
cross-references. Visualization can be simple: sequential episode cards
similar to *The Lamb God Provides*.

**Why it matters:** The kinsman-redeemer pattern is in the LAW (Lev 25),
narratively fulfilled in Ruth, theologically applied to Christ in the
NT (Heb 2). And — as the X-post observation goes one layer deeper —
the Moabite widow whose redemption pictures Christ's also becomes
Christ's literal ancestor. *The type and the fulfillment share a
bloodline.* Few typological studies have a payoff that sharp.

### 7. The Appointed Times of the LORD (Leviticus 23) ✅ done

**Shape:** Feast-by-feast walk through Leviticus 23 — Sabbath, then the
seven annual moedim in chronological order through the year:

1. **Sabbath** (Lev 23:3) — weekly rest
2. **Passover** (Nisan 14, Lev 23:5)
3. **Unleavened Bread** (Nisan 15–21, Lev 23:6–8)
4. **Firstfruits** (day after the Sabbath, Lev 23:9–14)
5. **Pentecost / Weeks** (50 days after Firstfruits, Lev 23:15–22)
6. **Trumpets** (Tishri 1, Lev 23:23–25)
7. **Day of Atonement** (Tishri 10, Lev 23:26–32) — links to dedicated spoke
8. **Booths / Tabernacles** (Tishri 15–22, Lev 23:33–43)

**Framing — deliberate guardrails:**
- Title is *The Appointed Times of the LORD* (Lev 23:2, 4 — *moedim YHWH*),
  not "Seven Appointed Times." The popular framing carries
  dispensationalist eschatology and Hebrew Roots prescriptions that are
  not in the text.
- NT correspondences are named only where Scripture itself names them:
  Passover (1 Cor 5:7), Unleavened Bread (1 Cor 5:8), Firstfruits
  (1 Cor 15:20–23), Pentecost (Acts 2), Sabbath (Heb 4), Atonement
  (Heb 9–10).
- Trumpets and Booths are flagged with a deliberate "what the NT does
  *not* name" callout. The trumpet at the resurrection (1 Cor 15:52)
  and John 7 at Sukkot are noted as resonances, not as named
  fulfillments. We don't invent what Scripture doesn't name.
- Lands at Col 2:16–17 — *shadow / substance / Christ* — the apostles'
  own verdict on the calendar for the church.

**Anchor events:**
- The book of Leviticus / the priestly system (Phase 5) — wired alongside
  DEEPDIVE_ATONEMENT via the new deepDives-array schema

**Why it matters:** The appointed times are how Israel marked the year
by what the LORD had done. The spring feasts cluster around Christ's
death, burial, resurrection, and the giving of the Spirit — Scripture
names every one of these. The fall feasts stand without explicit NT
fulfillment narratives. The honest study says so.

### 8. The Divided Kingdom Synoptic

**Shape:** Two parallel horizontal tracks running 931 BC → present-end-
of-each-kingdom (722 BC for Israel, 586 BC for Judah). Each king on
his track:
- Color-coded by faithfulness (Scripture's verdict: "did right in the
  eyes of the Lord" / "did evil")
- Reign duration visible from the track length
- Hover for short bio + key events of the reign

Prophets overlaid where they ministered:
- Elijah, Elisha, Amos, Hosea, Jonah → Israel
- Obadiah, Joel, Isaiah, Micah, Zephaniah, Habakkuk, Nahum, Jeremiah →
  Judah

External anchors (Pharaoh Shishak's invasion, Mesha Stele, Sennacherib,
Nebuchadnezzar) marked on the time axis.

**Anchor events:**
- The kingdom splits; Rehoboam loses ten tribes (Phase 10)
- Ahab and Jezebel; Elijah the Tishbite (Phase 10)
- The fall of Samaria; Israel taken into Assyrian captivity (Phase 10)
- The fall of Jerusalem; three deportations (Phase 11)

**Complexity:** *Large.* The data work is substantial — ~40 kings to
research and verify Scripture's verdict on each, dates of reigns
(some debated), prophet date ranges. The design work is also real
(two-track synoptic with overlaid prophets).

**Why it matters:** The Divided Kingdom is the hardest period for most
Bible students to keep straight. A synoptic chart would be one of the
most useful single tools for OT study on the internet. But it's the
most expensive build of the lot.

---

## Recommended order

| Order | Spoke | Tier | Complexity | Rationale |
|---|---|---|---|---|
| 1 | Passover Lamb (Lamb God Provides) | 1 | S | ✅ done. Validated the typology-sequence pattern. |
| 2 | Tabernacle | 1 | M | ✅ done. |
| 3 | Kinsman-Redeemer (Ruth → Christ) | 1–2 | S–M | ✅ done. The type-becomes-genealogy payoff is sharp. |
| 4 | Covenants | 2 | M | ✅ done. Five covenants side by side. |
| 5 | Day of Atonement | 2 | M-L | ✅ done. |
| 6 | The Appointed Times of the LORD (Lev 23) | 2 | M | ✅ done. Renamed from "Seven Appointed Times" to avoid dispensationalist framing. |
| 7 | Promise Threads | 3 | L | ✅ done. Eight threads, NT-named correspondences only. BEREAN_BRIEF.md drift-prevention now in place. |
| 7 | Promise Threads | 3 | L | Beautiful concept but the design is the real work; do after pattern is mature |
| 8 | Divided Kingdom Synoptic | 3 | L | ✅ done. 40 kings, 13 prophets, 8 external anchors on a 345-year two-track chart; Scripture's own verdict cited per king. |

The progression goes **small/contained → larger/more design → most
ambitious**. Each spoke we build teaches us something about what works
for the next one. The Genesis Genealogy chart (already built) is a
zero-th spoke that established the wiring pattern; the Passover Lamb
should be the first to establish the *content-shape pattern* for the
remaining five.

---

## Common implementation pattern (already proven in Genesis Genealogy)

For each spoke:

1. **Build the chart/diagram at `noblemind.study/<slug>/`** with a
   back-link `../old-testament-timeline/` and its own canonical tag.
2. **Add a `DEEPDIVE_<SLUG>` const** at the top of the OT timeline's
   events script:
   ```js
   const DEEPDIVE_PASSOVER = {
     label: "See the seven-day Passover sequence →",
     href: "../passover-lamb/"
   };
   ```
3. **Attach `deepDive: DEEPDIVE_<SLUG>`** to 2–3 anchor events.
4. **Optional teaser in the `secondary` field** of each anchor event —
   one sentence previewing what the spoke shows that the prose can't.
5. **Test the round-trip** before deploying.

The deep-dive UI (`.deep-badge`, `.deep-dive-link`, badge + link
rendering) is already in the OT timeline — no porting needed for any
future spoke.
