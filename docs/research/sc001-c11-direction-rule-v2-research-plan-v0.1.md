# SC001 — C11 Direction Rule v2 Research Plan v0.1

Date: 2026-09-18
Status: **NON-ALPHA DESIGN PLAN / NO NEW PRICE OUTCOME AUTHORIZED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.70.md`;
- `docs/research/sc001-strategy-landscape-v0.7.md`;
- `docs/research/sc001-c11-c12-three-role-current-state-review-v0.1.md`;
- `docs/research/sc001-c11-s0-event-move-headroom-survive-result-v0.1.md`;
- `docs/research/sc001-c11-s1-2025-05-02-zero-first-impulse-diagnostic-v0.1.md`.

## 1. Objective

Continue C11 without rescue-tuning by separating three questions that were previously partly conflated:

1. **Residual post-decision headroom** — how much absolute move remains after a causal decision point?
2. **Direction quality** — can one prospectively frozen rule choose the sign of that remaining move?
3. **Execution reality** — can realistic event execution preserve the gross edge?

C11-S0 already established large raw 60-second movement.

C11-S1 v0.1 did not reach a directional verdict because one valid event produced an exactly zero first one-second impulse.

## 2. Binding prior state

Remain unchanged:

- `C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`;
- `C11_S1_DEFER_SAMPLE`.

The S1 DEFER is not a REJECT.

H1-2025 is contaminated for C11 directional-rule design and cannot be reused as fresh evidence for a modified rule.

## 3. Signal-state semantics required for v2

Future signal code must distinguish explicitly:

- `DATA_INVALID`;
- `NO_TRADE`;
- `LONG`;
- `SHORT`.

A valid event with a non-actionable/zero direction statistic is `NO_TRADE`, not `DATA_INVALID`.

A DEFER condition caused by missing/stale data must be semantically separate from a valid abstention.

## 4. Preferred minimal-complexity v2 direction rule

Preferred design to critically review and, if accepted, freeze:

`1-second post-release impulse sign`

with:

- impulse >0 -> LONG;
- impulse <0 -> SHORT;
- impulse =0 -> NO_TRADE.

Why preferred:

- smallest change from S1 v0.1;
- explicitly solves the zero-impulse state without changing the causal window;
- does not search 2s/5s/10s alternatives;
- minimizes new degrees of freedom.

This is a design preference only until fresh chronology and all gates are frozen.

## 5. No window search

Forbidden within C11 v2:

- comparing 1s vs 2s vs 5s vs 10s on the same fresh outcomes;
- switching from continuation to reversal after outcome;
- choosing CPI-only or Employment-only after outcome;
- using macro surprise values;
- adding C5/C10 veto features;
- optimizing entry delay.

A different direction statistic/window requires a separate experiment design.

## 6. Fresh chronology gate

Before any v2 price-bearing run:

1. audit candidate historical periods for prior SC001 use;
2. choose a fresh chronology by calendar rule, not price outcome;
3. freeze event families to CPI + Employment only;
4. verify official BLS schedule metadata;
5. verify exact BTC-USDT-SWAP historical trade-source availability;
6. split prospectively into:
   - Selection/Calibration;
   - untouched Confirmation.

No price outcome may be opened before the chronology split is frozen.

## 7. Stage A — residual post-decision headroom

On the frozen fresh Selection/Calibration batch, before judging direction quality, measure:

`abs_residual_move_1s_to_60s_bps = 10000 * abs(ln(price_60s / price_1s))`

Purpose:

Determine whether enough movement remains after the decision latency.

This answers a different question from C11-S0.

Required reporting:

- total scheduled events;
- data-valid events;
- median residual absolute move;
- count above the structural burden;
- event-family breadth.

Exact gates must be frozen before outcome.

## 8. Stage B — directional continuation with opportunity retention

Using the already frozen v2 direction rule:

For actionable LONG/SHORT events:

`signed_continuation_1s_to_60s_bps = direction * 10000 * ln(price_60s / price_1s)`

Required denominator/accounting:

- total scheduled events;
- data-valid events;
- actionable events;
- NO_TRADE events;
- actionable share;
- CPI actionable count;
- Employment actionable count;
- signed-continuation count above burden;
- median signed continuation.

A rule cannot survive solely because it trades a tiny subset.

## 9. Opportunity-retention layer

Future reports must preserve the funnel:

`scheduled -> data-valid -> actionable -> executed`

At the direction stage, `executed` remains closed.

A matched denominator must be used in all later BASE vs auxiliary comparisons.

## 10. Statistical design

Because scheduled macro events are small-N:

Primary future gates should emphasize:

- counts;
- median;
- actionable share;
- family breadth.

High quantiles may be diagnostic but should not dominate the verdict.

Raw event count must not be treated as IID high-frequency evidence.

## 11. Confirmation gate

Untouched Confirmation remains closed unless both Selection/Calibration components survive:

1. residual post-decision headroom;
2. direction + opportunity-retention.

Confirmation must reuse the exact frozen rules with no threshold/window changes.

## 12. Execution stage

Only after untouched Confirmation survives may C11 proceed to event execution modeling.

Execution stage must model at minimum:

- taker entry after the frozen decision point;
- taker exit;
- event spread/slippage;
- latency;
- conservative fill price semantics;
- missed/partial fill policy if relevant;
- net economics after the same structural burden framework.

No execution model before confirmation.

## 13. Platform/research-kernel improvements

Add common semantic fields to reusable research outputs:

- `signal_state`: DATA_INVALID / NO_TRADE / LONG / SHORT;
- `verdict_computed`: true/false;
- metrics that were not computed must serialize as null, not synthetic zero;
- opportunity funnel counts.

This is a framework improvement and does not change past verdicts.

## 14. C12 disposition

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

Do not rescue.

Retain:

- RB019 direct stablecoin parity-stress state;
- collateral/risk-warning interpretation;
- rare-event research value on future fresh evidence only.

## 15. C13+ gate

Do not open a new independent base candidate while C11 remains structurally alive and the fresh v2 direction design has not been resolved.

## 16. Immediate next actions

1. perform a contamination/source audit for candidate fresh C11 chronology;
2. select and freeze Selection/Calibration + untouched Confirmation calendars;
3. freeze residual-headroom gates;
4. freeze v2 direction/opportunity-retention gates;
5. only then implement and run the fresh C11 v2 experiment.

No VPS price-bearing run is authorized before these freezes.
