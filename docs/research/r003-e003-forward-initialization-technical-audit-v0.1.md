# R003-E003 — Forward Initialization Technical Audit v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Scope:** first R003-E003 forward snapshot after fixed inception  
**Status:** initialization accepted; latent funding-timestamp attribution defect identified before first realized funding event

## 1. Submitted snapshot

The first submitted R003-E003 package contains the required nine user-facing outputs plus the locally patched engine copy.

Run state:

- status: `PASS`;
- evidence status: `FORWARD_EVIDENCE_ACCUMULATING`;
- fixed inception boundary: `2026-09-10 12:00:00 UTC`;
- initial establishment close: `2026-09-10 12:59:59.999 UTC`;
- latest included close: `2026-09-10 13:59:59.999 UTC`;
- elapsed forward time: one hour;
- realized funding events used: 0;
- completed month-end rebalances: 0.

This matches the frozen protocol's establishment rule: the first fully closed common one-hour bar with open time at or after the 12:00 UTC decision boundary establishes the paper position at approximately 12:59:59.999 UTC.

## 2. Data integrity

Source audit is correctly classified `EARLY_FORWARD_SAMPLE`, not a mature PASS, because only two common closed hourly bars exist in the first snapshot.

For spot, futures contract, futures mark and the common intersection:

- two expected/two retained hourly rows;
- 100% observed coverage;
- maximum gap one hour;
- no data-integrity failure is visible.

The early-sample status is appropriate and must not be interpreted as strategy evidence.

## 3. Initial implementation accounting

Baseline 10 bps per-leg track:

- initial long spot notional ~0.5 NAV;
- initial short perpetual notional ~0.5 NAV;
- total initial traded notional ~1.0 NAV;
- realized initial execution fee ~0.001 NAV, consistent with 10 bps applied to each leg's traded notional;
- no month-end rebalance yet;
- no realized funding event yet.

The reported liquidation-adjusted cumulative return near -0.203% is dominated by the already-realized initial entry cost plus a hypothetical terminal exit cost included for review metrics. It must not be read as one-hour economic underperformance of the carry mechanism. Going-concern NAV drawdown over the same tiny sample is about -0.103%.

## 4. Margin diagnostics

The first sample shows:

- minimum close collateral ratio ~99.12%;
- minimum intrahour collateral ratio ~98.95%;
- zero low-headroom flags;
- no modeled hard margin failure.

This is only a one-hour technical snapshot and is not evidence of long-run liquidation safety.

## 5. Safe-hurdle causality

Dynamic Treasury status is `PASS`.

The latest Treasury quote used is dated 2026-09-09, consistent with the protocol rule that a quote dated day d becomes usable only on day d+1.

The fixed 3.90% inception Treasury hurdle and fixed 5.90% compensation floor remain unchanged.

## 6. Latent funding timestamp attribution defect

A code audit found a technical causality issue in the v0.2 implementation before any forward funding event had entered the record.

The prior `align_funding` implementation used backward `merge_asof` from a funding timestamp to hourly `close_time`. For a funding event at exactly 16:00:00 UTC, the latest prior common close is 15:59:59.999 UTC. The implementation would therefore associate the 16:00 event with the 15:00 hourly accounting row and could include it one millisecond before the event timestamp.

The submitted first snapshot is **not contaminated** by this defect because `funding_events_used = 0` and the funding-event output is empty.

This is an implementation-timing defect, not a strategy or parameter issue.

## 7. Technical correction

A new launcher was created:

`research/r003/r003_e003_forward_paper_mobile_causality_hotfix.py`

Commit:

`4aef73ff696821d762e0822c012459078f7b8a33`

It still downloads the exact frozen economic engine commit `cfc001400008ee4d63a27ad6821dda5cb9354f3e` and applies only technical corrections:

1. preserves pandas datetime-unit normalization;
2. attributes funding to the first closed common hourly accounting row whose close is at/after the funding timestamp;
3. if a published funding mark is unavailable, uses only the latest mark close at/before the funding timestamp as causal fallback;
4. includes a funding event in a snapshot only when `funding_time <= latest closed common bar`.

No inception, portfolio weights, funding sign, costs, rebalance cadence, margin rule, Treasury rule, evidence threshold or strategy decision rule changes.

## 8. Decision

> **R003-E003 initial establishment is technically accepted and uncontaminated. Before the first realized funding event is recorded, future refreshes must use the funding-causality hotfix launcher.**

Do not reset the forward inception or delete the persistent R003 forward folder.

No strategy conclusion is permitted from this one-hour snapshot.
