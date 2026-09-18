# SC001 — C11-S1 First-Impulse Continuation Sentinel v0.1

Date: 2026-09-18
Status: **FROZEN BEFORE FIRST C11 DIRECTIONAL OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c11-s0-event-move-headroom-survive-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.17.json`.

## 1. Purpose

Test whether the first fully causal 1-second BTC impulse after a scheduled CPI / Employment release predicts enough same-direction continuation through +60 seconds to justify later execution modeling.

No macro surprise values are used.

## 2. Frozen event batch

Exactly the same 12 H1-2025 events used by C11-S0.

No event may be added, removed, reclassified or selected by outcome.

## 3. Frozen causal anchors

For event timestamp `T`:

### Pre-event anchor
Chronologically last trade with:

`trade_ts < T`

and staleness <=1000 ms.

### +1s anchor
Chronologically last trade with:

`trade_ts <= T+1s`

and staleness <=1000 ms.

### +60s anchor
Chronologically last trade with:

`trade_ts <= T+60s`

and staleness <=1000 ms.

No interpolation and no future trade relative to an anchor.

## 4. First impulse

`first_impulse_bps = 10000 * ln(price_1s / price_pre)`

Require nonzero sign.

Frozen direction:

- positive impulse -> long continuation direction;
- negative impulse -> short continuation direction.

No sign flip after outcome.

## 5. Frozen continuation statistic

`signed_continuation_1s_to_60s_bps = sign(first_impulse_bps) * 10000 * ln(price_60s / price_1s)`

This measures only the gross move still available after the first 1 second has been observed.

## 6. Structural burden

Keep the same conservative later-execution reference:

- taker entry after the first impulse;
- taker exit;
- 10 bps total fee reference;
- 10 bps event execution/slippage reserve;
- structural burden = `20 bps`.

## 7. Sample gates

Require:

- all 12 events have valid pre, +1s and +60s anchors;
- all 12 first impulses are nonzero.

Otherwise:

`C11_S1_DEFER_SAMPLE`

## 8. Continuation survival gates

SURVIVE only if all:

- positive signed continuation events >= `8 / 12`;
- events with signed continuation >=20 bps >= `6 / 12`;
- median signed continuation >= `20 bps`;
- p75 signed continuation >= `30 bps`.

Exact survive token:

`C11_S1_FIRST_IMPULSE_CONTINUATION_SURVIVE`

If sample gates pass but any continuation gate fails:

`C11_S1_REJECT_FIRST_IMPULSE_CONTINUATION`

## 9. Interpretation

SURVIVE means only that the first causal one-second impulse retains enough same-direction gross move to justify a later event execution/slippage model.

It does not establish net PnL.

REJECT means the raw C11-S0 move largely occurs before or against the first causal post-release direction.

## 10. No-rescue rules

After output do not:

- use 2s/5s/10s impulse instead;
- flip to reversal;
- split CPI vs Employment;
- drop weak events;
- use macro surprise;
- lower 20 bps;
- attach C5/C10 vetoes;
- search entry delays.

A different event-direction mechanism requires a new candidate ID.

## 11. Firewalls

Must remain false:

- macro_release_value_accessed;
- macro_surprise_calculated;
- execution_fill_model_calculated;
- pnl_calculated;
- promotional_alpha_accessed.
