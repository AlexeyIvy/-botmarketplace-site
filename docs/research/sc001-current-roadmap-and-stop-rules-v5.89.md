# SC001 Current Roadmap and Stop Rules v5.89

Date: 2026-09-25  
Status: **B15-P1 FINAL LAUNCH v0.1.1 SOURCE-VALIDITY TIMEOUT / READ-ONLY EVIDENCE DIAGNOSIS NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.88.md`

## Real v0.1.1 host retry result

The corrected v0.1.1 launch wrapper no longer reproduces the old ERR-trap bug.

Observed repeatedly during the readiness window:

`NOT_READY = valid_poll_count:0`

Terminal result:

`B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V011_REVIEW`

Reason:

`collector_initial_readiness_timeout`

Rollback:

`rollback_incomplete=0`

Systemd log tail confirmed:
- collector reached RUNNING;
- fast cadence = 15 seconds;
- price/PnL = CLOSED.

## Interpretation

This is a different failure class from the prior v0.1 control-flow defect.

The v0.1.1 NOT_READY loop worked correctly and waited instead of prematurely tripping ERR.

However, every completed poll was invalid because at least one venue did not have `status=OK`.

The collector stores the exact per-venue evidence in poll JSONL rows:
- status;
- HTTP status;
- elapsed time;
- safe rate-limit headers;
- raw-body SHA;
- redacted error.

No assumption is made yet about which venue failed or why.

Possible classes to distinguish from stored evidence:
- Bybit/OKX API code;
- HTTP status/rate limit;
- request deadline;
- scheduler overrun;
- transport/TLS/connection error;
- JSON/schema parse;
- another source-invalid reason.

## Read-only diagnostic prepared

Script:

`scripts/research/diagnose-b15p1-final-launch-v0.1.1-source-invalid-v0.1.py`

SHA256:

`fb4401b355cbc098863b9913cdaafaea5b5974ece7dbc35a0031265047780470`

It performs no exchange calls and does not read credential env files.

It reads only already-persisted:
- collector state;
- collector manifest;
- poll JSONL;
- source gaps;
- invalid records;
- fee records;
- raw objects;
- systemd state/log metadata;
- capability snapshot hash;
- runtime authorization/unit presence.

It writes one diagnostic JSON under:

`/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/diagnostics/`

and prints a concise venue-by-venue summary.

The script was syntax-checked and smoke-tested against a synthetic source-invalid fixture before repository commit.

## Stop rule

Do not rerun final launch v0.1.1 yet.

Do not change collector/parser/API cadence until the saved poll evidence identifies the actual failure class.

Price/PnL remain unauthorized.

## Next state

`RUN_READ_ONLY_V011_SOURCE_INVALID_DIAGNOSTIC_ON_VPS`
