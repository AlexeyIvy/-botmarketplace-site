# Stage 11 — Bot Factory Launch Flow

## Status: DONE

## 1) Scope

Full Bot Factory launch flow: create a bot from a strategy version, start/stop runs,
inject trading signals, and execute intents via exchange connections (or demo-sim).

### Deliverables

| Deliverable | Description |
|-------------|-------------|
| Bot CRUD | `POST/GET /bots`, `GET /bots/:id`, `PATCH /bots/:id` |
| Run lifecycle | `POST /bots/:id/runs`, `GET /bots/:id/runs`, `POST /bots/:id/runs/:runId/stop` |
| Run queries | `GET /bots/:botId/runs/:runId`, `GET /runs/:runId` |
| Signal injection | `POST /runs/:runId/signal` → BotIntent (idempotent, `intentId`) |
| Intent queries | `GET /runs/:runId/intents`, `POST /runs/:runId/intents` |
| Intent execution | Bot worker: PENDING → PLACED/FILLED (demo-sim or Bybit live) |
| Bot.status sync | DRAFT → ACTIVE when run is live; ACTIVE → DRAFT when all runs terminate |
| Emergency ops | `POST /runs/stop-all`, `POST /runs/reconcile` |
| Run events | `GET /runs/:runId/events` |
| Run heartbeat | `POST /runs/:runId/heartbeat` |
| State PATCH | `PATCH /runs/:runId/state` |
| Factory UI | Bot detail: intents table + events log with live polling |

## 2) Bot.status Lifecycle

| Trigger | Bot.status |
|---------|-----------|
| Bot created | `DRAFT` |
| Run reaches `RUNNING` (worker) | `ACTIVE` |
| All runs reach terminal state | `DRAFT` |
| (Future) explicit user disable | `DISABLED` |

## 3) Intent Execution Flow

```
POST /runs/:runId/signal
  → BotIntent created (state=PENDING)
  → Bot worker poll (every 4s)
  → processIntents() finds PENDING intents on RUNNING runs
  → atomically claim: state PENDING → PLACED (updateMany)
  → if no exchangeConnection:
      state → FILLED, metaJson.simulated=true, event=intent_simulated
  → if exchangeConnection present:
      decrypt secret, call bybitPlaceOrder()
      on success: orderId set, event=intent_placed
      on error:   state → FAILED, metaJson.error, event=intent_failed
```

### Idempotency

Signal endpoint (`POST /runs/:runId/signal`) accepts an optional `intentId`.
If the same `intentId` is submitted twice for the same run, the existing intent
is returned with status 200 (not 201). Workers use `updateMany` with a state
filter to avoid double-execution.

## 4) API Endpoints (Stage 11 additions)

### PATCH /bots/:id

Update bot metadata. Bot must belong to the caller's workspace.

**Request body** (all fields optional):
```json
{ "name": "New Name", "exchangeConnectionId": "<uuid-or-null>" }
```

**Responses:**
- `200` — updated bot object
- `400` — no updatable fields / invalid value
- `404` — bot not found or not in workspace
- `409` — name already taken in workspace

### GET /runs/:runId/intents

List intents for a run, ordered by creation time. Optional `?state=PENDING|PLACED|...` filter.

### POST /runs/:runId/intents

Alternative low-level intent creation (separate from signal endpoint).
Requires: `{ intentId, type, side, qty }`.

### PATCH /runs/:runId/intents/:intentId/state

Manually advance intent state. Cannot update terminal intents (FILLED/CANCELLED/FAILED).

## 5) Files Changed

| File | Change |
|------|--------|
| `apps/api/src/lib/botWorker.ts` | Added `processIntents()`, `executeIntent()`, `syncBotStatus()` |
| `apps/api/src/lib/crypto.ts` | Added `getEncryptionKeyRaw()` (no Fastify reply needed) |
| `apps/api/src/routes/bots.ts` | Added `PATCH /bots/:id` |
| `apps/api/src/routes/runs.ts` | Full run lifecycle (carry-over from Stage 10 groundwork) |
| `apps/api/src/routes/intents.ts` | Intent CRUD (carry-over from Stage 10 groundwork) |
| `apps/web/src/app/factory/bots/[id]/page.tsx` | Added intents table + Bot.status coloring |
| `docs/steps/11-stage-11-bot-factory-launch.md` | This file |
| `deploy/smoke-test.sh` | Added Section 11 smoke tests |

## 6) Security

- All endpoints require `authenticate` (JWT Bearer)
- All endpoints use `resolveWorkspace()` — cross-workspace access returns 403
- `exchangeConnectionId` verified to belong to workspace before use
- `SECRET_ENCRYPTION_KEY` required for live intent execution; missing key = FAILED intent
- Intents in terminal state (FILLED/CANCELLED/FAILED) cannot be re-processed

## 7) Verification Commands

### Setup

```sh
export BASE=http://localhost:3000/api/v1

REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"s11test@example.com","password":"Test1234!"}')
TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
```

### Create strategy + version

```sh
STRAT_ID=$(curl -s -X POST $BASE/strategies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"S11 Strategy","symbol":"BTCUSDT","timeframe":"M15"}' | jq -r '.id')

VER_ID=$(curl -s -X POST $BASE/strategies/$STRAT_ID/versions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{
    "dslJson": {
      "id":"s11-v1","name":"S11 Strategy","dslVersion":1,"enabled":true,
      "market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
      "entry":{"side":"Buy","signal":"manual"},
      "risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},
      "execution":{"orderType":"Market","clientOrderIdPrefix":"s11bot"},
      "guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}
    }
  }' | jq -r '.id')
```

### Create and update bot

```sh
BOT_ID=$(curl -s -X POST $BASE/bots \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"name\":\"S11 Bot\",\"strategyVersionId\":\"$VER_ID\",\"symbol\":\"BTCUSDT\",\"timeframe\":\"M15\"}" \
  | jq -r '.id')

# PATCH: rename bot
curl -s -X PATCH $BASE/bots/$BOT_ID \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"S11 Bot Renamed"}' | jq '.name'
# → "S11 Bot Renamed"
```

### Start run → wait for RUNNING → inject signal

```sh
RUN_ID=$(curl -s -X POST $BASE/bots/$BOT_ID/runs \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{}' | jq -r '.id')

# Check Bot.status → ACTIVE (after worker advances to RUNNING)
sleep 4
curl -s $BASE/bots/$BOT_ID \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | jq '.status'
# → "ACTIVE"

# Wait for RUNNING state
sleep 4
curl -s $BASE/runs/$RUN_ID \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | jq '.state'
# → "RUNNING"

# Inject signal (demo-sim: no exchange connection)
INTENT_ID=$(uuidgen)
curl -s -X POST $BASE/runs/$RUN_ID/signal \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"side\":\"BUY\",\"qty\":0.001,\"intentId\":\"$INTENT_ID\"}" | jq '{state:.state}'
# → { "state": "PENDING" }

# After worker poll (~4s): check intent state
sleep 6
curl -s $BASE/runs/$RUN_ID/intents \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '.[0] | {state:.state, simulated:.metaJson.simulated}'
# → { "state": "FILLED", "simulated": true }
```

### Stop run → Bot.status back to DRAFT

```sh
curl -s -X POST $BASE/bots/$BOT_ID/runs/$RUN_ID/stop \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | jq '.state'
# → "STOPPED" or "STOPPING"

sleep 6
curl -s $BASE/bots/$BOT_ID \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | jq '.status'
# → "DRAFT"
```

## 8) Acceptance Checklist (Stage 11)

- [x] `PATCH /bots/:id` updates name and exchangeConnectionId
- [x] Bot.status = ACTIVE when run is live; = DRAFT when all runs terminate
- [x] `POST /runs/:runId/signal` → BotIntent (PENDING), idempotent by intentId
- [x] Bot worker: `processIntents()` executes PENDING intents on RUNNING runs
- [x] Demo-sim mode: intent → FILLED + event `intent_simulated` (no exchange connection)
- [x] Live mode: intent → PLACED via Bybit (or FAILED if bad credentials)
- [x] Optimistic locking: `updateMany(where: PENDING)` prevents double-execution
- [x] `GET /runs/:runId/intents` returns intent list
- [x] UI: bot detail shows intents table with state coloring + events log
- [x] All endpoints protected by `authenticate` + `resolveWorkspace()`
- [x] Stage 11 smoke tests pass (Section 11 in smoke-test.sh)
- [x] No scope creep

## 9) Handover for Stage 12 (Research Lab)

- `dslVersion > 1` and DSL migration — deferred
- `entry.signal = "webhook"` — webhook routing to running bot deferred
- Order fill polling (PLACED → FILLED from exchange) — deferred
- `risk.dailyLossLimitUsd` enforcement — deferred
- `execution.maxSlippageBps` enforcement — deferred
- `enabled: false` runtime respect — deferred
- Backtest integration with bot strategy — Stage 12 scope
