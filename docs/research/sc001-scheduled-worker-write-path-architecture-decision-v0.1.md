# SC001 — Scheduled Worker Write-Path Architecture Decision v0.1

Date: 2026-10-02
Status: BINDING OPERATIONAL ARCHITECTURE DECISION / NO RESEARCH SCOPE CHANGE
Scope: BotMarketplace / SC001 multi-worker execution control

## STATE CHANGE

Suspend the v0.3 assumption that ChatGPT Scheduled Tasks can own durable worker claim/result state by mutating GitHub or the BotMarketplace GitHub Control MCP.

Decision token:

SCHEDULED_WORKER_DURABLE_WRITE_PATH_REJECTED

Scheduled ChatGPT workers are READ/REASON/NOTIFY only until a separately validated external mutation relay is installed and passes end-to-end smoke tests.

## Evidence

### H1

GitHub Issue #418 contains:

STRATEGY_ATTENTION_REQUEST — H1 SCHEDULED WRITE-PATH BLOCKER

Observed:
- scheduled H1 could read GitHub state and canonical context;
- its first unattended durable claim mutation was blocked before reaching GitHub;
- no research execution, network acquisition, protected/raw outcome access, or canonical research output occurred.

### Independent generic GitHub smoke

Issue #421 was created solely to test one scheduled Issue mutation.

The one-shot scheduled task ran, but:
- Issue title remained READY;
- body was unchanged;
- no SCHEDULED_SMOKE_PASS marker appeared.

Therefore the problem is not specific to H1 task complexity.

### X1 reproduction

X1 scheduled worker ran against Issue #419 and then disabled without:
- a claim;
- a CLAIM_BLOCK;
- canonical outputs;
- outcome/network access.

Issue #419 remained READY.

### Custom GitHub Control smoke

A separate scheduled one-shot attempted a harmless repository marker through BotMarketplace GitHub Control:
- get_repo_status;
- write one fixed text file;
- commit/push.

The scheduled task ran, but:
- repository HEAD did not advance;
- the marker file did not exist afterward.

Therefore moving claim state from GitHub Issues to a repository file does not solve the scheduled write restriction.

## Strategic implication

The prior architecture correctly separated Strategy Manager and domain workers, but selected the wrong mutation boundary.

The failure is not:
- GitHub repository permission;
- one malformed worker prompt;
- H1/X1 research logic;
- contamination;
- task authorization.

The failure is the unattended Scheduled Task -> durable external mutation path.

Do not spend research time repeatedly retrying scheduled GitHub writes.

## Architecture disposition

### Rejected: A — repository-file claim from Scheduled Task

Rejected by the custom GitHub Control smoke.

A scheduled worker cannot be assumed to mutate a repository task-state file merely because that same MCP works interactively.

### Rejected as complete solution: B — read-only worker with no external relay

Read-only detection is useful, but without a mutable external relay it cannot provide autonomous claim/result publication.

### Selected direction: C/D hybrid

Keep ChatGPT scheduled jobs for:
- liveness/read-only observation;
- detecting new canonical state;
- reasoning/review;
- notifying user/Strategy Manager.

Move durable autonomous mutation to an external server-side control plane that is not dependent on Scheduled Task write permission.

Prefer extending existing BotMarketplace controlled infrastructure rather than creating a broad new orchestration service.

Candidate minimal relay responsibilities:
1. atomic task claim / lease;
2. idempotent task ownership;
3. accept/publish a bounded worker result package;
4. commit canonical additive artifacts;
5. terminal task transition;
6. expose read-only status to ChatGPT scheduled watchers;
7. no research-rule decisions;
8. no trading credentials;
9. no collector mutation;
10. no automatic expansion of task scope.

## Important implementation caveat

Simply adding more mutating MCP tools and calling them directly from a Scheduled Task is NOT sufficient evidence of a fix.

The GitHub Control scheduled-write smoke already showed that a normal mutating MCP call can be blocked in unattended context.

The replacement must prove its mutation occurs in an external/server-side execution path that is allowed independently of the Scheduled Task mutation restriction.

## Current worker state

H1_HISTORICAL_INDICATORS:
- Issue #418 READY;
- scheduled execution suspended;
- no outcome/network access.

X1_CROSS_ASSET_STRUCTURE:
- Issue #419 READY;
- scheduled execution suspended;
- no outcome/network access.

P1_PROSPECTIVE_EVENT:
- prospective research/collector evidence window remains governed by its existing frozen rules;
- generic scheduled worker mutation must not be relied upon for future task execution until relay PASS.

SC001 Strategy Watch:
- may remain read-only for detection/review/notification;
- must not be relied upon to dispatch or write durable review receipts while this restriction remains.

## Acceptance gate for replacement relay

Do not re-enable autonomous H1/X1 execution until all of the following PASS:

1. READ task;
2. atomic CLAIM persisted;
3. second claimant rejected;
4. lease visible read-only;
5. harmless additive result artifact persisted;
6. terminal state persisted;
7. idempotent replay does not duplicate artifacts;
8. stale claim recovery tested;
9. scheduled watcher can observe all states;
10. no protected data or research outcome is needed for the smoke test.

Then perform exactly one DESIGN_ONLY end-to-end worker cycle before allowing network/outcome tasks.

## NEXT ALLOWED ACTION

Design the smallest extension of existing BotMarketplace control infrastructure that can provide the external mutation relay.

First preference:
reuse the existing BotMarketplace GitHub Control/Test Executor deployment and codebase.

Do not create a new database, message broker, generalized agent platform, or fourth research worker merely to solve this issue.

## DO NOT DO

- do not re-enable H1/X1 on the old scheduled-write architecture;
- do not retry GitHub Issue mutations every hour;
- do not move claims to repo files and assume that solves the restriction;
- do not open research outcomes while repairing orchestration;
- do not change research roadmap or candidate semantics because of this infrastructure failure.

NO ROADMAP CHANGE REQUIRED.
