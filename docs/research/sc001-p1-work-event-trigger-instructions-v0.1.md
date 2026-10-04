# SC001 — P1 Work Event Trigger Instructions v0.1

Date: 2026-10-04
Status: OPERATIONAL TRIGGER CONTRACT / NO RESEARCH AUTHORIZATION BY ITSELF
Worker: P1_PROSPECTIVE_EVENT
Repository: AlexeyIvy/-botmarketplace-site
Target Project: existing BotMarketplace Research Lab

Use only for Work driven by GitHub pull-request activity.

## Trigger gate

Accept only:
- repository exactly AlexeyIvy/-botmarketplace-site;
- pull_request action exactly ready_for_review;
- title starts exactly, case-sensitively, with:
  [SC001][P1][READY]

Ignore:
- opened/closed events;
- synchronize/commit updates;
- comments;
- reviews;
- ordinary GitHub churn.

If exact event/PR identity is unavailable, stop. Do not search for a replacement READY task.

## On matching event

1. Read the exact triggered PR.
2. Read and obey:
   docs/research/sc001-p1-prospective-event-project-instructions-v0.1.md
3. Read the exact task manifest/body and only its minimum binding references.
4. Validate WORKER_ID=P1_PROSPECTIVE_EVENT, READY state, authorization class/tier, budgets, frozen evidence boundary, stop rules, resource/collector gates and PR lifecycle authority.
5. Respect any existing valid claim/lease/terminal state; never duplicate work.
6. Claim exactly the triggered task when authorized.
7. Execute exactly one task.
8. Persist only explicitly allowed task-local artifacts.
9. Revalidate current main and binding context.
10. If strategy-relevant, create/update Worker Result Manifest LAST as the final repository artifact.
11. Write one terminal PR receipt and stop.

For a strategy-relevant task, terminal receipt must:
- start exactly with `TERMINAL RECEIPT —`;
- contain exactly `STRATEGY_REVIEW_REQUIRED: true`;
- include TASK_ID, WORKER_ID, TERMINAL_STATUS, MANIFEST_PATH and MANIFEST_SHA256.

For a non-strategy-relevant task, use:
- `STRATEGY_REVIEW_REQUIRED: false`
so Strategy Control ignores it.

## Hard safety

No Research Runner / Runner Probe bundle execution unless the exact task has explicit T3 user approval.

No Test Executor/network/data-body/protected-evidence action unless the exact task and delegated authorization permit that exact action.

No collector mutation/restart/source/permission change unless exact T3 user approval exists.

No protected raw outcome access, trading credentials or trading unless separately and explicitly authorized.

No roadmap/governance/Strategy State/contamination/reusable-registry mutation.

No same-evidence rescue or frozen-rule changes.

Never start a second task in the same Work run.

Never merge/close/retarget/auto-merge/delete the task PR or branch without exact lifecycle authority.
