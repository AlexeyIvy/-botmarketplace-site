# SC001 — Reusable Market Building Blocks Registry v0.5

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C7-S0**
Parent: `sc001-reusable-market-building-blocks-registry-v0.4.md`

## 1. Inheritance

RB001-RB016 remain unchanged.

## 2. New reusable blocks

### RB017 — Causal quoted-spread state v0.1

- primitives: P6/P8;
- source evidence: C7-S0 / F023;
- formula: 10000 * (best_ask - best_bid) / mid;
- role: R2/R6 execution-state reference;
- measurement validity: high;
- evidence strength: `REFERENCE_PRIMITIVE`;
- reusable lesson: fee/execution architecture should be screened against the empirical spread distribution before queue/fill simulation.

### RB018 — Persistent high-spread regime v0.1

- primitives: P6/P10;
- source evidence: C7-S0 / F024;
- tested definition: spread >=10 bps for >=5 consecutive valid seconds;
- role: R2/R4 eligibility state;
- observed breadth: absent across all seven frozen assets;
- evidence strength: `NEGATIVE_STRUCTURAL_EVIDENCE_AT_10BPS`;
- forbidden reuse: threshold lowering or sparse-tail mining under C7-S0.

## 3. Cross-candidate methodological lesson

C7 completes a recurring SC001 pattern:

`do structural headroom screening before expensive execution modeling`.

When quoted spread itself is orders of magnitude below the cost/reserve architecture, queue/fill realism cannot repair the mechanism.
