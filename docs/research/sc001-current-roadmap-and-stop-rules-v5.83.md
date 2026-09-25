# SC001 Current Roadmap and Stop Rules v5.83

Date: 2026-09-25  
Status: **B15-P1 FINAL COLLECTOR LAUNCH WRAPPER OFFLINE PREFLIGHT PASS / REAL LAUNCH APPROVAL NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.82.md`

## Final launch wrapper offline preflight

Bundle:

`bundle_20260925T154521Z_ed76febb`

Job:

`job_20260925T160937Z_b7b5e415`

Result:

`B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT_PASS`

Package integrity = true.  
Exit code = 0.

Manifest SHA256:

`fe10257934670c41ea49953a1a7e0985fbd1ba99594c85eb050994a079b22a3c`

## Verified final wrapper

Final wrapper:

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.sh`

SHA256:

`de9f13f36ad8e5492ca3a6bb3181cf3c0d4617542253cec6f39bdfea6dfe8d17`

Verified:
- 8 exact runtime/hash anchors;
- 22 source dependencies;
- 19 runtime deployment dependencies;
- bash syntax PASS;
- 5 embedded Python blocks compile;
- exactly one collector self-test invocation;
- zero direct collector `--mode run` invocations;
- canonical runtime launch authorization SHA:
  `fd5b9a6c683bd15df2dfc26c4ba6497d8e8e152d9b70ed1dc1edeab5107f13be`;
- prerequisite prelaunch PASS;
- post-reboot host-readiness PASS;
- exact operation ordering PASS;
- rollback marker count = 8;
- runtime verification marker count = 12;
- staging deletion scoped only to staging root.

Forbidden behavior checks all PASS:
- no systemctl restart;
- no mask/unmask;
- no legacy stable repo unit;
- no direct curl/wget/nc/socat;
- no direct URL;
- no failure-state deletion;
- no manifest deletion;
- no systemd-log deletion;
- no output-root deletion.

## Final runtime verification contract

After the real start, the wrapper will require:
- stable service active;
- stable service enabled;
- minimum 2 polls;
- minimum 1 valid poll;
- heartbeat age <= 60 seconds;
- nonzero poll-chain hash;
- cadence = 15 seconds;
- request deadline = 12 seconds;
- fee refresh = 21600 seconds;
- fee stale threshold = 28800 seconds;
- price data closed;
- PnL closed.

## Rollback contract

After mutation begins, any failure must:
- stop the service;
- disable the service;
- remove only the exact launch authorization created by this wrapper;
- remove the stable unit only if it was absent before and still has the exact expected SHA;
- daemon-reload after unit rollback;
- preserve state/manifest/systemd logs for forensic review.

## Safety of this completed preflight

No:
- credentials;
- exchange calls;
- systemd mutation;
- runtime authorization creation;
- collector start;
- price/PnL;
- live execution.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_FINAL_B15P1_COLLECTOR_DEPLOYMENT_AND_START`

The next action is the real final deployment/start wrapper on the VPS and requires separate explicit user approval.
