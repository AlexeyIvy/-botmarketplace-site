# SC001 — C7-C10 Post-Slate Mechanism & Building-Block Synthesis v0.2

Date: 2026-09-18
Status: **NON-ALPHA SYNTHESIS / EXPANDED AFTER MULTI-ROLE REVIEW / NO NEW OUTCOME AUTHORIZED**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-c7-c10-post-slate-mechanism-building-block-synthesis-v0.1.md`

Parents:

- `docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`;
- `docs/research/sc001-c1-c6-five-role-reusable-mechanism-feature-review-v0.1.md`;
- `docs/research/sc001-c1-c6-second-pass-knowledge-extraction-audit-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.6.md`;
- `docs/research/sc001-reusable-market-building-blocks-registry-v0.5.md`;
- `docs/research/sc001-strategy-landscape-v0.6.md`.

## 1. Purpose

This version expands the post-slate synthesis after an additional programmer/trader, financial, mathematical and statistical review.

It does not change any terminal verdict and does not open new alpha.

The purpose is to extract the maximum practical information from the completed SC001 research before defining any C11+ candidate.

## 2. Terminal strategy verdicts remain unchanged

Binding:

- C1-C6: terminal `REJECT_SENTINEL`;
- C9-S1: terminal `C9_S1_REJECT_SENTINEL`;
- C8B-S0: terminal `C8B_S0_REJECT_HEADROOM`;
- C10-S0: terminal `C10_S0_REJECT_HEADROOM`;
- C7-S0: terminal `C7_S0_REJECT_SPREAD_HEADROOM`.

No terminal verdict is softened by this synthesis.

## 3. New high-level conclusion: empirical edge-scale prior

Across materially different liquid-crypto mechanisms, observed conditional information repeatedly falls in the approximate range:

`~0.5 bps to ~4 bps`

unless there is a separately justified structural source of larger movement.

Examples:

- C4 residual response: ~0.4-0.7 bps;
- C5 exhaustion state: ~0.5 bps;
- C6 cross-sectional residual spread: ~2-4 bps;
- C8B p99 transient basis deviation: ~2.45 bps;
- C10 p90 absolute move: ~3.58 bps;
- C7 widest p75 quoted spread: ~3.68 bps;
- C9 scheduled funding normalization: approximately zero.

This becomes a **design prior**, not a universal market law.

Future candidate cards must explicitly state:

- expected informational-edge scale;
- structural fill count;
- gross cost reserve;
- edge-to-fill ratio.

Default skepticism applies when an ordinary liquid-market signal requiring two or four fills assumes tens of bps gross edge without an independent economic mechanism.

## 4. Strongest role-specific lessons

### 4.1 C2 is more valuable as a persistence/veto state than as mean reversion

Two related but distinct causal local-reference constructions both produced approximately -4 bps in the predeclared reversion direction.

This is not evidence for immediate sign-flipping.

It is evidence that:

`large local-reference deviation should not automatically be faded`.

Preferred future roles:

- R2 persistence/trend state;
- R3 veto against mechanical fading;
- R5 execution aggressiveness context.

R1 use requires a new prospectively frozen experiment and fresh evidence.

### 4.2 C6 remains the strongest directional/ranking block

C6 retained:

- positive trimmed spread ~3.0 bps;
- median spread ~3.84 bps;
- positive calendar-day share ~71.4%;
- acceptable concentration.

Standalone four-fill economics failed correctly.

Preferred future role:

- relative rank/state;
- selection/ranking;
- veto/risk allocation;
- lower-fill architecture only if scientifically distinct.

### 4.3 C5 and C10 are execution-context candidates, not standalone alpha

C5 and C10 both show weak but broad microstructure information.

C5:
- extreme aggressive-flow exhaustion tendency ~0.5 bps.

C10:
- mean signed 5s move ~+0.58 bps;
- positive signed share ~58.7%;
- rare large-move tail exists;
- broad p90 move far below standalone hurdle.

Preferred reuse:

- anti-chase veto;
- entry urgency;
- maker/taker mode;
- exit timing;
- execution-risk state.

These roles add no new fills if attached to an independently valid base opportunity.

## 5. C10 specific lesson: depletion is not enough; replenishment dynamics may matter

The broad one-sided liquidity-vacuum state is too frequent and too weak economically as a standalone trigger.

However, C10 leaves a separate mechanistic hypothesis:

`depletion -> replenishment failure -> directional/execution consequence`

This is not authorized as a C10 rescue.

If studied later:

- it must receive a new candidate/feature hypothesis ID;
- replenishment must be defined prospectively;
- fresh nonpromotional data must be used after definition;
- no post-hoc selection of the 19 large C10 tail events is allowed.

## 6. C8 specific lesson: stale trade carry-forward can manufacture cross-venue spread

The C8 engineering sequence established a reusable methodological standard:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

For fast trade-based cross-venue research:

- do not carry old transaction prices across inactive seconds;
- require same-second venue activity when using transaction-price comparisons;
- separate clock qualification from price outcome.

This should become a platform-level default for future trade-based cross-venue studies unless a different synchronization rule is prospectively justified.

## 7. C7 specific lesson: screen empirical spread before queue/fill work

C7 demonstrated:

- all seven frozen non-BTC L2 datasets were high quality;
- quoted spread distributions were overwhelmingly below the hybrid execution reserve;
- persistent >=10 bps regimes were absent.

Reusable design rule:

`empirical spread distribution first -> queue/fill model second`.

Do not spend queue-model engineering effort when quoted spread itself lacks structural headroom.

## 8. New custom-feature hypothesis: flow-to-liquidity pressure

A mechanistically plausible new feature family emerges from the distinction between C5 and C10:

`FLOW_TO_LIQUIDITY_PRESSURE`

Concept:

signed aggressive flow should be interpreted relative to available opposite-side near-touch liquidity rather than in isolation.

Illustrative family:

`pressure = signed_aggressive_notional / causal_opposite_side_depth_reference`

Possible role:

- R2 stress state;
- R3 veto;
- R5 execution urgency.

Important guardrail:

This hypothesis is informed by completed C5 and C10 calibration evidence and is therefore highly exposed to hidden overfitting.

It is **not** C11 and is not authorized for outcome testing.

Any future implementation requires:

- prospectively frozen formula;
- no reuse of C5/C10 outcome periods as clean evidence;
- fresh Selection/Calibration data;
- one small parameter budget;
- incremental test against an independent base opportunity.

## 9. Strongest architecture-level lesson

The project should optimize:

`informational edge scale / structural fill count / cost reserve`

rather than maximize standalone signal strength.

A weak 0.5-3 bps block may still matter if it:

- vetoes an expensive bad entry;
- changes maker/taker choice;
- changes sizing;
- changes timing;
- ranks opportunities already requiring a fill;
- reduces turnover;
- reduces adverse-selection exposure.

It is usually unsuitable if it requires a new two- or four-fill trade solely to monetize the feature.

## 10. Statistical caution hierarchy

Evidence maturity differs across branches.

Relatively broad/multi-day:

- C1-C6;
- C9.

More structurally informative but often single-day calibration:

- C8B;
- C10;
- C7.

Therefore:

- decisive large-gap negative structural conclusions remain meaningful for the frozen mechanisms;
- weak positive feature effects from one-day calibration are hypothesis-level only;
- raw event count must not be treated as IID sample size;
- future weak-effect validation should emphasize day blocks, asset breadth and paired incremental comparisons.

## 11. Programmer/systems conclusion

SC001 has accumulated reusable research infrastructure that should be treated as a versioned kernel rather than reimplemented per strategy.

Kernel-level components include:

- half-open causal windows;
- completed-bar semantics;
- D+D1 UTC stitching;
- strict-coactive cross-venue synchronization;
- fail-closed L2 replay;
- leading-update-until-first-snapshot handling;
- source identity/SHA lineage;
- contamination ledger;
- separate Strategy Evidence and Feature/Building-Block Evidence outputs.

Future candidate code should depend on these primitives.

Strategy verdicts must never be encoded inside feature functions.

## 12. Mandatory new preflight: Edge-to-Fill

Every C11+ feasibility card must pass a non-alpha preflight containing:

- expected informational-edge scale;
- number/type of structural fills;
- conservative fee floor;
- spread/depth exposure;
- execution reserve;
- break-even gross move;
- expected opportunity rate;
- capital-time utilization;
- plausible source of edge magnitude.

Default stop rule:

If the mechanism has no plausible path for:

`expected gross information > conservative structural burden`

before backtesting, reject structurally.

## 13. Candidate-family implications

### N1 — execution-veto architecture

Potentially strong because weak C5/C10-like information can matter without additional fills.

Current blocker:

An independent base opportunity must exist first.

Disposition before card review:

`HOLD_INFORMATION_VALUE`.

### N2 — relative ranking with one-sided execution

Potentially strong because RB006 has the best reusable directional evidence.

Current risk:

A naive implementation can become a disguised cheaper rewrite of C6.

Disposition before card review:

`HOLD_INFORMATION_VALUE`.

### N3 — regime-dependent execution-mode choice

Potentially strong because it uses high-validity state features to reduce cost rather than forecast return.

Current blocker:

Requires an independent base opportunity whose maker/taker/no-trade decision is economically meaningful.

Disposition before card review:

`HOLD_INFORMATION_VALUE`.

## 14. Critical insight before assigning C11+

All three families share the same hidden dependency:

`AN INDEPENDENT BASE OPPORTUNITY`

Without it:

- N1 has nothing to veto;
- N2 risks becoming C6 rescue;
- N3 has no trade whose execution mode can be optimized.

Therefore candidate-card review must explicitly test whether the base mechanism is truly independent of C1-C10.

If no such base mechanism exists, do not assign C11+ yet.

## 15. Next action

1. adopt a binding Edge-to-Fill Preflight;
2. create N1/N2/N3 feasibility cards using template v0.2;
3. perform a comparative non-alpha review;
4. assign C11+ IDs only to cards that have:
   - an independent base mechanism;
   - acceptable edge-to-fill architecture;
   - bounded complexity;
   - feasible fresh evidence.

No new outcome-bearing run is authorized by this synthesis.
