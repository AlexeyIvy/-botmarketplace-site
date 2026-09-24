# SC001 Current Roadmap and Stop Rules v5.64

Date: 2026-09-24  
Status: **B15-P1 NON-PRICE COLLECTOR IMPLEMENTATION v0.1 FROZEN / OFFLINE SELF-TEST SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.63.md`

## Frozen implementation

GitHub commit:

`124e8473777834f8aee7fbcf08a3e3da1045a62f`

Runner:

`research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1.py`

Runner SHA256:

`f4fd8d2672f726623eced6f4fa9d3bd0023b21b46f9037998803b7c5ee172db7`

Library SHA256:

`e03fdf1fd99b71ded3c4bbbd981d117b8ffbc89769e1c607776079cc280cb525`

Implementation freeze:

`docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.json`

Freeze SHA256:

`773fd3d2308ddf1b7a48a339db70db16ee1ff1add789f8a96887449a7eed4632`

## Implementation hardening

Frozen before self-test:

- exact v0.2.2/base-v0.1 live identity matchers;
- no fuzzy route admission;
- duplicate-alias metadata conflicts fail closed;
- 15-second phase scheduler;
- 12-second request deadline;
- no catch-up and no overlapping fast request per venue;
- independent Bybit/OKX fast source calls;
- slow account-fee lane isolated from fast polling;
- incremental fee-result persistence;
- exact raw HTTP bodies stored content-addressed by SHA256;
- append-only poll/normalized/event evidence;
- daily file hash manifest;
- poll hash chain;
- explicit source/process gaps;
- outside-frozen-route appeared/disappeared chronology with route_admitted=false;
- storage pressure fail-closed;
- atomic persistent state;
- systemd candidate;
- explicit launch-authorization file required before run mode.

## Run firewall

Even a valid capability snapshot is insufficient to start collection.

`--mode run` also requires an exact launch authorization bound to:

- runner SHA;
- implementation freeze SHA;
- capability snapshot SHA;
- systemd service SHA.

Without it:

`COLLECTOR_LAUNCH_NOT_AUTHORIZED`

## Sealed offline self-test

Bundle:

`bundle_20260924T105813Z_5a03098a`

SHA256:

`d8aa8f3698ffa43650b2c68177a8086ab45353cc3d547c4c66f15f5282b6cdde`

Approval code:

`BM-D8AA8F3698FF`

State:

`SEALED_RUN_PENDING`

The bundle contains no API credentials, no capability snapshot and no launch authorization.

Expected PASS token:

`B15P1_NONPRICE_COLLECTOR_V01_SELF_TEST_PASS`

Mandatory tests cover:

- frozen hash handshake;
- scheduler / no-catchup / no-overlap;
- Bybit and OKX parsers;
- frozen mapping counts and exact matchers;
- alias conflict fail-closed;
- route-state and transition fixtures;
- source-gap fixtures;
- fee staleness;
- storage pressure;
- content-addressed raw storage + corruption detection;
- append-only writes;
- atomic state/restart semantics;
- secret redaction;
- launch-authorization fail-closed;
- poll hash-chain tamper;
- systemd candidate static guard;
- no-price-endpoint static guard.

## Boundary

A self-test PASS authorizes only:

`PREPARE_B15P1_LIVE_READ_ONLY_SOURCE_CAPABILITY_REVALIDATION`

It does not authorize collector launch.

Still false:

- collector launch authorization;
- price/economic authorization;
- PnL;
- live execution.

## Next state

`RUN_B15P1_NONPRICE_COLLECTOR_IMPLEMENTATION_SELF_TEST_AFTER_USER_APPROVAL`
