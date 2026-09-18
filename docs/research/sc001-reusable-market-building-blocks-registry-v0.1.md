# SC001 — Reusable Market Building Blocks Registry v0.1

Date: 2026-09-18  
Status: **APPEND-ONLY REUSABLE-BLOCK REGISTRY / NO GLOBAL WORKS-DOES-NOT-WORK CLAIMS**  
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.2.md`;
- `docs/research/sc001-c1-c6-five-role-reusable-mechanism-feature-review-v0.1.md`.

## 1. Purpose

Store reusable market-behavior and measurement blocks independently from parent strategy verdicts.

A block is not a strategy. A block may be useful as:

- R1 core signal;
- R2 state/regime;
- R3 filter/veto;
- R4 sizing/risk;
- R5 execution;
- R6 reference/normalization.

Every block remains scoped by market, horizon, evidence stage and role.

## 2. Evidence-strength vocabulary

- `REFERENCE_PRIMITIVE` — useful measurement/reference semantics, no directional claim.
- `STATE_ONLY` — market state is measurable; standalone direction unsupported.
- `WEAK_BROAD_CALIBRATION` — small directional effect with useful breadth on calibration data.
- `MEDIUM_CALIBRATION_HYPOTHESIS` — stronger calibration pattern, still nonpromotional and requiring fresh evidence.
- `NEGATIVE_DIRECTIONAL_EVIDENCE` — tested directional use failed or showed opposite sign.
- `SCARCITY_LIMITED` — event definition too rare to support the tested use.

## 3. Registry

### RB001 — Local-reference deviation state v0.1

- primitives: P1 + P7;
- source evidence: C2 / F010;
- formula family: price or 1m VWAP deviation from causal 5-minute local reference;
- tested horizon: 10-minute response;
- observed calibration behavior: frozen reversion-signed mean approximately -4 bps across both reference variants;
- evidence strength: `MEDIUM_CALIBRATION_HYPOTHESIS`;
- interpretation: large deviation tended to persist away from the reference rather than revert on this calibration set;
- preferred future roles: R2, R3;
- R1 use: new experiment only;
- allowed prospective question: does deviation state veto fading or identify persistence regime?;
- forbidden reuse: flip C2 sign and reuse the same sandbox as proof.

### RB002 — Completed-bar expansion / breakout state v0.1

- primitives: P2 + P3;
- source evidence: C3 / F011;
- formula family: prior-6-bar breakout plus current true range >=1.5x prior-12 median true range;
- tested horizons: 5m->10m and 10m->20m;
- observed calibration behavior: near-zero/slightly negative continuation;
- evidence strength: `STATE_ONLY`;
- preferred future roles: R2, R4, possibly R3;
- allowed prospective question: does expansion state alter the value/risk of an independent signal?;
- forbidden reuse: add auxiliary filters and call it C3 rescue.

### RB003 — Cross-asset leader impulse residual context v0.1

- primitive: P9;
- source evidence: C4 / F012;
- formula family: BTC/ETH 30s/60s robust impulse with common-factor-adjusted alt response;
- observed calibration behavior: residual means broadly positive but approximately +0.38 to +0.67 bps;
- breadth: 5/6 or 6/6 positive target means depending variant;
- evidence strength: `WEAK_BROAD_CALIBRATION`;
- preferred future roles: R2, R3, ranking/timing;
- allowed prospective question: does leader impulse incrementally rank already-valid alt opportunities?;
- forbidden reuse: lag grid or target cherry-picking.

### RB004 — Common-market residualization v0.1

- primitive: P9;
- source evidence: C4 and C6;
- formula family: remove common crypto beta/common-market movement before interpreting relative response;
- evidence strength: `REFERENCE_PRIMITIVE`;
- preferred role: R6;
- reusable rule: raw cross-asset response is not sufficient evidence of information transfer when common beta can explain it;
- expected use: mandatory comparator/normalization in future cross-asset and cross-sectional work where applicable;
- forbidden claim: residualization itself creates alpha.

### RB005 — Extreme aggressive-flow exhaustion state v0.1

- primitives: P5 + P10;
- source evidence: C5 / F013;
- formula family: extreme signed aggressive-notional z-score with same-sign concurrent price move;
- observed calibration behavior: small reversal tendency, median active-asset mean about +0.5 bps, 6/8 positive assets;
- evidence strength: `WEAK_BROAD_CALIBRATION`;
- preferred roles: R2, R3, R5;
- allowed prospective questions:
  - does the state veto late aggressive continuation entries?;
  - does it improve maker/taker choice or exit timing?;
- forbidden reuse: add L2 to C5 and treat as same experiment rescue.

### RB006 — Cross-sectional residual rank / dispersion state v0.1

- primitives: P9 + P1;
- source evidence: C6 / F014;
- formula family: asset 5m return minus equal-weight universe mean, rank extremes;
- observed calibration behavior:
  - 10% trimmed relative spread about +3.00 bps;
  - median about +3.84 bps;
  - positive day share about 71.4%;
  - concentration within frozen limits;
- evidence strength: `MEDIUM_CALIBRATION_HYPOTHESIS`;
- preferred roles: R1 ranking under new mechanism, R3, R4, R6;
- allowed prospective question: does residual rank add value inside a lower-turnover or otherwise materially different relative-value architecture?;
- forbidden reuse: reduce fill count ad hoc and call it C6 rescue.

### RB007 — Continuous spot/perpetual basis state v0.1

- primitive: P8;
- source evidence: C1/F009 plus legacy F003;
- formula family: same-venue spot/perp basis relative to ordinary rolling basis reference;
- tested strict event: +50 bps dislocation;
- observed calibration behavior: zero strict C1 triggers;
- evidence strength: `SCARCITY_LIMITED` for the strict event, `REFERENCE_PRIMITIVE` for continuous basis state;
- preferred roles: R2, R6;
- allowed prospective question: can continuous derivative state inform a materially different scheduled funding/mark/index mechanism?;
- forbidden reuse: lower C1 threshold as direct rescue.

### RB008 — Causal local reference v0.1

- primitives: P7 + optional P4 weighting;
- source evidence: legacy F005 plus C2;
- formula family: VWAP, completed-bar median or other prospectively exact local center;
- evidence strength: `REFERENCE_PRIMITIVE`;
- preferred role: R6;
- reusable rule: a reference price is a baseline measurement, not a directional signal by itself;
- forbidden claim: C2 rejection proves VWAP/median reference is ineffective.

## 4. Existing legacy blocks retained by reference

The following pre-C1-C6 evidence remains important and should be cited when relevant:

- E002/F001 signed aggressive-flow imbalance: predictive support but standalone taker economics failed;
- E008/F006 visible spread/liquidity state: execution/economic feasibility primitive;
- E008/F008 queue-ahead uncertainty: execution scenario feature, not alpha;
- E009/F007 robust volatility normalization: defined measurement; strategy failure did not isolate feature utility.

These are not duplicated as new RB IDs in v0.1; future registry versions may normalize them into the RB namespace if needed.

## 5. Combination policy

RB IDs are not a feature-shopping menu.

A future candidate must:

1. define its economic mechanism first;
2. include the minimum necessary core blocks;
3. state each block's role;
4. cite prior scoped evidence;
5. freeze any auxiliary-block count before outcome;
6. prefer BASE vs BASE + RBxxx incremental tests;
7. preserve all variants in the multiplicity ledger;
8. obtain fresh promotional evidence after selection.

## 6. Suggested metadata for future append

For each new RB record:

- block ID/version;
- parent primitives;
- exact formula/code lineage;
- source experiments;
- market/universe;
- horizon;
- observed effect and breadth;
- evidence strength;
- allowed roles;
- forbidden inference;
- redundancy relationships;
- next falsifiable incremental question;
- contamination/evidence role.

## 7. Current highest-value prospective incremental questions

These are not rankings of strategies; they are high-information feature questions:

- RB005 as an execution/veto feature on a separately valid base opportunity set;
- RB006 as a relative-ranking feature under a materially different low-turnover architecture;
- RB001 as a persistence-state/veto feature rather than automatic mean reversion;
- RB003 as a small cross-asset ranking/confirmation feature;
- RB007 as continuous derivative context for a scheduled derivative-state mechanism.

All remain nonpromotional hypotheses until prospectively tested.
