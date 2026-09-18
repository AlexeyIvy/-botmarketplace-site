# SC001 — C8B-S0 Structural Headroom Result & Read-Only Postmortem v0.1

Date: 2026-09-18
Status: **C8B_S0_REJECT_HEADROOM — SAMPLE ADEQUATE / RAW CROSS-VENUE HEADROOM INSUFFICIENT**
Scope: `SCALPING RESEARCH / SC001`

## 1. Execution integrity

Exact terminal state:

`C8B_S0_REJECT_HEADROOM`

Technical completion:

- exit code: `0`;
- implementation completed normally;
- frozen strict-coactive representation preserved;
- frozen 5-minute causal median baseline preserved;
- frozen 30 bps headroom hurdle preserved;
- frozen 2-second persistence rule preserved;
- no convergence outcome calculated;
- no return/lag/PnL calculated;
- no promotional alpha accessed.

## 2. Sample result

Observed:

- strict coactive seconds: `82,024`;
- baseline-eligible seconds: `81,904`;
- baseline-eligible UTC hours: `24`.

All sample gates passed.

Therefore C8B-S0 did not fail because of insufficient synchronized data.

## 3. Structural headroom result

Observed:

- persistent qualifying episodes: `0`;
- persistent episode UTC hours: `0`;
- p99 absolute relative-basis dislocation: about `2.4455 bps`;
- maximum absolute dislocation: about `20.8001 bps`.

Frozen structural screen:

- four structural fills;
- 5 bps per-fill reference;
- 20 bps fee-reference floor;
- 30 bps gross headroom hurdle;
- persistence required for two consecutive wall-clock seconds.

All headroom gates failed.

## 4. Mechanism conclusion

Primary failure class:

`AMPLE_SAMPLE_NO_PAIRED_CROSS_VENUE_STRUCTURAL_HEADROOM`

The exact C8B mechanism:

- OKX BTC-USDT-SWAP vs Bybit BTCUSDT;
- strict same-second coactivity;
- last trade within active second;
- 5-minute causal median cross-venue basis;
- transient relative-basis deviation;
- paired four-fill convergence architecture;

does not show raw dislocation magnitude/frequency remotely sufficient to justify later convergence/execution work on the frozen calibration day.

The gap is structural:

- p99 is only ~2.45 bps;
- maximum is only ~20.8 bps;
- no persistent >=30 bps episode exists.

Therefore later bid/ask, legging, slippage, convergence and PnL modeling cannot rescue this exact C8B architecture.

## 5. No-rescue rule

Do not:

- lower 30 bps;
- shorten persistence to one second;
- change the 5-minute baseline;
- lower the 120-observation baseline requirement;
- choose only one spread sign;
- change asset/date/venue pair;
- add volatility/flow filters;
- switch to C8A directional lead/lag as a C8B rescue.

A directional cross-venue information-transfer mechanism would require a new independent candidate/experiment ID and prospective design.

## 6. Feature-level interpretation

The strategy-level rejection does not invalidate the measurements.

Retain:

### Cross-venue raw basis
- valid R6/R2 market-state measurement;
- stable under strict coactive-second representation.

### Causal local cross-venue basis
- valid R6 normalization/reference;
- useful for separating persistent venue basis from transient deviations.

### Transient relative-basis deviation
- measurement valid;
- observed magnitude overwhelmingly low-single-digit bps;
- insufficient for four-fill paired convergence;
- may still be useful as a descriptive execution/reference feature under a separately motivated future mechanism.

## 7. Statistical/economic reading

The sample is extremely large relative to the economic conclusion.

No sophisticated confidence interval is needed to explain the main failure:

- p99 ~2.45 bps;
- hurdle 30 bps.

The order-of-magnitude gap makes the economic conclusion robust for this frozen mechanism.

## 8. Evidence disposition

C8B-S0:

`REJECT_HEADROOM`

No convergence test.
No quote/execution test.
No MDE planning.
No promotional batch.

## 9. Next research action

Return to the orthogonal next-slate sequence.

Next direction:

`C10 — L2 LIQUIDITY-VACUUM / REPLENISHMENT EVENT`

Use the already-qualified BTC OKX L2 only for a prospectively defined nonpromotional structural pilot, independent of C5 aggressive-flow labels.

Do not reuse C8B as a neighboring threshold search.
