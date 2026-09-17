# SC001 Current Roadmap and Stop Rules v4.22

Date: 2026-09-17  
Status: **CURRENT SC001 ROADMAP — C1-C6 CALIBRATION/SENTINEL PLAN FROZEN / IMPLEMENTATION PREFLIGHT NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.21.md`

## 1. Binding terminal states

E001-E008 remain terminal/closed.

E007R1 remains terminal:
`E007R1_GROSS_FEASIBILITY_FAIL`.

E009 remains terminal:
`E009_GROSS_FEASIBILITY_FAIL`.

E009 postmortem remains complete.

No prior strategy is reopened by the new selection/calibration work.

## 2. Binding governance stack

Current entry point:

`docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`

New binding selection-stage artifacts:

- `docs/research/sc001-contamination-registry-v0.4.json`;
- `docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`;
- `docs/research/sc001-selection-research-ledger-v0.1.json`;
- `docs/research/sc001-c1-c6-feature-indicator-inventory-v0.1.md`.

Existing binding companions remain:

- feature/indicator governance/taxonomy/registry;
- incremental feature-testing protocol;
- legacy retest policy;
- strategy landscape;
- candidate-card template v0.2;
- next-generation multi-asset framework v0.3;
- simulation verification/accounting standard v0.1.

## 3. Contamination correction

The old v0.3 registry is now superseded because July Discovery is no longer unopened.

Current known selection/calibration pool is deliberately restricted to already contaminated evidence:

- July 1-14 2024 on BTC/ETH/DOGE/ORDI/UNI/XRP/OP/BCH — E007R1 contaminated;
- September 1-14 2024 on the same eight assets — E009 contaminated;
- March 1-20 2024 BTC spot/perp — legacy E006 contaminated, C1-only supplement.

Protected holdouts/Confirmation and unopened gaps remain closed.

Any additional source downloaded for these already contaminated dates inherits nonpromotional calibration status.

## 4. Frozen screening cost reference

Selection-only regular-user reference:

- 5 bps per taker fill.

Screening gross hurdle:

`1.5 x fee-reference floor`.

Thus:

- two-fill directional sentinel hurdle = 15 bps;
- four-fill paired sentinel hurdle = 30 bps.

These are not exact historical execution claims. Passing only opens deeper cost/spec/L2 work.

## 5. Frozen first-pass variant budget

Exactly 11 first-pass sentinel variants are registered:

- C1: 1;
- C2: 2;
- C3: 2;
- C4: 4;
- C5: 1;
- C6: 1.

No unlogged post-outcome threshold/horizon/indicator additions are permitted.

## 6. Candidate sentinel families

### C1 — E006R1 basis

Strict legacy mechanism, multi-asset calibration. Require meaningful event breadth and >=30 bps idealized contraction headroom before multi-leg engineering.

### C2 — multi-minute mean reversion

Two local-reference representations only. Require >=15 bps cost-relative 10-minute reversion with cross-asset breadth.

### C3 — 5m/10m continuation

Two completed-bar variants only. Require >=15 bps signed continuation and broad multi-asset support.

### C4 — BTC/ETH -> alt lead/lag

Four leader/horizon variants only. Must survive common-factor residual adjustment; raw beta-following alone is not lead/lag evidence.

### C5 — forced-flow exhaustion

One 30s robust flow-event definition. Trade-only first; L2 deferred until event frequency and >=15 bps reversal headroom survive.

### C6 — cross-sectional dispersion/reversion

One simple 5m residual top1/bottom1 -> 15m spread diagnostic. Four-fill screening hurdle = 30 bps.

## 7. MDE/sample planning

Primary planning inference unit is the calendar-day block, not individual events.

For sentinel survivors:

- compute sandbox block SD and robust MAD scale;
- use `sigma_plan = 1.25 * max(sd, 1.4826*MAD)`;
- one-sided planning alpha 0.05, power 0.80;
- `n_req = ceil(((1.645+0.842)*sigma_plan/delta_screen)^2)`;
- `n_plan = max(20, n_req)` active calendar-day blocks.

Too-sparse or prohibitively expensive candidates are deferred rather than rescued by weaker economics.

## 8. Sentinel dispositions

Allowed selection-stage terminals:

- `REJECT_STRUCTURAL`;
- `REJECT_SENTINEL`;
- `DEFER_SAMPLE_INSUFFICIENT`;
- `DEFER_HIGH_SAMPLE_COST`;
- `ELIGIBLE_FOR_BATCH`.

No candidate is called a strategy winner at this stage.

## 9. Batch freeze rule

Only after all C1-C6 have a selection-stage disposition may a small promotional research batch be frozen.

Among credible survivors:

- avoid Pareto-dominated candidates;
- prefer 2-3 candidates spanning multiple mechanisms/horizons/risk signatures where feasible;
- freeze batch order before the first promotional outcome;
- then assign new experiment IDs and fresh Discovery/holdout/Confirmation roles.

## 10. Current hard firewall

**NO NEW PROMOTIONAL ALPHA.**

The next work is implementation of the nonpromotional sentinel stage on the already contaminated sandbox.

Do not access:

- July asset holdout;
- July 16-30 gap;
- August protected period;
- September asset holdout;
- October Confirmation;
- legacy E006 March Confirmation.

## 11. Immediate next implementation step

Before computing any sentinel outcome:

1. build a local data-inventory/preflight runner;
2. verify July and September trade archives/reports are present and match qualified semantic parents;
3. verify legacy E006 March spot/perp artifacts where available;
4. identify C1 July/September spot-source gaps without downloading clean periods;
5. verify NumPy/runtime dependencies;
6. write a preflight report proving no protected date/body was accessed;
7. only after exact preflight PASS implement shared causal bar/return utilities and the six sentinel runners.
