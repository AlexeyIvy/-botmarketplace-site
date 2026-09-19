# SC001 Current Roadmap and Stop Rules v4.82

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — POST-C11 BASE POOL REVIEWED / B13-A STRUCTURAL PREFLIGHT NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.81.md`

## 1. Terminal history

All prior terminal states remain binding.

C11:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:

`C12_S0_REJECT_PARITY_REVERSION`

No rescue tuning.

## 2. New independent-base pool

Binding design review:

`docs/research/sc001-post-c11-independent-base-opportunity-pool-v0.1.md`

No C13+ ID has been assigned.

## 3. Pool dispositions

### B13-A — cross-venue funding-differential carry

`ELIGIBLE_FOR_CHEAP_STRUCTURAL_PREFLIGHT`

Primary mechanism:

actual funding cash-transfer differential.

### B13-B — scheduled new-perpetual launch dislocation

`ELIGIBLE_FOR_SOURCE_AND_HEADROOM_PREFLIGHT`

Primary mechanism:

new-market price discovery / inventory transfer relative to mature external reference.

### B13-C — explicit liquidation-flow event transfer

`DEFER_DATA_FEASIBILITY`

No qualified long historical forced-liquidation source yet.

## 4. Why B13-A goes first

The first B13-A stage can be non-price-bearing.

It can test:

- funding source availability;
- cross-venue timestamp/interval compatibility;
- magnitude/frequency of raw funding differential;
- four-fill fee/cost burden arithmetic.

If raw funding transfer cannot plausibly clear the burden often enough:

`REJECT_STRUCTURAL`

before any price backtest.

## 5. B13-A hard boundaries

The preflight may not:

- use subsequent price convergence;
- use basis PnL;
- pick historically profitable symbols;
- lower fee burden after output;
- rely on maker rebates;
- reuse C9 price-normalization logic as alpha.

The transfer itself must carry the structural case.

## 6. Candidate-ID gate

Do not call B13-A `C13` until the structural preflight is complete and its disposition is:

`SELECTED_FOR_FROZEN_EXPERIMENT`

Otherwise reject/defer without consuming fresh price evidence.

## 7. Immediate next action

Freeze B13-A funding-differential structural preflight.

No VPS price-bearing run is authorized.
