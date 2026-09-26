# SC001 Current Roadmap and Stop Rules v5.95

Date: 2026-09-26  
Status: **B15-P1 rolling-snapshot-safe recovery v0.1.1 offline preflight sealed / awaiting approval**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.94.md`

## Important operator event

A capability v0.2.2 command was run again instead of the recovery command.

The revalidation itself passed again and produced a new current snapshot SHA because the snapshot contains run-specific metadata.

This is safe, but it invalidated the old recovery v0.1 hardcoded snapshot SHA gate.

## Engineering correction

Old recovery v0.1 remains frozen and reproducible.

New recovery v0.1.1:

`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.1.sh`

SHA256:

`2a14da8e599feb0f2e075144bd64b269de44c916715790152e71ae5cc67eb2a7`

v0.1.1 no longer hardcodes a live snapshot SHA.

Before recovery it validates the current snapshot semantically:
- schema = v0.2.2;
- capability PASS status;
- exact collector v0.1.4 runner/library/freeze/service anchors;
- exact route graph and admitted universe anchors;
- Bybit/OKX permissions;
- 192/192/192 coverage;
- parser v0.1.4 compatibility;
- withdrawMax=-1 semantics = UNLIMITED;
- raw minus-one count equals normalized UNLIMITED count;
- security firewall;
- price/PnL/launch/live-execution closed;
- safe-summary points to the exact current snapshot SHA;
- v0.2.2 run log contains PASS/firewall tokens.

It records the current snapshot SHA before recovery and requires the same SHA after recovery.

Thus any current valid v0.2.2 snapshot is accepted, while stale/corrupt/mismatched snapshots remain fail-closed.

## Offline preflight hardening

The v0.1.1 offline preflight includes dynamic fixtures using two different synthetic snapshot SHA values.

Both must pass semantic validation.

A mismatched safe-summary snapshot SHA must fail closed.

Bootstrap compile gate is also included.

## Sealed bundle

- bundle ID: `bundle_20260926T101521Z_09b874f8`
- SHA256: `c6aed1d393ed470a18c674e45ae9ad5b36ad612cde5a140d99f475fe80bebe72`
- approval code: `BM-C6AED1D393ED`
- files: 5
- bytes: 35110
- runtime: offline-research-v1
- inputs: none

The bundle has NOT been run.

## Stop rule

Do not run old recovery v0.1.

Do not manually relaunch capability again before recovery unless needed for a separate reason.

Do not relaunch collector.

## Next state

`RUN_RECOVERY_V011_OFFLINE_PREFLIGHT_AFTER_EXPLICIT_APPROVAL`
