#!/bin/bash
# Deploy noblemind.study to VPS
# Usage: ./deploy.sh
#
# 2026-07-16: IPFS/IPNS publishing REMOVED (was steps 3-4). It was never a real
# backup — the pins lived on the same VPS that serves the site (git + GitHub is
# the backup) — and the accumulated historical pins kept accidentally-published
# files fetchable forever. The Kubo node's old noblemind pins were removed and
# garbage-collected the same day.

set -e

VPS_HOST="paul@198.23.134.103"
VPS_SSH_KEY="$HOME/.ssh/storylock_vps"
VPS_DIR="~/noblemind-study"
SITE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "Deploying noblemind.study"
echo "=========================================="
echo ""

# Step 1a: Rebuild Apostle Paul timeline PDFs from the live HTML so the
# downloadable PDFs always match what's online.
echo "[1a/2] Rebuilding Apostle Paul timeline PDFs..."
python3 "$SITE_DIR/tools/build_timeline_pdfs.py"
echo ""

# Step 1b: Rebuild OT-timeline spoke PDFs the same way.
echo "[1b/2] Rebuilding OT-spoke PDFs..."
python3 "$SITE_DIR/tools/build_spoke_pdfs.py"
echo ""

# Step 1c: Rebuild the offline interactive-timeline ZIP (timeline + all
# spokes, fonts embedded) so the download always matches what's online.
echo "[1c/2] Rebuilding offline timeline bundle..."
python3 "$SITE_DIR/tools/build_timeline_bundle.py"
echo ""

# Step 1d: Regenerate sitemap.xml and robots.txt so <lastmod> timestamps stay current
echo "[1d/2] Regenerating sitemap.xml and robots.txt..."
python3 "$SITE_DIR/tools/gen_sitemap.py"
echo ""

# Step 1e: Backfill social-card (OG/Twitter) meta into any indexable content
# page that lacks it. Idempotent — only touches pages missing og:title, so it's
# a no-op once backfilled and just covers newly added/regenerated book pages.
echo "[1e/2] Backfilling OG/social-card meta on content pages..."
python3 "$SITE_DIR/tools/gen_og_tags.py"
echo ""

# Step 2: Sync files to VPS
# --delete-excluded actively removes anything in the exclude list from the
# VPS, so if a draft or internal doc is added to the list later it will be
# purged on the next deploy rather than lingering from a prior sync.
#
# PRIVATE-BY-DEFAULT (2026-07-16 root sweep): whole file types that are never
# site content are excluded globally (*.md, *.docx, *.odt, *.py, *.sh,
# *.backup*, *.wav). A new draft, handoff, script, or manuscript is therefore
# private automatically — nobody has to remember to add an exclude line. The
# TWO served exceptions (the principles markdowns: _public is linked from
# principles.html, _full is fetched by the Study Tool and precached by sw.js)
# are re-included explicitly; rsync include lines must come BEFORE the exclude
# that would otherwise match them. PDFs stay served by default (books and
# timelines ARE the product), so private PDFs still need explicit excludes below.
echo "[2/2] Syncing files to VPS..."
SSH_AUTH_SOCK= rsync -avz --delete --delete-excluded --chmod=D755,F644 \
  -e "ssh -i $VPS_SSH_KEY" \
  --exclude='.git' \
  --include='data/principles_public.md' \
  --include='data/principles_full.md' \
  --exclude='*.md' \
  --exclude='*.docx' \
  --exclude='*.odt' \
  --exclude='*.py' \
  --exclude='*.sh' \
  --exclude='*.backup*' \
  --exclude='*.wav' \
  --exclude='.gitignore' \
  --exclude='tools/book-config-generator.html' \
  --exclude='tools/*.js' \
  --exclude='strongs-dictionary.xhtml' \
  --exclude='maps/data/*.jsonl' \
  --exclude='console/' \
  --exclude='cloud-tts/' \
  --exclude='admin/' \
  --exclude='__pycache__' \
  --exclude='.claude/' \
  --exclude='archive/' \
  --exclude='design-refs/' \
  --exclude='Works_In_Progress/' \
  --exclude='StraitWay-Enhanced/The_Strait_Way_Archive.html' \
  --exclude='WhyTheDivision/Debates_Notes/' \
  --exclude='WhyTheDivision/Resource Appendix_*.pdf' \
  --exclude='A_Good_Name/YourNameMeansEverything_Special_Edition_*.pdf' \
  --exclude='A_Good_Name/Message-to-Hagen.pdf' \
  --exclude='*hardcover-template.pdf' \
  --exclude='*paperback-cover-template.pdf' \
  --exclude='*Edition-Jacket.pdf' \
  --exclude='Audio Files/' \
  --exclude='Text Files for Audio/' \
  --exclude='text-files-for-audio/' \
  --exclude='audio-files-for-book/' \
  --exclude='audio-files/' \
  --exclude='apostle-paul/paul-*-journey.png' \
  --exclude='apostle-paul/paul-taken-to-rome.png' \
  --exclude='old-testament-timeline/unfolding-of-gods-plan.pdf' \
  --exclude='old-testament-timeline/the-3-cycle-approach.pdf' \
  "$SITE_DIR/" "$VPS_HOST:$VPS_DIR/"
echo "Files synced."
echo ""

echo "=========================================="
echo "Deployment complete!"
echo ""
echo "  https://noblemind.study"
echo "=========================================="
