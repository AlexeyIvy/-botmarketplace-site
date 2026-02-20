#!/usr/bin/env bash
# setup.sh — First-time VPS setup
# Run ONCE to install systemd units and nginx config.
# After this, use deploy.sh for all subsequent deploys.
#
# Usage: bash deploy/setup.sh

set -euo pipefail

APP_DIR="/home/user/-botmarketplace-site"
DOMAIN="botmarketplace.store"

cd "$APP_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  BotMarketplace — First-time setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Check .env exists
if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "[!] .env file not found at $APP_DIR/.env"
  echo "    Copy .env.example and fill in the values:"
  echo "    cp .env.example .env && nano .env"
  exit 1
fi
echo "[✓] .env found"

# 2. Install systemd services
echo "[1/4] Installing systemd services..."
cp "$APP_DIR/deploy/botmarket-api.service" /etc/systemd/system/botmarket-api.service
cp "$APP_DIR/deploy/botmarket-web.service" /etc/systemd/system/botmarket-web.service
systemctl daemon-reload
systemctl enable botmarket-api botmarket-web
echo "      botmarket-api and botmarket-web enabled"

# 3. Install nginx config
echo "[2/4] Installing nginx config..."
cp "$APP_DIR/deploy/nginx.conf" "/etc/nginx/sites-available/$DOMAIN"
if [[ ! -L "/etc/nginx/sites-enabled/$DOMAIN" ]]; then
  ln -s "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
fi
nginx -t
echo "      Nginx config installed and tested"

# 4. Install pnpm dependencies and build
echo "[3/4] Installing deps and building..."
pnpm install --frozen-lockfile
pnpm run db:migrate
pnpm run build:api
pnpm run build:web

# 5. Start services
echo "[4/4] Starting services..."
systemctl start botmarket-api
systemctl start botmarket-web
systemctl reload nginx

sleep 3
echo ""
echo "Status:"
systemctl is-active botmarket-api && echo "  ✓ botmarket-api" || echo "  ✗ botmarket-api FAILED — check: journalctl -u botmarket-api -n 50"
systemctl is-active botmarket-web  && echo "  ✓ botmarket-web"  || echo "  ✗ botmarket-web FAILED  — check: journalctl -u botmarket-web -n 50"

echo ""
echo "Setup complete!"
echo ""
echo "Next: configure Let's Encrypt TLS if not done yet:"
echo "  certbot --nginx -d $DOMAIN -d www.$DOMAIN"
