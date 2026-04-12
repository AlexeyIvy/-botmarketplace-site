#!/usr/bin/env bash
# deploy.sh — Pull latest code, build, migrate, restart services
# Usage: bash deploy/deploy.sh [--branch <branch>] [--ref <tag-or-sha>]
#
# Examples:
#   bash deploy/deploy.sh                     # deploy latest main
#   bash deploy/deploy.sh --branch my-branch  # deploy a branch
#   bash deploy/deploy.sh --ref v0.1.0-rc1    # deploy a specific tag
#   bash deploy/deploy.sh --ref abc1234def    # deploy a specific commit SHA
#
# Requirements:
#   - pnpm installed globally
#   - systemd services botmarket-api and botmarket-web installed
#   - .env file present at project root

set -euo pipefail

APP_DIR="/opt/-botmarketplace-site"
BRANCH="${BRANCH:-main}"
REF=""  # tag or SHA; if set, overrides BRANCH for checkout

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --branch) BRANCH="$2"; shift 2 ;;
    --ref)    REF="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$APP_DIR"

if [[ -n "$REF" ]]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  BotMarketplace deploy → ref: $REF"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  BotMarketplace deploy → $BRANCH"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

# 1. Pull latest code
echo "[1/7] Git fetch + checkout..."
git fetch origin --tags
if [[ -n "$REF" ]]; then
  # Detached HEAD at tag/SHA — reproducible, pinned deploy
  git checkout "$REF"
else
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
fi

# 2. Install dependencies
echo "[2/7] Installing dependencies..."
pnpm install --frozen-lockfile

# 3. Run DB migrations + regenerate Prisma client
echo "[3/7] Running DB migrations..."
pnpm run db:migrate
echo "[3/7] Regenerating Prisma client..."
pnpm --filter @botmarketplace/api exec prisma generate

# 4. Build
echo "[4/7] Building API and Web..."
pnpm run build:api
pnpm run build:web

# 5. Check critical env vars
echo "[5/7] Checking env..."
ENV_FILE="$APP_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  if ! grep -q "^BOT_WORKER_SECRET=" "$ENV_FILE" || grep -q '^BOT_WORKER_SECRET="change-me-in-production"' "$ENV_FILE"; then
    echo "  [!] WARNING: BOT_WORKER_SECRET is not set or still has placeholder value in .env"
    echo "      Worker endpoints (PATCH /state, POST /heartbeat, POST /reconcile) will be UNPROTECTED."
    echo "      Set a strong secret: echo 'BOT_WORKER_SECRET=\"$(openssl rand -hex 32)\"' >> $ENV_FILE"
  fi
fi

# 6. Sync systemd units (reinstall if deploy/*.service changed in the repo)
echo "[6/7] Syncing systemd units..."
UNITS_CHANGED=0
for svc in botmarket-api botmarket-web; do
  src="$APP_DIR/deploy/$svc.service"
  dst="/etc/systemd/system/$svc.service"
  if [[ -f "$src" ]] && ! cmp -s "$src" "$dst" 2>/dev/null; then
    cp "$src" "$dst"
    echo "      updated $dst"
    UNITS_CHANGED=1
  fi
done
if [[ $UNITS_CHANGED -eq 1 ]]; then
  systemctl daemon-reload
  echo "      systemd daemon reloaded"
fi

# 7. Restart services
echo "[7/7] Restarting services..."
systemctl restart botmarket-api
systemctl restart botmarket-web

# Wait a moment and show status
sleep 3
echo ""
echo "Service status:"
systemctl is-active botmarket-api && echo "  ✓ botmarket-api is running" || echo "  ✗ botmarket-api FAILED"
systemctl is-active botmarket-web  && echo "  ✓ botmarket-web is running"  || echo "  ✗ botmarket-web FAILED"

echo ""
DEPLOYED_REF=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
echo "Deployed ref: $DEPLOYED_REF"
echo ""
echo "Done. Check logs with:"
echo "  journalctl -u botmarket-api -f"
echo "  journalctl -u botmarket-web -f"
echo ""
echo "Run smoke tests with:"
echo "  bash deploy/smoke-test.sh"
