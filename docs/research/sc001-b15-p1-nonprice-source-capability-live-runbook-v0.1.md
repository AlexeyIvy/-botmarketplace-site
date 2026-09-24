# SC001 — B15-P1 Live Read-Only Source Capability Revalidation Runbook v0.1

Date: 2026-09-24  
Status: **OFFLINE SELF-TEST PASS / LIVE READ-ONLY RUN PENDING**

## Offline prerequisite

PASS tokens:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_SELF_TEST_PASS`

`B15P1_NONPRICE_SOURCE_CAPABILITY_COMPILE_AND_SELFTEST_PASS`

Offline self-test job:

`job_20260924T122232Z_8fd0930e`

Compile manifest SHA256:

`bc8253ab7d928622a13460a96b5d9aca0875840835ff877942df86482aba6ba0`

Self-test manifest SHA256:

`686e7151b4b858bcc3513468377b47b07e65fc440577b1e6551b3cbb47ba9f03`

## Live command

Run on the VPS:

```bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p1-nonprice-source-capability-revalidation-v0.1.sh
```

The wrapper:

- verifies exact probe/freeze SHA256;
- verifies the protected B15 env file has mode 0600;
- runs the probe as user `botmarket`;
- never prints credential values;
- performs only the frozen read-only/non-price endpoint set;
- writes a secret-free capability snapshot;
- checks the snapshot firewall again after the probe exits.

## Expected PASS

The live probe should print:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS`

and the wrapper should finish with:

`B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_PASS`

Also retain the printed:

- `snapshot_sha256`;
- qualified Bybit pair count;
- qualified OKX pair count;
- qualified both-venue asset count.

## Output files

- `/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/source_capability_snapshot.json`
- `/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/source_capability_safe_summary.json`
- `/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY/source_capability_revalidation_run.log`

The snapshot is secret-free but operationally important.

## What PASS does not do

The wrapper does not:

- install or start systemd service;
- create launch authorization;
- start the 15-second collector;
- request market prices;
- calculate PnL;
- place orders/transfers/withdrawals.

Collector launch remains a separate explicit gate.


## Permission correction — v0.1.1 wrapper

Observed live attempt:

- wrapper started correctly under sudo;
- probe itself did not start;
- Python returned `Permission denied` for the probe path inside
  `/var/lib/botmarket-github-control/repo`;
- no exchange call occurred.

Root cause:

The GitHub Control clone is intentionally isolated:

- owner/group: `botmarket-github:botmarket-github`;
- state directory mode: `0750`.

The live probe runs as `botmarket`, so direct execution/read from the isolated clone is intentionally denied.

Do **not** fix this with broad chmod/chown or by adding `botmarket` to the GitHub Control group.

Corrected wrapper behavior:

1. root verifies source probe/freeze SHA in the isolated clone;
2. root recreates a clean staging root under
   `/home/botmarket/.local/share/botmarket/b15p1-capability-revalidation-v0.1-stage`;
3. only the exact non-secret files required by the frozen probe are copied;
4. staged files are owned by `botmarket:botmarket` and mode 0640;
5. staged probe/freeze SHA are checked again;
6. readability as `botmarket` is checked before any exchange call;
7. probe runs as `botmarket` with `B15P1_REPO_ROOT` pointing to the staging root.

The GitHub Control clone permissions remain unchanged.
