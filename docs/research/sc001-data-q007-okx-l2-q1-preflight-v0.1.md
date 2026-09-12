# SC001-DATA-Q007 — OKX Q1 L2 Size/Identity Preflight v0.1

Status: **FROZEN BEFORE L2 BODY DOWNLOAD**  
Purpose: prepare the minimum L2 acquisition needed to falsify the transaction-price replication with a midquote-based screen.

## Scope

Venue: OKX  
Instrument: `BTC-USDT-SWAP`  
Historical module: `4`  
Archive family: `L2orderbook-400lv`

Frozen target dates:

- 2024-01-05
- 2024-01-14
- 2024-01-31
- 2024-02-12
- 2024-02-13

These are exactly the five already-open Q1 same-venue replication days. No Q2, formal Validation, or Final dates may be queried.

## Exact identity rule

For target date `D`, accept exactly one trusted archive whose filename equals:

`BTC-USDT-SWAP-L2orderbook-400lv-D.tar.gz`

Returned neighboring dates or other archive families are ignored. Multiple exact matches or no exact match cause `REVIEW`.

## What Q007 may do

- call the already-qualified OKX historical-data website backend for module `4`;
- inspect metadata only;
- issue HEAD for the exact selected archive;
- record reported size and `Content-Length`;
- verify HTTPS `static.okx.*` identity;
- calculate safe staged acquisition batches.

## What Q007 must not do

- download any L2 archive body;
- calculate TFI, midpoint response, P&L, spread cost, or strategy features;
- inspect OKX Q2;
- access formal Validation or Final.

## Safety

- network cap: 20 MB;
- workspace cap: 20 MB;
- per-response cap: 4 MB;
- minimum free-space reserve: 4 GB;
- archive body downloads: zero.

## Decision rule

`PASS` requires all five exact-date archives to be discovered and HEAD-qualified with known positive byte size.

After PASS, freeze staged acquisition batches such that:

- no run downloads more than 2,000,000,000 bytes;
- no single file is downloaded unless its exact HEAD size is known;
- all five acquisition dates are fixed before any L2-based signal metric is calculated.

## Boundary

Q007 is data-planning only. A PASS says nothing about predictability or profitability.
