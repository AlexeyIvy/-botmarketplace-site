# SC001 Current Roadmap and Stop Rules v5.68

Date: 2026-09-24  
Status: **B15-P1 COLLECTOR v0.1.2 SELF-TEST PASS / SOURCE CAPABILITY OFFLINE SELF-TEST SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.67.md`

## Collector implementation v0.1.2

Completed:

`B15P1_NONPRICE_COLLECTOR_V012_SELF_TEST_PASS`

and

`B15P1_NONPRICE_COLLECTOR_V012_COMPILE_AND_SELFTEST_PASS`

Job:

`job_20260924T120400Z_a7968f31`

All mandatory offline collector tests passed.

No exchange calls, credentials, collector launch, price or PnL were used.

## Live source-capability revalidation design

A new collector-specific capability probe v0.1 is frozen.

Purpose:
- bind capability result to the exact collector v0.1.2 runner/freeze/route graph;
- revalidate dedicated Bybit/OKX read-only credentials;
- require IP binding;
- validate collector source schema;
- qualify exact live USDT spot pairs for the frozen 192 admitted assets using public instrument metadata only;
- probe one exact account/pair fee endpoint on each venue;
- generate the secret-free `source_capability_snapshot.json` expected by the collector.

Allowed live calls include only:
- public server time;
- public spot instrument metadata;
- read-only permission endpoints;
- read-only source metadata endpoints;
- one account/pair fee metadata probe per venue.

No ticker, orderbook, candle, order, transfer or withdrawal call is allowed.

Pair qualification does not modify the frozen identity universe.

## Sealed offline capability self-test

Bundle:

`bundle_20260924T121552Z_a91e518e`

SHA256:

`b3342137e7d258fab5ae7b0bddf9cd926cf53b9da2c759027e7e71d69dbe6d70`

Approval code:

`BM-B3342137E7D2`

Probe SHA256:

`489e769665abcefd56bba9937d4179e932083e4545b3d1cac85638adf2b4bf1a`

Capability freeze SHA256:

`d0332d69208de8cdb4f8fdf9e521ff31b9db02717edbb1b2fae688931af4b4c3`

Expected PASS tokens:
- `B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_SELF_TEST_PASS`
- `B15P1_NONPRICE_SOURCE_CAPABILITY_COMPILE_AND_SELFTEST_PASS`

This bundle is offline:
- credentials absent;
- exchange calls = 0;
- capability snapshot not written;
- collector launch = false;
- price/PnL = false.

## Required order

1. run offline capability probe self-test;
2. if PASS, run the frozen live read-only probe on the VPS using the existing protected B15 credentials;
3. capture the secret-free capability snapshot and PASS summary;
4. verify systemd unit;
5. prepare explicit launch authorization;
6. only then consider collector launch.

## Next state

`RUN_B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_OFFLINE_SELF_TEST_AFTER_USER_APPROVAL`
