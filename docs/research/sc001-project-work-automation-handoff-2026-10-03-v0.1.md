# SC001 — Project/Work Automation Handoff v0.1

Date: 2026-10-03
Status: OPERATIONAL HANDOFF / NO ROADMAP CHANGE
Scope: cross-chat continuity for current Project/Work worker architecture
Repository: AlexeyIvy/-botmarketplace-site

## Purpose

Preserve only the current operational decisions and proven facts needed to continue in a new Strategy conversation without reconstructing the long discussion.

This document does not change research roadmap, governance, evidence status, contamination rules, or frozen experiment semantics.

## Current canonical head at handoff

main: 8226b3c53923aa3e755d02876b1b3aa1d57cf408

GitHub remains the durable source of truth.

## Proven execution facts

### H1 Project worker

A dedicated ChatGPT Project exists for H1_HISTORICAL_INDICATORS.

Proven in practice:

1. Normal Project chat + connected MCP can read an exact GitHub task and persist bounded GitHub output.
2. Comprehensive MCP smoke passed for:
   - GitHub
   - BotMarketplace GitHub Control
   - BotMarketplace Test Executor
   - BotMarketplace Runner Probe
   - BotMarketplace VPS Reader
3. A real DESIGN_ONLY H1 task SC001-H1-001 was completed through the dedicated Project.
4. Work inside the H1 Project was manually launched and successfully executed the bounded Strategy correction task for PR #425.
5. That Work run:
   - claimed the correction task;
   - applied all five Strategy corrections;
   - left PR lifecycle under Strategy control;
   - created/updated Worker Result Manifest last;
   - launched no Test Executor jobs;
   - created/ran no Runner bundles;
   - opened no protected/raw outcome data;
   - performed no network/source acquisition.

Therefore:
PROJECT_CHAT_MCP_PATH = PASS
PROJECT_WORK_MCP_PATH = PASS

The remaining unproven automation boundary is:
GITHUB_PR_EVENT -> AUTOMATIC_WORK_WAKEUP

## Important product constraint discovered by user

Work is unavailable inside Projects configured with project-only memory.

For worker Projects that need Work/event automation, use the non-project-only/default memory mode.

The current deep Strategy Project should remain project-only so it can continue serving as the isolated discussion/decision workspace.

## H1 research state

Issue #418:
[SC001][WORKER:H1_HISTORICAL_INDICATORS][DONE] SC001-H1-001 — Historical indicator discovery census and benchmark freeze proposal

State: CLOSED / DONE.

Reviewed H1 prefreeze was merged.

Key corrected properties:
- ADAPTIVE_DISCOVERY_GENERATED = true;
- primary 1m source reuses existing Binance USD-M long-history backbone;
- BAL14 v0.1 = R2_STATE_REGIME only;
- exact family-wise multiplicity rule must be frozen before any R1 outcome-bearing run;
- R2/R3/R4/R6-only features cannot receive standalone directional promotional claims;
- formulas/horizons/evidence fractions/8-variant budget unchanged.

Worker correction head:
caff459226d72fc5b1e1658b4e526249164e9cb3

Reviewed merge commit:
6acdfbc0f2a0c06054b7bdfcdb8522d59cd65b4f

Next research action allowed for H1:
one bounded Binance USD-M 1m source/prior-use audit with NO outcome access, resolving:
- exact 6–12 outcome-blind instruments;
- >=120 complete UTC-day multi-symbol coverage;
- prior SC001 use / contamination classification;
- DATASET_KEY / RESOURCE_ID;
- verified local reuse / DERIVED_ID if applicable;
- exact evidence-block allocation/access boundaries.

Do not open R1 outcomes until the family-wise multiplicity rule is frozen.

## Canonical H1 worker controls

Project instructions:
docs/research/sc001-h1-historical-indicators-project-instructions-v0.1.md

Work event-trigger contract:
docs/research/sc001-h1-work-event-trigger-instructions-v0.1.md

Target automatic trigger:
GitHub pull request opened or marked ready for review
AND title starts exactly:
[SC001][H1][READY]

Preferred behavior:
triggered Work reads the exact PR/task + current canonical H1 instructions, executes exactly one authorized task, writes terminal receipt, and stops.

Do not configure trigger on every PR activity if avoidable; worker commits/comments must not recursively re-trigger itself.

## X1 state

Issue #419 remains open:
[SC001][WORKER:X1_CROSS_ASSET_STRUCTURE][READY] SC001-X1-001 — Cross-asset information-transfer mechanism and source feasibility

Current task class: DESIGN_ONLY.

Canonical X1 Project instructions already exist:
docs/research/sc001-x1-cross-asset-project-instructions-v0.1.md

Canonical X1 Work event-trigger contract already exists:
docs/research/sc001-x1-work-event-trigger-instructions-v0.1.md

X1 Project itself is not yet created/configured.

Planned X1 setup:
- separate Project;
- default/non-project-only memory so Work is available;
- connect the same five BotMarketplace/GitHub MCPs;
- Work trigger prefix:
  [SC001][X1][READY]
- first useful run may be SC001-X1-001; no separate empty smoke is required if the trigger configuration is already proven via H1.

## P1 / Research Lab state

The pre-existing Research Lab / P1 execution Project is the original proven research execution surface and should not be redesigned for style.

Later automation step:
- preserve its current research role;
- enable/use default-memory Work capability if needed;
- add the same READY-PR event pattern for P1;
- keep all protected/prospective evidence rules unchanged.

Do not mutate the existing prospective collector merely to adopt Work automation.

## Strategy architecture decision

Keep the current deep Strategy Project unchanged and project-only.

Create a separate future Project:
BotMarketplace — Strategy Control

Purpose:
thin automated control surface, not a second independent strategist.

Planned behavior:
- default/non-project-only memory so Work is available;
- GitHub is sole authority;
- wake only on standardized worker terminal/review-request events;
- read Worker Result Manifest + minimal referenced governance;
- apply bounded corrections/dispatch only when already authorized;
- stop on USER_GATE for actions requiring explicit user approval;
- send the user concise notifications/receipts.

The deep Strategy Project remains the place for:
- ambiguous strategy decisions;
- roadmap/governance discussion;
- three-lens reviews when materially needed;
- user deliberation.

Do not let Strategy Control create a second source of strategic truth.

## Planned worker-to-strategy event

Preferred future terminal token:
STRATEGY_REVIEW_REQUEST

Worker emits it once, after Worker Result Manifest is durable.

Strategy Control trigger should react only to the intended terminal/review event, not to every commit/comment, to avoid self-trigger loops.

This token/trigger is PLANNED and not yet fully implemented/tested at this handoff.

## Existing fallback automation

Keep current hourly/read-only watches as fallback until event-triggered Work is proven end-to-end.

In particular:
- SC001 Strategy Watch
- SC001 Project Dispatch Watch

Do not rely on the old scheduled worker write architecture for autonomous mutation; its unattended durable write path previously failed.

After BOTH are proven:
1. READY PR -> automatic worker Work run;
2. worker terminal review request -> automatic Strategy Control Work run;

then retire redundant polling/fallback watches to avoid duplicate work.

## Immediate next implementation sequence

1. Finish/configure H1 GitHub PR event-triggered Work task.
2. Test it with one real bounded H1 source/prior-use task rather than another empty smoke.
3. If automatic H1 wakeup PASS:
   - create Strategy Control Project + terminal review trigger;
   - test full H1 -> Strategy Control cycle.
4. Then create/configure X1 Project and trigger.
5. Then adapt existing P1 / Research Lab to the same event pattern.
6. Only after event-path PASS retire old hourly worker/dispatch fallbacks.

## Hard boundaries unchanged

- GitHub is source of truth.
- Tool presence is not authorization.
- No same-evidence rescue.
- No post-outcome parameter/horizon/symbol search.
- No retroactive frozen-rule edits.
- No collector mutation without exact authorization.
- No Runner bundle execution without explicit authorized path.
- No protected/raw outcome access outside exact scope.
- Strategy Manager remains single writer for shared strategy/governance state.

NO ROADMAP CHANGE REQUIRED.
