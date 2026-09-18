# SC001 — Shared Causal Trade/Bar/Return Utilities Protocol v0.1

Date: 2026-09-18  
Status: **FROZEN ENGINEERING PROTOCOL — NO SENTINEL OUTCOME AUTHORIZED**  
Scope: `SCALPING RESEARCH / SC001`

## 1. Purpose

Provide one shared causal market-data kernel for C1-C6 Selection/Calibration sentinel engineering so that trade parsing, time-binning, bar-close availability, returns, trailing windows and non-overlap semantics are not reimplemented differently by each candidate.

This stage is engineering only. It must not calculate any C1-C6 sentinel disposition, feature ranking, strategy PnL, promotional alpha, holdout evidence or Confirmation evidence.

## 2. Required implementation

Library:

`research/sc001/sc001_selection_causal_utils_v0_1.py`

Synthetic/golden runner:

`research/sc001/sc001_selection_causal_utils_golden_v0_1.py`

The shared library must be pure with respect to strategy choice: no candidate-specific thresholds, no asset-selection logic and no outcome-dependent parameters.

## 3. Frozen causal semantics

### Trade ordering

Admitted trades must have:

- finite positive price and size;
- side in `buy/sell`;
- nondecreasing timestamps;
- strictly increasing trade IDs when IDs are supplied.

A duplicate/backward trade ID is a hard failure.

### Half-open time bars

A bar of width `W` beginning at `T` covers:

`[T, T+W)`

A trade exactly at `T+W` belongs to the next bar.

The completed bar becomes observable only at its close timestamp `T+W`.

No helper may expose a bar to a decision timestamp earlier than its close.

### Derived bar fields

For each nonempty bar calculate only from admitted trades in that half-open interval:

- open;
- high;
- low;
- close;
- base volume;
- notional;
- VWAP;
- trade count;
- buy notional;
- sell notional;
- signed aggressive notional = buy notional - sell notional.

Empty bars are not silently fabricated.

### Returns

Return helpers operate only on explicitly supplied causal price observations. A future value may be used only as an outcome after the decision clock, never as an input to the signal-side trailing window.

### Trailing windows

A trailing completed-bar query at decision timestamp `D` may return only bars with:

`bar.close_ms <= D`.

The caller may request the last N such bars. Appending future bars must not alter any already-computed historical trailing window.

### Non-overlap

Shared non-overlap selection is deterministic and chronological. Once an event at time `t` is accepted with horizon `H`, the next accepted event must satisfy `t_next >= t + H`.

## 4. Intended candidate coverage

The shared kernel must be sufficient as primitive infrastructure for:

- C1: causal 10-second spot/perp VWAP observations;
- C2: causal 1-minute bars and local references;
- C3: completed 5m/10m OHLC/range/breakout inputs;
- C4: causal 30s/60s leader returns and trailing-history transforms;
- C5: causal 30s signed aggressive-notional bars;
- C6: causal 5m cross-sectional returns.

Candidate-specific factor models, thresholds, costs and sentinel gates remain outside this shared module.

## 5. Mandatory synthetic/golden checks

The golden runner must prove at least:

1. half-open boundary assignment;
2. exact OHLC/VWAP/notional arithmetic on a hand-computable fixture;
3. completed-bar availability — no same-bar look-ahead;
4. trailing windows use only completed history;
5. future appends do not mutate historical trailing results;
6. empty bars are not fabricated;
7. deterministic non-overlap behavior;
8. duplicate/backward trade IDs fail closed;
9. D + D+1 UTC filtering admits only rows inside the target day;
10. signed aggressive notional sign convention is exact.

Exact terminal PASS token:

`SC001_SELECTION_CAUSAL_UTILS_GOLDEN_PASS`

Any failed assertion must terminate without this token.

## 6. Explicit firewalls

The golden report/output must state or imply by construction:

- no market-data body is required;
- no C1-C6 sentinel outcome is calculated;
- no strategy PnL is calculated;
- no protected market data is accessed;
- no promotional alpha is accessed;
- sentinel variant budget remains exactly 11.

## 7. Promotion rule

Only after the exact golden PASS and an implementation freeze of both the library and golden runner may C1-C6 sentinel runners import the shared utility layer.

Passing utility tests authorizes engineering of sentinel runners only. It does not authorize protected data, promotional alpha or live trading.
