# SC001 — C7-C10 No-Alpha Data / Structural Feasibility Audit v0.1

Date: 2026-09-18  
Status: **NO-ALPHA FEASIBILITY AUDIT — NO CANDIDATE RETURN OR PNL AUTHORIZED**  
Parent roadmap: `docs/research/sc001-current-roadmap-and-stop-rules-v4.31.md`

## 1. Purpose

Evaluate C7-C10 only on:

- free/public historical data availability;
- local SC001 data already qualified;
- timestamp/causality feasibility;
- likely data volume and engineering burden;
- structural fill/cost architecture;
- distinction from terminal C1-C6;
- relevant reusable building blocks;
- cheapest falsification path.

No strategy return, candidate PnL, parameter optimization or protected-data access is authorized by this audit.

## 2. Current external source facts

As of 2026-09-18:

### OKX

Official historical-data service advertises:

- tick trade history from September 2021 onward;
- candlestick history from July 2023 onward;
- perpetual funding history from March 2022 onward;
- high-resolution L2 order-book history from March 2023 onward;
- borrowing-rate history from December 2021 onward.

The OKX API also exposes funding-rate history, index candles and mark-price candle functionality.

This makes OKX structurally capable of supporting C7, C9 and C10 without paid data.

### Bybit

Official developer material advertises downloadable historical public market data including:

- orderbook;
- k-line;
- trades;
- funding rates.

The public V5 API also exposes historical funding-rate queries.

This makes Bybit a plausible second venue for C8 without paid data.

### Binance

Official Binance public-data archive provides downloadable daily/monthly market data for all supported symbols, including trades, aggregate trades and klines with checksums.

Futures APIs also expose funding-rate history and index/mark-price market-data endpoints.

Binance therefore remains another free source for cross-venue or derivative-state source verification, subject to SC001 independence/data-role rules.

## 3. Local SC001 data state relevant to next slate

Existing SC001 evidence already confirms qualified OKX 400-level L2 for BTC-USDT-SWAP across prior Q009A/Q009B / E008 research dates.

Important limitation:

- retained/replay-qualified local L2 evidence is BTC-centric;
- C7 requires a prospectively spread/fee-eligible **non-BTC or multi-asset universe**, so new multi-asset L2 acquisition is likely;
- C10 can potentially use already-contaminated BTC L2 for a cheap book-state structural sentinel, but only after an explicit contamination-role update.

C1-C6 July/September trade data and C1 SPOT data remain available as contaminated Selection/Calibration sources, but may not be repurposed into parameter-neighbor rescues.

## 4. C7 feasibility card — spread-qualified passive/hybrid maker universe

### Scientific distinction

C7 is valid only if it is not E008 BTC same-rule rescue.

Core mechanism:

- P6 visible liquidity/spread state;
- M2 liquidity provision;
- T2/T4 passive or hybrid execution.

### Relevant reusable blocks

Core prior evidence:

- F006 visible spread/liquidity state;
- F008 queue-ahead uncertainty.

Do **not** include RB005 aggressive-flow exhaustion by default. It could only become a later incremental execution/veto question after a C7 base mechanism survives.

### Data feasibility

**HIGH externally / LOW-MEDIUM locally.**

OKX provides public L2 history from March 2023 onward, but local qualified L2 is mainly BTC. Multi-asset C7 requires new acquisition.

### Data burden

**HIGH.**

Prior BTC 400-level files were hundreds of MB per day. A multi-asset multi-day universe can quickly reach many GB.

Therefore C7 must use a staged data plan:

1. non-PnL universe eligibility from listing/turnover/trade activity;
2. L2 metadata/HEAD size audit;
3. very small contaminated-date spread/headroom pilot;
4. only then broader L2 acquisition.

### Structural execution burden

Potential cycle architectures:

- maker entry + maker exit: 2 passive fills;
- maker entry + taker fail-safe exit: mixed T4;
- inventory-neutral two-sided quoting: path-dependent multiple fills.

Historical exact maker/taker fee treatment and adverse-selection reserve must be frozen before any economic sentinel.

### Cheapest kill test

**Spread/headroom sentinel only.**

Measure prospectively selected markets for:

- quoted spread distribution;
- spread persistence;
- top-of-book size;
- stale-book fraction;
- proportion of time spread exceeds a predeclared structural reserve.

No fill model, queue model or PnL.

### Feasibility disposition

`FEASIBLE_BUT_DATA_HEAVY`

Do not lead the next batch unless cheaper candidates fail structural audit.

## 5. C8 feasibility card — cross-venue same-asset dislocation / transfer

### Scientific distinction

C8 is not C4.

C4 was same-venue BTC/ETH -> alt transfer. C8 uses the **same asset across independent venues**, so the information source and execution relationship are materially different.

### Core primitives

- P8 cross-venue relative value;
- P9 information transfer if directional lag is chosen;
- R6 venue-relative reference/residual.

### Relevant reusable blocks

- RB008 causal reference-price semantics;
- RB004 residualization principle as a methodological warning: do not confuse common market movement with a venue-specific lead effect.

RB003 same-venue BTC/ETH leader impulse is not automatically part of C8.

### Free-data feasibility

**HIGH.**

At least OKX and Bybit currently expose free historical trades and order-book data. Binance also has extensive free public trade/aggTrade archives.

### Local-data feasibility

**LOW.**

No qualified SC001 cross-venue synchronized same-asset dataset is currently frozen for this role.

### Timestamp / causality risk

**MEDIUM-HIGH.**

Mandatory audit:

- exchange timestamp meaning;
- ms/us scale;
- event time vs publication/receive semantics where available;
- clock granularity;
- duplicate/out-of-order handling;
- cross-venue alignment tolerance.

A cross-venue lead claim is invalid if timestamp uncertainty is of the same order as the proposed lag.

### Structural execution fork

Before any outcome, C8 must split conceptually:

- **C8A directional lag capture** — two fills, directional exposure;
- **C8B paired cross-venue convergence** — four fills, legging/collateral/venue risk.

These cannot share one economic hurdle.

No outcome may be used to choose between C8A and C8B.

### Cheapest kill test

First stage:

1. freeze one venue pair and one asset universe using non-PnL liquidity/listing criteria;
2. metadata + timestamp-semantics audit;
3. raw same-time venue-price/dislocation distribution;
4. estimate frequency above the appropriate two-fill or four-fill structural hurdle.

No optimized lag grid and no PnL.

### Feasibility disposition

`HIGH_INFORMATION_VALUE / MODERATE_ENGINEERING`

Strong candidate for the next structural audit.

## 6. C9 feasibility card — scheduled funding / mark-index state transition

### Scientific distinction

C9 is not C1.

C1 required a rare +50 bps spot/perp dislocation. C9 is organized around **scheduled funding mechanics and derivative-state variables**.

### Core primitives

- P8 funding / mark / index / basis state;
- P11 scheduled funding-time context;
- possible P10 scheduled-event state.

### Relevant reusable blocks

- RB007 continuous spot/perp basis state;
- RB008 causal reference;
- legacy funding/mark implementation knowledge from prior project data, used only as source/engineering evidence unless explicitly re-governed.

### Free-data feasibility

**VERY HIGH.**

OKX publishes historical funding data from March 2022 onward and supports mark/index market-data endpoints/candles. Binance and Bybit also expose historical funding-rate data.

### Local-data feasibility

**MEDIUM.**

The project already contains historical BTC funding/mark work, but independent branch firewalls mean C9 should either:

- reacquire public source data into a dedicated SC001 workspace; or
- explicitly reclassify a copied source dataset under a new SC001 contamination/data-role record.

Do not use outcomes from independent R003/R009 branches as C9 calibration.

### Data burden

**LOW-MEDIUM.**

Funding observations are sparse scheduled events, and mark/index candles are much smaller than full L2.

### Structural execution burden

Must be frozen before any alpha sentinel:

- directional post-funding response: 2 fills;
- hedged spot/perp funding/basis mechanism: 4 fills plus funding/legging;
- state/risk-only use: no standalone trade yet.

### Cheapest kill test

No-alpha scheduled-state audit:

- exact funding timestamps and interval changes;
- event count and cross-asset breadth;
- funding/mark/index/basis state distributions before/after scheduled events;
- unconditional state-transition magnitude distribution;
- compare magnitude to predeclared fill-count structural hurdle.

No funding threshold, event window or sign may be selected from PnL.

### Feasibility disposition

`HIGHEST_DATA_FEASIBILITY / LOWEST_ENGINEERING_COST`

Best candidate to audit first structurally, without implying highest expected profitability.

## 7. C10 feasibility card — L2 liquidity-vacuum / replenishment event

### Scientific distinction

C10 is not C5 + L2.

Core trigger must originate from P6/P10 book-state primitives, for example:

- spread shock;
- near-touch depth collapse;
- one-sided depth vacuum;
- replenishment failure;
- abrupt book slope/microprice discontinuity.

C5 aggressive-flow event labels are excluded from the C10 base definition.

### Relevant reusable blocks

Core:

- P6 order-book/liquidity features;
- F008 queue/model uncertainty as execution caution.

RB005 extreme aggressive-flow state is **not core**. It may only become a later BASE + RB005 incremental test if an independently defined C10 base survives.

### Data feasibility

**HIGH.**

OKX public historical L2 is available from March 2023 onward.

### Local-data feasibility

**MEDIUM-HIGH for BTC pilot.**

Existing Q009A/Q009B/E008 BTC L2 can potentially support a cheap nonpromotional structural event-frequency pilot after explicit contamination-registry authorization.

Multi-asset breadth would require new L2 acquisition.

### Data burden

**HIGH**, but a BTC-only structural pilot can be cheap because data already exist locally.

### Structural execution burden

Depends on mechanism:

- directional response: 2 fills;
- hybrid liquidity provision/reaction: execution-model heavy;
- no execution architecture should be chosen after viewing move outcomes.

### Cheapest kill test

On explicitly re-governed contaminated BTC L2:

- define one objective liquidity-vacuum event family from book state only;
- count event frequency;
- report unconditional next-horizon absolute move distribution and direction symmetry;
- no strategy side optimization;
- no fill model;
- no C5 conditioning.

If event frequency or raw move magnitude is structurally inadequate, kill before multi-asset L2 acquisition.

### Feasibility disposition

`FEASIBLE_WITH_EXISTING_BTC_PILOT / HIGH_COMPLEXITY_AFTER_PILOT`

## 8. Comparative structural audit

| Candidate | Free source availability | Local readiness | Data burden | Engineering burden | First cheap question |
|---|---|---|---|---|---|
| C7 | High | Low-Medium | High | High | Is spread structurally large enough before queue modeling? |
| C8 | High | Low | Medium | Medium-High | Are cross-venue clocks clean and dislocations large/frequent enough? |
| C9 | Very High | Medium | Low-Medium | Low-Medium | Are scheduled derivative-state transitions large/frequent enough? |
| C10 | High | Medium-High BTC pilot | High after pilot | High | Do book-vacuum events exist with enough raw move headroom? |

## 9. Recommended audit order

This is an **engineering/information-efficiency order**, not a profitability ranking:

1. **C9** — cheapest and cleanest data audit;
2. **C8** — high orthogonality and free cross-venue data, moderate synchronization work;
3. **C10** — exploit existing BTC L2 for a cheap structural pilot before new downloads;
4. **C7** — defer large multi-asset L2 acquisition until spread/headroom metadata justify it.

## 10. Building-block governance

No RB block is automatically inserted into C7-C10.

Initial core stacks should remain minimal:

- C7: P6 spread/liquidity only;
- C8: P8/P9 venue-relative state + causal venue reference;
- C9: P8/P11 funding/mark/index state + RB007/RB008 as reference/context;
- C10: P6/P10 book-state only.

Potential auxiliary uses such as RB005 execution veto or RB003 leader context must be separately pre-registered as incremental tests after a base mechanism survives.

## 11. Immediate next action

Freeze **data-only feasibility cards and acquisition/preflight scope** for C9 first, while in parallel specifying the C8 venue/timestamp audit.

No candidate alpha, return, PnL or protected data should be opened yet.
