# R009-E002 — Forward Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Experiment:** R009-E002 forward paper  
**Date:** 2026-09-09  
**Protocol:** `docs/research/r009-e002-forward-paper-protocol-v0.1.md`

## Frozen engine

Path:

`research/r009/r009_e002_forward_paper.py`

Frozen engine commit:

`b82b5bb3cd71f6f3ba5efc796684e221c29917e7`

The mobile launcher must pin this exact engine commit.

## Frozen forward clock

- protocol/engine frozen before the 2026-09-09 UTC daily bar closed;
- 2026-09-09 fully closed bar determines the first target;
- formal inception: **2026-09-10 00:00:00 UTC**;
- first realized paper return is the next complete close-to-close interval;
- historical Binance bars are state warmup only and must not contribute pre-inception P&L.

## Frozen data source

- Binance Spot BTCUSDT;
- public market-data base: `https://data-api.binance.vision`;
- endpoint: `/api/v3/klines`;
- interval: `1d`;
- only fully closed UTC bars.

## Frozen strategy rules

- SMA120;
- TREND10 = 10% BTC when close > SMA120, else 0%;
- CRISIS10 = 4 x 2.5pp at -20/-35/-50/-65% closing drawdowns;
- crisis tranches sticky until new closing ATH;
- combined = TREND10 + CRISIS10;
- max desired BTC target 20%;
- no leverage/shorts/extra filters.

## Frozen accounting

- self-financing daily target;
- baseline cost 10 bps traded notional;
- shadows 5/25/50 bps;
- zero-yield paper USD cash;
- no pre-inception P&L.

## Persistent user-facing files

The tracker is intentionally kept below the 10-file convenience ceiling. It writes approximately seven files:

- `r009_e002_source_closed_bars.csv`
- `r009_e002_source_audit.json`
- `r009_e002_state_history.csv`
- `r009_e002_forward_daily.csv`
- `r009_e002_forward_metrics.csv`
- `r009_e002_forward_trades.csv`
- `r009_e002_forward_state.json`
- `r009_e002_forward_summary.md`

No parameter or inception change is allowed after the forward clock begins.