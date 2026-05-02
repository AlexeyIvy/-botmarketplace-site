# 54. Production Go / No-Go Gate

> **Type:** audit checklist (template)
> **Status:** template ready, awaiting acceptance for individual flagships
> **Owner:** tech lead + product lead + ops lead (joint)
> **Plan:** `docs/54-T6`
> **Last updated:** _populate when filling in for a real gate_

## Purpose

This document is the audit checklist used to make a deliberate, recorded
decision about enabling **live trading** on the platform. A decision of
**GO** is only valid when all nine sections below have `Status: PASS`,
**or** the rationale for any non-PASS status is explicitly written below
that section's `Notes:` field and accepted by all three sign-off owners.

Live trading remains gated by the `BYBIT_ENV=live` environment switch
and the global `TRADING_ENABLED` admin flag (see §5 below) regardless of
the outcome here — this gate authorises the operators to flip those
switches, it does not bypass them.

A separate sub-gate exists for the funding-arb BETA preset; see
`docs/55-T6` and the criterion described in §1 below.

## How to use this template

1. Copy this file to a dated companion-doc, e.g.
   `docs/54-go-no-go-gate-2026-MM-DD.md`, when running an actual gate.
2. Fill in `Status:`, `Evidence:` and `Notes:` for each of the nine
   sections.
3. Record the final decision in the **Decision** section at the bottom
   with rationale.
4. Commit the filled-in companion-doc — git history is the audit trail.
5. Leave this template file unchanged so it can be re-used.

## Companion documents

- `docs/53-baseline-results.md` — adaptive-regime acceptance baseline.
- `docs/54-baseline-results.md` — DCA / MTF / SMC acceptance baselines.
- `docs/55-baseline-results.md` — funding-arb acceptance baseline (BETA track, separate sub-gate).

---

## 1. Strategy acceptance

All four non-funding flagships must clear acceptance before live is
considered. Funding-arb is on its own BETA track (`docs/55-T6`) and
does not block this gate; flip its sub-gate independently.

For each preset (`adaptive-regime`, `dca-momentum`, `mtf-scalper`,
`smc-liquidity-sweep`):

- `walkForwardRunId` — valid, acceptance criteria met (see plan §54-T1/T2/T3 / §53-T2 — runId persisted in Postgres).
- `demoSmokeRunId` (or `.smoke-output/` recording) — 30-minute Bybit-demo run completed without unhandled errors.
- Golden DSL fixture / sanity / smoke-replay tests — green on `main` for the commit being shipped.

| Preset | walkForwardRunId | demoSmokeRunId | CI test status |
|---|---|---|---|
| `adaptive-regime`     | _fill_ | _fill_ | _PASS / FAIL_ |
| `dca-momentum`        | _fill_ | _fill_ | _PASS / FAIL_ |
| `mtf-scalper`         | _fill_ | _fill_ | _PASS / FAIL_ |
| `smc-liquidity-sweep` | _fill_ | _fill_ | _PASS / FAIL_ |

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _link to companion-docs / Postgres rows / CI run_
`Notes:`

---

## 2. Security review

- `docs/05-security.md` and `docs/06-threat-model.md` reviewed within the last **30 days** before this gate.
- Audit checklist run against every endpoint introduced under `docs/51` (preset system) and `docs/55` (funding-arb routes / spot dual-key reconciler):
  - **Secrets management:** `apiKey`, `encryptedSecret`, and the new `spotEncryptedSecret` (docs/55-T5) all encrypted at rest via `apps/api/src/lib/crypto.ts`; rotation path verified.
  - **Rate limiting:** every external endpoint that hits Bybit has a per-workspace cap.
  - **Auth:** `onRequest: [app.authenticate]` on every non-public route; admin-only routes verified.
  - **Idempotency:** `BotIntent.intentId` + unique `orderLinkId` on every order placement path, including the new hedge-leg intents (`hedge-<id>-{spot,perp}-{entry,exit}`).
  - **Input validation:** zod / fastify schemas on every new endpoint body.

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _link to security review notes / commit SHAs of last review_
`Notes:`

---

## 3. Ops runbook

`docs/15-operations.md` contains explicit, copy-pasteable procedures for:

- **Stop all bots in emergency** — single command / admin action that flips `TRADING_ENABLED=false` and drains in-flight intents.
- **Roll a preset back from PUBLIC to PRIVATE without deleting it** — e.g. via `publishPreset.ts --visibility PRIVATE`.
- **Diagnose a stuck `botRun`** — query template, expected lease state, manual unstick procedure.
- **Halt funding-arb worker only** — flip `ENABLE_HEDGE_WORKER=false` (introduced in `docs/55-T4`) without affecting the main `botWorker`.

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _runbook section anchors_
`Notes:`

---

## 4. Observability

Minimum live-ready observability surface:

- **a)** ERRORED bot-run count over rolling 5-minute and 15-minute windows; alert on a sudden spike (threshold documented in alert config).
- **b)** p95 latency of `POST /bots/:id/start`.
- **c)** Bybit API error rate (separate counters for linear vs spot endpoints — the latter introduced by docs/55-T1).
- **d)** Circuit-breaker triggered count (the daily-loss / error-pause guards in `safetyGuards.ts`).
- **e)** _funding-arb only:_ `HedgePosition.status = FAILED` count, alert on first occurrence per day.

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _dashboard links / alert rule IDs_
`Notes:`

---

## 5. Kill switch

A global admin flag (`TRADING_ENABLED=false`) exists and has been tested
end-to-end:

- Flipping `TRADING_ENABLED=false` rejects all new outbound `bybitPlaceOrder` calls with a typed `TradingDisabledError` (implemented in `apps/api/src/lib/tradingKillSwitch.ts`, guard wired into `apps/api/src/lib/bybitOrder.ts`).
- Existing in-flight intents are NOT auto-cancelled — the placement error classifies as `transient`, so the worker retry loop picks them up once the flag flips back on. Intents do not drift to FAILED simply because trading was paused.
- The flag is documented in `docs/15-operations.md §6.3` and is reachable from the on-call runbook within 60 seconds.
- The hedge worker (`docs/55-T4`) routes its leg orders through the same `bybitPlaceOrder` (once 55-T2 wires the spot leg), so it inherits the kill-switch automatically — no separate flag.
- Read-only paths (status fetch, market-data, balance reconciliation) are deliberately NOT guarded so operators can keep diagnosing during an incident.

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _commit SHAs / smoke-test record_
`Notes:`

---

## 6. Liability

- Legal disclaimer present on Lab Library landing page and on the **Bot Create** UI step:
  > _"Trading involves risk. Past performance is not indicative of future results."_
- Disclaimer text reviewed and approved by product / legal owner.
- BETA presets (currently `funding-arb`) carry an additional warning badge with text approved by product / legal.

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _UI screenshots / approval thread_
`Notes:`

---

## 7. Capacity / cost

- Estimated DB load (queries per second, write volume) under `N` simultaneously running bots, where `N` is the agreed first-pilot user count.
- Estimated Bybit API rate-limit usage at the same `N` — separately for `linear` and `spot` (the latter is the new pressure introduced by `docs/55`).
- Headroom: estimate stays under **70%** of every measured limit at peak.
- Storage growth projection over a 90-day horizon, with the existing `MarketCandle` retention job assumed to be running.

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _capacity calc spreadsheet / load-test run_
`Notes:`

---

## 8. Rollback procedure

A documented, rehearsed rollback path exists for the case where a critical bug is discovered after go-live:

1. **Stop new bot starts** — feature flag flip / admin gate within 5 minutes of the decision.
2. **Notify active users** — email / in-app banner template ready, owner identified.
3. **Hotfix or rollback** — either deploy hotfix to the offending commit, or roll the runtime back to a prior known-good tag and unset `BYBIT_ALLOW_LIVE`.
4. **Funding-arb specific** — if the bug is in the multi-leg path, flip `ENABLE_HEDGE_WORKER=false` and audit any open `HedgePosition` for the OPEN / CLOSING states; document any manual unwinds.

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _runbook anchor / rehearsal record_
`Notes:`

---

## 9. Sign-off

Decision is recorded by three roles. All three must sign for a `GO`.
A `NO-GO` from any single role is sufficient to block the gate.

| Role | Name | Decision | Date |
|---|---|---|---|
| Tech lead    | _name_ | GO / NO-GO / DEFERRED | _YYYY-MM-DD_ |
| Product lead | _name_ | GO / NO-GO / DEFERRED | _YYYY-MM-DD_ |
| Ops lead     | _name_ | GO / NO-GO / DEFERRED | _YYYY-MM-DD_ |

`Status:` _PASS / FAIL / PENDING_
`Evidence:` _commit SHA of this filled-in companion-doc, audit log entry_
`Notes:`

---

## Decision

**Outcome:** _GO / NO-GO / DEFERRED_

**Effective date:** _YYYY-MM-DD_

**Scope of GO (if GO):**
- Live trading enabled for: _list of preset slugs that the GO covers_
- Excluded (remain on demo): _list of preset slugs explicitly NOT yet live_
- Initial pilot user cap: _number_

**Rationale:**
_one paragraph summarising why the decision was reached, with explicit reference to any non-PASS section above and the agreed mitigation_

**Re-review date (if DEFERRED):**
_YYYY-MM-DD or condition for re-running this gate_
