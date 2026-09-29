# SC001 Current Roadmap and Stop Rules v5.204

Date: 2026-09-29
Status: **B15-P2 P0 IMPLEMENTATION FROZEN AFTER OFFLINE PASS / FULL REGISTERED OUTCOME RUN NEXT**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.203.md`

## Offline engineering gate

Initial candidate self-test failed before any outcome access because of a cluster-summary key namespace mismatch.

Diagnostic:

`docs/research/sc001-b15p2-p0-offline-selftest-failure-diagnostic-v0.1.json`

The correction changed only the three cluster-summary lookup keys and added regression assertions. No source, horizon, metric, threshold, weighting, hypothesis, or firewall changed.

Corrected Test Executor job:

`job_20260929T140157Z_aa541296`

Result:

`B15P2_P0_BASIS_CONVERGENCE_V01_SELF_TEST_PASS`

Network profile:

`offline`

Price/index/basis accessed in self-test:

**NO**

## Exact frozen implementation

Path:

`research/sc001/sc001_b15p2_p0_basis_convergence_v0_1.py`

SHA256:

`dc52b2fb4914ea29bc6bc85a9cfc8aa27f327d8dd160e6c4aa9feeab5e328945`

Implementation freeze:

`docs/research/sc001-b15p2-p0-implementation-freeze-v0.1.json`

SHA256:

`8e4af2f3195a08265a8eaa9fed8092f22dfa78aba8b1988d7bfa8018c3e9f33b`

No further implementation mutation is allowed before the full registered P0 outcome run.

## Full P0 authorized scope

Authorized:

- Bybit affected-contract 1m close/volume/turnover at T-55, T-30, T-5;
- official Bybit index 1m close at the same snapshots;
- derived basis and frozen P0 aggregation.

Still CLOSED:

- returns;
- PnL;
- L1/L2;
- individual trades;
- funding;
- mark/premium/spot;
- external venue price;
- alternate horizon/symbol/threshold search;
- trading.

## Execution rule

Do not run a partial outcome smoke.

Run the exact frozen P0 once through Test Executor `public_research`, then canonicalize the structured result and obey the registered verdict without rescue-tuning.

## Operational note

Test Executor enforces a hard limit of 3 launches per rolling hour. The corrected offline PASS filled the currently available third slot. Full P0 execution must wait until one earlier launch ages out of the rolling-hour window; this does not change research scope or implementation.

## Next state

`WAIT_FOR_TEST_EXECUTOR_RATE_SLOT_THEN_RUN_FULL_FROZEN_P0`
