# R001 — Free Data Strategy v0.1

**Candidate:** Antifragile Convex Barbell (R001)  
**Goal:** obtain enough historical options data to falsify or preliminarily validate the put-only hypothesis without purchasing commercial datasets.

## 1. Key finding

Tardis.dev explicitly allows historical datasets for the **first day of every month** to be downloaded **without an API key**. Deribit coverage includes all options and goes back to 2019-03-30. The normalized `options_chain` dataset contains bid/ask, IV, underlying price and Greeks.

This creates a viable no-cost research path for a **monthly decision strategy**.

## 2. Important distinction: screening vs final validation

Free first-of-month data is sufficient for an early economic screening experiment if we intentionally define the screening strategy to make decisions on the first day of each month.

It is **not sufficient by itself** for final high-resolution validation because:

- intramonth mark-to-market drawdowns are not observable from one monthly snapshot;
- a roll triggered exactly at 30 DTE may occur between first-of-month observations;
- crisis events between snapshots may be missed in mark-to-market diagnostics;
- daily IV/RV regime logic cannot be fully reproduced from monthly option chains alone.

Therefore the free-data experiment is labelled **E003-S — Screening**, not the final E003 validation.

## 3. Free data hierarchy

### Tier A — Tardis first-day monthly option data (primary)

Use Deribit first-day-of-month historical data without API key.

Preferred inputs:

1. raw one-minute `ticker` feed around a fixed decision time, if it yields sufficiently complete option coverage;
2. otherwise normalized `options_chain` first-day file, streamed and reduced to a small snapshot locally.

The raw one-minute HTTP API is preferred because it can avoid downloading hundreds of megabytes for an entire day.

### Tier B — Deribit free research datasets

Use public/academic/open datasets for cross-checks and additional coverage where licences permit.

Known useful sources include:

- University of Western Australia Deribit options dataset associated with Hoang & Baur (CC BY);
- free six-month hourly BTC option snapshot dataset referenced by Deribit Insights (2024-01-13 to 2024-07-27);
- CryptoDataDownload Deribit options OHLCV by maturity for coarse price-history checks.

These sources are supplementary because they may not contain executable bid/ask and Greeks in the exact form required for the primary simulator.

### Tier C — OKX first-day monthly data (cross-venue)

Tardis also provides first-day-of-month OKX Options historical data without an API key, with OKX options coverage beginning in 2020.

This is valuable later as a cross-venue robustness check.

## 4. Screening protocol E003-S

### Decision schedule

- first calendar day of each month;
- fixed UTC decision time, initially 12:00 UTC;
- only information observed at or before that timestamp may be used.

### Portfolio

Baseline:

- 90% cash;
- 10% BTC spot equivalent.

Put variant:

- same 90/10 baseline;
- buy 15-delta BTC put;
- eligible DTE: 60–120 days;
- choose actual listed expiry nearest target maturity;
- annual premium budget: 2% NAV;
- monthly budget = annual budget / 12;
- purchase at executable ask;
- next monthly observation values/sells at executable bid where available.

### Why first-of-month is acceptable for screening

The rule is fixed in advance and matches a real systematic calendar rule; it is not chosen after observing returns. It is also aligned with the free historical-data availability constraint.

However, results must be explicitly labelled **data-constrained screening results** and must never be presented as final proof.

## 5. Efficient acquisition plan

Do **not** download every full 500MB daily options-chain file unless necessary.

Try the Tardis raw HTTP API first:

- query only the first day of each month;
- query one or a few one-minute windows around the decision timestamp;
- request the Deribit `ticker` channel;
- reconstruct the latest ticker per option instrument;
- retain BTC options only;
- normalize to the internal `OptionQuote` representation;
- store only compact CSV/Parquet snapshots.

If ticker coverage within one minute is incomplete, expand the lookback to 5–15 minutes. Only if this remains inadequate should the workflow fall back to streaming the full daily `options_chain` file and discarding the raw file after snapshot extraction.

## 6. Storage target

The research repository should never store multi-hundred-megabyte raw market files.

Store only:

- compact monthly snapshots;
- source URLs/date/provider metadata;
- SHA256/content metadata where practical;
- extraction code version;
- data-quality audit results.

Raw source files remain external and reproducible from documented source endpoints.

## 7. Validation gates

A free monthly snapshot is accepted only if:

- sufficient BTC options are present;
- expiry parsing succeeds;
- delta is present for enough contracts;
- executable ask exists for candidate purchases;
- executable bid exists for valuation/exit candidates;
- underlying price is present;
- timestamps are not future relative to decision time;
- selected 10Δ/15Δ/20Δ puts are economically plausible;
- available DTE buckets are recorded, not synthesized.

## 8. What free monthly data can answer

It can answer the first-order economic question:

> Does regularly purchasing real historical BTC downside convexity at actual quoted asks show enough crisis benefit to justify its persistent premium cost on a monthly portfolio basis?

It can support:

- premium burn;
- monthly portfolio returns;
- monthly max drawdown;
- tail-month protection;
- contract-selection robustness;
- coarse premium-budget comparisons;
- put-only vs no-option ablation.

## 9. What it cannot prove

It cannot fully establish:

- daily/intraday max drawdown;
- precise crisis path behaviour;
- exact 30-DTE roll execution between monthly observations;
- continuous gamma/vega exposure;
- daily IV-regime timing;
- detailed liquidity deterioration during intramonth panic periods.

Those become requirements only if R001 survives the free screening stage.

## 10. Cost discipline

Commercial data should be considered only if all of the following are true:

1. R001 passes free-data screening;
2. the result is economically material rather than marginal;
3. the missing higher-frequency information could plausibly change the decision;
4. no adequate academic/open/venue source can fill the gap;
5. the expected value of obtaining final evidence justifies the data cost.

Until those conditions are met, **data budget = $0**.

## 11. Immediate next step

Build and test a small Python collector that requests Tardis first-of-month Deribit `ticker` data for a single minute, reconstructs a full BTC option snapshot and compares the resulting 15Δ/~90D selection against the already validated full-day `options_chain` sample for 2020-03-01.

If the minute collector reproduces the same or economically equivalent candidate, scale it across all first-of-month dates and create the free monthly R001 dataset.
