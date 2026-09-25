# SC001 Current Roadmap and Stop Rules v5.78

Date: 2026-09-25  
Status: **B15-P1 HOST DEPLOYMENT-READINESS WRAPPER OFFLINE PREFLIGHT SEALED / AWAITING APPROVAL**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.77.md`

## Where we are

The collector itself is still NOT running.

Completed:
- collector design preflight PASS;
- collector v0.1.3 implementation freeze;
- 28/28 mandatory + 8/8 extra collector tests PASS;
- capability v0.2.1 offline PASS;
- live authenticated source-capability PASS;
- full 192/192 Bybit + OKX coverage PASS;
- collector prelaunch readiness offline PASS;
- launch authorization fail-closed boundary PASS.

Current live snapshot SHA256:

`14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`

## Current purpose

We are preparing the VPS for a safe systemd deployment check without actually deploying or starting the collector.

The host-readiness wrapper must verify the real VPS state:
- live capability snapshot still has the exact frozen SHA;
- credential env exists, mode 0600, owner botmarket:botmarket, readable as botmarket;
- runtime launch authorization is absent;
- collector state/manifest are absent;
- no collector process is running;
- stable service is inactive and not enabled;
- installed stable unit, if already present, either matches exact v0.1.3 service SHA or the gate fails;
- no systemd drop-ins exist;
- exact 21 frozen files can be copied to a dedicated staging root and re-hashed;
- staged collector/library Python compile;
- staged collector `--mode self-test` PASS under `env -i`, with no credentials;
- staged stable-name unit passes `systemd-analyze verify`;
- no start/enable/restart/daemon-reload occurs.

## Important legacy-unit finding

The repository contains an older stable file:

`ops/systemd/sc001-b15p1-transferability.service`

which still points to collector v0.1.

It is intentionally NOT used by the new wrapper.

Canonical deployment candidate remains:

`ops/systemd/sc001-b15p1-transferability-v0.1.3.service`

SHA256:

`b59d61f25b4e643f6c9f27389d9829f7e4ea91cfbbb8dffeb48a91b55d755bf8`

Future deployment will map that exact versioned candidate to stable runtime name:

`sc001-b15p1-transferability.service`

only after later explicit approval.

## Host-readiness wrapper

Path:

`scripts/research/run-b15p1-collector-host-deployment-readiness-v0.1.sh`

SHA256:

`a962e3f1e071106228202e94af964e6c52faf1a13ca4b00c0b8ddaab6baedbdb`

Offline preflight verified statically before seal:
- 21 dependency path/SHA pins present;
- systemctl commands limited to is-active / is-enabled / show;
- collector `--mode self-test` count = 1;
- collector `--mode run` count = 0;
- no start/enable/restart/daemon-reload/stop;
- no runtime unit install;
- no legacy stable repo unit reference;
- no direct URL/curl/wget path;
- rm -rf scoped only to staging root.

## Sealed offline-preflight bundle

- bundle ID: `bundle_20260925T104044Z_27791ca1`
- SHA256: `d603b30daf2c7b65bba9406fc96247a8b5cada96a314ad18c87a53e1a393bf58`
- approval code: `BM-D603B30DAF2C`
- files: 25
- bytes: 328088
- runtime: `offline-research-v1`
- inputs: none

This bundle has NOT been run.

## Stop rule

Do not run the host wrapper until this sealed offline preflight returns PASS.

Do not install/enable/start the collector.

Do not create active runtime `collector_launch_authorization.json`.

## Next state

`RUN_B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_WRAPPER_OFFLINE_PREFLIGHT_AFTER_USER_APPROVAL`
