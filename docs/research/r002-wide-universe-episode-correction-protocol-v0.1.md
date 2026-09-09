# R002 Wide-Universe Episode-Corrected Rerun Protocol v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** pre-result correction freeze  
**Purpose:** rerun the exact frozen wide-universe finalist test after correcting listing-episode identity only.

## 1. Why a rerun is required

The listing-episode audit found 3 symbols with a >7-calendar-day gap between observed daily bars:

- BNXUSDT;
- ICPUSDT;
- TLMUSDT.

The original engine carried rolling state across these gaps. The corrected rerun must treat every gap >7 calendar days as a new listing episode.

This is a data-identity correction, not a strategy modification.

## 2. Frozen episode rule

For each base symbol, sort observed daily rows by date.

If the gap between two consecutive observed rows is:

- **<= 7 calendar days:** keep the same episode;
- **> 7 calendar days:** start a new episode.

Every episode is treated as an independent instrument identity for the backtest.

At the start of every new episode reset:

- observed-bar count;
- common 200-bar eligibility clock;
- SMA120 history;
- Donchian 100/50 rolling channels;
- Donchian long/cash state;
- target portfolio weight.

The prior episode disappears without advance knowledge and is subject to the same pre-specified disappearance stress grid.

## 3. Expected transformed-data invariants

Starting dataset remains:

- 864 base symbols;
- 637,705 rows;
- 2020-01-01 -> 2026-08-31.

Frozen episode audit implies:

- 867 episode identities;
- exactly 3 long-gap events;
- BNXUSDT: second episode starts 2023-02-22;
- ICPUSDT: second episode starts 2022-09-27;
- TLMUSDT: second episode starts 2023-03-30.

The corrected launcher must assert these facts before P&L is calculated.

## 4. Strategy rules remain unchanged

### SMA120

`close > SMA120 -> long, else cash`

### Donchian 100/50

- entry above prior 100-observed-bar high;
- exit below prior 50-observed-bar low;
- current bar excluded from channels.

Timing remains:

- signal formed at close t;
- applied to the next portfolio return.

## 5. Portfolio and stress rules remain unchanged

- common 200 observed-bar warmup per episode;
- equal sleeve across all currently eligible episode identities;
- inactive sleeves remain cash;
- PTI passive comparator under identical eligibility;
- transaction costs: 5 / 10 / 25 / 50 bps;
- disappearance penalties: 0 / 25 / 50 / 100%;
- baseline: 10 bps + 25% disappearance penalty;
- late-period slice from 2023-01-01;
- no leverage;
- cash return = 0.

## 6. Explicit prohibitions

Do not in this rerun:

- change SMA length;
- change Donchian windows;
- add indicators;
- use `exchangeInfo.underlyingType` as a filter;
- remove TradFi or any other category;
- remove the three multi-episode symbols;
- use current `onboardDate` to erase earlier valid listing episodes;
- optimize weights;
- change cost or disappearance assumptions.

## 7. Decision rule

Compare corrected outputs with the original wide-universe run.

If the corrected run remains economically weak post-2023, the prior **REDESIGN / NOT PASS** conclusion becomes final for naive equal-sleeve broad-universe deployment.

If the correction materially changes the conclusion, document the exact change and reassess using the original pre-specified PASS criteria only. No additional rescue filters are allowed.
