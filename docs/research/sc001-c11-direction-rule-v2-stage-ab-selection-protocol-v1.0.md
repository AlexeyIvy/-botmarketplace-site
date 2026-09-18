# SC001 — C11 Direction Rule v2 + Stage A/B Selection Protocol v1.0

Date: 2026-09-19
Status: **FROZEN DESIGN BEFORE C11 V2 SELECTION PRICE-BODY ACCESS**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-v2-selection-metadata-preflight-pass-result-v0.3.md`;
- `docs/research/sc001-c11-v2-chronology-freeze-v0.1.md`;
- `docs/research/sc001-c11-direction-rule-v2-research-plan-v0.1.md`;
- `docs/research/sc001-c11-c12-three-role-current-state-review-v0.1.md`;
- `docs/research/sc001-c11-s0-event-move-headroom-sentinel-v0.1.md`.

## 1. Purpose

Resolve C11 v2 on the exact frozen 24-event nonpromotional Selection/Calibration chronology while separating:

1. data validity;
2. residual post-decision absolute headroom;
3. actionable opportunity retention;
4. directional continuation.

Execution/fill/PnL remains closed.

## 2. Frozen chronology

Exactly 24 scheduled releases:

- 12 Consumer Price Index;
- 12 Employment Situation;

from the binding chronology freeze.

No event may be added, removed or reclassified by price outcome.

The full scheduled denominator is always `24`.

## 3. Source

Instrument:

`BTC-USDT-SWAP`

Use only the exact daily trade archives qualified by:

`C11_V2_SC_METADATA_PREFLIGHT_PASS`

Before opening a body, re-resolve the same exact archive and require HEAD Content-Length to equal the metadata-preflight value.

No alternate venue or archive substitution.

## 4. Frozen causal anchors

For release timestamp `T`:

### Pre anchor

Chronologically last trade with:

`trade_ts < T`

Require:

`T - trade_ts <= 1000 ms`.

### +1 second anchor

Chronologically last trade with:

`trade_ts <= T + 1s`

Require:

`(T + 1s) - trade_ts <= 1000 ms`.

### +60 seconds anchor

Chronologically last trade with:

`trade_ts <= T + 60s`

Require:

`(T + 60s) - trade_ts <= 1000 ms`.

No interpolation.

No future trade relative to any anchor.

If any required anchor is absent/stale after the archive passes structural integrity:

`signal_state = DATA_INVALID`.

## 5. Frozen Direction Rule v2

For every DATA_VALID event:

`first_impulse_bps = 10000 * ln(price_1s / price_pre)`

Signal state:

- `first_impulse_bps > 0` -> `LONG`;
- `first_impulse_bps < 0` -> `SHORT`;
- `first_impulse_bps == 0` -> `NO_TRADE`.

Exact zero is a valid market observation, not data failure.

No epsilon threshold.

No 2s/5s/10s comparison.

No reversal sign.

No macro-surprise input.

## 6. Structural burden reference

Keep the inherited screening reference:

- two future taker fills;
- fee reference = 10 bps total;
- event spread/slippage/model reserve = 10 bps;
- total structural burden = `20 bps`.

This remains a screening hurdle, not an exact execution-cost claim.

The hurdle may not be lowered after outcome.

## 7. Data-validity gate

Before any Stage A or Stage B verdict, require:

- data-valid events >= `22 / 24`;
- CPI data-valid >= `11 / 12`;
- Employment data-valid >= `11 / 12`.

Rationale:

The event sample must remain essentially complete while allowing at most one objective anchor/source failure per family.

If this gate fails:

`C11_V2_SC_DEFER_DATA_QUALITY`

and:

- Stage A verdict = NOT_COMPUTED;
- Stage B verdict = NOT_COMPUTED;
- uncomputed metrics serialize as null.

No event substitution.

## 8. Stage A — residual post-decision headroom

For each DATA_VALID event:

`abs_residual_move_1s_to_60s_bps = 10000 * abs(ln(price_60s / price_1s))`

Stage A SURVIVE requires all:

1. events with residual absolute move >=20 bps >= `12 / 24 scheduled`;
2. median residual absolute move across DATA_VALID events >= `20 bps`;
3. CPI events with residual absolute move >=20 bps >= `5 / 12 scheduled CPI`;
4. Employment events with residual absolute move >=20 bps >= `5 / 12 scheduled Employment`.

Primary count denominators remain scheduled slots; DATA_INVALID therefore cannot improve the breadth counts.

Diagnostics only, not verdict gates:

- p75 residual absolute move;
- maximum residual absolute move.

If data-quality gate passes but any Stage A gate fails:

`C11_V2_SC_REJECT_RESIDUAL_HEADROOM`

Stage B verdict remains NOT_COMPUTED.

## 9. Stage B — direction + opportunity retention

Stage B is computed only after Stage A SURVIVE.

Actionable:

`signal_state in {LONG, SHORT}`

NO_TRADE remains in the 24-event opportunity denominator.

### Opportunity-retention gates

Require all:

1. actionable events >= `18 / 24` = 75%;
2. CPI actionable >= `8 / 12`;
3. Employment actionable >= `8 / 12`.

This prevents survival on a tiny selected subset.

### Signed continuation

For actionable event:

`direction = +1 for LONG, -1 for SHORT`

`signed_continuation_1s_to_60s_bps = direction * 10000 * ln(price_60s / price_1s)`

Directional/economic SURVIVE gates require all:

1. median signed continuation across actionable events >= `20 bps`;
2. scheduled events with signed continuation >=20 bps >= `10 / 24`;
3. CPI events with signed continuation >=20 bps >= `4 / 12`;
4. Employment events with signed continuation >=20 bps >= `4 / 12`.

Diagnostics only:

- positive signed-continuation count/share;
- p75 signed continuation;
- worst signed continuation;
- best signed continuation.

If Stage A passes but any Stage B gate fails:

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

If all data, Stage A and Stage B gates pass:

`C11_V2_SC_SURVIVE_TO_PROSPECTIVE_CONFIRMATION`

## 10. Why these gates are not copied from H1

H1-2025 is contaminated for v2 design.

The new gates are structural, not fitted to the H1 values:

- 20 bps comes from the previously frozen two-fill burden reference;
- half of all scheduled events must retain >=20 bps residual headroom;
- 75% of scheduled events must remain actionable;
- both CPI and Employment must contribute;
- median actionable signed continuation itself must clear the 20 bps structural hurdle;
- high quantiles are removed from the verdict.

The H1 p75/max outcomes are not used as v2 thresholds.

## 11. Required report semantics

Always report:

- scheduled slots = 24;
- data-valid;
- DATA_INVALID;
- actionable;
- NO_TRADE;
- LONG;
- SHORT;
- CPI and Employment counts at every relevant funnel stage.

Funnel:

`scheduled -> data_valid -> actionable -> executed`

For this stage:

`executed = NOT_COMPUTED`

because execution remains closed.

Any metric blocked by DEFER or prior-stage REJECT must serialize as `null`, not zero.

Include:

`verdict_computed`

per stage.

## 12. One-shot / no rescue

After Selection outcome do not:

- change 1 second;
- change +60 second horizon;
- introduce nonzero impulse threshold;
- switch continuation to reversal;
- drop NO_TRADE events from scheduled denominator;
- select CPI-only or Employment-only;
- use macro surprise;
- add C5/C10 vetoes;
- lower 20 bps;
- alter actionability or breadth gates;
- add an entry-delay search.

A materially different extractor requires a separate candidate/experiment and cannot reuse this Selection chronology as fresh evidence.

## 13. Confirmation firewall

Prospective Confirmation remains closed unless exact Selection result is:

`C11_V2_SC_SURVIVE_TO_PROSPECTIVE_CONFIRMATION`

Confirmation must reuse this exact:

- anchor semantics;
- 1-second direction rule;
- NO_TRADE semantics;
- 20 bps burden;
- data-validity gates;
- Stage A gates;
- Stage B gates.

No retuning after Selection.

## 14. Execution firewall

Even Confirmation SURVIVE does not prove profitability.

Only after Confirmation survives may an event execution/slippage/fill/PnL protocol be frozen.

Selection stage must keep false:

- execution model calculated;
- PnL calculated;
- Confirmation outcome accessed;
- promotional alpha accessed.
