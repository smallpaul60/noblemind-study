#!/bin/bash
# VPS Security Hardening Script
# Run this on the VPS: ssh paul@198.23.134.103
# Then: bash security-hardening.sh
# Requires sudo access.

set -e

echo "=========================================="
echo "VPS Security Hardening"
echo "=========================================="
echo ""

# 1. Fix TLS - remove deprecated TLS 1.0 and 1.1
echo "[1/6] Removing TLS 1.0 and 1.1 from nginx..."
sudo sed -i 's/ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;/ssl_protocols TLSv1.2 TLSv1.3;/' /etc/nginx/nginx.conf
echo "  Done."

# 2. Add HSTS header to noblemind.study
echo "[2/6] Adding HSTS header to noblemind.study..."
if ! grep -q 'Strict-Transport-Security' /etc/nginx/sites-enabled/noblemind.study; then
  sudo sed -i '/X-Content-Type-Options/a\    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;' /etc/nginx/sites-enabled/noblemind.study
  echo "  Done."
else
  echo "  Already present, skipping."
fi

# 3. Add HSTS and security headers to StoryLock frontend
echo "[3/6] Adding HSTS and security headers to StoryLock frontend..."
if ! grep -q 'Strict-Transport-Security' /etc/nginx/sites-enabled/storylock-frontend.conf; then
  sudo sed -i '/location \/ {/i\    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;\n    add_header X-Content-Type-Options "nosniff" always;\n    add_header X-Frame-Options "SAMEORIGIN" always;\n    add_header X-XSS-Protection "1; mode=block" always;' /etc/nginx/sites-enabled/storylock-frontend.conf
  echo "  Done."
else
  echo "  Already present, skipping."
fi

# 4. Add IPFS API block to ipfs.noblemind.study
echo "[4/6] Adding IPFS API block to ipfs.noblemind.study..."
if ! grep -q 'api/v0' /etc/nginx/sites-enabled/ipfs.noblemind.study; then
  sudo sed -i '/location \/ {/i\    location /api/v0 { return 404; }' /etc/nginx/sites-enabled/ipfs.noblemind.study
  echo "  Done."
else
  echo "  Already present, skipping."
fi

# 5. Tighten analytics DB permissions
echo "[5/6] Tightening analytics DB permissions..."
if [ -f ~/noblemind-console/analytics.db ]; then
  chmod 600 ~/noblemind-console/analytics.db
  echo "  Done."
else
  echo "  DB not found, skipping."
fi

# 6. Test and reload nginx
echo "[6/6] Testing nginx configuration..."
sudo nginx -t
if [ $? -eq 0 ]; then
  echo "  Config OK. Reloading nginx..."
  sudo systemctl reload nginx
  echo "  Done."
else
  echo "  ERROR: nginx config test failed. NOT reloading."
  echo "  Fix the config and run: sudo nginx -t && sudo systemctl reload nginx"
  exit 1
fi

echo ""
echo "=========================================="
echo "Security hardening complete."
echo ""
echo "Remaining manual step:"
echo "  Run system updates: sudo apt update && sudo apt upgrade -y"
echo "  Then reboot if kernel was updated: sudo reboot"
echo "=========================================="
