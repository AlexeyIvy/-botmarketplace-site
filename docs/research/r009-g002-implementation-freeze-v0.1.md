# R009-G002 — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** frozen before G002 result inspection

## Protocol

`docs/research/r009-g002-pathwise-discrete-replay-protocol-v0.1.md`

Protocol commit:

`cde4d52e071b623588ce3583901aea25cff1f13e`

## Frozen engine

`research/r009/r009_g002_pathwise_discrete_replay.py`

Engine commit:

`ea713a8899673733692659a44ce397b96cd3d4c5`

## Frozen Android launcher

`research/r009/r009_g002_pathwise_discrete_replay_mobile.py`

Launcher commit:

`835638b5d844c3f72dca42545604bc954914b680`

## Frozen implementation semantics

- exact R009 SMA120 + TREND10 + CRISIS10 additive target path;
- crisis triggers -20/-35/-50/-65%;
- sticky crisis reset only at new closing ATH;
- Binance Spot BTCUSDT fully closed daily bars;
- primary implementation replay begins 2018-01-01 after 2017 warmup;
- G001 frozen execution rules: 0.00001 BTC step, 0.00001 BTC minQty, 5 USDT minNotional;
- account tiers: 200, 250, 500, 1,000, 5,000, 10,000 USD;
- fees: 5/10/25/50 bps;
- desired BTC quantity rounded down;
- order skipped if delta quantity/notional is below the frozen minimums;
- no batching/tolerance/cooldown/alternate venue;
- target=0 with sub-minimum BTC residual remains as dust;
- continuous R009 accounting tracked only as implementation-fidelity reference.

G002 is implementation research only. It cannot create strategy-performance PASS and cannot select a capital tier by whichever historical P&L looks best.
