# SC001 — Strategy Landscape v0.6

Date: 2026-09-18
Status: **CURRENT COVERAGE MAP AFTER C7-S0 / C7-C10 NEXT-SLATE COMPLETE / NON-ALPHA GOVERNANCE ARTIFACT**
Supersedes: `sc001-strategy-landscape-v0.5.md`

## 1. Binding terminal states

All prior terminal decisions remain binding.

- C1-C6: terminal `REJECT_SENTINEL`;
- C9-S1: terminal `C9_S1_REJECT_SENTINEL`;
- C8B-S0: terminal `C8B_S0_REJECT_HEADROOM`;
- C10-S0: terminal `C10_S0_REJECT_HEADROOM`;
- C7-S0: terminal `C7_S0_REJECT_SPREAD_HEADROOM`.

No direct rescue-tuning of any of these candidates is authorized.

## 2. C7 — non-BTC multi-asset passive/hybrid spread capture

Frozen structural sentinel:

`C7-S0 multi-asset quoted-spread structural headroom`

Terminal state:

`C7_S0_REJECT_SPREAD_HEADROOM`

Observed on the frozen 2024-02-12 seven-asset non-BTC calibration set:

- all 7 assets passed data gates;
- 0/7 assets passed structural spread eligibility;
- all p75 quoted spreads were below 10 bps;
- highest p75 in the universe was BCH at about 3.68 bps;
- >=10 bps spread seconds were zero or effectively zero;
- persistent >=5-second high-spread episode count was 0 for every asset.

Coverage implication:

- the prospectively frozen maker-entry + taker-fail-safe architecture lacks quoted-spread headroom across the frozen liquid non-BTC universe;
- queue/fill/adverse-selection modeling is not justified for this exact C7 mechanism;
- relatively wider assets such as BCH/XRP/UNI may not be selected post hoc as historical winners.

## 3. Completed C7-C10 next-slate summary

The diversified next-slate was designed to favor mechanisms where economic magnitude might come from structure rather than sub-bps directional forecasting.

### C9 — scheduled funding / mark-index normalization
- terminal: REJECT;
- ample sample;
- signed 30-minute normalization effect approximately zero.

### C8B — cross-venue paired relative-basis convergence
- terminal: REJECT_HEADROOM;
- excellent strict-coactive clock quality;
- p99 transient dislocation ~2.45 bps;
- max ~20.8 bps;
- zero persistent >=30 bps episodes.

### C10 — one-sided L2 liquidity vacuum
- terminal: REJECT_HEADROOM;
- very large event sample and broad time coverage;
- modest directional tendency retained as feature evidence;
- p90 absolute 5s move only ~3.58 bps versus 15 bps hurdle;
- rare tails not sufficient for promotion.

### C7 — passive/hybrid quoted-spread capture
- terminal: REJECT_SPREAD_HEADROOM;
- 7/7 data quality;
- 0/7 structurally eligible assets;
- quoted spreads overwhelmingly far below 10 bps.

## 4. What the slate taught us

Across C7-C10, the dominant recurring finding is:

`measurement quality is often high, but edge/headroom scale is too small for the required fill architecture`.

This strengthens the earlier C1-C6 lesson that future candidate design must focus on:

`informational edge scale / structural fill count / cost reserve`

before expensive simulation.

## 5. Strongest reusable evidence classes

The completed slate contributes high-confidence measurement/reference blocks:

- causal local references and residualization;
- strict-coactive 1-second synchronization with no carry-forward;
- cross-venue raw basis and local basis normalization;
- near-touch L2 depth and side-specific causal depth normalization;
- quoted spread state;
- scheduled funding clock/state;
- cross-sectional residual ranking;
- liquidity-vacuum onset as weak directional/context information.

Most of these are stronger as R2/R3/R5/R6 features than as standalone R1 strategies.

## 6. Current information gap

There is no surviving strategy from the frozen C7-C10 slate.

Therefore the next legitimate step is **not** to invent C11 from the most attractive historical residual.

The next step is a non-alpha synthesis that:

1. reviews all reusable blocks RB001-RB018;
2. identifies which blocks have:
   - valid measurement,
   - positive directional/state information,
   - low incremental fill cost,
   - orthogonal economic roles;
3. identifies combinations with a genuine economic interaction hypothesis rather than arithmetic addition;
4. proposes a new candidate slate only after complexity and contamination budgets are frozen.

## 7. Current hard gate

`NO NEW OUTCOME-BEARING CANDIDATE UNTIL POST-SLATE SYNTHESIS IS FROZEN`

Allowed:

- registry synthesis;
- redundancy/role mapping;
- edge-to-fill analysis;
- non-alpha candidate-card design;
- data-cost feasibility;
- prospective interaction hypotheses.

Not allowed:

- threshold shopping;
- historical winner subset mining;
- combination testing on the same calibration periods;
- opening protected promotional evidence.

## 8. Immediate next action

Create and freeze a **Post-Slate Mechanism & Building-Block Synthesis** and from it a small new candidate pool.

Only after that synthesis may any C11+ ID be assigned.
