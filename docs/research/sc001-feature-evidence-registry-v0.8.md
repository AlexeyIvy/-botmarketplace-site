# SC001 — Feature Evidence Registry v0.8

Date: 2026-09-19
Status: **APPEND-ONLY CONTINUATION AFTER C11 FINAL DISPOSITION**
Parent: `sc001-feature-evidence-registry-v0.7.md`

## 1. Inheritance

All prior feature-evidence records remain unchanged and binding.

## 2. New records

### F027 — Scheduled Tier-1 US macro-event movement / risk state

- primitive family: external scheduled event / exogenous information arrival;
- source: C11-S0 + C11-v2 Stage A;
- market: OKX BTC-USDT-SWAP;
- event families: U.S. CPI + Employment Situation;
- roles: R2 / R3 / R5 / R6;
- H1-2025 raw 60s evidence:
  - valid = 12/12;
  - abs 60s move >=20 bps = 11/12;
  - median abs 60s move ~45.26 bps;
- fresh C11-v2 Selection evidence:
  - valid = 24/24;
  - abs residual +1s -> +60s >=20 bps = 14/24;
  - median abs residual ~24.11 bps;
  - CPI breadth >=20 bps = 9/12;
  - Employment breadth >=20 bps = 5/12;
- classification:
  `BROAD_EXOGENOUS_EVENT_MOVEMENT_STATE / NON_DIRECTIONAL`;
- allowed conclusion:
  scheduled CPI/Employment releases are a reproducible high-movement risk regime relative to ordinary SC001 endogenous 1-4 bps effects;
- preferred roles:
  - execution-risk scheduler;
  - temporary risk-mode state;
  - strategy veto/context;
  - external calendar reference;
- forbidden claim:
  the state itself predicts direction or establishes profitable event trading.

### F028 — First causal 1-second impulse sign

- primitive family: immediate post-event price impulse;
- source: C11-v2 Selection Stage B;
- role tested: R1 core direction signal;
- market: OKX BTC-USDT-SWAP;
- chronology: 24-event nonpromotional Selection/Calibration;
- rule:
  - impulse >0 -> LONG;
  - impulse <0 -> SHORT;
  - impulse =0 -> NO_TRADE;
- observations:
  - data-valid = 24/24;
  - actionable = 24/24;
  - median abs first impulse ~1.64 bps;
  - positive signed continuation = 14/24;
  - median signed continuation ~3.63 bps;
  - signed continuation >=20 bps = 6/24;
  - CPI >=20 bps = 3/12;
  - Employment >=20 bps = 3/12;
  - among 14 large residual events, 8 had wrong-or-zero direction and 6 were captured >=20 bps;
- classification:
  `REJECTED_AS_STANDALONE_DIRECTION_EXTRACTOR`;
- allowed conclusion:
  first-1s sign is too weak and too often wrong relative to the residual event movement;
- forbidden reuse:
  - alternate window search on the same chronology;
  - sign flip/reversal rescue;
  - post-hoc CPI/Employment sign rules;
  - lower economic hurdle.
