# SC001 — Strategy Control Work Event Trigger Instructions v0.2

Date: 2026-10-03
Revision: 2026-10-04 — CONTINUATION / NOTIFICATION HARDENING
Status: OPERATIONAL TERMINAL-EVENT CONTRACT / NO RESEARCH AUTHORIZATION BY ITSELF
Repository: AlexeyIvy/-botmarketplace-site
Target Project: BotMarketplace — Strategy Control
Supersedes: docs/research/sc001-strategy-control-work-event-trigger-instructions-v0.1.md

Use only for a Work event-triggered task driven by GitHub pull request comments.

## Trigger filter

Accept only:
- repository exactly AlexeyIvy/-botmarketplace-site;
- GitHub pull request comment created;
- the terminal comment body starts exactly with:
  TERMINAL RECEIPT —
- originating task identifies WORKER_ID as one of:
  H1_HISTORICAL_INDICATORS
  X1_CROSS_ASSET_STRUCTURE
  P1_PROSPECTIVE_EVENT
- and one of:
  1. the comment contains exactly CONTINUATION_REVIEW_REQUIRED: true; or
  2. legacy compatibility: the comment contains exactly STRATEGY_REVIEW_REQUIRED: true.

Future terminal receipts should contain both lines:
- STRATEGY_REVIEW_REQUIRED: true | false
- CONTINUATION_REVIEW_REQUIRED: true

Every worker terminal event should request continuation review.
Deep Strategy Review is a separate boolean.

Ignore:
- commits;
- PR opened/closed/ready events;
- reviews;
- ordinary comments;
- CLAIM_BLOCK writes;
- STRATEGY_REVIEWED comments;
- STRATEGY_CONTROL_REVIEWED comments;
- USER_GATE / STRATEGY_ATTENTION_REQUIRED / TERMINAL_IDLE_JUSTIFIED control receipts;
- worker progress messages;
- comments that are neither continuation-review terminals nor legacy strategy-review terminals.

## Exact event resolution

Preferred path:
- use the exact PR/comment identity and body supplied by the GitHub event.

Bounded fallback when the platform supplies the exact triggered PR identity but omits the comment body or comment id:
1. Do NOT search any other PR, Issue or repository activity.
2. Fetch only top-level conversation comments on that exact triggered PR.
3. Keep only comments whose bodies start exactly with TERMINAL RECEIPT — and contain CONTINUATION_REVIEW_REQUIRED: true or legacy STRATEGY_REVIEW_REQUIRED: true.
4. Remove any terminal comment id already named by a matching STRATEGY_CONTROL_REVIEWED receipt on that PR.
5. For legacy strategy events, also remove any receipt whose exact MANIFEST_PATH + MANIFEST_SHA256 already has a matching legacy STRATEGY_REVIEWED receipt.
6. If exactly one unreviewed terminal comment remains, use it.
7. If multiple remaining receipts are byte-equivalent duplicates for the same TASK_ID, WORKER_ID and TERMINAL_STATUS, use the newest/topologically last one.
8. Otherwise stop with no write, no dispatch and no user notification.

If the event does not identify the exact triggered PR at all, stop. Never substitute another PR.

This fallback exists only to recover exact event identity when the GitHub Work trigger omits comment-level fields. It does not authorize polling or repository-wide discovery.

## On trigger

1. Resolve the exact terminal receipt and TERMINAL_COMMENT_ID using the event or bounded fallback.
2. Validate TASK_ID, WORKER_ID and TERMINAL_STATUS.
3. Read and obey:
   docs/research/sc001-strategy-control-project-instructions-v0.1.md
4. Determine review kind:
   - STRATEGY_REVIEW_REQUIRED: true => REVIEW_KIND=STRATEGY;
   - STRATEGY_REVIEW_REQUIRED: false plus CONTINUATION_REVIEW_REQUIRED: true => REVIEW_KIND=CONTINUATION_ONLY;
   - legacy STRATEGY_REVIEW_REQUIRED: true with no continuation line => REVIEW_KIND=STRATEGY.
5. Check whether the exact terminal comment already has STRATEGY_CONTROL_REVIEWED. If yes, stop.
6. If REVIEW_KIND=STRATEGY:
   - resolve exact Worker Result Manifest path/SHA;
   - verify the manifest exists and was the worker's final repository artifact before the terminal receipt;
   - honor an exact legacy STRATEGY_REVIEWED receipt as already reviewed;
   - read the manifest, canonical result and only the minimum referenced binding context;
   - perform one bounded Strategy Review.
7. If REVIEW_KIND=CONTINUATION_ONLY:
   - do not require or fabricate a Worker Result Manifest;
   - read only the exact task/PR/terminal state and minimum canonical context needed to classify the successor.
8. Classify exactly one continuation disposition:
   - AUTO_CONTINUE
   - STRATEGY_ATTENTION_REQUIRED
   - USER_GATE_REQUIRED
   - TERMINAL_IDLE_JUSTIFIED
9. Write one STRATEGY_CONTROL_REVIEWED receipt on the same PR.
10. If AUTO_CONTINUE, dispatch at most one next task only if the active delegated policy and exact canonical state permit it without ambiguity.
11. Otherwise stop; notify the user when required by the project instructions.
12. Never start a second task in the same Work run.

## Loop prevention

Never trigger on Strategy Control's own comments.
Never treat STRATEGY_REVIEWED, STRATEGY_CONTROL_REVIEWED, USER_GATE_REQUIRED, STRATEGY_ATTENTION_REQUIRED or TERMINAL_IDLE_JUSTIFIED as worker terminal events.
Never react to commit/comment churn after a reviewed terminal receipt.
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
