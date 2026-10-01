# SC001 — Execution Worker Routing & Automation Architecture v0.1

Date: 2026-10-01
Status: BINDING EXECUTION-ROUTING MVP / NO NEW OUTCOME AUTHORIZATION
Scope: BotMarketplace / SCALPING RESEARCH / SC001

## 1. Purpose

Introduce limited parallel execution without fragmenting portfolio strategy, contamination control or evidence interpretation.

This document changes execution routing only. It does not alter frozen experiment rules, contamination history, evidence standards, or terminal verdicts.

GitHub remains the sole durable source of truth.

## 2. Control plane

There is exactly one portfolio-level decision owner:

`SC001_STRATEGY_MANAGER`

The Strategy Manager owns:
- mechanism overlap and disguised-rescue decisions;
- portfolio priority;
- evidence-role allocation;
- contamination and multiplicity interpretation;
- promotion / stop / defer decisions;
- authorization boundaries for new outcome-bearing research.

Execution workers do not promote their own research and do not alter roadmap/governance unless an exact user-approved task says so.

Three analytical lenses (Financial/Trader, Programmer/Trader, Mathematician/Statistician) remain review passes of the Strategy Manager, not separate permanent agents.

## 3. Execution domains

### P1 — PROSPECTIVE_EVENT

Worker ID:
`P1_PROSPECTIVE_EVENT`

Owns the existing prospective/event-driven pipeline, including the current:
`VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION`

Evidence domain:
- prospective collectors;
- fresh event windows;
- event/source qualification;
- future source materialization;
- event-driven candidate implementation.

Must not open Historical Indicator or Cross-Asset outcome work unless explicitly reassigned by Strategy Manager.

### H1 — HISTORICAL_INDICATORS

Worker ID:
`H1_HISTORICAL_INDICATORS`

Mission:
systematically research classical and causal indicator/feature families on preallocated historical evidence without unrestricted parameter/composite mining.

Core scope:
- P1/P2/P3/P4/P7 feature families;
- RSI/Stochastic-style price-location transforms;
- EMA/MACD/ADX-style trend/persistence;
- ATR/range/volatility-state transforms;
- Bollinger/VWAP/reference-deviation constructions;
- volume/activity confirmation;
- small predeclared feature-combination budgets.

Hard rule:
indicator names are formulas, not independent economic mechanisms.

The worker must use the binding Feature / Indicator Governance and a multiplicity ledger.

It must never use protected P1 raw/fresh outcomes.

### X1 — CROSS_ASSET_STRUCTURE

Worker ID:
`X1_CROSS_ASSET_STRUCTURE`

Mission:
research causal cross-asset / cross-market information transfer, residual structure and relative-state mechanisms without turning unconditional correlation into a trading claim.

Initial scope:
- crypto-to-crypto information transfer;
- common-factor / residual structure;
- sector/peer relative state;
- cross-sectional dispersion/ranking;
- causal leader/follower hypotheses with fixed economic roles.

External non-crypto derivatives may be proposed only after a source/licensing/clock/latency feasibility review shows a plausible public and causal research path.

Hard rules:
- correlation alone is descriptive, not a mechanism;
- legacy C4/C6 outcomes may be read only for lineage/overlap, not parameter selection;
- any successor generated after those outcomes is ADAPTIVE_DISCOVERY_GENERATED unless independent pre-freeze is proven.

The worker must never use protected P1 raw/fresh outcomes.

## 4. Why only these workers

Do not create separate agents for:
- RSI;
- MACD;
- statistics;
- programming;
- L2;
- Financial/Trader lens;
- Mathematician lens.

Those splits would increase coordination cost without creating a separate evidence domain.

Do not create a Shared Data Infrastructure worker yet. Add one only if P1/H1/X1 repeatedly block on common data-engineering work and the separation would save material effort.

## 5. GitHub task queue

GitHub Issues are the execution task queue. Canonical research outputs remain repository files.

Issue title format:

`[SC001][WORKER:<WORKER_ID>][<STATE>] <TASK_ID> — <SHORT_TITLE>`

Allowed task states:
- `READY`
- `IN_PROGRESS`
- `USER_GATE`
- `BLOCKED`
- `DONE`

Each worker may have at most one `IN_PROGRESS` task.

A task body must contain:
- TASK_ID;
- WORKER_ID;
- PRIORITY;
- AUTHORIZATION_CLASS;
- strategy/charter references;
- exact allowed actions;
- exact forbidden actions;
- expected canonical outputs;
- whether a Worker Result Manifest is required;
- terminal handoff states.

Authorization classes:
- `DESIGN_ONLY`
- `READ_ONLY_AUDIT`
- `OFFLINE_SELFTEST`
- `NETWORK_METADATA_ONLY`
- `OUTCOME_BEARING`

A worker must never escalate its authorization class.

Any `OUTCOME_BEARING` task requires an explicit Strategy/User gate recorded before outcome access.

## 6. Worker polling / acceptance protocol

Workers poll only their own open GitHub Issues.

On each poll:
1. search exact worker ID and state READY;
2. if none: do nothing;
3. if more than one: take highest explicit priority, then oldest issue;
4. change only the selected issue to IN_PROGRESS;
5. record the current GitHub HEAD in the issue before work;
6. read only the issue, this architecture document, and the minimum canonical references named by the issue;
7. complete the bounded task;
8. canonicalize result files in GitHub;
9. create a Worker Result Manifest only when strategy-relevant;
10. move the issue to DONE, USER_GATE or BLOCKED.

Workers do not communicate directly with each other.

## 7. Strategy feedback loop

Canonical loop:

`STRATEGY MANAGER -> GitHub Issue -> WORKER -> Canonical Result + Worker Result Manifest -> SC001 Strategy Watch -> Strategy Manager/User`

The existing hourly `SC001 Strategy Watch` remains the strategy-level event detector.

A strategy-relevant worker result must use the existing manifest schema.

Routine parser/self-test/transport work should not create strategy manifests unless evidence eligibility or source semantics materially change.

## 8. Polling cadence

Use an hourly condition watch for each autonomous worker.

Reason:
- current ChatGPT scheduled-task infrastructure supports hourly as the highest recurring frequency;
- SC001 research decisions are materially slower than one hour;
- 10/30-minute polling would require an external orchestrator and would add operational complexity without current evidence of decision-value benefit.

Do not add GitHub webhooks, message brokers, a new database or a custom orchestration service yet.

## 9. Context isolation

Persistent conversational memory is not required for autonomous workers.

Preferred worker model:
- near-stateless scheduled execution;
- stable worker ID;
- bounded GitHub issue;
- minimal referenced canonical context.

Separate interactive ChatGPT Projects are optional for manual deep dives, not required for execution routing.

## 10. Concurrency / multiplicity

Parallel design and engineering are allowed across P1/H1/X1.

Outcome-bearing concurrency is not automatic.

Default:
- current P1 remains the only authorized outcome-bearing family;
- H1 and X1 begin with DESIGN_ONLY / source-feasibility tasks.

A second simultaneous outcome-bearing family may start only after explicit Strategy/User review of:
- multiplicity budget;
- evidence independence;
- contamination allocation;
- execution capacity;
- expected decision value.

## 11. User-gate policy

The user should not be required to visit every worker context.

Workers return to USER_GATE only for:
- new outcome access;
- networked research not already explicitly authorized;
- protected/raw data access;
- collector mutation;
- new paid/licensed data;
- roadmap/governance change;
- ambiguous contamination or mechanism-overlap decision.

Routine bounded execution should proceed without user intervention when already authorized by the GitHub task.

## 12. Anti-bureaucracy

Do not create work to keep workers busy.

If a worker has no READY task, it remains idle.

Idle capacity is cheaper than low-value multiplicity.

The objective remains:

`DECISION QUALITY / RESEARCH COST`

## 13. Current architecture decision

`ONE_STRATEGY_MANAGER + THREE_EXECUTION_DOMAINS`

- P1_PROSPECTIVE_EVENT — existing;
- H1_HISTORICAL_INDICATORS — new;
- X1_CROSS_ASSET_STRUCTURE — new.

No fourth execution domain is authorized by this version.

NO GOVERNANCE METHODOLOGY CHANGE REQUIRED.
