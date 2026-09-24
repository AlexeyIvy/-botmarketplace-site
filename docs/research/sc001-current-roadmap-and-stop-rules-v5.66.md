# SC001 Current Roadmap and Stop Rules v5.66

Date: 2026-09-24  
Status: **B15-P1 COLLECTOR IMPLEMENTATION v0.1.1 TECHNICAL GUARD FAIL / v0.1.2 SELF-TEST SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.65.md`

## v0.1.1 self-test result

Bundle:
`bundle_20260924T112109Z_0d20dff8`

Job:
`job_20260924T113440Z_6ed95905`

Technical protections that passed:
- package integrity = true;
- runner py_compile = PASS;
- library py_compile = PASS;
- runner EOF/main guard = PASS;
- self-test logic entered.

Failure:

`CollectorError: unexpected websocket endpoint in non-price REST collector`

Root cause:

the static no-price guard scanned the library source and matched its own literal `wss://` check. No actual websocket endpoint existed elsewhere.

Safety:
- exchange calls = 0;
- credentials not used;
- collector launch = false;
- price/PnL = false.

## Corrected implementation v0.1.2

GitHub commit:

`3b757308eaf1904c7e1b4845a003e28097348231`

Runner SHA256:

`157b1e7e77a9d4299c06ac60ce56e1544335d7435d9f25a6212d7f417b312b3d`

Library SHA256:

`007a97f817f04c50655ad6339b7eb9eb15aacfa8b0c851be97b7976c69308088`

Implementation freeze SHA256:

`fc4d7496870896ff7b8036ce9c17a3d5059142be2e18dd2c21eb646f8c32fabf`

Only technical guard construction changed:
- forbidden websocket marker is assembled without embedding the literal in the guard source;
- static no-price semantics remain equally strict;
- cadence/endpoints/frozen mappings/cost model/price firewall are unchanged.

## Sealed v0.1.2 offline self-test

Bundle:

`bundle_20260924T113941Z_3d1a43a4`

SHA256:

`6c88c578e38f1f7580befc1573a2fcb0206990a6d570e9ee647ba52c4c7f36c7`

Approval code:

`BM-6C88C578E38F`

Expected tokens:
- `B15P1_NONPRICE_COLLECTOR_V012_SELF_TEST_PASS`
- `B15P1_NONPRICE_COLLECTOR_V012_COMPILE_AND_SELFTEST_PASS`

Bundle remains fully offline:
- no credentials;
- no capability snapshot;
- no launch authorization;
- no exchange calls;
- no collector launch;
- no price/PnL.

## Boundary

A PASS authorizes only:

`PREPARE_B15P1_LIVE_READ_ONLY_SOURCE_CAPABILITY_REVALIDATION`

Collector launch remains a later separate gate.

## Next state

`RUN_B15P1_NONPRICE_COLLECTOR_IMPLEMENTATION_V012_SELF_TEST_AFTER_USER_APPROVAL`
