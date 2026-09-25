# SC001 / B15-P1 — dialog handoff v6.31 — 2026-09-25

Current state:

`B15P1_FINAL_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT_PASS_AWAITING_REAL_LAUNCH_APPROVAL`

## Latest PASS

Bundle:
`bundle_20260925T154521Z_ed76febb`

Job:
`job_20260925T160937Z_b7b5e415`

Status:
`B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT_PASS`

Manifest SHA256:
`fe10257934670c41ea49953a1a7e0985fbd1ba99594c85eb050994a079b22a3c`

## Final launch wrapper

Path:
`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.sh`

SHA256:
`de9f13f36ad8e5492ca3a6bb3181cf3c0d4617542253cec6f39bdfea6dfe8d17`

Offline validation:
- 22 source deps;
- 19 deploy deps;
- 5 Python heredocs;
- canonical authorization SHA verified;
- ordering verified;
- rollback verified;
- initial runtime heartbeat/poll verification verified;
- price/PnL remain closed.

No live mutation occurred in the preflight.

## Next

Only after explicit user approval, run the final wrapper on the VPS.

That action will:
- deploy exact B15-P1 runtime files;
- install stable systemd unit;
- create exact runtime launch authorization;
- enable/start collector;
- verify first polls/heartbeat;
- rollback fail-closed on error.

Collector is NOT running yet.
