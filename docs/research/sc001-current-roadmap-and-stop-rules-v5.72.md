# SC001 Current Roadmap and Stop Rules v5.72

Date: 2026-09-24  
Status: **B15-P1 ADAPTER COMBINED OFFLINE VALIDATION v0.1.1 SEALED / AWAITING USER APPROVAL**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.71.md`

## Prior combined attempt

Bundle:
`bundle_20260924T154611Z_653834a4`

Job:
`job_20260924T162915Z_80dc0899`

Result:
`B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_REVIEW`

The collector v0.1.3 portion fully passed:
- compile+self-test PASS;
- 28/28 mandatory tests PASS;
- 8/8 extra tests PASS;
- exchange calls = false;
- collector launch = false;
- price/PnL = false.

The capability v0.2 portion stopped on a technical self-test false positive. Its global source scan searched for the literal `nextPageCursor` and matched the literal inside the guard itself.

The actual `bybit_live_usdt_spot_pairs()` request remained non-paginated:
- `category=spot`;
- no cursor;
- no `limit=1000`;
- no pagination loop.

## Capability v0.2.1 correction

The correction changes only the offline static guard.

The pagination guard now inspects the source of `bybit_live_usdt_spot_pairs()` specifically, while its forbidden markers are constructed outside the scanned function. This prevents self-reference while retaining fail-closed detection of reintroduced Spot pagination logic.

Frozen hashes:
- probe: `dacaacd8563ec80d7f9f3006cc846795aa7e5e017518a817c962ee1dc7c1f1fe`
- self-test harness: `25e53b08c69fb85da1ec05e79263b33016412b7647ebdb7d14580d6ad2ba8057`
- spec: `9811fe0c10b9b4178376b7ce244936e9d00027ab4d6d234b9c8581cca75a00ef`
- freeze: `943a10a5da9ca4334366c2266df26e672bbc76eb30ebcf976e6fa8b1a8b6d73c`

No adapter request behavior, collector behavior, research semantics, identity/route universe, 15-second cadence, Stage C 61/71 bps rules, or price/PnL firewall changed.

## Combined offline validation v0.1.1

Harness SHA256:
`a7d313e1e00925e87adf6a05bf58c656a746b2820c02931abc3a80b246deca86`

Spec SHA256:
`7d6d467261bdd7ab39b7529d68a36c101d2740c7ef563df7774b4e9590e27353`

Freeze SHA256:
`8223afb6deef1a08543a7745f91bfa7e3a7467a30c36d855205ed1322e3a02d2`

Sealed Runner bundle:
- bundle ID: `bundle_20260924T163807Z_a5599568`
- SHA256: `0c69039ab5ff04e420633796c06c4b344bc972bd135ecdb5fcb9116664317b66`
- approval code: `BM-0C69039AB5FF`
- files: 36
- total bytes: 423592
- runtime: `offline-research-v1`
- external inputs: none

## Safety boundary

This bundle is offline only:
- credentials = false;
- exchange calls = false;
- capability live snapshot = false;
- collector launch = false;
- price data = false;
- PnL = false;
- live execution = false.

Do not run without separate user approval.

Do not prepare or execute a live capability retry unless this combined gate returns full PASS.

## Next state

`RUN_B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_V011_AFTER_USER_APPROVAL`
