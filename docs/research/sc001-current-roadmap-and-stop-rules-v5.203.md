# SC001 Current Roadmap and Stop Rules v5.203

Date: 2026-09-29
Status: **B15-P2 P0 LIMITED PRICE+INDEX+BASIS AUTHORIZED / OFFLINE IMPLEMENTATION VALIDATION PENDING**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.202.md`

## Authorization

The user explicitly authorized the exact pre-registered B15-P2 P0 scope.

Execution approval:

`docs/research/sc001-b15p2-p0-price-index-basis-execution-approval-v0.1.json`

SHA256:

`27a4f094767f19a9c992e3b777ceea9b2b1eb5cf12d9b5e6a3230f81e007b7fc`

Authorized outcome-bearing fields are limited to:

- affected Bybit linear perpetual 1-minute close/volume/turnover at the three registered snapshots;
- official Bybit index 1-minute close at the same snapshots;
- derived perpetual-vs-index basis and the already pre-registered P0 aggregates.

Still forbidden:

- returns;
- PnL;
- L1/L2;
- individual trade bodies;
- funding values;
- mark/premium/spot;
- external venue prices;
- alternate-horizon search;
- symbol/threshold selection from outcomes;
- trading/order execution.

## Implementation candidate

Candidate:

`research/sc001/sc001_b15p2_p0_basis_convergence_v0_1.py`

SHA256:

`dc52b2fb4914ea29bc6bc85a9cfc8aa27f327d8dd160e6c4aa9feeab5e328945`

The candidate contains only:

- exact frozen source/spec/clock checks;
- exact registered minute-candle retrieval;
- basis calculation;
- frozen 37-cluster aggregation;
- deterministic bootstrap and pre-registered gates;
- structured output.

No partial public outcome smoke is planned. This is deliberate: after offline validation, the exact implementation will be frozen and the full registered P0 will be executed once, avoiding partial outcome exposure followed by code adaptation.

## Required sequence

1. STATIC REVIEW — PASS.
2. REAL OFFLINE DYNAMIC SELF-TEST through Test Executor.
3. If PASS, freeze exact implementation bytes/SHA.
4. Full registered P0 run through Test Executor `public_research`.
5. Canonicalize structured result.
6. Three-role terminal review.
7. Obey the pre-registered stop rule without rescue-tuning.

## Current firewalls

Authorized but not yet accessed:

- affected-contract prices;
- official Bybit index values;
- basis.

Still CLOSED:

- returns;
- PnL;
- L1/L2;
- trades;
- funding/mark/premium/spot;
- external venue prices;
- trading.

## Next state

`OFFLINE_VALIDATE_P0_IMPLEMENTATION_BEFORE_PRICE_ACCESS`


## Offline iteration 1 diagnostic

First real Test Executor self-test:

- job: `job_20260929T135830Z_c00cff26`;
- profile: `offline`;
- outcome data accessed: NO;
- failure: cluster summary key namespace mismatch;
- diagnostic:
  `docs/research/sc001-b15p2-p0-offline-selftest-failure-diagnostic-v0.1.json`.

Corrected candidate SHA256:

`dc52b2fb4914ea29bc6bc85a9cfc8aa27f327d8dd160e6c4aa9feeab5e328945`

No frozen hypothesis, horizon, threshold, source, or firewall changed.

Next:

`REPEAT_OFFLINE_SELFTEST_CORRECTED_CANDIDATE`
