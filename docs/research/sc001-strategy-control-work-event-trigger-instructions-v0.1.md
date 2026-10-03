# SC001 — Strategy Control Work Event Trigger Instructions v0.1

Date: 2026-10-03
Status: OPERATIONAL TERMINAL-EVENT CONTRACT / NO RESEARCH AUTHORIZATION BY ITSELF
Repository: AlexeyIvy/-botmarketplace-site
Target Project: BotMarketplace — Strategy Control

Use only for a Work event-triggered task driven by GitHub pull request comments.

## Trigger filter

Accept only:
- repository exactly AlexeyIvy/-botmarketplace-site;
- GitHub pull request comment created;
- comment body starts exactly with:
  TERMINAL RECEIPT —
- the same comment contains exactly:
  STRATEGY_REVIEW_REQUIRED: true
- originating task identifies WORKER_ID as one of:
  H1_HISTORICAL_INDICATORS
  X1_CROSS_ASSET_STRUCTURE
  P1_PROSPECTIVE_EVENT

Ignore:
- commits;
- PR opened/closed/ready events;
- reviews;
- ordinary comments;
- CLAIM_BLOCK writes;
- STRATEGY_REVIEWED comments;
- worker progress messages;
- comments lacking the exact strategy-review requirement.

This terminal-comment filter is the standardized review event for v0.1. It intentionally reuses the already-proven worker terminal receipt instead of adding another redundant signal.

## On trigger

1. Read the triggered PR and exact terminal comment.
2. Validate TASK_ID, WORKER_ID, terminal status and STRATEGY_REVIEW_REQUIRED=true.
3. Read and obey:
   docs/research/sc001-strategy-control-project-instructions-v0.1.md
4. Resolve the exact Worker Result Manifest path/SHA from the terminal receipt or task branch.
5. Verify the manifest exists and is the worker's final repository artifact before the terminal receipt.
6. Check whether an exact STRATEGY_REVIEWED receipt for the same manifest already exists. If yes, stop.
7. Read the manifest, canonical result and only the minimum referenced binding context.
8. Perform one bounded Strategy Review.
9. Write one STRATEGY_REVIEWED receipt on the same PR.
10. Dispatch at most one next task only if the Strategy Control Project Instructions and active delegated policy permit it without ambiguity.
11. If a T3 or ambiguous strategy decision exists, write USER_GATE or DEEP_STRATEGY_REVIEW_REQUIRED instead of dispatch.
12. Notify the user concisely and stop.

## Loop prevention

Never trigger on Strategy Control's own comments.
Never treat STRATEGY_REVIEWED, USER_GATE or DEEP_STRATEGY_REVIEW_REQUIRED as worker terminal events.
Never react to commit/comment churn after the terminal receipt.
Never start a second task in the same Work run.

## Safety

No Runner bundle execution.
No Test Executor execution by Strategy Control.
No VPS raw-data browsing.
No collector mutation.
No outcome access beyond exact canonical result/manifest scope.
No automatic roadmap/governance/policy/charter change.
No same-evidence rescue.
No retroactive frozen-rule changes.

Tool presence is not authorization.
