# R003-E002 — Self-Financing BTC Cash-and-Carry Implementation Protocol v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R003 — Funding / Basis Carry  
**Experiment:** E002  
**Date:** 2026-09-09  
**Status:** pre-result frozen implementation-study specification  
**Parent:** `docs/research/r003-e001-results-v0.1.md`  
**Research posture:** implementation realism before any strategy promotion; no funding-threshold optimization

## 1. Objective

R003-E001 found a persistent historical BTCUSDT funding premium to the short-perpetual side but did not model an executable portfolio.

E002 asks the next, stricter question:

> Does an unconditional, fully funded, equal-BTC long-spot / short-perpetual portfolio remain economically useful after actual spot/perpetual basis movement, realized funding, two-leg execution costs, deterministic re-hedging, and separately tracked futures-margin headroom?

E002 is still historical research on already inspected Binance data. It cannot assign production PASS or independent OOS PASS.

Maximum positive status:

> **IMPLEMENTATION_PROMISING**

## 2. No post-E001 funding filter

E002 is unconditional / always-on once initialized.

It is explicitly prohibited to add after seeing E001:

- minimum positive funding threshold;
- moving average of funding;
- enter-only-when-funding-positive rule;
- price/trend/volatility activation filter;
- funding forecast;
- optimized leverage or collateral fraction.

Those would be new hypotheses, not implementation of the E001 premise.

## 3. Instruments and sources

### Spot leg

Binance Spot `BTCUSDT`, public 1h klines:

- base endpoint family: `https://data-api.binance.vision`;
- endpoint: `GET /api/v3/klines`;
- interval: `1h`.

### Perpetual execution/reference leg

Binance USD-M Futures `BTCUSDT`, public 1h contract klines:

- base: `https://fapi.binance.com`;
- endpoint: `GET /fapi/v1/klines`;
- interval: `1h`.

### Perpetual mark / margin leg

Binance USD-M Futures `BTCUSDT` mark-price 1h klines:

- endpoint: `GET /fapi/v1/markPriceKlines`;
- interval: `1h`.

### Funding

Reuse realized Binance USD-M `BTCUSDT` funding:

- endpoint: `GET /fapi/v1/fundingRate`;
- no funding forecast;
- published realized funding rate only.

No API key is required.

## 4. Data window and gate

Download from before 2019-10-01 and retain the first common valid observations.

Primary evaluation begins:

**2020-01-01 UTC**.

Reporting slices:

- `FULL_AVAILABLE` — first common usable spot/perp/mark observation after funding launch;
- `PRIMARY_2020` — 2020-01-01 onward;
- `PRE_2023` — 2020-01-01 through 2022-12-31;
- `POST_2023` — 2023-01-01 onward.

Only fully closed 1h bars may be used.

For the common hourly grid from 2020-01-01 onward require:

- each of spot, futures-contract and futures-mark series has at least 99.5% of expected common hourly observations;
- no individual source gap greater than 6 hours;
- no duplicate open timestamps after deterministic last-observation deduplication;
- all retained prices positive;
- funding timestamps strictly ordered after deduplication.

No interpolation across missing market bars. If the gate fails, return `DATA_REDESIGN` and do not issue implementation conclusions.

## 5. Canonical capital convention — FULLY_FUNDED_50_50

Fresh NAV = 1.0 at the start of each evaluation slice.

At inception:

- allocate **50% of NAV** to long BTC spot;
- hold the other **50% of NAV** as USDT futures-margin collateral;
- short BTCUSDT perpetual in exactly the same BTC quantity as the long spot quantity;
- no external borrowing;
- no leverage optimization;
- no yield on collateral or spot;
- no use of unrealized spot gains as free futures collateral unless a scheduled rebalance explicitly transfers capital.

Thus the initial economic exposure is approximately:

- +50% NAV spot BTC notional;
- -50% NAV perpetual BTC notional;
- net BTC delta approximately zero;
- gross directional notional approximately 100% NAV.

This is intentionally capital-conservative. A later higher-leverage variant, if ever justified, must be a new version and may not rescue E002.

## 6. Price and funding accounting

The portfolio is self financing.

Between rebalances the spot BTC quantity and short-perpetual BTC quantity are held equal and fixed.

At each common hourly close:

1. update long-spot market value using spot close;
2. mark the short perpetual using the USD-M mark-price close and add `-q * change_in_mark_price` to the futures collateral account;
3. apply all funding observations whose timestamp occurs after the previous common close and at or before the current close boundary using the position quantity legally in force at that funding time;
4. positive published funding is income to the short; negative funding is a cash cost;
5. for funding rows with a published positive mark price, use that mark price for the funding-notional calculation; otherwise use the latest causally available fully closed 1h mark-price close at or before the funding timestamp.

Portfolio NAV:

`spot market value + futures collateral cash`

The resulting spot-versus-perpetual mark divergence is therefore explicitly reflected as basis P&L rather than assumed away.

## 7. Deterministic re-hedging / capital rebalance

Canonical rebalance frequency:

> **UTC calendar month-end only**

After the final common fully closed hourly bar of each UTC calendar month:

- recompute NAV;
- reset long spot market value to 50% of pre-cost NAV;
- set short-perpetual BTC quantity equal to the resulting spot BTC quantity;
- transfer bookkeeping cash between spot and futures collateral as required;
- charge execution costs on the absolute traded notional of each leg.

No weekly/daily/quarterly rebalance grid is allowed in E002.

Month-end is an operational convention chosen before results, not an optimized parameter.

## 8. Execution-cost assumptions

Apply the same all-in cost to each leg's traded notional.

Cost grid per leg:

- 5 bps;
- **10 bps baseline**;
- 25 bps stress.

Costs are charged on:

- initial spot purchase;
- initial perpetual short establishment;
- every month-end change in spot BTC quantity;
- every matching month-end change in perpetual BTC quantity;
- hypothetical final close of both legs for terminal liquidation-adjusted return.

The all-in rate is intended to absorb commission plus ordinary spread/slippage at this stage. E002 does not claim to reproduce a specific Binance VIP fee tier.

## 9. Separate futures-margin account and headroom

Futures collateral must be tracked separately from spot value.

Report at every hour:

- futures collateral cash;
- absolute short mark notional;
- close-to-close collateral ratio = futures collateral / short mark notional;
- conservative intrahour short-side collateral ratio using the 1h mark-price high before assuming offsetting spot gains can be transferred.

Define research diagnostics:

- `HARD_MARGIN_FAILURE`: futures collateral <= 0 at any point;
- `LOW_HEADROOM`: conservative intrahour collateral ratio <10%;
- `ADEQUATE_HEADROOM`: never below 10%.

The 10% threshold is a conservative research buffer, not a claim about Binance's exact tiered maintenance-margin rule.

E002 does not silently assume portfolio-margin cross collateralization.

## 10. Basis diagnostics

Report hourly:

- mark basis = mark price / spot price - 1;
- contract-close basis = futures contract close / spot close - 1.

Report by slice:

- mean and median basis;
- 1st/99th percentile basis;
- maximum absolute basis;
- worst 24h basis widening against the short-perpetual hedge;
- total pair price/basis P&L contribution separate from funding.

## 11. Funding ablations and adverse carry stress

Run exactly these funding treatments with the same price path and monthly rebalancing:

### REALIZED_FUNDING

Use published realized funding unchanged.

### ZERO_FUNDING

Set funding cash flow to zero. This isolates basis/rebalancing/execution effects.

### ADVERSE_FUNDING

For every observed funding rate:

- positive rate -> multiply by 0.5;
- negative rate -> multiply by 2.0.

This is a pre-specified robustness stress representing lower future carry plus more punitive inversions. It is not a forecast.

## 12. Required performance outputs

For every slice, fee level and funding treatment report:

- ending multiple;
- CAGR;
- annualized volatility from hourly NAV returns;
- Max Drawdown;
- Calmar;
- worst 7d and 30d portfolio return;
- total funding contribution;
- total pair price/basis contribution;
- total execution-cost drag;
- spot turnover;
- perpetual turnover;
- minimum close collateral ratio;
- minimum conservative intrahour collateral ratio;
- count of `LOW_HEADROOM` hours;
- hard-margin-failure flag.

At baseline 10 bps also report calendar-year portfolio returns and contribution decomposition.

## 13. Capital-efficiency / safe-yield hurdle

Because a fully funded cash-and-carry trade ties up capital that could otherwise sit in a safe sleeve, report excess CAGR versus fixed annual hurdle rates:

- 0%;
- 2.5%;
- 5.0%.

These are decision diagnostics, not modeled T-bill returns.

Classify POST_2023 baseline capital efficiency:

- `STRONG`: net CAGR >=5%;
- `MARGINAL`: net CAGR >=2.5% but <5%;
- `WEAK`: net CAGR <2.5%.

This prevents a positive but economically trivial carry from being mistaken for an attractive use of risky exchange capital.

## 14. E002 decision gate

E002 returns one of:

### IMPLEMENTATION_PROMISING

Require all central conditions:

1. REALIZED_FUNDING baseline net CAGR >0 on PRIMARY_2020, PRE_2023 and POST_2023;
2. POST_2023 baseline net CAGR >=2.5%;
3. PRIMARY_2020 Max DD <10%;
4. no `HARD_MARGIN_FAILURE`;
5. minimum conservative intrahour collateral ratio never below 10%;
6. 25 bps per-leg execution stress remains positive on PRIMARY_2020 and POST_2023;
7. ADVERSE_FUNDING baseline remains positive on PRIMARY_2020;
8. REALIZED_FUNDING materially improves results versus ZERO_FUNDING;
9. completed-year results are not dominated by a single year and recent economics remain positive.

A positive result is still not production PASS.

If capital-efficiency classification is only `MARGINAL`, preserve the candidate but do not justify live deployment while a safer sleeve offers a comparable hurdle.

### IMPLEMENTATION_MIXED

Use if the strategy is positive but one or more margin, recent-regime, cost-stress or capital-efficiency conditions fail without outright economic collapse.

Action: no leverage/threshold rescue on the same history. Preserve findings and decide between forward observation, alternative venue/data validation, or closing the implementation branch.

### IMPLEMENTATION_FAIL

Use if realized-funding portfolio return is non-positive on PRIMARY_2020 or POST_2023, or if a hard margin failure occurs under the canonical fully funded convention.

Action: close the unconditional fully funded BTC spot/perp implementation as currently framed. Do not tune funding-entry thresholds or leverage to rescue the same sample.

## 15. What E002 still does not prove

Even IMPLEMENTATION_PROMISING does not remove:

- exchange default / withdrawal freeze risk;
- stablecoin depeg / collateral impairment;
- order-book gaps beyond the fixed execution-cost stress;
- API outage and legging risk;
- tax/legal constraints;
- production custody design;
- true OOS persistence of future funding.

These belong to later forward/operational testing.

## 16. Anti-overfitting freeze

Before inspecting E002 results, freeze:

- BTCUSDT only;
- always-on carry;
- 50% spot / 50% futures-collateral initial capital split;
- equal BTC quantity on both legs;
- month-end rebalance frequency;
- no external borrowing;
- no cross-margin assumption;
- 5/10/25 bps per-leg cost grid;
- REALIZED / ZERO / ADVERSE funding treatments;
- 10% conservative collateral-headroom threshold;
- 0/2.5/5% capital-efficiency hurdles;
- evaluation slices;
- decision rules.

Any funding threshold, leverage change, collateral fraction change, rebalance-frequency search or venue switch creates a new protocol/version.