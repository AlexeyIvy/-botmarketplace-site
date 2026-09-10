# R009-X002 Cross-Asset Breadth — Implementation Freeze v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** frozen before panel result inspection  
**Protocol:** `docs/research/r009-x002-cross-asset-breadth-panel-protocol-v0.1.md`  
**Frozen engine commit:** `9e5c28428ba62bdae8eda80db364fa6c65b3d34c`  
**Frozen Android launcher commit:** `150aa00687bbc74d1a5c303d7d2cfb7cfb4e0255`

## 1. Fixed panel

Exactly: BNBUSDT, LTCUSDT, XRPUSDT, ADAUSDT, SOLUSDT.

The selection reuses the earlier R002 major-asset subset excluding BTC and ETH; no coin may be added or removed after inspection.

## 2. Fixed mechanics

- Binance Spot daily klines;
- fully closed bars before persisted first-run cutoff;
- SMA120 trend sleeve 0/10%;
- crisis sleeve 0-10% with 2.5pp tranches at -20/-35/-50/-65%;
- sticky until strictly new ATH;
- additive combined target;
- self-financing daily-target accounting;
- 5/10/25/50 bps fee grid;
- cash yield 0;
- no leverage/funding/staking/lending.

## 3. Resume semantics

One local workspace `R009_X002_BREADTH` stores:

- `snapshot.json` with immutable first-run cutoff;
- page-level cache per symbol;
- result files.

Restart must reuse the same cutoff and already downloaded pages.

## 4. Decision semantics

Per-asset SUPPORT/MIXED/FAIL follows the frozen ETH X001 logic.

Panel verdict:

- `CROSS_ASSET_BREADTH_SUPPORT`: at least 4 SUPPORT and 0 FAIL;
- `CROSS_ASSET_BREADTH_REJECTED`: at least 3 FAIL;
- otherwise `CROSS_ASSET_BREADTH_MIXED`;
- any source-gate failure -> `DATA_REDESIGN`.

## 5. Evidence limitation

Because this panel was opened after seeing the ETH MIXED result, it is explicitly labeled a **post-ETH fixed breadth diagnostic**, not clean independent confirmatory evidence.

No best-performing coin may be selected as a replacement candidate from the panel.
