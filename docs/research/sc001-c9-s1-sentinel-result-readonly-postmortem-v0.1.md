# SC001 — C9-S1 Sentinel Result & Read-Only Postmortem v0.1

Date: 2026-09-18  
Status: **C9_S1_REJECT_SENTINEL — SAMPLE ADEQUATE / ECONOMIC EFFECT ~0**  
Scope: `SCALPING RESEARCH / SC001`

## 1. Execution integrity

Exact terminal state:

`C9_S1_REJECT_SENTINEL`

Technical completion:

- exit code: `0`;
- implementation did not fail;
- event universe remained frozen;
- no threshold/horizon/side optimization occurred;
- no protected/promotional alpha was accessed.

## 2. Frozen sample result

Observed:

- pooled event count: `712`;
- per-asset events: `89` for each of 8 assets;
- positive-funding observations: `490`;
- negative-funding observations: `222`;
- active calendar days: `30`.

All sample/sign-breadth gates passed.

Therefore C9-S1 did not fail because of sparse events, missing sign coverage, or insufficient calendar breadth.

## 3. Economic result

Observed signed post-funding mark/index normalization:

- pooled 10% trimmed mean: about `-0.0916 bps`;
- pooled median: `0.0 bps`;
- equal-weight asset mean: about `-0.0722 bps`;
- median asset mean: about `+0.0629 bps`;
- positive asset means: `5/8`;
- equal-weight calendar-day mean: about `-0.0776 bps`;
- positive calendar-day share: about `46.7%`.

All frozen economic gates failed.

The observed effect is effectively zero relative to the `30 bps` four-fill screening hurdle.

## 4. Mechanism conclusion

Primary failure class:

`AMPLE_SAMPLE_NO_POST_FUNDING_PREMIUM_NORMALIZATION_EDGE`

The frozen hypothesis:

- positive funding -> subsequent mark/index premium normalization downward;
- negative funding -> subsequent mark/index premium normalization upward;
- 30-minute horizon;

did not show economically meaningful calibration support.

No funding-rate threshold, sign selection, horizon change, basis filter, volatility filter, or asset subset may be introduced as C9-S1 rescue.

## 5. Feature-level interpretation

The strategy rejection does not invalidate the underlying measurements.

### Funding sign / scheduled funding clock

- measurement validity: established;
- event frequency: high;
- both signs present;
- standalone 30-minute directional normalization value: not supported.

Preferred future interpretation:

`STATE_ONLY / NEGATIVE_DIRECTIONAL_EVIDENCE_IN_THIS_ROLE`

### Mark/index premium

- measurement validity: established;
- synchronized 15m data quality: high;
- standalone scheduled post-funding normalization direction: unsupported;
- R6 reference/state role remains valid.

### Causal reference semantics

RB008 remains valid as methodology/reference infrastructure.

## 6. Important statistical reading

The pooled sample is large, but events are not IID.

Still, the mechanism is not near the economic hurdle:

- effect scale is around tenths of a basis point;
- hurdle is tens of basis points.

Therefore additional inference sophistication cannot plausibly bridge the economic gap for this exact frozen mechanism.

## 7. Edge-to-fill lesson

C9-S1 reinforces the SC001 second-pass lesson:

A valid scheduled market-state feature can be measurable and frequent while providing essentially no gross directional edge under a four-fill paired architecture.

Do not spend further engineering effort on exact spot/perp execution for this C9-S1 mechanism.

## 8. Evidence disposition

C9-S1:

`REJECT_SENTINEL`

No MDE/promotional batch planning is required.

C9 as a broad research family is not globally invalidated, but any materially different funding/carry mechanism requires a new candidate ID and prospective design.

## 9. Next research action

Return to the frozen next-slate sequence.

Next orthogonal direction:

`C8 — cross-venue same-asset data / clock audit`

Start with no-alpha source/timestamp compatibility only.

Do not open cross-venue dislocation outcomes until clock semantics are frozen.
