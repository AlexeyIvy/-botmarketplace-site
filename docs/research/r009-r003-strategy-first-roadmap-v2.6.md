# BotMarketplace Strategy-First Research Roadmap v2.6

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** R009 BTC forward initialized; Binance R003 forward initialized with causality hotfix pending retry; parallel Bybit R003 forward frozen; platform development frozen

## 1. Active forward records

### R009-E002 — BTC

- technically accepted initialization;
- fixed inception remains 2026-09-10 00:00 UTC;
- no parameter changes;
- forward evidence accumulates only from fully closed daily bars.

### R003-E003 — Binance

- original fixed decision boundary remains 2026-09-10 12:00 UTC;
- initial establishment was technically accepted;
- a pre-first-funding causality fix was frozen before any funding event entered the record;
- Binance HTTP 418 is treated as temporary source/access failure, not as permission to move inception or change venue inside E003;
- retry later using the causality-safe launcher without resetting the record.

### R003-X003 — Bybit parallel venue replication

New prospective forward branch, frozen before Bybit X003 forward P&L:

- protocol: `docs/research/r003-x003-bybit-forward-venue-replication-protocol-v0.1.md`;
- protocol commit: `7ba9bf6ca43e4d4936fbca9085f9adfea0a9f116`;
- engine: `research/r003/r003_x003_bybit_forward_venue_replication.py`;
- engine commit: `2ef343190a672a2099654ec91da88c4bef201b9f`;
- mobile launcher: `research/r003/r003_x003_bybit_forward_venue_replication_mobile.py`;
- launcher commit: `7b92db3b86bb64620b79bc5b8b26c0157439a15c`;
- fixed decision boundary: **2026-09-10 16:00 UTC**.

X003 uses Bybit public V5 spot, linear perpetual, mark-price and realized-funding data with the same 50/50 equal-BTC fully funded carry concept, same abstract 5/10/25 bps cost grid, same month-end rebalance rule and same Treasury opportunity-cost references.

X003 is not a rescue of Bybit X001 MIXED and does not authorize historical X002.

## 2. Why parallel Bybit forward is allowed

The goal is operational and economic venue replication, not winner selection.

Binance E003 remains canonical and must continue when source access is available. Bybit X003 runs beside it so future evidence can reveal whether carry behavior is portable across venues without mixing the two datasets or silently changing the original experiment.

If Binance and Bybit disagree materially, preserve both results; do not choose the prettier venue retrospectively.

## 3. R009 implementation branch

After forward plumbing remains technically stable, proceed with the already frozen R009-G001 mechanical capital-granularity snapshot, then freeze/run G002 pathwise discrete replay.

Do not use G001/G002 to retune R009 profitability.

## 4. R010 hypothesis

R010 drawdown-armed recovery remains hypothesis-only. Do not backtest or forward-launch it until the current forward/granularity sequence is completed enough to avoid research sprawl.

## 5. Immediate execution order

1. Start/initialize R003-X003 Bybit forward after its first eligible fully closed hourly bars are available.
2. Retry Binance R003-E003 causality-safe launcher only after Binance rate-limit/IP ban clears; never reset inception.
3. Continue R009-E002 unchanged.
4. Run R009-G001 after current forward technical gates are clean enough.
5. Freeze/run R009-G002.
6. Continue all forward records independently.
7. Open Safe-Sleeve S002 before demo/real-capital promotion.
8. Minimal demo only after capital granularity and forward plumbing are understood.
9. Broad platform development remains frozen.

## 6. Explicit prohibitions

Do not:

- replace Binance E003 with Bybit inside the same record;
- merge Binance and Bybit P&L into one forward history;
- move either fixed inception because of delayed first run;
- use Bybit X003 to erase the earlier Bybit X001 MIXED result;
- open Bybit historical X002 as a rescue;
- add leverage or funding thresholds;
- select whichever venue looks better after the fact;
- restart broad BotMarketplace platform development.
