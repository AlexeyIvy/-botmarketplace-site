#!/usr/bin/env bash
# setup.sh — First-time VPS setup
# Run ONCE to install systemd units and nginx config.
# After this, use deploy.sh for all subsequent deploys.
#
# Usage: bash deploy/setup.sh

set -euo pipefail

APP_DIR="/opt/-botmarketplace-site"
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

# 1. System dependencies
echo "[0/4] Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends postgresql-client
echo "      postgresql-client installed (required by backup.sh)"

# 2. Install systemd services
echo "[1/4] Installing systemd services..."
cp "$APP_DIR/deploy/botmarket-api.service" /etc/systemd/system/botmarket-api.service
cp "$APP_DIR/deploy/botmarket-web.service" /etc/systemd/system/botmarket-web.service
cp "$APP_DIR/deploy/botmarket-backup.service" /etc/systemd/system/botmarket-backup.service
cp "$APP_DIR/deploy/botmarket-backup.timer"   /etc/systemd/system/botmarket-backup.timer
systemctl daemon-reload
systemctl enable botmarket-api botmarket-web
systemctl enable --now botmarket-backup.timer
echo "      botmarket-api, botmarket-web enabled"
echo "      botmarket-backup.timer enabled (daily 03:00)"

# 3. Install nginx config
echo "[2/4] Installing nginx config..."
NGINX_ENABLED=0
for f in "/etc/nginx/sites-enabled/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN.conf" /etc/nginx/sites-enabled/botmarketplace.conf; do
  if [[ -e "$f" ]]; then
    echo "      Nginx config already active at $f — skipping install"
    NGINX_ENABLED=1
    break
  fi
done
if [[ $NGINX_ENABLED -eq 0 ]]; then
  cp "$APP_DIR/deploy/nginx.conf" "/etc/nginx/sites-available/$DOMAIN"
  ln -s "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
  nginx -t
  echo "      Nginx config installed and tested"
fi

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
systemctl is-active botmarket-backup.timer && echo "  ✓ botmarket-backup.timer" || echo "  ✗ botmarket-backup.timer NOT active"

echo ""
echo "Setup complete!"
echo ""
echo "Next: configure Let's Encrypt TLS if not done yet:"
echo "  certbot --nginx -d $DOMAIN -d www.$DOMAIN"
