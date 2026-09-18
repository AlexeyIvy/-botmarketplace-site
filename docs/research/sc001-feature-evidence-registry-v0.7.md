# SC001 — Feature Evidence Registry v0.7

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C12-S0**
Parent: `sc001-feature-evidence-registry-v0.6.md`

## 1. Inheritance

All prior feature-evidence records remain unchanged and binding.

## 2. New records

### F025 — Direct stablecoin cross-parity stress

- primitive family: external parity / spot cross-rate;
- source: C12-S0;
- instrument: USDC-USDT;
- parity anchor: 1.0000;
- role: R2 / R3 / R5 / R6;
- measurement validity: established under qualified H1 D+D1 SPOT semantics;
- frozen stress entry tested: abs deviation >=30 bps after re-arm inside <=10 bps band;
- H1-2025 observed:
  - target days with trades = 181/181;
  - stress episodes = 3;
  - episode dates = 3;
  - episode months = 1;
  - successful <=10 bps band reversion within 30m = 2/3;
  - median gross favorable reversion ~25.94 bps;
  - p75 gross favorable reversion ~29.93 bps;
- classification:
  `RARE_REGIME_CLUSTERED_PARITY_STRESS_WITH_DESCRIPTIVE_REVERSION`;
- allowed conclusion:
  direct stablecoin cross-parity stress is rare and clustered but can be economically large when present;
- forbidden claim:
  66.7% success is a stable probability estimate or the feature is a validated standalone alpha.

### F026 — Parity-band reversion state

- source: C12-S0;
- role tested: R1/R2;
- entry: >=30 bps absolute parity deviation;
- exit/re-arm band: <=10 bps;
- horizon: <=30m;
- sample size: 3 episodes;
- classification:
  `INSUFFICIENT_BREADTH_FOR_STANDALONE_STRATEGY`;
- preferred future role:
  risk/stress context or prospectively defined rare-event candidate on fresh evidence;
- forbidden reuse:
  threshold lowering, active-month selection, famous-date mining, H1 extension to manufacture episode count.
