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
   browser localStorage after `/login` (`accessToken` key).

### Harness command

```
pnpm --filter @botmarketplace/api exec tsx scripts/demoSmoke.ts \
  --preset adaptive-regime \
  --workspace <ws-id> \
  --connection <conn-id> \
  --token "$DEMO_JWT" \
  --base-url http://localhost:3001/api/v1 \
  --duration-min 30 \
  --symbol BTCUSDT \
  --quote-amount 50
```

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
- `marketEventCount === 0` (engine never received any market data)

WARNING (does not fail):
- `intentCount === 0` while `marketEventCount > 0` — legit flat market;
  operator decides rerun.

Pre-flight FAIL (exit code 3 — no bot is created):
- connection not found, FAILED, or non-Bybit
- `BYBIT_ENV=live`
- `TRADING_ENABLED` off
- post-instantiate `bot.exchangeConnectionId` mismatch

### Result

| Field | Value |
| ----- | ----- |
| Run timestamp |  |
| Duration (min) |  |
| Bybit env | demo \| live \| unknown |
| Connection id |  |
| Final run state |  |
| Intent count |  |
| Failed intents |  |
| Error events |  |
| Simulated events | 0 (must be 0) |
| Market events |  |
| Order samples (orderId list) |  |
| Acceptance | PASS \| FAIL |
| Report file | `apps/api/scripts/.smoke-output/<ts>-adaptive-regime.json` |

Notes: _operator pastes summary excerpt + sign-off here. Cross-check
`Order samples` on bybit.com → Demo Trading → Order History — they must
appear as real demo orders._

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
