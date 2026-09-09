# R002 Next-Chat Handoff — 2026-09-09

Use this document to continue the BotMarketplace R002 research in a fresh ChatGPT conversation without reconstructing prior context.

## Project and research style

Repository: `AlexeyIvy/-botmarketplace-site`

Research style:

- falsification-first;
- prefer simple rules over parameter-rich strategies;
- do not defend prior ideas;
- do not tune after seeing results unless a new strategy version is explicitly created;
- historical results are not future guarantees;
- preserve frozen forward clocks independently from new research branches.

User works primarily from Android/Pydroid and prefers complete copy-paste code blocks when local scripts are needed.

## R001 status

R001 was a convex/barbell options idea. It demonstrated real crisis convexity but static put protection had too much premium drag. IV-only and IV/RV filters improved economics but failed late-period validation. Current status: **REDESIGN / PAUSED**. Do not spend current effort on R001 unless a genuinely new options hypothesis or denser historical option data appears.

## R002 primary strategy

Frozen baseline:

`close > SMA120 -> long, else cash`

Daily bars. Signal formed using fully closed day t data and applied to t+1 return. No same-close look-ahead.

SMA120 was selected from a broad SMA110-130 robustness plateau rather than choosing the single best in-sample SMA.

Frozen BTC SMA120 forward validation is already in progress and must not be reset by any new research branch.

## Earlier R002 evidence

BTC historical robustness was strong. Historical reference through 2026-09-07 was approximately:

- CAGR 55.8%;
- Max DD -32.3%;
- BTC buy-and-hold CAGR 42.5%;
- BTC buy-and-hold Max DD -76.7%;
- exposure 57.8%;
- 59 switches.

Seven-asset cross-asset panel:

- BTCUSDT
- ETHUSDT
- SOLUSDT
- XRPUSDT
- LTCUSDT
- ADAUSDT
- BNBUSDT

SMA120 improved both CAGR and Max DD on 5/7 maximum-history assets. Cross-asset verdict: **PARTIAL PASS**.

## R002.1 ADX branch

Tested SMA120 + ADX14 with thresholds 15/20/25. ADX20 initially looked useful at portfolio level, especially for drawdown reduction, but later tournament comparison showed it cut return and did not justify the extra complexity. Current status: **NOT PROMOTED**.

## R002.2 volatility-target branch

Tested SMA120 with RV20 no-leverage scaling at 15/20/25/30% annualized volatility targets. It greatly reduced drawdown but cut participation and CAGR too much.

Approximate baseline stress results:

- SMA120: CAGR 50.19%, Max DD -51.85%
- VT15: 9.52%, -9.33%
- VT20: 12.75%, -12.29%
- VT25: 15.94%, -15.17%
- VT30: 18.98%, -17.85%

Current status: **REDESIGN / NOT PROMOTED**.

## Historical/non-survivor subset

A fixed Binance historical subset was collected before strategy testing:

- 22 historical/non-survivor candidates;
- 7 current controls;
- 29 total symbols;
- 37,821 daily rows;
- 0 failed downloads.

Important Binance data issue discovered: some delisted contracts continue with long dead tails of zero volume and unchanged price. Research cleaning rule: trim each symbol after its final positive-volume trading day.

Point-in-time subset portfolio at 10 bps, no disappearance penalty:

- SMA120 CAGR ~52.25%
- SMA120 Max DD ~-51.21%
- passive comparator CAGR ~37.83%
- passive comparator Max DD ~-86.85%

Verdict: **PASS WITH CAVEATS**.

## Independent Donchian test

Independent trend-family confirmation tested:

- 50/25
- 100/50
- 200/100

Common 200-day warmup. Donchian channels use only prior highs/lows. Signal at t applied to t+1.

Common-period approximate results:

- SMA120 CAGR 46.86%, Max DD -54.53%
- Donchian100/50 CAGR 46.77%, Max DD -39.78%
- Buy & Hold CAGR 24.84%, Max DD -89.47%

Turnover:

- SMA120 ~86.94
- Donchian100/50 ~14.73

At 50 bps cost:

- Donchian100/50 CAGR ~45.37%
- SMA120 CAGR ~38.75%

Verdict:

- independent trend thesis: **PASS**
- Donchian100/50: **PROMOTE TO CO-FINALIST / CHALLENGER**

## Candidate tournament

Approximate unified results:

| Candidate | CAGR | Max DD | Worst year | Turnover |
|---|---:|---:|---:|---:|
| SMA120 | 46.86% | -54.53% | -28.55% | 86.94 |
| SMA120+ADX20 | 35.80% | -40.85% | -22.54% | 89.20 |
| Donchian100/50 | 46.77% | -39.78% | -16.04% | 14.73 |
| SMA120+VT30 | 20.84% | -18.56% | -10.40% | 57.18 |

Current finalists:

1. SMA120 — frozen primary/control.
2. Donchian100/50 — co-finalist/challenger.

## Ensemble diagnostic

Tested:

- SMA120
- Donchian100/50
- 50/50 capital blend
- AND
- OR

Approximate results:

| Variant | CAGR | Max DD | Turnover |
|---|---:|---:|---:|
| SMA120 | 46.86% | -54.53% | 86.94 |
| Donchian100/50 | 46.77% | -39.78% | 14.73 |
| 50/50 blend | 47.39% | -46.88% | 50.79 |
| AND | 39.24% | -44.28% | 39.84 |
| OR | 54.45% | -50.72% | 61.83 |

Signal agreement ~80.9% of eligible symbol-days. Daily strategy-return correlation ~0.934.

Interpretation: the two finalists mostly express the same medium/long-term trend factor. No ensemble is promoted now.

Important caveat from the 29-symbol subset: historical/non-survivor-only aggregate performance was weak:

- SMA120 CAGR ~-4.3%
- Donchian100/50 ~-1.3%
- 50/50 blend ~-1.4%

This is why the next test expands to the complete archive-defined universe.

## Full Binance archive-defined universe dataset

Manifest:

- 864 symbols
- 21,383 monthly 1d archives
- latest archive month 2026-08

Final combined daily dataset:

- file: `r002_binance_full_universe_daily.csv`
- state: `r002_binance_full_universe_state.json`
- 864 / 864 symbols
- 637,705 rows
- date range 2020-01-01 -> 2026-08-31
- duplicate symbol+timestamp: 0
- duplicate symbol+date: 0
- missing core OHLCV: 0
- negative volume: 0
- invalid OHLC: 0
- non-positive prices: 0

Four Chinese Unicode symbols initially failed because urllib/http.client attempted non-ASCII URL paths. They were repaired by percent-encoding the URL path and storing repair shards under ASCII-safe hash filenames while preserving original symbol names inside CSV.

Final state version: `unicode-repair-0.2`

Final repair result:

- combined symbols: 864
- missing: 0
- failed repair targets: 0

The four repaired instruments:

- 币安人生USDT — ~316 trading days, eligible under 200-day warmup
- 我踏马来了USDT — ~223 days, eligible
- 龙虾USDT — ~174 days, not eligible
- 牛来USDT — ~2 days, not eligible

Approximately 641 symbols are expected to reach 200 point-in-time observed trading days, but the backtest must determine eligibility dynamically rather than pre-filtering by final history length.

Data verdict: **FULL-UNIVERSE DATASET PASS**.

## Immediate next task

Implement and run one reproducible **wide-universe point-in-time finalist engine** on `r002_binance_full_universe_daily.csv`.

Use all 864 archive-defined symbols as input.

Cleaning / universe rules:

- trim dead post-delisting zero-volume tails after final positive-volume day;
- common 200-observed-trading-day warmup for both finalists;
- point-in-time eligibility only;
- do not use future lifetime, current survivor status, final months_count, future delisting, or later liquidity in eligibility;
- no manual exclusion of poor performers.

Finalists:

### SMA120

- long when close > SMA120;
- else cash.

### Donchian100/50

- long after close breaks above prior 100-day high;
- stay long until close falls below prior 50-day low;
- prior-data-only channels.

Timing:

- calculate signal at close t;
- apply exposure to return t+1.

Portfolio:

- equal sleeve across all currently eligible assets;
- inactive sleeves remain cash;
- no risk parity / vol weighting / market-cap weighting in the primary test.

Comparator:

- point-in-time passive equal-sleeve comparator using the same eligibility and disappearance assumptions.

Cost stress:

- 5 bps
- 10 bps baseline
- 25 bps
- 50 bps

Disappearance penalty stress on disappearing long sleeve:

- 0%
- 25% baseline
- 50%
- 100%

Required metrics:

- CAGR
- Max DD
- annualized vol
- Calmar
- ending multiple
- turnover
- average gross exposure
- worst year
- worst quarter
- worst month
- worst rolling 12-month return
- eligible asset count through time
- active long count through time
- cash fraction
- late-period metrics from 2023-01-01
- concentration diagnostic / P&L contribution by asset
- survivor vs non-survivor contribution as diagnostic attribution only, never as portfolio eligibility

Decision:

- each finalist gets PASS / FAIL / REDESIGN;
- do not rescue a failure by adding new indicators or retuning parameters on the same sample.

## GitHub documents to use

Primary current roadmap:

`docs/research/r002-near-term-research-roadmap-v2.0.md`

Full-universe protocol:

`docs/research/r002-full-universe-validation-protocol-v0.1.md`

Previous roadmap retained for history:

`docs/research/r002-near-term-research-roadmap-v1.0.md`

## Key GitHub code / report commits from this phase

- full-universe manifest downloader v0.2: `0d41ae8523fb339a8444035ce5f146524acefa25`
- historical subset downloader: `9268a8396dc8404c08f8d7681684eb9d93dfa3ac`
- historical subset validation: `e05f51fd7988690b59052c77b102cfa19170b2b9`
- point-in-time portfolio: `c28e9bd0bcb1747cc369666e065a8ff248da7286`
- vol targeting: `48fe1bb9d755a666332dd54d7338b021b0dccd50`
- Donchian breakout: `e567c72f62d0bad302df6c29669f51a7dd69e052`
- candidate tournament: `b7d58647eb09be42ba42d8e599e7e233d7fdecac`
- finalist robustness/ensemble: `57e8303918a90578f6dac0211e3b6bdf1e583e80`
- full-universe downloader: `1a65b3729109427ffd3b9951986db073f2f0a648`
- full-universe protocol: `957615edb0d8e8db233a903a469e5ed50ee71b22`
- Unicode repair script: `e68f8105a13c6f8b99fab77c2ecea602a3173bd0`
- current roadmap v2.0: see latest commit on that file.
