# SC001 P1 collector health adapter static/synthetic preparation result v0.1

Date: 2026-10-05
TASK_ID: SC001-P1-OPS-002
WORKER_ID: P1_PROSPECTIVE_EVENT
Authorization: T0_REPOSITORY_IMPLEMENTATION_AND_SYNTHETIC_TEST_PREP
TERMINAL_STATUS: P1_HEALTH_ADAPTER_IMPLEMENTATION_READY_FOR_REVIEW
CONTINUATION_REVIEW_REQUIRED: true
STRATEGY_REVIEW_REQUIRED: false
PR: https://github.com/AlexeyIvy/-botmarketplace-site/pull/435

## Result

The fixed-purpose B13-C operational-health adapter and its offline synthetic
test fixture are prepared on the task branch. This terminal state is an
implementation-preparation/static-review result only. It is not a runtime test
PASS and authorizes no merge, deployment, live state read, collector access,
permission change or service action.

The dispatcher amended the exact task before any test launch:

- \`HEARTBEAT_STALE_AFTER_MS=90000\` is prospectively frozen as a
  60-second collector stale-connection bound plus a 30-second heartbeat margin.
  The implementation uses exactly 90,000 ms. This operational threshold is not
  evidence eligibility and must not be tuned after synthetic or live observations.
- Test Executor execution is deferred until Strategy Manager review/merge.
  \`max_test_executor_runs=0\` for this task. No Test Executor job was launched.

Current main remained identical to dispatch base
\`d4221a2d7b1ac13c2afc7f10cef1d5c645a6d05b\` at pre-result revalidation.
The corrected task manifest blob is
\`3ec253527e416fa6753bb4748535b3ee430055a2\`.

## Artifacts and identities

| Artifact | Git blob SHA | SHA256 |
| --- | --- | --- |
| \`ops/mcp/sc001_b13c_health_adapter_v0_1.py\` | \`4c26f19b362d4f8ee9af1b34cbbf4d924323f755\` | \`844949ec670c6cd1856d2a1ea016f3554b6c6e85b95b254b6e370907eb47d2c7\` |
| \`tests/research/sc001_b13c_health_adapter_synthetic_test_v0_1.py\` | \`2a36f2992939b5d343be07491d2d9d3dc1d00b9c\` | \`9d33b9938c6a1cf67675d069527ce84d2fddcd8976c7a93b05a2ad9717f95da3\` |

Exact committed contents were read back from PR head
\`32b2c55488a41d304624683841e3ede981ae2b05\` before this result was created.
No executable or test file changed during the intervening dispatcher corrections.

## Implementation contract

The only public adapter function is zero-argument \`get_health()\`. Production
identities are fixed in code:

- collector: \`SC001_B13C_PROSPECTIVE_LIQUIDATIONS\`;
- state path:
  \`/home/botmarket/sc001_data/SC001_B13C_PROSPECTIVE_LIQUIDATIONS/collector_state.json\`;
- systemd unit: \`sc001-b13c-liquidation.service\`;
- command: fixed non-shell \`systemctl show\` argument vector;
- maximum state bytes: 65,536;
- heartbeat stale threshold: 90,000 ms;
- expected stage:
  \`SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.3\`;
- expected version: \`0.3\`.

The file path is opened component-by-component without following symlinks. The
final opened inode must be regular and within the byte bound. JSON rejects
invalid UTF-8, malformed structure and duplicate keys. Identity and scalar types
are strict; booleans are not accepted as integers. Missing fields remain
unavailable/null and are never silently converted to zero.

Only these state families are projected into a newly constructed response:

- bounded collector status;
- bounded connection state;
- heartbeat state and age, using \`last_heartbeat_ms\` only;
- qualified-symbol count;
- reconnect count and cumulative connection gap;
- process-restart count and cumulative process gap.

Raw JSON, symbols, raw/event/invalid counts, \`last_message_ms\`, event
frequencies, timestamps other than observation time, prices, sizes, clusters,
returns, PnL, log content and raw exception text are not returned. A connected
or running state never becomes a completeness or evidence-eligibility PASS;
the response fixes \`evidence_eligibility=NOT_EVALUATED\`.

The process query contains no shell or service-control verb. Failures return
bounded error enums and never raw stderr/exception content. Static source review
found no network imports or mutation calls such as chmod/chown/kill/write/remove.

## Synthetic fixture static review

The prepared standard-library \`unittest\` fixture contains 23 test methods and
covers the exact task requirements:

- allowlist-only projection and deliberate forbidden-marker leakage checks;
- CURRENT, STALE, FUTURE and unavailable heartbeat semantics;
- no fallback from missing heartbeat to \`last_message_ms\`;
- missing counters remain null, not zero;
- malformed JSON, invalid UTF-8 and duplicate-key rejection;
- wrong stage/version and strict scalar/type/range rejection;
- bounded file size;
- final and parent symlink rejection;
- FIFO, directory, missing-file and relative-path rejection;
- zero-argument public surface and fixed production path;
- fixed unit and fixed nonmutating \`systemctl show\` vector with \`shell=False\`;
- bounded process-query errors without raw-text leakage;
- static isolation from network and filesystem/service mutation primitives;
- explicit check that CONNECTED/running does not claim completeness.

This review verifies source coverage and frozen constants. It does not claim that
Python import, syntax, platform behavior or the tests themselves have executed.
Those remain deliberately pending for the separately authorized canonical-main
offline run.

## Execution and repair ledger

- Worker repository commits before this result: 2.
- New allowed implementation/test files before this result: 2.
- Test Executor runs: 0 of 0.
- Network runs: 0.
- Repair cycles: 0 of 1.
- Runtime failure signatures observed: none.
- Tests weakened: false.
- Outcome accessed: false.
- Protected evidence accessed: false.

The Test Executor capability/info endpoint was read once while the original
pre-correction task still allowed the exact offline run. That read exposed only
executor limits/capability metadata. No job, repository test execution, job log
or job artifact was launched or opened. After the dispatcher correction, no
further Test Executor call was made.

## Safety receipts

\`\`\`text
live_collector_state_read=false
vps_browsed=false
protected_evidence_accessed=false
outcome_accessed=false
price_return_pnl_accessed=false
collector_changed=false
collector_restarted=false
systemd_changed=false
permissions_or_acl_changed=false
deployment_performed=false
network_accessed=false
runner_bundle_created=false
runner_bundle_executed=false
test_executor_info_metadata_read=true
test_executor_job_launched=false
test_executor_job_log_read=false
test_executor_job_artifact_read=false
\`\`\`

Here \`network_accessed=false\` means no research/source network, socket probe or
runtime network use. Authorized GitHub connector operations occurred.

## Residual host-side and T3 requirements

No host-side deployment sandbox, service account, exact read privilege, MCP
exposure, rate/caching policy or live-path behavior has been validated.

After an offline synthetic PASS from canonical main, any live deployment,
service/permission/interface installation, exact \`collector_state.json\` read,
or collector/systemd change still requires separately explicit T3 authorization
for the exact action. That later work must preserve the protected window and may
not broaden access to raw/event/log directories.

## Exact next action

1. Strategy Manager reviews this PR and decides whether to merge it. This worker
   has no merge/close/retarget/auto-merge or branch-deletion authority.
2. After merge, issue one separate exact authorization for an OFFLINE Test
   Executor run from canonical main using only
   \`tests/research/sc001_b13c_health_adapter_synthetic_test_v0_1.py\`,
   network profile \`offline\`, timeout 120 seconds, maximum one run.
3. Treat that future runtime result only as adapter synthetic validation. It
   authorizes neither deployment nor live/protected access.

No second task is started by this worker.
