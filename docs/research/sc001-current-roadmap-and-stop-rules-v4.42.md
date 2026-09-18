# SC001 Current Roadmap and Stop Rules v4.42

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9-S1 TERMINAL REJECT / FEATURE KNOWLEDGE RETAINED / C8-D0 NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.41.md`

## 1. Binding terminal states

Prior terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 is now terminal:

`C9_S1_REJECT_SENTINEL`

No C9-S1 rescue tuning is authorized.

## 2. C9-S1 execution/result integrity

Technical completion:

- exit code 0;
- pooled events 712;
- 89 events per each of 8 assets;
- positive funding observations 490;
- negative funding observations 222;
- 30 calendar days;
- all sample/sign-breadth gates passed.

Therefore C9-S1 rejection is not a sample-scarcity result.

## 3. C9-S1 economic result

Observed:

- pooled 10% trimmed mean about -0.0916 bps;
- pooled median 0.0 bps;
- equal-weight asset mean about -0.0722 bps;
- median asset mean about +0.0629 bps;
- positive asset count 5/8;
- equal-weight calendar-day mean about -0.0776 bps;
- positive calendar-day share about 46.7%.

All frozen economic gates failed.

Primary failure class:

`AMPLE_SAMPLE_NO_POST_FUNDING_PREMIUM_NORMALIZATION_EDGE`

## 4. C9 evidence outputs

Binding strategy postmortem:

`docs/research/sc001-c9-s1-sentinel-result-readonly-postmortem-v0.1.md`

Current feature registry:

`docs/research/sc001-feature-evidence-registry-v0.3.md`

Current reusable-block registry:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.2.md`

Current strategy landscape:

`docs/research/sc001-strategy-landscape-v0.3.md`

## 5. Reusable C9 conclusions

Retain:

- RB009 scheduled funding-event context as state-only / negative directional evidence in the tested role;
- RB010 mark/index premium as R6/R2 reference/state primitive;
- no global claim that funding or mark/index state is useless.

Do not:

- add a funding threshold;
- choose only one funding sign;
- change horizon;
- add basis/volatility/flow filters;
- select winner assets;
- change execution architecture to rescue C9-S1.

## 6. October funding contamination remains binding

October 2024 funding bodies were opened by the D1 v0.2 implementation incident.

Therefore October funding cannot be clean C9 Confirmation evidence.

October trade/SPOT/L2/mark/index channels remain separately governed.

## 7. C9 MDE consequence

There is no C9-S1 survivor.

Therefore:

- no C9-S1 MDE planning;
- no promotional C9-S1 Discovery;
- no exact spot/perp execution build for this mechanism.

## 8. Next frozen research direction

Return to next-slate sequence:

`C8 — CROSS-VENUE SAME-ASSET DATA / CLOCK AUDIT`

Current parent plan:

`docs/research/sc001-c8-cross-venue-data-clock-audit-plan-v0.1.md`

C8-D0 must remain no-alpha.

## 9. C8-D0 requirements before any outcome

Freeze and verify:

- exact venue pair;
- exact same-asset contract/instrument mapping;
- source archive/API identities;
- timestamp unit and meaning;
- chronological ordering;
- duplicate/out-of-order rules;
- day/archive boundaries;
- deterministic causal synchronization;
- staleness tolerance semantics;
- expected data volume.

Do not calculate:

- cross-venue returns;
- price dislocations;
- lag performance;
- lead/lag direction;
- strategy signals;
- PnL.

## 10. Immediate next action

Verify current public historical source contracts for OKX and Bybit, then freeze and implement C8-D0 source/clock semantics probe.

No VPS alpha run is authorized until C8-D0 implementation is frozen.
