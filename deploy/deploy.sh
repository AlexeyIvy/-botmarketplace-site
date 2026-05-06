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
for svc in botmarket-api botmarket-web botmarket-worker; do
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
# botmarket-worker hosts the funding-arb hedge runtime + the DSL evaluator
# loop. Skipping it leaves long-lived worker code stale across deploys —
# any change to botWorker.ts / hedgeBotWorker.ts / intentExecutor.ts /
# windowDetector.ts / preset evaluator does NOT take effect until the
# unit is restarted explicitly. Always restart all three.
systemctl restart botmarket-worker

# Wait for services to stabilize. With RestartSec=5s in the unit files,
# sleeping 7s ensures at least one full restart cycle has completed if
# the service is crash-looping — otherwise we'd catch the brief
# "activating" window between crash and auto-restart and report success.
# Incident 2026-05-06 (#377 hardening missing AF_NETLINK) slipped past
# the previous 3s sleep + `is-active && echo OK || echo FAIL` check
# because is-active returns 0 for "activating" state.
sleep 7

echo ""
echo "Service health check:"
DEPLOY_FAILED=0

# API: must respond with HTTP 2xx on /healthz. Curling the bound port
# is stronger than systemctl is-active because it confirms the port is
# actually open and the request handler is alive.
if curl -sf -m 5 http://127.0.0.1:4000/api/v1/healthz > /dev/null 2>&1; then
  echo "  ✓ botmarket-api → /healthz 200"
else
  echo "  ✗ botmarket-api → /healthz unreachable or non-200"
  echo "    Last 30 journal lines:"
  journalctl -u botmarket-api -n 30 --no-pager 2>&1 | sed 's/^/      /'
  DEPLOY_FAILED=1
fi

# Web: 3xx is acceptable (Next.js may redirect / to /login when
# unauthenticated), so accept any 2xx or 3xx.
WEB_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -m 5 http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [[ "$WEB_HTTP" =~ ^[23] ]]; then
  echo "  ✓ botmarket-web → / HTTP $WEB_HTTP"
else
  echo "  ✗ botmarket-web → / HTTP $WEB_HTTP"
  echo "    Last 30 journal lines:"
  journalctl -u botmarket-web -n 30 --no-pager 2>&1 | sed 's/^/      /'
  DEPLOY_FAILED=1
fi

# Worker: no HTTP endpoint. ActiveState="active" is the only OK value;
# "activating" can mean crash-loop auto-restart, so reject it.
WORKER_STATE=$(systemctl show -p ActiveState --value botmarket-worker 2>/dev/null || echo "unknown")
if [[ "$WORKER_STATE" == "active" ]]; then
  echo "  ✓ botmarket-worker → ActiveState=active"
else
  echo "  ✗ botmarket-worker → ActiveState=$WORKER_STATE"
  echo "    Last 30 journal lines:"
  journalctl -u botmarket-worker -n 30 --no-pager 2>&1 | sed 's/^/      /'
  DEPLOY_FAILED=1
fi

if [[ $DEPLOY_FAILED -eq 1 ]]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  [!] DEPLOY FAILED — services not healthy"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  One or more services are not healthy. See journal output above."
  echo "  Rollback options:"
  echo "    1. git checkout <previous-ref> && bash deploy/deploy.sh"
  echo "    2. If you tagged the previous prod state before this deploy,"
  echo "       check it out and re-run deploy.sh."
  exit 1
fi

echo ""
DEPLOYED_REF=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
echo "Deployed ref: $DEPLOYED_REF"
echo ""
echo "Done. Check logs with:"
echo "  journalctl -u botmarket-api -f"
echo "  journalctl -u botmarket-web -f"
echo "  journalctl -u botmarket-worker -f"
echo ""
echo "Run smoke tests with:"
echo "  bash deploy/smoke-test.sh"
