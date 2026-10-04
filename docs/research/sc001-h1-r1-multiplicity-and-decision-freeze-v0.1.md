# SC001-H1-003 — R1 multiplicity and decision freeze v0.1

Date: 2026-10-04
Worker: H1_HISTORICAL_INDICATORS
Task / PR: SC001-H1-003 / #432
Authorization: DESIGN_ONLY / R1_MULTIPLICITY_DECISION_FREEZE
Disposition: H1_R1_MULTIPLICITY_FREEZE_READY_FOR_STRATEGY
Evidence: DEFINED_ONLY / ADAPTIVE_DISCOVERY_GENERATED / nonpromotional
Dispatch and reviewed main: c65021d200b417bda7cd24f64a1bca48c7c2bb89
Task branch: sc001/h1/SC001-H1-003-r1-multiplicity-freeze

This is one pre-outcome statistical specification for Strategy Manager review. It authorizes no implementation execution, data access, acquisition, or research run. READY_FOR_STRATEGY means the design is specified; it does not certify source availability, dependence assumptions, finite-sample coverage, or satisfaction of the joint H1/X1 pre-outcome barrier.

## FROZEN R1 FAMILY

The exact task, benchmark design and variant ledger agree on precisely these four members, in this reporting order. No member or parameter is added, removed, replaced or optimized.

| Order | Feature ID | Exact raw formula | Warm-up | Fixed horizon | Orientation | R1 eligibility |
|---|---|---|---|---|---|---|
| 1 | H1-BM-P1-LOC20-v0.1 | 2*(C_t-min(L[t-19:t]))/(max(H[t-19:t])-min(L[t-19:t]))-1; zero denominator => missing | 20 completed bars | 3 minutes | negate raw feature; REVERSION | R1_CORE_SIGNAL |
| 2 | H1-BM-P2-MASPREAD-8-32-v0.1 | mean(ln(C[t-7:t]))-mean(ln(C[t-31:t])) | 32 completed bars | 8 minutes | raw feature; CONTINUATION | R1_CORE_SIGNAL |
| 3 | H1-BM-P2-SIGNPERSIST16-v0.1 | mean(sign(r_i)), i=t-15..t; r_i=ln(C_i/C_(i-1)); sign(0)=0 | 17 completed bars | 4 minutes | raw feature; CONTINUATION | R1_CORE_SIGNAL |
| 4 | H1-BM-P7-MEDDEV20-v0.1 | ln(C_t/median(C[t-19:t])) | 20 completed bars | 5 minutes | negate raw feature; REVERSION | R1_DEVIATION_SIGNAL |

All bracket endpoints in formulas are inclusive bar indices. An even-sample median is the arithmetic mean of the two central values in sorted order. This convention makes the existing median formula explicit; it adds no alternate formula.

C, H, L are source-finalized completed 1m close, high and low. A feature is available only after the source finalizes bar t. No open-bar final value is usable. All four formulas, warm-ups, horizons and eligible roles above are unchanged from the canonical benchmark.

BAL14 is R2 only. BAL14, RV20, RANGEEXP-5-20 and RELACT20 are outside this directional family; R2/R3/R4/R6-only uses receive no standalone directional claim. They need a separately frozen base-opportunity denominator and authorization for incremental tests. Their exclusion here does not remove them from the eight-variant benchmark panel.

No new feature variant, interaction, composite, horizon, symbol subset, venue or hour filter is introduced. The statistical score below measures the fixed formulas; it is not a new tradable feature or position rule.

## ORIENTATION / HYPOTHESES

Let X_(j,a,d,t) be the oriented feature: minus LOC20, plus MASPREAD, plus SIGNPERSIST, minus MEDDEV20. The only response is

Y_(j,a,d,t) = ln(C_(a,d,t+h_j) / C_(a,d,t)),

at h_j = 3, 8, 4, 5 respectively. This is a gross completed-close response for predictive association, not an executable fill return, alpha, net edge or PnL. Source-finalization delays and executable entry prices are unresolved for a later economic protocol; this design must not imply a trade at the just-finalized close.

Define the calendar-day score Z_(j,d) exactly below and its stationary-population mean mu_j = E[Z_(j,d)] for the frozen source, development universe and Discovery evidence regime.

For each member j, separately:
- H0_j: mu_j <= 0.
- H1_j: mu_j > 0.

The tested object is positive average within-instrument/day rank association after the predeclared orientation. It is not an unconditional expected trading profit, a cross-sectional winner ranking, a conditional-mean martingale hypothesis, or proof of a causal economic mechanism. The alternative does not require every day or asset to have positive association.

No two-sided reinterpretation, absolute-effect selection, negative-tail success, sign reversal, horizon adjustment or selection of the best member is permitted. Negative results remain negative in the oriented reporting convention.

## PRIMARY EFFECT STATISTIC

Exactly one primary statistic: equal-calendar-day, equal-development-asset mean Spearman rank association.

1. Source/universe/evidence membership must first be frozen by a separate authorized metadata task. Retain the benchmark's Binance USD-M perpetual 1m source, outcome-blind 6-12 instrument eligibility, lexicographic cap and holdout positions 5,10,... unchanged. Only development assets enter Discovery. This leaves at least 5 development assets when the full universe has 6. Never require 6 development assets by silently changing the original split.
2. Within each scheduled complete UTC day index the 1,440 bars t=0,...,1439. Use the same deterministic evaluation grid t=31,...,1431 inclusive for all four members: exactly 1,401 paired observations per asset/day. The first 31 bars supply the longest unchanged warm-up; the final 8 bars supply the longest unchanged forward response. These boundary bars remain required inputs. No time-of-day search or alternative grid is permitted.
3. This common grid keeps every feature window and every response inside its own UTC day. No Selection/Discovery/Holdout/Confirmation boundary is crossed for warm-up or response. It is a mechanical boundary guard, not an economic session filter.
4. For each member, asset and day compute average/mid-ranks R_t of X_t and S_t of Y_t over that fixed grid. Ties get their exact average rank, with no random jitter or tie-breaking by outcome.
5. Compute rho_(j,a,d) = sum_t[(R_t-Rbar)(S_t-Sbar)] / sqrt(sum_t(R_t-Rbar)^2 * sum_t(S_t-Sbar)^2).
6. With A frozen development assets, Z_(j,d) = (1/A) * sum_a rho_(j,a,d). With N scheduled Discovery days, theta_hat_j = (1/N) * sum_d Z_(j,d).

Each rho and Z lies in [-1,1]. Every asset receives weight 1/A; every day receives weight 1/N. No weighting by volume, available row count, volatility, significance or past performance. Day/asset ranks are retrospective evaluation summaries, not causal transformations available at individual trade times; they must never be fed back as live signal inputs.

This statistic is threshold-free: it has no signal cutoff, quantile portfolio, optimized position size or outcome-selected threshold. Quality gates below are fixed feasibility rules, not feature thresholds.

Required descriptive disclosure, using the same scores only: per-asset mean rho in fixed lexicographic order, per-day Z in chronological order, positive-asset and positive-day fractions with the full frozen denominators, and each asset/day's additive contribution to theta_hat. These are breadth/concentration descriptions, not extra tests, selection rules or alternate primary statistics. No per-asset/hour significance tests or leave-one-out winner search.

## DEPENDENCE / INFERENCE UNIT

Primary observation for inference: one common UTC calendar day containing all frozen development assets and all four member scores. Asset-days and 1m rows are NOT independent replicates.

Common-market and same-day cross-asset dependence is unrestricted inside Z_d. Overlapping forward responses and overlapping lookbacks within a day are also unrestricted. Averaging them does not manufacture additional independent observations.

Across days use contiguous calendar-day blocks of the joint vector (Z_1,d,...,Z_4,d). All assets have already been kept together in their day aggregate, and all four members use identical bootstrap day indices. No independent resampling of assets, minutes, features or arbitrary nonadjacent days.

Validity model for the marginal construction:
- the joint day-score process on the frozen Discovery regime is strictly stationary and geometrically alpha-mixing;
- the long-run variance of every tested member's mean is finite and strictly positive;
- the complete common panel and evidence allocation were fixed without viewing outcomes, and there is no informative outcome-driven deletion.

Bounded scores supply finite moments; mixing provides decay of serial dependence and the mean/block-bootstrap limit. Neither the 8-minute maximum response nor the daily aggregation proves that different days are independent. The procedure does not assume Gaussian minute returns, symmetric day scores, independent assets or independent hypotheses.

The resulting inference is ASYMPTOTIC, dependence-aware inference under this stated model, not an exact finite-sample or distribution-free 5% guarantee. Holm cannot repair invalid marginal p-values. A fixed finite N threshold is only an operational minimum, not a proof that asymptotics are accurate.

Before any later outcome access, Strategy Manager must explicitly accept this inferential scope and the exact implementation/data task must record a defensible dependence/stationarity rationale. Finite samples cannot prove stationarity or mixing. A known structural break, unresolved missingness selection, or inability to defend this scope results in INFERENCE_DATA_INVALID_OR_INSUFFICIENT; do not tune block length, segment the window, choose another test or claim support. If Strategy requires exact finite-sample control under arbitrary serial dependence, this specification does not supply it: return H1_R1_MULTIPLICITY_FREEZE_STRATEGY_ATTENTION_REQUIRED rather than silently strengthening claims or substituting a method.

## MARGINAL TEST CONSTRUCTION

Freeze one circular moving-block bootstrap of centered joint day scores. No permutation of raw response rows and no independent day sign-flips.

Fixed choices:
- one terminal evaluation at the predetermined Discovery end; no sequential looks or optional stopping;
- N >= 60 scheduled complete common Discovery days;
- A >= 5 development assets, with the full eligible universe still satisfying the original 6-12 rule;
- block length L = ceil(N^(1/3)) calendar days;
- K = ceil(N/L) sampled blocks per replicate;
- require floor(N/L) >= 12;
- B = 19,999 replicates;
- one shared deterministic random stream for all four tests;
- no alternative lengths, seeds, replicate budgets, statistics or p-values are considered.

Exact pseudocode, for a future separately authorized implementation:
1. Compute theta_hat_j and U_(j,d)=Z_(j,d)-theta_hat_j, d=0,...,N-1.
2. For each replicate b, draw K starts independently and uniformly from {0,...,N-1}; each start s yields indices s,s+1,...,s+L-1 modulo N. Concatenate the K blocks and keep the first N indices. Circular wrap is a resampling device, not a claim that the observed end and start were adjacent in real time; its boundary contribution vanishes in the stated block-bootstrap limit.
3. Apply these exact same N day indices to all four U series. Define Tstar_(j,b)=sqrt(N)*mean(U_(j,resampled indices)). Observed T_j=sqrt(N)*theta_hat_j.
4. If theta_hat_j <= 0, set p_j=1. Otherwise set p_j=(1 + count_b[Tstar_(j,b) >= T_j])/(B+1), with equality included in the upper tail.
5. Run Holm exactly once on these four p_j. The bootstrap is solely the marginal test, never a bootstrap/max-stat multiplicity replacement.

Random stream specification independent of library defaults:
- Domain bytes are UTF-8 of SC001-H1-003-CMBB-v0.1 followed by one zero byte.
- For counter c=0,1,... append c as unsigned 64-bit big-endian bytes and SHA-256 the concatenation.
- Read each digest as four unsigned 64-bit big-endian integers, in byte order.
- Set M=floor(2^64/N)*N. Reject integers u>=M; for accepted integers use u mod N as the next start.
- Consume starts replicate-major then block-major; use exactly B*K accepted values. Do not reseed between members. Exact unsigned arithmetic is required.

This specifies a reproducible pseudorandom Monte Carlo approximation to ideal uniform block draws; it is not an exact randomization test. The plus-one convention prevents zero Monte Carlo p-values; it does not turn an approximate bootstrap law into a finite-sample super-uniform law. Report B, exceedance counts, N, A, L, K and random-stream specification with all results; do not rerun borderline results with extra seeds or a larger budget.

Justification: with bounded stationary geometrically mixing scores, nonzero long-run variance, L tending to infinity and L/N tending to zero, the centered block-bootstrap distribution of the mean estimates its centered sampling distribution. L=ceil(N^(1/3)) has these rates. At mu_j=0 the one-sided tail tests the boundary null; fixed mu_j<0 is conservative asymptotically. No claim about uniform validity over arbitrary nonstationary markets is made. The finite B approximation introduces Monte Carlo uncertainty and must be disclosed.

The benchmark minimum of 120 total days supplies only about 24 Discovery days under its unchanged 40/20/20/20 split, so it does NOT pass this inference minimum. For example, 300 total eligible days supply 60 Discovery days under the unchanged split; noninteger partition boundaries must follow the existing canonical rounding rule in the later metadata freeze. The program already favors longer eligible history, but this task chooses no dates, source resource or larger window and authorizes no acquisition. If the later predeclared eligible span is too short, return insufficient; do not move partition boundaries or steal Holdout/Confirmation days.

## HOLM FWER PROCEDURE

Exactly m=4, familywise alpha=0.05. Sort marginal p-values ascending; break exact ties by the frozen family order above.

For sorted p_(k), k=1,...,4, compare sequentially against:
- k=1: 0.05/4 = 0.0125;
- k=2: 0.05/3;
- k=3: 0.05/2 = 0.025;
- k=4: 0.05.

Reject H0_(k) while p_(k) <= 0.05/(5-k). Stop at the first failure; that member and all remaining members are not rejected. Use unrounded values for decisions.

Adjusted values:
pHolm_(k)=min(1,max_(i<=k)[(5-i)*p_(i)]).
Map results back into frozen family order and disclose all four. No sorted leaderboard in the primary report. An internal sort for Holm is not winner selection.

With valid super-uniform marginal tests, Holm controls FWER under arbitrary dependence among the four hypotheses. Here marginal validity is asymptotic under the explicit calendar-process model and approximate Monte Carlo calculation, so familywise control carries those same limitations. Feature redundancy neither reduces m nor creates independent confirmations.

A missing/invalid member never shrinks m. Use p_for_Holm=1 only as a conservative bookkeeping placeholder, clearly marked UNAVAILABLE rather than a computed p-value; apply the whole-family invalid/insufficient override below. No partial-family success claim survives that override.

## MISSINGNESS / INVALID BLOCKS

Prospectively fixed strict complete-panel rule:
- Source identity, instrument membership, prior-use status, finalized-bar clock, UTC grid and evidence-role authorization must be settled before outcomes.
- Every scheduled Discovery day and every frozen development asset must contain all 1,440 unique, ordered, source-finalized 1m bars with finite valid required OHLC and positive prices. No duplicate timestamps, unresolved gaps, forward fill, interpolation or fabricated bars.
- Every one of the 1,401 scheduled feature/response pairs must be finite for all four members. LOC20 zero range, unavailable required input, invalid log input or nonfinite transform makes that member/asset/day invalid.
- If either rank vector has zero variance, rho is undefined: invalid, never zero association. Ties with positive rank variance are allowed.
- Any invalid required asset/day/member invalidates the family inference. Do not drop that cell, day, asset or hypothesis; disclose all scheduled and invalid counts/reasons. Stop further outcome work when the failure is known, under the later run's stop rule.
- Too few total eligible days/assets, too few Discovery days/development assets, too few complete blocks, or an unqualified evidence window yields insufficient before calculation where metadata permit.
- A constant day-score series, zero empirical day-score variance, nonfinite statistics, no variation across the B bootstrap means, or numerical/hash/clock failure yields invalid/degenerate; do not return p=0 or invent uncertainty.
- Positive empirical variance alone does not prove positive long-run variance or validity of the dependence model. Known model failure/unresolved scope yields invalid/insufficient.
- No replacement instrument, alternate missingness tolerance, window shortening, fallback IID test, alternative seed, block length or post-outcome repair is allowed.

The strict rule sacrifices availability to avoid outcome-dependent panel selection. A later proposal for a more permissive design needs a new prospectively reviewed version and appropriately untouched evidence; it cannot rescue this version on the same evidence.

## FAMILY TERMINAL DECISION SEMANTICS

Apply the following precedence. These are future research-result classifications, distinct from this DESIGN_ONLY task's terminal tokens.

1. STALE_CONTEXT_REVALIDATION_REQUIRED:
   Relevant task, authorization, feature, contamination, architecture, protocol or lineage context changed since the accepted freeze. Stop; no support/no-support conclusion. Unrelated main changes may be reviewed as nonconflicting with explicit evidence; conflicting changes require Strategy review.
2. INFERENCE_DATA_INVALID_OR_INSUFFICIENT:
   Any source/evidence/causality/breadth/degeneracy/dependence-model/implementation gate fails or cannot be established. Report which gate and all available permitted bookkeeping, not a negative discovery or a partial success. Uncomputed entries remain null/unavailable.
3. R1_DISCOVERY_NO_SUPPORT:
   All validity gates pass, all four marginal and Holm results are available, and none is rejected. This is failure to demonstrate positive association at the frozen error target, not proof of zero effect, equivalence, economic uselessness, or invalidity of non-R1 roles.
4. R1_DISCOVERY_SUPPORT_ONE_OR_MORE:
   All validity gates pass and at least one preoriented hypothesis is rejected by Holm. Report the entire supported set plus every unsupported member; never only the strongest member. This means multiplicity-adjusted Discovery support within the stated asymptotic inferential scope, never Confirmation, promotion, tradability, PnL or permission to trade.

A future report must include all four IDs, orientations, horizons, theta_hat, raw p (or explicit null/reason), pHolm, reject/not-reject/unavailable, validity flags, scheduled/valid/missing days and assets, breadth/contributions, and resampling metadata. Report the frozen order, no winner ranking. Negative or nonsignificant members must not be omitted or reoriented.

## CONTAMINATION / EVIDENCE CLASS

This design remains ADAPTIVE_DISCOVERY_GENERATED. No independent pre-existing research queue is asserted. Four-test Holm controls only this declared family under its marginal assumptions; it does not erase the broader adaptive SC001 path.

No market evidence was opened here. Future Selection remains calibration/nonpromotional. Discovery uses only its assigned development assets and time slice; Asset Holdout and Chronological Confirmation remain unopened until separately authorized. A positive Discovery member still requires independent asset/time Confirmation and fresh chronological/prospective evidence before promotional interpretation, with unchanged feature implementation and predeclared confirmation multiplicity. This task does not define or authorize that later confirmation family.

P1 protected/fresh collector data is not a generic H1 confirmation source. Neither physical availability nor another program's access supplies permission or cleanliness. Shared H1/X1 resource and evidence lineage must be resolved separately; both programs' relevant design freeze barriers remain binding.

No contamination registry, feature registry, reusable-block registry or shared-state artifact is changed.

## DO NOT DO

- Do not open market rows, protected evidence, historical responses, alpha or PnL.
- Do not use VPS Reader, Test Executor, Runner, collectors or source/network acquisition.
- Do not change the four formulas, signs, horizons, family size, partitions or universe-selection rule.
- Do not add signal thresholds, asset/hour/venue searches, interactions or alternative statistics.
- Do not use minute/sample count as independent inference breadth.
- Do not call bootstrap/Holm exact under arbitrary time dependence.
- Do not select a more favorable seed, block length, period, missingness rule or statistic.
- Do not repair or rescue after outcome access, replace a failed member, or borrow untouched holdout days.
- Do not convert rank association into bps, fill economics or a trade recommendation.
- Do not promote state-only features as directional alpha.
- Do not modify task JSON, roadmap, governance, Strategy State, contamination/reusable registries or routing architecture.
- Do not merge, close, retarget, auto-merge or delete PR/branch.

## TERMINAL DISPOSITION

H1_R1_MULTIPLICITY_FREEZE_READY_FOR_STRATEGY

The exact four-member family, primary statistic, marginal algorithm, Holm rule, missingness rules and terminal semantics are specified before outcomes. All formulas/roles/horizons match the canonical benchmark and ledger. The exact task permits this design selection, not execution.

Strategy review must specifically assess the asymptotic dependence model, strict complete-panel rule and 60-day Discovery minimum. No finite-sample guarantee or actual data sufficiency is asserted. A manager requirement for exact finite-sample arbitrary-dependence control, or a concrete defect in this marginal construction, requires H1_R1_MULTIPLICITY_FREEZE_STRATEGY_ATTENTION_REQUIRED, not an adaptive replacement.

Next allowed action: Strategy Manager reviews this package and decides whether to accept the pre-outcome freeze. Data qualification, joint H1/X1 freeze acceptance, implementation qualification and every outcome run require separate authorization. The worker starts no successor task.

PROPOSED_SHARED_STATE_CHANGE: none.
MERGE_AUTHORIZED: false.
STRATEGY_REVIEW_REQUIRED: true.
CONTINUATION_REVIEW_REQUIRED: true.

Safety receipts for this task:
outcome_accessed=false
protected_evidence_accessed=false
market_rows_read=false
network_accessed=false
test_executor_job_launched=false
runner_bundle_created=false
runner_bundle_executed=false
vps_data_read=false
collector_changed=false

Here network_accessed=false refers to research/source acquisition: authorized GitHub control-plane reads/writes occurred. No exchange, dataset, general web or VPS access occurred.

Budget use: zero research/implementation executions, zero network acquisition runs, zero new feature variants/parameterizations/horizons/subset alternatives, zero repair cycles; two authorized repository artifacts, with Worker Result Manifest LAST. Hashing and structural verification are artifact checks only.

### Canonical provenance

- Exact task: docs/research/tasks/sc001-h1-003-r1-multiplicity-decision-freeze.json, task-head cd0dab2b48918a57abf0998cc4aa4e56067bc5e8; blob d8f97c971f8197386aa4d5b92e4e5eec13c7f180.
- Trigger: docs/research/sc001-h1-work-event-trigger-instructions-v0.1.md.
- Worker: docs/research/sc001-h1-historical-indicators-project-instructions-v0.1.md.
- Strategy: docs/research/sc001-h1-x1-historical-research-program-strategy-v0.1.md.
- Benchmark: docs/research/sc001-historical-indicator-benchmark-batch-design-v0.1.md.
- Ledger: docs/research/sc001-historical-indicator-benchmark-variant-ledger-v0.1.json.
- Feature governance: docs/research/sc001-feature-indicator-research-governance-v0.1.md.
- Incremental boundary: docs/research/sc001-incremental-feature-testing-protocol-v0.1.md.
- Adaptive/dependence governance: docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md.
- Contamination: docs/research/sc001-contamination-registry-v0.41.json.
- Architecture: docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.3.md.
- Result schema: docs/research/sc001-worker-result-manifest-schema-v0.1.json.

Only exact task references were read as research specification. The supplied ready_for_review event, PR identity/title and repository ID 1149728560 were checked; no replacement tasks were searched. No prior claims, terminal receipts or Strategy review comments were present on PR #432 at claim time. The matching worker claim and 3-hour lease are in the PR body.
