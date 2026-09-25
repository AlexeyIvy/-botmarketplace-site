# SC001 Current Roadmap and Stop Rules v5.85

Date: 2026-09-25
Status: **B15-P1 FAILED LAUNCH RECOVERY WRAPPER OFFLINE PREFLIGHT PASS / HOST RECOVERY NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.84.md`

## Recovery preflight result

Bundle:

`bundle_20260925T163125Z_2331de78`

Job:

`job_20260925T163702Z_51227679`

Result:

`B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_PASS`

Manifest SHA256:

`923ee7e05a61a22db293be021b43b79397930b6e58ff008e4386aa72eda81266`

Package integrity = true.
Exit code = 0.

## Verified recovery wrapper

Wrapper:

`scripts/research/run-b15p1-final-launch-v0.1-failure-recovery-v0.1.sh`

SHA256:

`9ef7d1631d5e1b54d01b33c27b30050837e1914051784d2e114f7ed7efe903bb`

Verified:
- bash syntax PASS;
- embedded Python compile PASS;
- 24 required recovery markers;
- no protected evidence mutation;
- no systemctl start;
- no systemctl enable;
- no systemctl restart;
- no collector run;
- no snapshot deletion;
- systemctl set limited to stop/disable/is-active/is-enabled/daemon-reload.

## Recovery host action

The next action is NOT a collector retry.

Run recovery on VPS first.

The recovery wrapper will:
1. force stop + disable;
2. confirm no collector process;
3. archive exact runtime authorization if it remains;
4. archive exact runtime unit if it remains, then remove it and daemon-reload;
5. archive state/manifest/systemd.log/polls/raw/normalized/events/gaps/fees/invalid/daily manifests from the failed attempt;
6. hash all archived files recursively;
7. verify active runtime authorization/state/manifest/unit are absent;
8. preserve live capability snapshot and host-readiness evidence.

## Stop rule

Do not rerun final launch v0.1.

Do not manually start/enable collector.

Only after host recovery PASS prepare corrected final launch v0.1.1 with NOT_READY-aware poll verification.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_FAILURE_RECOVERY_HOST_WRAPPER`
