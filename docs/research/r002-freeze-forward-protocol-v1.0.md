# R002 — BTC Trend Following Freeze & Forward Protocol v1.0

**Status:** FROZEN RESEARCH CANDIDATE  
**Freeze date:** 2026-09-08  
**Candidate:** BTC Trend Following (R002)  
**Frozen rule:** daily close vs SMA120

## Why this rule is frozen

The discovery/robustness stage found a broad performance plateau around SMA110–SMA130. SMA120 is intentionally selected near the center of that plateau rather than at the numerically best point. The goal is to reduce parameter-selection risk.

No future result may be used to change 120 into another lookback while still claiming the same forward test. Any change creates a new strategy version and resets the forward-validation clock.

## Frozen signal

At the close of UTC day `t`:

- compute `SMA120_t` from the most recent 120 fully closed daily BTCUSD candles, including day `t`;
- if `Close_t > SMA120_t`, target exposure for the next day is `1.0` BTC;
- otherwise target exposure is `0.0` BTC/cash.

Only fully closed UTC candles may be used. The in-progress current-day candle is forbidden.

## Execution convention

Primary research convention:

- signal observed after the fully closed UTC daily candle;
- target position applies from the next UTC daily open;
- exposure changes are charged 10 bps per 0→1 or 1→0 transition in the primary model.

Stress results at 5/25/50 bps remain diagnostics only and are not alternative strategy definitions.

## Portfolio definition

- asset: BTCUSD proxy during research;
- position: long BTC or cash only;
- no leverage;
- no short position;
- no options;
- no discretionary overrides;
- cash yield = 0 in the current research baseline unless a separately versioned carry sleeve is later evaluated.

## Frozen benchmark set

1. BTC buy-and-hold over the same dates.
2. Cash / zero return.
3. For research context only, R001 remains a complexity benchmark, not a component of R002.

## Forward-validation start

Forward observations start after the 2026-09-08 freeze. The first legitimate forward signal must be formed from a candle that closes after the freeze and must not use any data available only after that decision.

The historical 2019-09 through 2026-09 sample is development/backtest data and must never be relabeled as forward OOS.

## Forward metrics

Track without changing the rule:

- cumulative return;
- CAGR when sample length becomes meaningful;
- max drawdown;
- realized volatility;
- time in market;
- number of exposure changes;
- transaction-cost drag;
- return and drawdown relative to buy-and-hold;
- trade-level holding periods;
- whipsaw frequency;
- largest avoided BTC drawdowns;
- largest missed BTC rallies.

## Review gates

### 3 months
Operational sanity only. No PASS/FAIL based on performance.

### 6 months
Check implementation fidelity, data integrity, turnover, and whether realized behavior is consistent with the historical mechanism. Do not tune parameters.

### 12 months
First meaningful forward review. Continue unless there is evidence of implementation failure or the economic mechanism is contradicted.

### 24 months
Primary forward validation gate. Compare with frozen expectations and benchmark behavior.

## Change-control rule

The following require a new version and a new forward clock:

- changing SMA120 lookback;
- adding a second indicator or filter;
- changing long/cash into long/short;
- adding leverage;
- changing the execution timing convention;
- introducing volatility targeting;
- combining with R001 or another sleeve.

Data-source substitutions that preserve the same daily UTC price semantics may be treated as implementation changes only if cross-validated and documented.

## Current pre-freeze diagnostic

Using fully closed data through 2026-09-07, the historical SMA120 research simulation at 10 bps per exposure change produced approximately:

- CAGR: 55.8%;
- max drawdown: -32.3%;
- buy-and-hold CAGR over the comparable usable interval: 42.5%;
- buy-and-hold max drawdown: -76.7%;
- exposure: ~57.8%;
- exposure changes: 59.

These are development statistics, not promises and not forward results.

## Integrity note discovered at freeze

The earlier mobile Bybit collector could include the current in-progress UTC daily candle when run before that candle closed. That is acceptable for a raw market-data download only if later filtered, but it is not acceptable for signal generation. The collector has therefore been revised so the current UTC candle is automatically excluded. For the freeze diagnostics, data are explicitly truncated through 2026-09-07.

## Verdict

R002 has passed discovery and coarse robustness. SMA120 is now **FROZEN FOR FORWARD VALIDATION**. The next task is not optimization; it is faithful observation and independent validation.
