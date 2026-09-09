# R008 Near-Term Research Roadmap v1.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-09  
**Status:** E002 complete; R008 v0.1 REDESIGN  
**Research posture:** antifragility-first, falsification-first, no hidden tuning

---

## 1. Current strategic decision

R008 remains the primary active antifragility research branch, but **R008 v0.1 is closed as REDESIGN** after independent long-history validation.

Canonical result:

`docs/research/r008-e002-results-v0.1.md`

R002 broad-universe SMA120 and Donchian 100/50 remain FINAL REDESIGN / NOT PASS for naive complete archive-defined deployment. Do not rescue them with technical indicators on the same sample.

The frozen BTC SMA120 forward record continues independently as a control.

R001 tested option implementations remain paused/redesign.

---

## 2. What E002 established

Independent Blockchain.com Bitcoin reference history passed data audit and extended the state path back to 2010.

Primary new evidence window: 2013-01-01 through 2019-12-31.

R008 v0.1 on PRE_2020_NEW:

- CAGR ~19.67%;
- Max DD ~-22.99%;
- Calmar ~0.86;
- average BTC exposure ~18.35%.

STATIC15 on the same slice:

- CAGR ~20.16%;
- Max DD ~-19.83%;
- Calmar ~1.02.

Therefore STATIC15 economically dominates R008 on the primary new evidence slice.

At the same time, crisis-event evidence remains strong:

- Benefit10 positive in all 18 closed events across the long history;
- mean Benefit10 rises from ~+0.81% at Level 1 to ~+12.78% at Level 4;
- PRE_2020_NEW has 7/7 positive Benefit10 events;
- no single event explains the majority of positive benefit;
- costs through 50 bps do not erase the effect;
- post-2020 replay is consistent with E001.

Conclusion:

> Crisis deployment itself works as an incremental mechanism, but ATH-only release keeps risk deployed too long.

---

## 3. Primary failure mode

R008 v0.1 spends too much time at maximum BTC target:

- ~58% of PRIMARY_LONG observations at 20% BTC;
- ~76% of PRE_2020_NEW observations at 20% BTC.

Deep crises can leave all tranches deployed for years:

- one pre-2020 episode lasted ~1,175 days before ATH reset;
- another lasted ~1,074 days.

This violates the intended cash-heavy barbell behavior and explains why a simple static midpoint allocation can outperform the state machine.

---

## 4. Anti-overfitting closure for v0.1

Do not alter or rerun R008 v0.1 with nearby settings.

Frozen historical record remains:

- 10% permanent BTC;
- 10% reserve;
- 2.5% x 4 tranches;
- -20/-35/-50/-65 triggers;
- ATH-only reset.

Do not search:

- nearby trigger thresholds;
- different tranche sizes;
- alternative base/reserve weights;
- optimized ATH/recovery thresholds;
- event-specific exits;
- RSI/SMA/ADX/volatility filters to rescue the result.

Any material change is a new R008 version.

---

## 5. NEXT STEP — R008 v0.2 recovery-release hypothesis

**Priority:** immediate design/freeze before any new result.

The next test should isolate the observed economic failure mode with minimal additional degrees of freedom.

### Proposed mechanism

Retain for comparability:

- 10% permanent BTC base;
- 10% opportunity reserve;
- four equal 2.5% tranches;
- the same -20/-35/-50/-65 drawdown thresholds;
- no leverage/shorts/technical filters.

Change only the release logic:

> Target exposure is determined by the **currently breached drawdown levels**, not by whether a level was ever breached since the last ATH.

Thus:

- as drawdown deepens, additional tranches deploy;
- as drawdown recovers above a threshold, that tranche is released and dry powder is rebuilt;
- no new recovery thresholds are introduced;
- the same four levels govern both deployment and release.

This is a new economic hypothesis, not a tweak to v0.1:

> Temporarily increase BTC exposure while stress is extreme, then systematically restore dry powder as stress normalizes.

The first v0.2 test should add no hysteresis or optimized exit bands. Boundary-churn risk should be measured explicitly rather than solved in advance with another parameter.

---

## 6. Required v0.2 benchmarks and evidence

Reuse the independent long-history source and the same main slices:

- PRE_2020_NEW;
- PRIMARY_LONG;
- REPLAY_2020;
- POST_2023.

Mandatory benchmarks:

- CASH;
- STATIC10;
- STATIC15;
- STATIC20;
- R008 v0.1 frozen historical comparator;
- BTC100 contextual.

The key question is not whether v0.2 has higher CAGR than v0.1. It is whether it restores a genuine dry-powder/barbell profile while retaining meaningful severity-ordered crisis benefit.

Required new diagnostics:

- fraction of time at each target exposure;
- average target exposure;
- tranche entries and exits;
- turnover and cost stress;
- time from maximum deployment back to 10/12.5/15% exposure;
- crisis Benefit10/15/20;
- severity ordering;
- comparison with STATIC15 on CAGR/DD/Calmar.

---

## 7. v0.2 decision gates

Before running, create a formal protocol with exact rules.

### Advance / promising

A redesigned architecture should broadly:

1. beat STATIC10 on geometric growth;
2. avoid economic domination by STATIC15;
3. keep Max DD materially below STATIC20;
4. retain coherent positive Benefit10 during deep crises;
5. spend substantially less than half of the primary history at maximum 20% exposure;
6. rebuild dry powder materially faster than ATH-only v0.1;
7. remain robust under 25-50 bps cost stress despite higher turnover;
8. reproduce qualitatively in both pre-2020 and post-2020 periods.

### Redesign / fail

If symmetric release simply turns into noisy rebalancing, loses the crisis benefit, or remains dominated by static allocation, close the mechanism rather than adding hysteresis immediately.

Any hysteresis/band redesign would require yet another explicit version and independent justification.

---

## 8. Research priority hierarchy

1. **Write/freeze R008 v0.2 recovery-release protocol before backtest.**
2. Implement one auditable long-history engine using the same source and benchmarks.
3. Run the frozen test once; no rescue parameter grid.
4. BTC SMA120 frozen forward record continues independently.
5. If v0.2 fails, consider an economically distinct antifragility branch rather than endless release-rule tuning:
   - carry-funded dry powder;
   - trend + dry powder as a separate architecture;
   - true long convexity with better option data.
6. R002 broad-universe rescue and new technical-indicator combinations remain closed priorities.

---

## 9. Plain-language interpretation

The first anti-fragile idea taught us something useful rather than simply passing or failing.

Buying more BTC after deep drawdowns consistently helped relative to keeping only 10% BTC, and the benefit became larger in deeper crises. That part reproduced over older independent history.

The flaw was that after buying during a crash, v0.1 waited for a new all-time high before rebuilding cash. In long Bitcoin bear/recovery cycles that can take several years, so the supposedly cash-heavy barbell spends most of its time near maximum risk.

The next clean question is therefore narrow:

> Can we preserve the crisis-buying benefit while automatically rebuilding dry powder as the drawdown itself heals, using the same thresholds in reverse and without introducing another optimized indicator?
