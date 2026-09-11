# SC001 Event Calendar Policy v0.1

Date: 2026-09-11

## Purpose

Add real-world scheduled macro-event context to SC001 without contaminating the primary signal search or creating hindsight filters.

## Core rule

Scheduled macro events are an **exogenous diagnostic/stress layer first**, not a trading-signal filter.

No SC001 hypothesis may be rescued after seeing P&L by excluding event windows. Any event-aware entry/exit rule must receive a new experiment ID and be frozen before testing.

## Initial event families

The first calendar should be limited to objectively timestamped, recurring high-impact US macro / policy events with official release times, such as:

- FOMC policy decisions and press conferences;
- CPI / Core CPI;
- Employment Situation / Nonfarm Payrolls / unemployment rate;
- PCE / Core PCE;
- GDP releases.

Additional event families require a separate documented amendment before they are used in strategy rules.

## Source preference

Prefer official first-party calendars/releases (Federal Reserve, BLS, BEA and equivalent authoritative sources) over retrospective lists or subjective news classifications.

A commercial economic calendar may be used for cross-checking, but must not be the sole provenance when an official source exists.

## Time handling

Every event must be stored with:

- event family;
- official scheduled release timestamp;
- UTC timestamp;
- source/provenance;
- release version where relevant;
- whether the timestamp was scheduled or unscheduled.

Do not label an event as important because BTC moved strongly afterward.

## Frozen diagnostic windows

Before observing strategy P&L by event, use fixed windows around the scheduled timestamp. Initial diagnostic windows:

- narrow: `[-5 min, +30 min]`;
- primary: `[-30 min, +60 min]`;
- broad stress: `[-60 min, +180 min]`.

These windows are diagnostics only unless promoted in a later pre-registered experiment.

## Required comparisons

For each strategy candidate, compare event vs non-event periods on at least:

- gross and net edge per trade;
- trade count;
- realized volatility;
- spread where available;
- depth / imbalance where L2 is available;
- trade intensity / aggressor flow;
- slippage/execution proxy;
- latency sensitivity;
- tail losses and drawdown contribution.

## Surprise data

Actual-vs-consensus surprise may be valuable but is not part of v0.1. Consensus histories are often less reproducible/free than official timestamps. Any surprise-based rule requires separate provenance and pre-registration.

## Crypto-specific unscheduled news

Exchange failures, hacks, regulatory actions, ETF decisions and similar events are potentially important but carry much higher classification/hindsight risk. They must be maintained in a separate event family with explicit provenance and must not be mixed into the initial scheduled-macro gate.

## Anti-overfitting boundary

Forbidden after result inspection:

- selecting only event types that improve P&L;
- tuning event windows to maximize returns;
- removing individual events because they were unfavorable;
- defining importance by realized BTC volatility;
- using event exclusions to rescue a failed base hypothesis.

## Role in SC001

The event calendar is mandatory context before serious minute/tick/L2 validation. It does not alter the mathematical signal definition unless a later independent experiment explicitly pre-registers an event-aware rule.
