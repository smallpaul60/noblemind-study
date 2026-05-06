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
  "$SITE_DIR/" "$VPS_HOST:$VPS_DIR/"
echo "Files synced."
echo ""

# Step 3: Add to IPFS on remote Kubo node
echo "[3/4] Adding to IPFS on VPS..."
CID=$(SSH_AUTH_SOCK= ssh -i "$VPS_SSH_KEY" "$VPS_HOST" "cd $VPS_DIR && ipfs add -r -Q --pin=true .")
echo "CID: $CID"
echo ""

# Step 4: Publish to IPNS
echo "[4/4] Publishing to IPNS..."
SSH_AUTH_SOCK= ssh -i "$VPS_SSH_KEY" "$VPS_HOST" "ipfs name publish --key=$IPNS_KEY /ipfs/$CID"
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
