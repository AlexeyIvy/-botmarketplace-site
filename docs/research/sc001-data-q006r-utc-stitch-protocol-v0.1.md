# SC001-DATA-Q006R — OKX Trade UTC-Stitch Repair Protocol v0.1

Status: **FROZEN BEFORE REPAIR RUN**  
Parent: `SC001-DATA-Q006-OKX-TRADES` = `SCHEMA_REVIEW`  
Purpose: repair only the objectively identified schema/time-boundary issues before any OKX E002 feature calculation.

## 1. Scope

Target venue/instrument: OKX `BTC-USDT-SWAP`.

Frozen target UTC dates remain unchanged:
- 2024-01-05 — NFP;
- 2024-01-14 — ordinary weekend;
- 2024-01-31 — FOMC;
- 2024-02-12 — ordinary weekday;
- 2024-02-13 — CPI.

Q006R is data engineering only. It may not calculate TFI, future returns, Spearman, thresholds, strategy P&L, or any formal Validation/Final metric.

2024-Q2 OKX remains unopened.

## 2. Objective reason for repair

Q006 observed the same six-column CSV schema on all five downloaded archives:

`instrument_name, trade_id, side, price, size, created_time`

The frozen Q006 alias map omitted `created_time` from timestamp aliases and `instrument_name` from instrument aliases, so row-level validation correctly stopped at `SCHEMA_REVIEW`.

Additionally, first sample `created_time` values in every exact-date archive were around 16:00 UTC on the previous calendar day. This is consistent with non-UTC daily packaging and with the earlier Q005 backend returning both `D` and `D+1` trade archives for a UTC-day metadata query.

The repair is therefore restricted to schema resolution and UTC-day reconstruction. No market-performance result motivates it.

## 3. Frozen schema mapping

Required exact logical mapping:
- instrument -> `instrument_name`;
- trade id -> `trade_id`;
- taker side -> `side`;
- price -> `price`;
- size -> `size`;
- timestamp -> `created_time`.

Allowed side values: `buy`, `sell` only.

Target instrument must equal `BTC-USDT-SWAP` on every admitted row.

`created_time` is interpreted as Unix epoch time using the same numeric scale resolver as Q006, with the observed 13-digit values expected to resolve to milliseconds.

## 4. UTC reconstruction rule

For each frozen target UTC date `D`, Q006R must use exactly two archive labels:

- `D`;
- `D+1`.

The already-downloaded `D` archive is reused from Q006 only after byte-size and SHA-256 verification against the Q006 manifest.

The `D+1` archive is rediscovered through the already-qualified OKX module `1` metadata path and must match the exact filename:

`BTC-USDT-SWAP-trades-<D+1>.zip`

Only rows with timestamps in:

`[D 00:00:00.000 UTC, D+1 00:00:00.000 UTC)`

are admitted to the reconstructed UTC day.

No row is admitted or rejected because of price, return, volatility, signal value, or apparent profitability.

## 5. Neighbor-download safety

Hard caps:
- session network cap: `100,000,000` bytes;
- Q006R workspace cap: `100,000,000` bytes;
- per-neighbor-file cap: `25,000,000` bytes;
- metadata response cap: `4,000,000` bytes;
- minimum free-space reserve: `4,000,000,000` bytes.

Existing Q006 archives are referenced in-place rather than duplicated into Q006R.

If a required neighbor archive is missing, ambiguous, untrusted, too large, or changes size between HEAD and GET, Q006R stops/reports `REVIEW` rather than substituting a different date.

## 6. Full-archive temporal diagnostics

For both source archives of each target UTC day, record:
- first parsed timestamp UTC;
- last parsed timestamp UTC;
- total valid source rows;
- invalid source rows;
- timestamp backwards count;
- instrument mismatch count;
- buy/sell counts;
- trade-ID duplicate/backwards count;
- exact SHA-256 and bytes.

These diagnostics must establish from complete files whether the observed 16:00 UTC boundary is real; Q006R must not simply assume it from the five-row Q006 samples.

## 7. Reconstructed UTC-day gates

For each target UTC day, `PASS` requires:
1. exact `D` archive identity verified;
2. exact `D+1` neighbor identity/download verified;
3. ZIP CRC pass on both archives;
4. exactly one expected CSV member per archive;
5. exact six-column schema resolvable as frozen above;
6. zero invalid admitted rows;
7. zero target-instrument mismatches among admitted rows;
8. admitted timestamps monotonic nondecreasing after `D` then `D+1` stitching;
9. all admitted rows lie inside the target UTC day by construction;
10. both `buy` and `sell` observed;
11. all `1,440` UTC minute buckets observed;
12. admitted trade IDs are monotonic increasing, with duplicate/backward count zero.

Trade-ID gaps, if any, are diagnostic unless an overlap/backward condition occurs. No global gap-free guarantee is assumed without evidence.

## 8. Aggregate PASS

Q006R overall `PASS` requires all five frozen UTC days PASS.

Any failed day yields `REVIEW`/`ERROR`; no replacement day is allowed.

## 9. Firewall

Q006R must record explicitly:
- `strategy_features_calculated = false`;
- `future_returns_calculated = false`;
- `strategy_pnl_calculated = false`;
- `q2_okx_accessed = false`;
- `validation_or_final_accessed = false`.

## 10. Promotion rule

Only after Q006R PASS may SC001 freeze and run the same-venue OKX replication of the already-fixed E002 feature:

5-second signed-notional aggressive trade-flow imbalance, continuation direction, 5-second response horizon, frozen latency scenarios, with no retuning on these Q1 dates before that replication protocol is frozen.
