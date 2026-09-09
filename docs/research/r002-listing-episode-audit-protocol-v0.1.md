# R002 Listing-Episode Audit Protocol v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Purpose:** identify delist/relist and ticker-reuse episodes before any corrected wide-universe rerun.  
**No strategy P&L is calculated in this audit.**

## Why this audit is required

Current Binance `exchangeInfo.onboardDate` is not necessarily the first-ever historical availability date for a symbol. A symbol can be delisted and later relisted, and the same symbol string can even be reused for a different underlying asset.

Therefore historical daily rows must be segmented into separate listing episodes before a strict point-in-time backtest can safely carry history, eligibility, or signal state.

## Frozen episode rule for this audit

A new listing episode is flagged when two adjacent observed daily rows for the same symbol are separated by **more than 7 calendar days**.

Reason:

- Binance USD-M perpetual contracts are intended to trade continuously;
- a gap longer than one full week is treated conservatively as evidence that the instrument was not continuously available;
- the threshold is frozen before any corrected strategy P&L is viewed;
- this is a data-identity rule, not a strategy parameter.

Rows after the final positive-volume day remain trimmed as in the prior research protocol.

## Required outputs

For every symbol and episode:

- symbol;
- episode number;
- episode start/end;
- observed bars;
- positive-volume bars;
- gap from prior episode;
- whether the episode independently reaches 200 observed bars;
- episode-specific 200-bar eligibility date.

Also report:

- number of symbols with multiple episodes;
- number of total episodes;
- distribution of long gap lengths;
- number of symbols whose naive symbol-level eligibility differs from episode-aware eligibility;
- examples of the largest gaps.

## Decision gate

If multiple listing episodes are nontrivial, the wide-universe engine must be versioned and rerun with:

- history reset at episode start;
- 200-bar warmup reset at episode start;
- SMA and Donchian rolling history reset at episode start;
- signal state reset at episode start;
- disappearance treatment applied at episode end;
- no parameter changes to SMA120 or Donchian 100/50.

If the audit shows no material multi-episode problem, the previous REDESIGN verdict stands without rerun.
