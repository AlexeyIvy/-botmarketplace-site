# SC001 Current Roadmap and Stop Rules v5.188

Date: 2026-09-28
Status: **B15-P2 ARTICLE-STRUCTURE PROBE HOST-LAUNCHER FIXED / APPROVAL REMAINS VALID**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.187.md`

## Failed host launch

The approved article-structure probe self-test passed, but the transient service failed before Python execution:

- unit: `sc001-b15p2-article-structure-probe-v01.service`
- result: `exit-code`
- ExecMainStatus: `226/NAMESPACE`
- error:
  `ReadWritePaths target .../SC001_B15P2_ANNOUNCEMENT_STRUCTURE_PROBE: No such file or directory`

systemd also warned that `RuntimeMaxSec` is ineffective with the explicitly selected `Type=oneshot`.

Canonical diagnostic:

`docs/research/sc001-b15p2-article-structure-probe-systemd-namespace-failure-diagnostic-v0.1.json`

No live probe process started and no probe network call occurred.

## Corrected host wrapper

`scripts/research/run-b15p2-announcement-article-structure-probe-v0.1.sh`

Wrapper SHA256:

`3439f583b0f9d485252193b8af7f4a0117bfdc02ba5cfdb60a19bf831cdeaeb0`

The probe itself remains byte-identical:

`73c14a0963a245ad9ee431f6e76d16deed99d698fddeb32f78ca4c1fb685fa81`

The corrected wrapper:

- verifies exact probe SHA;
- reruns the no-network self-test;
- creates the output directory before systemd namespace setup;
- uses `Type=exec`;
- retains `RuntimeMaxSec=180`;
- uses a unique transient unit name;
- persists a launch marker;
- exposes `--status` with journal + compact structural result summary.

The existing user approval `BM-73C14A0963A2` remains valid because:
- probe bytes are unchanged;
- exact network scope is unchanged;
- only the failed host launcher is corrected.

## Firewalls

Still closed:
- semantic classification;
- price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- trading.

## Next state

`RERUN_APPROVED_ARTICLE_STRUCTURE_PROBE_VIA_CORRECTED_HOST_WRAPPER`
