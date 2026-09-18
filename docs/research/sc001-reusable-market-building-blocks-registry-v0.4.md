# SC001 — Reusable Market Building Blocks Registry v0.4

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C10-S0**
Parent: `sc001-reusable-market-building-blocks-registry-v0.3.md`

## 1. Inheritance

RB001-RB013 remain unchanged.

## 2. New reusable blocks

### RB014 — Causal near-touch depth state v0.1

- primitives: P6;
- source evidence: C10-S0 / F020;
- formula family: top-5 displayed depth separately on bid and ask;
- measurement validity: high on replay-qualified OKX 400-level L2;
- preferred roles: R2 book-state descriptor, R6 reference;
- evidence strength: `REFERENCE_PRIMITIVE`.

### RB015 — Side-specific depth normalization v0.1

- primitives: P6 + P7;
- source evidence: C10-S0 / F021;
- formula: current top-5 side depth divided by prior 60-second causal median;
- minimum baseline observations: 45;
- preferred role: R6 normalization / R2 state;
- evidence strength: `REFERENCE_PRIMITIVE`;
- reusable lesson: book depth should be interpreted relative to a causal local baseline rather than an absolute-contract threshold.

### RB016 — One-sided liquidity-vacuum onset v0.1

- primitives: P6/P10;
- source evidence: C10-S0 / F022;
- role tested: R1/R2;
- event breadth: very high;
- directional association: modest positive;
- broad economic headroom: insufficient for frozen standalone two-fill taker architecture;
- tail association: rare large moves exist but were not prospectively isolated;
- evidence strength: `WEAK_DIRECTIONAL_STATE_RARE_TAIL`;
- preferred future roles: state/context feature in a materially new replenishment, execution-risk, or event-combination mechanism;
- forbidden reuse: post-hoc selection of large-move tails, C5 conditioning, or threshold/horizon tuning under C10-S0.

## 3. Methodological lesson

C10 reinforces:

`frequent state + statistically directional tendency != sufficient executable economic headroom`.

Rare tails should not convert a failed broad structural sentinel into a survivor unless the tail-selection mechanism was defined prospectively.
