# SC001 / B15-P1 — dialog handoff v6.42 — 2026-09-26

Current state:

`B15P1_V011_SOURCE_INVALID_RECOVERY_OFFLINE_PASS_VPS_RECOVERY_NEXT`

Latest offline recovery preflight:
- bundle: `bundle_20260926T092023Z_1873afa0`
- job: `job_20260926T094525Z_7cd54910`
- status: `B15P1_V011_SOURCE_INVALID_RECOVERY_WRAPPER_OFFLINE_PREFLIGHT_PASS`
- manifest SHA: `d249b8376510d629ec3d14cd01be043f5c7f3ff6d595e7d45b044666f80a8e63`

Next user-visible action:
`sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-v011-source-invalid-recovery-before-v014-v0.1.sh`

This recovery archives old v0.1.1 collector evidence while preserving the new v0.2.2 capability snapshot SHA:

`fc1b4537290451241596e67342a9ab8fa6acd827afd4aeb70b70cee1e24e8e47`

No collector start or exchange calls occur in recovery.
