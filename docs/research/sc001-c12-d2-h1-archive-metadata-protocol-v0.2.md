# SC001 — C12-D2 H1-2025 USDC-USDT Archive Metadata Batch v0.2

Date: 2026-09-18
Status: **FROZEN RATE-LIMIT-SAFE METADATA REPAIR / NO PEG OUTCOME**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-c12-d2-h1-archive-metadata-protocol-v0.1.md`

Parents:

- `docs/research/sc001-c12-d2-v0.1-rate-limit-review-v0.1.md`;
- `docs/research/sc001-c12-d1-spot-trade-semantics-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.16.json`.

## 1. Purpose

Complete the exact frozen C12 H1 metadata batch after v0.1 was interrupted by OKX HTTP 429 rate limiting.

This is an engineering/request-orchestration repair only.

No research chronology, archive identity, threshold or outcome rule changes.

## 2. Frozen target/source windows unchanged

Target UTC days:

`2025-01-01 through 2025-06-30`

Required source archives because D+D1 stitching is qualified:

`2025-01-01 through 2025-07-01`

inclusive.

Required unique archive count:

`182`

## 3. Exact source identity unchanged

For every source date:

`USDC-USDT-trades-YYYY-MM-DD.zip`

Require:

- qualified priapi SPOT `instIdList=[USDC-USDT]` resolver;
- unique exact trusted URL;
- HTTPS;
- host `static.okx.com`;
- HEAD success;
- positive Content-Length.

No body GET/open.

## 4. Rate-limit-safe request policy

The v0.2 runner must:

- issue requests sequentially;
- enforce a minimum delay between HTTP requests;
- detect HTTP 429 explicitly;
- honor integer `Retry-After` when present;
- otherwise use bounded exponential backoff;
- never reinterpret 429 as archive absence;
- stop as REVIEW only after the frozen retry budget is exhausted.

Frozen defaults:

- minimum inter-request spacing = `1.5 seconds`;
- maximum attempts for one HTTP operation = `8`;
- fallback 429 backoff schedule begins at `15 seconds` and doubles up to `240 seconds`.

## 5. Persistent checkpoint / resume

After every exact archive + HEAD success, atomically write a checkpoint containing:

- stage/version;
- fixed source window;
- verified date;
- exact filename;
- Content-Length.

On restart:

- accept only checkpoint rows with exact expected date/filename and positive Content-Length;
- resume from the first unverified date;
- never infer unverified dates from sequence position.

The checkpoint is engineering metadata only.

## 6. PASS semantics unchanged

Exact PASS:

`C12_D2_V02_H1_ARCHIVE_METADATA_PASS`

requires all 182 exact source archives verified.

REVIEW:

`C12_D2_V02_H1_ARCHIVE_METADATA_REVIEW`

is engineering/source state only.

## 7. Firewalls unchanged

Must remain false:

- historical_trade_body_downloaded;
- historical_trade_body_opened;
- peg_deviation_calculated;
- reversion_outcome_calculated;
- threshold_selected;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 8. No research interpretation of request failures

429, timeout or transient HTTP failure:

- is not a C12 mechanism verdict;
- may not alter the date window;
- may not drop individual dates;
- may not change the 182-file requirement.

## 9. Consequence of PASS

Only after exact v0.2 PASS may C12 freeze its first outcome-bearing parity headroom/reversion sentinel.
