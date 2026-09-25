# SC001 / B15-P1 — dialog handoff v6.26 — 2026-09-25

Current state:

`B15P1_HOST_DEPLOYMENT_READINESS_WRAPPER_OFFLINE_PREFLIGHT_SEALED_AWAITING_APPROVAL`

## Plain-language status

We have finished validating the collector code and its API access.

The collector is NOT running yet.

We are now checking the last operational layer before deployment: whether the actual VPS is safe and ready for the exact frozen collector to be staged under systemd without accidentally starting it.

## Prepared host wrapper

`scripts/research/run-b15p1-collector-host-deployment-readiness-v0.1.sh`

SHA256:

`a962e3f1e071106228202e94af964e6c52faf1a13ca4b00c0b8ddaab6baedbdb`

It will check real VPS state and run only collector self-test from an isolated staging root.

It does NOT:
- install runtime unit;
- start/enable/restart service;
- daemon-reload;
- create active launch authorization;
- run collector mode;
- call exchange APIs;
- use price/PnL.

## Important finding

Legacy repo stable unit:

`ops/systemd/sc001-b15p1-transferability.service`

still points to v0.1.

The wrapper does not use it.

Canonical candidate is versioned v0.1.3 service with SHA:

`b59d61f25b4e643f6c9f27389d9829f7e4ea91cfbbb8dffeb48a91b55d755bf8`

## Sealed offline preflight

- bundle ID: `bundle_20260925T104044Z_27791ca1`
- bundle SHA256: `d603b30daf2c7b65bba9406fc96247a8b5cada96a314ad18c87a53e1a393bf58`
- approval code: `BM-D603B30DAF2C`
- files: 25
- bytes: 328088
- runtime: offline-research-v1
- inputs: none

The bundle is sealed and has NOT been run.

## Next

After explicit approval, run exactly this sealed offline-preflight bundle.

If it returns:

`B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_WRAPPER_OFFLINE_PREFLIGHT_PASS`

then the next action is to run the verified host-readiness wrapper manually on the VPS.

Collector launch remains a later separate approval.
