# SC001 — Historical Research Program Strategy v0.1

Date: 2026-10-04
Status: STRATEGY MANAGER FINAL PROGRAM PLAN / USER-APPROVED DIRECTION / NO EXECUTION AUTHORIZATION
Scope: BotMarketplace / SC001 / H1 + X1 historical research program
Source of truth: GitHub
Parent controls:
- docs/research/sc001-research-strategy-agent-charter-v0.1.md
- docs/research/sc001-feature-indicator-research-governance-v0.1.md
- docs/research/sc001-feature-indicator-taxonomy-v0.1.md
- docs/research/sc001-incremental-feature-testing-protocol-v0.1.md
- docs/research/sc001-contamination-registry-v0.41.json
- docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.3.md
- docs/research/sc001-shared-data-and-resource-coordination-v0.1.md

This document records the final strategy direction after two independent three-lens reviews. It does not authorize data-body access, outcomes, Runner execution, Test Executor jobs, collector mutation, or a roadmap/governance rewrite by itself.

## 1. Program objective

Run H1 and X1 as sustained historical research lanes that do not wait on unrelated prospective collectors.

H1 objective:
- learn the scoped historical usefulness of causal indicator/feature primitives across roles R1-R6;
- avoid indicator leaderboards and same-evidence parameter mining;
- progress from predeclared historical Discovery to independent asset/time Confirmation and only later to fresh/forward evidence.

X1 objective:
- map cross-asset dependence and information-transfer structure;
- distinguish contemporaneous common-factor correlation from predictive lead-lag;
- identify whether delayed information incorporation is stable, incremental, economically interpretable and tradable;
- permit broad descriptive discovery before requiring a complete economic mechanism, while preserving strict promotion firewalls.

Core principle:
OBSERVE BROADLY -> SELECT NARROWLY -> EXPLAIN ECONOMICALLY -> FALSIFY CHEAPLY -> VALIDATE INDEPENDENTLY -> ONLY THEN DESIGN A TRADING CANDIDATE.

## 2. Second three-lens review — final corrections

### 2.1 Programmer / Trader

Retain one shared physical Historical Data Backbone when source semantics permit it.

Do not build separate H1 and X1 downloads/pipelines for the same Binance USD-M historical resource.

Required data-control separation:
- raw RESOURCE_ID is shared physically;
- deterministic derived datasets receive DERIVED_ID;
- evidence-access receipts remain task/program specific;
- physical presence never implies permission to inspect a block;
- one worker's Selection access must be reflected in contamination/evidence lineage before another program calls the same material untouched.

The backbone should favor:
- exact source identity and hashes;
- point-in-time instrument membership;
- listing/delisting continuity;
- causal completed-bar semantics;
- explicit missingness/gap rules;
- no hidden forward fill;
- deterministic transform hashes;
- compact GitHub metadata/summary artifacts, not giant market matrices in GitHub.

Heavy acquisition/compute may be serialized under shared-resource protection even while design/review work proceeds in parallel.

### 2.2 Financial / Trader

H1 must not answer only "does indicator X make money?"

Every feature is tested in an explicit role:
- R1 core signal;
- R2 state/regime;
- R3 filter/veto;
- R4 risk/sizing;
- R5 execution;
- R6 reference/normalization.

State/filter features can be useful even with no standalone directional alpha.
Incremental tests must report opportunity retention and block-level economic contribution, not only bps/trade.

X1's economically interesting object is delayed information incorporation, not raw correlation.

Distinguish:
- contemporaneous common-factor dependence;
- predictive lead-lag;
- stale-print / asynchronous-sampling artifacts;
- actual actionable information transfer.

Historical trade/bar lag is not automatically tradable lag. A surviving relationship eventually needs an executable-price/latency gate.

Prefer lower-fill architectures when information content is otherwise comparable. Four-fill paired trades require materially more headroom than a two-fill directional target trade.

### 2.3 Mathematician / Statistician

A broad X1 atlas creates severe multiplicity. Do not run a giant significance leaderboard.

Discovery atlas outputs are descriptive/calibration by construction.

Primary protection:
- no promotional p-value mining across all directed pairs/lags/regimes;
- record the complete search ledger;
- select only under a frozen survivor rule;
- all selected relationships become ADAPTIVE_DISCOVERY_GENERATED;
- untouched chronological/asset-node holdout is mandatory before promotion.

Use block/calendar-level inference rather than treating minute observations as IID.

Any market-factor/residual model must be causal:
- weights/parameters estimated from past-only calibration/rolling/expanding data;
- no full-history PCA/beta leakage into earlier timestamps.

Do not add nonlinear methods, transfer entropy, broad Granger grids or ML merely because they are available. Start with the simplest dependence model that can falsify the idea. Complexity is added only after simpler models leave an unresolved decision.

## 3. Joint pre-outcome freeze barrier

Before either H1 or X1 opens a new shared historical outcome body for research selection, BOTH programs should have their relevant design rules frozen.

This protects against cross-program adaptive contamination.

Minimum barrier:

H1:
- exact R1 hypothesis family;
- orientations/sign semantics;
- fixed horizons;
- family-wise multiplicity decision procedure;
- no sign flipping/winner picking.

X1:
- source/universe rule;
- historical partition;
- base resolution;
- directed lag grid or lag-band summary rule;
- factor-control construction;
- missingness rule;
- descriptive versus predictive outputs;
- survivor budget/selection rule;
- untouched holdout definition.

Shared data qualification/engineering may precede outcome inspection, but design may not be changed after seeing research outcomes without a new version and fresh evidence.

## 4. Historical Data Backbone

Preferred initial backbone:
- Binance USD-M perpetual public historical data;
- one common exact resource lineage usable by H1 and X1 when semantics match.

The existing H1 requirement of >=120 common complete UTC days remains a minimum viability gate, not the desired research horizon.

If materially longer common history exists, use the longest predeclared eligible contiguous span up to a frozen cutoff rather than choosing a favorable date range after outcomes.

Backbone qualification must resolve:
- exact 6-12 or broader program-specific universe under outcome-blind eligibility;
- source/resource identity;
- current local reuse;
- RESOURCE_ID;
- DERIVED_ID for causal 1m matrix where applicable;
- point-in-time instrument membership;
- coverage/gaps;
- prior-use/contamination;
- evidence partition boundaries.

H1 currently owns the unresolved source-identity lineage and may be the first worker to establish this reusable backbone. X1 should reuse it rather than redownload it, subject to its own access receipt and universe requirements.

## 5. H1 program

The reviewed eight-variant benchmark is Batch v0.1, not a permanent limit on all indicator research.

It is the first controlled batch. Future batches may add new economic primitive families only through a new predeclared budget and fresh evidence.

### H1-003 — R1 Multiplicity & Decision Freeze

Class:
DESIGN_ONLY / T0.

No market outcome access.

Freeze:
- exact directional R1 variants;
- hypothesis orientation/sign;
- primary block-level effect statistic;
- dependence-valid family-wise procedure;
- family-wise error target;
- no sign/horizon flip after outcomes;
- terminal family-level decision semantics.

Preferred statistical posture:
use a simple dependence-valid procedure. Holm over valid block-level tests is an acceptable default unless a justified max-stat/stepdown implementation provides clear value without unnecessary complexity.

### H1-004 — Shared Historical Backbone Qualification

Resolve the current DEFER_METADATA_ACCESS.

No directional outcome search.

Establish exact reusable source identity, coverage, universe, prior-use and resource lineage.

If the required read-only metadata surface does not exist, create a separately authorized minimal metadata-interface/registry task rather than browsing raw VPS data arbitrarily.

### H1-005 — Historical Calibration + Frozen Discovery

After the joint pre-outcome freeze and data gate.

Use the predeclared Batch v0.1 only.

Calibration may inspect:
- feature distributions;
- missingness;
- same-family redundancy;
- regime/state behavior;
- implementation correctness.

Directional Discovery:
- exact R1 variants only;
- fixed horizons/orientations;
- no best-symbol/hour/parameter search;
- aggregate breadth/stability, not historical winner picking.

R2/R3/R4/R6-only features do not receive standalone directional promotional claims.

### H1-006 — Independent Holdout / Chronological Confirmation

Use frozen implementation only.

Preserve asset breadth and later time evidence.

Any positive adaptive Discovery requires independent Confirmation before promotion.

### Later H1 batches

Only after Batch v0.1 resolves a decision:
- add P5 aggressive flow;
- P6 book/liquidity;
- P8 relative value;
- other primitives where source economics justify them.

Do not expand the batch merely to keep H1 busy.

## 6. X1 program

X1_CROSS_ASSET_STRUCTURE remains the worker ID.

Its mission is broadened from mechanism-first static screening to:

CROSS-ASSET DEPENDENCE -> PREDICTIVE LEAD-LAG -> STABILITY -> HIGH-RESOLUTION VALIDATION -> MECHANISM -> TRADABILITY.

Broad descriptive research is not a reopening of C4/C6 by itself.
Any promoted trading candidate must still pass the mechanism-overlap gate and cannot claim novelty merely because asset, lag or threshold changed.

### X1-002 — Multi-Year Dependence Atlas Prefreeze

Class:
DESIGN_ONLY / T0.

Freeze before outcome access:
- exact source and data identity;
- outcome-blind universe rule;
- historical partitions;
- 1m broad-screen resolution;
- small predeclared directed lag grid or lag-profile rule;
- primary linear dependence metric;
- at most one simple robustness metric;
- rolling/time stability views;
- market/common-factor model using past-only parameters;
- missingness/survivorship handling;
- search ledger;
- survivor budget;
- holdout/node/chronological reserve;
- high-resolution escalation rule.

No PnL.

### X1 two-track discovery structure

Track A — fixed anchors:
- predeclare a very small anchor set such as BTC and ETH before outcomes;
- examine their relationship to the frozen target universe;
- lower multiplicity and directly tests the user's flagship-leader hypothesis.

Track B — broad network discovery:
- all eligible directed relationships under the frozen universe;
- descriptive/calibration only;
- no direct promotional claim;
- any selected relationship is adaptive and requires untouched validation.

Do not add new anchors after viewing results without a new version.

### X1-003 — Multi-Year Dependence & Predictive Discovery

Broad stage may include:
- contemporaneous correlation/dependence;
- rolling/year/regime stability;
- directed lag profiles;
- positive and negative dependence;
- network/community structure;
- incremental prediction beyond target's own history and the causal common factor;
- one bounded shock-conditioned propagation design.

Do not choose "best exact lag" from an unrestricted grid and call it a mechanism.

Prefer a predeclared lag profile/band summary for broad discovery; freeze one actionable horizon only after selection and before holdout.

No massive p-value leaderboard.

### Shock-conditioned research

The user's motivating observation is explicitly in scope:
large/abnormal leader movement -> delayed follower response.

Freeze a small event-definition budget before data:
- causal return shock definition;
- optionally one activity/volume-conditioned companion;
- positive/negative directions handled prospectively;
- no threshold ladder after outcomes.

### X1-004 — Independent Holdout + High-Resolution Survivor Validation

Only a small frozen survivor set progresses.

Validate on untouched time and/or asset-node holdout.

Then move survivors from 1m to 1s/trades only where needed.

Purpose:
- detect aggregation/stale-print artifacts;
- verify temporal ordering;
- estimate how much apparent lag remains after causal availability;
- reject relationships that disappear at actionable resolution.

Do not acquire multi-year high-resolution data for the entire universe before the cheap 1m screen justifies it.

### X1-005 — Mechanism & Edge-to-Fill Gate

For validated survivors classify:
- common factor;
- stale/low-liquidity print;
- microstructure lag;
- cross-market price discovery;
- inventory/hedging transmission;
- forced flow;
- other economically identifiable mechanism;
- unknown.

Unknown is not automatically promotional.

Then apply:
- expected information scale;
- structural fills;
- fees/spread/slippage;
- latency;
- opportunity frequency;
- capital occupancy;
- capacity.

Only then may a trading candidate/fingerprint be proposed.

## 7. Evidence and contamination rules

Physical data reuse is encouraged; promotional evidence reuse is not assumed.

Every access records:
- TASK_ID;
- worker;
- RESOURCE_ID/DERIVED_ID;
- exact interval/assets;
- evidence role;
- fields/derived outputs opened;
- access time;
- resulting contamination classification.

Atlas Selection data cannot later become X1 Confirmation.

H1 feature Selection data cannot later become promotional Confirmation for that feature/version.

Because H1/X1 designs are now frozen before shared-history inspection, later cross-program knowledge does not retroactively change those frozen designs. New post-outcome ideas remain adaptive and require new versions/fresh evidence.

P1 protected/fresh collector data is NOT automatically a future H1/X1 Confirmation source. H1/X1 may require their own prospectively frozen current-data feed/collector when they reach forward validation. Reuse of P1 evidence requires exact semantic fit and explicit authorization; availability alone is not permission.

## 8. Computation / research-cost control

Do not equate agent utilization with research value.

Agents may work in parallel on T0 design/review.

Heavy data acquisition or compute can queue/serialize when needed to protect:
- disk headroom;
- Test Executor limits;
- protected collectors;
- shared resources.

X1 implementation should avoid materializing huge pair-by-time matrices in GitHub. Persist:
- resource identities;
- compact sufficient summaries;
- search ledger;
- selected survivor definitions;
- reproducible code/config hashes.

Use vectorized/block processing and deterministic transforms before considering more infrastructure.

## 9. Continuation / notification control

The observed silent-idle problem is real and warrants a small control-plane hardening.

Every terminal worker event should be eligible for continuation review, even when deep Strategy Review is not required.

Future terminal contract should distinguish:
- STRATEGY_REVIEW_REQUIRED;
- CONTINUATION_REVIEW_REQUIRED.

Strategy Control classifies terminal work into exactly one disposition:

- AUTO_CONTINUE
  One exact next T0/T1/T2 task is already authorized and unambiguous. Dispatch at most one.

- STRATEGY_ATTENTION_REQUIRED
  Deep Strategy Manager choice is needed. Notify the user and stop.

- USER_GATE_REQUIRED
  Exact T3 approval is needed. Notify the user with the exact action and stop.

- TERMINAL_IDLE_JUSTIFIED
  No decision-relevant successor exists. Notify the user briefly why the worker is intentionally idle.

Do not create busywork merely to avoid IDLE.

Notifications should be concise. Human attention is especially required for STRATEGY_ATTENTION_REQUIRED, USER_GATE_REQUIRED and terminal branch closure.

Add one low-frequency read-only orphan audit as a safety net, not as the primary dispatcher:
- recommended cadence: daily;
- detect terminal/READY work lacking a continuation disposition;
- no research execution or writes;
- notify only on anomaly.

This is justified by the already observed silent-idle/event-loss class and does not replace event-driven Work.

## 10. Antifragility future lane

Future marker:
docs/research/future-antifragility-research-lane-backlog-v0.1.md

No dispatch now.

Later consider a separate dedicated Project/worker for the medium/long-horizon R008/R009/R010/R003/safe-sleeve/convexity research lineage and connect it to the same worker -> terminal -> Strategy Control architecture.

Before doing so, Strategy Manager must decide whether it remains inside SC001 governance or receives a separate research-program namespace.

## 11. Optimized implementation sequence

Do not create one micro-task per paragraph.

Phase A — control and pre-outcome freeze, parallel:
1. harden terminal continuation/notification semantics;
2. H1-003 multiplicity freeze;
3. X1-002 atlas prefreeze.

No historical outcome body access required.

Phase B — shared data gate:
4. H1-004 establishes the reusable Historical Data Backbone / metadata identity;
5. X1 binds to the same verified resource where semantics fit instead of duplicating acquisition.

Phase C — historical Discovery, parallel subject to resource limits:
6. H1-005 Calibration + frozen Discovery;
7. X1-003 dependence/predictive/shock Discovery.

Phase D — independent validation:
8. H1-006 holdout/chronological Confirmation;
9. X1-004 holdout + high-resolution survivor validation.

Phase E — economic promotion:
10. H1 survivors enter role-appropriate incremental testing / Edge-to-Fill;
11. X1 survivors enter mechanism + Edge-to-Fill gate.

Phase F — fresh evidence:
12. only survivors receive prospectively frozen fresh/forward programs; do not assume the existing P1 collector is the appropriate source.

## 12. Do not do

- Do not run broad indicator parameter grids.
- Do not call a state/filter feature directional alpha without a separate R1 test.
- Do not run broad X1 p-value leaderboards.
- Do not select the historical best pair/lag and reuse the same history as confirmation.
- Do not use full-history factor parameters at earlier timestamps.
- Do not infer causality from correlation alone.
- Do not infer tradability from delayed prints alone.
- Do not download years of L2/tick data for the whole universe before cheap gates survive.
- Do not duplicate a verified raw historical resource for H1 and X1.
- Do not let physical data sharing erase task-specific contamination/evidence roles.
- Do not force an agent to remain busy when no decision-relevant next action exists.
- Do not use P1 protected evidence as generic H1/X1 confirmation.
- Do not resume antifragility work from memory alone; use its canonical lineage marker.

## 13. Strategic disposition

H1:
CONTINUE. Current idle state is not optimal because meaningful pre-outcome work exists.

X1:
CONTINUE UNDER REVISED PROGRAM. The prior X1-001 bounded defer remains valid for the three mechanism sketches it tested; it does not reject descriptive/predictive cross-asset market-structure research.

P1:
INDEPENDENT PROSPECTIVE LANE. It should not gate H1/X1 historical work.

Architecture:
NO NEW WORKER OR ORCHESTRATION SERVER REQUIRED FOR H1/X1.
Only the bounded continuation-notification hardening is justified.

Roadmap:
A narrow future operational/roadmap alignment is required before executing the revised X1 program, because the new descriptive/predictive Discovery phase is broader than the prior X1-001 mechanism-first task. Binding contamination, no-rescue and promotion rules remain unchanged.

DECISION QUALITY / RESEARCH COST remains the controlling objective.
