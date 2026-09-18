# SC001 — Independent Base Opportunity Search / Design Brief v0.1

Date: 2026-09-18
Status: **NON-ALPHA DESIGN STAGE / REQUIRED BEFORE C11+**
Scope: `SCALPING RESEARCH / SC001`

## 1. Objective

Define one or more economically independent base opportunities that can stand without RB001-RB018.

Only after a base mechanism exists may weak reusable blocks be attached as veto/ranking/execution-state features.

## 2. Definition of an independent base opportunity

A base mechanism is independent only if:

- its economic rationale does not require a C1-C10 feature effect;
- it remains meaningful if all RB001-RB018 are removed;
- its entry/exit logic is not a parameter-neighbor version of a terminal candidate;
- its expected edge source can be described before outcome;
- its fill architecture is economically plausible under the SC001 Edge-to-Fill preflight.

## 3. Forbidden disguised rescues

Not independent:

- reversed C2;
- cheaper one-leg C6 without an external reason for one-sided exposure;
- lower-threshold C7;
- tail-selected C10;
- lower-hurdle C8B;
- filtered C9;
- C5+C10 combination presented as a new base;
- E008/BTC same-rule retest.

## 4. Base-mechanism design domains allowed for review

Allowed to design, not yet test:

### A. Mandatory-action selection
An economic process in which a trade/rebalance/hedge must occur for reasons independent of a weak feature, and SC001 blocks only choose instrument/timing/execution.

### B. Inventory/risk transfer
A base opportunity arising from inventory, hedge, funding, collateral or exposure-management needs rather than pure directional prediction.

### C. Structural venue/product event
A prospectively known market-structure event with a direct economic mechanism not already covered by C7-C10.

### D. Slower low-turnover state transition
A mechanism whose expected edge horizon can plausibly exceed the cost burden without increasing fill count.

### E. External independently specified signal
A base opportunity defined outside the reused SC001 feature stack, after which SC001 blocks may be tested incrementally.

## 5. Edge-to-Fill requirements

For every proposed base:

- expected gross information scale;
- structural fills;
- fee floor;
- spread/depth reserve;
- execution reserve;
- break-even move;
- opportunity rate;
- capital-time utilization.

A base that relies on ordinary ~1-4 bps information but requires a 10-30 bps burden should be rejected before outcome unless a separate structural source explains the gap.

## 6. Complexity budget

Per proposed base:

- one core mechanism;
- no more than one mechanism-defining primary feature family;
- no auxiliary SC001 block during base feasibility review;
- no parameter grid;
- no historical winner subset.

Auxiliary blocks are considered only after the base passes structural review.

## 7. Data feasibility

Prefer:

- already available public/free data;
- already qualified source semantics;
- modest new acquisition cost;
- no proprietary latency feed unless absolutely necessary.

Reject or defer candidates whose claimed edge exists only at a latency/data resolution unavailable to the project.

## 8. Evidence chronology

Before any base outcome:

- declare Selection/Calibration periods;
- preserve untouched later evidence;
- record contamination;
- freeze cheapest sentinel;
- freeze stop rule.

## 9. Stop rule

If no base mechanism can simultaneously satisfy:

- economic independence;
- edge-to-fill plausibility;
- data feasibility;
- bounded complexity;
- fresh evidence availability;

then stop SC001 candidate expansion rather than force C11.

## 10. Immediate design task

Produce a small pool of at most three independent base-mechanism concepts.

For each:

- write a feasibility card;
- run only non-alpha structural review;
- select at most one or two for candidate-ID assignment.

Until then:

`NO C11+ OUTCOME RUN`.
