# SC001 — C1-C6 Five-Role Reusable Mechanism / Feature Review v0.1

Date: 2026-09-18  
Status: **READ-ONLY MULTI-ROLE SYNTHESIS / SELECTION_CALIBRATION_ONLY**  
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c1-c6-sentinel-batch-results-readonly-postmortem-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.2.md`;
- `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
- `docs/research/sc001-feature-indicator-taxonomy-v0.1.md`.

This document does not rescue C1-C6 and does not create promotional evidence. Its purpose is to preserve useful market-behavior information contained inside failed strategies.

---

## 1. Executive principle

A strategy can fail for at least four different reasons:

1. the economic mechanism is absent;
2. the mechanism exists but is too weak relative to costs;
3. the mechanism is real but the chosen execution architecture is too expensive;
4. the feature measures useful market state, but was assigned the wrong role as a standalone alpha signal.

Therefore strategy verdict and feature verdict must be separated.

The C1-C6 batch provides several reusable **calibration-level building blocks** even though all six strategy candidates were rejected.

---

# 2. Financial / economic expert review

## 2.1 Dominant lesson: effect magnitude matters more than event count

C2-C6 all produced large samples. The key failures were not lack of observations but lack of economic headroom.

Observed gross effect scales:

- C2 local-reference reversion: approximately -4 bps in the reversion direction;
- C3 breakout continuation: approximately 0 bps;
- C4 cross-asset residual response: roughly +0.4 to +0.7 bps;
- C5 forced-flow exhaustion: roughly +0.5 bps;
- C6 cross-sectional reversion: roughly +2 to +4 bps;
- C1 strict basis dislocation: effectively no event set.

This suggests a strategic shift for future SC001 work:

> prioritize mechanisms where the economic source can plausibly generate tens of bps or reduce structural execution cost, rather than repeatedly searching for sub-bps directional prediction.

## 2.2 Weak information can still be valuable if it reduces cost or risk

A +0.5 bps predictive feature is not useful as a standalone two-fill taker strategy against a 15 bps structural screen.

The same feature may still be economically valuable if it:

- vetoes a high-cost bad entry;
- improves maker/taker choice;
- reduces adverse selection;
- improves ranking among already-valid opportunities;
- improves exit timing;
- reduces turnover;
- improves hedge selection;
- changes risk sizing without adding fills.

Thus C4/C5/C6 should be retained primarily as **auxiliary information candidates**, not standalone alpha mechanisms.

## 2.3 C6 has the strongest reusable economic signal of C1-C6

C6 showed:

- positive 10% trimmed spread about +3.0 bps;
- median spread about +3.84 bps;
- positive day share about 71.4%;
- acceptable long/short contribution concentration.

This was nowhere near the frozen four-fill 30 bps hurdle, so the strategy was correctly rejected.

But among C1-C6, C6 is the strongest candidate for future reuse as a **relative-value state/ranking feature** if a genuinely new execution architecture can use the information without recreating the same four-fill C6 strategy.

That future use requires a new experiment ID and fresh evidence.

---

# 3. Trader review

## 3.1 C2: large deviation from local reference behaved more like persistence than reversion

C2 explicitly signed the outcome in the direction of reversion toward the local reference.

Both variants produced negative mean signed reversion:

- C2-A about -3.96 bps;
- C2-B about -4.28 bps.

Therefore, on this calibration sample, large multi-minute deviation from a local reference tended on average to continue **away** from the reference over the next 10 minutes rather than revert.

This does not authorize flipping C2 into a momentum strategy using the same evidence.

But it creates a reusable prospective hypothesis:

`LOCAL_REFERENCE_DEVIATION_PERSISTENCE_STATE`

Possible future roles:

- R2 trend/persistence state;
- R3 veto against fading a large deviation;
- R1 only under a new prospectively frozen continuation experiment.

Practical trader implication:

> a large local-reference deviation may be more useful as a warning not to fade price mechanically than as an entry trigger for mean reversion.

## 3.2 C3: breakout + range expansion is not enough by itself

C3 produced thousands of events but essentially no directional continuation edge.

Useful conclusion:

- breakout/range expansion can still identify a high-movement regime;
- it should not be treated as sufficient direction by itself in the tested construction.

Potential future roles:

- R2 volatility/trend regime;
- R4 sizing/risk state;
- R3 condition on another independently motivated signal.

Do not interpret C3 as evidence that ATR/true range or breakout state is useless.

## 3.3 C4: leader impulse carries weak information but not taker-scale alpha

Residual responses were broadly positive across targets, especially for ETH-leader variants, but sub-1-bps.

Trader use candidate:

`CROSS_ASSET_LEADER_IMPULSE_CONTEXT`

Potential roles:

- R2 market information-transfer state;
- R3 confirmation/veto;
- ranking feature among already-valid alt opportunities;
- R5 timing feature only if separately validated.

Important: common-factor adjustment must remain mandatory. Raw positive response alone can be ordinary crypto beta.

## 3.4 C5: extreme flow event may be an anti-chase signal

C5 showed approximately +0.5 bps reversal on average after extreme signed aggressive flow plus same-direction price movement, with 6/8 assets positive.

This is too small for standalone trading.

But from a trader perspective, the useful rule is:

> after an extreme aggressive-flow burst with concurrent same-sign price displacement, blindly joining the move may face a small but broad short-horizon exhaustion tendency.

Prospective roles:

- R3 veto against late aggressive continuation entry;
- R5 execution aggressiveness/timing;
- R2 forced-flow state;
- possibly exit timing for an existing position.

This is a stronger reuse case than treating C5 as a failed alpha signal.

## 3.5 C6: residual rank is a potentially useful relative-state signal

The cross-sectional top/bottom residual construction had positive day breadth and several bps of gross spread.

Useful market behavior:

> extreme relative under/over-performance within the liquid crypto basket showed a weak tendency to compress over the next 15 minutes.

Potential roles:

- R1 relative-value ranking under a new lower-cost mechanism;
- R6 residual normalization;
- R4 portfolio/hedge adjustment;
- R3 veto against adding exposure to already-extreme relative moves.

Again, this is not permission to redesign C6 after the fact.

---

# 4. Programmer / systems review

## 4.1 Features should become reusable modules, not strategy-specific code

The following primitives should be preserved as versioned functions/interfaces:

1. causal local reference:
   - aggregate VWAP;
   - median of completed minute VWAPs;
2. deviation from local reference;
3. completed-bar true range / expansion ratio;
4. causal cross-asset leader return;
5. pre-event common-factor beta and residualization;
6. signed aggressive notional;
7. robust z-score of aggressive flow;
8. cross-sectional common-factor residual rank;
9. continuous spot/perp basis and ordinary-basis reference.

Each should expose:

- exact inputs;
- update timestamp;
- warm-up;
- missing-data behavior;
- output role;
- version.

## 4.2 Do not encode strategy verdict into feature code

Example:

`deviation_bps()`

should calculate a causal measurement.

It should not contain:

- C2's 30 bps trigger;
- mean-reversion direction;
- C2's 10-minute hold.

Similarly:

`signed_aggressive_notional_z()`

should not contain C5's reversal rule.

This separation lets the same measurement be tested prospectively in another role without silently recreating the failed strategy.

## 4.3 Reusable infrastructure already validated

The shared causal utility layer has Golden PASS for:

- half-open bars;
- completed-bar availability;
- causal trailing windows;
- no future mutation;
- deterministic non-overlap;
- D+D1 filtering;
- return arithmetic;
- signed aggressive-notional arithmetic.

Future feature modules should depend on that layer rather than reimplement clocks independently.

## 4.4 Add provenance to every building block

Every future candidate should log, for each feature:

`building_block_id -> feature_version -> code/hash -> role -> parameterization -> evidence source`.

This makes it possible to know whether a future strategy is genuinely new or quietly reusing/tuning a failed component.

---

# 5. Mathematical review

## 5.1 Sign inversion in C2 is information

C2 was constructed so positive outcome = movement toward the reference.

A negative mean therefore contains directional information: the conditional expectation on this calibration set pointed away from the reference.

Mathematically, that means the tested feature is not simply “noisy”; its conditional first moment had the opposite sign of the hypothesis.

However:

- magnitude is only ~4 bps;
- this was discovered on calibration data;
- changing sign after observing it is a new hypothesis.

Therefore record the sign, but require fresh evidence before using it as R1.

## 5.2 Residualization in C4 is a reusable decomposition

C4 separates:

`target move = beta * common crypto move + residual move`.

This decomposition is valuable independently of whether C4 was profitable.

It prevents a common mathematical error: mistaking synchronized beta exposure for information transfer.

Reusable rule:

> any future cross-asset lead/lag claim should demonstrate effect in residual space, not only raw return space.

## 5.3 C6 illustrates signal-vs-architecture decomposition

C6's relative spread was positive but much smaller than the four-fill hurdle.

Thus:

`observed relative-value signal > 0`

does not imply:

`four-fill paired strategy EV > 0`.

This is a useful decomposition:

`strategy economics = informational edge - execution architecture burden`.

A future mechanism may reuse the informational state only if the new execution structure is scientifically distinct and prospectively frozen.

## 5.4 Continuous features may be more reusable than thresholded events

C1's +50 bps event had zero triggers, but the continuous quantities remain well-defined:

- spot/perp basis;
- ordinary rolling basis reference;
- basis deviation.

The failed threshold is not evidence that the continuous P8 state is meaningless.

For future derivative-state work, continuous state may be used as R2/R6 under a new mechanism, while the +50 bps C1 trigger remains terminal.

---

# 6. Statistical review

## 6.1 Do not use raw event count as IID evidence

C4/C5 have thousands of observations, but crypto assets and intraday events share shocks.

Future evidence about reusable blocks should continue to use:

- calendar-day blocks;
- asset breadth;
- paired base-vs-feature differences;
- cluster/block-aware uncertainty.

Do not claim high confidence merely from 10,000 event rows.

## 6.2 Breadth is useful even when effect is small

C4/C5/C6 showed useful breadth patterns:

- C4 residual positive on 5/6 or 6/6 targets depending variant;
- C5 6/8 positive asset means;
- C6 ~71.4% positive days and acceptable concentration.

This supports the statement:

`weak effect is not driven solely by one asset/day`.

It does **not** support:

`profitable alpha exists`.

That distinction should be retained in the registry.

## 6.3 C2 is especially informative because both parameterizations agree

Two different local-reference representations produced the same qualitative conclusion:

- large sample;
- full asset/day coverage;
- negative signed reversion.

Because the two transforms are related, they are not independent replications, but their agreement reduces the chance that the result is a trivial artifact of one reference definition.

This makes `local-reference deviation state` worth preserving as a prospective feature family, while preserving the rule that the reversed continuation hypothesis requires new evidence.

## 6.4 Incremental testing is now the right tool for weak blocks

For C4/C5/C6-like weak features, standalone strategy tests are likely wasteful.

Better future question:

`BASE` vs `BASE + BLOCK_X`

with the same base opportunities and block-aware comparison.

For a veto/filter, always report:

- retained opportunity share;
- effect per retained trade;
- effect per original opportunity;
- turnover change;
- tail/risk change.

This is the statistically clean way to learn whether a weak standalone feature adds value inside a stronger mechanism.

---

# 7. Reusable building blocks identified

The following are retained as prospective reusable blocks:

### RB001 — Local-reference deviation state

Parents: P1 + P7.  
Evidence source: C2 / F010.  
Observed calibration behavior: large deviation showed continuation rather than reversion on average.  
Preferred future roles: R2, R3; R1 only under new experiment.  
Strength: **medium calibration signal, economically insufficient standalone**.

### RB002 — Completed-bar expansion / breakout state

Parents: P2 + P3.  
Evidence source: C3 / F011.  
Observed behavior: no meaningful standalone direction.  
Preferred roles: R2, R4, possible R3.  
Strength: **state descriptor; directional value not established**.

### RB003 — Cross-asset leader impulse residual context

Parents: P9.  
Evidence source: C4 / F012.  
Observed behavior: broad positive residual response, sub-1-bps.  
Preferred roles: R2, R3, ranking/timing.  
Strength: **weak but broad calibration information**.

### RB004 — Common-market residualization

Parents: P9 / R6.  
Evidence source: C4 and C6.  
Observed value: separates common beta from relative information.  
Preferred role: R6 mandatory normalization for cross-asset/relative-value work.  
Strength: **methodological building block, not standalone alpha**.

### RB005 — Extreme aggressive-flow exhaustion state

Parents: P5 + P10.  
Evidence source: C5 / F013.  
Observed behavior: small broad reversal tendency.  
Preferred roles: R2, R3, R5.  
Strength: **weak but broad calibration information**.

### RB006 — Cross-sectional residual rank / dispersion state

Parents: P9 + P1.  
Evidence source: C6 / F014.  
Observed behavior: low-single-digit positive relative-reversion tendency with good day breadth.  
Preferred roles: R1 ranking under a new mechanism, R3, R4, R6.  
Strength: **strongest reusable directional block from C1-C6, still insufficient standalone economics**.

### RB007 — Continuous spot/perp basis state

Parents: P8.  
Evidence source: C1/F009 plus legacy F003.  
Observed behavior: strict +50 bps event too scarce; continuous state remains measurable.  
Preferred roles: R2, R6; possible input to a materially different derivative-state mechanism.  
Strength: **measurement valid; strict event alpha unsupported**.

### RB008 — Causal local reference

Parents: P7/P4.  
Evidence source: F005 + C2.  
Observed value: stable causal reference primitive; directional interpretation depends on mechanism.  
Preferred role: R6.  
Strength: **reusable reference primitive, not directional alpha claim**.

---

# 8. Combination rule for future strategies

Reusable blocks are **not** permission to search arbitrary combinations.

Allowed process:

1. new economic mechanism first;
2. choose the minimum core feature stack;
3. cite relevant RB IDs;
4. freeze one small auxiliary-block budget;
5. compare BASE vs BASE + one block where meaningful;
6. use fresh evidence after selection;
7. append result back to the registry.

Disallowed:

- trying every subset of RB001-RB008;
- selecting the historical best combination;
- calling a calibration sign a confirmed predictor;
- using C2-C6 data as clean evidence for the new combination.

---

# 9. Priority reuse hypotheses

Without ranking future strategies, the most scientifically informative reuse questions are:

1. Does RB005 extreme-flow state improve execution/veto quality for a separately valid base signal?
2. Does RB006 residual rank add incremental value to a lower-turnover/structurally different relative-value mechanism?
3. Does RB001 local-reference deviation serve as a trend-state veto rather than a reversal signal?
4. Does RB003 leader impulse add small but consistent incremental ranking value when entry economics already exist?
5. Can RB007 continuous derivative state combine prospectively with scheduled funding/mark/index mechanics without recreating C1?

These are hypotheses only. Each requires a new frozen incremental or strategy experiment.

---

## 10. Bottom line

C1-C6 produced no profitable selection survivor, but they did produce reusable knowledge.

The useful outputs are not “indicators that work” in a global sense. They are:

- scoped conditional behaviors;
- state descriptors;
- normalization rules;
- veto/execution hypotheses;
- relative-ranking information;
- clear examples of signals whose magnitude is too small for standalone trading.

The project should accumulate these blocks and test them prospectively, one role at a time, instead of discarding them with the failed parent strategy.
