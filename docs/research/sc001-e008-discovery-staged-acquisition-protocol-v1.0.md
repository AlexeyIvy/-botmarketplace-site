# SC001-E008 — Discovery Staged Acquisition Protocol v1.0

Date: 2026-09-16  
Status: **FROZEN BEFORE FIRST PROMOTIONAL BODY DOWNLOAD**

Prerequisite: exact `E008_DISCOVERY_METADATA_PREFLIGHT_PASS` from `research/sc001/sc001_e008_discovery_metadata_preflight.py`.

## 1. Purpose

Acquire only the already-frozen E008 Discovery market-data bodies in bounded stages, while preserving exact metadata identities and preventing accidental date/source expansion.

This is data engineering only. It must not calculate hypothetical maker fills, spread capture, markouts, fees, inventory P&L or profitability.

## 2. Frozen Discovery dates

Exactly:

- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

No substitutions are allowed in this protocol.

Confirmation dates remain unopened.

## 3. Source identity

The authoritative source manifest for acquisition is the successful local report:

`~/sc001_data/SC001_E008_DISCOVERY_METADATA_PREFLIGHT/sc001_e008_discovery_metadata_preflight_report.json`

The acquisition implementation must:

- require exact status `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`;
- require the exact eight frozen Discovery dates;
- use only URL and Content-Length identities already recorded in that report;
- require HTTPS `static.okx.com` and exact expected filename;
- perform a fresh HEAD check of the same frozen URL before downloading;
- fail closed if final URL/host/filename/Content-Length differs;
- never rediscover or substitute another archive URL automatically.

If a frozen URL later becomes unavailable, acquisition stops and requires a separately documented metadata-refresh procedure; no silent source substitution.

## 4. Frozen stages

Trade stage:

- all unique exact/D+1 trade archives referenced by the eight Discovery rows;
- expected aggregate size is taken from the PASS report (about 76.6 MB at freeze time).

L2 stages:

- Batch A: 2024-01-06, 2024-01-13;
- Batch B: 2024-01-19, 2024-01-24;
- Batch C: 2024-02-06, 2024-02-11;
- Batch D: 2024-02-21, 2024-02-23.

Each batch must remain below 1.2 GB compressed according to the PASS report.

Expected L2 batch totals at freeze time:

- A: 820,010,542 bytes;
- B: 1,104,242,824 bytes;
- C: 859,021,338 bytes;
- D: 941,347,731 bytes.

Expected all-eight L2 total: 3,724,622,435 bytes.

## 5. Local layout

Data root defaults to `~/sc001_data` via `SC001_DATA_ROOT` override.

Workspace:

`SC001_E008_DISCOVERY_DATA/`

Subdirectories:

- `trades/`
- `l2/<date>/`
- `reports/`

Partial downloads use `.part` files and may resume. Completed exact-size files are reused only after local integrity checks.

## 6. Download/integrity rules

For every file:

1. minimum free-space reserve before and after the planned stage: 10 GB;
2. same frozen URL HEAD must still return expected exact Content-Length;
3. resumable GET is allowed;
4. final compressed byte count must equal frozen expected bytes exactly;
5. calculate and record local SHA256 after completion;
6. trade ZIP: CRC check, exactly one regular CSV member, expected basic header;
7. L2 tar.gz: compressed stream/tar readability and exactly one regular member; no profitability semantics are parsed;
8. preserve a per-stage JSON report atomically.

Local SHA256 becomes an immutable identity for later E008 integrity/replay stages.

## 7. Stage tokens

Successful stages print:

- `E008_DISCOVERY_TRADES_ACQUISITION_PASS`
- `E008_DISCOVERY_L2_A_ACQUISITION_PASS`
- `E008_DISCOVERY_L2_B_ACQUISITION_PASS`
- `E008_DISCOVERY_L2_C_ACQUISITION_PASS`
- `E008_DISCOVERY_L2_D_ACQUISITION_PASS`
- `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`

Any mismatch/error is fail closed and must not be bypassed.

## 8. Firewall

This stage must explicitly record false for:

- fill simulation;
- spread capture;
- markout;
- maker/taker fee application;
- inventory P&L;
- profitability;
- TFI use;
- Q2 access;
- Validation/Final access;
- Confirmation-body access.

## 9. Stop rule

Do not run E008 Discovery merely because all bodies download successfully.

After all acquisition stages pass, a separate full semantic replay/integrity qualification must PASS on all eight Discovery L2/trade days before the frozen maker engine may be run.
