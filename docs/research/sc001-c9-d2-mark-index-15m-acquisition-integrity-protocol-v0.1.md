# SC001 — C9-D2 September Mark/Index 15m Acquisition & Integrity Protocol v0.1

Date: 2026-09-18  
Status: **FROZEN DATA-ONLY PROTOCOL — NO STATE-TRANSITION OUTCOME AUTHORIZED**  
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c9-d1-v0.3-funding-archive-integrity-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.9.json`;
- `docs/research/sc001-c9-scheduled-funding-mark-index-feasibility-card-v0.1.md`.

## 1. Purpose

Acquire and qualify causal historical OKX mark-price and index-price candles at 15-minute resolution for the C9 nonpromotional calibration interval.

This stage is data engineering only.

It may open and store historical mark/index OHLC values inside the already-declared Selection/Calibration channel, but it must not calculate:

- mark/index premium;
- premium contraction/expansion;
- returns;
- funding-conditioned outcomes;
- strategy direction;
- threshold;
- event window;
- signal;
- sentinel disposition;
- PnL.

## 2. Why 15-minute bars

C9 is a scheduled-event mechanism whose future position horizon must remain compatible with core SC001 short-horizon research.

The prior D0 4H source check is too coarse to support a causal 30-minute event-state study.

15-minute bars provide:

- exact UTC alignment with 00:00/08:00/16:00 funding timestamps;
- two completed post-event bars over 30 minutes;
- a manageable acquisition footprint;
- no need to open sub-minute data before structural feasibility is established.

This is a data-resolution choice, not a signal/window optimization result.

## 3. Authorized universe

Exactly:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

Index identifiers must use the exact `uly` already resolved by C9-D0 v0.2.

## 4. Authorized UTC interval

Only:

`[2024-08-31T00:00:00Z, 2024-10-01T00:00:00Z)`

This interval covers:

- one complete prior UTC warm-up day;
- all September 2024 funding timestamps;
- all September UTC post-event windows;
- no October UTC mark/index candle.

The full interval is prospectively classified:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

for C9 mark/index evidence.

## 5. Public endpoints

Mark:

`GET /api/v5/market/history-mark-price-candles`

Index:

`GET /api/v5/market/history-index-candles`

Frozen bar:

`15m`

Pagination:

- chronological target interval fixed before access;
- paginate backwards using `after`;
- limit `100`;
- deduplicate exact timestamps;
- no alternate dates or assets if gaps occur.

## 6. Expected grid

UTC interval length:

31 complete days.

Expected 15-minute timestamps per source:

`31 * 24 * 4 = 2976`

For every asset require exactly:

- mark rows = 2976;
- index rows = 2976;
- exact common timestamps = 2976.

No missing bar is synthesized or forward-filled.

## 7. Bar semantics

For each admitted mark/index candle:

- timestamp must be unique;
- timestamp must satisfy `start <= ts < end`;
- timestamp must align to a UTC 15-minute boundary;
- confirmed flag must equal `1`;
- OHLC values must be finite and strictly positive;
- high >= max(open, close, low);
- low <= min(open, close, high).

D2 treats the timestamp as the candle start.

A later state-transition sentinel must respect completed-bar availability and may not use final OHLC before bar close.

## 8. Normalized output

Write one synchronized CSV per asset:

`~/sc001_data/SC001_C9_D2_MARK_INDEX_15M/normalized/<ASSET>_mark_index_15m.csv`

Columns exactly:

- `ts_ms`;
- `mark_open`;
- `mark_high`;
- `mark_low`;
- `mark_close`;
- `index_open`;
- `index_high`;
- `index_low`;
- `index_close`;
- `confirmed`.

Rows are sorted strictly increasing by `ts_ms`.

The report records file byte size and SHA256 but not individual price values.

## 9. Parent requirements

Require local exact D1 v0.3 PASS:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS`

with:

- assets passed = 8/8;
- prior October funding contamination known = true;
- October funding clean C9 Confirmation eligible = false;
- October funding body accessed by v0.3 = false;
- returns/basis-transition/signal/sentinel/PnL = false;
- direction/threshold/event-window selected = false.

Also require C9-D0 v0.2 exact PASS for the frozen `uly` mapping.

## 10. Exact terminal states

PASS:

`C9_D2_MARK_INDEX_15M_INTEGRITY_PASS`

REVIEW:

`C9_D2_MARK_INDEX_15M_INTEGRITY_REVIEW`

REVIEW is a data/implementation state, not a C9 strategy FAIL.

## 11. Report firewalls

Report must distinguish data access from strategy use.

Required fields:

- `mark_index_values_opened_by_d2=true`;
- `mark_index_values_used_for_strategy=false`;
- `funding_values_opened_by_d2=false`;
- `premium_calculated=false`;
- `returns_calculated=false`;
- `state_transition_outcome_calculated=false`;
- `strategy_signal_calculated=false`;
- `sentinel_outcome_calculated=false`;
- `pnl_calculated=false`;
- `direction_selected=false`;
- `threshold_selected=false`;
- `event_window_selected=false`;
- `october_utc_mark_index_accessed=false`;
- `promotional_alpha_accessed=false`.

## 12. Consequence of PASS

D2 PASS establishes only a synchronized, causal 15-minute mark/index calibration tape.

Only after D2 PASS may a separate C9 state-transition sentinel protocol define:

- exact event-state measurement;
- exact pre/post observation clocks;
- exact execution architecture;
- structural cost hurdle;
- minimal variant budget.

No outcome-bearing state-transition calculation is authorized by D2 itself.
