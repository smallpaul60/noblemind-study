#!/bin/bash
# Deploy noblemind.study to VPS and IPFS/IPNS
# Usage: ./deploy.sh

set -e

VPS_HOST="paul@198.23.134.103"
VPS_DIR="~/noblemind-study"
IPNS_KEY="noblemind"
IPNS_ADDR="k51qzi5uqu5dg9bleldhzzzxmydvtmntfl2lajle3jfi8wv58xdc5jw0i6tunj"
SITE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "Deploying noblemind.study"
echo "=========================================="
echo ""

# Step 1: Sync files to VPS
echo "[1/3] Syncing files to VPS..."
rsync -avz --delete --chmod=D755,F644 \
  --exclude='.git' \
  --exclude='*.py' \
  --exclude='PRINCIPLES.md' \
  --exclude='console/' \
  "$SITE_DIR/" "$VPS_HOST:$VPS_DIR/"
echo "Files synced."
echo ""

# Step 2: Add to IPFS on remote Kubo node
echo "[2/3] Adding to IPFS on VPS..."
CID=$(ssh "$VPS_HOST" "cd $VPS_DIR && ipfs add -r -Q --pin=true .")
echo "CID: $CID"
echo ""

# Step 3: Publish to IPNS
echo "[3/3] Publishing to IPNS..."
ssh "$VPS_HOST" "ipfs name publish --key=$IPNS_KEY /ipfs/$CID"
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
