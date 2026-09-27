# SC001 — B13-C S0 Offline Outcome Computation Protocol v0.1

Date: 2026-09-27  
Status: **FROZEN AFTER PRICE-ANCHOR DATASET PASS, BEFORE ANY RETURN CALCULATION**  
Scope: `SCALPING RESEARCH / SC001 / B13-C / S0 / OUTCOME`

## 1. Immutable price-anchor parent

Dataset freeze PASS:

`B13C_S0_PRICE_ANCHOR_DATASET_FREEZE_PASS`

Frozen file identities:
- `price_anchor_extraction_manifest.json`
  SHA256 `79db43a19249c8f56f886cf01616f3e56704d4a8fc8e5c5e03609254b2de1acf`
- `price_anchors.jsonl`
  SHA256 `5f84f40a91c3a7bc57bf3c4e878a53130ef696a28be162c014c10f8253223a1e`

Frozen counts:
- total cluster rows = 1,905;
- valid-price clusters = 1,793;
- missing entry only = 25;
- missing exit only = 75;
- missing both = 12.

No return was computed before this protocol freeze.

## 2. Valid analytical sample

Use only rows with:

`valid_price_cluster = true`

Require exactly:

`1,793`

No missing anchor may be imputed.

No cluster may be added, dropped for performance, weighted by liquidation size, or ranked by symbol.

## 3. Frozen signed outcome

For each valid cluster:

`raw_log_return_bps = 10000 * ln(P_exit / P_entry)`

`signed_reversal_bps = reversal_sign * raw_log_return_bps`

where:
- LONG_LIQUIDATED => reversal_sign = +1;
- SHORT_LIQUIDATED => reversal_sign = -1.

The stored canonical reversal_sign must be used.

No alternative sign, horizon, entry delay or price is authorized.

## 4. Pooled statistics

Sort all 1,793 `signed_reversal_bps` values ascending.

Report:
- n;
- median;
- p25;
- p75;
- strictly-positive count;
- positive-cluster share.

### Quantile convention

For p in {0.25, 0.50, 0.75} use deterministic linear interpolation equivalent to Hyndman-Fan type 7 / NumPy default:

`h = (n - 1) * p`

`lo = floor(h)`
`hi = ceil(h)`
`q = x[lo] + (h-lo)*(x[hi]-x[lo])`

if lo=hi, q=x[lo].

No alternate quantile convention may be substituted after outcome.

### Positive cluster

A cluster is positive iff:

`signed_reversal_bps > 0`

Zero is not positive.

## 5. Complete-day breadth diagnostic

Complete UTC days are exactly:

- 2026-09-20
- 2026-09-21
- 2026-09-22
- 2026-09-23
- 2026-09-24
- 2026-09-25

Assign each valid cluster to a day using the UTC date of:

`cluster_end_ms`

For each day report:
- valid cluster count;
- median signed_reversal_bps using the same type-7 p=0.50 rule.

A day is positive iff its median is strictly >0.

If a complete day has zero valid clusters:
- daily median = null;
- positive = false.

No other day is used for the 4-of-6 breadth gate.

Partial Sep19 and Sep26 remain in pooled statistics only.

## 6. Frozen S0 decision

Sample gate:

`valid_price_clusters >= 100`

Headroom gate:

`pooled median signed_reversal_bps >= 30.0`

Positive-share gate:

`positive_cluster_share >= 0.55`

Breadth gate:

`positive complete-day medians >= 4 of 6`

If all four pass:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_SURVIVE`

If sample >=100 and any of the other three gates fails:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`

If sample <100:

`B13C_S0_DEFER_SAMPLE`

No rescue tuning is permitted on this interval.

## 7. Output restriction

The outcome report may contain only:
- pooled aggregate statistics;
- the six complete-day counts/medians;
- gate booleans;
- terminal S0 classification.

Do **not** emit:
- per-cluster return rows;
- per-symbol performance;
- liquidation-size strata;
- alternate horizons;
- PnL.

## 8. Interpretation

SURVIVE means only that the simple reversal mechanism has sufficient gross 30-second headroom/breadth to justify a separate execution-cost feasibility stage.

REJECT closes this exact S0 architecture on the protected interval. Do not rescue it by changing cluster gap, minimum event count, size threshold, direction purity, entry delay, or horizon.

Neither classification is final live-trading proof.
