# SC001 — B15-P1 Live Read-Only Credential Capability Preflight v0.1

Date: 2026-09-20
Status: **FROZEN SECURITY/SOURCE CAPABILITY PREFLIGHT / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md`;
- `docs/research/sc001-b15-p1-transferability-shock-four-role-optimization-review-v0.2.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.29.md`.

## 1. Purpose

Verify that the user's dedicated OKX and Bybit credentials can safely read the transferability-state sources required by B15-P1.

No order, transfer, withdrawal, price, spread, return or PnL endpoint is authorized.

## 2. Default domains

Given a Russian/global account context, defaults are:

- OKX: `https://openapi.okx.com`;
- Bybit: `https://api.bybit.com`.

These values remain explicit configuration and may be corrected only if live capability responses show a region/domain mismatch.

## 3. Secret source

Read only:

`/home/botmarket/.config/sc001/b15-p1.env`

Required filesystem mode:

`0600`

Do not print secret values.

## 4. OKX capability

Public time:

`GET /api/v5/public/time`

Private permission check:

`GET /api/v5/account/config`

Require current API-key permission:

`read_only`

No `trade` or `withdraw`.

Transferability source:

`GET /api/v5/asset/currencies`

Require:

- code = 0;
- non-empty currency list;
- chain-level fields include:
  - ccy;
  - chain;
  - canDep;
  - canWd.

## 5. Bybit capability

Public time:

`GET /v5/market/time`

Private API-key check:

`GET /v5/user/query-api`

Require:

`readOnly = 1`

Record only safe diagnostics:

- readOnly;
- IP-bound yes/no;
- permission-category names;
- whether Withdraw token is present.

Do not print UID, API key, KYC region, IP values or secret material.

Transferability source:

`GET /v5/asset/coin/query-info`

Require:

- retCode = 0;
- non-empty rows;
- chain-level fields:
  - chain;
  - chainType;
  - chainDeposit;
  - chainWithdraw;
  - contractAddress.

## 6. Clock gate

Authenticated REST depends on synchronized time.

Record local-vs-exchange time skew for both venues.

Require absolute skew <= 10 seconds.

Failure is CAPABILITY_REVIEW, not source/strategy reject.

## 7. PASS

Exact PASS:

`B15_P1_READONLY_CAPABILITY_PASS`

Requires all:

- secret file mode 0600;
- OKX read-only permission;
- OKX currencies schema PASS;
- Bybit readOnly=1;
- Bybit coin-info schema PASS;
- both clocks within tolerance.

Otherwise:

`B15_P1_READONLY_CAPABILITY_REVIEW`

## 8. Firewalls

Forbidden:

- price endpoints;
- order endpoints;
- transfer endpoints;
- withdrawal endpoints;
- balance-based strategy logic;
- spread/basis;
- PnL.

## 9. Consequence

PASS authorizes only:

1. canonical route/universe identity freeze;
2. prospective 15-second transferability-state collector design.

No B15 price outcome is authorized.
