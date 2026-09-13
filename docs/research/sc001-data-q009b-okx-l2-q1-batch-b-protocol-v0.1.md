# SC001-DATA-Q009B — OKX Q1 L2 Batch B Protocol v0.1

Status: **FROZEN BEFORE BATCH-B DOWNLOAD**  
Parent data preflight: `SC001-DATA-Q007-OKX-L2-Q1-PREFLIGHT`  
Full-day pilot prerequisite: `SC001-DATA-Q008 = FULL_DAY_PASS`  
Prior batch prerequisite: `SC001-DATA-Q009A = PASS`

## Purpose

Acquire and full-day replay-qualify the final two unopened L2 days required by the already frozen four-day OKX midquote confirmation.

Data engineering only. No TFI, no midquote-response alpha, no P&L.

## Frozen dates

- `2024-02-12` — expected compressed bytes `601,976,188`;
- `2024-02-13` — expected compressed bytes `550,675,409`.

Expected batch total: `1,152,651,597` bytes.

No substitution based on speed, size, replay behavior or market performance.

## Safety

- session network cap: `1,350,000,000` bytes;
- batch workspace cap: `1,350,000,000` bytes;
- per-file cap: `650,000,000` bytes;
- minimum free-storage reserve: `4,000,000,000` bytes;
- absolute project rule remains <2 GB downloaded per run.

Downloads must be resumable via `.part` where supported. Completed exact-size final files must be reused rather than re-downloaded.

## Full-day replay gates per file

Use the same semantic replay integrity family already frozen in Q008 and used in Q009A:
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

Every file is evaluated independently. Batch PASS requires both days `FULL_DAY_PASS`.

## Sequential-testing firewall

Q009B is data-only. It must not calculate or expose:
- TFI scores;
- future midquote responses;
- extreme-decile results;
- signal ranking;
- strategy P&L;
- execution profitability.

The already frozen four-day midquote confirmation may be calculated only after both Q009A and Q009B are PASS.

## Holdout boundary

The batch must record:
- strategy_features_calculated = false;
- midquote_response_calculated = false;
- strategy_pnl_calculated = false;
- execution_profitability_calculated = false;
- q2_okx_accessed = false;
- validation_or_final_accessed = false.

2024-Q2 OKX, formal Validation and Final remain unopened.
