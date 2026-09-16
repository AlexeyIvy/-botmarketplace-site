# SC001 — Historical Universe Seeded Enumeration Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN METADATA-ONLY ENUMERATION FALLBACK**

## 1. Purpose

The first blank-family OKX metadata probe returned `SC001_HISTORICAL_UNIVERSE_METADATA_PROBE_REVIEW` with zero enumerated instruments. That result is preserved and means the blank/wildcard-style request is not a valid historical-universe enumeration method.

This protocol defines a historically defensible fallback without using today's live top-coins list.

## 2. Historical seed

Use only the frozen pre-period seed:

`docs/research/sc001-historical-universe-seed-2023-12-30-v0.1.json`

The seed is derived from the public CoinMarketCap historical snapshot dated 2023-12-30 and is used only as a broad candidate list. It is not the final universe and does not determine strategy performance.

Stablecoins are excluded from the seed. No symbol is accepted merely because it appears in the external ranking.

## 3. OKX historical eligibility evidence

For every seeded base symbol `X`, probe the exact OKX linear family:

`X-USDT`

and require official historical metadata evidence for the exact instrument archive:

`X-USDT-SWAP-trades-YYYY-MM-DD.zip`

Probe anchor dates:

- 2023-12-30;
- 2024-02-29.

The first anchor establishes pre-period existence. The second establishes persistence through the end of the pre-March calibration period.

For each exact archive require:

- metadata success;
- exact filename match;
- trusted `static.okx.com` URL;
- successful HEAD;
- positive Content-Length.

Do not open/download the archive body in this stage.

## 4. Control instruments

`BTC-USDT-SWAP` and `ETH-USDT-SWAP` are controls.

If either control cannot be resolved on both anchor dates, terminal status is REVIEW and no candidate-pool inference is allowed.

## 5. Candidate pool classification

For each seed symbol classify:

- `BOTH_ANCHORS_PASS` — exact archive verified on both dates;
- `EARLY_ONLY` — early anchor verified but late anchor did not;
- `LATE_ONLY` — late anchor verified but early anchor did not;
- `NO_EXACT_ARCHIVE` — neither verified;
- `ERROR` — transport/identity ambiguity.

Only `BOTH_ANCHORS_PASS` instruments enter the provisional OKX candidate pool for the next pre-period liquidity calibration stage.

This still does not freeze the final 8-12 instruments.

## 6. PASS gate

Exact token:

`SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS`

requires:

- both BTC and ETH controls `BOTH_ANCHORS_PASS`;
- at least 16 non-stable `BOTH_ANCHORS_PASS` instruments, providing enough breadth to later choose 8-12 without performance selection;
- no market-data body download;
- no strategy signal/PnL calculation;
- promotional universe remains unfrozen.

If fewer than 16 pass, return:

`SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_REVIEW`

and broaden the historical seed prospectively before any final universe selection.

## 7. Next stage after PASS

Freeze a small pre-period calibration window and download only trade archives for the provisional pool to measure exchange-specific historical activity using non-promotional data, including:

- trade count;
- USD-equivalent turnover using transaction prices and historical contract specification where required;
- archive/data continuity;
- active-day coverage.

Then apply prospectively frozen eligibility/stratification rules and freeze the final 8-12 instrument universe.

No L2 acquisition is authorized by this protocol.
