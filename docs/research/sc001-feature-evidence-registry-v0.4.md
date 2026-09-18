# SC001 — Feature Evidence Registry v0.4

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C8B-S0**
Parent: `sc001-feature-evidence-registry-v0.3.md`

## 1. Inheritance

All prior records remain unchanged and binding.

New evidence role:

`SELECTION_CALIBRATION_ONLY`

## 2. New records

### F017 — Strict-coactive cross-venue raw basis

- primitive family: P8 cross-venue relative state;
- source: C8 D1E/D3/S0;
- universe: OKX BTC-USDT-SWAP vs Bybit BTCUSDT;
- temporal representation: strict coactive 1-second, no carry-forward;
- role: R6 reference / R2 state;
- measurement validity: established;
- sample: 82,024 strict coactive seconds on frozen price-calibration day;
- classification: `REFERENCE_PRIMITIVE`;
- allowed conclusion: same-second cross-venue basis is causally measurable with high timestamp quality when stale carry-forward is excluded;
- forbidden claim: raw basis itself is executable alpha.

### F018 — Causal local cross-venue basis median

- primitive family: P8/P7;
- source: C8B-S0;
- role: R6 normalization;
- definition: median raw cross-venue basis over prior 300 wall-clock seconds, current second excluded, minimum 120 prior coactive observations;
- measurement validity: established;
- baseline-eligible observations: 81,904;
- classification: `REFERENCE_PRIMITIVE`;
- allowed conclusion: local causal basis normalization removes persistent venue offset before evaluating transient dislocation;
- forbidden claim: the baseline creates convergence alpha.

### F019 — Transient cross-venue relative-basis deviation

- primitive family: P8/P9;
- source: C8B-S0;
- role tested: R1/R2 candidate dislocation state;
- sample: 81,904 baseline-eligible seconds over 24 UTC hours;
- observed magnitude:
  - p99 absolute dislocation about 2.4455 bps;
  - maximum absolute dislocation about 20.8001 bps;
  - persistent >=30 bps same-sign two-second episodes: 0;
- classification: `AMPLE_SAMPLE_INSUFFICIENT_PAIRED_HEADROOM`;
- allowed conclusion: on the frozen BTC OKX/Bybit calibration day, transient same-second trade-price basis deviations were overwhelmingly far below a conservative four-fill paired threshold;
- forbidden overclaim: all cross-venue information transfer or all cross-venue execution features are useless;
- future rule: no threshold/persistence/baseline rescue under C8B-S0.
