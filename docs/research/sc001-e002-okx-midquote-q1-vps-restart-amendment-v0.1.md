# SC001-E002 OKX Q1 Midquote Confirmation — VPS Restart Amendment v0.1

Date: 2026-09-14  
Status: **INFRASTRUCTURE-ONLY RESTART AUTHORIZED AFTER PHONE PROCESS LOSS**

## 1. Reason for this amendment

The previously launched Android/Termux four-day frozen confirmation did not produce a final report, final safety file, or error file, and no live confirmation process remained when checked on 2026-09-14.

No terminal verdict (`PASS`, `WEAK`, or `FAIL`) was available. Partial checkpoint alpha was not inspected or interpreted.

The phone run is therefore classified as a **technical interruption / incomplete computation**, not as a statistical result.

## 2. VPS qualification prerequisite

The new Timeweb Frankfurt VPS completed the required infrastructure qualification before this restart decision:

- environment audit: PASS;
- base tools: PASS;
- non-root `botmarket` access and SSH key hardening: PASS;
- repository access/clone: PASS;
- GitHub / OKX / Binance outbound network checks: PASS;
- Q008 2024-01-05 parity: PASS.

Q008 parity reproduced the exact frozen archive identity and replay output:

- bytes: `500060536`;
- SHA256: `7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`;
- records: `7568405`;
- snapshots: `1441`;
- updates: `7566964`;
- first UTC: `2024-01-05T00:00:00.005Z`;
- last UTC: `2024-01-05T23:59:59.990Z`;
- minute buckets: `1440/1440`;
- crossed states: `0`;
- empty states: `0`;
- delete-missing-level: `0`.

Reference: `docs/research/sc001-vps-qualification-and-q008-parity-results-v0.1.md`.

## 3. Statistical and financial freeze remains unchanged

This amendment changes **only the compute environment**. It does not change:

- the four frozen Q1 dates;
- event/ordinary labels;
- 5-second grid;
- 5-second lookback;
- 5-second horizon;
- 100 / 250 / 500 ms latencies;
- causal L2 midquote response semantics;
- expected decision counts;
- daily/statistical gates;
- PASS / WEAK / FAIL logic;
- Q2 firewall;
- Validation / Final firewall;
- no-P&L boundary.

The authoritative frozen confirmation engine remains:

`research/sc001/sc001_e002_okx_midquote_q1_confirmation.py`

at commit:

`38d3ab050ff64555b0149c31c52e1ab1775ae579`

with protocol commit:

`c6f9f01f7aed9a84786c6bb791ab88707dd1a5d7`.

## 4. VPS adaptation method

A thin VPS launcher is added:

`research/sc001/sc001_e002_okx_midquote_q1_confirmation_vps_launcher.py`

The launcher:

- reads the exact frozen engine bytes from the pinned Git commit;
- verifies frozen identity tokens and protocol commit;
- remaps only Android filesystem paths to a VPS data root;
- preserves the engine's own parent-report checks, source SHA checks, replay logic, daily computations, final aggregation and verdict logic;
- refuses to overwrite an already existing final VPS report;
- preserves the frozen 4 GB free-space reserve;
- does not import or inspect phone checkpoints/results;
- does not open Q2, Validation or Final;
- does not calculate strategy P&L.

## 5. Compute optimization decision

For this restarted four-day confirmation, the frozen engine remains **sequential**.

Reason: the engine intentionally mutates a pinned pilot-engine namespace per day. Thread-level parallelization would be unsafe, while process-level parallelization would introduce a second implementation change at the same time as the environment migration.

Given that Q008 full-day replay completed on the qualified VPS in about 438 seconds, the expected wall-clock cost of a sequential four-day confirmation is acceptable. Robustness and exact reproducibility take priority over shaving minutes from this one-off gate.

Parallel processing of independent frozen days remains an approved optimization for later newly frozen heavy-compute stages, after their own implementation freeze.

## 6. Phone-state rule

Do not inspect or reuse any phone partial checkpoint alpha for decision-making.

The VPS restart is a clean four-day recomputation under the exact frozen statistical rules. The phone run remains recorded only as an interrupted technical attempt with no verdict.

## 7. Data staging rule

Before launching confirmation on VPS:

- stage the required Q006R, Q009A and Q009B PASS parent reports;
- stage/reacquire the exact required Q1 trade and L2 archives;
- verify L2 size and SHA256 against the already-qualified parent reports;
- do not acquire Q2, Validation or Final data;
- do not run confirmation until all four frozen days pass source preflight.

Large market data should be acquired directly by the VPS where possible. The Android phone should not be used for heavy recomputation merely to support this restart.

## 8. Decision after the VPS final report

- `MIDQUOTE_CONFIRMATION_PASS` → freeze executable taker economics before any P&L.
- `MIDQUOTE_CONFIRMATION_WEAK` → retain as weak evidence; do not silently promote.
- `MIDQUOTE_CONFIRMATION_FAIL` → stop/downgrade E002; no rescue tuning.
