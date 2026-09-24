# SC001 — B15-P1 OKX Adapter Compatibility Audit v0.1

Date: 2026-09-24  
Status: **ROOT CAUSE IDENTIFIED / PRE-LIVE ADAPTER HARDENING REQUIRED**

## Trigger

Live source-capability revalidation reached the authenticated OKX currencies endpoint and stopped with:

`OKX currencies schema missing required fields in 591 rows`

The probe itself ran. This is no longer an infrastructure permission problem.

Safety remained intact:
- secret values printed = false;
- collector launch = false;
- price data used = false.

## Root cause

The v0.1 capability validator incorrectly treated `feeCcy` as a mandatory field of every row returned by:

`GET /api/v5/asset/currencies`

The current OKX Get currencies documentation does not list `feeCcy` in that endpoint's standard response schema. It lists fields including:

- ccy;
- chain;
- ctAddr;
- canDep;
- canWd;
- fee;
- burningFeeRate;
- minDep;
- minWd;
- maxWd;
- wdTickSz;
- minDepArrivalConfirm;
- minWdUnlockConfirm.

The 591-row all-row failure is therefore consistent with one universally absent wrongly-required field rather than 591 independently corrupt rows.

## Additional API drift identified before retry

### OKX fee-rate endpoint

Current OKX fee-rate semantics use:

`feeGroup[]`

with:

- groupId;
- taker;
- maker.

Top-level `taker`/`maker` remain documented as deprecated compatibility fields.

The current collector v0.1.2 slow fee parser primarily consumes the deprecated top-level fields.

If we only remove `feeCcy` from the capability validator, the next live or long-running stage could fail on this newer fee schema.

### Bybit spot instrument metadata

Current Bybit documentation states that Spot instruments do not support pagination. The previous capability probe included generic limit/cursor logic.

This should be simplified before the next live attempt.

## Hardening decision

Do not patch only the immediate failing line.

Before the next live revalidation:

1. version collector implementation to v0.1.3;
2. harden OKX Get currencies parser:
   - strict core identity/state fields;
   - optional/economic field profiling;
   - absent burningFeeRate must not silently become zero;
   - feeCcy becomes optional;
   - when Get currencies omits feeCcy, fixed fee currency is explicitly classified as the withdrawn asset under this endpoint adapter;
3. support OKX feeGroup/groupId response semantics in the slow fee lane;
4. retain deprecated top-level fee fields only as explicit fallback;
5. version capability probe to v0.2;
6. profile OKX schema instead of requiring all economic fields on every row;
7. qualify OKX instruments with groupId metadata;
8. remove unsupported Bybit Spot pagination logic;
9. add offline fixtures for:
   - current OKX currencies shape without feeCcy;
   - missing burningFeeRate fail-closed;
   - feeGroup parsing;
   - deprecated fee-field fallback;
   - Bybit no-pagination spot metadata;
10. run one combined offline adapter validation bundle before the next live command.

## Research semantics

Unchanged:
- frozen asset universe;
- frozen canonical representations;
- route graph;
- 15-second cadence;
- Stage C 61/71 bps cost floors;
- no-price firewall;
- launch authorization boundary.

This is an API-adapter compatibility correction only.
