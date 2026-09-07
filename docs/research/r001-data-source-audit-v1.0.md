# R001 — Antifragile Convex Barbell: Data Source Audit v1.0

**Project:** BotMarketplace / botmarketplace.store  
**Research candidate:** R001 — Antifragile Convex Barbell  
**Status:** Data-source design / pre-implementation  
**Version:** 1.0  
**Date:** 2026-09-07

---

## 1. Objective

Determine which historical data sources are sufficiently complete and realistic to test R001 independently of BotMarketplace production infrastructure.

The immediate research priority is not to collect every possible market dataset. It is to obtain the minimum data required for the first falsification experiments, especially the put-only convexity experiment.

The most demanding requirement is historical BTC option-chain data with executable pricing information.

---

## 2. Required data by sleeve

### 2.1 Capital Preservation / Carry

For initial cash baseline:

- USD / stable reserve value series;
- explicit stablecoin assumptions if stablecoins are used.

For later basis/funding research:

- BTC spot prices;
- perpetual prices;
- funding rates and funding timestamps;
- dated futures prices;
- expiry dates;
- futures basis;
- bid/ask where possible;
- volume/open interest where relevant;
- fee schedules.

### 2.2 Directional Growth

Minimum:

- BTC spot or index OHLCV;
- sufficiently accurate timestamps;
- exchange fee assumptions;
- execution-price assumptions.

### 2.3 Convexity

Minimum historical option-chain snapshot fields:

- exchange;
- instrument name;
- timestamp;
- option type;
- strike;
- expiry;
- underlying/index price;
- bid price;
- ask price;
- bid size;
- ask size;
- mark price;
- implied volatility;
- delta.

Strongly preferred:

- bid IV;
- ask IV;
- gamma;
- theta;
- vega;
- rho;
- open interest;
- volume;
- contract metadata;
- creation timestamp;
- settlement rules.

A historical option backtest based only on closing underlying prices and synthetic Black-Scholes premiums is not sufficient for primary acceptance/rejection of R001.

---

## 3. Primary venue recommendation: Deribit

Use Deribit as the first options venue for R001 research.

Reasons:

- long history as a crypto derivatives venue;
- historical BTC options trading;
- documented instrument metadata;
- official historical trade/instrument endpoints;
- mature third-party historical datasets with Deribit options coverage;
- sufficient market structure for delta/DTE-based contract selection research.

This recommendation is for research comparability and data availability, not a permanent venue selection for production.

---

## 4. Source A — Deribit official historical APIs

### 4.1 What is available

Deribit documents historical trade and instrument information going back to its launch period and exposes dedicated historical endpoints under `history.deribit.com`.

Relevant public capabilities include historical instrument metadata and historical trades.

Historical option trade records include fields such as:

- instrument name;
- timestamp;
- price;
- amount;
- direction;
- index price;
- mark price;
- implied volatility.

Instrument metadata includes:

- creation timestamp;
- expiry timestamp;
- contract size;
- option/future specifications;
- strike where applicable.

### 4.2 Strengths

- first-party source;
- no need to infer whether a contract historically existed;
- useful for instrument-universe reconstruction;
- useful for trade-level cross-checks;
- useful for validating third-party datasets;
- historical trade records can support preliminary price sanity checks.

### 4.3 Critical limitation

Executed trades are not equivalent to a full historical option chain.

For R001 we need to know what price could realistically have been paid at a strategy decision timestamp even if no trade occurred exactly then.

Historical trades alone therefore do not reliably provide:

- contemporaneous best bid/ask for all relevant strikes;
- option-chain state at every rebalance timestamp;
- quoted liquidity;
- continuous Greeks across the full chain.

Therefore Deribit official historical trades are valuable as a **verification and fallback source**, but not sufficient by themselves for the primary realistic option-fill backtest.

---

## 5. Source B — Tardis.dev

### 5.1 Data suitability

Tardis.dev explicitly provides historical crypto options-chain datasets and supports Deribit.

Its published options-chain schema includes the fields required by R001, including:

- symbol;
- call/put type;
- strike;
- open interest;
- last price;
- bid price and bid amount;
- bid IV;
- ask price and ask amount;
- ask IV;
- mark price;
- mark IV;
- underlying index;
- underlying price;
- delta;
- gamma;
- vega;
- theta;
- rho;
- exchange timestamp;
- local collection timestamp.

This is close to the ideal raw dataset for R001.

### 5.2 Historical scope

Tardis states that its historical market-data archive extends back to 2019-03-30 for the majority of supported exchanges, with exact dates varying by exchange.

Its published Deribit options-chain example contains BTC options observations from July 2019, confirming that Deribit BTC option-chain history exists in the archive by that period.

The exact first date and completeness for every required Deribit channel must still be verified before buying a full historical subscription.

### 5.3 Access model

Tardis is subscription-based rather than a one-off historical-data purchase.

Current documentation states:

- a 30-day free trial is available;
- the trial includes a randomly selected recent 7–14-day historical range;
- no payment details are required for the trial;
- Academic and Solo tiers use downloadable CSV datasets;
- Pro and Business additionally provide replay/API tooling;
- historical depth depends on billing interval and subscription type;
- yearly Academic/Solo/Pro subscriptions provide four years of history;
- yearly Business provides access to all available history;
- quarterly billing provides 12 months;
- monthly billing provides four months.

This access structure matters materially for R001 because a four-year window beginning in 2026 would not include COVID 2020.

### 5.4 Strengths

- real historical option chains;
- bid/ask and sizes;
- Greeks;
- IV data;
- timestamps;
- open interest;
- practical CSV workflow;
- suitable for executable-fill research;
- can support historical reconstruction without synthesizing options.

### 5.5 Limitations

- commercial access for the longer historical range;
- tick-level raw data can be extremely large;
- subscription scope must be chosen carefully;
- vendor data still requires independent validation against first-party Deribit trades/metadata.

### 5.6 Recommendation

**Primary candidate for R001 historical options research.**

Do not purchase the maximum data plan initially.

First validate the schema and research pipeline with a free/recent sample or limited accessible slice.

---

## 6. Source C — Coin Metrics

Coin Metrics exposes catalogued Deribit option-market datasets including market implied volatility, Greeks, and contract-price coverage.

Examples in its API documentation show Deribit BTC option instruments and min/max historical timestamps.

### Strengths

- institutional-quality normalized data model;
- option IV / Greeks products;
- useful potential cross-check;
- catalog endpoints make coverage inspection possible.

### Limitations

- significant data access requires authorization/commercial access;
- coverage can vary by instrument and metric;
- it is not yet established that the product gives the exact historical executable bid/ask chain state required by R001 at our intended timestamps.

### Recommendation

Treat as a **secondary validation/vendor alternative**, not first choice until executable quote coverage and economics are confirmed.

---

## 7. Source D — Kaiko

Kaiko provides institutional crypto market data and an implied-volatility product for Deribit-derived BTC/ETH options.

Its methodology explicitly addresses:

- sparse option trades;
- missing quotes;
- wide bid/ask spreads;
- strike/expiry interpolation;
- hourly volatility estimates.

### Strengths

- strong institutional data-quality focus;
- useful IV surface / volatility-regime research;
- suitable for checking independent IV and surface calculations;
- relevant later for R001 volatility-regime experiments.

### Limitation for early R001

Our first convexity experiment requires real option selection and executable bid/ask accounting, not only a smoothed implied-volatility surface.

### Recommendation

Potentially useful for later IV/RV/skew/term-structure research and cross-validation, but not the primary first dataset for E003.

---

## 8. Source E — Amberdata

Amberdata provides crypto derivatives and volatility datasets and has published substantial research using Deribit BTC options across multiple market regimes.

### Strengths

- derivatives-focused analytics;
- volatility surfaces and option research;
- institutional-quality candidate source;
- potentially useful for cross-validation.

### Limitation

The exact cost/access model and raw historical quote-chain fields required for R001 need to be verified before adopting it as the primary source.

### Recommendation

Keep as vendor alternative / cross-check, not initial default.

---

## 9. Source decision matrix

| Source | Instrument history | Historical trades | Historical bid/ask chain | IV | Greeks | OI | Primary role |
|---|---:|---:|---:|---:|---:|---:|---|
| Deribit official | Yes | Yes | Insufficient for full chain reconstruction | Trade IV | Limited for historical chain | Limited | First-party validation / metadata |
| Tardis.dev | Yes/vendor metadata | Yes | **Yes** | **Yes** | **Yes** | **Yes** | **Primary R001 options dataset** |
| Coin Metrics | Yes | Product-dependent | Verify | Yes | Yes | Product-dependent | Secondary vendor / cross-check |
| Kaiko | Yes/product-dependent | Yes | Product-dependent | **Strong** | Surface analytics | Product-dependent | IV/regime research |
| Amberdata | Yes/product-dependent | Yes/product-dependent | Verify | Strong | Strong | Likely/product-dependent | Secondary vendor / cross-check |

---

## 10. Minimum dataset for E003 — Put-only convexity

Do not ingest every tick of every option initially.

E003 requires only enough data to implement this decision rule:

1. At each scheduled option-purchase timestamp, reconstruct the available BTC put universe.
2. Keep contracts whose DTE falls in the predefined window around the target maturity.
3. Select the contract closest to target absolute delta, initially 15Δ.
4. Require valid two-sided or otherwise acceptable executable quotes.
5. Buy at historical ask plus any additional stress slippage.
6. Mark the position using a consistent observable rule.
7. Roll according to the predefined DTE policy.
8. Sell at historical bid minus stress slippage or settle at expiry.

### Recommended first snapshot frequency

For the first monthly/low-frequency R001 experiments:

- one deterministic decision timestamp per day is sufficient for selection/marking research;
- preserve higher-frequency raw data only around execution timestamps if necessary.

A reasonable first convention is a fixed UTC timestamp, selected before backtest results are examined.

This materially reduces storage and compute cost without pretending the strategy trades intraday.

---

## 11. Dataset layers

Use three separate layers rather than one giant raw file.

### Layer 1 — Raw immutable vendor data

Never modify.

### Layer 2 — Normalized option-chain snapshots

Suggested schema:

```text
ts
exchange
underlying
instrument
option_type
strike
expiry_ts
dte
underlying_price
bid
ask
bid_size
ask_size
mark
bid_iv
ask_iv
mark_iv
delta
gamma
vega
theta
open_interest
volume_if_available
source
```

### Layer 3 — Research decision table

One row per rebalance / roll decision:

```text
decision_ts
strategy_version
available_contracts
selected_contract
selection_reason
target_delta
actual_delta
target_dte
actual_dte
bid
ask
fill_assumption
premium
nav
```

This makes option selection auditable.

---

## 12. Data-validation requirements

Before any strategy result is accepted, run at least the following checks.

### Completeness

- missing timestamps;
- missing expiries;
- missing strike regions;
- sudden unexplained universe collapse;
- quote gaps.

### Quote validity

Reject or flag:

- bid > ask;
- negative prices;
- zero/invalid underlying price;
- stale quotes beyond a predefined age;
- impossible IV/Greek values unless independently explained.

### Instrument consistency

- expiry must be after creation;
- strike and option type must match symbol metadata;
- only instruments known to exist at time `t` may be selected.

### Cross-source checks

For sampled dates:

- compare Tardis trade/mark observations with Deribit official historical trades;
- compare instrument metadata with Deribit;
- independently recompute selected option delta/IV for a sample where feasible;
- validate settlement logic.

---

## 13. Historical-period implications

The desired crisis set includes events such as COVID 2020, 2021 leverage flushes, Terra/3AC/Celsius, FTX, later bull regimes, and low-volatility periods.

This creates an important procurement constraint:

- a vendor subscription granting only the most recent four years in 2026 will exclude COVID 2020 and part/all of 2021;
- therefore a full long-history R001 study may require a plan with access to older history, a separate historical source, or a staged study in which recent data is validated first and older coverage is acquired only after the simulator passes validation.

Do not silently drop early crisis regimes simply because the convenient subscription tier cannot access them.

---

## 14. Recommended procurement sequence

### Phase D0 — No purchase

Use:

- Deribit official documentation/history endpoints;
- Tardis published sample/schema;
- public recent/current chain data where useful;
- free vendor trial if available.

Goal: validate the data model and selection logic.

### Phase D1 — Small recent validation slice

Obtain enough real chain data to test:

- parser;
- timestamps;
- delta selection;
- DTE selection;
- bid/ask fills;
- roll accounting;
- Greeks/IV sanity checks.

Do not evaluate profitability yet.

### Phase D2 — Multi-regime historical subset

Once D1 passes, obtain a longer period sufficient to run E003/E004 and verify option-premium accounting.

### Phase D3 — Full research history

Only after the simulator and data validation pass, obtain the oldest practical history required for the complete walk-forward/event-study protocol.

---

## 15. What should not be done

Do not:

- purchase a huge tick archive before validating its schema;
- use synthetic Black-Scholes option prices as the main R001 proof;
- use only last-trade prices as executable fills;
- select strikes that did not exist at the decision timestamp;
- use current Greeks to classify historical contracts;
- interpolate missing bid/ask prices without explicitly labelling the experiment as synthetic;
- silently use mid prices as if they were executable;
- drop illiquid contracts after seeing their subsequent outcomes;
- ignore quote staleness;
- mix UTC/local timestamps without explicit normalization.

---

## 16. Decision

### Primary source

**Tardis.dev Deribit BTC options-chain history** is the best first candidate for realistic R001 option backtesting because its published schema contains the core fields required for contract selection, executable pricing, IV and Greek-based research.

### First-party verification source

**Deribit historical instruments and trades** should be used to validate instrument existence, historical trades, marks/IV where available, and settlement/instrument metadata.

### Secondary sources

**Coin Metrics, Kaiko and Amberdata** remain valuable potential cross-checks and later sources for volatility-surface and regime analysis.

---

## 17. Next action

Do not build production BotMarketplace support yet.

Next research implementation step:

> **Build the smallest independent data-validation prototype capable of loading one historical Deribit BTC option-chain sample, normalizing it, selecting a 15Δ put near the target DTE, applying executable bid/ask fills, and producing an auditable decision record.**

This prototype is a research tool, not a production trading system.

Only after this data-validation step passes should E003 historical profitability testing begin.
