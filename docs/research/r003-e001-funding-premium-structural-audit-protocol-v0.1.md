# R003-E001 — Funding Premium Structural Audit Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R003 — Funding / Basis Carry  
**Experiment:** E001  
**Date:** 2026-09-09  
**Status:** pre-result frozen structural-premium specification  
**Research posture:** falsification-first; prove the premium before building the trade

## 1. Objective

R003 investigates whether crypto derivatives contain a sufficiently persistent funding premium to justify a later, more expensive delta-neutral cash-and-carry implementation study.

E001 deliberately does **not** backtest a complete long-spot / short-perpetual portfolio.

It asks the narrower question:

> Has the realized BTCUSDT perpetual funding stream historically paid a persistent normalized premium to the short side across materially different regimes, or is the apparent carry concentrated, unstable, or strongly adverse during stress?

This sequencing is intentional. A full cash-and-carry portfolio adds basis P&L, margin mechanics, collateral transfers, liquidation risk, legging, spreads, slippage and exchange risk. Those costs are not worth modeling if the underlying funding premium itself is weak.

## 2. Important terminology correction

Do not call R003 market-neutral merely because spot delta and perpetual delta can be offset.

A future long-spot / short-perpetual implementation can still have:

- spot/perpetual basis risk;
- margin and liquidation risk;
- collateral-transfer risk;
- legging risk;
- execution spread/slippage;
- venue counterparty/default risk;
- stablecoin/collateral risk;
- funding sign reversal.

E001 therefore studies a **normalized realized funding premium**, not executable strategy alpha.

## 3. Primary data

### Funding

Use Binance USD-M perpetual public funding-rate history:

- symbol: `BTCUSDT`;
- endpoint family: `https://fapi.binance.com`;
- endpoint: `GET /fapi/v1/fundingRate`;
- begin request before the USD-M funding endpoint launch and retain the first valid returned observation;
- use `fundingTime` and realized `fundingRate` exactly as published;
- preserve any returned `markPrice` and `rateType` fields for audit;
- no API key.

Binance introduced the USD-M funding-rate history endpoint in October 2019. Current documentation/changelog also records the public `GET /fapi/v1/fundingRate` endpoint and notes that later responses may include fields such as mark price / rate type.

### Spot stress state

Use Binance Spot BTCUSDT fully closed UTC daily klines from the public market-data endpoint family:

- base: `https://data-api.binance.vision`;
- endpoint: `GET /api/v3/klines`;
- interval: `1d`;
- only fully closed bars.

Spot data is used only to classify the market drawdown state associated with each funding observation.

## 4. Causal alignment

Funding observations must never be classified using a future daily close.

For each funding timestamp, attach the latest **fully closed** BTCUSDT daily spot bar whose close timestamp is less than or equal to the funding timestamp.

Compute running closing-price ATH and drawdown only from those already-closed daily bars.

This means, for example, an 08:00 UTC funding observation cannot use that same calendar day's final close.

## 5. Primary statistic

For a normalized one-unit short perpetual notional:

`short funding carry = + fundingRate`

when the published rate is positive, because longs pay shorts; a negative published rate is a cost to the short.

E001 reports both:

- simple cumulative sum of realized funding rates;
- a compounded normalized funding index `(1 + fundingRate)` for descriptive continuity.

Neither quantity is an executable portfolio return because no spot leg, basis P&L, collateral or trading costs are included.

## 6. Frozen reporting slices

Report:

- `FULL_AVAILABLE` — first valid funding observation onward;
- `PRIMARY_2020` — 2020-01-01 onward;
- `PRE_2023` — 2020-01-01 through 2022-12-31;
- `POST_2023` — 2023-01-01 onward.

These are not train/validation/test splits. They are regime-stability diagnostics on a single historical source.

## 7. Required funding diagnostics

For each slice report:

- number of funding observations;
- start/end;
- simple cumulative normalized short funding;
- compounded normalized short funding;
- mean and median funding rate;
- positive / negative / zero fraction;
- best and worst single funding observation;
- longest consecutive negative-funding observation streak;
- worst rolling 7d / 30d / 90d cumulative funding;
- median rolling 365d cumulative funding;
- positive share of rolling 365d funding;
- worst and best rolling 365d funding.

Also report calendar-year funding totals and positive-rate fractions.

## 8. Concentration diagnostic

Among completed calendar years from 2020 onward:

- report the fraction with positive cumulative short funding;
- compute the largest positive year's share of total positive completed-year funding.

A funding premium that appears attractive only because of one exceptional year is not treated as structurally robust.

## 9. Stress / antifragility compatibility diagnostic

Classify every funding observation by the causally known BTC closing drawdown state:

- `DD_0_TO_10`: drawdown greater than -10%;
- `DD_10_TO_20`: -10% to -20%;
- `DD_20_TO_35`: -20% to -35%;
- `DD_35_TO_50`: -35% to -50%;
- `DD_50_PLUS`: -50% or worse.

For each bucket report:

- observations;
- cumulative normalized short funding;
- mean/median funding rate;
- positive/negative fraction.

The combined `DD_35_TO_50` and `DD_50_PLUS` region is used to classify whether contemporaneous funding is compatible with crisis financing.

This is important because later carry-funded convexity must **not** assume that positive funding will still be available exactly when crisis protection is most valuable.

## 10. E001 structural decision

E001 cannot assign strategy PASS.

### STRUCTURAL_SIGNAL_PRESENT

Require all of the following:

1. cumulative normalized short funding is positive on FULL_AVAILABLE;
2. positive on PRE_2023;
3. positive on POST_2023;
4. a majority of completed calendar years from 2020 onward have positive cumulative short funding;
5. median rolling 365d cumulative funding is positive;
6. more than half of rolling 365d windows are positive;
7. no single positive completed calendar year contributes 50% or more of total positive completed-year funding.

Action: advance to R003-E002 full self-financing cash-and-carry implementation study.

### STRUCTURAL_SIGNAL_MIXED

Use if full-history carry is positive but one or more stability criteria fail.

Action: do not tune a funding threshold from this history. Decide whether a forward-only observation stage is justified or close the branch.

### STRUCTURAL_SIGNAL_ABSENT

Use if full-history cumulative normalized short funding is non-positive.

Action: close the BTC perpetual funding-carry premise as currently framed; do not build a more complex execution model to rescue it.

## 11. Separate crisis-financing classification

Regardless of the structural carry result, classify deep-drawdown funding:

- `CRISIS_FINANCING_COMPATIBLE` if deep-drawdown weighted mean funding and representative median sign are non-negative;
- `CRISIS_FINANCING_PROCYCLICAL_RISK` if both are negative;
- `CRISIS_FINANCING_MIXED` otherwise.

This classification does **not** determine whether standalone carry exists. It determines whether contemporaneous funding can plausibly be relied upon during market stress.

Even a compatible result does not authorize same-period option financing. Any future carry-funded convexity design must use a pre-funded / ring-fenced premium budget unless separately validated.

## 12. What E001 deliberately omits

Do not infer from E001:

- executable long-spot/short-perp return;
- basis-capture return;
- liquidation safety;
- margin efficiency;
- optimal leverage;
- optimal funding-entry threshold;
- optimal venue;
- option-budget sizing.

These require later experiments.

## 13. Data failure rule

If Binance public futures funding history is unavailable from the user's network or returns a materially incomplete series, stop with a source/data error.

Do not silently switch venue or source after seeing partial results.

A switch to Binance Vision bulk archives or another venue requires a documented data-protocol revision before inspecting strategy implications.

## 14. Anti-overfitting freeze

Before seeing E001 results, freeze:

- BTCUSDT only;
- realized funding-rate history;
- no activation threshold;
- no filtering for positive funding;
- no moving average / volatility / price signal;
- reporting slices above;
- rolling windows above;
- drawdown buckets above;
- structural decision rule above.

Any conditional funding strategy is a later candidate/version and cannot be retrofitted into E001 after results.