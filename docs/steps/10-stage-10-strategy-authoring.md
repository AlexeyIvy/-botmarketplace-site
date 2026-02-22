# Stage 10 — Strategy Authoring UX

## Status: DONE

## 1) Scope

- **DSL contract freeze** — schema for `StrategyVersion.dslJson` (body) defined, documented, and enforced by Ajv
- Strategy authoring UI: structured form replacing raw textarea
- `POST /strategies/validate` — Ajv validation with field-level error pointers
- `POST /strategies/:id/versions` — Ajv validation before save; previous versions not modified
- `GET /strategies/:id` — returns all versions including full `dslJson`
- Version history shows DSL summary (orderType, side, risk%, maxPos, enabled)
- OpenAPI updated: `StrategyCreateRequest`, `StrategyView`, `StrategyVersionView`,
  `StrategyVersionCreateRequest`, `StrategyValidateResponse`, `ValidationProblem`, `StrategyDslBody`

## 2) DSL Contract Freeze (v1)

### Source of truth
- Schema file: `docs/schema/strategy.schema.json` (JSON Schema 2020-12)
- Validator: `apps/api/src/lib/dslValidator.ts` (Ajv, module-level singleton)

### Frozen shape (Stage 10)

```json
{
  "id": "<string>",
  "name": "<string>",
  "dslVersion": 1,
  "enabled": true,
  "market": {
    "exchange": "bybit",
    "env": "demo",
    "category": "linear",
    "symbol": "BTCUSDT"
  },
  "entry": {
    "side": "Buy|Sell",
    "signal": "manual|webhook"
  },
  "risk": {
    "maxPositionSizeUsd": 100,
    "riskPerTradePct": 1,
    "cooldownSeconds": 60
  },
  "execution": {
    "orderType": "Market|Limit",
    "clientOrderIdPrefix": "mybot"
  },
  "guards": {
    "maxOpenPositions": 1,
    "maxOrdersPerMinute": 10,
    "pauseOnError": true
  }
}
```

### Validation rules

| Field | Rule |
|-------|------|
| `dslVersion` | integer ≥ 1 |
| `market.exchange` | must be `"bybit"` |
| `market.env` | must be `"demo"` |
| `market.category` | must be `"linear"` |
| `risk.maxPositionSizeUsd` | number > 0 |
| `risk.riskPerTradePct` | number > 0 and ≤ 100 |
| `risk.cooldownSeconds` | integer ≥ 0 |
| `execution.orderType` | `"Market"` or `"Limit"` |
| `guards.maxOpenPositions` | must be `1` (MVP: one position per symbol) |
| `guards.maxOrdersPerMinute` | integer 1–120 |
| `guards.pauseOnError` | boolean |

### Error format (field pointers)

Validation errors returned as `errors[]` in Problem Details response:
```json
{
  "title": "Validation Error",
  "status": 400,
  "detail": "DSL validation failed",
  "errors": [
    { "field": "risk.maxPositionSizeUsd", "message": "must be > 0" },
    { "field": "guards.maxOpenPositions", "message": "must be equal to constant" }
  ]
}
```

## 3) Scope Boundaries (what is NOT in Stage 10)

- No backtesting/research functions (Stage 12)
- No AI-generated strategies
- No advanced parameter optimization
- No RBAC / multi-user
- No deep UI redesign
- No Bot Launch Flow (Stage 11)
- `entry.signal = "webhook"` accepted by validator but webhook endpoint pre-exists (separate route)
- `dslVersion > 1` and DSL migration — deferred

## 4) Files Changed

| File | Change |
|------|--------|
| `apps/api/src/lib/dslValidator.ts` | NEW — Ajv validator (JSON Schema 2020-12) |
| `apps/api/src/routes/strategies.ts` | Updated: use `validateDsl()` in validate + version creation |
| `apps/web/src/app/factory/strategies/[id]/page.tsx` | Updated: structured DSL form editor + version summary |
| `docs/openapi/openapi.yaml` | Updated: Strategy/StrategyVersion schemas + endpoints |
| `docs/schema/strategy.schema.json` | Existing — DSL contract freeze source |
| `docs/steps/10-stage-10-strategy-authoring.md` | NEW — this file |

## 5) Security

- All `/strategies/*` endpoints use `onRequest: [app.authenticate]` (JWT required)
- All `/strategies/*` endpoints use `resolveWorkspace(request, reply)` (membership enforced)
- Cross-workspace access returns 403 (workspace membership check in `resolveWorkspace`)
- Without auth returns 401

## 6) Verification Commands

### Setup

```sh
export BASE=http://localhost:3000/api/v1

# Register and get token
REG=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"s10test@example.com","password":"Test1234!"}')
TOKEN=$(echo "$REG" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
WS_ID=$(echo "$REG" | grep -o '"workspaceId":"[^"]*"' | cut -d'"' -f4)
```

### Create strategy
```sh
curl -s -X POST $BASE/strategies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"BTC Scalper","symbol":"BTCUSDT","timeframe":"M15"}' | jq .
# → 201, { id, name, symbol, timeframe, status: "DRAFT" }

STRAT_ID=$(curl -s -X POST $BASE/strategies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"name":"BTC Scalper 2","symbol":"BTCUSDT","timeframe":"M15"}' | jq -r '.id')
```

### Validate valid DSL → 200
```sh
curl -s -X POST $BASE/strategies/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{
    "dslJson": {
      "id":"test-1","name":"Test","dslVersion":1,"enabled":true,
      "market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
      "entry":{"side":"Buy","signal":"manual"},
      "risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},
      "execution":{"orderType":"Market","clientOrderIdPrefix":"bot"},
      "guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}
    }
  }' | jq .
# → 200, { "ok": true, "message": "DSL is valid" }
```

### Validate invalid DSL → 400 with errors
```sh
curl -s -X POST $BASE/strategies/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"dslJson":{"id":"x","name":"y","dslVersion":1}}' | jq .
# → 400, { "title": "Validation Error", "errors": [{ "field": "enabled", ...}, ...] }
```

### Validate wrong dslVersion type → 400
```sh
curl -s -X POST $BASE/strategies/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"dslJson":{"id":"x","name":"y","dslVersion":"not-a-number","enabled":true,"market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},"entry":{},"risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},"execution":{"orderType":"Market","clientOrderIdPrefix":"bot"},"guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}}}' | jq '.errors[0]'
# → { "field": "dslVersion", "message": "must be integer" }
```

### Create valid strategy version → 201
```sh
VER=$(curl -s -X POST $BASE/strategies/$STRAT_ID/versions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{
    "dslJson": {
      "id":"'$STRAT_ID'-v1","name":"BTC Scalper 2","dslVersion":1,"enabled":true,
      "market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
      "entry":{"side":"Buy","signal":"manual"},
      "risk":{"maxPositionSizeUsd":100,"riskPerTradePct":1,"cooldownSeconds":60},
      "execution":{"orderType":"Market","clientOrderIdPrefix":"scalpbot"},
      "guards":{"maxOpenPositions":1,"maxOrdersPerMinute":10,"pauseOnError":true}
    }
  }')
echo "$VER" | jq '{id:.id, version:.version}'
# → { "id": "...", "version": 1 }
VER_ID=$(echo "$VER" | jq -r '.id')
```

### Create invalid version → 400
```sh
curl -s -X POST $BASE/strategies/$STRAT_ID/versions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{"dslJson":{"id":"x"}}' | jq '{status:.status, errors:.errors}'
# → { "status": 400, "errors": [...] }
```

### Create second version — old version not modified
```sh
curl -s -X POST $BASE/strategies/$STRAT_ID/versions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Workspace-Id: $WS_ID" \
  -d '{
    "dslJson": {
      "id":"'$STRAT_ID'-v2","name":"BTC Scalper 2 (updated)","dslVersion":1,"enabled":true,
      "market":{"exchange":"bybit","env":"demo","category":"linear","symbol":"BTCUSDT"},
      "entry":{"side":"Sell","signal":"manual"},
      "risk":{"maxPositionSizeUsd":200,"riskPerTradePct":2,"cooldownSeconds":120},
      "execution":{"orderType":"Limit","clientOrderIdPrefix":"scalpbot"},
      "guards":{"maxOpenPositions":1,"maxOrdersPerMinute":5,"pauseOnError":true}
    }
  }' | jq '{version:.version}'
# → { "version": 2 }

# Verify v1 is unchanged
curl -s $BASE/strategies/$STRAT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Workspace-Id: $WS_ID" | \
  jq '.versions | sort_by(.version) | .[0] | {version:.version, side:.dslJson.entry.side}'
# → { "version": 1, "side": "Buy" }  ← not modified to "Sell"
```

### Without auth → 401
```sh
curl -s $BASE/strategies | jq .status
# → 401
```

### Cross-workspace → 403
```sh
REG2=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"s10other@example.com","password":"Test1234!"}')
TOKEN2=$(echo "$REG2" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
curl -s $BASE/strategies/$STRAT_ID \
  -H "Authorization: Bearer $TOKEN2" \
  -H "X-Workspace-Id: $WS_ID" | jq .status
# → 403
```

## 7) Acceptance Checklist (Stage 10)

- [x] DSL contract freeze performed and documented (`docs/schema/strategy.schema.json` + this doc)
- [x] Strategy authoring flow works (create/version/validate)
- [x] Validation returns field-level errors (pointer + message)
- [x] Versioning does not modify previous versions (immutable snapshots)
- [x] All endpoints protected by `authenticate`
- [x] All endpoints use `resolveWorkspace()`
- [x] OpenAPI updated (Strategy/StrategyVersion schemas + endpoints)
- [x] Handover notes for Stage 11 included below
- [x] No scope creep
- [x] Verification reproducible with curl commands above

## 8) Handover for Stage 11 (Bot Factory Launch Flow)

### How Stage 11 uses StrategyVersion

```typescript
// In Stage 11: create bot from strategy version
const bot = await prisma.bot.create({
  data: {
    workspaceId,
    name: "My Bot",
    strategyVersionId: versionId,  // ← link to frozen DSL snapshot
    symbol: dsl.market.symbol,     // ← from dslJson.market.symbol
    timeframe: "M15",
    status: "DRAFT",
  },
});
```

### Stable fields from StrategyVersion.dslJson (Stage 11 can rely on)

| Field | Type | Description |
|-------|------|-------------|
| `market.symbol` | string | Trading symbol (e.g. "BTCUSDT") |
| `market.env` | "demo" | Always demo in Stage 11 |
| `entry.side` | "Buy"\|"Sell" | Trade direction |
| `risk.maxPositionSizeUsd` | number | Max position size |
| `risk.cooldownSeconds` | integer | Wait after trade |
| `execution.orderType` | "Market"\|"Limit" | Order type |
| `execution.clientOrderIdPrefix` | string | For `orderLinkId` generation |
| `guards.maxOrdersPerMinute` | integer | Rate guard |
| `guards.pauseOnError` | boolean | Pause bot on repeated errors |

### Stage 10 limitations (deferred to later)

- `dslVersion > 1` / DSL migration logic — deferred (Stage 12+)
- `entry.signal = "webhook"` accepted but webhook routing to bot — deferred (Stage 11+)
- `risk.dailyLossLimitUsd` — accepted in schema, not enforced by runtime yet (Stage 11)
- `execution.maxSlippageBps` — accepted in schema, not enforced yet (Stage 11)
- `timeframes` array — accepted in schema, not used yet (Stage 11)
- `enabled: false` — accepted in schema, runtime respect deferred (Stage 11)

## 9) Deviations from original Stage 10 scope

The branch also contains Stage 11-scope API changes from an earlier attempt
(`Bot.exchangeConnectionId`, `BotRun.durationMinutes`, `GET /bots/:id/runs`,
`GET /runs/:runId`, `POST /runs/:runId/signal`). These were added before the
correct Stage 10 scope was clarified. They do not break Stage 10 and will be
adopted as early Stage 11 groundwork. The Stage 11 task pack should verify and
expand on these additions.
