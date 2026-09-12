# SC001-DATA-A002-B01 — Frozen acquisition protocol v0.1

Status: PRE-EXECUTION / DATA-ONLY FREEZE

## Purpose
Acquire and integrity-qualify the first frozen DEV trade-level batch for SC001. This stage is not a strategy test. It must not compute features, signals, P&L, thresholds, execution assumptions, or any ranking of days.

## Authorized scope
Venue: Binance USD-M Futures. Symbol: BTCUSDT. Dataset: daily aggTrades. Split: DEV only. Batch: 2023-Q2.

Frozen dates and labels:
- 2023-04-12 — CPI
- 2023-04-23 — ordinary weekend
- 2023-05-01 — ordinary weekday
- 2023-05-05 — NFP
- 2023-06-14 — FOMC

The dates originate from frozen calendar SHA256 `e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b` and A002-PREFLIGHT PASS. No date may be added, removed, substituted or reordered because of market behavior.

## Frozen remote identities
The downloader must require that the live Binance checksum and Content-Length remain identical to A002-PREFLIGHT before downloading. Any mutation is REVIEW/STOP, not an automatic acceptance of the new object.

- 2023-04-12: 18,877,620 bytes; SHA256 `07be4bf404751ae8e14749f3c5e5abd31de05feecbf34f9d8f95e9e790ce5af2`
- 2023-04-23: 12,440,613 bytes; SHA256 `0164fa1cc3380992990c44763b898bd1ab42533bd218ca1575c8526b2ec79e72`
- 2023-05-01: 22,518,837 bytes; SHA256 `1978075ebf9b39fd4950d5fe4f72d08f650a6deabfd2cfc01c8fe763d0a7bf52`
- 2023-05-05: 21,579,218 bytes; SHA256 `5efcc4c5faaf44ba6f2bd8bd80d32f64ca350a785f64da2862a7e93a1348837e`
- 2023-06-14: 16,402,788 bytes; SHA256 `73628c85d9d60ffd5dd0d5aa2c40b625ecfca68d302591d813ab3a8b7be1cfaf`

Expected compressed total: 91,819,076 bytes.

## Safety
Hard caps are stricter than the prior global 2 GB phone constraint:
- session download <= 300,000,000 bytes;
- workspace <= 300,000,000 bytes;
- single archive <= 256,000,000 bytes;
- free-storage reserve >= 4,000,000,000 bytes;
- uncompressed ZIP member metadata <= 2,000,000,000 bytes.

ZIPs are retained for reproducibility. CSVs are streamed directly from ZIP and are not extracted to disk. Interrupted runs are restartable: a local archive may be reused only if size and SHA256 exactly match the frozen identity.

## Required integrity checks per day
1. live checksum equals frozen checksum;
2. live Content-Length equals frozen size;
3. downloaded bytes equal frozen size and SHA256;
4. ZIP CRC passes and archive contains exactly one expected CSV member;
5. CSV schema is exactly the seven aggTrades fields (header may be present or absent, but if present it must match the canonical order);
6. price and quantity parse as positive finite Decimal values, never float-based validation;
7. all rows belong to the target UTC day;
8. timestamps are monotonic nondecreasing; same-millisecond rows are permitted;
9. agg_trade_id is strictly contiguous inside the day;
10. underlying first_trade_id <= last_trade_id and successive ranges never overlap or run backwards;
11. all 1,440 UTC minute buckets contain at least one aggTrade;
12. both buyer-maker boolean states occur;
13. zero malformed rows.

Underlying raw-trade ID gaps, if any, are diagnostic only in B01; overlap/backward ranges are a failure. Cross-selected-day aggregate and underlying trade IDs must preserve chronological ordering, but gaps across nonconsecutive selected dates are expected.

## Why these gates
The batch is intended to establish that the retained trade stream is structurally usable for later sub-minute research. Contiguous aggregate IDs and complete minute coverage help distinguish a real archive from a truncated or internally missing export. Decimal parsing avoids precision artifacts. We deliberately do not compare P&L, signal quality, volatility or event response at this stage.

## Explicit non-claims
A PASS does not establish profitable scalping, spread, order-book depth, maker queue position, latency realism, exact taker slippage, or cross-venue synchrony. aggTrades are trade-level flow data, not L2.

## Forbidden actions
No VALIDATION/FINAL access. No Bybit/OKX substitution. No strategy feature construction. No event-window performance comparison. No side filtering. No parameter search. No P&L. No loosening a failed gate after looking at the data; any necessary implementation correction becomes a separately documented revision.

## Outputs
Workspace: `/storage/emulated/0/Download/SC001_DATA_A002_B01_2023Q2`

Small outputs to return for review:
- `sc001_data_a002_b01_report.json`
- `sc001_data_a002_b01_manifest.json`
- `sc001_data_a002_b01_summary.md`
- `sc001_data_a002_b01_final_safety.json`

Raw ZIP archives stay on the phone and should not be uploaded unless specifically requested.

## Advancement rule
Advance beyond B01 only if all five frozen days PASS every mandatory gate and cross-selected-day ID ordering has zero violations. A B01 PASS authorizes only the next frozen data-acquisition step; it does not authorize strategy/P&L work.