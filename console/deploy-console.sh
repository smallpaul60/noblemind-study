#!/bin/bash
# Deploy noblemind-console to VPS
# Usage: ./deploy-console.sh
#
# Prerequisites:
#   - Go 1.22+ installed locally (or at ~/.local/go/bin/go)
#   - SSH access to VPS as paul@198.23.134.103
#
# First-time VPS setup (run once):
#   ssh paul@198.23.134.103
#   mkdir -p ~/noblemind-console
#   openssl rand -hex 32   # generate auth token
#   echo 'CONSOLE_TOKEN=<paste-token-here>' > ~/noblemind-console/.env
#   # Download IP2Location LITE DB1 CSV (free):
#   #   https://lite.ip2location.com/database/db1-ip-country
#   # Place as ~/noblemind-console/IP2LOCATION-LITE-DB1.CSV
#   sudo cp noblemind-console.service /etc/systemd/system/
#   sudo systemctl daemon-reload
#   sudo systemctl enable noblemind-console

set -e

VPS_HOST="paul@198.23.134.103"
VPS_DIR="~/noblemind-console"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Find Go 1.22+
GO_BIN="go"
if [ -x "$HOME/.local/go/bin/go" ]; then
  GO_BIN="$HOME/.local/go/bin/go"
fi

echo "=========================================="
echo "Deploying noblemind-console"
echo "=========================================="
echo ""

# Step 1: Cross-compile for Linux amd64
echo "[1/4] Building binary..."
cd "$SCRIPT_DIR"
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 $GO_BIN build -ldflags="-s -w" -o noblemind-console .
echo "Binary built: $(ls -lh noblemind-console | awk '{print $5}')"
echo ""

# Step 2: Upload binary
echo "[2/4] Uploading to VPS..."
ssh "$VPS_HOST" "mkdir -p $VPS_DIR"
scp noblemind-console "$VPS_HOST:$VPS_DIR/noblemind-console.new"
ssh "$VPS_HOST" "mv $VPS_DIR/noblemind-console.new $VPS_DIR/noblemind-console && chmod +x $VPS_DIR/noblemind-console"
echo "Uploaded."
echo ""

# Step 3: Upload service file
echo "[3/4] Updating systemd service..."
scp noblemind-console.service "$VPS_HOST:/tmp/noblemind-console.service"
ssh "$VPS_HOST" "sudo mv /tmp/noblemind-console.service /etc/systemd/system/noblemind-console.service && sudo systemctl daemon-reload"
echo "Service updated."
echo ""

# Step 4: Restart service
echo "[4/4] Restarting service..."
ssh "$VPS_HOST" "sudo systemctl restart noblemind-console"
sleep 2
ssh "$VPS_HOST" "sudo systemctl status noblemind-console --no-pager -l" || true
echo ""

# Clean up local binary
rm -f noblemind-console

echo "=========================================="
echo "Deployment complete!"
echo ""
echo "Dashboard: https://noblemind.study/console?token=<your-token>"
echo "=========================================="
