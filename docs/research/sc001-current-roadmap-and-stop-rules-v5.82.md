# SC001 Current Roadmap and Stop Rules v5.82

Date: 2026-09-25  
Status: **B15-P1 FINAL COLLECTOR LAUNCH WRAPPER OFFLINE PREFLIGHT SEALED / AWAITING APPROVAL**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.81.md`

## Current project position

All technical prerequisites before final launch are complete:

1. collector design preflight PASS;
2. collector v0.1.3 implementation freeze PASS;
3. 28/28 mandatory + 8/8 extra collector tests PASS;
4. capability v0.2.1 offline PASS;
5. live authenticated Bybit/OKX capability PASS;
6. 192/192 Bybit + 192/192 OKX + 192/192 both-venue coverage PASS;
7. collector prelaunch readiness PASS;
8. host deployment-readiness wrapper offline preflight PASS;
9. real VPS host readiness PASS;
10. VPS reboot performed before first start;
11. post-reboot host readiness PASS.

The collector is still NOT installed/enabled/started.

## Final launch wrapper prepared

Path:

`scripts/research/run-b15p1-final-collector-deployment-launch-v0.1.sh`

SHA256:

`de9f13f36ad8e5492ca3a6bb3181cf3c0d4617542253cec6f39bdfea6dfe8d17`

The wrapper is fail-closed and binds exactly to:

- runner SHA: `f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0`;
- library SHA: `f4e27edff5acb38fb1c9ee840490179d1c3ebe13fd258d8875de768acc4078b5`;
- implementation freeze SHA: `cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96`;
- live snapshot SHA: `14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`;
- service SHA: `b59d61f25b4e643f6c9f27389d9829f7e4ea91cfbbb8dffeb48a91b55d755bf8`;
- runtime launch authorization SHA: `fd5b9a6c683bd15df2dfc26c4ba6497d8e8e152d9b70ed1dc1edeab5107f13be`.

## Final wrapper behavior

Before mutation:
- verifies post-reboot host-report SHA;
- verifies live snapshot SHA;
- verifies credential env mode/owner;
- requires no existing authorization/state/manifest/launch report;
- requires no running collector;
- requires service inactive and disabled/not-found;
- validates all 22 source files by SHA;
- stages exact files;
- runs collector self-test;
- validates staged launch authorization with the collector's exact validator;
- validates frozen prerequisite result documents.

After mutation boundary:
- deploys only 19 exact B15-P1 runtime files;
- installs exact v0.1.3 service under stable name;
- systemd-analyze verify;
- daemon-reload;
- installs exact runtime authorization;
- re-validates freeze + capability + authorization at runtime;
- enables and starts only `sc001-b15p1-transferability.service`;
- waits for at least 2 polls and at least 1 valid poll;
- requires heartbeat age <= 60 seconds;
- requires nonzero poll-chain hash;
- verifies cadence 15s, request deadline 12s, fee refresh 6h, stale threshold 8h;
- verifies price/PnL remain closed;
- writes a final launch verification report.

## Rollback

After mutation starts, any error causes:
- stop service;
- disable service;
- remove the runtime authorization only if its SHA is exactly the one created by this wrapper;
- remove the stable unit only if it was absent before and still has the exact expected SHA;
- daemon-reload after unit removal.

Failure state/manifest/systemd logs are preserved for review.

## Sealed offline preflight bundle

- bundle ID: `bundle_20260925T154521Z_ed76febb`
- SHA256: `d308a48b55efd181e41eeb86b46c98bdc602db4c5f56f283ec759f1d8b154aec`
- approval code: `BM-D308A48B55EF`
- files: 26
- bytes: 345062
- runtime: `offline-research-v1`
- inputs: none

This bundle has NOT been run.

## Stop rule

Do not execute the final launch wrapper until this offline preflight returns PASS and the user gives a separate explicit approval for the real deployment/start.

Price/PnL research remains unauthorized.

## Next state

`RUN_FINAL_B15P1_COLLECTOR_LAUNCH_WRAPPER_OFFLINE_PREFLIGHT_AFTER_USER_APPROVAL`
