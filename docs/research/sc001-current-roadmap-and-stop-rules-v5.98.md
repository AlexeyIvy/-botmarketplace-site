# SC001 Current Roadmap and Stop Rules v5.98

Date: 2026-09-26  
Status: **B15-P1 recovery v0.1.2 OFFLINE PASS / VPS RECOVERY NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.97.md`

## Latest PASS

Bundle:
`bundle_20260926T115009Z_9a599660`

Job:
`job_20260926T120049Z_1f2263c6`

Result:
`B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_V012_PASS`

Bootstrap:
`B15P1_V011_SOURCE_INVALID_RECOVERY_BOOTSTRAP_V012_PASS`

Package integrity = true.  
Exit code = 0.

Main manifest SHA256:
`54b5d35284f69099cfd15d02b5f606ad9622906ae47e606933567b4211d85e36`

Bootstrap manifest SHA256:
`fa2d5d69be100a3bb92444484cddb061b27158de5f253901d1f8895c3527da23`

## What v0.1.2 proved

- freeze-chain wrapper/harness/bootstrap/spec/diagnostic = PASS;
- valid semantic snapshot with generated SHA A = PASS;
- valid semantic snapshot with different generated SHA B = PASS;
- mismatched safe-summary snapshot SHA = fail closed;
- realistic live-probe tee log = PASS;
- missing probe PASS token = fail closed;
- Bash syntax = PASS;
- 2 embedded Python blocks compile;
- start/enable/restart absent;
- collector run absent;
- exchange calls absent.

## Recovery wrapper

Use only:

`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.2.sh`

SHA256:

`04d6f49a38882e94928ae7fef0b1068670dfb536361cd72c77659aefc17bac20`

Do not use v0.1 or v0.1.1.

## Next host action

Run the v0.1.2 recovery wrapper on VPS.

Expected terminal PASS:

`B15P1_V011_SOURCE_INVALID_RECOVERY_V012_PASS`

Only after recovery PASS may preparation of the controlled collector v0.1.4 launch gate continue.

## Next state

`RUN_V011_SOURCE_INVALID_RECOVERY_V012_ON_VPS`
