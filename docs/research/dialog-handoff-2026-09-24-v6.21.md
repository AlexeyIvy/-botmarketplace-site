# SC001 / B15-P1 — dialog handoff v6.21 — 2026-09-24

Current state:

`B15P1_SOURCE_CAPABILITY_LIVE_WRAPPER_V02_OFFLINE_PREFLIGHT_SEALED_AWAITING_APPROVAL`

## Combined offline gate

PASS.

Bundle:
`bundle_20260924T163807Z_a5599568`

Job:
`job_20260924T170906Z_810905df`

Status:
`B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PASS`

Collector v0.1.3:
- 28/28 mandatory PASS;
- 8/8 extra PASS;
- compile+self-test PASS.

Capability v0.2.1:
- self-test PASS;
- compile+self-test PASS;
- Bybit Spot scoped pagination guard PASS.

No credentials, exchange calls, live snapshot, collector launch, price/PnL or live execution occurred.

## Safe-staging live wrapper

New wrapper:

`scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.2.sh`

SHA256:

`0bc379933be07fb7b31e2efe4a2f06b4b7b99ad2fdc4db403dbffbe63ebc556e`

It targets frozen capability v0.2.1 and collector v0.1.3.

## Wrapper offline preflight bundle

- bundle ID: `bundle_20260924T171540Z_9f83d965`
- bundle SHA256: `188ea1ddde3fb5e3633881e1e030077b5482c48ef78e99ed74106115bcd03787`
- approval code: `BM-188EA1DDDE3F`
- entrypoint: `research/sc001/sc001_b15p1_source_capability_live_wrapper_v02_offline_preflight_v0_1.py`
- files: 14
- total bytes: 209868
- runtime: `offline-research-v1`
- inputs: none

The bundle is sealed and has NOT been run.

## Next

After explicit approval, run the sealed wrapper offline preflight.

Only if it returns:

`B15P1_SOURCE_CAPABILITY_LIVE_WRAPPER_V02_OFFLINE_PREFLIGHT_PASS`

prepare for a separate explicit approval to execute the live read-only wrapper.

Do not run the old live wrapper v0.1.
