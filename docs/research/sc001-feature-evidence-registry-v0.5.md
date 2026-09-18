# SC001 — Feature Evidence Registry v0.5

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C10-S0**
Parent: `sc001-feature-evidence-registry-v0.4.md`

## 1. Inheritance

All prior feature-evidence records remain unchanged and binding.

New evidence role:

`SELECTION_CALIBRATION_ONLY`

## 2. New records

### F020 — Top-5 near-touch visible depth

- primitive family: P6 order-book liquidity;
- source: C10-S0;
- venue/instrument: OKX BTC-USDT-SWAP;
- definition: displayed size sum over best five prices on each side;
- role: R2 state / R6 reference;
- measurement validity: established under replay-qualified 400-level L2;
- classification: `REFERENCE_PRIMITIVE`;
- allowed conclusion: near-touch visible depth is a stable causal book-state measurement;
- forbidden claim: visible depth alone is executable alpha.

### F021 — Side-specific causal depth baseline

- primitive family: P6/P7;
- source: C10-S0;
- definition: side-specific median top-5 depth over prior 60 wall-clock seconds, current second excluded, minimum 45 valid observations;
- role: R6 normalization;
- measurement validity: established;
- classification: `REFERENCE_PRIMITIVE`;
- allowed conclusion: side depth can be normalized against a causal local baseline without trade-flow conditioning.

### F022 — One-sided near-touch liquidity-vacuum onset

- primitive family: P6/P10;
- source: C10-S0;
- role tested: R1/R2 event state;
- event rule:
  - depleted side <=1/3 of its causal median;
  - opposite side >=2/3 of its causal median;
  - onset from prior valid NONE state;
- sample:
  - bid-vacuum events = 6,443;
  - ask-vacuum events = 6,331;
  - 24 UTC hours;
- 5-second absolute move distribution:
  - p50 ~0.9543 bps;
  - p90 ~3.5799 bps;
  - p99 ~8.4431 bps;
  - max ~39.0877 bps;
- directional diagnostics:
  - mean signed move ~+0.5803 bps;
  - positive signed-move share ~58.67%;
- tail:
  - >=15 bps absolute moves = 19 across 4 UTC hours;
- classification: `WEAK_DIRECTIONAL_STATE_RARE_TAIL_INSUFFICIENT_STANDALONE_HEADROOM`;
- allowed conclusion: one-sided depth-vacuum onset contains measurable directional information and rare large-move association, but the broad move scale is too small for the frozen standalone two-fill taker mechanism;
- forbidden overclaim: all liquidity-vacuum/replenishment information is useless;
- forbidden reuse: post-hoc tail filtering or threshold tuning under C10-S0.
