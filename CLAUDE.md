# Noble Mind Study Tool — Project Context

## Architecture

Single-page Progressive Web App (PWA) for Bible study. Entirely client-side — no backend server, no build step, no package manager. The main application lives in one file:

- **`Noble_Mind_Study_Tool_v2.html`** (~6,300 lines) — The entire app: UI, logic, styles, all inline.
- **`index.html`** — Landing page with links and PWA install prompt.
- **`user-guide.html`** — Comprehensive user guide (opens in new tab from study tool).
- **`sw.js`** — Service worker (cache-first strategy, version `v52`). Bump the version when updating cached assets.
- **`nm-beacon.js`** — Client-side analytics beacon (~40 lines). POSTs to `/api/analytics/event`. No cookies, no fingerprinting.
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
- **Privacy model:** Raw IPs never stored. SHA-256(IP + daily_salt) truncated to 16 hex chars. No cookies, no localStorage, no fingerprinting. Daily salt rotation prevents cross-day correlation.
- **VPS directory:** `/home/paul/noblemind-console/` (separate from static site).
- **Database:** SQLite at `/home/paul/noblemind-console/analytics.db`. Raw data purged after 90 days.
- **Auth:** Token-based via `?token=` query param or `Authorization: Bearer` header. Token stored in `/home/paul/noblemind-console/.env`.
- **Nginx:** Proxies `/api/analytics/*` and `/console` to `:3001`. Static files served directly.

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
