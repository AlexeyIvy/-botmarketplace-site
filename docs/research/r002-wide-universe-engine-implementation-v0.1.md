# R002 Wide-Universe PTI Engine — Implementation Freeze v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** pre-result implementation freeze  
**Engine:** `research/r002/wide_universe_point_in_time_finalists.py`  
**Initial engine commit:** `9275d50e321dd24f5eabe83cc20dd340cfda6350`

## Purpose

Freeze the implementation details of the full Binance archive-defined point-in-time finalist test before observing the wide-universe strategy results.

This note does not change the research hypothesis or strategy parameters. It resolves implementation details that were largely irrelevant on the earlier continuously traded crypto subset but can matter in the much broader archive-defined universe.

## Frozen candidates

Only:

1. **SMA120**
   - long when `close > SMA120`;
   - otherwise cash.

2. **Donchian 100/50**
   - enter long when close exceeds the highest high of the prior 100 observed bars;
   - remain long until close falls below the lowest low of the prior 50 observed bars;
   - channels exclude the current bar.

3. **PTI passive comparator**
   - every currently eligible instrument receives its equal sleeve.

No new indicator, retuning, asset-specific parameter, optimized weighting rule, leverage, shorting, or liquidity filter is permitted in this phase.

## Dataset invariants

Primary input:

`r002_binance_full_universe_daily.csv`

Expected raw invariants:

- 864 symbols;
- 637,705 rows;
- 2020-01-01 through 2026-08-31;
- no duplicate symbol-date rows;
- no missing core OHLCV;
- no non-positive OHLC prices;
- no negative volume;
- valid OHLC relationships.

The engine checks these invariants before strategy evaluation.

## Point-in-time warmup and rolling windows

The common warmup is **200 genuinely observed bars per instrument**.

This is implemented on each symbol's own ordered observed-bar history, not as 200 global calendar rows.

Likewise:

- SMA120 uses the latest 120 observed closes for that symbol;
- Donchian entry uses the prior 100 observed highs;
- Donchian exit uses the prior 50 observed lows.

This matters because the archive-defined universe can contain instruments with non-trading calendar days. Counting global calendar rows would make their effective lookbacks shorter or prevent them from becoming eligible under the intended rule.

No symbol is pre-filtered using its final lifetime. Symbols that never reach 200 observed bars remain in the input universe but simply never become eligible.

## Dead-tail cleaning

For each symbol, archive rows after the final positive-volume day are trimmed as dead post-delisting tails.

Internal zero-volume or missing-calendar observations before the final live period are not automatically treated as a permanent disappearance.

## Internal non-trading gaps

A missing global calendar day inside an otherwise continuing symbol history is **not** treated as a delisting event.

Implementation rule:

- the most recent signal state is carried through internal non-trading gaps;
- no artificial price return is created on the missing day;
- when the next observed close arrives, the observed close-to-close return is booked then;
- the instrument remains eligible after it has reached the 200-observed-bar warmup while its history is still considered alive.

This avoids applying repeated disappearance penalties to instruments that merely do not trade every calendar day.

The primary equal-sleeve portfolio remains a signal-validation abstraction; exact closed-market execution mechanics are deferred to the later execution-realism phase.

## Terminal disappearance and right-censoring

For a historical instrument whose real archive history ends before the dataset boundary, a held long sleeve can receive the pre-specified disappearance penalty after its final live day.

An instrument present in the latest available archive month is treated as **right-censored at the dataset boundary** rather than assumed to disappear merely because no later archive exists.

This right-censoring affects only terminal disappearance handling. It does not change the 200-bar eligibility clock, signal calculation, or parameter selection.

## Timing convention

Signal information from close `t` is applied to the next portfolio return period.

There is no same-close execution or same-bar look-ahead.

For continuously observed daily instruments this is exactly `t -> t+1`.

For an internal non-trading gap, the last known signal is carried until the next observed close-to-close return is available.

## Portfolio construction

At each point in time:

- `N` = number of currently eligible instruments;
- each eligible instrument owns a capital sleeve of `1/N`;
- SMA120 or Donchian invests that sleeve only when its frozen signal is long;
- inactive sleeves stay in cash;
- passive invests every eligible sleeve;
- no leverage;
- cash return = 0 for this signal-validation test.

Transaction costs are charged on absolute portfolio target-weight changes under the same accounting convention for finalists and passive comparator.

## Stress grid

Run the complete Cartesian grid:

Transaction cost:

- 5 bps;
- 10 bps;
- 25 bps;
- 50 bps.

Disappearance penalty on a disappearing held sleeve:

- 0%;
- 25%;
- 50%;
- 100%.

Therefore each strategy/comparator receives 16 stress combinations.

Baseline remains:

- 10 bps transaction cost;
- 25% disappearance penalty.

No stress setting will be selected after seeing which one makes a candidate look best.

## Required slices and metrics

For every stress combination, report both:

- full evaluation period;
- post-2023 period beginning 2023-01-01.

Metrics include:

- CAGR;
- Max Drawdown;
- annualized volatility;
- Calmar;
- ending multiple;
- turnover;
- average gross exposure and cash fraction;
- worst calendar year;
- worst calendar quarter;
- worst month;
- worst rolling 12-month return;
- longest drawdown duration;
- average/median eligible count;
- average/median active count.

Also save per-calendar-year returns and breadth through time.

## Concentration definition

Concentration diagnostics are evaluated on the frozen baseline of 10 bps + 25% disappearance penalty.

Asset contribution is measured in portfolio wealth units so symbol-level net contributions sum to total ending portfolio P&L.

For each finalist report:

- net wealth contribution by symbol;
- fee drag by symbol;
- disappearance drag by symbol;
- top contributor;
- top 5 contributors;
- bottom 5 contributors;
- top-5 share of **total positive symbol contributions**;
- contribution attributed to latest-archive survivors versus historical/non-survivors.

Survivor/non-survivor status is diagnostic attribution only and is not a strategy selection filter.

### Excluding top contributors

`EX_TOP1` and `EX_TOP5` are explicitly ex-post concentration stress diagnostics.

Procedure:

1. identify top contributors from the baseline full-universe run;
2. rerun the same frozen strategy after removing the top 1 or top 5 symbols from the diagnostic universe;
3. recompute equal sleeves among the remaining instruments;
4. report CAGR, Max Drawdown, ending multiple, and turnover.

These ex-post exclusions are not alternative production universes and must not be used to select assets for trading. They only test whether headline economics collapse when hindsight winners are removed.

## Decision discipline

The engine intentionally does **not** auto-promote either finalist.

After outputs are generated, the result must be reviewed against the already frozen roadmap criteria and each finalist assigned:

- PASS;
- FAIL;
- REDESIGN.

A poor result must not be rescued on this same sample by adding filters, tuning SMA length, tuning Donchian windows, excluding bad symbols, or optimizing weights.

If neither finalist survives, the next action is hypothesis reassessment rather than parameter search.
