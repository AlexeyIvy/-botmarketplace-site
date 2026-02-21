#!/usr/bin/env bash
# deploy.sh — Pull latest code, build, migrate, restart services
# Usage: bash deploy/deploy.sh [--branch <branch>]
#
# Requirements:
#   - pnpm installed globally
#   - systemd services botmarket-api and botmarket-web installed
#   - .env file present at project root

set -euo pipefail

APP_DIR="/opt/-botmarketplace-site"
BRANCH="${BRANCH:-main}"

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --branch) BRANCH="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$APP_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  BotMarketplace deploy → $BRANCH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Pull latest code
echo "[1/5] Git pull..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

# 2. Install dependencies
echo "[2/5] Installing dependencies..."
pnpm install --frozen-lockfile

# 3. Run DB migrations + regenerate Prisma client
echo "[3/5] Running DB migrations..."
pnpm run db:migrate
echo "[3/5] Regenerating Prisma client..."
pnpm --filter @botmarketplace/api exec prisma generate

# 4. Build
echo "[4/5] Building API and Web..."
pnpm run build:api
pnpm run build:web

# 5. Check critical env vars
echo "[5/5] Checking env..."
ENV_FILE="$APP_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  if ! grep -q "^BOT_WORKER_SECRET=" "$ENV_FILE" || grep -q '^BOT_WORKER_SECRET="change-me-in-production"' "$ENV_FILE"; then
    echo "  [!] WARNING: BOT_WORKER_SECRET is not set or still has placeholder value in .env"
    echo "      Worker endpoints (PATCH /state, POST /heartbeat, POST /reconcile) will be UNPROTECTED."
    echo "      Set a strong secret: echo 'BOT_WORKER_SECRET=\"$(openssl rand -hex 32)\"' >> $ENV_FILE"
  fi
fi

# 6. Restart services
echo "[6/6] Restarting services..."
systemctl restart botmarket-api
systemctl restart botmarket-web

# Wait a moment and show status
sleep 3
echo ""
echo "Service status:"
systemctl is-active botmarket-api && echo "  ✓ botmarket-api is running" || echo "  ✗ botmarket-api FAILED"
systemctl is-active botmarket-web  && echo "  ✓ botmarket-web is running"  || echo "  ✗ botmarket-web FAILED"

echo ""
echo "Done. Check logs with:"
echo "  journalctl -u botmarket-api -f"
echo "  journalctl -u botmarket-web -f"
echo ""
echo "Run smoke tests with:"
echo "  bash deploy/smoke-test.sh"
