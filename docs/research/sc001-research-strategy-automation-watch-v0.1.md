# SC001 — Research Strategy Automation Watch v0.1

Date: 2026-09-27
Status: **ACTIVE OPERATIONAL MVP**
Scope: `BotMarketplace / SCALPING RESEARCH / SC001`

## Purpose

Provide automatic event-driven invocation of the Research Strategy Agent after a strategy-relevant research boundary is recorded in GitHub.

This automation is a monitoring/control-plane convenience only. It does not execute trading research.

## Trigger source

The canonical trigger is a new SC001 Worker Result Manifest conforming to:

`docs/research/sc001-worker-result-manifest-schema-v0.1.json`

The watch must ignore ordinary implementation churn that does not produce a strategy-relevant manifest.

Examples that normally do NOT trigger Strategy Review:
- parser fixes;
- routine unit/self-test PASS;
- bundle sealing;
- transport/ACK repair;
- ordinary script iteration.

Examples that DO trigger Strategy Review when represented by a strategy-relevant manifest:
- new outcome-mechanism gate;
- terminal/reject/economically meaningful defer;
- reusable-block change;
- evidence-maturity change;
- contamination change;
- custom-indicator proposal;
- roadmap/governance change.

## Cadence

Default watch cadence:

`HOURLY CONDITION WATCH`

The watch is intentionally not more frequent. SC001 research stages are slow relative to one hour, so higher-frequency polling would add cost without material decision value.

## Governing documents

The watch must use:

- `docs/research/sc001-research-strategy-agent-charter-v0.1.md`
- `docs/research/sc001-research-strategy-state-v0.1.json`

and then only the minimum additional canonical documents referenced by a new manifest.

## No-event behavior

If no new strategy-relevant manifest exists:

`NO NOTIFICATION / NO STRATEGY REVIEW / NO DOCUMENT CHURN`

## New-event behavior

When a new unreviewed strategy-relevant manifest is found:

1. read the manifest;
2. read its referenced canonical result;
3. read only the minimum governance/contamination/reusable/lineage context needed;
4. perform the Strategy Review defined by the Charter;
5. notify the user with the compact strategic result.

## Hard boundaries

The watch MUST NOT:

- run Research Runner bundles;
- launch networked VPS jobs;
- operate or mutate collectors;
- read raw VPS data without separate explicit authorization;
- access secrets;
- alter frozen experiment rules;
- perform same-evidence rescue;
- open protected outcome data beyond the canonical authorization boundary;
- automatically modify roadmap/governance.

## Runtime placement

The automatic watcher is a **global Scheduled Task outside the Strategy Project**.

The interactive `BotMarketplace — Research Strategy` Project should use Project-only memory to keep its conversational context isolated from execution work. ChatGPT Work is not relied upon inside that project.

This separation intentionally gives two strategy surfaces:
- automated, near-stateless review via the global condition watch;
- manual, deeper strategy discussion inside the isolated Strategy Project.

## Architecture

`EXECUTION PROJECT -> GITHUB RESULT + MANIFEST -> GLOBAL HOURLY CONDITION WATCH -> STRATEGY REVIEW -> USER`

and for manual follow-up:

`USER -> PROJECT-ONLY RESEARCH STRATEGY PROJECT -> GITHUB CANONICAL STATE`

The user remains the approval authority for:
- roadmap/governance writes;
- new research execution;
- sealed bundle runs;
- networked jobs.

## Escalation rule

Do not introduce GitHub webhooks, PR-only routing, a new orchestration server, or API-driven autonomous agents unless the hourly condition watch proves operationally insufficient in real use.

The default rule remains:

`SIMPLEST ARCHITECTURE THAT PRESERVES RESEARCH CONTROL`
