# SC001 / B15-P1 — dialog handoff v6.20 — 2026-09-24

Current state:

`B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_V011_SEALED_AWAITING_APPROVAL`

## What happened

The first combined offline validation ran from sealed bundle:

`bundle_20260924T154611Z_653834a4`

Job:

`job_20260924T162915Z_80dc0899`

Collector v0.1.3 fully PASS:
- 28/28 mandatory;
- 8/8 extra;
- compile+self-test PASS.

Capability v0.2 stopped on a self-referential static guard false positive:
the source-wide check for `nextPageCursor` matched its own guard literal.

No credentials, exchange calls, capability live snapshot, collector launch, price/PnL, or live execution occurred.

## Correction

Capability v0.2.1 changes only the Bybit Spot pagination self-test guard.

Actual Bybit adapter behavior is unchanged and remains non-paginated.

Capability v0.2.1:
- probe SHA256: `dacaacd8563ec80d7f9f3006cc846795aa7e5e017518a817c962ee1dc7c1f1fe`
- harness SHA256: `25e53b08c69fb85da1ec05e79263b33016412b7647ebdb7d14580d6ad2ba8057`
- freeze SHA256: `943a10a5da9ca4334366c2266df26e672bbc76eb30ebcf976e6fa8b1a8b6d73c`

Correction implementation commit:

`45e9f072ef9fb9f0851c2d5d0b341082c48db3ce`

## New combined offline bundle

- bundle ID: `bundle_20260924T163807Z_a5599568`
- bundle SHA256: `0c69039ab5ff04e420633796c06c4b344bc972bd135ecdb5fcb9116664317b66`
- approval code: `BM-0C69039AB5FF`
- entrypoint: `research/sc001/sc001_b15p1_adapter_combined_offline_validation_v0_1_1.py`
- files: 36
- total bytes: 423592
- runtime: `offline-research-v1`
- inputs: none

The bundle has been sealed and has NOT been run.

## Next

After explicit user approval, run exactly the sealed v0.1.1 bundle.

If and only if full status is:

`B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PASS`

then prepare the new safe-staging live source-capability wrapper for capability v0.2.1.

Do not reuse the old live wrapper.
