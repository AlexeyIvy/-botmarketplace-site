# SC001 — B13-C Explicit Liquidation-Flow Source / Data Feasibility Audit v0.1

Date: 2026-09-19
Status: **HISTORICAL DEFER / PROSPECTIVE FREE COLLECTION FEASIBLE**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.94.md`;
- `docs/research/sc001-post-c11-independent-base-opportunity-pool-v0.1.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Research question

Can B13-C study an economically explicit forced-liquidation mechanism using a free, qualified, historically adequate event source rather than reconstructing "liquidation-like" events from ordinary trade flow?

## 2. Required source semantics

A qualifying source must expose actual platform liquidation events with at minimum:

- event timestamp;
- symbol;
- liquidated-position side or unambiguous forced-order side semantics;
- size/quantity;
- price/bankruptcy price or equivalent event price field;
- venue identity.

Generic aggressive trades are not a substitute.

## 3. OKX

Official OKX changelog states that platform historical liquidation orders were no longer retrievable through the REST endpoint by the end of April 2023 and directs users to the live Liquidation Orders WebSocket channel instead.

OKX current Historical Market Data download categories expose:

- trades;
- candles;
- funding;
- order book;
- borrowing rate;

but not a public long-history liquidation-order archive.

Disposition:

`NO_QUALIFIED_FREE_LONG_HISTORICAL_PUBLIC_LIQUIDATION_ARCHIVE`

Current/live liquidation monitoring remains possible prospectively.

## 4. Bybit

Official Bybit V5 exposes:

`allLiquidation.{symbol}`

on the public linear/inverse WebSocket.

The documentation states:

- pushes all liquidations occurring on Bybit;
- 500 ms push frequency;
- event fields include timestamp, symbol, position side, executed size and bankruptcy price;
- `S=Buy` means a long position was liquidated;
- `S=Sell` means a short position was liquidated.

The all-liquidation topic was introduced in February 2025.

Bybit separately exposes downloadable historical public trades, but no equivalent official long-history liquidation-event archive was identified in the current V5/public archive documentation.

Disposition:

`PROSPECTIVE_EXPLICIT_LIQUIDATION_COLLECTION_FEASIBLE`

`HISTORICAL_EXPLICIT_EVENT_BACKTEST_NOT_QUALIFIED`

## 5. Binance

Binance historically exposed public market liquidation REST endpoints, but the official changelog records that:

- public market `allForceOrders` REST stopped being maintained/accepting requests in April 2021;
- liquidation WebSocket streams continued as snapshots;
- the current forceOrders REST family is user/account liquidation history, not public whole-market history;
- current forceOrders query retention is limited to the recent period.

Therefore Binance does not supply the required long, free, public event-level liquidation history for B13-C.

Disposition:

`NO_QUALIFIED_FREE_LONG_HISTORICAL_PUBLIC_MARKET_LIQUIDATION_ARCHIVE`

## 6. Third-party data

CoinGlass currently documents:

- historical liquidation aggregates by pair/coin;
- plan/API-key access;
- granularity restrictions on lower plans;
- a liquidation-order endpoint covering only the past 7 days and requiring higher API plans.

These sources may be useful for independent validation later, but they do not satisfy the current project preference for free official long-history event-level data.

No paid source is adopted by this audit.

## 7. Historical B13-C disposition

Exact source/data state:

`B13C_DEFER_HISTORICAL_DATA_FEASIBILITY`

Reason:

`NO_FREE_QUALIFIED_LONG_EVENT_LEVEL_EXPLICIT_LIQUIDATION_HISTORY`

This is not:

- an economic reject;
- an alpha reject;
- evidence that liquidation cascades lack information.

It is a data-source limitation.

## 8. Forbidden workaround

Do not create a historical B13-C by:

- labeling generic aggressive trades as liquidation events;
- thresholding volume/return and calling the result liquidations;
- using C5/C10 tail events as implied liquidations;
- mining news reports of famous liquidation days;
- silently substituting aggregated liquidation bars for explicit event-level flow.

Any such design would be a different candidate/mechanism.

## 9. Prospective free-data path

The preferred free path is:

`BYBIT_ALL_LIQUIDATION_PROSPECTIVE_RAW_COLLECTION`

Initial frozen symbol universe should reuse the existing pre-outcome 12-symbol SC001 universe where an active Bybit LinearPerpetual exists:

BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI.

No symbol substitution based on observed liquidation activity.

## 10. Prospective evidence role

Raw collection begins before any B13-C feature threshold/horizon/direction rule is selected.

Classification:

`PROTECTED_PROSPECTIVE_RAW_LIQUIDATION_STREAM`

During collection, allowed diagnostics are source/quality only:

- connection uptime;
- reconnect/gap ledger;
- subscription status;
- schema validity;
- raw event count only for data sufficiency.

Forbidden during protected collection:

- post-liquidation return;
- continuation/reversal;
- threshold search;
- best-symbol ranking;
- PnL;
- event-window optimization.

## 11. Parallel-work consequence

Because prospective liquidation data must accumulate over time, SC001 does not need to stop all research while waiting.

After the collector is frozen and started, independent non-B13-C design work may continue in parallel without consuming the protected liquidation outcomes.

## 12. Immediate next action

Freeze a Bybit all-liquidation prospective raw collection protocol and implementation.

No B13-C alpha/sentinel runner is authorized yet.
