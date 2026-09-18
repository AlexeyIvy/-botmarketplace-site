# SC001 — C9-D0 OKX Funding / Mark / Index Data-Semantics Protocol v0.1

Date: 2026-09-18  
Status: **FROZEN DATA-ONLY PROTOCOL — NO RETURN / SIGNAL / PNL AUTHORIZED**  
Scope: `SCALPING RESEARCH / SC001`

Parent:

- `docs/research/sc001-c9-scheduled-funding-mark-index-feasibility-card-v0.1.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v4.33.md`.

## 1. Purpose

Determine whether OKX public historical funding, mark-price and index-price sources are semantically sufficient for a future C9 scheduled derivative-state experiment.

This stage is data/semantics only.

It must not:

- choose a C9 direction;
- choose a funding threshold;
- choose an event window;
- calculate returns;
- calculate basis transitions;
- calculate strategy signals;
- calculate sentinel outcomes;
- calculate PnL;
- open protected holdout or Confirmation data.

## 2. Why funding interval must be observed rather than assumed

OKX funding intervals are not safely modeled as permanently fixed at eight hours.

The public funding-rate history exposes `fundingTime`, and OKX documentation notes that collection frequency can change for some perpetuals.

Therefore C9-D0 reconstructs observed historical funding intervals directly from consecutive `fundingTime` timestamps.

No fixed 8-hour assumption is permitted.

## 3. Public endpoints

Use only public unauthenticated GET endpoints:

### Instrument semantics

`/api/v5/public/instruments`

Purpose:

- exact SWAP identity;
- underlying/index identifier `uly`;
- contract/settlement metadata.

### Funding history

`/api/v5/public/funding-rate-history`

Fields validated:

- `instId`;
- `instType`;
- `fundingTime`;
- `fundingRate`;
- `realizedRate`;
- `method`;
- `formulaType`.

Funding values are parsed only for numeric/schema validation and are not retained as strategy features in D0.

### Historical mark-price candles

`/api/v5/market/history-mark-price-candles`

Use `4H` bars only for coverage/timestamp/schema verification.

### Historical index candles

`/api/v5/market/history-index-candles`

Use the exact `uly` obtained from instrument metadata and `4H` bars only.

## 4. Probe universe

Exactly eight currently frozen SC001 liquid USDT swaps:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

This is a data-semantics probe universe, not a final C9 trading universe.

No asset is included/excluded using C9 outcome.

## 5. Probe windows

Use only already contaminated Selection/Calibration dates:

- July: `2024-07-01..2024-07-14`;
- September: `2024-09-01..2024-09-14`.

No new clean date is opened by D0.

Explicitly prohibited:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August 1-30 protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- legacy E006 March 22-30 Confirmation.

## 6. Funding semantics checks

For each instrument and each 14-day window:

1. request history with the upper window boundary as pagination anchor;
2. admit only `fundingTime` inside the frozen window;
3. require unique, strictly increasing admitted timestamps;
4. require at least 30 admitted funding events;
5. parse `fundingRate` and `realizedRate` only to verify finite numeric schema;
6. record distinct `method` values;
7. record distinct `formulaType` values;
8. reconstruct consecutive interval lengths from `fundingTime`;
9. require positive intervals and no observed consecutive interval larger than 8 hours.

Observed interval sets are descriptive data semantics, not a strategy parameter.

## 7. Mark/index candle checks

For each instrument/window:

- mark endpoint instrument = exact SWAP;
- index endpoint instrument = exact current `uly`;
- bar = `4H`;
- window contains 84 scheduled 4-hour starts;
- require at least 80 rows per source;
- require confirmed bars;
- require valid positive numeric OHLC only as schema validation;
- do not store OHLC values in the D0 report;
- require timestamps aligned to UTC 4-hour boundaries;
- require at least 80 exact common mark/index timestamps.

D0 may report missing-row counts and timestamp coverage only.

## 8. Network / source identity

Permitted public API domains:

- `https://www.okx.com`;
- `https://us.okx.com`.

Use HTTPS only.

Each request uses failover/retry but no alternate venue and no alternate date substitution.

Response bodies are capped to prevent unintended bulk acquisition.

## 9. PASS rule

Exact PASS token:

`C9_D0_DATA_SEMANTICS_PASS`

PASS requires all eight probe instruments to pass both July and September semantics checks.

If any instrument/window is incomplete or endpoint semantics are ambiguous, return:

`C9_D0_DATA_SEMANTICS_REVIEW`

A REVIEW is a data/implementation state, not a C9 strategy rejection.

## 10. Report firewalls

Report must state:

- `funding_values_used_for_strategy=false`;
- `mark_index_prices_used_for_strategy=false`;
- `returns_calculated=false`;
- `basis_transition_calculated=false`;
- `strategy_signal_calculated=false`;
- `sentinel_outcome_calculated=false`;
- `pnl_calculated=false`;
- `direction_selected=false`;
- `threshold_selected=false`;
- `event_window_selected=false`;
- all protected-data flags false;
- `promotional_alpha_accessed=false`.

## 11. Promotion rule

C9-D0 PASS establishes only that funding/mark/index source semantics are sufficiently available for further design.

It does not establish:

- predictive value;
- direction;
- event threshold;
- event window;
- economic headroom;
- execution architecture;
- profitability.

Only after D0 PASS may a separate non-alpha state-transition sentinel protocol be designed and frozen.
