# SC001 — C9-S1 Scheduled Post-Funding Relative Premium Normalization Sentinel v0.1

Date: 2026-09-18  
Status: **FROZEN SELECTION/CALIBRATION SENTINEL BEFORE FIRST C9 OUTCOME**  
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c9-d1-v0.3-funding-archive-integrity-pass-result-v0.1.md`;
- `docs/research/sc001-c9-d2-mark-index-15m-integrity-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.9.json`;
- `docs/research/sc001-c1-c6-second-pass-knowledge-extraction-audit-v0.1.md`.

## 1. Purpose

Test the cheapest outcome-bearing version of the C9 scheduled derivative-state mechanism without threshold shopping.

Question:

> After a scheduled nonzero funding event, does the perpetual mark move relative to its index in the direction of post-funding normalization with enough gross magnitude to justify later paired-execution research?

This is Selection/Calibration only.

A SURVIVE does not prove executable profitability.

## 2. Frozen variant budget

Exactly **one** strategy-mechanism variant.

No funding-rate magnitude threshold.

No parameter grid.

No alternative horizons.

No time-of-day choice because all published funding events are used.

No auxiliary RB001/RB003/RB005/RB006 feature.

Total C9-S1 first-pass strategy variants:

`1`

## 3. Event universe

Assets exactly:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

Funding events:

- exact September 2024 funding archive;
- event timestamp `T` must satisfy:
  `2024-09-01T00:00:00Z <= T < 2024-10-01T00:00:00Z`;
- funding rate must be finite and nonzero.

No event is selected by outcome magnitude.

## 4. Causal mark/index state

D2 15-minute normalized candles use candle-start timestamps.

At funding timestamp `T`:

### Pre-event observable state

Use the candle:

`[T-15m, T)`

Its final close is observable at exactly `T`.

Define:

`pre_premium_bps = 10000 * (mark_close / index_close - 1)`

### Post-event outcome

Use the candle:

`[T+15m, T+30m)`

Its final close is observable at `T+30m`.

Define:

`post_premium_bps = 10000 * (mark_close / index_close - 1)`

No candle final value from after `T` enters the signal/state side.

## 5. Frozen economic direction

Funding sign alone fixes the hypothesized post-event relative direction:

- positive funding -> rich-perpetual normalization direction is SHORT relative premium;
- negative funding -> cheap-perpetual normalization direction is LONG relative premium.

No sign is chosen from observed outcomes.

Define:

`funding_sign = +1` for positive funding, `-1` for negative funding.

Primary gross relative response:

`signed_normalization_bps = -funding_sign * (post_premium_bps - pre_premium_bps)`

Positive value means the mark/index premium moved in the post-funding normalization direction.

## 6. Execution architecture and screening hurdle

The mechanism is treated prospectively as a paired relative-value T3 family:

- perpetual leg entry/exit;
- spot/index-proxy hedge leg entry/exit;
- four structural fills per cycle.

Selection reference:

- 5 bps per taker fill;
- four-fill fee reference floor = 20 bps;
- screening gross hurdle = `30 bps`.

Mark/index is an idealized mechanism proxy, not executable historical fills.

A sentinel SURVIVE only justifies later exact spot/perp execution and cost work.

## 7. Sample/breadth requirements

Require all:

- pooled evaluable event-asset observations >= 500;
- each of 8 assets has >= 60 evaluable nonzero-funding events;
- events span >= 25 UTC calendar days;
- positive-funding observations >= 20 pooled;
- negative-funding observations >= 20 pooled.

If either funding-sign side has fewer than 20 pooled observations, do not invent a threshold or separate winner side; retain the fixed rule and report the sign-breadth limitation.

## 8. Economic gates

C9-S1 survives only if all:

- 10% trimmed mean pooled signed normalization >= `30 bps`;
- pooled median signed normalization >= `20 bps`;
- equal-weight asset mean signed normalization >= `30 bps`;
- median asset mean signed normalization >= `20 bps`;
- at least 6/8 asset means are positive;
- equal-weight UTC calendar-day mean signed normalization >= `30 bps`;
- positive UTC calendar-day share >= `0.60`.

These gates mirror the conservative four-fill structural philosophy used elsewhere in SC001.

## 9. Terminal states

SURVIVE:

`C9_S1_SENTINEL_SURVIVE`

REJECT:

`C9_S1_REJECT_SENTINEL`

DEFER sign/sample limitation:

`C9_S1_DEFER_SAMPLE_OR_SIGN_BREADTH`

DEFER is allowed only if economic gates cannot be interpreted credibly because the fixed event universe fails the sample/sign-breadth requirements.

Do not lower the funding threshold because there is no threshold.

Do not change the 30-minute horizon after output.

## 10. Strategy Evidence Report

Write:

`~/sc001_data/SC001_C9_S1_SENTINEL/c9_s1_strategy_evidence_v0_1.json`

Report:

- terminal status;
- pooled event count;
- funding sign counts;
- per-asset event count;
- per-asset mean response;
- pooled trimmed mean/median;
- equal-weight asset mean;
- median asset mean;
- positive-asset count;
- day count;
- equal-weight day mean;
- positive-day share;
- frozen gates and failed gates.

No promoted net PnL is calculated.

## 11. Feature / Building-Block Evidence Report

Write separately:

`~/sc001_data/SC001_C9_S1_SENTINEL/c9_s1_feature_block_evidence_v0_1.json`

Declared blocks:

### C9-F1 funding sign state
- primitive P8;
- role R2/R1 event-direction input;
- no magnitude threshold.

### C9-F2 scheduled funding clock
- primitive P11;
- role R2 deterministic event context.

### C9-F3 mark/index premium
- primitive P8/P7;
- role R6 reference/state.

### RB008 causal reference semantics
- role R6.

The feature report must distinguish:

- measurement validity;
- sign breadth;
- directional response;
- economic magnitude;
- evidence maturity = `SELECTION_CALIBRATION_ONLY`.

Do not create a global `works=true` field.

## 12. Parent integrity requirements

Before outcome:

Require exact local:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS`

and:

`C9_D2_MARK_INDEX_15M_INTEGRITY_PASS`.

Re-verify:

- exact September funding file byte size/SHA against D1 report;
- exact D2 normalized file byte size/SHA against D2 report;
- October funding body is not opened by S1;
- October UTC mark/index is not opened by S1.

## 13. No-rescue rules

After S1 output do not:

- add a funding magnitude threshold;
- choose only positive or only negative funding after seeing results;
- change horizon;
- add basis threshold;
- add volatility, flow, trend or time filters;
- select historical winner assets;
- change from paired to directional architecture merely because the 30 bps hurdle fails.

A materially different future funding mechanism requires a new candidate/experiment ID.

## 14. Interpretation

A rejection means the **frozen scheduled post-funding relative-normalization mechanism** lacks the required calibration headroom.

It does not mean funding state, mark/index premium or scheduled-event context is globally useless.

Any reusable feature conclusion is recorded separately in the Feature/Building-Block report.
