# R008 Near-Term Research Roadmap v1.2

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** R008 v0.1 REDESIGN; R008 v0.2/E003 frozen before results  
**Research posture:** antifragility-first, falsification-first, no hidden tuning

---

## 1. Current strategic decision

R008 remains the primary active antifragility branch.

R008 v0.1 is closed as **REDESIGN** after E002 independent long-history validation.

Canonical v0.1 result:

`docs/research/r008-e002-results-v0.1.md`

The retained evidence is narrow but useful:

- crisis deployment Benefit10 was positive in all closed events;
- crisis benefit increased materially with severity;
- the main failure was ATH-only release keeping added risk deployed for years;
- STATIC15 dominated v0.1 on the primary pre-2020 evidence slice;
- costs were not the failure mode.

R002 broad-universe trend rescue remains closed. BTC SMA120 frozen forward control continues independently. R001 tested option implementations remain paused/redesign.

---

## 2. New version — R008 v0.2

R008 v0.2 changes only one economic mechanism:

> extra crisis exposure is determined by the current drawdown and is released as the drawdown recovers through the same thresholds.

Unchanged:

- 10% permanent BTC base;
- 10% opportunity reserve;
- four 2.5 percentage-point tranches;
- thresholds -20/-35/-50/-65%;
- maximum 20% BTC;
- zero cash yield in architecture screen;
- no leverage/shorts;
- no SMA/Donchian/RSI/MACD/ADX/volatility filter.

Exact v0.2 mapping:

- DD > -20% -> 10%;
- -35% < DD <= -20% -> 12.5%;
- -50% < DD <= -35% -> 15%;
- -65% < DD <= -50% -> 17.5%;
- DD <= -65% -> 20%.

There is no sticky tranche memory, hysteresis or cooldown. Repeated threshold crossings are allowed and measured.

Protocol:

`docs/research/r008-v0.2-symmetric-recovery-protocol-v0.1.md`

Protocol freeze commit:

`81b380b80c98b7dcc3e58dc605ca48b15d42bfa6`

Implementation freeze:

`docs/research/r008-e003-implementation-freeze-v0.1.md`

Implementation-freeze commit:

`72221f41ca662d722afd2e6e3385cf2f9e0b50de`

Frozen engine commit:

`243fdf7e68ab150936b7fa461182c770a9a4e974`

Android launcher commit:

`1bd3a6d7f3dd1559104e0a4f31946886d4547f92`

---

## 3. Evidence-status rule for E003

E003 is intentionally a **redesign/mechanism screen**, not independent historical validation.

Reason: the 2013-2026 history was already inspected before the symmetric release rule was designed.

Therefore even a strong E003 result cannot receive HISTORICAL PASS.

Maximum positive status:

**PROMISING / ADVANCE TO FORWARD OR NEW-INDEPENDENT VALIDATION.**

No result on the already-inspected history may be relabeled OOS merely because a different data source or reporting slice is used.

---

## 4. E003 required comparisons

Same Blockchain.com daily reference source and same main slices:

- FULL_AVAILABLE;
- PRIMARY_LONG from 2013;
- PRE_2020_NEW retained as a label for comparability only;
- REPLAY_2020;
- POST_2023.

Mandatory strategies:

- R008_V02 symmetric recovery;
- R008_V01 sticky-until-ATH comparator;
- CASH;
- STATIC10;
- STATIC15;
- STATIC20;
- BTC100 contextual.

Fee grid remains 5/10/25/50 bps.

---

## 5. What E003 must prove to advance

The frozen protocol requires broadly all of the following:

1. v0.2 beats STATIC10 on geometric growth in both pre-2020 and post-2020 regimes;
2. STATIC15 does not Pareto-dominate v0.2 on PRE_2020_NEW or PRIMARY_LONG;
3. v0.2 Max DD remains smaller than STATIC20 on the main long-history slices;
4. time at 20% falls below 50% on PRIMARY_LONG and PRE_2020_NEW;
5. 20% occupancy is lower than v0.1 on both slices;
6. at least 75% of closed crisis events retain positive Benefit10;
7. completed Level 3/4 crises retain positive mean Benefit10 and exceed Level-1 mean benefit;
8. no single event explains half or more of total positive Benefit10;
9. 50-bps costs do not erase the central economic comparison;
10. post-2020 behavior does not contradict the pre-2020 direction.

The test additionally measures boundary churn, transition counts, threshold-unit moves and 20%-exposure spell duration.

---

## 6. If E003 is promising

Do not search recovery bands, hysteresis values or nearby thresholds on the same history.

Next step becomes independent evidence:

- freeze v0.2 exactly;
- begin forward paper tracking on future BTC data;
- optionally run a separately pre-specified structural falsification test or block/regime-resampling diagnostic;
- later test implementation realism with real spot weight drift, explicit rebalancing, spread/slippage and cash/custody assumptions.

---

## 7. If E003 redesigns/fails

Do not immediately create v0.3 with optimized hysteresis.

Move to an economically distinct antifragility mechanism, with priority candidates:

- carry-funded dry powder;
- trend + dry powder as a separately specified architecture;
- true long convexity with better option data.

The goal is not to defend the R008 family indefinitely.

---

## 8. Research priority hierarchy

1. Run frozen R008-E003 once and review against its precommitted decision gate.
2. BTC SMA120 frozen forward control continues independently.
3. If E003 advances, create a forward/independent-validation protocol before any additional tuning.
4. If E003 does not advance, close symmetric release and move to a distinct antifragility mechanism.
5. R002 broad-universe rescue and new technical-indicator combinations remain closed priorities.

---

## 9. Plain-language interpretation

v0.1 taught us that buying deeper crashes helped, but holding those extra purchases until a new all-time high trapped the strategy near maximum risk for years.

v0.2 asks one clean question: instead of remembering that a tranche was once triggered, what if the portfolio simply owns more BTC only while the market is currently in a deep drawdown and automatically rebuilds cash as the drawdown heals?

No new thresholds are introduced. The same crisis levels are used in both directions. The price of that simplicity may be threshold churn; E003 measures whether that cost is acceptable rather than hiding it with another parameter.