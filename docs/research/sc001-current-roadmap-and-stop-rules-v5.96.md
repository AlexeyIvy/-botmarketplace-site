# SC001 Current Roadmap and Stop Rules v5.96

Date: 2026-09-26  
Status: **B15-P1 rolling-snapshot-safe recovery v0.1.1 OFFLINE PASS / VPS RECOVERY NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.95.md`

## Latest offline result

Bundle:

`bundle_20260926T101521Z_09b874f8`

Job:

`job_20260926T113445Z_a1d1038b`

Result:

`B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_V011_PASS`

Bootstrap result:

`B15P1_V011_SOURCE_INVALID_RECOVERY_BOOTSTRAP_V011_PASS`

Package integrity = true.  
Exit code = 0.

Main manifest SHA256:

`a0263abf09242bc0b3b33c560f837cdc5b61ee666223ca3c651722ed33350865`

Bootstrap manifest SHA256:

`7d3d1b1c19a781fba6977eb4c11e73d19070e88403547c52dfbc9866d8aa723a`

## What was proven

Recovery v0.1.1 no longer depends on one pre-known live capability snapshot SHA.

It validates the current v0.2.2 snapshot semantically and then requires pre/post SHA identity.

Dynamic offline fixtures proved:
- one valid v0.2.2 snapshot with one generated SHA passes;
- a second valid v0.2.2 snapshot with a different generated SHA also passes;
- a mismatched safe-summary snapshot SHA fails closed.

The recovery wrapper also passed:
- Bash syntax;
- 2 embedded Python blocks compile;
- systemctl restricted to stop/disable/is-active/is-enabled/daemon-reload;
- no start/enable/restart;
- no collector run;
- no exchange calls;
- no snapshot/safe-summary/capability-log move or delete.

## Recovery wrapper

Use only:

`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.1.sh`

SHA256:

`2a14da8e599feb0f2e075144bd64b269de44c916715790152e71ae5cc67eb2a7`

Do NOT use recovery v0.1.

## Next host action

Run the v0.1.1 recovery wrapper on VPS.

It will:
- validate the current live v0.2.2 capability snapshot by content;
- record its actual SHA;
- archive old v0.1.1 collector evidence;
- preserve current capability snapshot/safe-summary/run-log;
- require unchanged snapshot SHA after archive;
- leave service inactive/not-found and active collector state/manifest absent.

## Stop rule

Do not relaunch collector until recovery v0.1.1 returns PASS.

## Next state

`RUN_V011_SOURCE_INVALID_RECOVERY_V011_ON_VPS`
