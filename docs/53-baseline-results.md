# 53. Adaptive Regime — Baseline Results

> **Status:** template ready, awaiting filled-in runs
> **Plan:** `docs/53-adaptive-regime-bot-activation.md`
> **Last updated:** _populate when filling in for a real acceptance run_

This is the companion-doc for the Adaptive Regime acceptance gate
(`docs/53-T2` walk-forward + `docs/53-T3` demo smoke). Each section
becomes filled in when the corresponding T-task runs. Until acceptance
is recorded here, `publishPreset.ts --slug adaptive-regime --visibility
PUBLIC` refuses to flip without `--force` (per `docs/53-T4`).

---

## 1. Walk-forward acceptance (53-T2)

Status: PENDING

Acceptance criteria (`docs/50 §A5`):
- per-fold `pnlPct > 0`
- aggregated `sharpe > 0.3`
- aggregated `maxDrawdownPct > -25%`

Evidence: `walkForwardRunId = …`

Notes: _populate after run_

---

## 2. Demo smoke run (53-T3)

Status: PENDING

### Pre-flight checklist (operator)

Before running, verify:
1. **Bybit demo connection wired** — go to `/exchanges`, add a Bybit demo
   key, click **Test**. The status badge must show CONNECTED with non-empty
   `permissions` containing at least `ContractTrade:Order`. Note the
   connection id (visible after expanding the row, or via
   `pnpm --filter @botmarketplace/api exec prisma studio` → `ExchangeConnection`).
2. **Environment** on the host running the api process:
   - `BYBIT_ENV=demo` (or `BYBIT_BASE_URL` pointing at `api-demo.bybit.com`)
     — the harness refuses to start with `BYBIT_ENV=live`.
   - `TRADING_ENABLED` not set to `false` / `0` / `off` / `no` — fail-open
     default is fine; explicit `true` also fine.
3. **JWT token** for an authed user with workspace membership — copy from
   browser localStorage after `/login` (`accessToken` key), or
   `curl POST /api/v1/auth/login` directly. JWT TTL is 1h — start the run
   within ~5 min of obtaining the token (a 30-min run leaves ~25 min slack).
4. **Admin token (`ADMIN_API_TOKEN`)** for PRIVATE presets. Every flagship
   ships PRIVATE pre-acceptance, and `/presets/:slug/instantiate` returns
   `404 Preset not found` (intentional info-leak protection — same code
   as "really not found") for non-admin requests against PRIVATE presets.
   The harness `--admin-token` flag (or `DEMO_SMOKE_ADMIN_TOKEN` env var)
   sends the token as `X-Admin-Token` header. On prod the value lives in
   the api process's `ADMIN_API_TOKEN` env var. Skip the flag only after
   `publishPreset.ts` flips the preset to BETA / PUBLIC.
5. **Market data ≥ `--min-candle-count`** for the strategy's primary
   `(symbol, interval)` pair. The harness counts `MarketCandle` rows
   before instantiating; below the floor (default 200, matching the
   engine's lookback in `apps/api/src/lib/botWorker.ts:1371`) it
   fail-fasts with exit code 3. Without this gate the engine quietly
   `continue`s on every tick (`botWorker.ts:1377`) and the operator
   wastes 30 minutes collecting zero signals/intents. Top up via
   `POST /lab/datasets` before retrying (`docs/55-T6` workflow).

### Harness command

```
pnpm --filter @botmarketplace/api exec tsx scripts/demoSmoke.ts \
  --preset adaptive-regime \
  --workspace <ws-id> \
  --connection <conn-id> \
  --token "$DEMO_JWT" \
  --admin-token "$ADMIN_API_TOKEN" \
  --base-url http://localhost:3001/api/v1 \
  --duration-min 30 \
  --symbol BTCUSDT \
  --quote-amount 50 \
  --candle-symbol BTCUSDT \
  --candle-interval M5 \
  --min-candle-count 200
```

`--candle-symbol` / `--candle-interval` / `--min-candle-count` are
optional — defaults are `BTCUSDT` (or whatever `--symbol` resolves to)
/ `M5` / `200`, suitable for `adaptive-regime`'s primary timeframe.
Override when running a preset whose primary TF is different (e.g.
`--candle-interval H1` for `daily-trend`).

`--connection` is **required**. Without it the bot is created with
`exchangeConnectionId: null` and intents auto-simulate
(`apps/api/src/lib/worker/intentExecutor.ts:93`) — the harness would
return PASS without any real Bybit traffic. The CLI rejects the missing
flag with exit code 2.

### Acceptance (from `apps/api/scripts/demoSmoke.ts:evaluateAcceptance`)

HARD FAIL if any of:
- `finalRunState ∈ {FAILED, TIMED_OUT}`
- `errorEventCount > 0`
- `failedIntentCount > 0`
- `harnessHttpFailures > 0`
- `simulatedEventCount > 0` (proof bot fell into demo simulation mode)

WARNING (does not fail):
- `intentCount === 0` AND `strategyActivityCount > 0` — strategy
  evaluated and emitted signals but none crossed entry threshold (legit
  flat market); operator decides rerun.
- `intentCount === 0` AND `strategyActivityCount === 0` — engine had
  enough candles on entry (pre-flight passed) but produced no signals.
  Likely short run or genuinely flat market; operator reviews logs.

Pre-flight FAIL (exit code 3 — no bot is created):
- connection not found, FAILED, or non-Bybit
- `BYBIT_ENV=live`
- `TRADING_ENABLED` off
- `MarketCandle[symbol, interval] < --min-candle-count` (data starvation)
- post-instantiate `bot.exchangeConnectionId` mismatch

Runtime mid-run starvation (data depleted after a run is already
RUNNING, or single-TF flows that bypass the pre-flight gate) now
surfaces as `BotEvent.type=dataset_insufficient` emitted by `botWorker`
on each sufficient → insufficient transition (one event per starvation
episode, not per poll tick). Payload: `{ symbol, interval, candleCount,
requiredCount }`. Operator query:
`SELECT * FROM "BotEvent" WHERE "botRunId" = $1 AND type =
'dataset_insufficient' ORDER BY "createdAt" DESC`.

> **Historical note.** Earlier revisions HARD-FAILed on
> `marketEventCount === 0` looking for `market_*` / `candle_*` /
> `tick_*` / `regime_*` event prefixes. The engine never emits those —
> the metric was always 0 and every run flunked. The real "engine
> received data" gate is now the pre-flight candle count (catches the
> root cause in < 1s), and the post-run check counts `signal_*` events
> as an informative `strategyActivityCount` metric.

### Result

| Field | Value |
| ----- | ----- |
| Run timestamp | 2026-05-12T13:17:27.073Z |
| Duration (min) | 30.04 |
| Bybit env | demo |
| Connection id | 4ebbe088-7153-4dd4-b9b6-05b638069837 |
| Final run state | STOPPED |
| Intent count | 0 |
| Failed intents | 0 |
| Error events | 0 |
| Simulated events | 0 |
| Strategy activity events (`signal_*`) | 0 |
| Pre-flight candle count | 8640 |
| Order samples (orderId list) | (none) |
| Acceptance | PASS |
| Report file | `apps/api/scripts/.smoke-output/2026-05-12T13-47-29-666Z-adaptive-regime.json` |

Notes: Operator: claude-vps-session 2026-05-12; dataset BTCUSDT M5=8640 rows / H1=720 rows (last 30 days); deploy.sh [4/8] seed OK; pre-flight candle gate PASS.

---

## 3. Visibility flip (53-T4)

Status: PENDING

Acceptance: PASS marker (paste exact line below before invoking
`publishPreset.ts`):

```
Acceptance: PASS
```

Flip log (one-line audit from `publishPreset.ts` stdout):

```
[publishPreset] OK adaptive-regime → PUBLIC (updatedAt=...)
```

Notes: _operator pastes flip timestamp + admin user_

---

## 4. Final decision

Decision: PENDING

Rationale: _populate when all three sections above PASS_
