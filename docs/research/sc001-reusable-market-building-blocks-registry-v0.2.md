# SC001 — Reusable Market Building Blocks Registry v0.2

Date: 2026-09-18  
Status: **APPEND-ONLY CONTINUATION AFTER C9-S1**  
Parent: `sc001-reusable-market-building-blocks-registry-v0.1.md`

## 1. Inheritance

RB001-RB008 remain unchanged.

## 2. New blocks

### RB009 — Scheduled funding-event context v0.1

- primitives: P8 + P11;
- source evidence: C9-D1 / C9-S1 / F015;
- formula family: realized funding timestamp + funding sign, no magnitude threshold;
- measurement validity: high;
- event breadth: high across 8 assets and 30 days;
- tested directional role: 30-minute post-funding mark/index normalization;
- observed directional effect: effectively zero;
- evidence strength: `STATE_ONLY_WITH_NEGATIVE_DIRECTIONAL_EVIDENCE`;
- preferred future roles: R2 scheduled-event context, possibly R3/R5 only under a separately motivated mechanism;
- forbidden reuse: choose funding threshold/sign/horizon from C9-S1 outcome;
- next valid question: only a materially different economic mechanism, not a tuned C9-S1.

### RB010 — Mark/index premium state v0.1

- primitives: P8 + P7;
- source evidence: C9-D2 / C9-S1 / F016;
- formula family: causal mark price relative to index price;
- measurement validity: high;
- data semantics: synchronized 15m mark/index tape;
- tested directional use: post-funding 30-minute normalization;
- observed directional effect: unsupported;
- evidence strength: `REFERENCE_PRIMITIVE`;
- preferred roles: R6 reference, R2 derivative-state descriptor;
- forbidden claim: directional C9-S1 failure implies the premium state is globally useless.

## 3. Combination guardrail

RB009/RB010 must not be combined with RB001-RB008 by historical subset search.

Any future use requires:

- a new economic mechanism;
- explicit role;
- frozen interaction budget;
- fresh evidence.
