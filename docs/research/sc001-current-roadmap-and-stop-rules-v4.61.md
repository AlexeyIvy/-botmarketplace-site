# SC001 Current Roadmap and Stop Rules v4.61

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — POST-SLATE SYNTHESIS EXPANDED / N1-N3 CARDS REVIEWED / INDEPENDENT BASE OPPORTUNITY REQUIRED BEFORE C11+**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.60.md`

## 1. Binding terminal strategy states

All prior terminal states remain immutable.

- C1-C6: `REJECT_SENTINEL`;
- C9-S1: `C9_S1_REJECT_SENTINEL`;
- C8B-S0: `C8B_S0_REJECT_HEADROOM`;
- C10-S0: `C10_S0_REJECT_HEADROOM`;
- C7-S0: `C7_S0_REJECT_SPREAD_HEADROOM`.

No rescue tuning is authorized.

## 2. Expanded post-slate synthesis

Current binding synthesis:

`docs/research/sc001-c7-c10-post-slate-mechanism-building-block-synthesis-v0.2.md`

New major conclusions include:

- empirical design prior: ordinary liquid-crypto conditional information often appears in the ~0.5-4 bps range;
- future candidate design must optimize `edge scale / fill count / cost reserve`;
- C2 is more useful as no-fade/persistence veto information than as mean-reversion alpha;
- C6 remains the strongest reusable directional/ranking block;
- C5/C10 are better suited to R2/R3/R5 execution-context roles;
- C10 suggests a future replenishment-failure hypothesis, not a C10 rescue;
- C8 strict-coactive no-carry-forward is a reusable cross-venue standard;
- C7 reinforces spread-first, queue-model-second research order.

## 3. Binding Edge-to-Fill preflight

New required governance artifact:

`docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`

No C11+ candidate ID may be assigned before this preflight is completed.

Required explicit fields include:

- expected information scale;
- structural fill count;
- conservative fee floor;
- spread/depth exposure;
- execution reserve;
- break-even move;
- opportunity rate;
- capital-time utilization.

## 4. N1/N2/N3 feasibility cards completed

Cards:

- `docs/research/sc001-n1-execution-veto-feasibility-card-v0.1.md`;
- `docs/research/sc001-n2-relative-ranking-one-sided-feasibility-card-v0.1.md`;
- `docs/research/sc001-n3-execution-mode-state-feasibility-card-v0.1.md`.

Comparative review:

`docs/research/sc001-n1-n3-non-alpha-feasibility-review-v0.1.md`

## 5. N1/N2/N3 dispositions

### N1 — Execution Veto
Disposition:

`HOLD_INFORMATION_VALUE`

Blocker:

`NO_INDEPENDENT_BASE_OPPORTUNITY_DEFINED`

### N2 — Relative Ranking with One-Sided Execution
Disposition:

`HOLD_INFORMATION_VALUE`

Blocker:

`NO_INDEPENDENT_ONE_SIDED_BASE_EXPOSURE_DEFINED`

N2 retains the strongest inherited directional/ranking information but also the highest hidden-C6-rescue risk.

### N3 — Regime-Dependent Execution Mode
Disposition:

`HOLD_INFORMATION_VALUE`

Blocker:

`NO_INDEPENDENT_BASE_OPPORTUNITY_DEFINED`

## 6. No C11+ ID assigned

This is deliberate.

Shared hidden dependency:

`INDEPENDENT BASE OPPORTUNITY`

Without such a base:

- N1 has nothing to veto;
- N2 risks becoming a cheaper rewrite of C6;
- N3 has no trade whose execution mode can be optimized.

Therefore:

`NO C11/C12/C13 ASSIGNMENT YET`

## 7. Custom feature hypothesis backlog

New design-only registry:

`docs/research/sc001-custom-feature-hypothesis-backlog-v0.1.md`

Current entries:

- FH001 Flow-to-Liquidity Pressure;
- FH002 Liquidity Replenishment Failure;
- FH003 No-Fade Local-Deviation State.

All are:

`HOLD_INFORMATION_VALUE`

No outcome test is authorized.

## 8. Independent Base Opportunity design stage

Binding brief:

`docs/research/sc001-independent-base-opportunity-design-brief-v0.1.md`

A base mechanism is independent only if:

- it remains economically meaningful without RB001-RB018;
- it is not a parameter-neighbor or sign-flip of C1-C10;
- it has a plausible edge source before outcome;
- it passes Edge-to-Fill review;
- it has feasible fresh evidence.

## 9. Allowed design domains

Non-alpha design may explore:

- mandatory-action selection;
- inventory/risk transfer;
- structural venue/product events;
- slower low-turnover state transitions;
- externally specified independent signals.

These are design domains, not candidate IDs.

## 10. Current hard gate

`NO OUTCOME-BEARING C11+ EXPERIMENT`

Allowed:

- independent base-mechanism concept design;
- feasibility cards;
- data-cost/source review;
- edge-to-fill arithmetic;
- contamination planning;
- sentinel design.

Forbidden:

- new backtests;
- threshold search;
- feature-combination mining;
- historical winner selection;
- protected/promotional evidence access.

## 11. Immediate next action

Create a pool of at most three genuinely independent base-mechanism concepts.

For each:

1. state economic payer/source of edge;
2. show independence from C1-C10;
3. complete Edge-to-Fill arithmetic;
4. state required free/public data;
5. state cheapest non-alpha sentinel;
6. reject any concept whose architecture is structurally implausible.

Only after this review may at most one or two mechanisms receive C11+ IDs.
