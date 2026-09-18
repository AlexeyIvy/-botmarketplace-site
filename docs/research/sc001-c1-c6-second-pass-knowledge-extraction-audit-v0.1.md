# SC001 — C1-C6 Second-Pass Knowledge Extraction Audit v0.1

Date: 2026-09-18
Status: **READ-ONLY SECOND-PASS REVIEW / NO NEW OUTCOME / NO RESCUE-TUNING**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `sc001-c1-c6-sentinel-batch-results-readonly-postmortem-v0.1.md`
- `sc001-c1-c6-five-role-reusable-mechanism-feature-review-v0.1.md`
- `sc001-reusable-market-building-blocks-registry-v0.1.md`
- `sc001-feature-indicator-research-governance-v0.1.md`

## 1. Purpose

Re-examine the C1-C6 conclusions for overstatement, missed reusable information, hidden statistical caveats and research-process improvements before moving to the next candidate family.

This audit changes no terminal strategy verdict and opens no new alpha.

## 2. Important corrections / refinements

### 2.1 C2 opposite sign is useful, but not yet a validated continuation signal

C2 produced approximately -4 bps when outcomes were signed for reversion.

This is strong evidence that the frozen reversion hypothesis was wrong on the calibration sample.

It is **not** yet clean evidence that a +4 bps continuation strategy exists, because the continuation interpretation was formulated after observing the C2 outcome.

Therefore RB001 should be interpreted as:

`OPPOSITE_SIGN_CALIBRATION_OBSERVATION / PERSISTENCE HYPOTHESIS`

rather than a confirmed directional continuation feature.

Prospective reuse should favor R2/R3 first; R1 requires a new frozen experiment and fresh evidence.

### 2.2 C4 COMMON_BETA_NOT_LEAD_LAG flag must not be over-read

The C4 code used a coarse diagnostic label when raw response was positive but the frozen residual economic gate failed.

However the measured residual response itself remained positive in all four variants, approximately +0.38 to +0.67 bps equal-weight.

Therefore the defensible conclusion is:

- raw response did not establish economically meaningful lead/lag after common-factor control;
- common beta is an important confounder;
- a small residual effect remained;
- the test does **not** prove that common beta explains 100% of the response.

Future documents should not interpret the boolean diagnostic more strongly than the measured residuals justify.

### 2.3 C5 broad positive sign may include microstructure bounce

C5 used trade-derived bars rather than quote-aware execution.

The small ~0.5 bps reversal tendency could reflect a combination of:

- genuine exhaustion;
- short-horizon price-impact decay;
- bid/ask or microstructure bounce;
- common intraday shocks.

Therefore RB005 is best retained as an R2/R3/R5 hypothesis, especially an execution/anti-chase context, not as established forced-flow alpha.

A future incremental test should use a separately valid base opportunity and, where needed, quote-aware outcome semantics.

### 2.4 C6 is the strongest directly positive tested block, but uncertainty remains material

C6 had:

- positive trimmed and median spread;
- approximately 20/28 positive calendar days;
- acceptable asset concentration.

But the primary calendar-day block count is only 28, and no block-level confidence interval was part of the sentinel gate because the economic magnitude already failed decisively.

Therefore RB006 can be called the strongest **directly positive tested calibration block** from C1-C6, but not a statistically confirmed reusable alpha block.

Its most interesting future role is relative ranking/state under a materially different architecture, not a lower-cost post-hoc rewrite of C6.

### 2.5 C3 did not test volatility forecasting

C3 demonstrated that breakout + expansion did not provide sufficient **directional continuation**.

It did not test whether expansion predicts:

- future realized variance;
- tail risk;
- execution slippage;
- stop/position-size requirements.

Therefore RB002 may be a useful R2/R4 state descriptor, but that role remains a prospective hypothesis rather than an observed C3 result.

### 2.6 C1 zero triggers is threshold-specific evidence

C1 established zero events under the exact +50 bps dislocation event definition.

It did not establish that:

- basis deviations are always tiny;
- continuous basis state has no information;
- funding/mark/index derivative state is uninformative.

No lower-threshold C1 rescue is allowed, but RB007 continuous basis remains a valid R2/R6 measurement primitive.

## 3. What was still missing from the first knowledge extraction

For most C1-C6 features we currently know:

- event/sample count;
- mean or median effect;
- asset/day breadth;
- coarse concentration.

We generally do **not** yet have a complete reusable-feature passport containing all of:

- block-level uncertainty;
- effect quantiles/tails;
- conditional downside;
- opportunity-retention impact as a filter;
- turnover impact;
- execution/slippage impact;
- redundancy/correlation with other RB blocks;
- state persistence / transition matrix;
- incremental value over an independently valid base mechanism.

These missing fields should not be retroactively mined from C1-C6 merely to rescue them.

Instead they should become mandatory outputs of future feature-aware experiments where scientifically relevant.

## 4. New research-process optimization

Every future outcome-bearing candidate should produce two parallel outputs from the beginning:

### A. Strategy Evidence Report

- terminal strategy state;
- economic gates;
- cost/execution result;
- breadth;
- sample/MDE state.

### B. Feature / Building-Block Evidence Report

For each declared feature/RB:

- exact formula/version;
- R1-R6 role;
- feature distribution;
- opportunity count;
- asset/day breadth;
- block-level effect where applicable;
- sign consistency;
- tail/risk diagnostics;
- turnover/opportunity-retention effect;
- execution/cost interaction;
- redundancy with simpler features;
- allowed reusable conclusion;
- forbidden inference.

This prevents useful market information from being reconstructed only after a strategy fails.

## 5. Feature usefulness must be multi-dimensional, not binary

Future RB records should track at least these dimensions separately:

1. **Measurement validity** — is the feature causally and stably computable?
2. **Directional information** — is there a conditional expected-return sign?
3. **Breadth** — does the sign/general behavior span assets and days?
4. **Economic magnitude** — is the effect large relative to the relevant fill architecture?
5. **State/risk value** — does it describe volatility, regime, liquidity or tail behavior?
6. **Execution value** — can it improve maker/taker choice, timing or adverse selection?
7. **Incremental value** — does it add beyond a simpler/base feature?
8. **Evidence maturity** — calibration, Discovery, Confirmation, forward/demo.

A block can be strong on one axis and weak on another.

## 6. Revised interpretation of current blocks

### RB001 — local-reference deviation
- measurement validity: high;
- observed directional reversion evidence: negative;
- prospective persistence hypothesis: meaningful but post-hoc;
- best next role: R2/R3.

### RB002 — expansion/breakout state
- measurement validity: high;
- standalone directional information: near zero;
- state/risk value: untested prospectively;
- best next role: R2/R4 hypothesis.

### RB003 — leader impulse residual context
- measurement validity: high;
- directional information: small positive;
- breadth: high;
- economic magnitude: very low;
- best next role: R2/R3/ranking.

### RB004 — residualization
- measurement validity: high;
- directional alpha: not applicable;
- methodological value: high;
- best role: R6.

### RB005 — aggressive-flow exhaustion state
- measurement validity: high;
- directional information: small positive reversal;
- breadth: moderate-high;
- economic magnitude: very low;
- microstructure-confound risk: material;
- best next role: R3/R5 hypothesis.

### RB006 — cross-sectional residual rank
- measurement validity: high;
- directional information: positive;
- breadth: high by day;
- economic magnitude: low-single-digit bps;
- evidence maturity: calibration only;
- best next role: ranking/state under a genuinely new architecture.

### RB007 — continuous basis state
- measurement validity: high;
- strict threshold event utility: scarcity-limited;
- directional information outside threshold: untested;
- best next role: R2/R6 in a different derivative-state mechanism.

### RB008 — causal local reference
- measurement validity: high;
- directional alpha: not applicable;
- best role: R6.

## 7. One more important strategic lesson

C2-C6 imply that the project should search not only for a "stronger predictor", but for a better **edge-to-fill architecture**.

A feature with 2-4 bps of gross information may be unusable in a four-taker-fill cycle but could still matter in:

- an already-required hedge;
- a passive fill architecture;
- a one-sided ranking decision;
- a veto that avoids an expensive bad trade;
- a sizing/risk decision that adds no extra fills.

This does not authorize re-engineering C2-C6. It changes the design criterion for future independent mechanisms.

Future candidate cards should therefore explicitly contain:

`expected informational edge scale / number and type of structural fills`.

## 8. Guardrail against false "combination alpha"

Because several weak blocks have positive signs, it will be tempting to combine them.

That is the highest current overfitting risk.

Do not infer:

`0.5 bps + 0.7 bps + 3 bps = profitable composite`.

Feature effects may be:

- redundant;
- conditional on the same market shocks;
- non-additive;
- mutually exclusive;
- destroyed by reduced opportunity count;
- offset by added latency/turnover.

Any combination requires an economic interaction hypothesis and a frozen incremental test.

## 9. Consequence for C9/C8 next slate

The planned next step remains valid.

C9 should use RB007/RB008 only as state/reference primitives and should not import C2-C6 directional blocks by default.

C8 should use RB004 residualization principle and RB008 causal reference semantics, but should not inherit C4 lag parameters.

This preserves orthogonality and avoids turning the new slate into a hidden rescue of the old one.

## 10. Final second-pass conclusion

No terminal verdict should be changed.

No additional C1-C6 strategy should be run.

The main improvements are:

- downgrade any over-strong causal interpretation of weak calibration effects;
- preserve opposite-sign and weak-breadth information as hypotheses, not alpha claims;
- distinguish feature usefulness dimensions explicitly;
- make Building-Block Evidence Reports mandatory in future experiments;
- optimize future research around edge-to-fill architecture;
- treat feature combinations as new hypotheses, never arithmetic addition of historical effects.

The next C9-D0 data-only stage remains the correct immediate action after these governance refinements.
