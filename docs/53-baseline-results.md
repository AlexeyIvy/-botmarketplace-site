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

Harness:

```
pnpm --filter @botmarketplace/api exec tsx scripts/demoSmoke.ts \
  --preset adaptive-regime \
  --workspace <ws-id> \
  --token "$DEMO_JWT" \
  --base-url http://localhost:3001/api/v1 \
  --duration-min 30 \
  --symbol BTCUSDT \
  --quote-amount 50
```

Acceptance (from `apps/api/scripts/demoSmoke.ts:evaluateAcceptance`):
- `finalRunState ∉ {FAILED, TIMED_OUT}`
- `errorEventCount === 0`
- `failedIntentCount === 0`
- `harnessHttpFailures === 0`
- `intentCount > 0` (warning if 0; operator decides rerun)

| Field | Value |
| ----- | ----- |
| Run timestamp |  |
| Duration (min) |  |
| Final run state |  |
| Intent count |  |
| Failed intents |  |
| Error events |  |
| Acceptance | PASS \| FAIL |
| Report file | `apps/api/scripts/.smoke-output/<ts>-adaptive-regime.json` |

Notes: _operator pastes summary excerpt + sign-off here_

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
