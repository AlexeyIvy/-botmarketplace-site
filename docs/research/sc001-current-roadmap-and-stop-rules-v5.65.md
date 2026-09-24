# SC001 Current Roadmap and Stop Rules v5.65

Date: 2026-09-24  
Status: **B15-P1 COLLECTOR IMPLEMENTATION v0.1 TECHNICAL FAIL / v0.1.1 CORRECTED SELF-TEST SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.64.md`

## v0.1 technical failure

The first implementation self-test:

- bundle: `bundle_20260924T105813Z_5a03098a`
- job: `job_20260924T110817Z_2d8e094b`
- package integrity: PASS
- process exit: 1

failed before self-test logic entered.

Exact failure:

`SyntaxError: unterminated string literal`

at runner line 1826.

Root cause:

the large v0.1 runner had been truncated during an earlier bounded read/edit cycle and ended mid-key at `"ambigu`.

Consequences:
- no exchange call was made;
- no credential was used;
- collector was not launched;
- no price/PnL data was opened;
- identity/route/cost/design research semantics were not changed.

## Corrected implementation v0.1.1

GitHub commit:

`3125e1f72605b803ab7f73228bc2199b96828245`

Runner:
- path: `research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_1.py`
- SHA256: `698835eda4a17e76b9127586bff72d95c9fb1e721b30708755a9198e43ca3211`
- size: 71,319 bytes
- lines: 1,899
- EOF/main completeness guard: PASS

Library SHA256:

`99f1f2b28d415b1574c2c998a7a7ba6e73317bd09825d9f760b0faf5417fcfc7`

Implementation freeze SHA256:

`df826ff11da7fddf91fcc247fc70a32dff3ee79f88f0b4b9ed11304b64946caa`

Additional correction hardening:
- missing runner tail restored;
- compile harness added;
- runner + library must pass `py_compile` before self-test;
- EOF/main guard is checked;
- fast poll ledger now binds request-start and receive timestamps;
- source/server timestamp retained when supplied.

No research threshold, cadence, route rule or price firewall changed.

## Corrected sealed offline self-test

Bundle:

`bundle_20260924T112109Z_0d20dff8`

SHA256:

`eb0e9ee92d2a0fc64a620206b103fc11ecd64dc4c858039af1855fc4776b6006`

Approval code:

`BM-EB0E9EE92D2A`

Entrypoint:

`research/sc001/sc001_b15p1_nonprice_collector_selftest_harness_v0_1_1.py`

Expected tokens:

- `B15P1_NONPRICE_COLLECTOR_V011_SELF_TEST_PASS`
- `B15P1_NONPRICE_COLLECTOR_V011_COMPILE_AND_SELFTEST_PASS`

Bundle is offline:
- no API credentials;
- no capability snapshot;
- no launch authorization;
- no exchange calls;
- no collector launch;
- no price/PnL.

## Boundary

A PASS authorizes only:

`PREPARE_B15P1_LIVE_READ_ONLY_SOURCE_CAPABILITY_REVALIDATION`

Collector launch still requires:
1. live read-only capability revalidation;
2. systemd unit verification;
3. explicit launch authorization.

## Next state

`RUN_B15P1_NONPRICE_COLLECTOR_IMPLEMENTATION_V011_SELF_TEST_AFTER_USER_APPROVAL`
