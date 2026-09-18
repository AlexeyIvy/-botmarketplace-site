# SC001 — C1-C6 Sentinel Executable Protocol v0.1

Date: 2026-09-18  
Status: **FROZEN BEFORE FIRST C1-C6 SENTINEL OUTCOME**  
Scope: `SCALPING RESEARCH / SC001`

Parent:
`docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`

This executable protocol fixes implementation details that were intentionally left below code-level precision in the frozen sentinel/MDE plan. It does not change any candidate, threshold, horizon, asset universe, cost hurdle, feature budget, or the exact total budget of 11 strategy variants.

## 1. Shared parents and sandbox

Permitted performance dates only:

- 2024-07-01..2024-07-14 UTC;
- 2024-09-01..2024-09-14 UTC.

Permitted causal source-support dates only:

- 2024-06-30 and 2024-07-15;
- 2024-08-31 and 2024-09-15.

Perpetual universe exactly:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP and BCH USDT swaps.

C1 SPOT universe exactly the corresponding eight OKX USDT spot instruments.

Required qualified parents:

- E007R1 July trade semantic integrity PASS;
- E009 September trade semantic integrity PASS;
- C1 SPOT body integrity PASS;
- shared causal utilities golden PASS.

No SOL/FIL/LTC/SUI holdout, July 16-30, August 1-30, October Confirmation, or legacy E006 March Confirmation body may be opened by these runners.

## 2. Common chronology rules

All derived bars are half-open `[T,T+W)` and observable only at close `T+W`.

All outcomes must complete inside the same performance UTC day as the signal. The D+1 archive is source support for reconstruction of the performance day only; it is not a new performance day.

Missing bars are not fabricated.

Every sentinel is selection/calibration only. No fee-adjusted/net PnL is calculated here.

## 3. C1 executable semantics — 1 variant

Variant:
`strict_legacy_E006_mechanism_multiasset`

For each SPOT/perpetual pair:

- 10-second causal VWAP bars;
- basis bps = `10000 * (perp_vwap / spot_vwap - 1)`;
- prior scheduled lookback = 2160 ten-second points = 6 hours;
- baseline requires at least 2052 valid paired observations, preserving the old E006 95% validity floor;
- ordinary median baseline uses prior observations only, excluding the current point;
- trigger is a strict crossing from below `+50 bps` to at/above `+50 bps` dislocation relative to the current frozen baseline;
- frozen baseline is held fixed for that event;
- same-day maximum horizon = 30 minutes;
- idealized exit is first future valid paired basis at/below frozen baseline +10 bps;
- if no such convergence occurs, use the last valid paired basis observation at or before 30 minutes;
- idealized contraction = trigger dislocation minus exit dislocation.

For breadth accounting, an active pair is a pair with at least 3 measured triggers. Gates remain exactly those in the parent sentinel plan.

## 4. C2 executable semantics — 2 variants

Use completed 1-minute swap bars.

C2-A:
- local reference = aggregate VWAP of the current completed minute plus the preceding 4 contiguous completed 1-minute bars.

C2-B:
- local reference = ordinary median of the five completed 1-minute VWAPs over the same contiguous window.

For both:
- deviation bps = current completed 1-minute VWAP versus reference;
- event requires absolute deviation >=30 bps;
- direction is toward the reference;
- response is signed current-VWAP to VWAP of the bar closing exactly 10 minutes later;
- accept events chronologically and non-overlapping per asset with 10-minute horizon;
- no volatility/trend/oscillator rescue filter.

Gates remain exactly those in the parent plan.

## 5. C3 executable semantics — 2 variants

C3-A: 5-minute bars, 10-minute response.  
C3-B: 10-minute bars, 20-minute response.

At current completed bar close:

- breakout requires close strictly above prior 6 completed highs or strictly below prior 6 completed lows;
- true range uses standard `max(high-low, |high-prev_close|, |low-prev_close|)`;
- expansion requires current true range >=1.5x median true range of prior 12 completed bars;
- response is signed close-to-close continuation at the frozen response horizon;
- events are chronological and non-overlapping per asset using the response horizon.

No volume/ADX/MACD/flow/time-of-day rescue is permitted.

## 6. C4 executable semantics — 4 variants

Variants:

- BTC 30s impulse -> alt 60s;
- BTC 60s impulse -> alt 60s;
- ETH 30s impulse -> alt 60s;
- ETH 60s impulse -> alt 60s.

Base derived grid is completed 30-second swap bars.

Leader impulse:
- same-horizon close-to-close leader return;
- robust z-score uses the prior 60 minutes of non-overlapping same-horizon leader returns;
- current leader return is excluded from the history window;
- event is a strict crossing from prior `|Z| < 3` to current `|Z| >= 3`.

Targets exactly:
DOGE, ORDI, UNI, XRP, OP and BCH.

Common-factor adjustment:
- factor = equal-weight BTC and ETH 60-second return;
- target beta is ordinary OLS slope estimated only from prior 60 non-overlapping 60-second target/factor returns;
- future target 60-second response may be used only as the ex-post outcome;
- future residual = target future return - frozen pre-event beta * future common-factor return;
- report both raw signed response and signed residual response.

If raw response is positive but residual gates fail, report `COMMON_BETA_NOT_LEAD_LAG` diagnostic; do not promote the raw beta response under C4.

## 7. C5 executable semantics — 1 variant

Use completed 30-second swap bars.

For each bar:
- signed aggressive notional = buy notional - sell notional;
- robust z-score uses prior 120 contiguous completed 30-second signed-notional bars = 60 minutes;
- current bar excluded from history;
- strict crossing from prior `|Z| < 3` to current `|Z| >= 3`;
- concurrent price move = current bar open-to-close return;
- event requires flow and price move same sign and absolute price move >=10 bps;
- response = signed reversal against event direction from current close to close exactly 5 minutes later;
- events are chronological and non-overlapping per asset for 5 minutes.

No L2 is accessed by the first C5 sentinel.

## 8. C6 executable semantics — 1 variant

Use completed 5-minute swap bars.

Decision times are exact UTC 15-minute boundaries, making 15-minute opportunities non-overlapping by construction.

At each decision:
- each asset current 5-minute return = close at decision / close 5 minutes earlier - 1;
- common-market return = equal-weight mean of the eight asset returns;
- residual = asset return - common-market return;
- conceptually LONG the single most negative residual asset;
- conceptually SHORT the single most positive residual asset;
- deterministic alphabetical tie-break only;
- hold exactly 15 minutes;
- opportunity gross spread = long 15-minute return - short 15-minute return.

Contribution concentration uses absolute realized leg return separately for long-role and short-role attribution by asset.

Gates remain exactly those in the parent plan.

## 9. One-shot and multiplicity

Frozen first-pass count remains:

- C1 = 1;
- C2 = 2;
- C3 = 2;
- C4 = 4;
- C5 = 1;
- C6 = 1;
- total = 11.

No new threshold, horizon, indicator, asset-selection, calendar filter, or interaction may be introduced after outcomes.

Each runner must refuse to overwrite an existing terminal sentinel report.

## 10. Implementation preflight

Before any sentinel outcome, a master implementation preflight must verify:

- exact Git blob identities for this protocol, common helper, shared causal utility library and all six runners;
- frozen ledger total = 11;
- required qualified parent reports;
- golden PASS;
- no terminal sentinel report already exists;
- each candidate runner's own `preflight` returns its exact PASS token.

Master exact PASS token:

`SC001_C1C6_SENTINEL_IMPLEMENTATION_PREFLIGHT_PASS`

No sentinel `run` is authorized before this exact token.

## 11. Interpretation

A sentinel survival means only selection-stage eligibility for later MDE/block planning and diversified research-batch consideration.

It is not promotional evidence, does not prove profitability or live executability, and does not authorize protected holdout, Confirmation, or live trading.
