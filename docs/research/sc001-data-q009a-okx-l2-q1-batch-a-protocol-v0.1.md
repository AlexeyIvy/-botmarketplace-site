# SC001-DATA-Q009A — OKX Q1 L2 Batch A Protocol v0.1

Status: **FROZEN BEFORE BATCH-A DOWNLOAD**  
Parent data preflight: `SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT`  
Full-day pilot prerequisite: `SC001-DATA-Q008 = FULL_DAY_PASS`

## Purpose

Acquire and full-day replay-qualify the first two unopened L2 days required by the frozen four-day OKX midquote confirmation.

Data engineering only. No TFI, no midquote-response alpha, no P&L.

## Frozen dates

- `2024-01-14` — expected compressed bytes `426,641,072`;
- `2024-01-31` — expected compressed bytes `519,114,508`.

Expected batch total: `945,755,580` bytes.

No substitution based on speed, size, replay behavior or market performance.

## Safety

- session network cap: `1,200,000,000` bytes;
- batch workspace cap: `1,200,000,000` bytes;
- per-file cap: `650,000,000` bytes;
- minimum free-storage reserve: `4,000,000,000` bytes;
- absolute project rule remains <2 GB downloaded per run.

Downloads must be resumable via `.part` where supported. Completed exact-size final files must be reused rather than re-downloaded.

## Full-day replay gates per file

Use the same semantic replay integrity family already proven in Q008:
- one regular tar member;
- first action snapshot;
- snapshots and updates both present;
- zero invalid JSON lines;
- zero missing required keys;
- correct instrument only;
- valid actions only;
- timestamps monotonic nondecreasing;
- zero malformed levels;
- zero crossed-book states;
- zero empty-book states;
- zero zero-size/nonzero-orders anomalies;
- zero delete-missing-level events;
- exact UTC day boundary;
- all 1440 UTC minutes observed.

Every file is evaluated independently. Batch PASS requires both days FULL_DAY_PASS.

## Firewall

This batch must record:
- strategy_features_calculated = false;
- midquote_response_calculated = false;
- strategy_pnl_calculated = false;
- execution_profitability_calculated = false;
- q2_okx_accessed = false;
- validation_or_final_accessed = false.

Do not calculate or inspect the frozen four-day midquote confirmation until Q009A and Q009B both pass.
