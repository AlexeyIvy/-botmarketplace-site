# Stage 12 — DSL Enforcement & Research Lab Improvements

## Status: DONE

## 1) Scope

- `enabled: false` runtime respect in botWorker: PENDING intents are CANCELLED with `intent_cancelled` event
- `risk.dailyLossLimitUsd` enforcement: RUNNING run transitions to STOPPING when estimated daily loss exceeds limit
- Lab UI: strategy dropdown (replaces manual UUID input) with auto-fill symbol from selected strategy
- Lab UI: trade log table toggle — show/hide per-trade details (entry/exit/SL/TP prices, outcome, PnL%)
- Smoke test Section 12: 12 new checks (lab backtest API + intent API + DSL enforcement contracts)

## 2) Scope Boundaries (what is NOT in Stage 12)

- No real-time price feed integration for `execution.maxSlippageBps` enforcement (requires WebSocket or polling — deferred to Stage 13+)
- No DSL migration (dslVersion > 1 schema) — still on v1
- No `entry.signal = "webhook"` routing to RUNNING bot
- No multi-bot scheduler
- No production-grade worker extraction (still in-process)
- No PnL tracking per trade for live bots (only simulated fills in demo mode)

## 3) Files Changed

| File | Change |
|------|--------|
| `apps/api/src/lib/botWorker.ts` | Add `enforceDailyLossLimit()` + `enabled: false` check in `processIntents()` |
| `apps/web/src/app/lab/page.tsx` | Strategy dropdown + trade log table + `TradeRecord` type |
| `deploy/smoke-test.sh` | Add Section 12 (12 checks) |
| `docs/steps/12-stage-12-dsl-enforcement.md` | NEW — this file |

## 4) DSL Enforcement Details

### enabled: false

When the worker processes PENDING intents, it checks the strategy DSL before calling the exchange:

```typescript
if (dsl && dsl["enabled"] === false) {
  // mark intent CANCELLED, emit intent_cancelled event, skip executeIntent()
}
```

**Effect:** Bot can still be created and run started. All PENDING intents on that run are cancelled by the worker on the next poll cycle (~4 s). The run itself is not stopped — the operator can stop it manually or let it time out.

**DSL example:**
```json
{ "enabled": false, "market": { ... }, ... }
```

### risk.dailyLossLimitUsd

After each worker poll cycle `enforceDailyLossLimit()` scans all RUNNING runs:

```
estimated_daily_loss = count(FAILED intents today for run) × (riskPerTradePct / 100 × maxPositionSizeUsd)
if estimated_daily_loss ≥ dailyLossLimitUsd → transition run to STOPPING
```

This is a conservative heuristic: each failed intent counts as a full `riskPerTradePct` loss of `maxPositionSizeUsd`. In production this would be replaced by tracking actual realized PnL per fill.

**DSL example:**
```json
{
  "risk": {
    "maxPositionSizeUsd": 100,
    "riskPerTradePct": 1,
    "dailyLossLimitUsd": 50
  }
}
```

With these settings: 50 failed intents in one calendar day would trigger the limit ($0.01 × 50 × 100 = $50 estimated loss). The run transitions RUNNING → STOPPING → STOPPED.

## 5) Lab UI Improvements

### Strategy Dropdown
- Fetches `GET /strategies` on mount (requires workspace ID set in Factory)
- Shows `name (symbol · timeframe)` per option
- Selecting a strategy auto-fills the Symbol field from `strategy.symbol`
- Falls back to a plain UUID text input if no strategies are loaded (e.g. workspace not set yet)

### Trade Log Table
- Appears after a backtest completes with status DONE
- Toggle button: "Show Trade Log (N trades)" / "Hide Trade Log"
- Columns: Entry date, Exit date, Entry $, Exit $, SL $, TP $, Outcome (WIN/LOSS/NEUT), PnL %
- Color-coded: green for positive PnL, red for negative
- Data comes from `reportJson.tradeLog` (already populated by `runBacktest()` in `backtest.ts`)

## 6) Security

No changes to auth or workspace isolation. All new worker paths are internal (no HTTP surface). All Lab API endpoints retain `onRequest: [app.authenticate]` + `resolveWorkspace`.

## 7) Verification Commands

```sh
export BASE=http://localhost:3000/api/v1

# Register and get token
REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"s12test@example.com","password":"Test1234!"}')
TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
```

### enabled: false intent cancellation

```sh
# Create strategy version with enabled: false
STRAT=$(curl -s -X POST $BASE/strategies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"Disabled Strategy","symbol":"BTCUSDT","timeframe":"M15"}')
STRAT_ID=$(echo "$STRAT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

VER=$(curl -s -X POST $BASE/strategies/$STRAT_ID/versions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{
    "dslJson": {
      "id":"s12-dis","name":"Disabled","dslVersion":1,"enabled":false,
      "market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
      "entry":{"side":"Buy","signal":"manual"},
      "risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},
      "execution":{"orderType":"Market","clientOrderIdPrefix":"s12bot"},
      "guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}
    }
  }')
VER_ID=$(echo "$VER" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# Create bot + run
BOT=$(curl -s -X POST $BASE/bots \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"name\":\"Disabled Bot\",\"strategyVersionId\":\"$VER_ID\",\"symbol\":\"BTCUSDT\",\"timeframe\":\"M15\"}")
BOT_ID=$(echo "$BOT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

RUN=$(curl -s -X POST $BASE/bots/$BOT_ID/runs \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"durationMinutes":5}')
RUN_ID=$(echo "$RUN" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

sleep 6  # wait for RUNNING

# Post an intent
curl -s -X POST $BASE/runs/$RUN_ID/intents \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"intentId":"s12-dis-1","type":"ENTRY","side":"BUY","qty":0.001}'

sleep 6  # wait for worker to process

# Check intent state → should be CANCELLED
curl -s $BASE/runs/$RUN_ID/intents \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '[.[] | {intentId:.intentId, state:.state}]'
# → [{ "intentId": "s12-dis-1", "state": "CANCELLED" }]

# Check events → should have intent_cancelled
curl -s $BASE/runs/$RUN_ID/events \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '[.[] | select(.type == "intent_cancelled")]'
# → [{ "type": "intent_cancelled", "payloadJson": { "reason": "strategy disabled (enabled: false)", ... } }]
```

### dailyLossLimitUsd enforcement

The enforcement triggers automatically after FAILED intents accumulate. In practice, test by:
1. Creating a bot with `risk.dailyLossLimitUsd: 0.01` (very low, triggers on first fail)
2. Starting a run with a live ExchangeConnection and submitting an invalid order (will fail)
3. Worker poll will detect the estimated loss ≥ limit and stop the run

### Lab backtest with trade log

```sh
# Create strategy + run backtest (30-day window)
STRAT=$(curl -s -X POST $BASE/strategies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"Backtest Strategy","symbol":"BTCUSDT","timeframe":"M15"}')
STRAT_ID=$(echo "$STRAT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

BT=$(curl -s -X POST $BASE/lab/backtest \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"strategyId\":\"$STRAT_ID\",\"symbol\":\"BTCUSDT\",\"interval\":\"15\",
       \"fromTs\":\"2024-01-01T00:00:00Z\",\"toTs\":\"2024-01-31T00:00:00Z\"}")
BT_ID=$(echo "$BT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "BT_ID=$BT_ID, status=$(echo $BT | grep -o '"status":"[^"]*"')"
# → 202, status=PENDING

sleep 8  # wait for async runner

curl -s $BASE/lab/backtest/$BT_ID \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '{status:.status, trades:.reportJson.trades, winrate:.reportJson.winrate, tradeLogLen:(.reportJson.tradeLog | length)}'
# → { "status": "DONE", "trades": N, "winrate": 0.xxx, "tradeLogLen": N }
```

## 8) Acceptance Checklist (Stage 12)

- [x] `enabled: false` in DSL → PENDING intents cancelled by worker with `intent_cancelled` event
- [x] `risk.dailyLossLimitUsd` → run stopped when estimated daily loss threshold exceeded
- [x] Lab UI: strategy dropdown fetches `/strategies`, auto-fills symbol
- [x] Lab UI: fallback to text input if no strategies loaded
- [x] Lab UI: trade log table toggle shows per-trade details when backtest DONE
- [x] Trade log columns: entry/exit dates, prices, SL/TP, outcome badge, PnL% colored
- [x] All new endpoints retain `authenticate` + `resolveWorkspace()`
- [x] No new secrets exposed in API responses
- [x] Smoke test Section 12 added (12 checks)
- [x] No scope creep

## 9) Handover for Stage 13

### Deferred items

| Feature | Target Stage |
|---|---|
| `execution.maxSlippageBps` enforcement (real-time price) | Stage 13 |
| `entry.signal = "webhook"` routing to RUNNING bot | Stage 13+ |
| DSL migration (dslVersion > 1) | Stage 13+ |
| WebSocket live dashboard for bot events | Stage 13+ |
| Worker process extraction (dedicated worker) | Stage 13+ |
| Realized PnL tracking per fill (replace heuristic) | Stage 13+ |

### Stable contracts Stage 13 can rely on

| Contract | Status |
|---|---|
| `BotIntent.state` enum (PENDING/PLACED/FILLED/CANCELLED/FAILED) | Stable — CANCELLED now used by worker |
| `intent_cancelled` event type | Stable — emitted when strategy has `enabled: false` |
| `enforceDailyLossLimit()` → RUNNING → STOPPING transition | Stable |
| Lab backtest `reportJson.tradeLog` array | Stable — `TradeRecord[]` shape from `backtest.ts` |
| Strategy dropdown in Lab uses `GET /strategies` | Stable |

## 10) Deviations

None. All Stage 12 scope was implemented as planned.
`execution.maxSlippageBps` enforcement was explicitly deferred (requires real-time price feed — noted in Scope Boundaries).
