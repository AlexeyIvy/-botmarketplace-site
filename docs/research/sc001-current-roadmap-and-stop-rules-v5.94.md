# SC001 Current Roadmap and Stop Rules v5.94

Date: 2026-09-26  
Status: **B15-P1 v0.1.1 SOURCE-INVALID RECOVERY OFFLINE PREFLIGHT PASS / VPS RECOVERY NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.93.md`

## Latest PASS

Bundle:
`bundle_20260926T092023Z_1873afa0`

Job:
`job_20260926T094525Z_7cd54910`

Result:
`B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_PASS`

Package integrity = true.  
Exit code = 0.

Manifest SHA256:
`d249b8376510d629ec3d14cd01be043f5c7f3ff6d595e7d45b044666f80a8e63`

## Recovery wrapper

`scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.sh`

SHA256:
`466782f5c00d878ea37aa4eff7c29ae7b064015f689c27947a7977e1d1c79ce3`

Verified offline:
- bash syntax PASS;
- embedded Python compile PASS;
- systemctl only stop/disable/is-active/is-enabled/daemon-reload;
- no start/enable/restart;
- no collector run;
- no exchange calls;
- v0.2.2 snapshot is protected from move/delete;
- safe summary and v0.2.2 run log are protected;
- collector evidence is archived before v0.1.4 launch preparation.

## Protected capability baseline

Live capability v0.2.2 PASS is bound to snapshot SHA:

`fc1b4537290451241596e67342a9ab8fa6acd827afd4aeb70b70cee1e24e8e47`

This snapshot must remain unchanged through recovery.

## Next state

`RUN_SOURCE_INVALID_RECOVERY_ON_VPS`

Collector launch remains blocked until recovery PASS and subsequent v0.1.4 controlled launch gate preparation.
