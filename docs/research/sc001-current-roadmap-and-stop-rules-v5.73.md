# SC001 Current Roadmap and Stop Rules v5.73

Date: 2026-09-24  
Status: **B15-P1 COMBINED OFFLINE PASS / LIVE WRAPPER v0.2 OFFLINE PREFLIGHT SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.72.md`

## Combined offline validation v0.1.1

Sealed bundle:
`bundle_20260924T163807Z_a5599568`

Job:
`job_20260924T170906Z_810905df`

Result:
`B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PASS`

Verified:
- package integrity PASS;
- exit code 0;
- collector v0.1.3 compile+self-test PASS;
- 28/28 mandatory collector tests PASS;
- 8/8 extra collector tests PASS;
- capability v0.2.1 compile+self-test PASS;
- scoped Bybit Spot pagination guard PASS;
- credentials used = false;
- exchange calls = false;
- capability snapshot written = false;
- collector launch = false;
- price/PnL = false;
- live execution = false.

Result document SHA256:

`c9b2a2dfa193a596939627284a7221541452434cbab363b92dece4477c3d913a`

## New safe-staging live wrapper

Wrapper:

`scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.2.sh`

Wrapper SHA256:

`0bc379933be07fb7b31e2efe4a2f06b4b7b99ad2fdc4db403dbffbe63ebc556e`

Target capability:

`v0.2.1`

The wrapper:
- requires root only for safe staging;
- leaves GitHub Control clone permissions unchanged;
- requires protected credential env mode 0600;
- confirms botmarket can read the env file;
- validates exact SHA256 for all 10 staged non-secret dependencies;
- copies only those exact dependencies into a botmarket-owned staging root;
- rechecks SHA after staging;
- rejects staging symlinks and unexpected file count;
- rechecks the successful combined offline prerequisite before live calls;
- removes stale capability snapshot/summary before running;
- runs only the frozen capability probe as botmarket;
- performs post-run anchor, permission, endpoint-security and snapshot-integrity checks;
- does not start the collector or create launch authorization.

## Wrapper offline preflight

Harness SHA256:

`5e8886fe3e4d96f6d8c2279dfe9f29730445ea0061c66370571573abad359674`

Spec SHA256:

`3e457fe433de6ccbe5b3ac7b43e9f5b4fa19cf704994ebf151f7de0268b0f0bf`

Freeze SHA256:

`49467cc88ae58627907762702f3e135f48e7fcdead30dd0f57944dcddd63c234`

Sealed Runner bundle:
- bundle ID: `bundle_20260924T171540Z_9f83d965`
- SHA256: `188ea1ddde3fb5e3633881e1e030077b5482c48ef78e99ed74106115bcd03787`
- approval code: `BM-188EA1DDDE3F`
- files: 14
- total bytes: 209868
- runtime: `offline-research-v1`
- inputs: none

This preflight is fully offline and has NOT been run.

## Stop rule

Do not execute the live wrapper until:
1. the sealed wrapper offline preflight returns full PASS; and
2. a separate explicit user approval is given for the live read-only revalidation.

Do not reuse the old live wrapper v0.1.

## Next state

`RUN_B15P1_SOURCE_CAPABILITY_LIVE_WRAPPER_V02_OFFLINE_PREFLIGHT_AFTER_USER_APPROVAL`
