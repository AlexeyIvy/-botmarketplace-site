# SC001 — Delegated User Authorization Policy v0.2

Date: 2026-10-01
Status: PROPOSED / PENDING ONE-TIME USER RATIFICATION
Scope: BotMarketplace / SCALPING RESEARCH / SC001
Supersedes proposal: docs/research/sc001-delegated-user-authorization-policy-v0.1.md

Parents:
- docs/research/sc001-research-strategy-agent-charter-v0.1.md
- docs/research/sc001-execution-worker-routing-and-automation-architecture-v0.2.md
- docs/research/sc001-shared-data-and-resource-coordination-v0.1.md
- docs/research/sc001-implementation-debugging-and-repair-control-v0.1.md

## 1. Purpose

Remove the user as a routine execution bottleneck while preserving strict human control over strategic, irreversible, paid, protected, trading and rescue actions.

Delegation authorizes bounded execution of already-governed research.
It never authorizes agents to expand their own scope.

## 2. T0 — ALWAYS_AUTOMATIC

No user approval required:
- GitHub/source-of-truth reads;
- design/static analysis;
- task-local additive documentation;
- hashes and metadata-only local inventory;
- reuse of VERIFIED data under an existing evidence-access receipt;
- offline synthetic/unit/static checks with no protected evidence;
- Strategy reviews;
- public documentation lookup with no market-data body acquisition.

## 3. T1 — STRATEGY_MANAGER_DELEGATED

After ratification, Strategy Manager may issue exact task authorization without another user prompt when every prerequisite passes.

Eligible:
- bounded Test Executor public_research metadata/HEAD/source-semantic probes;
- bounded public historical market-data acquisition;
- bounded public archive-body downloads;
- deterministic source normalization / derived-data construction;
- bounded historical Selection/Calibration/Discovery outcomes on preallocated evidence;
- exact next pre-frozen S0/sentinel run when all scientific gates pass;
- bounded task-local PRE-OUTCOME implementation repair under:
  docs/research/sc001-implementation-debugging-and-repair-control-v0.1.md

Automatic repair defaults:
- REPAIR_MODE=AUTO_PRE_OUTCOME only when task explicitly enables it;
- MAX_REPAIR_CYCLES=2;
- MAX_CHANGED_TASK_LOCAL_FILES=4;
- branch + PR required;
- same failure signature after a repair => immediate STOP;
- full preflight required after every patch;
- task-local passing repair may auto-merge only when all repair-control gates pass;
- any protected/outcome access disables automatic repair.

Mandatory T1 prerequisites:
1. exact TASK_ID/worker;
2. Strategy Manager PASS;
3. eligible mechanism disposition where applicable;
4. frozen protocol/fingerprint/implementation semantics before evidence access;
5. contamination/evidence role preallocated;
6. no same-evidence rescue;
7. task run/data/resource/repair budgets frozen;
8. resource reservation PASS when needed;
9. disk/rate/collector-protection gates PASS;
10. current execution-plane limits PASS;
11. global outcome concurrency respected;
12. no paid/licensed data;
13. no credentials/trading;
14. no collector mutation;
15. no Runner Probe bundle execution.

Default per-task T1 caps unless lower:
- MAX_NETWORK_RUNS=1;
- MAX_OUTCOME_RUNS=1;
- MAX_REPAIR_CYCLES=2;
- no post-outcome repair/rerun;
- MAX_TOTAL_NETWORK_BYTES=10 GiB;
- MAX_SINGLE_DATASET_BYTES=5 GiB;
- MAX_PEAK_WORKSPACE_INCREMENT=15 GiB;
- exact preregistered variants only.

## 4. T2 — STRATEGY_MANAGER DECISION + USER NOTIFICATION, NO WAIT

May proceed after Strategy Manager decision inside this ratified envelope, while notifying the user without blocking.

Examples:
- advancing to the next already enumerated pre-frozen T1 stage;
- stale reservation recovery when no active owner is mechanically proven;
- prospectively declared equivalent official-source fallback;
- repair of a shared/common engineering component before protected/outcome access, only after Strategy Manager review and full repair-control validation.

T2 cannot:
- select a new mechanism;
- add a new outcome family;
- increase multiplicity after evidence;
- change evidence role after outcome;
- perform any T3 action.

## 5. T3 — EXPLICIT USER GATE REQUIRED

Always stop for user approval:
- Research Runner / Runner Probe sealed bundle execution;
- live trading/orders;
- exchange/API secrets or trading credentials;
- collector creation/mutation/restart-policy/source change;
- paid/licensed data or new variable cloud spend;
- deletion of verified evidence-bearing raw data;
- lowering resource safety reserves;
- changing binding governance or this authorization policy;
- frozen-rule change after outcome access;
- protected raw outcome access outside a pre-frozen T1 task;
- starting a second concurrent outcome-bearing family;
- increasing variant/horizon/symbol budget after outcomes;
- changing mechanism/evidence role after outcomes;
- same-evidence rescue;
- implementation repair after protected evidence/outcome access;
- any action outside T0/T1/T2.

## 6. Automatic continuation chain

A task may predeclare a bounded chain before first outcome access, e.g.:

DESIGN_PASS
-> IMPLEMENTATION_STATIC_PASS
-> OFFLINE_PREFLIGHT_PASS
-> SOURCE_SEMANTIC_PASS
-> RESOURCE_READY
-> ONE_FROZEN_DISCOVERY_RUN
-> STRATEGY_REVIEW

If implementation fails before protected evidence:
-> diagnosis-first repair control
-> at most two repair cycles
-> full preflight
-> re-freeze passing hash
-> continue only if the chain explicitly allowed repair.

The chain stops on:
- REJECT;
- DEFER;
- REVIEW;
- same repair failure signature;
- repair budget exhaustion;
- source/schema drift;
- unexpected evidence access;
- resource failure;
- contamination ambiguity;
- any T3 condition.

No rescue step may be inserted dynamically.

## 7. Task authorization artifact

T1/T2 execution requires:
docs/research/authorizations/<TASK_ID>-authorization-v0.1.json

It binds:
- policy hash;
- task/worker;
- strategy review;
- exact protocol/implementation hashes;
- evidence role/window;
- allowed data classes/hosts;
- execution profile;
- network/outcome/resource budgets;
- repair mode/budget when enabled;
- stop rules;
- expiry/one-shot semantics.

Any mismatch fails closed.

## 8. User availability

T0/T1/T2 work does not wait for the user to be online.

If one task reaches T3:
- mark USER_GATE;
- freeze exact state;
- do not retry or open new evidence;
- other independent T0/T1/T2 tasks continue normally.

## 9. Notifications

Workers remain quiet.
Strategy Manager / Strategy Watch aggregates notifications.

Immediate notification only for:
- T3 gate;
- protected collector/resource threat;
- protected-data risk;
- terminal strategic result materially changing portfolio state.

## 10. Scientific governance unchanged

Delegation does not relax:
- mechanism gate;
- adaptive-discovery classification;
- contamination;
- multiplicity;
- Edge-to-Fill;
- fresh Confirmation;
- no-rescue;
- default one outcome-bearing family.

## 11. Strategy Manager cannot self-expand delegation

Strategy Manager may:
- classify actions;
- lower budgets;
- stop/defer;
- issue task authorization inside T1/T2.

Strategy Manager may not:
- raise this policy's caps;
- move a T3 action into T1/T2;
- weaken repair loop breakers;
- change scientific firewalls.

Ambiguity escalates upward.

## 12. Revocation

User may revoke/narrow delegation at any time.

No new T1/T2 task starts after canonical revocation.

## 13. Ratification

This v0.2 becomes ACTIVE only after one explicit user message approving:

SC001 Delegated User Authorization Policy v0.2

Canonical ratification artifact is created only after that message.

Until then current explicit-approval rules remain binding.

## 14. Review trigger

Revisit only if:
- user blocking remains material;
- repair budgets are repeatedly exhausted;
- an incident shows scope too broad;
- infrastructure/cost/trading capabilities change materially.

No routine policy churn.
