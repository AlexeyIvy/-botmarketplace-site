# SC001 — Delegated User Authorization Policy v0.1

Date: 2026-10-01
Status: PROPOSED / PENDING ONE-TIME USER RATIFICATION
Scope: BotMarketplace / SCALPING RESEARCH / SC001

Parents:
- docs/research/sc001-research-strategy-agent-charter-v0.1.md
- docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.2.md
- docs/research/sc001-shared-data-and-resource-coordination-v0.1.md

## 1. Purpose

Reduce unnecessary user blocking while preserving:
- evidence integrity;
- explicit control over irreversible/high-risk actions;
- bounded network/resource use;
- no silent outcome mining;
- no collector mutation;
- no paid-data commitment;
- no trading or credentialed exchange actions.

The user should not need to approve ordinary research mechanics one step at a time.

## 2. Authorization model

Use four authorization tiers.

### T0 — ALWAYS_AUTOMATIC

No user approval required.

Allowed:
- GitHub reads;
- canonical document creation under already authorized task scope;
- issue/task state updates;
- local static analysis;
- code review;
- metadata-only local inventory;
- deterministic hashing;
- reuse of VERIFIED datasets under an already authorized evidence-access receipt;
- offline synthetic/unit/self-tests that do not open protected/raw outcomes;
- routine non-outcome Strategy Manager review;
- source/documentation lookup with no private/raw market-data acquisition.

Constraints:
- must stay inside task budget;
- no network market-data acquisition;
- no protected outcome access;
- no collector mutation;
- no paid service;
- no real-money/trading action.

### T1 — STRATEGY_MANAGER_DELEGATED

After this policy is ratified, the user delegates authority to the SC001 Strategy Manager to issue task-specific authorization automatically, without another user prompt, when ALL conditions pass.

Eligible actions:
- Test Executor public_research metadata/HEAD/source-semantics probes;
- public historical market-data acquisition;
- public archive body downloads;
- bounded READ_ONLY audits of already authorized non-protected data;
- deterministic source normalization / derived-data construction;
- bounded historical Selection/Calibration/Discovery outcome runs on preallocated evidence;
- bounded fresh/prospective S0/sentinel outcome runs when they are the exact next stage already pre-frozen and all scientific gates pass;
- exact rerun/recovery only when the protocol explicitly defines idempotent recovery and no outcome-informed change occurred.

Mandatory prerequisites:
1. exact TASK_ID and worker;
2. Strategy Manager review PASS;
3. structured mechanism disposition eligible where applicable;
4. exact protocol/fingerprint/implementation hashes frozen before access;
5. contamination/evidence role preallocated;
6. no same-evidence rescue;
7. task-specific run/data/resource budgets frozen;
8. shared resource reservation PASS;
9. disk/rate/collector-protection gates PASS;
10. Test Executor current limits PASS;
11. MAX_CONCURRENT_OUTCOME_BEARING_FAMILIES respected;
12. no paid/licensed data;
13. no secrets/trading credentials;
14. no collector mutation;
15. no Runner Probe bundle execution.

Default T1 limits per task unless Strategy Manager selects lower:
- MAX_NETWORK_RUNS = 1;
- MAX_OUTCOME_RUNS = 1;
- MAX_RETRIES_AFTER_LAUNCH = 0 except transport retry already implemented inside the frozen program;
- MAX_TOTAL_NETWORK_BYTES = 10 GiB;
- MAX_SINGLE_DATASET_BYTES = 5 GiB;
- MAX_PEAK_WORKSPACE_INCREMENT = 15 GiB;
- MAX_RUNTIME_PER_RUN = current Test Executor hard cap;
- MAX_NEW_VARIANTS = exact preregistered count only;
- source hosts/endpoints frozen before execution.

T1 automatic execution is valid only when a canonical TASK_AUTHORIZATION artifact exists and is bound to exact hashes/budgets.

### T2 — STRATEGY_MANAGER_DECISION + USER_NOTIFICATION, NO WAIT

These actions may proceed automatically after Strategy Manager decision but must notify the user; notification is informational and does not block execution.

Eligible only if already inside the ratified envelope:
- switching a task from data/source preparation to the next already pre-frozen T1 stage;
- using a larger but still bounded dataset within the T1 global caps;
- routine resource recovery after a stale reservation where ownership is mechanically disproven;
- one-shot acquisition of an alternate official source that was prospectively predeclared as an equivalent fallback before any outcome.

T2 must not be used for:
- new mechanism selection;
- new outcome family;
- new source chosen after seeing an outcome;
- higher multiplicity;
- any T3 action.

### T3 — EXPLICIT USER GATE REQUIRED

Always stop and request user approval.

Includes:
- Research Runner / Runner Probe bundle execution requiring bundle seal/hash approval;
- any trading/live-order action;
- any use of exchange/API secrets or trading credentials;
- collector creation, mutation, restart policy change, source change, or protected-window rule change;
- paid/licensed data purchase or subscription;
- cloud/service spend outside preexisting fixed infrastructure;
- deleting verified evidence-bearing raw data;
- lowering disk/resource safety reserves;
- changing binding governance or authorization policy;
- modifying frozen experiment rules after outcome access;
- opening protected raw outcome data not already authorized by a frozen T1 task;
- starting a second concurrent outcome-bearing family;
- raising multiplicity/variant/horizon/symbol budget after outcomes;
- changing economic mechanism or evidence role after outcome access;
- same-evidence rescue request;
- any action outside the explicit T1/T2 envelope.

## 3. Strategy Manager delegation boundary

After ratification, the user delegates the Strategy Manager to:
- classify a proposed action T0/T1/T2/T3;
- issue T1/T2 task authorizations when all prerequisites pass;
- choose lower execution/resource limits than the defaults;
- stop/defer any action despite delegation;
- aggregate T3 gates and present them to the user.

The Strategy Manager may never self-expand this policy.

Ambiguity defaults upward:
T0 uncertainty -> T1 review
T1 uncertainty -> T3 user gate

## 4. Task authorization artifact

For T1/T2 execution, create:

docs/research/authorizations/<TASK_ID>-authorization-v0.1.json

Required fields:
- schema;
- task_id;
- worker_id;
- authorization_tier;
- authorization_source = USER_DELEGATED_POLICY_v0.1;
- policy_path;
- policy_sha256;
- strategy_review_ref;
- protocol/fingerprint/implementation refs + hashes;
- evidence_class;
- promotional flag;
- outcome_access_authorized;
- allowed data classes;
- allowed hosts/endpoints;
- network_profile;
- max_network_runs;
- max_outcome_runs;
- max_network_bytes;
- max_dataset_bytes;
- max_peak_workspace_increment;
- exact source/evidence window;
- resource reservation refs;
- validity / expiration;
- terminal stop rules.

Workers must fail closed on any mismatch.

## 5. Automatic continuation chain

To minimize user blocking, a task may declare an AUTOMATIC_CONTINUATION_CHAIN before the first outcome access.

Example:
DESIGN_PASS
-> OFFLINE_SELFTEST_PASS
-> SOURCE_SEMANTIC_PASS
-> RESOURCE_READY
-> ONE_FROZEN_DISCOVERY_RUN
-> TERMINAL STRATEGY REVIEW

Each transition must:
- already be explicitly enumerated before outcome;
- preserve exact hashes/rules;
- satisfy T1 gates;
- not introduce a new variant, source, horizon, symbol subset or mechanism.

The chain must stop automatically on:
- REJECT;
- DEFER;
- REVIEW;
- source/schema mismatch;
- resource failure;
- contamination ambiguity;
- any unexpected condition.

No repair/rescue step may be inserted after outcome without new Strategy review, and T3 where applicable.

## 6. User interruption / revocation

The user may revoke or narrow delegated authority at any time.

Canonical revocation path:
docs/research/sc001-user-delegated-authorization-revocation-v0.1.json

On revocation:
- no new T1/T2 task may start;
- already running bounded jobs may finish only if stopping them would risk data integrity; otherwise stop safely;
- T0 remains available unless also disabled.

## 7. Quiet-hours / delayed user attention

T1/T2 tasks do not wait for user presence.

If a task reaches T3 while the user is unavailable:
- mark USER_GATE;
- preserve exact state;
- do not retry;
- do not open additional evidence;
- other independent T0/T1 tasks may continue if their own authorization remains valid.

This prevents one blocked gate from stopping the entire research program.

## 8. Notification policy

User-facing notifications should be aggregated through Strategy Manager / Strategy Watch.

Immediate notification only for:
- T3 gate;
- protected collector/resource threat;
- unexpected protected-data access risk;
- terminal strategic result that changes portfolio state.

Routine T1/T2 mechanics should not generate separate worker notifications.

## 9. Scientific safeguards unaffected

Delegated execution does not relax:
- mechanism fingerprint gate;
- adaptive-discovery classification;
- contamination rules;
- variant/multiplicity budget;
- fresh Confirmation requirement;
- Edge-to-Fill;
- no-rescue;
- one default outcome-bearing family;
- reusable-block policy.

Faster approval flow is not weaker research governance.

## 10. Runner Probe exception

This policy does NOT pre-authorize Runner Probe / Research Runner bundle execution where the execution system requires the exact sealed bundle/hash to be shown to the user and explicitly approved.

Those actions remain T3.

## 11. Ratification

This policy becomes ACTIVE only after one explicit user message approving:
SC001 Delegated User Authorization Policy v0.1

Ratification artifact:
docs/research/sc001-user-delegated-authorization-ratification-v0.1.json

Until ratified:
- current approval rules remain binding;
- T1/T2 delegation is not active.

## 12. Review trigger

Revisit this policy only if:
- user blocking remains material after ratification;
- workers repeatedly hit T3 gates for routine work;
- an incident shows T1 scope is too broad;
- infrastructure/cost/trading capabilities materially change.

No routine version churn.
