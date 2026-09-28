# SC001 Current Roadmap and Stop Rules v5.177

Date: 2026-09-28
Status: **B15-P2 ASYNC NETWORKED 94-PAGE SEMANTIC-AUDIT BOUNDARY FROZEN / AWAITING EXPLICIT APPROVAL**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.176.md`

## Offline prerequisite

The v0.1.3 semantic implementation passed exact sealed offline validation:

- implementation SHA256:
  `8a5ba89168dcd7845a7f340027e552767b41836b3c10755df00a6f9b7a309e78`
- self-test job:
  `job_20260928T065945Z_6977cbfd`
- exact PASS:
  `B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_V013_SELF_TEST_PASS`

## Frozen evidence

Unchanged:

- frozen events: **94**
- unique official announcement URLs: **94**
- source-result SHA256:
  `c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c`
- event-set SHA256:
  `1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`

## Asynchronous host boundary

Wrapper:

`scripts/research/run-b15p2-announcement-body-semantic-audit-v0.2.sh`

SHA256:

`7bf4d61206b4f761f986f23cf6c58a2ddb436406b490523fb8923dc721520a31`

Launch contract:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-networked-launch-contract-v0.2.json`

Approval code:

`BM-7BF4D61206B4`

Networked execution is NOT authorized by this roadmap update.

## Execution behavior

After explicit approval:

1. run `--preflight` with no network;
2. run `--launch`;
3. staged self-test must PASS again;
4. systemd unit starts asynchronously;
5. Termux prompt returns immediately;
6. use `--status` in the same Termux session.

While running, status may expose only transport/progress information:

- `progress_started=N/94`;
- `progress_done=N/94`;
- `progress_errors=N`;
- last transport-progress line.

It must not expose partial semantic classifications.

Terminal semantic aggregates appear only after PASS/REVIEW completion.

## Runtime bounds

- per request: 30 seconds;
- attempts per URL: 2;
- maximum retry sleep per URL: 1 second;
- inter-event sleep: 0.25 seconds;
- deterministic rough worst case: ~5757 seconds;
- service bound: **7200 seconds**.

## Firewalls

Still closed:

- affected-contract price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- event outcome ranking;
- outcome-driven filtering;
- price-outcome horizon search;
- trading.

## Strategy Manager

The terminal full semantic result will be strategy-relevant.

After PASS/REVIEW:

1. freeze the canonical semantic result;
2. create `sc001.worker_result_manifest.v0.1`;
3. trigger the automatic Strategy Watch;
4. do not open any price outcome until Research Strategy Manager completes the mandatory pre-price gate.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_ASYNC_NETWORKED_SEMANTIC_AUDIT_BM-7BF4D61206B4`
