# SC001 / B15-P1 — dialog handoff v6.40 — 2026-09-26

Current state:

`B15P1_V014_CAPABILITY_V022_STACK_OFFLINE_PREFLIGHT_SEALED_AWAITING_APPROVAL`

## Current technical position

Collector v0.1.4 already has full 32/32 offline PASS.

New capability v0.2.2 and live-wrapper v0.3 are prepared and bound to v0.1.4 hashes.

Capability v0.2.2 will prove the actual v0.1.4 Bybit parser accepts the current live Get Coin Info response and maps each legal `withdrawMax=-1` row to `UNLIMITED`.

Old v0.2.1 snapshot reuse is forbidden.

## Sealed combined offline gate

- bundle ID: `bundle_20260926T084231Z_2c0e59c2`
- bundle SHA256: `37b560ba6f9ce85ad67c79ca47d7ba1d8b66aaa9eeb7a8196d697310d87f9fca`
- approval code: `BM-37B560BA6F9C`
- files: 20
- bytes: 274111
- entrypoint: stack bootstrap
- inputs: none

Not run yet.

## Next

Run this sealed offline stack preflight after explicit approval.

Only if full PASS, the next user-visible action will be one verified read-only VPS capability command. Collector launch remains later.
