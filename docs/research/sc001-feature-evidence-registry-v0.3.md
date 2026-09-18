# SC001 — Feature Evidence Registry v0.3

Date: 2026-09-18  
Status: **APPEND-ONLY CONTINUATION AFTER C9-S1**  
Parent: `sc001-feature-evidence-registry-v0.2.md`

## 1. Inheritance rule

All records in v0.1 and v0.2 remain unchanged and binding.

This version appends scoped C9 Selection/Calibration evidence only.

Evidence role:

`SELECTION_CALIBRATION_ONLY`

## 2. New records

### F015 — Funding-sign scheduled-event state

- primitive family: P8 + P11;
- role tested: R2 state + R1 event-direction input;
- candidate: C9-S1;
- market/universe: OKX BTC/ETH/DOGE/ORDI/UNI/XRP/OP/BCH USDT perpetuals;
- event set: all nonzero September 2024 funding events;
- horizon: 30 minutes;
- sample: 712 pooled observations, 89 per asset, 30 calendar days;
- sign breadth: 490 positive-funding, 222 negative-funding observations;
- observed signed normalization:
  - trimmed mean about -0.0916 bps;
  - median 0.0 bps;
  - equal-weight asset mean about -0.0722 bps;
  - equal-weight day mean about -0.0776 bps;
- classification: `NEGATIVE_DIRECTIONAL_EVIDENCE_IN_TESTED_ROLE`;
- allowed reusable conclusion: funding sign and scheduled funding clock are valid causal state variables, but the frozen 30-minute post-funding mark/index normalization direction showed essentially zero economic effect;
- forbidden overclaim: funding state is globally useless;
- future rule: no post-hoc funding threshold, sign-side selection, or horizon tuning under C9-S1.

### F016 — Mark/index premium as causal derivative-state reference

- primitive family: P8 + P7;
- role tested: R6 reference/state;
- candidate: C9-S1 / C9-D2;
- data quality: synchronized 15m mark/index tape with 2976 aligned rows per asset;
- measurement validity: established;
- tested directional use: scheduled 30-minute post-funding normalization;
- directional result: unsupported / effect ~0;
- classification: `REFERENCE_PRIMITIVE_DIRECTIONAL_USE_FAILED`;
- allowed reusable conclusion: mark/index premium is a valid causal derivative-state measurement/reference, but this specific scheduled normalization rule did not create material alpha;
- forbidden overclaim: mark/index premium has no value in carry, risk, execution, or other prospectively defined roles.

## 3. Cross-record lesson

C9 demonstrates that a structurally meaningful scheduled market variable can be frequent and well-measured while containing no useful directional edge in the tested horizon/role.

This strengthens the registry rule:

`measurement validity != directional information != economic viability`.
