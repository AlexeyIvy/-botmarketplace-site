#!/usr/bin/env bash
# smoke-test.sh — MVP release smoke tests
# Usage: bash deploy/smoke-test.sh [--base-url https://botmarketplace.store]
# Exit code: 0 = all passed, >0 = number of failures
#
# Design notes:
#   - No set -e: each check is independent; failures accumulate
#   - Rate limit section checks headers only — does NOT exhaust quota
#   - Auth section: register is idempotent (201 or 409 → login to get token)

BASE_URL="${BASE_URL:-https://botmarketplace.store}"
# Fixed email so re-runs hit 409 (idempotent) instead of new registrations
TEST_EMAIL="smoke-ci@botmarketplace.store"
TEST_PASS="Smoke1234!"
PASS=0
FAIL=0

# ─── helpers ────────────────────────────────────────────────────────────────

green()  { printf "\033[32m✓ %s\033[0m\n" "$1"; }
red()    { printf "\033[31m✗ %s\033[0m\n" "$1"; }
header() { printf "\n\033[1m%s\033[0m\n" "$1"; }

pass() { green "$1"; PASS=$((PASS + 1)); }
fail() { red "$1";   FAIL=$((FAIL + 1)); }

check() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then pass "$label"
  else fail "$label (expected=$expected, got=$actual)"; fi
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

check "GET /api/v1/healthz → 200" "200" \
  "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/healthz")"

check "GET /api/v1/readyz → 200" "200" \
  "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/readyz")"

# ─── 2. UI pages ─────────────────────────────────────────────────────────────
header "2. UI pages"

for page in /login /register /lab /factory; do
  check "GET $page → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$page")"
done

# ─── 3. Auth ─────────────────────────────────────────────────────────────────
header "3. Auth"

# Register — treat 201 (created) and 409 (already exists) as success
# This makes the test idempotent across multiple runs
REG_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}")

if [[ "$REG_CODE" == "201" || "$REG_CODE" == "409" ]]; then
  pass "POST /auth/register → $REG_CODE (user exists or created)"
else
  fail "POST /auth/register → $REG_CODE (expected 201 or 409)"
fi

# Login with the fixed test account
LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}")
TOKEN=$(echo "$LOGIN" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4 || true)
WS_ID=$(echo "$LOGIN"  | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4 || true)

if [[ -n "$TOKEN" ]]; then pass "POST /auth/login → accessToken received"
else                        fail "POST /auth/login → no accessToken (response: $LOGIN)"; fi

# Wrong password → 401
check "POST /auth/login wrong password → 401" "401" \
  "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"wrongpass\"}")"

# ─── 4. Auth protection ───────────────────────────────────────────────────────
header "4. Auth protection"

if [[ -n "$TOKEN" ]]; then
  check "GET /auth/me with token → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/me" \
       -H "Authorization: Bearer $TOKEN")"
else
  fail "GET /auth/me with token → skipped (no token)"
fi

check "GET /auth/me without token → 401" "401" \
  "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/me")"

# ─── 5. Rate limiting ─────────────────────────────────────────────────────────
header "5. Rate limiting"

# Check that X-RateLimit-Limit header is present — confirms plugin is active.
# We do NOT hammer new registrations to avoid exhausting the 15-min window.
RL_HEADER=$(curl -s -I "$BASE_URL/api/v1/healthz" | grep -i "x-ratelimit-limit" || true)

if [[ -n "$RL_HEADER" ]]; then
  pass "Rate limiting active — X-RateLimit-Limit header present"
else
  fail "Rate limiting header NOT found (plugin may not be registered)"
fi

# Also check that 429 response format is correct when rate limit IS hit.
# We reuse any 429 already present from auth register if we got one.
if [[ "$REG_CODE" == "429" ]]; then
  pass "Rate limiting 429 confirmed (register was already rate-limited)"
fi

# ─── 6. Stop-all endpoint ─────────────────────────────────────────────────────
header "6. Stop-all endpoint"

if [[ -n "$WS_ID" ]]; then
  check "POST /runs/stop-all → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" \
       -X POST "$BASE_URL/api/v1/runs/stop-all" \
       -H "X-Workspace-Id: $WS_ID")"
else
  fail "POST /runs/stop-all → skipped (no workspace id)"
fi

# ─── 7. Bot worker ───────────────────────────────────────────────────────────
header "7. Bot Worker"

WORKER_LOG=$(journalctl -u botmarket-api --no-pager -n 500 2>/dev/null | grep "botWorker" | head -1 || true)
if [[ -n "$WORKER_LOG" ]]; then
  pass "Bot worker log line found in API logs"
else
  fail "Bot worker log NOT found in API logs"
fi

# ─── 8. DB backup ────────────────────────────────────────────────────────────
header "8. DB backup"

TIMER_STATE=$(systemctl is-active botmarket-backup.timer 2>/dev/null || true)
if [[ "$TIMER_STATE" == "active" ]]; then
  pass "botmarket-backup.timer is active"
else
  fail "botmarket-backup.timer is NOT active (state: $TIMER_STATE)"
fi

if command -v pg_dump &>/dev/null; then
  pass "pg_dump binary available for backup.sh"
else
  fail "pg_dump NOT found — install: apt-get install postgresql-client"
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL=$((PASS + FAIL))
echo "  Results: $PASS/$TOTAL passed"
if [[ $FAIL -eq 0 ]]; then
  printf "  \033[32mALL TESTS PASSED ✓\033[0m\n"
else
  printf "  \033[31m%d TEST(S) FAILED ✗\033[0m\n" "$FAIL"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit "$FAIL"
