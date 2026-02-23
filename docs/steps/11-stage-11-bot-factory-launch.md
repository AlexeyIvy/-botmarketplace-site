# Stage 11 — Bot Factory Launch Flow

## Status: DONE

## 1) Scope

- Bot creation UI: strategy+version selector (dropdown from workspace strategies), optional ExchangeConnection selector, auto-fill symbol from DSL
- `durationMinutes` support in run start (UI + API)
- Run history table in Bot Detail page (GET /bots/:id/runs, click row to load events)
- Bug fix: `factory/page.tsx` Quick Start demo setup was creating an invalid DSL stub — replaced with a valid Stage-10 v1 DSL
- OpenAPI updated: proper Bot/Run schemas and all endpoints documented
- Smoke-test Section 11: 14 new checks

## 2) Scope Boundaries (what is NOT in Stage 11)

- No SL/TP logic
- No WebSocket / streaming dashboard
- No advanced strategy runtime optimization
- No production-grade orchestration / queue refactor
- No multi-bot scheduler
- No DSL migration (Stage 12+)
- No `entry.signal = "webhook"` routing (Stage 11+ API endpoint exists but routing is deferred)
- No `risk.dailyLossLimitUsd` enforcement (deferred)
- No `execution.maxSlippageBps` enforcement (deferred)
- No `enabled: false` runtime respect (deferred)

## 3) What Was Already Ready (Stage 10 Groundwork)

All backend API endpoints were complete from Stage 10 groundwork:

| Endpoint | Stage |
|---|---|
| `POST /bots` | Stage 10 groundwork |
| `GET /bots` | Stage 10 groundwork |
| `GET /bots/:id` | Stage 10 groundwork |
| `GET /bots/:id/runs` | Stage 10 groundwork |
| `POST /bots/:id/runs` (with durationMinutes) | Stage 10 groundwork |
| `GET /bots/:id/runs/:runId` | Stage 10 groundwork |
| `POST /bots/:id/runs/:runId/stop` | Stage 10 groundwork |
| `GET /runs/:runId` | Stage 10 groundwork |
| `GET /runs/:runId/events` | Stage 10 groundwork |
| `POST /runs/:runId/signal` | Stage 10 groundwork |
| botWorker QUEUED → RUNNING lifecycle | Stage 10 groundwork |
| `BotRun.durationMinutes` per-run timeout | Stage 10 groundwork |
| `Bot.exchangeConnectionId` nullable FK | Stage 10 groundwork |

Stage 11 focused on closing the UI gap and documenting the contract properly.

## 4) Files Changed

| File | Change |
|------|--------|
| `apps/web/src/app/factory/page.tsx` | Fix: demo setup DSL was invalid (`kind: demo` stub) — replaced with valid Stage-10 v1 DSL |
| `apps/web/src/app/factory/bots/page.tsx` | Rewrite: strategy+version dropdown, ExchangeConnection dropdown, symbol auto-fill from DSL |
| `apps/web/src/app/factory/bots/[id]/page.tsx` | Update: durationMinutes input, exchange connection display, run history table |
| `docs/openapi/openapi.yaml` | Add: Bot/Run/Event schemas, all Stage 11 endpoints documented |
| `deploy/smoke-test.sh` | Add: Section 11 (14 checks) |
| `docs/steps/11-stage-11-bot-factory-launch.md` | NEW — this file |

## 5) Security

All Bot/Run endpoints from Stage 10 groundwork already have:
- `onRequest: [app.authenticate]` (JWT required)
- `resolveWorkspace(request, reply)` (workspace membership enforced)
- Cross-workspace access returns 404 (workspace isolation — resource hidden, not 403)
- Without auth: 401

ExchangeConnection secrets:
- `encryptedSecret` never returned in any API response
- `apiKey` never returned in any Bot/Run/Event API response
- Exchange credentials only used internally (decrypt → pass to exchange client)

## 6) Verification Commands

```sh
export BASE=http://localhost:3000/api/v1

# Register and get token
REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"s11test@example.com","password":"Test1234!"}')
TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
```

### Full Bot Factory Launch Flow

```sh
# 1) Create strategy
STRAT=$(curl -s -X POST $BASE/strategies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"S11 Strategy","symbol":"BTCUSDT","timeframe":"M15"}')
STRAT_ID=$(echo "$STRAT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# 2) Create strategy version (valid DSL v1)
VER=$(curl -s -X POST $BASE/strategies/$STRAT_ID/versions \
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
  }')
VER_ID=$(echo "$VER" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "VER_ID=$VER_ID"
# → valid UUID

# 3) Create bot from strategy version
BOT=$(curl -s -X POST $BASE/bots \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d "{\"name\":\"S11 Bot\",\"strategyVersionId\":\"$VER_ID\",\"symbol\":\"BTCUSDT\",\"timeframe\":\"M15\"}")
BOT_ID=$(echo "$BOT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "BOT_ID=$BOT_ID"
# → 201, bot with status DRAFT

# 4) Start run with 5-minute limit
RUN=$(curl -s -X POST $BASE/bots/$BOT_ID/runs \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"durationMinutes":5}')
RUN_ID=$(echo "$RUN" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "RUN_ID=$RUN_ID state=$(echo $RUN | grep -o '"state":"[^"]*"')"
# → 201, state QUEUED

# 5) Get run status (worker advances state within ~5s)
sleep 5
curl -s $BASE/runs/$RUN_ID \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | grep -o '"state":"[^"]*"'
# → "state":"RUNNING"

# 6) Get event log
curl -s $BASE/runs/$RUN_ID/events \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '[.[] | {type:.type, at:.payloadJson.at}]'
# → [RUN_CREATED, RUN_QUEUED, RUN_STARTING, RUN_SYNCING, RUN_RUNNING, ...]

# 7) Stop run
curl -s -X POST $BASE/bots/$BOT_ID/runs/$RUN_ID/stop \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '{state:.state, stoppedAt:.stoppedAt}'
# → { "state": "STOPPED", "stoppedAt": "..." }

# 8) List run history
curl -s $BASE/bots/$BOT_ID/runs \
  -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '[.[] | {state:.state, durationMinutes:.durationMinutes}]'
# → [{ "state": "STOPPED", "durationMinutes": 5 }]
```

### Stop scenario → STOPPED state

```sh
# Already shown above — stop mid-run → state = STOPPED, stoppedAt set
```

### Timeout scenario (durationMinutes)

```sh
# Start run with durationMinutes=1 (worker will TIMED_OUT after ~1 min)
RUN_TIMEOUT=$(curl -s -X POST $BASE/bots/$BOT_ID/runs \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"durationMinutes":1}')
TID=$(echo "$RUN_TIMEOUT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
sleep 90  # wait for worker to tick
curl -s $BASE/runs/$TID -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  jq '{state:.state, errorCode:.errorCode}'
# → { "state": "TIMED_OUT", "errorCode": "MAX_DURATION_EXCEEDED" }
```

### Without auth → 401

```sh
curl -s $BASE/bots | jq .status
# → 401
curl -s $BASE/runs/fake-id/events | jq .status
# → 401
```

### Cross-workspace → 404

```sh
REG2=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"other@example.com","password":"Test1234!"}')
TOKEN2=$(echo "$REG2" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID2=$(echo "$REG2" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)

curl -s $BASE/bots/$BOT_ID \
  -H "Authorization: Bearer $TOKEN2" \
  -H "X-Workspace-Id: $WS_ID2" | jq .status
# → 404
```

### No secrets in responses

```sh
curl -s $BASE/bots/$BOT_ID -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  grep -c "encryptedSecret\|apiKey\|passwordHash"
# → 0
curl -s $BASE/runs/$RUN_ID/events -H "Authorization: Bearer $TOKEN" -H "X-Workspace-Id: $WS_ID" | \
  grep -c "encryptedSecret\|apiKey"
# → 0
```

## 7) Acceptance Checklist (Stage 11)

- [x] Bot Factory Launch Flow works end-to-end (strategy version → bot → run → events → stop)
- [x] Bot created from StrategyVersion (with DSL contract freeze from Stage 10)
- [x] Run starts and state advances through worker lifecycle (QUEUED → RUNNING)
- [x] Stop scenario works: POST /bots/:id/runs/:runId/stop → STOPPED
- [x] Timeout scenario: durationMinutes respected, run → TIMED_OUT with errorCode
- [x] ExchangeConnection visible in bot detail UI (ID shown if set)
- [x] All endpoints protected by `authenticate` + `resolveWorkspace()`
- [x] Cross-workspace access returns 404 (workspace isolation)
- [x] No secrets (encryptedSecret, apiKey) in any API response
- [x] Problem Details (RFC 9457) on all errors
- [x] OpenAPI updated (Bot/Run/Event schemas + all endpoints)
- [x] Run history table in UI (click row → loads events for that run)
- [x] durationMinutes input in UI for Start Run
- [x] Strategy+Version dropdown in bot creation UI
- [x] ExchangeConnection dropdown in bot creation UI
- [x] factory/page.tsx demo setup uses valid DSL (bug fixed)
- [x] Smoke test Section 11 added (14 checks)
- [x] Handover notes for Stage 12 written below
- [x] No scope creep
- [x] Verification commands reproducible

## 8) Handover for Stage 12 (Research Lab Results & Reproducibility)

### Stable contracts Stage 12 can rely on

| Contract | Status |
|---|---|
| `StrategyVersion.dslJson` shape (frozen v1 DSL) | Stable — `docs/schema/strategy.schema.json` |
| `BotRunState` enum (CREATED→…→STOPPED/FAILED/TIMED_OUT) | Stable — `src/lib/stateMachine.ts` |
| `BotEvent.type` labels | Stable — `RUN_CREATED`, `RUN_QUEUED`, `RUN_STARTING`, `RUN_SYNCING`, `RUN_RUNNING`, `RUN_STOPPING`, `RUN_STOPPED`, `RUN_TIMED_OUT`, `RUN_FAILED`, `signal_generated` |
| `BotIntent` model (ENTRY/EXIT/SL/TP/CANCEL, PENDING/PLACED/FILLED/CANCELLED/FAILED) | Stable |
| `GET /runs/:runId/events` API | Stable |
| `BacktestResult` model in Prisma | Exists (Stage 12 will populate) |

### Stage 12 inputs from Stage 11

- `StrategyVersion.dslJson` (frozen DSL) — backtest runner reads `market`, `entry`, `risk`, `execution` from it
- `BotRun.id` — backtest result links to strategy for reproducibility tracking
- `GET /runs/:runId/events` — can replay signal/transition log for research analysis

### Deferred items (for Stage 12+)

| Feature | Target Stage |
|---|---|
| Backtest / replay runner | Stage 12 |
| DSL migration (dslVersion > 1) | Stage 12+ |
| `risk.dailyLossLimitUsd` enforcement | Stage 12 |
| `execution.maxSlippageBps` enforcement | Stage 12 |
| `enabled: false` runtime respect | Stage 12 |
| `entry.signal = "webhook"` routing to RUNNING bot | Stage 12+ |
| Result persistence & UI report (PnL, winrate, drawdown) | Stage 12 |

## 9) Deviations

None. All Stage 11 scope was implemented as planned. The backend API was fully available from Stage 10 groundwork — Stage 11 focused on UI completion, OpenAPI documentation, and smoke testing.
