# SC001 — Independent Short-Horizon Research Protocol v0.1

**Project:** BotMarketplace / BotMarketplace.store  
**Branch:** SCALPING RESEARCH / SC001  
**Date:** 2026-09-11  
**Status:** FROZEN BEFORE FIRST SC001 BACKTEST  
**Parent audit:** `docs/research/sc001-data-sufficiency-audit-v0.1.md`

---

## 1. Purpose

Test whether the data already present in the BotMarketplace research project contain an economically meaningful, statistically credible, execution-robust short-horizon trading edge.

The protocol does **not** assume that such an edge exists.

The current data audit does not support honest true-scalping claims. Until suitable minute/sub-minute trade/quote history exists, SC001 historical experiments are classified as **short-horizon intraday**, not scalping.

---

## 2. Hard independence rule

SC001 is isolated from the principal research tracks.

No SC001 observation, result, failure, parameter sensitivity, or forward outcome may be used to retrospectively change:

- R009-E002;
- R003-E003 Binance;
- R003-X003 Bybit;
- R010-E001;
- Safe-Sleeve S002.

Likewise, SC001 must not optimize itself against the historical performance of those strategies.

Existing artifacts are read-only evidence about available data, venue mechanics, and research infrastructure.

---

## 3. Anti-overfitting constitution

SC001 shall:

1. write the economic hypothesis before seeing experiment P&L;
2. freeze exact primary rules before running them;
3. use only a small, declared sensitivity neighborhood;
4. never choose an asset because it later produced the best return;
5. never choose a venue because it later produced the best return;
6. never add a filter merely to rescue a failed experiment;
7. never modify a frozen version after viewing validation/OOS results;
8. issue a new experiment identifier for a genuinely distinct hypothesis;
9. keep development, validation, and final untouched periods separate;
10. enforce timestamp causality and fully closed input bars;
11. avoid survivorship/cherry-picking;
12. report failed hypotheses permanently rather than deleting them.

A failed strategy is a valid research outcome.

---

## 4. Predeclared strategy families

Only a small number of economically distinct families are admitted to the first research program.

### Family A — Extreme-move short-horizon mean reversion

Hypothesis:

A sufficiently unusual one-hour BTC perpetual move may contain temporary overshoot caused by leverage, forced flow, inventory adjustment, or short-lived liquidity imbalance, followed by partial reversal.

Why an edge could exist:

- forced liquidations / stop cascades can push price temporarily away from short-horizon equilibrium;
- liquidity can replenish after an extreme move;
- market makers / arbitrageurs may fade transient dislocations.

Why it can disappear:

- extreme moves can be informed and persistent;
- momentum regimes can dominate reversal;
- execution cost can exceed the reversal magnitude;
- one-hour bars may be too coarse to isolate the temporary component.

Required data:

- causal hourly perpetual OHLC;
- sufficient history across regimes;
- cost proxy;
- actual funding timestamps if a held position crosses funding.

Expected holding period:

- approximately one hour in the primary experiment.

Primary risks:

- catching genuine trend continuation;
- bar-resolution execution error;
- spread/slippage underestimation;
- crisis tail losses.

Predeclared first test: **SC001-E001**.

### Family B — Extreme-move short-horizon momentum / continuation

Hypothesis:

An unusual one-hour move may reflect information arrival or sustained forced flow that persists into the next hour rather than reverting.

Economic difference from Family A:

- A bets against the extreme move;
- B follows it.

Family B is a separate hypothesis, not a rescue filter for Family A. If tested, it receives its own experiment identifier and frozen rules before results.

Why it can disappear:

- rapid mean reversion;
- adverse selection after entering late;
- transaction costs;
- crowding.

### Family C — Volatility compression -> expansion / breakout

Hypothesis:

Periods of unusually compressed hourly range/realized volatility may be followed by clustered volatility and short directional expansion.

Why it can exist:

- volatility clustering;
- order accumulation around local ranges;
- delayed information / liquidation cascades after range escape.

Why it can disappear:

- compression can persist;
- breakout direction can reverse rapidly;
- OHLC bars do not reveal intrabar breakout ordering;
- costs can dominate small expansions.

This family is lower priority than A/B because causal entry design from hourly OHLC requires more care to avoid intrabar ambiguity.

### Family D — Hourly basis / funding dislocation reversion

Hypothesis:

Temporary divergence among Binance BTC spot, perpetual contract, and mark price around funding / stressed intervals may mean-revert.

Why it is testable in principle:

- the existing R003 history contains synchronized hourly spot/perpetual/mark series and funding timestamps.

Why it is not first:

- two-leg execution multiplies cost uncertainty;
- historical bid/ask is absent;
- funding cadence is much slower than true scalping;
- economic overlap with basis/carry mechanisms demands especially clear separation from R003.

If tested, Family D must be documented as an independent SC001 short-horizon basis experiment. It must not alter R003 in any way.

### Order-flow / imbalance family

**NOT ADMITTED with current data.**

No long validated trade tape / L2 book history has been located. Daily or hourly candle aggregates must not be relabeled as order flow.

---

## 5. Family selection for first experiments

Priority order before any SC001 strategy P&L is seen:

1. Family A — extreme-move mean reversion;
2. Family B — extreme-move momentum as an independent competing hypothesis;
3. Family C — volatility compression/expansion;
4. Family D — basis/funding dislocation only after execution assumptions are separately audited.

This order is frozen for v0.1. It may be changed only for a documented data/implementation impossibility, not because a result is unattractive.

---

## 6. Canonical dataset for initial experiments

Venue: Binance.  
Instrument: BTCUSDT USD-M perpetual.  
Frequency: 1 hour.  
Primary common research history: 2020-01-01 through 2026-09-09 19:00 UTC, subject to exact available fully closed rows and gap handling.  
Auxiliary synchronized data: Binance BTCUSDT spot, mark price, realized funding.

Why BTCUSDT is preselected:

- it is the longest, highest-quality, already-audited intraday series located in the project;
- it is highly liquid relative to the broad archive;
- the choice is made before any SC001 P&L is generated.

BTCUSDT is **not** selected because of observed SC001 historical performance.

No cross-asset winner search is authorized in the first stage.

---

## 7. Validation architecture

For the first frozen experiments, use calendar-separated periods:

- **Development / mechanism slice:** 2020-01-01 through 2022-12-31;
- **Validation slice:** 2023-01-01 through 2024-12-31;
- **Final untouched slice:** 2025-01-01 through 2026-09-09 (or latest fixed pre-run closed-hour cutoff recorded by the experiment engine).

Rules are frozen before examining any SC001 P&L, therefore the development slice is primarily a mechanism / implementation diagnostic rather than an invitation to optimize parameters.

Once the final untouched slice has been inspected, the same experiment version cannot be tuned and retested as if it remained OOS.

Yearly / rolling / regime breakdowns are descriptive robustness diagnostics, not alternative optimization surfaces.

---

## 8. Execution-model principles

The 1h history lacks historical bid/ask. Therefore all fill assumptions must be described as explicit conservative proxies.

Mandatory principles:

- signal computed after a fully closed bar;
- primary entry no earlier than next bar open;
- side-dependent adverse execution friction applied at entry and exit;
- taker-style cost assumption; no maker rebate / queue advantage assumed;
- any funding timestamp crossed by an open perpetual position is included causally;
- bars missing across required signal/entry/exit sequence cause the trade to be skipped and logged;
- no intrabar stop-loss / take-profit whose ordering cannot be known from OHLC;
- latency robustness must include at least a delayed-entry scenario;
- cost stress must include a materially worse scenario than baseline.

The first-stage goal is edge existence, not account-size optimization. If a strategy survives historical gates, a separate SC001 granularity / small-account audit must test $250 / $500 / $1,000 / $5,000 with contemporaneous exchange filters where possible.

---

## 9. Mandatory output metrics

Every tested candidate must report, where meaningful:

- total return;
- annualized return / CAGR where meaningful;
- max drawdown;
- Calmar;
- Sharpe / Sortino with clear sampling convention;
- profit factor;
- win rate;
- average trade;
- median trade;
- gross edge per trade;
- **net edge per trade after costs**;
- trades/day;
- trade count;
- turnover;
- fee drag;
- spread/slippage-proxy drag;
- funding contribution where applicable;
- longest losing streak;
- exposure;
- capital utilization;
- return / edge by year, month, validation slice, and regime;
- cost sensitivity;
- latency sensitivity;
- parameter-neighbor sensitivity;
- skipped-trade count from data gaps.

Net edge per trade after costs is a primary decision metric. Attractive total return cannot compensate for a near-zero per-trade edge that is smaller than plausible execution error.

---

## 10. Robustness diagnostics

A surviving experiment must be stressed for:

- neighboring, predeclared parameter values;
- worse execution friction;
- doubled fee component;
- delayed entry;
- random omission of a fixed fraction of eligible trades using a fixed random seed set before result inspection;
- calendar-year and regime concentration;
- recent-period behavior.

The sensitivity analysis is diagnostic. The highest-P&L neighbor must not replace the frozen primary parameter.

---

## 11. Status vocabulary

Allowed SC001 statuses:

- `FAIL`;
- `WEAK`;
- `PROMISING_SCREEN`;
- `ROBUST_HISTORICAL_CANDIDATE`;
- `ADVANCE_TO_FORWARD`.

No historical backtest can establish `proven profitable` status.

`ADVANCE_TO_FORWARD` requires a separate explicit decision after historical robustness and execution/granularity checks.

---

## 12. Forward-testing boundary

If a candidate eventually passes historical gates:

- freeze its exact rules and forward inception before subsequent data are observed;
- paper/demo only initially;
- do not move inception after poor results;
- do not tune from early forward observations;
- keep SC001 forward evidence independent of the other project forwards.

No real capital is authorized by this protocol.

---

## 13. First experiment

The first frozen experiment is:

> **SC001-E001 — BTCUSDT 1h Extreme-Move Mean-Reversion Falsification**

Its exact pre-test definition is stored separately in:

`docs/research/sc001-e001-pretest-freeze-v0.1.md`

No SC001-E001 P&L may be interpreted until that document is committed.
