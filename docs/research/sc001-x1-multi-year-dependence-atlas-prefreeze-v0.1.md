# SC001 — X1 Multi-Year Dependence Atlas Prefreeze v0.1

Date: 2026-10-04
TASK_ID: SC001-X1-002
WORKER_ID: X1_CROSS_ASSET_STRUCTURE
AUTHORIZATION_CLASS: DESIGN_ONLY
Terminal: X1_ATLAS_PREFREEZE_READY_FOR_STRATEGY
Adaptive classification: ADAPTIVE_DISCOVERY_GENERATED
Origin: PR #433
Assigned branch: sc001/x1/SC001-X1-002-dependence-atlas-prefreeze
Dispatch/current main: c65021d200b417bda7cd24f64a1bca48c7c2bb89
Starting PR head: 08878c6f8c51885a9e9519bfa8cc962a12813ac0
Task blob: 09e4b6c3f11437b41e60df5d10d23006c07506f2

This is a complete outcome-blind design submitted for Strategy Manager acceptance. All numerical rules below are predeclared design choices, not measurements, optimized settings or claims of available clean data. No implementation, market analysis or execution occurred. READY_FOR_STRATEGY does not authorize X1-003 or certify the shared-data gate.

## SOURCE / RESOURCE BINDING RULE

Use the shared Binance USD-M perpetual public historical completed 1m trade-price kline source class. No spot, delivery futures, mark/index-price substitution, venue substitution or reconstruction from a different feed. Source semantic incompatibility means DEFER_SOURCE, not a new source chosen by this worker.

H1-004/shared-backbone qualification must bind the physical inventory once. Reuse exact verified resources and derived tables rather than redownload or independently normalize them. RESOURCE_ID and DERIVED_ID remain UNBOUND in this design.

Canonical DATASET_KEY fields: source_provider; source_host/endpoint_class; market_type; exact instrument identity or frozen universe ID; data_kind; granularity/archive class; UTC_start; UTC_end_exclusive; exact filename/query identity rule; semantic version. Canonical JSON uses UTF-8, sorted object keys, no insignificant whitespace and literal UTC strings. RESOURCE_ID = SHA256 of that serialization. No strategy name enters the resource identity. Reuse existing registry canonicalization verbatim; disagreement is an identity gate, not permission to mint duplicates.

Keep individual archive identities at the shared backbone's existing granularity; do not concatenate source files merely to obtain an X1-specific raw ID. A sorted manifest of parent IDs identifies the atlas resource set. DERIVED_ID binds ordered parent IDs, transform implementation hash, exact configuration hash and schema version under the shared-resource policy. Required derived columns: immutable contract identity, canonical symbol, UTC bar start/end, availability convention, completed status, close, trade count, validity mask, source lineage and PIT membership. Volume is not used in v0.1.

Before future body access, a GitHub binding receipt must record resource/derived IDs, hashes, universe and partition manifests, prior-use findings, approved evidence role, code/config hashes and both H1/X1 freeze approvals. Neither file presence nor this design permits an access receipt to be assumed. No registry entry is written in this task.

## OUTCOME-BLIND UNIVERSE

A contract identity is venue + market type + original instrument identity + listing epoch + denomination/multiplier version. Renames, redenominations and relistings are not silently spliced. Ambiguous identities are ineligible with a recorded reason.

Anchors are exactly BTCUSDT and ETHUSDT in their qualified USD-M perpetual identities. Both must qualify; no replacement anchor. Exclude non-USDT settlement, dated contracts, leveraged/index-basket tokens, stablecoin-underlying contracts and ambiguous mappings using versioned instrument metadata alone.

Build a finite retrospective pool from the PIT listing/delisting ledger before the frozen cutoff, including delisted contracts. No current-only list, realized returns, liquidity/volume ranking, correlation or survivorship-to-cutoff requirement. Order non-anchor identities by SHA256 of UTF-8 "SC001-X1-ATLAS-v0.1|"+contract_identity; bytewise contract identity breaks a hash tie. Retain the first 24, or all if fewer; require at least 8. Hash ordering is an outcome-blind budget, not a claim that this is a representative sample of all crypto.

Of N pool identities, reserve the last ceil(N/4) in this ordering as NODE_RESERVE. Never inspect their prices, summaries or use them as common-factor constituents during Selection. The others are DISCOVERY_POOL. This fixed partition cannot change because of availability or results.

For each UTC calendar month, eligible nodes must have been listed for at least 180 complete calendar days at month start and not yet delisted. Select the first 10 eligible DISCOVERY_POOL identities in the frozen hash order, plus the two anchors. No new entry midmonth. Delistings/identity breaks terminate eligibility immediately; no intra-month replacement. A future listing enters only by this past-membership rule. The retrospective pool limit is explicitly a historical sampling frame; membership at each observation still uses only then-effective facts.

The maximum simultaneously active discovery universe is 12; across all months it is at most 20 identities (18 non-anchor discovery identities + 2 anchors). All pair opportunities, including delisted/missing/failed ones, remain in the ledger. There is no removal of losing nodes. Month-level eligibility uses only instrument metadata, not realized outcome coverage. Missing data causes masked observations or a gate failure, not a ranked replacement.

## HISTORICAL CUTOFF / PARTITIONS

Fixed exclusive cutoff C = 2026-10-01T00:00:00Z. No rolling "latest" cutoff or extension in v0.1.

Using only a subsequently authorized coverage/identity metadata qualification, enumerate complete UTC months before C. A source-eligible month has unambiguous PIT metadata, both anchor identities active and continuous, and a verified daily archive/coverage manifest for every day of every selected discovery identity's active tenure. Listing/delisting absences are structural absence, not missing files. Coverage qualification must not export return/price summaries. NODE_RESERVE coverage metadata may be checked, its price bodies may not.

Select the longest contiguous run of source-eligible whole months; ties go to the earliest start. The run is common at the shared-source/calendar level for the PIT panel, not a requirement that every node survives throughout history. No outcome-dependent start date, silent shrinking around volatility or favorable subperiod. Record all rejected intervals and metadata reasons. If the last eligible month predates September 2026, record the gap explicitly; do not extend C. Unknown coverage cannot be treated as complete.

Require at least 36 complete months for this multi-year design. This is stricter than the H1 120-day minimum and does not redefine H1. If unavailable, DEFER_INSUFFICIENT_HISTORY; do not fall back to a shorter favorable study.

For the selected M-month span:
- first 6 months: CALIBRATION/WARMUP, no survivor ranking;
- next M-18 months: SELECTION, at least 18 months;
- final 12 months: CHRONOLOGICAL_HOLDOUT, untouched by research selection.

Boundaries are exact month starts, computed mechanically and recorded before any research body access. No moving a contaminated holdout to another conveniently clean historical interval. If the assigned holdout is contaminated/reserved by prior H1/X1/other relevant access, DEFER_CLEAN_HOLDOUT and request separately frozen fresh evidence. Source coverage is not contamination clearance.

## CAUSAL CLOCK / MISSINGNESS

Bar k covers [k,k+60 seconds), labelled by its exclusive end t=k+60 seconds. r_i(t)=log(C_i(t)/C_i(t-60 seconds)) is defined only for two consecutive qualified completed positive-price closes in the same contract segment. No cross-gap, cross-listing or cross-denomination return.

Historical analytical availability of a completed bar is assigned t+60 seconds. This one-minute embargo is a conservative research convention, not measured transport latency. Actual receive/publication time remains unqualified; no live-actionability claim follows from it.

At analytical decision a=t+60 seconds, features may use bars ending at or before t only. Forward response Y_j,h(t)=log(C_j(a+60h seconds)/C_j(a)), for h in {1,3}. The response-entry close C_j(a) is used solely to define the future response, never as a feature available at t. No response begins inside the source feature bar. L0 uses r_j(t) as a contemporaneous descriptive response and cannot be predictive evidence.

Every response requires all constituent one-minute bars, not just matching endpoints. Each bar must be completed, valid and contain at least one trade; otherwise missing. No zero/last-price fill, interpolation, carry-forward, backfill, resampling across a missing interval or imputation through delisting. Zero observed return with valid trades is retained.

All regressions, correlations and masks are pair-specific but identical between their raw/control/robustness views. Day validity requires at least 95% of possible aligned analytical decision minutes for that pair/profile, before shock conditioning; otherwise the entire pair/profile day is unavailable. Denominator includes all scheduled eligible minutes. Report missing days as missing, never as favorable zero effects.

Training, shock lookbacks and response windows may not cross partition boundaries without explicit past-only use below. Purge training origins whose final response is not strictly before the daily fit boundary. Last four minutes of a partition cannot create a response in the next partition. No holdout row supplies a Selection feature or fit.

## TRACK A — BTC/ETH ANCHORS

Track A contains BTCUSDT -> each eligible discovery non-anchor and ETHUSDT -> each eligible discovery non-anchor. Those are the only directional anchors. BTC/ETH mutual relationships may be displayed under Track B's descriptive ledger but are not anchor-target survivors. Reverse target -> anchor views, if inspected, belong to Track B and cannot become new anchors.

At most two Track A survivors: at most one per anchor and distinct target identities. This cap is not filled by force. No change to target membership, anchor identity or direction after outcomes.

## TRACK B — BROAD NETWORK

Enumerate all ordered, distinct pairs in the eligible discovery panel, excluding Track A directions already recorded there. At most 380 unique directed pairs across both tracks for a 20-node discovery pool, before PIT/missingness restrictions. Enumerate all even when no valid sample exists; do not hunt for extra pairs.

Persist compact signed edge/profile tables and fixed-calendar views, not giant time-by-pair arrays in GitHub. No community detection, clustering search, additional network statistics or new methods in v0.1. Track B is descriptive/calibration and bounded survivor selection only. Every selected edge is ADAPTIVE_DISCOVERY_GENERATED.

At most two Track B survivors; exclude anchor-involving edges from Track B survivor eligibility to preserve exactly two fixed anchors in the actionable shortlist. Broad non-anchor -> non-anchor directions remain eligible. Reverse directions of the same unordered pair cannot both survive; deterministic selection order below resolves ties.

## LAG PROFILE

Exactly three labelled views:
- L0: same completed-bar response r_j(t), contemporaneous only.
- L1: one-minute cumulative response after the fixed one-minute availability embargo.
- L3: three-minute cumulative response after the same embargo.

This is a bounded profile, not a best-lag search. Inspect/report all three wherever eligible. No intermediate lag, negative-lag sweep, band refinement, finer offset, alternate embargo or horizon extension.

One future holdout horizon is fixed now for every survivor: h=3 minutes after availability, label L3. L1 is a sign/persistence diagnostic and cannot replace failed L3. L0 can never select a trading horizon. This choice defines an analytical response timescale, not a mechanism-derived trading holding period; an economic mechanism and executable-price gate remain mandatory later.

## PRIMARY / ROBUSTNESS METRICS

One primary metric family: signed Pearson correlation. For each pair/profile, raw Pearson(r_i(t),Y_j,h(t)) is DESCRIPTIVE_DEPENDENCE only. The controlled version is Pearson(u_i(t),e_j,h(t)) where u and e are prequential residuals defined below. L0 uses its contemporaneous response. No p-value table/ranking.

At most one robustness metric: Spearman correlation of the same two controlled residual series on exactly the same valid observations, average ranks for ties. It is sign/monotonicity robustness, never an alternate winner statistic. Do not add mutual information, transfer entropy, Granger grids, nonlinear transforms or ML.

Primary aggregation is calendar based: compute each valid UTC day's correlation, clip numerical values only to [-1+1e-12,1-1e-12] for Fisher transformation, average daily Fisher z equally within a month, then average valid monthly z equally. Display tanh of that mean for interpretability. A valid month requires at least 20 valid days; fewer means unavailable. Pooled minute correlations are not primary decisions. Constant/zero-variance residuals yield undefined, not zero or automatic PASS.

"Incremental support" means a stable linear residual association beyond the frozen nuisance controls. It does not mean forecast-loss improvement, proven causation, trade PnL or economic significance. Those would need separately authorized tests.

## CAUSAL COMMON-FACTOR CONTROL

For each pair i,j and minute s, define m_ij(s) as the equal-weight mean of valid one-minute returns of the month's eligible discovery nodes excluding both i and j. No NODE_RESERVE input. Require at least three remaining constituents and all those predetermined constituents valid at s; otherwise m is missing. Equal weights are fixed, not estimated from full history. Excluding both nodes avoids mechanically subtracting the leader or target from itself.

Nuisance vector Z_ij(t): intercept; target returns r_j(t),r_j(t-1),...,r_j(t-4); and m_ij(t),m_ij(t-1),...,m_ij(t-4), with lag indices in minutes. For L0 only, omit r_j(t) to avoid putting the dependent variable directly into its own regressors; use r_j(t-1) through r_j(t-5). L0 and predictive views therefore have explicitly different interpretations.

At each UTC day start d fit two OLS models on the preceding 90 calendar days, using only eligible origins with all responses strictly before d:
r_i(t) = Z(t)*b_x + u_i(t);
Y_j,h(t) = Z(t)*b_y,h + e_j,h(t).
Freeze coefficients for the whole next UTC day. Each profile has its own response coefficients, one algorithm and no parameter search. Historical training rows retain their then-effective membership/factor values.

Require at least 60 valid training days, 50,000 complete training rows, full column rank and condition number <=1e8 after past-training-only non-intercept standardization. Use deterministic QR OLS; zero-variance columns, missing constituents or conditioning failure invalidate that day's fit. No ridge tuning, column dropping, fallback model or rescue.

For prequential Selection, training may use earlier calibration/Selection rows only. During holdout, an automated sealed evaluation may update nuisance models from already elapsed holdout days under this unchanged daily rule, without human viewing or adaptive decisions. This is prequential validation, not a single frozen-coefficient test. Prior Selection data can warm the first holdout fit; holdout targets never feed earlier decisions.

No full-history PCA, backward-applied beta, future membership weights or response-based refitting schedule. Controls reduce specified confounding; they cannot establish causality.

## ROLLING STABILITY / SEARCH LEDGER

Fixed views only: UTC day, calendar month, calendar year, and trailing 90-calendar-day windows ending at month end. Rolling views are descriptive; only non-overlapping calendar months enter the survivor stability rule. Years with fewer than 6 valid months are labelled insufficient. No selected hour, weekday, custom volatility regime or post-outcome episode.

Every planned pair/profile receives a ledger row, including empty/failed cells. Required fields:
design_version/config_sha256; TASK_ID/worker; track; ordered source/target contract identities; immutable unordered-pair ID; anchor flag; source/resource/derived IDs; universe/membership hash; partition/node-role; exact interval; analytical availability rule; profile/horizon; metric and control mode; shock/regime label (ALL, SHOCK_POS, SHOCK_NEG only); code/transform hashes; nuisance training interval/fit validity; scheduled and valid minutes/days/months; each missingness/exclusion reason and count; inspected_at_utc; authorized access receipt; contamination/lineage refs; effect/sign/stability summaries; selection order/rule result/reason; shortlist version; holdout eligibility/access state; terminal disposition.

All inspections, failed variants and manual summaries count. Do not omit nulls, reverse edges, unavailable periods or negative findings. Unplanned views are STOP_SCOPE, not an unlogged notebook experiment.

## SHOCK-CONDITIONED DESIGN

Exactly one shock definition, on the raw causal leader one-minute return:
z_i(t)=r_i(t)/sigma_i,d,
where sigma_i,d is the uncentered RMS of valid one-minute returns over the 30 calendar days strictly before UTC day d containing t. Require 20 valid days (>=95% valid minutes each) and positive finite RMS; otherwise no qualified shock. Freeze sigma for the day.

Event iff abs(z)>=3. Positive and negative signs are recorded separately; no threshold ladder, alternate lookback, quantile tuning or activity/volume companion. Optional companion budget used: 0.

Per leader keep the first qualifying event and suppress further events for 10 elapsed minutes, across UTC day boundaries. Suppression does not change because of target outcomes. Evaluate the same controlled Pearson/Spearman families, masks and L1/L3 response definitions. For shock propagation use orientation-aligned residual response s_i*e_j,h (s_i=sign of leader shock) as a descriptive event summary; this summary is not an additional promotion test.

Primary shock claim at L3 requires the selected unconditional relation sign to agree with the median orientation-aligned response in both shock signs, at least 30 events per sign, at least 12 distinct event days per sign and at least 6 valid months in Selection. Otherwise SHOCK_INSUFFICIENT or SHOCK_NOT_SUPPORTED. Count independent leader episodes and calendar breadth, not each target response as a new independent shock.

Shock status cannot select a different pair, rescue failed unconditional stability, change relation sign or consume another horizon. It is a separate support label for already eligible survivors. No shock-based trading strategy is authorized.

## SURVIVOR BUDGET / SELECTION

Eligibility for a directed relationship:
1. Valid L3 controlled primary estimates in >=12 Selection months and >=2 calendar years with >=6 valid months each.
2. Nonzero aggregate L3 sign, frozen as s. At least 75% of its valid Selection months have that sign, and each adequately covered year has that sign.
3. At least 60% of valid months have abs(controlled Pearson)>=0.01; this is a fixed weak-information screening floor, not an economic hurdle or significance level.
4. Aggregate L1 controlled sign equals s; L1 need not exceed the L3 size floor.
5. L3 controlled Spearman sign equals s. Undefined estimates fail eligibility.
6. No unresolved identity, contamination, model or source gate.

Negative relations are allowed: their sign is frozen in Selection, never flipped in holdout. Raw correlation alone and shock-only results cannot qualify.

Among eligible relationships, use deterministic SHA256("SC001-X1-SURVIVOR-v0.1|"+source_identity+"->"+target_identity) ordering, then bytewise IDs. Do not rank by p-value, correlation magnitude or best lag. Track A selects at most one per anchor with distinct targets; process BTC then ETH. Track B selects at most two, each with a distinct unordered pair. Do not refill rejected holdout slots from the Selection runner-up list.

Total <=4, A<=2, B<=2. All unselected eligible edges remain descriptive and cannot silently enter later tests. The shortlist freezes ordered pair, sign, L3, timing, coefficients-update rule, shock definition, resource/partition identity, code/config hashes and rejection rules before any holdout report is opened. A zero shortlist is an informative terminal result.

## UNTOUCHED HOLDOUT

Chronological holdout is the final 12 source-eligible months assigned above. Full prior-use lineage, including the inherited contamination registry chain and H1/shared-source access, must be audited later at metadata level. This task does not declare any date/asset clean. Any relevant prior Selection view invalidates a Confirmation label for that implementation.

NODE_RESERVE is a second, entirely uninspected reserve: it does not contribute to selection, factor models, diagnostics, plots or training. Reserve nodes are not replacement targets for a failing survivor. Their actual cross-node experiment requires a separate design frozen before opening them. Thus v0.1 provides the required outcome-blind node reserve without pretending that changing the target validates the exact selected pair.

Evaluate the frozen <=4 exact pairs once on chronological holdout. Require >=9 valid holdout months; each half-year must have >=4 valid months. A survivor needs the Selection sign in >=75% of valid months, that sign in both adequately covered half-years, abs(aggregate controlled Pearson)>=0.01, and the frozen Spearman sign. No alternate horizons or screening of runner-ups in holdout.

For uncertainty, use daily Fisher-z observations on the complete holdout calendar with missing days retained as missing. Apply a synchronized circular moving-block bootstrap of 30-calendar-day blocks, 9,999 replicates, seed 433002, truncate to original calendar length. Each replicate recomputes the equal-month mean; same block draws across shortlisted edges preserve cross-edge dependence. Replicates lacking >=9 estimable months are invalid; <9,000 valid replicates means DEFER_UNCERTAINTY, not a fallback IID test.

Orient the statistic by frozen Selection sign. A one-sided bootstrap lower percentile bound at alpha=0.05/4 must exceed zero for each retained pair, using the fixed denominator 4 even if fewer are selected. This is a Bonferroni simultaneous interval gate for at most four predeclared L3 endpoints, not a discovery p-value leaderboard. The block-bootstrap approximation assumes adequate short-range dependence at the 30-day block scale; 12 months is limited evidence. Persistent longer regime dependence remains a reported limitation, not a reason to change block length after outcomes. No formal causal/economic Confirmation follows from this statistical gate.

Holdout shock support uses the same formula/count rules, but requires >=4 covered months, >=20 events per sign and >=8 event days per sign; no separate significance claim. Unconditional and shock labels remain separate. No partial release of holdout reports to revise the method. Failure ends that version; no second look, sign swap, horizon swap or reserve substitution.

## HIGH-RESOLUTION ESCALATION

At most two exact chronological-holdout survivors may be proposed later: first one Track A and one Track B in frozen shortlist order, then an unused slot may go to the next surviving relationship in that same order. No ranking by holdout effect size. Freeze identities/sign/horizon before new access; no full-universe high-resolution acquisition.

A separate authorized task must bind exact 1s/trade source resources, dates, byte/compute budgets and evidence role. Purpose only: temporal ordering, stale-print/asynchronous-sampling artifacts, source availability versus delayed target updating, and remaining actionable lag under the frozen L3 horizon. No best subsecond lag, fee tuning or horizon rescue.

High-resolution views of the same historical holdout interval are artifact diagnostics, not independent new Confirmation. Fresh/otherwise genuinely untouched evidence and executable-price/receive-time qualification remain necessary for tradability. If historical receipt information is absent, mark actionability unqualified; an event-time ordering PASS is insufficient.

## TERMINAL DECISION SEMANTICS

Future research labels are separate:
- DESCRIPTIVE_DEPENDENCE_ONLY: contemporaneous/raw association; no transfer claim.
- PREDICTIVE_INCREMENTAL_SUPPORT_SELECTION: frozen controlled L3 screen survives; adaptive nonpromotional.
- SHOCK_PROPAGATION_SUPPORT / SHOCK_NOT_SUPPORTED / SHOCK_INSUFFICIENT: separate event-conditioned status, never unconditional rescue.
- HOLDOUT_ELIGIBLE: shortlist sealed and untouched-evidence gates pass; no holdout result implied.
- HOLDOUT_SUPPORT / HOLDOUT_NOT_SUPPORTED / HOLDOUT_INSUFFICIENT: exact predeclared chronological evaluation.
- NO_SURVIVOR: valid study, none passed; preserve ledger and stop this version.
- DEFER_SOURCE / DEFER_INSUFFICIENT_HISTORY / DEFER_CLEAN_HOLDOUT / DEFER_UNCERTAINTY: named missing precondition, not a negative market finding.
- STOP_SCOPE or STALE_CONTEXT_REVALIDATION_REQUIRED: authorization/context boundary failed.

None is a trading-candidate promotion. Mechanism fingerprint, novelty, economic payer, executable costs/latency, capital-time and fresh evidence remain later gates. This task's actual terminal token is X1_ATLAS_PREFREEZE_READY_FOR_STRATEGY; no research-result label above has been earned.

## CONTAMINATION / MULTIPLICITY

C4 standalone leader continuation and C6 paired residual convergence remain terminal in their tested architectures. X1-001's A/B overlap rejection and C basket-source defer remain unchanged. The broader atlas studies descriptive/predictive structure under the revised manager program; it does not reopen those results, manufacture a new payer or reuse their terminal windows as Confirmation.

Every looked-at pair/direction/profile/calendar view counts in the complete ledger. Maximum universe/directed-pair bounds are structural, not an authorization to expand through extra nodes. Selection, nuisance calibration and published legacy summaries are nonpromotional. Atlas Selection never becomes X1 Confirmation. H1 data sharing does not erase prior use. P1 protected evidence, C8/Candidate 2 and the fresh primary window are not generic reserve data.

Registry v0.41 inherits prior registries. Its latest file alone cannot prove cleanliness. Full relevant lineage clearance is a future binding prerequisite; no registry/shared-state edits were made here.

Existing RB003/RB004/RB006 clock/reference/context concepts are acknowledged only in their previously scoped roles via X1-001. No new empirical reusable block exists: NO_REUSABLE_BLOCK_IDENTIFIED. Funding-state RB022 is not inserted into the atlas.

## DO NOT DO

No market-body access, return/correlation computation, PnL, protected outcomes, research-source network, Runner, Test Executor, VPS or collector work in this task. No additional source discovery or external documentation lookup.

No best pair/lag/horizon search, threshold ladder, activity companion, new anchors, full-history beta/PCA, nonlinear models, hidden missingness fill, outcome-conditioned universe edits, chosen regime, same-evidence rescue or reclassification of used data as clean.

No shared roadmap, governance, Strategy State, contamination or reusable-registry mutation. Out-of-domain ideas are CROSS_DOMAIN_REFERRAL only. No merge, close, retarget, auto-merge or branch deletion. The exact task contract and source documents remain unchanged.

## TERMINAL DISPOSITION

X1_ATLAS_PREFREEZE_READY_FOR_STRATEGY.
The design is fixed for review; resource IDs, actual coverage, identities and clean evidence remain unqualified. This is deliberate mechanical late binding, not permission to tune the design after viewing data.

Required next decision: Strategy Manager accept/reject this exact design and align the operational roadmap before revised X1 execution. Shared-backbone qualification and the joint H1/X1 pre-outcome freeze barrier must then pass. No successor task is launched here.

Three-lens self-review:
- Financial/trader: weak stable dependence is not fee-paying alpha. L3 is a research timescale; mechanism and executable economics are deferred explicitly.
- Programmer/trader: no new engine; deterministic source/node/calendar rules, no forward fill, past-only fits, sealed holdout and exact lineage. Missing source or ill-conditioned fits fail closed.
- Mathematician/statistician: bounded profiles, calendar-level stability, deterministic survivor ordering, four-endpoint holdout correction, isolated node reserve. Bootstrap validity is approximate and long-regime dependence remains a limitation.

Safety receipts:
outcome_accessed=false
protected_evidence_accessed=false
market_rows_read=false
network_accessed=false
test_executor_job_launched=false
runner_bundle_created=false
runner_bundle_executed=false
vps_data_read=false
collector_changed=false

network_accessed=false denotes no research-source network/acquisition; authorized GitHub control-plane reads/writes occurred. Published legacy summaries were read only as prescribed lineage; no new/raw outcome was opened.

Accounting: research executions 0/0; network runs 0/0; repair cycles 0/0; candidate relations actually evaluated 0; empirical survivors 0. Two allowed repository artifacts only, at most two planned worker commits (budget three). The task ID used in the result schema is a design-work identifier, not a new outcome experiment.

PROPOSED_SHARED_STATE_CHANGE: NONE by worker; manager's already-required roadmap alignment remains a prerequisite.
MERGE_AUTHORIZED: false
SHARED_STATE_WRITE_AUTHORIZED: false
CONTINUATION_REVIEW_REQUIRED: true
STRATEGY_REVIEW_REQUIRED: true

Completion order: persist this exact result, read back and verify its content/hash, refresh main and exact task/PR/claim/reviews, create Worker Result Manifest LAST, then exactly one terminal PR receipt. No additional repository artifact follows the manifest.

Canonical source snapshot (Git blob identities; all read from current main above):

| Path under docs/research/ | Git blob SHA |
|---|---|
| sc001-x1-work-event-trigger-instructions-v0.1.md | 1c71d538bc451273a91ff237bad4bcf214e98d52 |
| sc001-x1-cross-asset-project-instructions-v0.1.md | c2e42f09fd97a086ff5a76ad61513ab6418507ce |
| sc001-h1-x1-historical-research-program-strategy-v0.1.md | a90223723923170f3984193b256231760129b606 |
| sc001-cross-asset-information-transfer-landscape-v0.1.md | 18adcdd4abac3c6fea27ccd02ee730dc0e1462ed |
| sc001-cross-asset-source-and-clock-feasibility-v0.1.md | 39dfaa094c3b56ffae6394267b39f0e85b1111ad |
| sc001-shared-data-and-resource-coordination-v0.1.md | cff6ec686601db030f4d8d1a16cad050745cf0bd |
| sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md | 4223ca29afe540a7998c1af82af2cf671d1129ca |
| sc001-contamination-registry-v0.41.json | df03cf18222fafb7cb8bbc4f69c720c03ecc528e |
| sc001-reusable-market-building-blocks-registry-v0.9.md | 9c4b3517a99fc91ca02493e0c9e4e2fcee646ba9 |
| sc001-execution-worker-routing-and-automation-architecture-v0.3.md | 8a6010e2fdc6d914f73c165701f93bba4ac7acb0 |
| sc001-worker-result-manifest-schema-v0.1.json | e9507a2b88abd86316695baa841b3194b9b52898 |
