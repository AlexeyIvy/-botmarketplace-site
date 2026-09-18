# SC001 — N2 Relative Ranking with One-Sided Execution Feasibility Card v0.1

Date: 2026-09-18
Status: **NON-ALPHA FEASIBILITY CARD / NO EXPERIMENT ID**
Template: `sc001-candidate-feasibility-card-template-v0.2.md`

## 1. Identity

- candidate ID: **NOT ASSIGNED**
- short name: `N2_RELATIVE_RANK_ONE_SIDED`
- relationship to prior SC001 experiments: uses RB006 residual rank information from C6
- why this is not rescue tuning requirement: any future architecture must be materially distinct from C6 four-fill top-vs-bottom round trip
- mechanism family: cross-sectional relative ranking
- execution archetype: one-sided decision only
- Signal Horizon: ~15m ranking state
- Position Horizon: must be prospectively defined by new base mechanism

## 2. Economic mechanism

Observed reusable information:

RB006 showed low-single-digit positive cross-sectional reversion tendency with good day breadth.

Potential economic use:

Use residual rank to choose **which single instrument** receives an already-required directional allocation/hedge/rebalance, instead of opening both long and short legs solely to monetize rank.

Who pays for edge:

Cross-sectional relative normalization may improve selection among actions that would occur anyway.

Main falsification:

If ranking does not improve an independently defined one-sided base decision versus a predeclared neutral selector, stop.

## 3. Time architecture

- feature resolution: inherited from RB006 reference implementation
- signal lookback: causal common-factor residualization
- decision cadence: tied to future base opportunity
- no same-window future information
- hold/max hold: not yet frozen

## 4. Feature inventory

Core auxiliary:

- RB004 common-market residualization;
- RB006 residual rank.

No additional predictive feature in first experiment.

RB004 is methodological normalization, not a second alpha block.

## 5. Risk signature

Primary concern:

Removing the paired short/long leg creates directional beta and idiosyncratic risk.

Therefore a future N2 base must independently justify why one-sided exposure already exists.

If one-sided exposure is created only to make C6 cheaper, N2 is a disguised rescue and must be rejected.

## 6. Execution economics

- desired incremental fills due to ranking: `0`
- target architecture: choose among fills already required by base
- observed rank information scale: roughly `2-4 bps`
- Edge-to-Fill classification: `PLAUSIBLE_IF_NO_NEW_FILL_AND_BASE_EXPOSURE_EXISTS`

If N2 itself creates entry+exit solely because of RB006:

`STRUCTURALLY_RISKY / C6_RESCUE_RISK`.

## 7. Universe and breadth

Use a frozen liquid cross-asset universe.

No historical winner subset.

Asset holdout required in any future experiment.

## 8. Data and causality

Existing data/tooling sufficient for rank measurement.

Fresh outcome evidence required.

C6 calibration sandbox is nonpromotional for RB006 reuse.

## 9. Selection/Calibration sandbox

Allowed first-stage question:

Does residual rank improve selection among a fixed denominator of one-sided base opportunities?

Forbidden:

- rank cut grid;
- hold grid;
- top-k grid;
- long-only versus short-only winner selection after output.

## 10. Sample design

Use day blocks and asset breadth.

Primary denominator:

base opportunities, not only selected trades.

## 11. Null/matched diagnostic

Pre-register:

- neutral/random selector with same opportunity count;
- optionally common-beta-only selector.

## 12. Cheapest sentinel falsification

Cannot be finalized until an independent one-sided base opportunity is defined.

Future kill condition should test incremental selection value without changing total structural fills.

## 13. Structural feasibility gates

Pass:

- measurement validity;
- observed directional rank information;
- existing data availability.

Blocker:

`NO_INDEPENDENT_ONE_SIDED_BASE_EXPOSURE_DEFINED`.

Additional hard gate:

Must prove architecture is not simply C6 with one leg removed post hoc.

## 14. Engineering plan if later selected

- reusable residualization module;
- fixed rank transform;
- base-opportunity denominator;
- matched selector;
- paired incremental evidence.

## 15. Incremental feature test

Required:

`BASE_SELECTOR vs BASE_SELECTOR + RB006_RANK`

Metrics:

- effect per original opportunity;
- effect per selected opportunity;
- exposure/beta change;
- turnover;
- tail risk.

## 16. Promotion / stop rules

Do not promote merely because rank reproduces C6's sign.

Must demonstrate incremental value under a genuinely distinct one-sided base architecture.

## 17. Evidence-registry update

Append scoped rank-role evidence.

## 18. Candidate disposition

`HOLD_INFORMATION_VALUE`

Reason:

N2 has the strongest reusable directional evidence, but currently lacks an independent base exposure and has the highest hidden-C6-rescue risk.
