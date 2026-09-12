# SC001-DATA-Q005R — OKX Tick-Trade Preflight Repair Protocol v0.1

Status: **FROZEN BEFORE RERUN**

Parent: `SC001-DATA-Q005` (REDESIGN)

## Purpose

Repair only the objective exact-date identity defect found in Q005. Q005R is metadata/HEAD qualification only. No archive bodies, signal/features, P&L, formal Validation or Final.

## Frozen venue / instrument / module

- Venue: OKX
- Instrument type: SWAP
- Instrument family: BTC-USDT
- Target instrument: BTC-USDT-SWAP
- Trade module: `1`

Freezing module `1` is not performance selection. Q005 metadata showed module `1` returning `BTC-USDT-SWAP-trades-*`; module `2` returned candlesticks; module `4` returned L2; modules `3`/`5` did not return usable trade files.

## Frozen dates

Exactly the same five 2024-Q1 dates:

- 2024-01-05
- 2024-01-14
- 2024-01-31
- 2024-02-12
- 2024-02-13

No replacement dates are allowed.

## Exact identity rule

For requested date `D`, the only acceptable filename is:

`BTC-USDT-SWAP-trades-D.zip`

The backend may return adjacent-day files. Those must be ignored, not treated as ambiguity, provided there is exactly one exact-date filename match.

PASS for a date requires:

1. exactly one exact-date filename match;
2. HTTPS URL on trusted `static.okx.*` host;
3. HEAD succeeds without untrusted redirect;
4. positive Content-Length;
5. filename and URL remain consistent with requested date and target instrument.

If zero or more than one exact-date candidate remains, mark REVIEW and do not substitute another date.

## Prior-run anchoring

Q005R must read the local Q005 report and require:

- correct Q005 stage;
- `overall_status=REDESIGN`;
- archive bodies were not downloaded;
- module `1` metadata contains an exact target/date trade filename for 2024-01-05.

This prevents Q005R from silently becoming a new discovery procedure.

## Safety

- network cap: 20 MB
- workspace cap: 20 MB
- per response cap: 4 MB
- minimum free reserve: 4 GB
- no archive GET

## Outcome

`PASS`: all five exact-date trade archives qualify by metadata + HEAD.

`REVIEW`: at least one fixed date fails exact-date identity or HEAD checks.

`ERROR`: safety or parser failure.

No profitability status is available in Q005R.
