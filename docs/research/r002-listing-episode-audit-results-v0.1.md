# R002 Listing-Episode Audit Results v0.1

**Project:** BotMarketplace strategy research  
**Date:** 2026-09-09  
**Status:** metadata/data-identity audit complete; corrected rerun required  
**Research posture:** falsification-first; no signal retuning

## 1. Result

The frozen >7-calendar-day gap rule was applied to the full 864-symbol archive-defined dataset.

Observed result:

- archive symbols: **864**;
- total listing episodes: **867**;
- multi-episode symbols: **3**;
- long-gap events: **3**;
- total episodes independently reaching 200 observed bars: **644**;
- symbols whose **first** naive 200-bar eligibility date changes under episode segmentation: **0**.

The three multi-episode symbols are:

| Symbol | Episode 1 | Gap | Episode 2 | Episode-2 200-bar eligibility |
|---|---|---:|---|---|
| BNXUSDT | 2022-04-01 -> 2023-01-31 | 22 days | 2023-02-22 -> 2025-03-17 | 2023-09-09 |
| ICPUSDT | 2021-05-11 -> 2022-08-31 | 27 days | 2022-09-27 -> 2026-08-31 | 2023-04-14 |
| TLMUSDT | 2021-07-16 -> 2023-02-28 | 30 days | 2023-03-30 -> 2026-08-31 | 2023-10-15 |

## 2. Interpretation

This audit materially narrows the previously suspected data-identity problem.

There is **not** widespread multi-episode contamination across the 864-symbol universe. Only 3 symbols split under the pre-specified >7-day rule.

However, the original wide-universe engine treated these long gaps as internal missing-calendar gaps. As a result, when BNXUSDT, ICPUSDT and TLMUSDT reappeared, the engine could carry old rolling history and signal state into the new episode instead of resetting:

- common 200-bar warmup;
- SMA120 rolling history;
- Donchian 100/50 rolling channels and state;
- portfolio disappearance/re-entry mechanics.

The fact that each symbol's **first-ever** eligibility date is unchanged does not remove the bug. The required correction applies to the beginning of each later listing episode.

## 3. Preliminary materiality context

Using the original baseline contribution output, the three affected symbols together contributed approximately:

- SMA120 net wealth contribution: **+0.0739**, about **3.4%** of total baseline net P&L;
- Donchian 100/50 net wealth contribution: **+0.0175**, about **0.85%** of total baseline net P&L.

This suggests that the episode bug is probably not large enough to reverse the headline late-period weakness by itself. It is **not** a formal bound, because episode reset also changes portfolio denominators, transaction costs, disappearance events and subsequent target weights.

Therefore no conclusion is changed without a corrected rerun.

## 4. Decision

A corrected wide-universe rerun is required for methodological correctness.

The corrected rerun is a **bug-fix rerun only**:

- same frozen SMA120;
- same frozen Donchian 100/50;
- same point-in-time passive comparator;
- same 200 observed-bar warmup;
- same equal-sleeve construction;
- same 5/10/25/50 bps cost grid;
- same 0/25/50/100% disappearance grid;
- same post-2023 diagnostics;
- no universe filtering;
- no parameter changes;
- no use of current `exchangeInfo.onboardDate` to delete valid historical episodes.

Only listing-episode identity changes: a gap >7 calendar days starts a new episode and resets all history/state.

Until that rerun is complete, the prior broad-universe verdict remains **provisional REDESIGN / NOT PASS**.
