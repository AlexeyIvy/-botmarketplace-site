# R003-X003 — Bybit Forward Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Protocol:** `docs/research/r003-x003-bybit-forward-venue-replication-protocol-v0.1.md`  
**Status:** frozen before any Bybit X003 forward P&L

## Frozen protocol commit

`7ba9bf6ca43e4d4936fbca9085f9adfea0a9f116`

## Frozen engine

`research/r003/r003_x003_bybit_forward_venue_replication.py`

Exact engine commit:

`2ef343190a672a2099654ec91da88c4bef201b9f`

## Frozen Android launcher

`research/r003/r003_x003_bybit_forward_venue_replication_mobile.py`

Exact launcher commit:

`7b92db3b86bb64620b79bc5b8b26c0157439a15c`

## Fixed forward boundary

`2026-09-10 16:00:00 UTC`

Initial establishment is at the close of the first fully closed common Bybit hourly bar whose open time is >= this boundary. The boundary may never move forward on reruns.

## Frozen economic semantics

- Bybit BTCUSDT spot + Bybit linear BTCUSDT perpetual.
- 50% spot / 50% separate USDT futures-collateral bookkeeping.
- Equal BTC quantity long spot / short perpetual.
- No borrowing and no leverage optimization.
- Month-end UTC rebalance only.
- Positive Bybit funding is income to the short.
- Funding only after actual event timestamp and only after portfolio establishment.
- Funding event is booked to first closed hourly row ending at/after event time.
- Funding mark proxy is latest causally available hourly Bybit mark close at/before funding timestamp.
- 5/10/25 bps per-leg research cost tracks, 10 bps baseline.
- Same conservative margin proxy and 10% low-headroom diagnostic as Binance E003.
- Same fixed 3.90% Treasury and 5.90% compensation references plus causal dynamic 13-week Treasury proxy.
- REALIZED / ZERO / ADVERSE funding ablations unchanged in meaning.

## Source mechanics

Public Bybit V5 endpoints only:

- `/v5/market/kline` category spot, interval 60;
- `/v5/market/kline` category linear, interval 60;
- `/v5/market/mark-price-kline` category linear, interval 60;
- `/v5/market/funding/history` category linear;
- `/v5/market/instruments-info` category linear.

Only fully closed hourly bars are retained. Funding history uses actual timestamps; no fixed 8h cadence is assumed.

## Evidence-status restriction

X003 is a separate prospective venue replication. It does not:

- replace Binance R003-E003;
- convert Bybit X001 MIXED into PASS;
- authorize the prohibited Bybit historical X002 rescue;
- authorize demo/live trading;
- prove venue diversification or antifragility.

Any material implementation/economic change requires a new version and cannot overwrite this forward record.
