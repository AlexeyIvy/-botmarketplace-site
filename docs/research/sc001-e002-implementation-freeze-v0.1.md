# SC001-E002 Implementation Freeze v0.1

Status: **FROZEN BEFORE RUN**

Experiment: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`

Protocol commit: `4022da85f5ffb873d558ccda74d20b8c16272ba7`

Engine commit: `95ab41d5c6db58101ce19ebb56b459927c3a20e2`

Launcher commit: `81d3f9fefb44f469471f29d873273a5c1d1ccefc`

## Frozen implementation

The engine reads only the qualified B01/B02/B03 DEV-DISCOVERY archives already retained on the phone.

Before any feature calculation it verifies:
- source batch report PASS;
- source manifest PASS;
- no strategy P&L in acquisition stage;
- no Validation/Final access;
- frozen calendar SHA identity;
- exact source archive byte size;
- exact source archive SHA256.

The engine never references B04/B05, formal Validation, or Final paths.

Feature/label implementation:
- non-overlapping 5-second buckets;
- signed notional uses `price * quantity`;
- buyer-taker (`is_buyer_maker=false`) positive;
- seller-taker (`is_buyer_maker=true`) negative;
- TFI = signed notional / total notional;
- decision at bucket right edge;
- first transaction price at/after 100ms, 250ms, or 500ms observation latency;
- fixed 5-second future response;
- response in log-return basis points;
- no spread/depth/fee/fill model.

Primary day-level inference:
- daily Spearman;
- exact sign count across 15 days;
- quarter/event/ordinary robustness;
- extreme-decile spread diagnostics.

No parameter sweep is implemented.

## Output folder

`/storage/emulated/0/Download/SC001_E002_TFI_SCREEN`

Expected outputs:
- `sc001_e002_report.json`
- `sc001_e002_daily_metrics.csv`
- `sc001_e002_summary.md`
- `sc001_e002_final_safety.json`

## Boundary

A `PROMISING_SCREEN` result means only that the trade-flow feature family survives a frozen DEV-DISCOVERY predictive screen. It does not establish executable or net-profitable scalping.
