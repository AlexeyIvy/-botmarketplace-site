# SC001 Current Roadmap and Stop Rules v5.99

Date: 2026-09-26  
Status: **B15-P1 v0.1.1 source-invalid evidence recovery PASS / controlled collector v0.1.4 launch gate preparation**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.98.md`

## Recovery host PASS

Wrapper:
`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.2.sh`

Result:
`B15P1_V011_SOURCE_INVALID_RECOVERY_V012_PASS`

Recovery report SHA256:
`553a89d82dba67ee80166ccff32841b51ecbc25a9d8b47f5d84f6f6dd769e89b`

Archived collector evidence files:
`134`

Archive:
`/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/launch_attempts/20260926T120327Z_final_launch_v0.1.1_source_invalid_failed`

## Preserved capability baseline

Current live v0.2.2 snapshot SHA256:

`01cfa63b6001ec972c4ed87daba5bbd9fba932233b9e8323a49a6a5355e89647`

The snapshot semantic contract passed before recovery and the same SHA remained after recovery.

Bybit adapter evidence:
- withdrawMax=-1 rows = 1007;
- normalized UNLIMITED rows = 1007.

## Clean active baseline after recovery

- service active = inactive;
- service enabled = not-found;
- runtime unit = absent;
- runtime authorization = absent;
- active collector state = absent;
- active collector manifest = absent;
- collector start authorization = false;
- price/PnL authorization = false.

## Next

Prepare a new controlled launch gate for collector v0.1.4.

The new gate must NOT reuse the old v0.1.3 launch authorization or the old final launch wrapper unchanged.

It must bind exactly to:
- collector v0.1.4 runner/library/freeze/service hashes;
- current valid capability snapshot v0.2.2 semantic contract;
- recovery v0.1.2 host result and recovery report;
- frozen route graph;
- 192 admitted assets;
- price/PnL closed.

## Stop rule

Do not manually start collector.

Do not use final launch v0.1 or v0.1.1 for v0.1.4.

## Next state

`PREPARE_CONTROLLED_COLLECTOR_V014_LAUNCH_GATE`
