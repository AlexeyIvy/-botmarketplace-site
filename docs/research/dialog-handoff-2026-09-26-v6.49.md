# SC001 / B15-P1 — dialog handoff v6.49 — 2026-09-26

Current state:

`B15P1_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_PASS_REAL_HOST_LAUNCH_NEXT`

GitHub baseline before this checkpoint:
`ae449723ab33569f00a738e9a56423b09dfd6fad`

Final launch wrapper:
`scripts/research/run-b15p1-final-collector-deployment-launch-v0.2.0.sh`

Wrapper SHA256:
`25387c527fcd77b59bac96a1c88316029e093edc99848e60842e6436d90424ad`

Capability snapshot SHA256:
`01cfa63b6001ec972c4ed87daba5bbd9fba932233b9e8323a49a6a5355e89647`

Runtime authorization SHA256:
`7c6a0296dc47f91a47d4747a0d29174338599a805b797427f19aa2e0c9d3b01c`

Offline preflight:
- bundle: `bundle_20260926T122142Z_bf51bc5e`
- bundle SHA: `b334eb37fc66bc6f97a85313a6b53a4b156c1e882a014c593b3ea501021b005c`
- Runner job: `job_20260926T125951Z_ec46c508`
- result: `B15P1_FINAL_LAUNCH_V020_OFFLINE_PREFLIGHT_PASS`
- stderr: empty
- no collector start, credentials, exchange calls, systemd mutation, price/PnL or live execution occurred.

Full result:
`docs/research/sc001-b15-p1-final-launch-v0.2.0-offline-preflight-result-v0.1.json`

Roadmap:
`docs/research/sc001-current-roadmap-and-stop-rules-v5.101.md`

Next: execute the exact v0.2.0 real host wrapper on the VPS. Do not use old v0.1/v0.1.1 launch wrappers. The v0.2.0 wrapper is fail-closed and performs host prechecks before any mutation.

Recommended manual host command:

`sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-final-collector-deployment-launch-v0.2.0.sh`

After completion, preserve the complete terminal output. PASS target:

`B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V020_PASS`

If REVIEW/failure occurs, do not rerun blindly. Analyze the exact reason and rollback state first.
