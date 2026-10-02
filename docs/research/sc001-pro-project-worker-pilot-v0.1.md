# SC001 — Pro Project Worker Pilot v0.1

Date: 2026-10-02
Status: BINDING OPERATIONAL PILOT / NO RESEARCH OUTCOME AUTHORIZATION
Scope: SC001 worker execution on ChatGPT Pro

## STATE CHANGE

Adopt a bounded Project-based worker pilot before building any external mutation relay.

The prior conclusion remains valid:
- generic Scheduled Tasks are not trusted for durable external writes;
- do not re-enable H1/X1 hourly scheduled mutation workers.

New pilot:
- keep Strategy Manager in the current Strategy Project;
- keep the already-working existing Researcher Project as the P1 execution pattern;
- create exactly one new Project first: H1_HISTORICAL_INDICATORS;
- prove normal Project/Work + connected plugins can perform a harmless end-to-end GitHub task;
- only after H1 PASS, clone the pattern for X1_CROSS_ASSET_STRUCTURE.

## Why this pilot is preferred now

Observed working facts:
1. Strategy Project can read/write canonical GitHub through connected tools.
2. Existing Researcher Project can execute research workflows and persist GitHub results.
3. GitHub, BotMarketplace GitHub Control and BotMarketplace Test Executor have app-specific permission mode Allow all actions.
4. ChatGPT Pro supports Projects and Work.
5. Pro supports GitHub pull-request-activity event-triggered Work tasks.

Unproven:
- whether a Project/Work event-triggered run can use the BotMarketplace mutating plugins unattended.

Therefore do not infer autonomous PASS. Test it.

## Architecture during pilot

USER
  -> Strategy Manager Project
  -> GitHub task PR
  -> H1 Project
  -> GitHub task branch / PR
  -> Strategy Manager review

GitHub remains the durable source of truth.

No direct H1<->X1 communication.

## H1 Project tool set

Connect/use:
- GitHub
- BotMarketplace GitHub Control
- BotMarketplace Test Executor

Do NOT connect/use for H1 pilot:
- BotMarketplace Runner Probe
- BotMarketplace VPS Reader
- collector controls
- trading credentials/tools

VPS Reader may be added later only for an explicitly authorized read-only inventory need.

## Pilot stages

### Stage A — interactive Project write smoke

Goal:
prove the newly created H1 Project has the same basic read/write capability as the existing working Researcher Project.

Input:
PR [SC001][H1][READY] H1-PROJECT-SMOKE-001.

H1 must:
1. read the PR task manifest;
2. read only the listed harmless canonical docs;
3. create exactly one smoke result file on the task branch;
4. commit it;
5. update the PR body or add a PR comment with terminal PASS;
6. open no market data, outcomes or network research.

PASS token:
H1_PROJECT_INTERACTIVE_WRITE_SMOKE_PASS

If Stage A fails:
stop. Do not attempt event automation.

### Stage B — Work execution smoke

Run the same class of harmless task from Work inside the H1 Project.

PASS requires:
- connected plugins usable;
- branch write/commit succeeds;
- no extra approval required for the bounded low-risk write.

PASS token:
H1_PROJECT_WORK_WRITE_SMOKE_PASS

### Stage C — GitHub PR event-trigger smoke

Create a second harmless PR with title prefix:
[SC001][H1][READY]

Configure one event-triggered Work task on GitHub pull request activity for the authorized repository.

PASS requires:
1. PR activity triggers H1 Work;
2. exact worker/task identity is checked;
3. H1 persists a harmless result on the task branch;
4. terminal marker is persisted;
5. no user intervention is required after trigger.

PASS token:
H1_PROJECT_EVENT_TRIGGER_WRITE_SMOKE_PASS

If Stage C fails but A/B pass:
Project worker remains viable for manual/Work execution, but not unattended autonomous wake-up.
Do not build X1 automation yet.

## Research gate after pilot

Only after Stage A PASS may H1 resume DESIGN_ONLY task SC001-H1-001 manually/through Work.

Only after Stage C PASS may H1 be considered autonomous for GitHub-triggered bounded tasks.

Outcome-bearing historical research remains separately governed and is NOT authorized by this pilot.

## X1 gate

Do not create/activate X1 Project automation until H1 Stage A and B PASS.

Prefer waiting for Stage C result before configuring X1 event automation.

If H1 Project pattern passes, X1 should reuse the same minimal template with domain-specific instructions only.

## Existing P1

Do not migrate or redesign the existing working Researcher Project during this pilot.

P1 prospective rules/window remain unchanged.

Use the existing Researcher Project as the proven execution reference.

## Acceptance

Pilot is successful when:
- new H1 Project can independently read its task from GitHub;
- exact scope is respected;
- additive result is committed through connected plugins;
- Strategy Manager can read the durable result;
- no protected evidence is touched.

## DO NOT DO

- do not rebuild an external relay before this pilot is resolved;
- do not reactivate old hourly H1/X1 scheduled mutation workers;
- do not connect Runner Probe to H1 merely for convenience;
- do not copy P1 protected/raw context into H1;
- do not start H1 outcome research during smoke;
- do not create X1 Project before the H1 template has at least interactive/Work PASS.

NO ROADMAP CHANGE REQUIRED.
