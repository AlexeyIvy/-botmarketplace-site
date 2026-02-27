#!/usr/bin/env bash
# smoke-test.sh — MVP release smoke tests
# Usage: bash deploy/smoke-test.sh [--base-url https://botmarketplace.store]
# Exit code: 0 = all passed, 1 = failures found

set -euo pipefail

BASE_URL="${BASE_URL:-https://botmarketplace.store}"
TEST_EMAIL="smoke_$(date +%s)@test.com"
TEST_PASS="Smoke1234!"
TEST_EMAIL2="smoke2_$(date +%s)@test.com"
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

# Pre-register second user before rate-limiter fires (used in Section 11 cross-workspace test)
REG2_PRE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL2\",\"password\":\"$TEST_PASS\"}")
TOKEN2=$(echo "$REG2_PRE" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4) || true
WS_ID2=$(echo "$REG2_PRE" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4) || true

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

# ─── 9. Terminal Market Data (Stage 9a) ──────────────────────────────────────
header "9. Terminal Market Data (Stage 9a)"

# 9.1 ticker valid symbol → 200 + required fields
TICKER_RESP=$(curl -s "$BASE_URL/api/v1/terminal/ticker?symbol=BTCUSDT" \
  -H "Authorization: Bearer $TOKEN")
TICKER_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/terminal/ticker?symbol=BTCUSDT" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/ticker?symbol=BTCUSDT → 200" "200" "$TICKER_CODE"
check_contains "/terminal/ticker → lastPrice" '"lastPrice"' "$TICKER_RESP"
check_contains "/terminal/ticker → symbol" '"symbol"' "$TICKER_RESP"

# 9.2 candles valid params → 200 + OHLCV fields
CANDLES_RESP=$(curl -s "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=15&limit=10" \
  -H "Authorization: Bearer $TOKEN")
CANDLES_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=15&limit=10" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/candles 15m/10 → 200" "200" "$CANDLES_CODE"
check_contains "/terminal/candles → openTime" '"openTime"' "$CANDLES_RESP"
check_contains "/terminal/candles → close" '"close"' "$CANDLES_RESP"

# 9.3 ticker ETHUSDT → 200
ETH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/terminal/ticker?symbol=ETHUSDT" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/ticker ETHUSDT → 200" "200" "$ETH_CODE"

# 9.4 ticker missing symbol → 400
NO_SYM=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/terminal/ticker" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/ticker (no symbol) → 400" "400" "$NO_SYM"

# 9.5 candles invalid interval → 400 + "Allowed values"
BAD_INT_RESP=$(curl -s "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=999" \
  -H "Authorization: Bearer $TOKEN")
BAD_INT_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=999" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/candles interval=999 → 400" "400" "$BAD_INT_CODE"
check_contains "/terminal/candles bad interval → 'Allowed values'" "Allowed values" "$BAD_INT_RESP"

# 9.6 candles limit > 1000 → 400
BIG_LIMIT=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&limit=9999" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/candles limit=9999 → 400" "400" "$BIG_LIMIT"

# 9.7 ticker unknown symbol → 422
FAKE_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/ticker?symbol=FAKESYMBOLABC123" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/ticker FAKE → 422" "422" "$FAKE_CODE"

# 9.8 ticker without auth → 401
NO_AUTH_TICKER=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/ticker?symbol=BTCUSDT")
check "GET /terminal/ticker without auth → 401" "401" "$NO_AUTH_TICKER"

# 9.9 candles without auth → 401
NO_AUTH_CANDLES=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=15&limit=10")
check "GET /terminal/candles without auth → 401" "401" "$NO_AUTH_CANDLES"

# 9.10 candles daily interval D → 200
DAILY=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/terminal/candles?symbol=BTCUSDT&interval=D&limit=5" \
  -H "Authorization: Bearer $TOKEN")
check "GET /terminal/candles interval=D → 200" "200" "$DAILY"

# 9.11 no secrets leaked in ticker response
if ! echo "$TICKER_RESP" | grep -q "encryptedSecret\|\"secret\"\|\"apiKey\""; then
  green "/terminal/ticker → no secret fields in response"
  ((++PASS))
else
  red "/terminal/ticker → secret fields found in response!"
  ((++FAIL))
fi

# ─── 10. Stage 10 — Strategy DSL Validation + Bot Runtime ───────────────────
header "10. Stage 10 — DSL Validation + Bot Runtime"

# ── Fixture: create strategy + version + bot for runtime tests ──────────────
S10_STRAT=$(curl -s -X POST "$BASE_URL/api/v1/strategies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"Stage10Strategy","symbol":"BTCUSDT","timeframe":"M15"}')
S10_STRAT_ID=$(echo "$S10_STRAT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true

VALID_DSL='{
  "id": "s10-dsl-1",
  "name": "Stage10 Test Strategy",
  "dslVersion": 1,
  "enabled": true,
  "market": {"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
  "entry": {"side":"Buy","signal":"manual"},
  "risk": {"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},
  "execution": {"orderType":"Market","clientOrderIdPrefix":"s10test"},
  "guards": {"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}
}'

# 10.1 POST /strategies/validate valid DSL → 200 + ok:true
VALID_RESP=$(curl -s -X POST "$BASE_URL/api/v1/strategies/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"dslJson\":$VALID_DSL}")
VALID_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/strategies/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"dslJson\":$VALID_DSL}")
check "POST /strategies/validate valid DSL → 200" "200" "$VALID_CODE"
check_contains "/strategies/validate → ok:true" '"ok":true' "$VALID_RESP"

# 10.2 POST /strategies/validate missing required fields → 400 + errors
INVALID_DSL='{"id":"x","name":"y","dslVersion":1}'
BAD_DSL_RESP=$(curl -s -X POST "$BASE_URL/api/v1/strategies/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"dslJson\":$INVALID_DSL}")
BAD_DSL_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/strategies/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"dslJson\":$INVALID_DSL}")
check "POST /strategies/validate invalid DSL → 400" "400" "$BAD_DSL_CODE"
check_contains "/strategies/validate invalid → errors array" '"errors"' "$BAD_DSL_RESP"

# 10.3 POST /strategies/validate wrong dslVersion type → 400
BAD_VER='{"id":"x","name":"y","dslVersion":"not-a-number","enabled":true,"market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},"entry":{},"risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},"execution":{"orderType":"Market","clientOrderIdPrefix":"x"},"guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}}'
BAD_VER_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/strategies/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"dslJson\":$BAD_VER}")
check "POST /strategies/validate wrong dslVersion type → 400" "400" "$BAD_VER_CODE"

# 10.4 Create strategy version with valid DSL → 201
if [[ -n "$S10_STRAT_ID" ]]; then
  S10_VER=$(curl -s -X POST "$BASE_URL/api/v1/strategies/$S10_STRAT_ID/versions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"dslJson\":$VALID_DSL}")
  S10_VER_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/strategies/$S10_STRAT_ID/versions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"dslJson\":$VALID_DSL}")
  S10_VER_ID=$(echo "$S10_VER" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
  check "POST /strategies/:id/versions valid DSL → 201" "201" "$S10_VER_CODE"
else
  red "Skipping version creation (no strategy ID)"
  ((++FAIL))
  S10_VER_ID=""
fi

# 10.5 Create strategy version with invalid DSL → 400
if [[ -n "$S10_STRAT_ID" ]]; then
  BAD_VER_RESP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/strategies/$S10_STRAT_ID/versions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"dslJson\":$INVALID_DSL}")
  check "POST /strategies/:id/versions invalid DSL → 400" "400" "$BAD_VER_RESP_CODE"
else
  red "Skipping bad version creation (no strategy ID)"
  ((++FAIL))
fi

# 10.6 Create bot with exchangeConnectionId field (no real conn needed — test field accepted)
if [[ -n "$S10_VER_ID" ]]; then
  S10_BOT=$(curl -s -X POST "$BASE_URL/api/v1/bots" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"name\":\"Stage10Bot\",\"strategyVersionId\":\"$S10_VER_ID\",\"symbol\":\"BTCUSDT\",\"timeframe\":\"M15\"}")
  S10_BOT_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/bots" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"name\":\"Stage10BotB\",\"strategyVersionId\":\"$S10_VER_ID\",\"symbol\":\"BTCUSDT\",\"timeframe\":\"M15\"}")
  S10_BOT_ID=$(echo "$S10_BOT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
  check "POST /bots → 201" "201" "$S10_BOT_CODE"
else
  red "Skipping bot creation (no strategy version ID)"
  ((++FAIL))
  S10_BOT_ID=""
fi

# 10.7 GET /bots/:id/runs → 200 + array
if [[ -n "$S10_BOT_ID" ]]; then
  RUNS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/bots/$S10_BOT_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  RUNS_RESP=$(curl -s "$BASE_URL/api/v1/bots/$S10_BOT_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "GET /bots/:id/runs → 200" "200" "$RUNS_CODE"
  # Empty array is fine (bot just created)
  if echo "$RUNS_RESP" | grep -q '^\[\]$\|^\[{'; then
    green "GET /bots/:id/runs → returns array"
    ((++PASS))
  elif [[ "$RUNS_RESP" == "[]" ]]; then
    green "GET /bots/:id/runs → returns empty array"
    ((++PASS))
  else
    check_contains "GET /bots/:id/runs → array response" '[' "$RUNS_RESP"
  fi
else
  red "Skipping GET /bots/:id/runs (no bot ID)"
  ((++FAIL))
fi

# 10.8 POST /bots/:id/runs with durationMinutes → 201 + durationMinutes field
if [[ -n "$S10_BOT_ID" ]]; then
  RUN_RESP=$(curl -s -X POST "$BASE_URL/api/v1/bots/$S10_BOT_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d '{"durationMinutes":5}')
  RUN_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/bots/$S10_BOT_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d '{"durationMinutes":5}')
  S10_RUN_ID=$(echo "$RUN_RESP" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
  # 201 = created, 409 = already active (OK for smoke idempotency)
  if [[ "$RUN_CODE" == "201" ]] || [[ "$RUN_CODE" == "409" ]]; then
    green "POST /bots/:id/runs with durationMinutes → $RUN_CODE"
    ((++PASS))
  else
    red "POST /bots/:id/runs with durationMinutes → $RUN_CODE (expected 201)"
    ((++FAIL))
  fi
  check_contains "POST /bots/:id/runs → durationMinutes field" '"durationMinutes"' "$RUN_RESP"
else
  red "Skipping POST /bots/:id/runs (no bot ID)"
  ((++FAIL))
  S10_RUN_ID=""
fi

# 10.9 GET /runs/:runId → 200 (fetch run by ID)
if [[ -n "$S10_RUN_ID" ]]; then
  GET_RUN_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/runs/$S10_RUN_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "GET /runs/:runId → 200" "200" "$GET_RUN_CODE"
else
  red "Skipping GET /runs/:runId (no run ID)"
  ((++FAIL))
fi

# 10.10 POST /runs/:runId/signal on non-RUNNING run → 409
if [[ -n "$S10_RUN_ID" ]]; then
  SIG_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/runs/$S10_RUN_ID/signal" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d '{"side":"BUY","qty":0.001}')
  # Run is QUEUED/STARTING — should get 409 (not RUNNING yet)
  # OR 201 if worker already advanced it to RUNNING
  if [[ "$SIG_CODE" == "409" ]] || [[ "$SIG_CODE" == "201" ]]; then
    green "POST /runs/:runId/signal → $SIG_CODE (expected 409 or 201)"
    ((++PASS))
  else
    red "POST /runs/:runId/signal → $SIG_CODE (expected 409 or 201)"
    ((++FAIL))
  fi
else
  red "Skipping POST /runs/:runId/signal (no run ID)"
  ((++FAIL))
fi

# 10.11 POST /runs/:runId/signal without auth → 401
if [[ -n "$S10_RUN_ID" ]]; then
  SIG_UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/runs/$S10_RUN_ID/signal" \
    -H "Content-Type: application/json" \
    -d '{"side":"BUY","qty":0.001}')
  check "POST /runs/:runId/signal without auth → 401" "401" "$SIG_UNAUTH"
else
  red "Skipping signal unauth test (no run ID)"
  ((++FAIL))
fi

# 10.12 POST /bots/:id/runs invalid durationMinutes → 400
if [[ -n "$S10_BOT_ID" ]]; then
  BAD_DUR_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/bots/$S10_BOT_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d '{"durationMinutes":99999}')
  check "POST /bots/:id/runs durationMinutes=99999 → 400" "400" "$BAD_DUR_CODE"
else
  red "Skipping bad durationMinutes test (no bot ID)"
  ((++FAIL))
fi

# ─── 11. Stage 11 — Bot Factory Launch Flow ─────────────────────────────────
header "11. Stage 11 — Bot Factory Launch Flow"

# Reuse fixtures from Section 10 ($S10_VER_ID, $S10_BOT_ID, $S10_RUN_ID)

# 11.1 GET /bots/:id → 200 + strategyVersion nested
if [[ -n "$S10_BOT_ID" ]]; then
  BOT_DETAIL=$(curl -s "$BASE_URL/api/v1/bots/$S10_BOT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  BOT_DETAIL_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/bots/$S10_BOT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "GET /bots/:id → 200" "200" "$BOT_DETAIL_CODE"
  check_contains "GET /bots/:id → strategyVersion present" '"strategyVersion"' "$BOT_DETAIL"
  check_contains "GET /bots/:id → lastRun field present" '"lastRun"' "$BOT_DETAIL"
else
  red "Skipping GET /bots/:id (no bot ID from Section 10)"
  ((++FAIL)); ((++FAIL)); ((++FAIL))
fi

# 11.2 GET /runs/:runId/events → 200 + events array
if [[ -n "$S10_RUN_ID" ]]; then
  EVT_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/runs/$S10_RUN_ID/events" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  EVT_RESP=$(curl -s "$BASE_URL/api/v1/runs/$S10_RUN_ID/events" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "GET /runs/:runId/events → 200" "200" "$EVT_CODE"
  # Should have at least RUN_CREATED event
  if echo "$EVT_RESP" | grep -q '"type"'; then
    green "GET /runs/:runId/events → events returned"
    ((++PASS))
  else
    check_contains "GET /runs/:runId/events → array" '[' "$EVT_RESP"
  fi
  # No secrets in event log
  if ! echo "$EVT_RESP" | grep -q '"encryptedSecret"\|"apiKey"\|"secret"'; then
    green "GET /runs/:runId/events → no secrets in payload"
    ((++PASS))
  else
    red "GET /runs/:runId/events → secret field found in events!"
    ((++FAIL))
  fi
else
  red "Skipping GET /runs/:runId/events (no run ID)"
  ((++FAIL)); ((++FAIL)); ((++FAIL))
fi

# 11.3 GET /runs/:runId/events without auth → 401
if [[ -n "$S10_RUN_ID" ]]; then
  EVT_UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/runs/$S10_RUN_ID/events")
  check "GET /runs/:runId/events without auth → 401" "401" "$EVT_UNAUTH"
else
  red "Skipping events unauth test (no run ID)"
  ((++FAIL))
fi

# 11.4 POST /bots/:id/runs/:runId/stop
# Create a second bot for stop test so we don't collide with active run from Section 10
if [[ -n "$S10_VER_ID" ]]; then
  STOP_BOT=$(curl -s -X POST "$BASE_URL/api/v1/bots" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"name\":\"Stage11StopBot\",\"strategyVersionId\":\"$S10_VER_ID\",\"symbol\":\"ETHUSDT\",\"timeframe\":\"M15\"}")
  STOP_BOT_ID=$(echo "$STOP_BOT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true

  if [[ -n "$STOP_BOT_ID" ]]; then
    # Start a run
    STOP_RUN=$(curl -s -X POST "$BASE_URL/api/v1/bots/$STOP_BOT_ID/runs" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -H "X-Workspace-Id: $WS_ID" \
      -d '{"durationMinutes":60}')
    STOP_RUN_ID=$(echo "$STOP_RUN" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true

    if [[ -n "$STOP_RUN_ID" ]]; then
      sleep 6  # wait for worker to advance run from QUEUED → RUNNING before stop
      # Stop it
      STOP_RESP=$(curl -s -X POST "$BASE_URL/api/v1/bots/$STOP_BOT_ID/runs/$STOP_RUN_ID/stop" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -H "X-Workspace-Id: $WS_ID" \
        -d '{}')
      STOP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        "$BASE_URL/api/v1/bots/$STOP_BOT_ID/runs/$STOP_RUN_ID/stop" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -H "X-Workspace-Id: $WS_ID" \
        -d '{}')
      # 200 = stopped, 409 = already terminal (if worker already terminated it)
      if [[ "$STOP_CODE" == "200" ]] || [[ "$STOP_CODE" == "409" ]]; then
        green "POST /bots/:id/runs/:runId/stop → $STOP_CODE (expected 200 or 409)"
        ((++PASS))
      else
        red "POST /bots/:id/runs/:runId/stop → $STOP_CODE (expected 200 or 409)"
        ((++FAIL))
      fi
      # Verify response has state field
      check_contains "POST .../stop → state field" '"state"' "$STOP_RESP"
    else
      red "Skipping stop test (failed to start run for stop bot)"
      ((++FAIL)); ((++FAIL))
    fi
  else
    red "Skipping stop test (failed to create stop bot)"
    ((++FAIL)); ((++FAIL))
  fi
else
  red "Skipping stop test (no strategy version ID)"
  ((++FAIL)); ((++FAIL))
fi

# 11.5 Cross-workspace: bot from other workspace → 403
if [[ -n "$S10_BOT_ID" ]]; then
  # TOKEN2/WS_ID2 pre-registered before rate-limiter section (see above)
  if [[ -n "$TOKEN2" && -n "$WS_ID2" ]]; then
    # Try to access bot from workspace 1 using workspace 2's token+wsId
    XWS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/bots/$S10_BOT_ID" \
      -H "Authorization: Bearer $TOKEN2" \
      -H "X-Workspace-Id: $WS_ID2")
    # Accept 404 (workspace isolation hides the resource) or 403
    if [[ "$XWS_CODE" == "404" ]] || [[ "$XWS_CODE" == "403" ]]; then
      green "GET /bots/:id cross-workspace → $XWS_CODE (workspace isolated)"
      ((++PASS))
    else
      red "GET /bots/:id cross-workspace → $XWS_CODE (expected 403 or 404)"
      ((++FAIL))
    fi

    # Try to start run on bot from workspace 1 using workspace 2
    XWS_RUN_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      "$BASE_URL/api/v1/bots/$S10_BOT_ID/runs" \
      -H "Authorization: Bearer $TOKEN2" \
      -H "Content-Type: application/json" \
      -H "X-Workspace-Id: $WS_ID2" \
      -d '{}')
    if [[ "$XWS_RUN_CODE" == "403" ]] || [[ "$XWS_RUN_CODE" == "404" ]]; then
      green "POST /bots/:id/runs cross-workspace → $XWS_RUN_CODE (workspace isolated)"
      ((++PASS))
    else
      red "POST /bots/:id/runs cross-workspace → $XWS_RUN_CODE (expected 403 or 404)"
      ((++FAIL))
    fi
  else
    red "Skipping cross-workspace test (failed to register second user)"
    ((++FAIL)); ((++FAIL))
  fi
else
  red "Skipping cross-workspace test (no bot ID)"
  ((++FAIL)); ((++FAIL))
fi

# 11.6 POST /bots without strategyVersionId → 400
MISSING_SVER=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/bots" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"NoStratBot","symbol":"BTCUSDT","timeframe":"M15"}')
check "POST /bots without strategyVersionId → 400" "400" "$MISSING_SVER"

# 11.7 POST /bots with non-existent strategyVersionId → 400
BAD_SVER=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/bots" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"BadStratBot","strategyVersionId":"00000000-0000-0000-0000-000000000000","symbol":"BTCUSDT","timeframe":"M15"}')
check "POST /bots with invalid strategyVersionId → 400" "400" "$BAD_SVER"

# 11.8 GET /bots without auth → 401
BOTS_UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/bots")
check "GET /bots without auth → 401" "401" "$BOTS_UNAUTH"

# 11.9 No secrets in bot/run responses
if [[ -n "$S10_BOT_ID" ]]; then
  BOT_RESP=$(curl -s "$BASE_URL/api/v1/bots/$S10_BOT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  if ! echo "$BOT_RESP" | grep -q '"encryptedSecret"\|"apiKey"\|"passwordHash"'; then
    green "GET /bots/:id → no secret fields in response"
    ((++PASS))
  else
    red "GET /bots/:id → secret fields found in bot response!"
    ((++FAIL))
  fi
else
  red "Skipping secret-check test (no bot ID)"
  ((++FAIL))
fi

# 11.10 GET /bots/:id/runs after section 10 run → array with at least 1 run
if [[ -n "$S10_BOT_ID" ]]; then
  RUNS_AFTER=$(curl -s "$BASE_URL/api/v1/bots/$S10_BOT_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  if echo "$RUNS_AFTER" | grep -q '"state"'; then
    green "GET /bots/:id/runs → at least one run returned with state"
    ((++PASS))
  else
    red "GET /bots/:id/runs → no runs found (expected at least 1 from Section 10)"
    ((++FAIL))
  fi
else
  red "Skipping runs-after test (no bot ID)"
  ((++FAIL))
fi

# ─── 12. Stage 12 — DSL enforcement + Lab backtest API ──────────────────────
header "12. Stage 12 — DSL enforcement + Lab backtest API"

# Shared setup: create strategy + version for Stage 12 tests
S12_STRAT=$(curl -s -X POST "$BASE_URL/api/v1/strategies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"S12 Test Strategy","symbol":"BTCUSDT","timeframe":"M15"}')
S12_STRAT_ID=$(echo "$S12_STRAT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true

S12_VER_ENABLED=$(curl -s -X POST "$BASE_URL/api/v1/strategies/$S12_STRAT_ID/versions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{
    "dslJson": {
      "id":"s12-enabled","name":"S12 Enabled","dslVersion":1,"enabled":true,
      "market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
      "entry":{"side":"Buy","signal":"manual"},
      "risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60,"dailyLossLimitUsd":50},
      "execution":{"orderType":"Market","clientOrderIdPrefix":"s12bot"},
      "guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}
    }
  }')
S12_VER_ENABLED_ID=$(echo "$S12_VER_ENABLED" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true

S12_VER_DISABLED=$(curl -s -X POST "$BASE_URL/api/v1/strategies/$S12_STRAT_ID/versions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{
    "dslJson": {
      "id":"s12-disabled","name":"S12 Disabled","dslVersion":1,"enabled":false,
      "market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
      "entry":{"side":"Buy","signal":"manual"},
      "risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},
      "execution":{"orderType":"Market","clientOrderIdPrefix":"s12bot"},
      "guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}
    }
  }')
S12_VER_DISABLED_ID=$(echo "$S12_VER_DISABLED" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true

# 12.1 POST /lab/backtest → 202 PENDING
if [[ -n "$S12_STRAT_ID" ]]; then
  S12_BT_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/lab/backtest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"strategyId\":\"$S12_STRAT_ID\",\"symbol\":\"BTCUSDT\",\"interval\":\"15\",\"fromTs\":\"2024-01-01T00:00:00Z\",\"toTs\":\"2024-01-31T00:00:00Z\"}")
  check "POST /lab/backtest → 202" "202" "$S12_BT_CODE"

  S12_BT=$(curl -s -X POST "$BASE_URL/api/v1/lab/backtest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"strategyId\":\"$S12_STRAT_ID\",\"symbol\":\"BTCUSDT\",\"interval\":\"15\",\"fromTs\":\"2024-01-01T00:00:00Z\",\"toTs\":\"2024-01-31T00:00:00Z\"}")
  S12_BT_ID=$(echo "$S12_BT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
  S12_BT_STATUS=$(echo "$S12_BT" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4) || true
  if [[ "$S12_BT_STATUS" == "PENDING" ]] || [[ "$S12_BT_STATUS" == "RUNNING" ]]; then
    green "POST /lab/backtest → status PENDING/RUNNING"
    ((++PASS))
  else
    red "POST /lab/backtest → unexpected status: $S12_BT_STATUS"
    ((++FAIL))
  fi
else
  red "Skipping backtest tests (no strategy created)"
  ((++FAIL)); ((++FAIL))
fi

# 12.2 GET /lab/backtests → 200 + array
S12_LIST_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/lab/backtests" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
check "GET /lab/backtests → 200" "200" "$S12_LIST_CODE"

# 12.3 GET /lab/backtest/:id → 200
if [[ -n "$S12_BT_ID" ]]; then
  S12_GET_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/lab/backtest/$S12_BT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "GET /lab/backtest/:id → 200" "200" "$S12_GET_CODE"
else
  red "Skipping GET /lab/backtest/:id (no backtest ID)"
  ((++FAIL))
fi

# 12.4 POST /lab/backtest without auth → 401
S12_UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/lab/backtest" \
  -H "Content-Type: application/json" \
  -d '{"strategyId":"fake","fromTs":"2024-01-01T00:00:00Z","toTs":"2024-01-31T00:00:00Z"}')
check "POST /lab/backtest without auth → 401" "401" "$S12_UNAUTH"

# 12.5 POST /lab/backtest without strategyId → 400
S12_NO_STRAT=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/lab/backtest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"fromTs":"2024-01-01T00:00:00Z","toTs":"2024-01-31T00:00:00Z"}')
check "POST /lab/backtest without strategyId → 400" "400" "$S12_NO_STRAT"

# 12.6 POST /lab/backtest with fromTs >= toTs → 400
if [[ -n "$S12_STRAT_ID" ]]; then
  S12_BAD_RANGE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/lab/backtest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"strategyId\":\"$S12_STRAT_ID\",\"fromTs\":\"2024-02-01T00:00:00Z\",\"toTs\":\"2024-01-01T00:00:00Z\"}")
  check "POST /lab/backtest fromTs >= toTs → 400" "400" "$S12_BAD_RANGE"
else
  red "Skipping date-range validation test (no strategy)"
  ((++FAIL))
fi

# 12.7 Bot with enabled DSL → bot creation succeeds
if [[ -n "$S12_VER_ENABLED_ID" ]]; then
  S12_BOT=$(curl -s -X POST "$BASE_URL/api/v1/bots" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"name\":\"S12 Enabled Bot\",\"strategyVersionId\":\"$S12_VER_ENABLED_ID\",\"symbol\":\"SOLUSDT\",\"timeframe\":\"M15\"}")
  S12_BOT_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/bots" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"name\":\"S12 Enabled Bot2\",\"strategyVersionId\":\"$S12_VER_ENABLED_ID\",\"symbol\":\"SOLUSDT\",\"timeframe\":\"M15\"}")
  check "POST /bots with enabled DSL → 201" "201" "$S12_BOT_CODE"
  S12_BOT_ID=$(echo "$S12_BOT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
else
  red "Skipping enabled-bot test (no strategy version)"
  ((++FAIL))
  S12_BOT_ID=""
fi

# 12.8 Bot with disabled DSL → bot creation succeeds (enforcement is in worker, not create)
if [[ -n "$S12_VER_DISABLED_ID" ]]; then
  S12_DIS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/bots" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"name\":\"S12 Disabled Bot\",\"strategyVersionId\":\"$S12_VER_DISABLED_ID\",\"symbol\":\"SOLUSDT\",\"timeframe\":\"M15\"}")
  check "POST /bots with disabled DSL → 201 (worker cancels intents)" "201" "$S12_DIS_CODE"
else
  red "Skipping disabled-bot test (no strategy version)"
  ((++FAIL))
fi

# 12.9 Run + intent on enabled bot → intent created 201
if [[ -n "$S12_BOT_ID" ]]; then
  S12_RUN=$(curl -s -X POST "$BASE_URL/api/v1/bots/$S12_BOT_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d '{"durationMinutes":5}')
  S12_RUN_ID=$(echo "$S12_RUN" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
  sleep 6  # wait for worker to advance to RUNNING
  if [[ -n "$S12_RUN_ID" ]]; then
    S12_INTENT=$(curl -s -X POST "$BASE_URL/api/v1/runs/$S12_RUN_ID/intents" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -H "X-Workspace-Id: $WS_ID" \
      -d "{\"intentId\":\"s12-intent-1\",\"type\":\"ENTRY\",\"side\":\"BUY\",\"qty\":0.001}")
    S12_INTENT_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/runs/$S12_RUN_ID/intents" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -H "X-Workspace-Id: $WS_ID" \
      -d "{\"intentId\":\"s12-intent-2\",\"type\":\"ENTRY\",\"side\":\"BUY\",\"qty\":0.001}")
    check "POST /runs/:runId/intents → 201" "201" "$S12_INTENT_CODE"
    S12_INTENT_ID=$(echo "$S12_INTENT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
  else
    red "Skipping intent test (no run ID)"
    ((++FAIL))
    S12_INTENT_ID=""
  fi
else
  red "Skipping intent test (no bot ID)"
  ((++FAIL))
  S12_RUN_ID=""
  S12_INTENT_ID=""
fi

# 12.10 GET /runs/:runId/intents → 200 + array
if [[ -n "$S12_RUN_ID" ]]; then
  S12_INTENTS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/runs/$S12_RUN_ID/intents" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "GET /runs/:runId/intents → 200" "200" "$S12_INTENTS_CODE"
else
  red "Skipping GET intents (no run ID)"
  ((++FAIL))
fi

# 12.11 POST /runs/:runId/intents without auth → 401
if [[ -n "$S12_RUN_ID" ]]; then
  S12_INTENT_UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/runs/$S12_RUN_ID/intents" \
    -H "Content-Type: application/json" \
    -d '{"intentId":"x","type":"ENTRY","side":"BUY","qty":0.001}')
  check "POST /runs/:runId/intents without auth → 401" "401" "$S12_INTENT_UNAUTH"
else
  red "Skipping intents-unauth test (no run ID)"
  ((++FAIL))
fi

# 12.12 Intent idempotency: same intentId → existing record returned (200 or 201)
if [[ -n "$S12_RUN_ID" && -n "$S12_INTENT_ID" ]]; then
  S12_IDEM_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/runs/$S12_RUN_ID/intents" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "X-Workspace-Id: $WS_ID" \
    -d "{\"intentId\":\"s12-intent-1\",\"type\":\"ENTRY\",\"side\":\"BUY\",\"qty\":0.001}")
  if [[ "$S12_IDEM_CODE" == "200" ]] || [[ "$S12_IDEM_CODE" == "201" ]]; then
    green "POST /runs/:runId/intents idempotency → $S12_IDEM_CODE (existing intent returned)"
    ((++PASS))
  else
    red "POST /runs/:runId/intents idempotency → $S12_IDEM_CODE (expected 200 or 201)"
    ((++FAIL))
  fi
else
  red "Skipping idempotency test (no run/intent ID)"
  ((++FAIL))
fi

# ─── 13. Observability ───────────────────────────────────────────────────────
header "13. Observability"

# 13.1 /healthz has uptime field
S13_HEALTH=$(curl -s "$BASE_URL/api/v1/healthz")
check_contains "GET /healthz → has uptime" '"uptime"' "$S13_HEALTH"

# 13.2 /healthz has timestamp field
check_contains "GET /healthz → has timestamp" '"timestamp"' "$S13_HEALTH"

# 13.3 Response includes X-Request-Id header
S13_HEADERS=$(curl -sD- -o /dev/null "$BASE_URL/api/v1/healthz")
if echo "$S13_HEADERS" | grep -qi "x-request-id:"; then
  green "GET /healthz → X-Request-Id header present"
  ((++PASS))
else
  red "GET /healthz → X-Request-Id header missing"
  ((++FAIL))
fi

# 13.4 Client-provided X-Request-Id is echoed back
S13_ECHO_HEADERS=$(curl -sD- -o /dev/null "$BASE_URL/api/v1/healthz" -H "X-Request-Id: test-req-123")
if echo "$S13_ECHO_HEADERS" | grep -qi "x-request-id: test-req-123"; then
  green "GET /healthz with X-Request-Id → echoed back"
  ((++PASS))
else
  red "GET /healthz with X-Request-Id → not echoed (headers: $(echo "$S13_ECHO_HEADERS" | grep -i x-request-id || echo 'none'))"
  ((++FAIL))
fi

# ─── 14. Stage 14 — RC Validation (Exchange Connections + Secret Leak Guard) ──
header "14. Stage 14 — RC Validation"

# 14.1 POST /exchanges → 201 (demo connection, no real keys needed)
EC_RESP=$(curl -s -X POST "$BASE_URL/api/v1/exchanges" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"exchange":"bybit","name":"smoke-demo-conn","apiKey":"smoke-api-key","secret":"smoke-secret"}')
EC_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/exchanges" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"exchange":"bybit","name":"smoke-demo-conn-b","apiKey":"smoke-api-key-b","secret":"smoke-secret-b"}')
EC_ID=$(echo "$EC_RESP" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4) || true
check "POST /exchanges (demo connection) → 201" "201" "$EC_CODE"

# 14.2 No secrets in exchange connection response
if [[ -n "$EC_RESP" ]]; then
  if ! echo "$EC_RESP" | grep -q '"encryptedSecret"\|"apiKey"\|"secret"'; then
    green "POST /exchanges → no secret fields in response"
    ((++PASS))
  else
    red "POST /exchanges → secret field found in exchange connection response!"
    ((++FAIL))
  fi
else
  red "Skipping exchange secret-check (no response)"
  ((++FAIL))
fi

# 14.3 GET /exchanges → 200 + array
EC_LIST_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/exchanges" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID")
check "GET /exchanges → 200" "200" "$EC_LIST_CODE"

# 14.4 GET /exchanges/:id → 200 + no secrets
if [[ -n "$EC_ID" ]]; then
  EC_GET=$(curl -s "$BASE_URL/api/v1/exchanges/$EC_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  EC_GET_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/exchanges/$EC_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "GET /exchanges/:id → 200" "200" "$EC_GET_CODE"
  if ! echo "$EC_GET" | grep -q '"encryptedSecret"\|"apiKey"\|"secret"'; then
    green "GET /exchanges/:id → no secret fields in response"
    ((++PASS))
  else
    red "GET /exchanges/:id → secret field found!"
    ((++FAIL))
  fi
else
  red "Skipping GET /exchanges/:id (no connection ID)"
  ((++FAIL)); ((++FAIL))
fi

# 14.5 GET /exchanges without auth → 401
EC_UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/exchanges")
check "GET /exchanges without auth → 401" "401" "$EC_UNAUTH"

# 14.6 DELETE /exchanges/:id → 204
if [[ -n "$EC_ID" ]]; then
  EC_DEL_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/exchanges/$EC_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID")
  check "DELETE /exchanges/:id → 204" "204" "$EC_DEL_CODE"
else
  red "Skipping DELETE /exchanges/:id (no connection ID)"
  ((++FAIL))
fi

# 14.7 Global secret leak guard — scan strategy + run + lab responses
S14_SAFE=1
for endpoint_name in "terminal/ticker" "strategies" "bots" "lab/backtests"; do
  RESP=$(curl -s "$BASE_URL/api/v1/$endpoint_name" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Workspace-Id: $WS_ID" 2>/dev/null || true)
  if echo "$RESP" | grep -qE '"encryptedSecret"|"passwordHash"'; then
    red "Secret leak detected in GET /$endpoint_name response!"
    S14_SAFE=0
    ((++FAIL))
  fi
done
if [[ $S14_SAFE -eq 1 ]]; then
  green "Global secret leak guard → no encryptedSecret/passwordHash in list endpoints"
  ((++PASS))
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
  echo ""
  echo "  Troubleshooting hints:"
  echo "  ─────────────────────"
  echo "  • Rate limit failures: wait ~15 min between full runs (window resets)"
  echo "  • Worker state failures: wait 6-10 s for QUEUED→RUNNING transition"
  echo "  • Auth failures: check JWT_SECRET in .env on VPS"
  echo "  • Secret leak: check safeView() projection in exchanges.ts / botWorker.ts"
  echo "  • 5xx errors: journalctl -u botmarket-api --since '5 min ago' | grep Unhandled"
  echo "  • Correlation: add -H 'X-Request-Id: debug-1' and grep logs for 'debug-1'"
  echo ""
  echo "  Re-run a single section manually:"
  echo "    BASE_URL=$BASE_URL bash deploy/smoke-test.sh"
  echo ""
  echo "  Full logs:"
  echo "    journalctl -u botmarket-api -f"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $FAIL
