# SC001 Current Roadmap and Stop Rules v4.33

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — SECOND-PASS KNOWLEDGE AUDIT COMPLETE / C9-D0 DATA-ONLY AUDIT NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.32.md`

## 1. Binding terminal states

All prior terminal states remain unchanged.

C1-C6 remain `REJECT_SENTINEL`. No rescue-tuning, sign-flip reuse, parameter-neighbor retest or post-hoc combination search is authorized.

## 2. Second-pass review complete

Binding refinement:

`docs/research/sc001-c1-c6-second-pass-knowledge-extraction-audit-v0.1.md`

This review did not change any strategy verdict.

It refined evidence interpretation and identified several anti-overclaim guardrails.

## 3. Important interpretation refinements

- C2 opposite-sign outcome is a **persistence hypothesis**, not confirmed continuation alpha.
- C4 common-beta diagnostic must not be read as proof that beta explains 100% of the response; positive but economically tiny residuals remained.
- C5 small reversal may include microstructure bounce; retain primarily as R2/R3/R5 hypothesis.
- C6 is the strongest directly positive tested calibration block among C1-C6, but block-level uncertainty and execution economics remain inadequate for alpha promotion.
- C3 directional failure does not establish or test volatility/risk forecasting value.
- C1 zero-trigger result applies to the frozen +50 bps event, not to the existence of continuous basis information.

## 4. New mandatory dual-output rule

Every future outcome-bearing SC001 experiment must prospectively produce:

### Strategy Evidence Report
- terminal strategy verdict;
- economic gates;
- sample/breadth;
- cost/execution result.

### Feature / Building-Block Evidence Report
For every declared feature/RB:
- formula/version;
- R1-R6 role;
- distribution;
- asset/day breadth;
- block-level effect where applicable;
- tail/risk diagnostics;
- opportunity-retention / turnover impact;
- execution/cost interaction;
- redundancy/incremental value where tested;
- allowed reusable conclusion;
- forbidden inference.

This is designed before outcome, not reconstructed only after failure.

## 5. Feature evidence remains multi-dimensional

Do not use a single `works` field.

Track separately:

- measurement validity;
- directional information;
- breadth;
- economic magnitude;
- state/risk value;
- execution value;
- incremental value;
- evidence maturity.

## 6. Edge-to-fill architecture becomes a first-class candidate field

Every new candidate card must explicitly state:

`plausible information/edge scale relative to number and type of structural fills`.

The project should prioritize mechanisms that can either:

- generate materially larger raw economic effects;
- reduce fill/cost burden;
- earn spread/carry;
- or improve an existing valid trade without adding fills.

This is a design principle, not permission to re-engineer C1-C6.

## 7. Combination guardrail

Do not assume weak RB effects add arithmetically.

Any multi-block combination requires:

1. an economic interaction hypothesis;
2. a frozen interaction budget;
3. simpler BASE comparators;
4. fresh evidence;
5. multiplicity accounting.

No arbitrary RB subset search is allowed.

## 8. Next-slate order unchanged

C7-C10 feasibility audit remains binding.

Engineering/information-efficiency sequence remains:

1. C9 scheduled funding/mark-index state;
2. C8 cross-venue same-asset data/clock audit;
3. C10 L2 liquidity-vacuum BTC structural pilot;
4. C7 spread-qualified multi-asset maker universe.

This is not a profitability ranking.

## 9. C9 guardrail

C9 may use:

- RB007 continuous basis state;
- RB008 causal reference;

only as R2/R6 state/reference primitives initially.

Do not import C2-C6 directional blocks into C9-D0 or the first C9 base mechanism by default.

## 10. C8 guardrail

C8 may use:

- RB004 residualization principle;
- RB008 causal reference semantics;

without inheriting C4 lag parameters or target-selection logic.

## 11. Protected data remain closed

Still closed:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August 1-30 protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- legacy E006 March 22-30 SPOT Confirmation.

## 12. Immediate next action

Proceed to C9-D0:

1. freeze metadata/data-semantics protocol;
2. implement metadata-only public-source probe;
3. verify funding coverage, historical interval semantics, mark/index availability, timestamp alignment and data volume;
4. calculate no return/PnL;
5. only after C9-D0 PASS decide whether an outcome-bearing C9 sentinel deserves design.

No VPS command is authorized until the C9-D0 probe is frozen.
