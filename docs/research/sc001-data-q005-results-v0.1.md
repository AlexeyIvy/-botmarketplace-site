# SC001-DATA-Q005 — OKX Tick-Trade Preflight Results v0.1

Status: **REDESIGN (engineering identity bug, not data unavailability)**

## What happened

Q005 was intentionally fail-closed. It downloaded no archive bodies and calculated no strategy feature or P&L.

On the frozen probe date `2024-01-05`, OKX module `1` returned trusted `static.okx.com` links for BTC-USDT-SWAP daily trade archives, including:

- `BTC-USDT-SWAP-trades-2024-01-05.zip` (`7.18 MB` reported), and
- adjacent-day `BTC-USDT-SWAP-trades-2024-01-06.zip` (`3.32 MB` reported).

Module `2` returned candlesticks, module `4` returned L2 order book, and modules `3` and `5` returned no usable trade files.

The v0.1 selector treated both module-1 filenames as exact target-instrument matches but did not additionally require the requested **calendar date** in the filename. It therefore classified module `1` as `AMBIGUOUS_EXACT_TARGET`. Because no module then produced one canonical candidate under that selector, the run correctly ended `REDESIGN`.

## Interpretation

This is **not** evidence that OKX historical trades are unavailable. To the contrary, Q005 directly observed a trusted trade archive for the requested instrument and requested date.

The failure is an objective parser/identity-rule defect: instrument identity was enforced, but date identity was not.

This correction is data engineering only and does not use any market return, signal strength, P&L, volatility, spread, or strategy outcome.

## Safety / firewall

- archive bodies downloaded: NO
- network bytes read: 2,918
- strategy features: NO
- strategy P&L: NO
- formal Validation/Final: unopened

## Corrective action

Create `Q005R` as a versioned repair rather than overwriting Q005.

Q005R will:

1. freeze module `1` as the trade module based solely on Q005 metadata identity evidence;
2. query only the five already-frozen 2024-Q1 dates;
3. accept exactly one filename equal to `BTC-USDT-SWAP-trades-YYYY-MM-DD.zip` for the requested date;
4. ignore adjacent-day files returned by the backend;
5. HEAD the exact-date URL and record size/host identity;
6. still download no archive bodies and calculate no strategy feature/P&L.

If any requested date lacks exactly one exact-date trusted trade archive, Q005R returns REVIEW/REDESIGN rather than substituting another date.
