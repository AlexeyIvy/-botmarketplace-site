# SC001 — Reusable Market Building Blocks Registry v0.3

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C8B-S0**
Parent: `sc001-reusable-market-building-blocks-registry-v0.2.md`

## 1. Inheritance

RB001-RB010 remain unchanged.

## 2. New reusable blocks

### RB011 — Strict-coactive cross-venue basis v0.1

- primitives: P8;
- source evidence: C8-D1E / C8-D3 / F017;
- formula family: same-second cross-venue last-trade relative basis;
- temporal rule: both venues must trade inside the exact same second;
- no carry-forward;
- measurement validity: high;
- preferred roles: R6 reference, R2 venue-state descriptor;
- evidence strength: `REFERENCE_PRIMITIVE`;
- forbidden claim: measurable basis implies tradable arbitrage.

### RB012 — Causal local cross-venue basis reference v0.1

- primitives: P8 + P7;
- source evidence: C8B-S0 / F018;
- formula: prior 300-second wall-clock median of strict-coactive raw basis, current second excluded, min 120 observations;
- preferred role: R6;
- measurement validity: high;
- evidence strength: `REFERENCE_PRIMITIVE`;
- reusable rule: cross-venue dislocation should be measured relative to a causal local venue-basis reference rather than raw price difference alone.

### RB013 — Transient relative-basis deviation v0.1

- primitives: P8/P9;
- source evidence: C8B-S0 / F019;
- role tested: R1/R2;
- observed calibration scale:
  - p99 abs deviation ~2.45 bps;
  - max ~20.8 bps;
  - zero persistent >=30 bps two-second episodes;
- evidence strength: `NEGATIVE_STANDALONE_PAIRED_HEADROOM`;
- preferred future roles: descriptive R2/R6 or execution-context hypothesis only under a materially different economic mechanism;
- forbidden reuse: lowering C8B-S0 threshold or persistence after outcome.

## 3. Important method block

C8 also establishes a non-price reusable engineering rule:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

For trade-based cross-venue research, same-second coactivity is preferred over stale last-trade carry-forward when studying fast dislocations because it avoids manufacturing spread from inactive venue prices.

This is a clock/data-semantics rule, not alpha.
