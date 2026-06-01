# Noble Mind Study Tool — Project Context

## Architecture

Single-page Progressive Web App (PWA) for Bible study. Entirely client-side — no backend server, no build step, no package manager. The main application lives in one file:

- **`Noble_Mind_Study_Tool_v2.html`** (~6,300 lines) — The entire app: UI, logic, styles, all inline.
- **`index.html`** — Landing page with links and PWA install prompt.
- **`user-guide.html`** — Comprehensive user guide (opens in new tab from study tool).
- **`sw.js`** — Service worker (cache-first strategy, version `v52`). Bump the version when updating cached assets.
- **`nm-core.js`** — Client-side analytics (~40 lines). POSTs to `/api/nm/p`. No cookies, no fingerprinting.
- **`manifest.json`** — PWA manifest (standalone, dark theme `#0d0d0d`).

### Data Files
- `KJV.json` (12.4 MB) — Full King James Version text (embedded client-side).
- `BDBT.json` (10.5 MB) — Bible database.
- `strongs.json` (2.7 MB) — Strong's Hebrew & Greek dictionary (8,700+ entries).
- `maps/data/` — Biblical location data (ancient.jsonl, modern.jsonl, locations.json — 1,309 locations from OpenBible.info).

### Lesson Content
- `Acts-Enhanced/` — 53 HTML lesson files for the Book of Acts.
- `StraitWay/` — 60 PDF study materials (curriculum).
- `StraitWay-Enhanced/` — Enhanced versions of StraitWay materials.

### Analytics Console (`console/`)
- **Self-hosted, privacy-first analytics** — Go binary (`noblemind-console`) running on port 3001.
- `console/main.go` — Entry point, HTTP server, graceful shutdown.
- `console/handlers.go` — Beacon receiver, stats API, dashboard serving, auth middleware.
- `console/database.go` — SQLite schema, inserts, queries, aggregation loop.
- `console/privacy.go` — Daily salt rotation, IP hashing (SHA-256), GeoIP, UA parsing.
- `console/beacon.go` — Payload parsing and validation.
- `console/dashboard.html` — Single-file analytics UI (embedded via `go:embed`), Chart.js, NobleMind theme.
- `console/deploy-console.sh` — Cross-compile, SCP to VPS, restart systemd service.
- `console/noblemind-console.service` — Systemd unit file.
- **Privacy model:** Raw IPs never stored. SHA-256(IP + permanent_salt) truncated to 16 hex chars. No cookies, no localStorage, no fingerprinting. Permanent salt loaded from `VISITOR_SALT` env var (auto-generated and persisted to the `daily_salt` table under key `PERMANENT` if unset). Stable visitor hash means returning visitors are detectable across days; the daily salt rotation was removed 2026-04-30 because the cross-day blackout was hurting analytics more than it was protecting users.
- **VPS directory:** `/home/paul/noblemind-console/` (separate from static site).
- **Database:** SQLite at `/home/paul/noblemind-console/analytics.db`. Raw data purged after 90 days.
- **Auth:** Token-based via `?token=` query param or `Authorization: Bearer` header. Token stored in `/home/paul/noblemind-console/.env`.
- **Nginx:** Proxies `/api/nm/*` and `/console` to `:3001`. Static files served directly.

### Utility Scripts (not deployed)
- `convert_strongs.py` — Converts Strong's XHTML to JSON.
- `update_map.py` — Updates Bible maps with themed journey routes.
- `deploy.sh` — Deployment script (see Deployment section).

## Tech Stack

- **Languages:** HTML5, CSS3, JavaScript (ES6+), Go (analytics console), Python (utilities only)
- **No build tools** — No Node.js, npm, webpack, vite, etc. Pure static files.
- **CDN Libraries:**
  - Leaflet.js v1.9.4 (maps)
  - Tesseract.js v5 (OCR for PDF import)
  - pdf.js v3.11.174 (PDF parsing)
  - jsPDF v2.5.1 (PDF generation)
  - Google Fonts (Open Dyslexic for accessibility)
- **External API:** Bolls.Life (`https://bolls.life`) — Bible text lookup for multiple translations (NASB, LSB, ESV, NIV, NLT, KJV, etc.)
- **UI:** Dark theme, glassmorphism, green/cyan accents (`#06FFA5`, `#5ee5ff`)

## VPS & Deployment

### Server
- **Host:** `198.23.134.103`
- **User:** `paul`
- **SSH:** `ssh paul@198.23.134.103` (authenticates via SSH key from `~/.ssh/`)
- **Remote directory:** `~/noblemind-study`
- **IPFS Kubo node** runs on this VPS
- **Shared VPS** — StoryLock also runs on this server

### Deploy Process (`./deploy.sh`)
1. **Rsync** project files to VPS (excludes `.git`, `*.py`, `PRINCIPLES.md`, `console/`)
2. **IPFS add** — pins content to local Kubo node on VPS
3. **IPNS publish** — updates the IPNS name so the domain resolves to the new CID

### Deploy Console (`./console/deploy-console.sh`)
1. Cross-compile Go binary for linux/amd64
2. SCP binary to VPS `/home/paul/noblemind-console/`
3. Update systemd service and restart

### IPNS
- **Key name:** `noblemind`
- **IPNS address:** `k51qzi5uqu5dg9bleldhzzzxmydvtmntfl2lajle3jfi8wv58xdc5jw0i6tunj`

### URLs
- **Primary:** https://noblemind.study
- **IPFS subdomain:** https://ipfs.noblemind.study
- **IPNS gateway:** https://ipfs.io/ipns/k51qzi5uqu5dg9bleldhzzzxmydvtmntfl2lajle3jfi8wv58xdc5jw0i6tunj

## Conventions

- All application code lives in a single HTML file — keep it that way.
- Bump `sw.js` cache version when changing any cached asset.
- Dark theme is the only theme. Maintain glassmorphism aesthetic.
- Scripture methodology: "Scripture Interprets Scripture" (Churches of Christ tradition).
- Offline-first: everything the user needs must work without a network connection.
- Accessibility: Open Dyslexic font option, high contrast, semantic HTML.

### Doctrinal content

No doctrinal text — paragraphs, sentences, claims, or Scripture quotations — may be dropped, summarized, condensed, or rewritten during a refactor or reskin without explicit author sign-off.

- **Reformatting** prose into a list of the same content is fine.
- **Relocating** approved prose to a new section is fine, as long as an HTML comment traces the source paragraph.
- **Removing** content because it "feels redundant" is *not* fine. Surface every drop as a question to the author *before* committing.
- **NASB quotations** must be cross-checked against the actual text per `design-refs/BRAND_BRIEF.md` § Scripture accuracy. Near-quotes are not Scripture. The mono small-caps gold citation is reserved for verbatim NASB only.

This applies to every editorial page, every test-this-claim study, every book chapter, every mockup, and every Scripture or doctrinal claim anywhere on the site.

### Per-book generator scripts

Each book directory follows the same script layout:

- `generate_html_chapters.py` — online reader HTML (dark-theme glass pages).
- `generate_pdf.py` — downloadable reader PDF. 5.5" × 8.5", EB Garamond, single-sided with centered page numbers, cover image on page 1, then title / copyright / TOC / body. Scripture blockquotes use a per-book accent-color 2pt left border with italic quote + citation. Distinct from the Lulu interior — do not conflate them. If the book is access-gated, encrypt the output with `pypdf` using the same password as the online reader gate.
- `generate_epub.py` — downloadable EPUB. Matching structure and metadata, cover embedded, nested nav when the book has Parts or Appendices.
- `generate_lulu_interior.py` — print interior for Lulu. 5.5" × 8.5" with 0.75" gutter, 0.625" outside, alternating facing-page margins, chapters start recto. Not the same file as the reader PDF.
- `generate_lulu_paperback_cover.py` / `generate_ingram_paperback_cover.py` / `generate_ingram_hardcover_cover.py` — print-ready covers. IngramSpark hardcover doc size must be 24"×12.5"; see the memory note on the jacket pipeline.

### `books.html` card pattern

- **Action buttons**, left to right: `Read Online` (`.btn-primary`) → `PDF` (`.btn-outline`) → `EPUB` (`.btn-outline`) → `Order Paperback` (`.btn-lulu`) or `Amazon` (`.btn-amazon`).
- **Format tags**, left to right: `Online` → `PDF` → `EPUB` → `Paperback` → `Hardcover`.
- **Optional `.book-note`** (small italic accent-color line under the description): **only apply when the author explicitly designates the book as printed-at-cost** — this is NOT the default. The standing wording for at-cost titles is `Free to download. Printed at cost.` Currently only From the Beginning and Before I Formed You carry this note. New books default to no book-note unless the author specifies. Do not use phrases like "Not for Profit" (implies 501(c)(3)) or "Not for Resale" (contradicts the retail listing).

### Gated-access books

When a book is in review (awaiting a signed release, etc.), gate it at multiple layers for consistency:

- **Online reader**: JS prompt on every page checking a sessionStorage key (e.g. `ctm_auth`), 3-attempt lockout that bounces to `/index.html`.
- **Download buttons** on `books.html`: route through the `ctmGated(url)` helper (or a book-specific analogue) that checks the same sessionStorage key. Unlocking the reader unlocks the downloads.
- **PDF file itself**: encrypt with `pypdf` AES-256 using the same password. The PDF remains inert even if someone bypasses the JS gate or shares the URL. EPUB has no comparable encryption and is JS-gated only.

Remove all three layers together when a book goes public.
