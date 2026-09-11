# SC001 — Data Sufficiency Audit v0.1

**Project:** BotMarketplace / BotMarketplace.store  
**Research branch:** SCALPING RESEARCH / SC001  
**Date:** 2026-09-11  
**Status:** PRE-TEST DATA AUDIT — NO SC001 P&L INSPECTED  
**Repository:** `AlexeyIvy/-botmarketplace-site`

---

## 1. Independence boundary

SC001 is a new independent research branch.

SC001 must not modify, retune, reset, merge, replace, or retrospectively influence:

- R009-E002;
- R003-E003 Binance;
- R003-X003 Bybit;
- R010-E001;
- Safe-Sleeve S002.

Their forward clocks, frozen parameters, interpretations, and decision rules remain unchanged. Existing research artifacts may be read only as data-source / implementation evidence. SC001 results must never be used to rewrite their frozen rules.

No real-money deployment is authorized by SC001.

---

## 2. Audit question

Before designing any strategy, determine whether the data already present in the project can honestly support:

A. true scalping research;
B. short-horizon intraday research only;
C. neither.

No new paid data is to be purchased at this stage.

---

## 3. Located datasets and artifacts

### 3.1 Binance USD-M broad-universe daily archive — R002

Primary file:

`r002_binance_full_universe_daily.csv`

State / validation evidence:

- 637,705 rows after repair;
- 864 archive-defined symbols;
- period: 2020-01-01 through 2026-08-31;
- zero duplicate symbol-date rows in the validated research table;
- zero missing core rows;
- zero non-positive price rows;
- zero negative-volume rows;
- zero invalid-OHLC rows.

Stored fields include:

- symbol;
- open/close timestamps;
- daily open/high/low/close;
- base volume;
- quote volume;
- number of trades;
- taker-buy base volume;
- taker-buy quote volume;
- source month.

Important qualification: these are **daily aggregates**. Trade count and taker-buy aggregates do not turn daily OHLCV into trade-level order flow.

Point-in-time/listing diagnostics already found a small number of long listing gaps and some exchange-metadata matching/onboarding complications. These are relevant for broad-universe cross-sectional work but do not create intraday data.

**SC001 classification:** useful for long-horizon context / regime diagnostics only. Not usable for true scalping or short-horizon intraday entry/exit reconstruction.

### 3.2 Binance BTCUSDT hourly spot/perpetual/mark/funding history — R003-E002

This is the highest-frequency long historical dataset already evidenced in the project.

Sources:

- Binance Spot BTCUSDT klines;
- Binance USD-M BTCUSDT perpetual contract klines;
- Binance USD-M BTCUSDT mark-price klines;
- Binance BTCUSDT realized funding history.

Primary hourly window:

- 2020-01-01 through 2026-09-09 19:00 UTC;
- spot primary rows: 58,620 of 58,652 expected, coverage ~99.945%;
- perpetual contract primary rows: 58,652, coverage 100%;
- mark primary rows: 58,652, coverage 100%;
- common primary rows: 58,620 of 58,652 expected, coverage ~99.945%;
- maximum common gap: 6 hours.

Funding:

- 7,670 clean observations;
- 7,357 aligned to the hourly history in the existing R003 audit;
- history begins 2019-09-10;
- typical cadence approximately 8 hours, subject to actual published timestamps.

The R003-E002 normalized engine retained:

- OHLC for spot;
- OHLC for perpetual contract;
- OHLC for mark price;
- timestamps;
- realized funding.

It did **not** retain volume in its normalized DataFrames.

However, the Android/Pydroid resumable launcher persisted the original Binance JSON kline pages in `R003_E002_WORKSPACE/_cache` and/or `_cache_bundle.zip`. Because standard Binance kline rows were preserved as raw JSON before normalization, base volume, quote volume, trade count, and taker-buy aggregates are technically recoverable from the local raw cache if that cache is still retained and passes checksum verification.

For SC001-E001, volume-dependent rules are deliberately avoided so that the first falsification experiment does not depend on a reconstruction step.

Missing from this long historical dataset:

- historical best bid/ask;
- order-book levels;
- individual trades;
- queue position;
- sub-minute path;
- millisecond/second execution path.

**SC001 classification:** sufficient for **hourly short-horizon intraday research**, not true scalping.

### 3.3 R003 forward datasets

R003-E003 Binance and R003-X003 Bybit use 1-hour bars prospectively from their frozen inception boundaries. They are active independent forward records and are out of bounds for SC001 redesign.

SC001 must not use their post-inception outcomes as a tuning source.

Their presence confirms 1h plumbing but does not create a multi-year minute/tick dataset.

### 3.4 Bybit historical material

The project contains Bybit funding/history work and a separate forward R003-X003 record. Existing evidence is sufficient for venue/funding structural research but no long multi-regime Bybit tick/trade/order-book or minute-level dataset has been located in the accessible SC001 audit.

**SC001 classification:** no evidence of a retained Bybit dataset sufficient for true scalping.

### 3.5 Deribit / Tardis BTC options snapshots — R001

The retained free Tardis dataset contains 84 first-of-month BTC option-chain decision snapshots from 2019-10-01 through 2026-09-01, with 54,329 normalized option rows and executable bid/ask information for many contracts.

The underlying raw first-day files can contain many quote updates, but the project research dataset deliberately extracts a deterministic monthly snapshot. It is not continuous multi-day intraday history.

**SC001 classification:** excellent for the original low-frequency options research purpose, not usable as a continuous scalping history.

### 3.6 BotMarketplace application candle storage / demo backfill

The platform code supports M1/M5/M15/H1 multi-timeframe plumbing and can ingest candle datasets. Operational documentation also describes recent Bybit backfills, with a typical BTCUSDT example of roughly 8,640 M5 rows / 1,854 H1 rows over about 30 days.

This proves platform capability, **not** the existence of a long validated minute history. A ~30-day M5 sample is inadequate for multi-regime historical validation and cannot establish durable scalping edge.

No long validated project dataset at tick, trade, order-book, 1-second, or multi-year 1-minute resolution was located in this audit.

---

## 4. Frequency matrix

| Frequency / data type | Located long usable history? | SC001 interpretation |
|---|---:|---|
| Tick quotes | No | Not testable |
| Individual trades | No long retained history located | Not testable |
| Order book / L2 | No | Not testable |
| 1 second | No | Not testable |
| 1 minute | No long validated history located | True 1m scalping not testable |
| 5 minute | Only recent/demo-scale evidence (~30 days) | Too short for robust multi-regime validation |
| 15 minute | Platform support exists; no long validated dataset located | Not currently testable as a robust historical branch |
| 1 hour | **Yes — Binance BTCUSDT, ~2020-01-01 to 2026-09-09** | **Primary usable short-horizon dataset** |
| Daily | **Yes — broad Binance USD-M universe + long BTC spot** | Regime/context only for SC001 |

---

## 5. Market-field matrix

| Field | Binance BTC 1h long history | Binance broad daily | Deribit monthly snapshots |
|---|---:|---:|---:|
| OHLC | Yes | Yes | N/A / option quotes |
| Volume | Recoverable from raw cache; omitted from normalized R003 table | Yes | Product-dependent fields |
| Trade count | Recoverable from raw kline cache | Yes, daily aggregate | Not a continuous trades tape |
| Taker-buy aggregate | Recoverable from raw kline cache | Yes, daily aggregate | No relevance to continuous BTC perp scalp |
| Historical bid/ask | No | No | Yes for snapshot options where quoted |
| Order book | No | No | No continuous SC001 book history |
| Funding | Yes, BTCUSDT | Not in R002 daily table | N/A |
| Mark price | Yes, BTCUSDT hourly | No | Option mark in snapshots |
| Index price | Not a dedicated long hourly SC001 series in the R003 normalized table | No | Yes/underlying fields in option snapshots |

---

## 6. Timestamp / gap quality

### Binance BTC hourly common history

The existing audit reports ~99.945% common primary coverage with a maximum common gap of 6 hours. Futures-contract and mark series have full primary hourly coverage; the small deficit is driven by spot history.

SC001 must:

- preserve UTC;
- use only fully closed bars;
- calculate signals only from information available at or before the signal bar close;
- enter no earlier than the next bar after the signal is observable;
- never fill using a signal bar high/low after the fact;
- explicitly flag / skip signals whose required next bar is absent across a data gap.

### Broad daily universe

The validated table is clean at row level, but listing episodes / historical availability require point-in-time treatment. SC001 must not choose an asset after examining its historical P&L.

---

## 7. Fees and execution information

Existing project research contains execution-cost grids, but SC001 will define an independent frozen cost model before testing.

For the long hourly history there is **no historical bid/ask series**. Therefore:

- exact spread cannot be reconstructed;
- exact slippage cannot be reconstructed;
- queue position cannot be modeled;
- second-level latency cannot be modeled;
- intra-hour stop/target ordering cannot be known reliably from OHLC alone.

Any hourly backtest must therefore use a conservative explicit cost proxy and label it as a proxy, not as reconstructed historical fills.

SC001 must not call a strategy viable if its net edge is close to the size of this execution-model uncertainty.

---

## 8. Can realistic execution be reconstructed?

### True scalping

**No.** Not from the current retained long historical data.

A proper true-scalping execution study would normally require at least minute/sub-minute trades and preferably contemporaneous bid/ask / L2 information. Those data are not presently evidenced over a sufficiently long multi-regime period.

### Hourly short-horizon intraday

**Partially.** We can model causal bar-to-bar execution using next-hour prices plus conservative transaction-cost and latency stress assumptions. We cannot claim exchange-microstructure fidelity.

---

## 9. Final data sufficiency decision

### A) True scalping

**NO — CURRENT DATA INSUFFICIENT.**

Do not use the label `scalping` for results produced from the current 1h historical dataset.

### B) Short-horizon intraday

**YES — LIMITED BUT RESEARCHABLE.**

The strongest existing source is Binance BTCUSDT hourly spot / perpetual / mark / funding history from 2020 through 2026. It spans multiple market regimes and has high timestamp coverage.

### C) Completely insufficient

**NO.** The data are not completely insufficient because a legitimate hourly short-horizon falsification program is possible.

Therefore SC001 proceeds as:

> **SC001 = short-horizon intraday research using existing data; true scalping remains untested.**

If later research specifically requires true scalping, a separate data-acquisition gate must be opened. It must first investigate free/public sources; paid data are not authorized by this v0.1 audit.

---

## 10. What SC001 must not infer

- M1/M5 platform support does not imply long M1/M5 history exists.
- Daily taker-buy aggregates are not order flow.
- Hourly OHLC is not microstructure.
- A spread proxy is not historical bid/ask.
- A profitable hourly backtest is not proof of a scalping strategy.
- Current exchange filters are not guaranteed to equal historical filters.
- R003/R009/R010 results are not SC001 calibration targets.

---

## 11. Next permitted step

Freeze an independent SC001 research protocol and a first **hourly short-horizon** experiment before calculating any SC001 strategy P&L.
