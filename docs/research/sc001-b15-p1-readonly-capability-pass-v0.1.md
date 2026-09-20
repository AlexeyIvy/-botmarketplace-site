# SC001 — B15-P1 Read-Only Capability PASS v0.1

Date: 2026-09-20
Status: **B15_P1_READONLY_CAPABILITY_PASS**

## 1. OKX

- capability = PASS;
- base URL = `https://openapi.okx.com`;
- permission = `read_only`;
- IP bound = true;
- currency/chain rows = 591;
- clock skew = approximately -241 ms.

## 2. Bybit

- capability = PASS;
- base URL = `https://api.bybit.com`;
- `readOnly = 1`;
- IP bound = true;
- Withdraw permission token present = false;
- coin rows = 793;
- chain rows = 1035;
- clock skew = approximately -130 ms.

## 3. Security confirmation

- secret values printed = false;
- price endpoints called = false;
- order endpoints called = false;
- transfer endpoints called = false;
- withdrawal endpoints called = false.

## 4. Research consequence

The credential/domain/source capability gate is complete.

Next allowed work:

1. canonical cross-venue asset/network identity freeze;
2. common-route universe construction;
3. prospective 15-second transferability-state collector design;
4. no price outcome yet.
