# SC001 — N1/N2/N3 Non-Alpha Feasibility Review v0.1

Date: 2026-09-18
Status: **CARD REVIEW COMPLETE / NO C11+ ID ASSIGNED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c7-c10-post-slate-mechanism-building-block-synthesis-v0.2.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-n1-execution-veto-feasibility-card-v0.1.md`;
- `docs/research/sc001-n2-relative-ranking-one-sided-feasibility-card-v0.1.md`;
- `docs/research/sc001-n3-execution-mode-state-feasibility-card-v0.1.md`.

## 1. Review purpose

Apply the newly binding Edge-to-Fill preflight and determine whether N1/N2/N3 are ready to receive C11+ experiment IDs.

No outcome data is opened.

## 2. N1 — Execution Veto

Strengths:

- weak C5/C10 information can matter without adding fills;
- directly targets adverse selection / anti-chase behavior;
- causal measurement infrastructure exists;
- incremental BASE vs BASE+VETO design is statistically clean.

Blocker:

`NO_INDEPENDENT_BASE_OPPORTUNITY_DEFINED`

Without a base opportunity, N1 has nothing to veto.

Disposition:

`HOLD_INFORMATION_VALUE`

## 3. N2 — Relative Ranking with One-Sided Execution

Strengths:

- RB006 is the strongest reusable directional/ranking block from C1-C10;
- observed low-single-digit information is potentially meaningful if it adds no new fills;
- day breadth is better than most other directional blocks.

Risks:

- one-sided implementation can introduce directional beta;
- removing one C6 leg merely to make costs smaller would be disguised rescue tuning;
- no independent one-sided exposure currently exists.

Blocker:

`NO_INDEPENDENT_ONE_SIDED_BASE_EXPOSURE_DEFINED`

Disposition:

`HOLD_INFORMATION_VALUE`

Information-value note:

Among N1/N2/N3, N2 has the strongest inherited directional evidence, but also the strongest hidden-rescue risk.

## 4. N3 — Regime-Dependent Execution Mode

Strengths:

- high-validity R2/R6 state measurements exist;
- no incremental fill requirement;
- direct economic objective: execution cost/adverse-selection reduction;
- counterfactual policy comparison is feasible in principle.

Blocker:

`NO_INDEPENDENT_BASE_OPPORTUNITY_DEFINED`

Without a base trade, maker/taker/no-trade mode has no economic denominator.

Disposition:

`HOLD_INFORMATION_VALUE`

## 5. Comparative Edge-to-Fill review

### N1
- inherited information scale: weak, ~sub-1 bps directional/context
- incremental fills: 0
- cost path: favorable if base exists
- structural classification: `PLAUSIBLE_IF_BASE_EXISTS`

### N2
- inherited information scale: strongest, ~2-4 bps ranking
- incremental fills target: 0
- cost path: favorable only if one-sided base exposure already exists
- structural classification: `PLAUSIBLE_IF_NO_NEW_FILL_AND_BASE_EXPOSURE_EXISTS`

### N3
- direct return information not required
- incremental fills: 0
- cost path: favorable if state can reduce execution burden
- structural classification: `PLAUSIBLE_IF_BASE_EXISTS`

## 6. Shared hidden dependency

All three families fail the same feasibility gate:

`INDEPENDENT_BASE_OPPORTUNITY`

This is now the highest-priority design problem.

Assigning C11/C12/C13 before solving it would create one of two errors:

- a weak feature pretending to be a base strategy;
- a disguised rescue of C1-C10.

## 7. Decision

Do **not** assign C11+ IDs yet.

No new backtest or sentinel is authorized.

Next stage:

`INDEPENDENT BASE OPPORTUNITY DESIGN`

The base mechanism must be economically meaningful without RB001-RB018.

Only after a base mechanism passes non-alpha structural review may N1/N2/N3 be attached as auxiliary roles.

## 8. Required next deliverable

Create an Independent Base Opportunity Search/Design Brief that specifies:

- what counts as independent from C1-C10;
- forbidden rescue relationships;
- edge-scale plausibility;
- fill architecture constraints;
- free/public data feasibility;
- candidate mechanism families allowed for design review;
- stop rule if no credible base is found.

No outcome-bearing experiment may precede that brief.
