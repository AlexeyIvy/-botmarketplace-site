# SC001 Current Roadmap and Stop Rules v5.152

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A future retry wait / B13-C+B14-B terminal with reusable blocks / B15-P2 source-census self-test SEALED**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.151.md`

## B14-B closed

Terminal:

`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`

Reusable:

`RB022 — Persistent cross-venue funding-differential direction state v0.1`

No rescue tuning.

## B15-P2 source-only branch

Mechanism family:

`SCHEDULED PERPETUAL DELISTING / FORCED CLOSE`

First census venue:

`BYBIT`

No price outcome authorized.

## Exact offline self-test bundle

Bundle ID:

`bundle_20260927T095903Z_afb63063`

SHA256:

`ed2812b5baae997a24e3f10e5a214a5d71ae9f0f9fe9448625a4faf03611592a`

Approval code:

`BM-ED2812B5BAAE`

Runtime:
`offline-research-v1`

Inputs:
none

Package files:
5

Package bytes:
28,061

Entrypoint SHA256:

`da047f6dba6881fdfa04db187616b851e1ed35af7af9b33ed6921daed807f8ef`

Expected PASS:

`B15P2_BYBIT_DELISTING_SOURCE_CENSUS_V01_SELF_TEST_PASS`

## Self-test scope

Synthetic-only validation:
- exact product filtering;
- pre-market identity exclusion;
- exact alphanumeric symbol matching;
- causal pre-event notice;
- revision handling;
- deliveryTime identity;
- coverage/month breadth gates;
- lead-time quantiles.

No:
- network;
- real announcements;
- real instrument metadata;
- prices;
- basis;
- PnL.

## After PASS

Prepare a separate networked source-only census launch.

That later census may read only:
- official Bybit delisting announcements;
- official closed linear instrument metadata.

It still may not read any price outcome.

## Next state

`RUN_B15P2_BYBIT_DELISTING_SOURCE_CENSUS_OFFLINE_SELFTEST_AFTER_EXPLICIT_APPROVAL`
