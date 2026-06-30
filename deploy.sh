#!/bin/bash
# Deploy noblemind.study to VPS and IPFS/IPNS
# Usage: ./deploy.sh

set -e

VPS_HOST="paul@198.23.134.103"
VPS_SSH_KEY="$HOME/.ssh/storylock_vps"
VPS_DIR="~/noblemind-study"
IPNS_KEY="noblemind"
IPNS_ADDR="k51qzi5uqu5dg9bleldhzzzxmydvtmntfl2lajle3jfi8wv58xdc5jw0i6tunj"
SITE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "Deploying noblemind.study"
echo "=========================================="
echo ""

# Step 1a: Rebuild Apostle Paul timeline PDFs from the live HTML so the
# downloadable PDFs always match what's online.
echo "[1a/4] Rebuilding Apostle Paul timeline PDFs..."
python3 "$SITE_DIR/tools/build_timeline_pdfs.py"
echo ""

# Step 1b: Rebuild OT-timeline spoke PDFs the same way.
echo "[1b/4] Rebuilding OT-spoke PDFs..."
python3 "$SITE_DIR/tools/build_spoke_pdfs.py"
echo ""

# Step 1c: Rebuild the offline interactive-timeline ZIP (timeline + all
# spokes, fonts embedded) so the download always matches what's online.
echo "[1c/4] Rebuilding offline timeline bundle..."
python3 "$SITE_DIR/tools/build_timeline_bundle.py"
echo ""

# Step 1: Regenerate sitemap.xml and robots.txt so <lastmod> timestamps stay current
echo "[1/4] Regenerating sitemap.xml and robots.txt..."
python3 "$SITE_DIR/tools/gen_sitemap.py"
echo ""

# Step 2: Sync files to VPS
# --delete-excluded actively removes anything in the exclude list from the
# VPS, so if a draft or internal doc is added to the list later it will be
# purged on the next deploy rather than lingering from a prior sync.
echo "[2/4] Syncing files to VPS..."
SSH_AUTH_SOCK= rsync -avz --delete --delete-excluded --chmod=D755,F644 \
  -e "ssh -i $VPS_SSH_KEY" \
  --exclude='.git' \
  --exclude='*.py' \
  --exclude='maps/data/*.jsonl' \
  --exclude='PRINCIPLES.md' \
  --exclude='console/' \
  --exclude='cloud-tts/' \
  --exclude='CLAUDE.md' \
  --exclude='Bible_Study_Principles_Comprehensive_04-20-2026.md' \
  --exclude='NobleMind_Build_Plan_for_Claude_Code.md' \
  --exclude='infant_baptism_content_draft_rev2.md' \
  --exclude='admin/' \
  --exclude='__pycache__' \
  --exclude='.claude/' \
  --exclude='WhyTheDivision/Chapter_*.md' \
  --exclude='WhyTheDivision/Preface.md' \
  --exclude='MadeNotWritten/Made_Not_Written_*.md' \
  --exclude='WhyTheDivision/PROJECT_HANDOFF.md' \
  --exclude='WhyTheDivision/ai_guidance_note_handoff.md' \
  --exclude='WhyTheDivision/principles_addition_emphasis_not_exhaustion.md' \
  --exclude='WhyTheDivision/Debates_Notes/' \
  --exclude='WhyTheDivision/Resource Appendix_*.pdf' \
  --exclude='TheGodWhoShowedUp/em-dash_alt-0151.odt' \
  --exclude='A_Good_Name/A_GOOD_NAME_CH9_HANDOFF.md' \
  --exclude='A_Good_Name/AGoodName_ClaudeCode_Handoff.md' \
  --exclude='A_Good_Name/AGoodName_Chapter9.md' \
  --exclude='A_Good_Name/AGoodName_Chapter9.docx' \
  --exclude='A_Good_Name/YourNameMeansEverything_Special_Edition_*.pdf' \
  --exclude='A_Good_Name/Message-to-Hagen.pdf' \
  --exclude='*hardcover-template.pdf' \
  --exclude='*paperback-cover-template.pdf' \
  --exclude='*Edition-Jacket.pdf' \
  --exclude='*_Lulu_Metadata.docx' \
  --exclude='strength_and_dignity/' \
  --exclude='a_new_and_living_way/' \
  --exclude='archive/' \
  --exclude='design-refs/' \
  --exclude='Works_In_Progress/' \
  --exclude='*.wav' \
  --exclude='Audio Files/' \
  --exclude='Text Files for Audio/' \
  --exclude='text-files-for-audio/' \
  --exclude='audio-files-for-book/' \
  --exclude='audio-files/' \
  --exclude='apostle-paul/paul-*-journey.png' \
  --exclude='apostle-paul/paul-taken-to-rome.png' \
  --exclude='apostle-paul/SPOKE_PLAN.md' \
  --exclude='old-testament-timeline/unfolding-of-gods-plan.pdf' \
  --exclude='old-testament-timeline/the-3-cycle-approach.pdf' \
  --exclude='old-testament-timeline/*.md' \
  "$SITE_DIR/" "$VPS_HOST:$VPS_DIR/"
echo "Files synced."
echo ""

# Step 3: Add to IPFS on remote Kubo node
echo "[3/4] Adding to IPFS on VPS..."
CID=$(SSH_AUTH_SOCK= ssh -i "$VPS_SSH_KEY" "$VPS_HOST" "cd $VPS_DIR && ipfs add -r -Q --pin=true .")
echo "CID: $CID"
echo ""

# Step 4: Publish to IPNS
# `ipfs name publish` updates the LOCAL IPNS record immediately, then tries to
# propagate it across the DHT — and that DHT put can hang indefinitely (a known
# Kubo wart; it once blocked a deploy for ~2h). Wrap it in `timeout` so the
# deploy never stalls: the local record (and thus the served content) is already
# updated, and the daemon re-announces to the DHT periodically on its own.
echo "[4/4] Publishing to IPNS..."
SSH_AUTH_SOCK= ssh -i "$VPS_SSH_KEY" "$VPS_HOST" "timeout 180 ipfs name publish --key=$IPNS_KEY /ipfs/$CID" \
  || echo "WARNING: IPNS publish did not confirm within 180s (local record updated; DHT propagation continues in the background)."
echo ""

echo "=========================================="
echo "Deployment complete!"
echo ""
echo "IPFS CID: $CID"
echo "IPNS Key: $IPNS_ADDR"
echo ""
echo "Gateway URLs:"
echo "  https://noblemind.study"
echo "  https://ipfs.io/ipns/$IPNS_ADDR"
echo "  https://ipfs.io/ipfs/$CID"
echo "=========================================="
