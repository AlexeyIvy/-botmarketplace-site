# SC001 Current Roadmap and Stop Rules v5.81

Date: 2026-09-25  
Status: **B15-P1 POST-REBOOT HOST READINESS PASS / FINAL COLLECTOR LAUNCH GATE NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.80.md`

## Post-reboot host readiness

The VPS was rebooted before the first collector start.

The same verified non-starting host-readiness wrapper was rerun after reconnect.

Observed:

`B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_PASS`

Post-reboot host report SHA256:

`e249f824a4b10f19a81aa6e01f1f5d7beee5088997880b146378f73f676d7aee`

Live snapshot SHA256 remains:

`14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`

## Verified post-reboot VPS baseline

- collector v0.1.3 staged self-test PASS;
- live snapshot contract PASS;
- base assets = 146;
- overlay assets = 46;
- asset common representations = 207;
- quote common representations = 12;
- quote one-sided representations = 14;
- stable service active = inactive;
- stable service enabled = not-found;
- stable runtime unit = absent;
- runtime launch authorization = absent;
- collector start performed = false;
- systemd start/enable performed = false.

The reboot hold is cleared.

## What this means

All preconditions for preparing the final controlled launch gate are now satisfied:

1. collector design preflight PASS;
2. implementation freeze PASS;
3. 28/28 mandatory + 8/8 extra offline tests PASS;
4. capability v0.2.1 offline PASS;
5. live authenticated Bybit/OKX capability PASS;
6. 192/192 both-venue coverage PASS;
7. collector prelaunch readiness PASS;
8. host deployment-readiness wrapper offline preflight PASS;
9. real VPS host readiness PASS;
10. post-reboot real VPS host readiness PASS.

The collector is still NOT installed, enabled or started.

## Final launch gate requirements

The final deployment/authorization/start procedure must be fail-closed and bind exactly to:
- collector runner SHA `f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0`;
- collector library SHA `f4e27edff5acb38fb1c9ee840490179d1c3ebe13fd258d8875de768acc4078b5`;
- implementation freeze SHA `cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96`;
- live capability snapshot SHA `14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc`;
- service candidate SHA `b59d61f25b4e643f6c9f27389d9829f7e4ea91cfbbb8dffeb48a91b55d755bf8`.

The final procedure must:
- deploy exact frozen runtime files;
- install the exact v0.1.3 service candidate under stable runtime name `sc001-b15p1-transferability.service`;
- create the exact runtime launch authorization bound to the hashes above;
- daemon-reload only after exact unit installation;
- enable/start only this collector service;
- verify service active state, collector manifest/state, first heartbeat and initial poll progress;
- verify price/PnL remain closed;
- fail closed on any hash/state mismatch.

## Stop rule

Do not perform final deployment/start until the final launch wrapper itself has passed an offline preflight and a new explicit user approval is given.

Price/PnL research remains unauthorized.

## Next state

`PREPARE_FINAL_COLLECTOR_DEPLOYMENT_AUTHORIZATION_AND_START_GATE`
