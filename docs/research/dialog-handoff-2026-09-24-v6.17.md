# SC001 / B15-P1 — dialog handoff v6.17 — 2026-09-24

Latest completed state:

`B15P1_NONPRICE_COLLECTOR_IMPLEMENTATION_V012_SELF_TEST_PASS`

Latest prepared state:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_OFFLINE_SELF_TEST_SEALED_RUN_PENDING`

## Collector v0.1.2 PASS

- job: `job_20260924T120400Z_a7968f31`
- runner SHA256: `157b1e7e77a9d4299c06ac60ce56e1544335d7435d9f25a6212d7f417b312b3d`
- implementation freeze SHA256: `fc4d7496870896ff7b8036ce9c17a3d5059142be2e18dd2c21eb646f8c32fabf`
- self-test manifest SHA256: `d54b4ee0711dfe39ae1b606ae2f7caa25115d70106f405960cfddab87b85f0ef`

All mandatory offline tests passed. No exchange calls or price/PnL.

## Capability probe v0.1

Commit:

`ab4f9060a1f4b01d7a6491e8e3a099159ce77464`

Probe SHA256:

`489e769665abcefd56bba9937d4179e932083e4545b3d1cac85638adf2b4bf1a`

Capability freeze SHA256:

`d0332d69208de8cdb4f8fdf9e521ff31b9db02717edbb1b2fae688931af4b4c3`

## Sealed offline self-test

- bundle: `bundle_20260924T121552Z_a91e518e`
- SHA256: `b3342137e7d258fab5ae7b0bddf9cd926cf53b9da2c759027e7e71d69dbe6d70`
- approval code: `BM-B3342137E7D2`

Expected PASS:
- `B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_SELF_TEST_PASS`
- `B15P1_NONPRICE_SOURCE_CAPABILITY_COMPILE_AND_SELFTEST_PASS`

The self-test is offline and requires no credentials.

## After offline PASS

Run live revalidation on VPS with the existing 0600 B15 env file.

Collector launch remains unauthorized.
