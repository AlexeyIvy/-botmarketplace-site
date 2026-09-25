# SC001 / B15-P1 — dialog handoff v6.39 — 2026-09-25

Current state:

`B15P1_COLLECTOR_V014_OFFLINE_PASS_CAPABILITY_REVALIDATION_NEXT`

## v0.1.4 PASS

Bundle:
`bundle_20260925T185135Z_6c28a359`

Job:
`job_20260925T191249Z_2ab861e9`

Result:
`B15P1_NONPRICE_COLLECTOR_V014_COMPILE_AND_SELFTEST_PASS`

All 32 mandatory tests passed.

New Bybit fixtures all PASS:
- withdrawMax=-1 -> UNLIMITED;
- other negative withdrawMax fail closed;
- negative non-max field fail closed;
- UNLIMITED -> finite max-withdraw transition preserved.

No credentials, exchange calls, collector launch, price/PnL or live execution occurred.

## v0.1.4 hashes

- runner: `280253b060f65517548054b3d8c33c315013d724ef2b836e9b8fef14628be213`
- library: `eaa925b71a7f33ec59de69f32dd0fb06f85bac67e89101b6f2ad50c1d792fd3f`
- freeze: `80928b0a11dac333b7844aa15bcdf399fd4db8739a4845e6118ebb576153b38c`
- service: `7a0f1742481b92f4d2590f09defcc5b287baaf1a9ba50f0da27488f8f5272f9d`

## Next

Prepare a new authenticated read-only source-capability revalidation bound to v0.1.4.

Do not reuse the v0.1.3 capability snapshot.

Do not retry collector launch until the v0.1.4-bound live capability gate passes.
