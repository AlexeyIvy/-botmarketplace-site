# R002 Availability & Domain Metadata Audit — Results v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** metadata audit complete; no strategy P&L calculated  

## 1. Audit completion

The metadata-only audit completed successfully on the full archive-defined dataset.

- archive symbols: **864**;
- current Binance USD-M `exchangeInfo` symbols: **897**;
- matched archive symbols: **833**;
- unmatched archive symbols: **31**;
- matched symbols whose archive history begins before the current `onboardDate`: **11**;
- matched symbols whose naive 200-bar eligibility date would move later if current `onboardDate` were treated as first availability: **11**;
- median apparent eligibility shift among those 11: **622 days**;
- maximum apparent shift: **1769 days**.

## 2. Correction of the XAU hypothesis

The previous suspicion that `XAUUSDT` contained pre-launch archive bars was incorrect.

Audit result:

- archive first date: **2025-12-11**;
- current official `onboardDate`: **2025-12-11**;
- pre-onboard rows: **0**;
- eligibility shift: **0**.

Therefore XAU is not evidence of a backfill bug.

## 3. What the 11 apparent mismatches actually imply

The current `exchangeInfo.onboardDate` cannot be interpreted automatically as the first-ever historical availability date for a symbol.

At least some of the 11 apparent mismatches are explained by **delist/relist or ticker reuse** rather than false archive history.

Example: `CVCUSDT` had an earlier perpetual-contract episode that Binance later delisted in November 2022, and Binance launched a new `CVCUSDT` perpetual contract again in May 2025. Therefore the current `onboardDate` describes the latest listing episode, while older archive bars can still be genuine historical trading data.

More importantly, ticker reuse can join economically different assets under the same symbol string. `LIT` originally referred to **Litentry**; Binance later removed that LIT contract during the Litentry-to-HEI transition, while a new `LITUSDT` contract launched in December 2025 for **Lighter Protocol**. Treating all `LITUSDT` rows as one continuous instrument is therefore invalid.

## 4. Consequence for the original wide-universe engine

The original engine keyed history only by `symbol`. If a symbol disappears for a long period and later returns, the engine can carry prior observed-bar history, eligibility, and potentially signal state across the gap.

That is a genuine point-in-time identity/availability problem for relisted or reused symbols.

However, the 11 current-`onboardDate` mismatches alone are not sufficient to quantify the problem because:

- current `exchangeInfo` does not provide all historical listing episodes;
- 31 archive symbols are absent from the current snapshot;
- some symbols can have multiple legitimate historical episodes;
- ticker reuse can represent a different underlying asset.

Therefore the correct next step is **listing-episode segmentation from the archive timeline itself**, not simply dropping all pre-current-onboard rows.

## 5. Decision

The wide-universe verdict remains **provisional REDESIGN / NOT PASS** until the listing-episode issue is resolved.

Do not retune SMA120 or Donchian 100/50.

Next step:

1. run a metadata-only listing-episode audit on all 864 archive symbols;
2. identify long discontinuities objectively;
3. freeze an episode-segmentation rule before any strategy rerun;
4. if multi-episode symbols are material, rerun the exact frozen strategy protocol with history/warmup reset at each new episode.
