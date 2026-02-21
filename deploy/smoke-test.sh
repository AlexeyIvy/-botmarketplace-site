#!/usr/bin/env bash
# smoke-test.sh — MVP release smoke tests
# Usage: bash deploy/smoke-test.sh [--base-url https://botmarketplace.store]
# Exit code: 0 = all passed, 1 = failures found

set -euo pipefail

BASE_URL="${BASE_URL:-https://botmarketplace.store}"
TEST_EMAIL="smoke_$(date +%s)@test.com"
TEST_PASS="Smoke1234!"
PASS=0
FAIL=0

# ─── helpers ────────────────────────────────────────────────────────────────

green()  { printf "\033[32m✓ %s\033[0m\n" "$1"; }
red()    { printf "\033[31m✗ %s\033[0m\n" "$1"; }
header() { printf "\n\033[1m%s\033[0m\n" "$1"; }

check() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    green "$label"
    ((++PASS))
  else
    red "$label (expected: $expected, got: $actual)"
    ((++FAIL))
  fi
}

check_contains() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -q "$needle"; then
    green "$label"
    ((++PASS))
  else
    red "$label (expected to contain: $needle)"
    ((++FAIL))
  fi
}

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --base-url) BASE_URL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  BotMarketplace Smoke Tests"
echo "  Target: $BASE_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── 1. Infrastructure ───────────────────────────────────────────────────────
header "1. Infrastructure"

HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/healthz")
check "GET /api/v1/healthz → 200" "200" "$HEALTH"

READYZ=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/readyz")
check "GET /api/v1/readyz → 200" "200" "$READYZ"

# ─── 2. UI pages ─────────────────────────────────────────────────────────────
header "2. UI pages"

for page in /login /register /lab /factory; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$page")
  check "GET $page → 200" "200" "$CODE"
done

# ─── 3. Auth — register + login ──────────────────────────────────────────────
header "3. Auth"

REG=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}")

TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4) || true
WS_ID=$(echo "$REG" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4) || true

if [[ -n "$TOKEN" ]]; then
  green "POST /auth/register → accessToken received"
  ((++PASS))
else
  red "POST /auth/register → no accessToken (response: $REG)"
  ((++FAIL))
fi

if [[ -n "$WS_ID" ]]; then
  green "POST /auth/register → workspaceId received"
  ((++PASS))
else
  red "POST /auth/register → no workspaceId"
  ((++FAIL))
fi

LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}")

LOGIN_TOKEN=$(echo "$LOGIN" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4) || true
if [[ -n "$LOGIN_TOKEN" ]]; then
  green "POST /auth/login → accessToken received"
  ((++PASS))
else
  red "POST /auth/login → failed (response: $LOGIN)"
  ((++FAIL))
fi

# Wrong password → 401
WRONG=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"wrongpass\"}")
check "POST /auth/login wrong password → 401" "401" "$WRONG"

# ─── 4. Protected endpoints ───────────────────────────────────────────────────
header "4. Auth protection"

ME_AUTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN")
check "GET /auth/me with token → 200" "200" "$ME_AUTH"

ME_UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/me")
check "GET /auth/me without token → 401" "401" "$ME_UNAUTH"

# ─── 5. Rate limiting ─────────────────────────────────────────────────────────
header "5. Rate limiting"

# Hit /auth/register 7 times quickly — should get 429 on 6th+ attempt
RL_HIT=0
for i in $(seq 1 7); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"rl_test_${i}_$(date +%s)@test.com\",\"password\":\"Test1234!\"}")
  if [[ "$CODE" == "429" ]]; then
    RL_HIT=1
    break
  fi
done
if [[ $RL_HIT -eq 1 ]]; then
  green "Rate limiting on /auth/register → 429 triggered"
  ((++PASS))
else
  red "Rate limiting on /auth/register → 429 NOT triggered after 7 requests"
  ((++FAIL))
fi

# ─── 6. Stop-all endpoint ─────────────────────────────────────────────────────
header "6. Stop-all endpoint"

STOP_ALL=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/runs/stop-all" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
# 200 = success (0 active runs is fine), 4xx = problem
if [[ "$STOP_ALL" == "200" ]]; then
  green "POST /runs/stop-all → 200"
  ((++PASS))
else
  red "POST /runs/stop-all → $STOP_ALL (expected 200)"
  ((++FAIL))
fi

# ─── 7. Worker endpoint auth ─────────────────────────────────────────────────
# These three endpoints are worker-to-API (machine-to-machine) and must NOT be
# freely callable by anyone with just a workspace ID.
# When BOT_WORKER_SECRET is set (production): expect 401 without the secret.
# When BOT_WORKER_SECRET is unset (dev):       endpoint falls through to normal
#   workspace/run validation, so we accept any non-500 response.
header "7. Worker endpoint auth"

WORKER_SECRET="${BOT_WORKER_SECRET:-}"

# PATCH /runs/:runId/state — no auth header
PATCH_STATE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH \
  "$BASE_URL/api/v1/runs/smoke-fake-id/state" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"state":"RUNNING"}')
if [[ -n "$WORKER_SECRET" ]]; then
  check "PATCH /runs/:id/state without secret → 401" "401" "$PATCH_STATE"
else
  if [[ "$PATCH_STATE" != "5"* ]]; then
    green "PATCH /runs/:id/state (dev, no secret) → $PATCH_STATE (no 5xx)"
    ((++PASS))
  else
    red "PATCH /runs/:id/state → unexpected $PATCH_STATE"
    ((++FAIL))
  fi
fi

# POST /runs/:runId/heartbeat — no auth header
HEARTBEAT=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "$BASE_URL/api/v1/runs/smoke-fake-id/heartbeat" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"workerId":"smoke-test"}')
if [[ -n "$WORKER_SECRET" ]]; then
  check "POST /runs/:id/heartbeat without secret → 401" "401" "$HEARTBEAT"
else
  if [[ "$HEARTBEAT" != "5"* ]]; then
    green "POST /runs/:id/heartbeat (dev, no secret) → $HEARTBEAT (no 5xx)"
    ((++PASS))
  else
    red "POST /runs/:id/heartbeat → unexpected $HEARTBEAT"
    ((++FAIL))
  fi
fi

# POST /runs/reconcile — no auth header
RECONCILE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "$BASE_URL/api/v1/runs/reconcile" \
  -H "X-Workspace-Id: $WS_ID")
if [[ -n "$WORKER_SECRET" ]]; then
  check "POST /runs/reconcile without secret → 401" "401" "$RECONCILE"
else
  if [[ "$RECONCILE" != "5"* ]]; then
    green "POST /runs/reconcile (dev, no secret) → $RECONCILE (no 5xx)"
    ((++PASS))
  else
    red "POST /runs/reconcile → unexpected $RECONCILE"
    ((++FAIL))
  fi
fi

# ─── 8. Bot worker ───────────────────────────────────────────────────────────
header "8. Bot Worker"

if (set +o pipefail; journalctl -u botmarket-api --no-pager --output=cat 2>/dev/null | grep -q "botWorker.*started" 2>/dev/null); then
  green "Bot worker started line found in API logs"
  ((++PASS))
else
  red "Bot worker start line NOT found in API logs"
  ((++FAIL))
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL=$((PASS + FAIL))
echo "  Results: $PASS/$TOTAL passed"
if [[ $FAIL -eq 0 ]]; then
  printf "  \033[32mALL TESTS PASSED ✓\033[0m\n"
else
  printf "  \033[31m$FAIL TEST(S) FAILED ✗\033[0m\n"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $FAIL
