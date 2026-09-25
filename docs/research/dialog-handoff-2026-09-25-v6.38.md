# SC001 / B15-P1 — dialog handoff v6.38 — 2026-09-25

Current state:

`B15P1_COLLECTOR_V014_OFFLINE_SELFTEST_SEALED_AWAITING_APPROVAL`

## Exact source-invalid root cause

The v0.1.1 diagnostic observed:

- Bybit: 10/10 HTTP 200 but 10/10 SOURCE_INVALID;
- exact error: `ValueError: invalid nonnegative decimal '-1'`;
- OKX: 8 OK, 2 request deadlines.

Bybit documents `withdrawMax=-1` as no limit.

v0.1.3 incorrectly treated that legal sentinel as an invalid generic negative decimal.

## Correction

New collector/library/service version: v0.1.4.

`withdrawMax=-1` is normalized to:

`UNLIMITED`

Only for that exact Bybit field.

All other negative numeric values remain fail-closed.

Route logic/cadence/price-PnL firewall are unchanged.

## New sealed offline self-test

- bundle ID: `bundle_20260925T185135Z_6c28a359`
- bundle SHA256: `cec279cbdb2768003f35ae9d1388d883caff6e3b8472ed4d6fc09bc8b3242e17`
- approval code: `BM-CEC279CBDB27`
- files: 23
- bytes: 297879
- inputs: none

Not run yet.

After full PASS:
1. create a new capability revalidation bound to v0.1.4 hashes;
2. do not reuse the old v0.1.3 capability snapshot;
3. only later prepare another controlled host launch retry.
