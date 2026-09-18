# SC001 — Next-Slate Candidate Design Brief v0.1

Date: 2026-09-18  
Status: **NON-ALPHA CANDIDATE POOL / NO OUTCOME AUTHORIZED**  
Parent roadmap: `sc001-current-roadmap-and-stop-rules-v4.30.md`

## 1. Purpose

After the C1-C6 frozen sentinel batch produced 0 survivors, define a materially new research pool without rescue-tuning any rejected candidate.

This document does not freeze a new sentinel budget and does not authorize any alpha outcome.

## 2. Design principles after C1-C6

The next slate should favor mechanisms where expected economic magnitude can plausibly arise from:

- spread capture / execution structure;
- cross-venue dislocation;
- scheduled derivative-state transitions;
- liquidity-state discontinuities;

rather than another weak sub-bps directional forecast.

Every candidate must pass a cheap structural/data feasibility screen before any alpha sentinel.

## 3. Candidate C7 — spread-qualified passive/hybrid maker universe

### Mechanism

M2 liquidity provision / spread capture.  
Execution: T2/T4 passive or hybrid.

### Why distinct

This is not an E008 BTC same-rule retest.

Universe must be selected prospectively by non-PnL spread/fee/liquidity eligibility before queue modeling.

### First non-alpha question

Do any frozen liquid markets have quoted spread distributions large enough to leave structural headroom after maker/taker fee reserve and a conservative adverse-selection reserve?

### Data

Requires top-of-book/L2 snapshots or equivalent reconstructable best bid/ask on already contaminated calibration dates or newly governed calibration dates.

### Cheapest kill test

Spread/headroom distribution only:

- no fill model;
- no queue model;
- no PnL;
- no historical winner selection.

If spread headroom is structurally absent, kill C7 before heavy queue work.

## 4. Candidate C8 — cross-venue same-asset dislocation / information transfer

### Mechanism

M5/M6 relative value / cross-venue information transfer.  
Execution: T1 directional lag capture or T3 paired hedge, to be decided before outcome.

### Why distinct

C4 tested BTC/ETH -> alt information transfer on the same venue. C8 tests independent venue clocks for the same asset.

### First non-alpha question

Can free historical data from two venues be synchronized causally with sufficient timestamp quality, and do raw cross-venue dislocations occur at magnitudes that could exceed the relevant fill-count cost floor?

### Data

Prospectively selected venue pair, preferably OKX plus one venue with free historical trade/quote archives.

No use of protected data from other BotMarketplace branches without an explicit SC001 contamination/data-role decision.

### Cheapest kill test

- data availability;
- clock/alignment audit;
- raw dislocation frequency/headroom distribution;
- no strategy optimization.

## 5. Candidate C9 — scheduled funding / mark-index state transition

### Mechanism

M5/M7 derivative-state / scheduled-event mechanism.  
Execution to be frozen after structural feasibility.

### Why distinct

C1 used spot/perp basis threshold convergence. C9 uses a scheduled derivative-state event and funding/mark/index information rather than a +50 bps basis-dislocation trigger.

### First non-alpha question

Around known funding timestamps, do funding/mark/index states create sufficiently frequent and sufficiently large post-event price/basis transitions to justify a new experiment?

### Data

Prefer public historical funding-rate, mark/index and trade data.

### Cheapest kill test

- funding-event count;
- exact historical availability;
- state-transition magnitude distribution;
- estimated fill-count structural hurdle.

No funding threshold or event window may be optimized on PnL in the feasibility stage.

## 6. Candidate C10 — L2 liquidity-vacuum / replenishment event

### Mechanism

M7 + M3/M4 liquidity-state discontinuity.  
Execution: T1/T4 depending prospectively frozen mechanism.

### Why distinct

This is not C5 plus L2.

C5's trigger was aggressive trade flow. C10 would be defined directly from book-state primitives such as spread shock, near-touch depth depletion, or replenishment failure, with an independently stated economic mechanism.

### First non-alpha question

Do objectively large liquidity-vacuum states occur frequently enough, and are subsequent price transitions large enough, to justify full L2 execution research?

### Data

L2/top-of-book history on a prospectively frozen universe.

### Cheapest kill test

Event frequency + unconditional move/headroom only.

No C5 event labels, no trade-flow rescue filter, and no post-outcome threshold grid.

## 7. Candidate-pool constraints

C7-C10 are **candidate directions**, not yet experiments.

Before any outcome:

1. write one feasibility card per candidate;
2. freeze data role and contamination status;
3. verify free-data availability;
4. define structural cost/fill architecture;
5. define one cheapest falsification sentinel;
6. decide whether each candidate is distinct enough from terminal families;
7. only then freeze a small diversified next-slate budget.

## 8. Data-cost posture

Continue the project preference to avoid paid data where possible.

A candidate that depends on expensive proprietary data must first show that no adequate free source exists and that its expected information value justifies the cost.

## 9. Immediate next action

Perform a **no-alpha data/structural feasibility audit** for C7-C10:

- available local data;
- free public historical sources;
- expected data volume;
- causal timestamp quality;
- fill count / cost architecture;
- cheapest sentinel complexity.

Do not compute candidate returns or PnL during this audit.
