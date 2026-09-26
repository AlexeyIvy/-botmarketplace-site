# SC001 Current Roadmap and Stop Rules v5.92

Date: 2026-09-26  
Status: **B15-P1 v0.1.4-BOUND CAPABILITY v0.2.2 STACK OFFLINE PREFLIGHT SEALED / AWAITING APPROVAL**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.91.md`

## Completed

- collector v0.1.4 offline compile+self-test PASS;
- all 32/32 mandatory tests PASS;
- Bybit `withdrawMax=-1` normalized only as `UNLIMITED`;
- all other unsupported negative values remain fail-closed;
- frozen cadence/route logic/price-PnL firewall unchanged.

## New capability gate

Capability v0.2.2 is bound exactly to:
- collector v0.1.4 runner SHA;
- collector v0.1.4 library SHA;
- v0.1.4 implementation freeze;
- v0.1.4 service candidate;
- frozen route graph;
- 192-asset admitted universe;
- collector v0.1.4 32/32 offline PASS result;
- prior source-invalid diagnostic.

It additionally executes the actual collector v0.1.4 Bybit parser against the live Get Coin Info response and requires:
- parser compatibility = true;
- `withdrawMax=-1` raw-row count equals normalized `UNLIMITED` row count.

The old v0.2.1 capability snapshot is explicitly not reusable.

## Live wrapper v0.3

Wrapper SHA256:

`3e8f453f54951f8bb125fda533214b05f949fa5d2500eaa20d9881f5e8e4e928`

Before its only live read-only boundary, the wrapper:
1. validates all 15 exact staging dependency SHA values;
2. re-checks collector v0.1.4 offline PASS;
3. re-runs capability v0.2.2 self-test from staged bytes;
4. only then permits authenticated read-only/non-price capability calls.

No collector start/systemd mutation/runtime authorization path is present.

## Sealed combined offline preflight

- bundle ID: `bundle_20260926T084231Z_2c0e59c2`
- SHA256: `37b560ba6f9ce85ad67c79ca47d7ba1d8b66aaa9eeb7a8196d697310d87f9fca`
- approval code: `BM-37B560BA6F9C`
- files: 20
- bytes: 274111
- runtime: `offline-research-v1`
- inputs: none

The bundle has NOT been run.

## Stop rule

Do not run live capability v0.2.2 on the VPS until this combined offline gate returns full PASS.

Do not retry collector launch yet.

## Next state

`RUN_V014_CAPABILITY_V022_STACK_OFFLINE_PREFLIGHT_AFTER_USER_APPROVAL`
