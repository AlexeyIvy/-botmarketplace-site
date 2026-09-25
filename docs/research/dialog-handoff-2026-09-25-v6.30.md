# SC001 / B15-P1 — dialog handoff v6.30 — 2026-09-25

Current state:

`B15P1_FINAL_COLLECTOR_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT_SEALED_AWAITING_APPROVAL`

## Where we are

All collector code/API/host prerequisites have passed, including post-reboot VPS readiness.

The collector is still NOT running.

## Final launch wrapper

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.sh`

SHA256:

`de9f13f36ad8e5492ca3a6bb3181cf3c0d4617542253cec6f39bdfea6dfe8d17`

It is transactional/fail-closed:
- exact frozen deploy;
- exact runtime authorization;
- stable systemd unit;
- prestart runtime validator;
- enable/start only after validation;
- minimum two polls + one valid poll;
- heartbeat + chain verification;
- rollback stop/disable/auth/unit on failure;
- failure evidence preserved;
- price/PnL remain closed.

## Sealed offline-preflight bundle

- bundle ID: `bundle_20260925T154521Z_ed76febb`
- bundle SHA256: `d308a48b55efd181e41eeb86b46c98bdc602db4c5f56f283ec759f1d8b154aec`
- approval code: `BM-D308A48B55EF`
- files: 26
- bytes: 345062
- runtime: offline-research-v1
- inputs: none

The bundle has NOT been run.

## Next

After explicit approval, run exactly this sealed offline-preflight bundle.

Only after full PASS may the user separately approve the real final collector deployment/start wrapper.
