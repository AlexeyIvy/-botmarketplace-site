# SC001-DATA-Q007 — OKX Q1 L2 Preflight Results v0.1

Status: **PASS**

Stage: `SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT`
Scope: five frozen 2024-Q1 OKX `BTC-USDT-SWAP` L2 dates

## Result

All five exact-date 400-level L2 archives were discovered and passed HEAD identity/size checks. No archive body was downloaded and no strategy, midquote response, or P&L metric was calculated.

Exact compressed sizes:

- 2024-01-05 — 500,060,536 bytes
- 2024-01-14 — 426,641,072 bytes
- 2024-01-31 — 519,114,508 bytes
- 2024-02-12 — 601,976,188 bytes
- 2024-02-13 — 550,675,409 bytes

Total: **2,598,467,713 bytes**.

This total exceeds the frozen 2 GB per-run phone safety ceiling and therefore the five files must not be downloaded in one run.

## Methodological consequence

Q004R previously proved semantic replay only on bounded archive prefixes, not complete-day archive integrity. Therefore the next step is **not** immediate 5-day strategy/midquote evaluation.

Before bulk L2 acquisition, run one fixed full-day engineering pilot on the chronologically first frozen date, **2024-01-05**, independent of performance and without calculating E002 response metrics.

The pilot must establish:

- full archive download integrity;
- complete tar/gzip readability without extraction to disk;
- exact semantic schema across the whole member;
- deterministic full-day snapshot/update replay;
- timestamp boundary and UTC-day coverage;
- no malformed JSON/levels, wrong instrument, nonmonotonic timestamps, crossed/empty reconstructed books, or delete-missing-level anomalies;
- Android/Pydroid runtime feasibility.

Only after that pilot passes may remaining L2 dates be acquired in staged batches below the 2 GB ceiling.

## Safe batching after pilot

If the 2024-01-05 pilot passes, the remaining four exact-date files can be staged as:

- Batch B: 2024-01-14 + 2024-01-31 = 945,755,580 bytes;
- Batch C: 2024-02-12 + 2024-02-13 = 1,152,651,597 bytes.

Each remains below 2 GB, before small metadata overhead.

## Boundary

Q007 is metadata/HEAD qualification only. It does not establish full-day L2 integrity, executable prices, net profitability, maker fill probability, or a robust historical strategy candidate. Q2 OKX, formal Validation, and Final remain unopened.
