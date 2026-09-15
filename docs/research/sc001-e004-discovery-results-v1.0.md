# SC001-E004 — Discovery Results v1.0

Date: 2026-09-15  
Status: **TERMINAL DISCOVERY FAIL**

Parent financial protocol:

`docs/research/sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`

Implementation freeze:

`docs/research/sc001-e004-implementation-freeze-v1.0.md`

Preflight specification:

`docs/research/sc001-e004-implementation-preflight-spec-v1.1.md`

## 1. Terminal verdict

The frozen SC001-E004 DEV-DISCOVERY run completed with exact terminal token:

`E004_DISCOVERY_FAIL`

Per the frozen stop rule:

- DEV-CONFIRMATION remains unopened;
- E004 L2 acquisition/economics remains blocked;
- Q2 remains closed;
- formal Validation remains closed;
- Final remains closed;
- E004 v1.0 may not be rescue-tuned.

The preflight had previously returned exact `PREFLIGHT_PASS` with matching engine/config/preflight SHA identities and with `alpha_calculated = false`.

## 2. Frozen primary economics result

Primary configuration:

`E004_P_W15_Q20_LB1440_B2_ARM15_LAT250_H15_CAP4`

Observed frozen primary metrics relevant to failed gates:

- pooled mean gross edge: approximately `+0.17935 bps` versus required `>= 20.0 bps`;
- symmetric 10% trimmed mean: approximately `+1.05414 bps` versus required `>= 15.0 bps`;
- pooled median gross edge: approximately `+1.66221 bps` versus required `>= 10.0 bps`;
- median active-day mean gross edge: approximately `-1.75324 bps` versus required `>= 12.0 bps`;
- positive active-day share: approximately `0.473684` versus required `>= 0.70`;
- one-sided 95% day-block-bootstrap lower bound: approximately `-3.93417 bps` versus required `> 10.0 bps`.

The result therefore failed not merely on one robustness condition but on the central magnitude/breadth economics requirements.

## 3. Frozen latency stress

500 ms stress:

- pooled mean gross edge: approximately `+0.12147 bps` versus required `>= 15.0 bps`;
- trimmed mean gross edge: approximately `+1.05733 bps` versus required `>= 10.0 bps`.

1,000 ms stress:

- pooled mean gross edge: approximately `+0.05194 bps` versus required `>= 12.0 bps`;
- trimmed mean gross edge: approximately `+0.94365 bps` versus required `>= 8.0 bps`.

Latency robustness therefore also failed by a very large margin.

## 4. Gates that passed

The visible frozen gate ledger shows that several structural/robustness conditions did pass, including:

- top-one day contribution concentration <= 0.25;
- top-three day contribution concentration <= 0.55;
- each side had at least the minimum required completed-trade count;
- maximum side share <= 0.75;
- hard daily decision cap respected;
- maximum one concurrent position respected.

This matters because the terminal failure is not explained by a single dominant day, severe side imbalance, or a state-machine/turnover invariant breach.

## 5. Failed-gate count

The frozen report showed:

`failed_gate_count = 10`

Failed gates visible in the terminal audit:

1. pooled mean gross edge;
2. trimmed mean gross edge;
3. pooled median gross edge;
4. median daily mean gross edge;
5. positive active-day share;
6. bootstrap lower bound;
7. 500 ms pooled mean;
8. 500 ms trimmed mean;
9. 1,000 ms pooled mean;
10. 1,000 ms trimmed mean.

## 6. Interpretation

E004 is a **gross-mechanism failure**, not an execution-cost failure.

The frozen compression-to-breakout mechanism did not generate post-latency continuation remotely close to the many-bps scale required for a standalone taker strategy. The pooled mean was only a small fraction of one basis point, while the predeclared primary economics hurdle was 20 bps and the regular-user round-trip taker fee reference is about 10 bps before spread/depth deterioration.

The positive pooled median does not rescue the candidate because:

- its magnitude was far below the frozen hurdle;
- median active-day mean was negative;
- fewer than half of active days had positive mean;
- the day-block bootstrap lower bound was negative;
- 500/1,000 ms stress remained near zero.

Therefore this is not a near miss and should not proceed to L2 engineering.

## 7. Relation to E001-E003

E004 reinforces the prior SC001 economics-first lesson:

- E002 showed real predictive microstructure information but standalone executable edge was tiny relative to fees;
- E003 showed that stronger rare flow did not create a large continuation residual;
- E004 now shows that this frozen volatility-compression breakout formulation also failed to create a many-bps post-entry continuation move.

The recurring constraint is not merely statistical detectability. It is obtaining a robust post-decision move large enough to survive real taker economics.

## 8. Read-only diagnostics

The eight one-factor E004 diagnostic variants defined before the primary run may be evaluated only as postmortem research knowledge after this terminal verdict is fixed.

They cannot:

- change `E004_DISCOVERY_FAIL`;
- open Confirmation;
- select a replacement primary E004 rule;
- justify E004 L2 acquisition;
- justify Q2/Validation/Final access;
- rescue E004 through parameter substitution.

Any materially different candidate inspired by diagnostics requires a new experiment identifier and a new pre-alpha freeze.

## 9. E005 boundary

The previously reserved E005 incremental-TFI experiment is **not opened**, because its prerequisite was an independently viable E004 base strategy. That prerequisite failed.

TFI remains preserved only as a future auxiliary feature for some later independently viable base strategy.

## 10. Immediate next action

Run, if desired, the already-predeclared E004 read-only diagnostic neighborhood strictly as postmortem. Then use the combined E001-E004 evidence to choose and freeze a genuinely new SC001 candidate family under a new experiment identifier. Do not retune E004 v1.0.
