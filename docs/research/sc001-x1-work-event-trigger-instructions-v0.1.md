# SC001 — X1 Work Event Trigger Instructions v0.1

Status: OPERATIONAL TRIGGER CONTRACT / NO RESEARCH AUTHORIZATION BY ITSELF
Revision: 2026-10-04 — TERMINAL CONTINUATION CONTRACT HARDENING

Worker: X1_CROSS_ASSET_STRUCTURE
Repository: AlexeyIvy/-botmarketplace-site

Use only for a Work event-triggered task driven by GitHub pull request activity.

## Trigger filter

Accept only an authorized GitHub pull request in repository AlexeyIvy/-botmarketplace-site whose title starts exactly:

[SC001][X1][READY]

Preferred event: pull request opened or marked ready for review.

Do not trigger on worker-authored commit updates/comments if the platform permits event narrowing.

## On trigger

1. Read the triggered PR.
2. Validate WORKER_ID=X1_CROSS_ASSET_STRUCTURE and state READY.
3. Read and obey current canonical worker instructions:
   docs/research/sc001-x1-cross-asset-project-instructions-v0.1.md
4. Read the exact task manifest/body and latest Strategy Manager review comments on that PR.
5. Treat all other memory/chat context as NON-AUTHORITATIVE for research specification.
6. Validate authorization class, budgets, stop rules, allowed tools/writes, protected-evidence boundary and PR lifecycle authority.
7. Claim exactly this task when the task contract permits claim mutation.
8. Execute exactly one task.
9. Persist only allowed artifacts; Worker Result Manifest LAST when required.
10. Write one terminal receipt and stop.
11. Never start another READY task in the same Work run.
12. Never merge/close/retarget/auto-merge unless exact task explicitly authorizes it.

## Terminal receipt contract

Every terminal X1 event must:
- start exactly with TERMINAL RECEIPT —;
- include TASK_ID, WORKER_ID and TERMINAL_STATUS;
- contain exactly CONTINUATION_REVIEW_REQUIRED: true;
- contain exactly one STRATEGY_REVIEW_REQUIRED line whose value is true or false.

For strategy-relevant work:
- STRATEGY_REVIEW_REQUIRED: true;
- include MANIFEST_PATH and MANIFEST_SHA256;
- create/update the Worker Result Manifest LAST before the terminal receipt.

For non-strategy-relevant work:
- STRATEGY_REVIEW_REQUIRED: false;
- CONTINUATION_REVIEW_REQUIRED remains true;
- do not fabricate a Worker Result Manifest unless the exact task separately requires one.

Tool presence is not authorization.
No Runner/Test Executor/network/VPS raw/collector/outcome action is allowed unless exact canonical task explicitly authorizes it.

If validation fails:
write only the bounded BLOCKED/USER_GATE terminal receipt allowed by the task, including CONTINUATION_REVIEW_REQUIRED: true, then stop.
