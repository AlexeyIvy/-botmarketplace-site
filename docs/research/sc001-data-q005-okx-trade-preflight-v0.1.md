# SC001-DATA-Q005 — OKX Same-Venue Tick-Trade Preflight v0.1

Status: **FROZEN BEFORE NETWORK RUN**

Parent evidence:
- `SC001-E002 = PROMISING_SCREEN`
- `SC001-E002-CONFIRMATION = CONFIRMATION_PASS`
- `SC001-DATA-Q004R` already qualified replayable OKX BTC-USDT-SWAP price-level L2 semantics on engineering samples.

## 1. Purpose

Identify and qualify the credential-free OKX historical **tick-trade** download path for `BTC-USDT-SWAP` on a fixed 2024-Q1 same-venue development layer, without downloading archive bodies and without calculating E002 features/P&L.

The purpose is to establish the lightest same-venue evidence layer before expensive full-day L2 economics.

## 2. Why this precedes L2

E002/confirmation establish a stable Binance trade-flow predictive association but not OKX executable alpha. Full OKX L2 days are much larger than trade metadata/trade archives. Therefore same-venue trade-flow should be falsified cheaply before incurring L2 processing cost.

Official OKX historical-data documentation advertises tick-level trade history from September 2021 onward and high-resolution L2 from March 2023 onward. Q003/Q004R already established a working public website-backend route for historical-data archive discovery and trusted `static.okx.*` download URLs for L2.

## 3. Fixed same-venue Q1 layer

Only these five dates may be used in Q005 and the first OKX same-venue predictive replication:

- 2024-01-05 — NFP
- 2024-01-14 — ordinary weekend
- 2024-01-31 — FOMC
- 2024-02-12 — ordinary weekday
- 2024-02-13 — CPI

These dates were frozen before current OKX performance is known. 2024-Q2 OKX trade/L2 data remain unopened as a later same-venue confirmation layer.

## 4. Instrument

Venue: OKX  
Instrument type: `SWAP`  
Instrument family: `BTC-USDT`  
Target instrument: `BTC-USDT-SWAP`

For predictive TFI replication, trade size may be used in contract units because any constant contract-value multiplier cancels from the signed-notional ratio. This does **not** authorize capital sizing or P&L; historical contract metadata remains mandatory before execution economics.

## 5. Discovery endpoint and finite module identification

Use only the public historical-data website backend already qualified in Q003:

`POST /priapi/v5/broker/public/trade-data/download-link`

The exact tick-trade module code is treated as website-backend metadata rather than a documented public API contract. Therefore Q005 must not silently assume a module code.

On the first fixed date `2024-01-05`, probe exactly the finite module-code set:

`1, 2, 3, 4, 5`

using identical `SWAP / BTC-USDT / daily` date bounds.

A module may be accepted as the tick-trade module only if its returned trusted file metadata is unambiguous and the filename/path semantics identify trade history while not identifying order-book/L2, funding, candle/kline, or borrowing-rate data.

If exactly one module is unambiguously identified, reuse that module for the other four fixed dates. If zero or multiple modules remain plausible, status is `REDESIGN`; do not download archive bodies.

## 6. Trust boundary

Every returned archive URL must:
- use HTTPS;
- resolve to a host beginning with `static.okx.`;
- remain on a trusted `static.okx.*` host after HEAD redirects;
- have a positive Content-Length when available.

No private API key or account endpoint is permitted.

## 7. Hard safety

Preflight only:
- total network cap: **20,000,000 bytes**;
- workspace cap: **20,000,000 bytes**;
- per metadata response cap: **4,000,000 bytes**;
- minimum free-storage reserve: **4,000,000,000 bytes**;
- archive body download: **FORBIDDEN**;
- signal calculation: **FORBIDDEN**;
- strategy P&L: **FORBIDDEN**;
- formal Validation/Final access: **FORBIDDEN**.

HEAD requests may be used for size/content metadata. If HEAD is unsupported, the preflight must record that fact rather than falling back to a full GET.

## 8. PASS gates

`PASS` requires:
1. exactly one unambiguous tick-trade module identified from the fixed module set;
2. all five fixed dates return at least one trusted trade-history candidate consistent with `BTC-USDT-SWAP`/scoped family;
3. all five URLs pass trust validation;
4. all five remote sizes are known and positive, or are otherwise explicitly documented for a later bounded acquisition redesign;
5. no archive body is downloaded;
6. network/workspace/free-space limits remain intact.

If file identity is family-level rather than single-instrument, Q005 must report this explicitly. A later parser must then filter `BTC-USDT-SWAP` without assuming the archive is instrument-exclusive.

## 9. Output

Write:
- `sc001_data_q005_okx_trade_preflight_report.json`
- `sc001_data_q005_okx_trade_preflight_summary.md`
- `sc001_data_q005_okx_trade_preflight_final_safety.json`

## 10. Next gate

Only after Q005 PASS may SC001 freeze the bounded 2024-Q1 OKX tick-trade acquisition/parser and the unchanged same-venue E002 replication. No L2 full-day acquisition is authorized by Q005 alone.
