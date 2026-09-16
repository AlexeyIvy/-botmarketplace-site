# SC001 — Common Accounting Core Validation Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN SYNTHETIC VALIDATION — NO REAL MARKET BODY ACCESS**

## 1. Purpose

Validate the common accounting primitives required by future SC001 taker/passive/multi-leg execution kernels before any fresh July/August strategy body is opened.

This stage is synthetic-only. It does not calculate any strategy alpha or promotional PnL.

## 2. Representation

Canonical execution/accounting state uses:

- integer price ticks;
- integer quantity lots;
- Decimal conversion from exact string specifications;
- explicit linear USDT-settled contract value;
- immutable fill records with unique fill IDs;
- cash-flow accounting independent of strategy logic.

Binary float is not the source of truth for tick/lot equality or fee/PnL conservation.

## 3. Linear contract accounting

For a linear swap where `ctVal` is base-asset amount per contract:

`contracts = qty_lots * lotSz`

`base_amount = contracts * ctVal`

`notional_USDT = price * base_amount`

BUY cashflow:
`-notional - fee`

SELL cashflow:
`+notional - fee`

`fee = notional * fee_bps / 10,000`

When inventory returns exactly to zero, cumulative cash delta is realized net PnL.

Non-flat equity may be marked independently using a supplied mark price.

Inverse/non-USDT formulas are explicitly unsupported by this v0.1 core and must fail closed rather than be approximated.

## 4. Required synthetic tests

At minimum:

1. exact tick conversion round-trip;
2. reject off-tick price;
3. exact lot conversion round-trip;
4. reject off-lot quantity;
5. minimum-size enforcement;
6. long round-trip gross/fee/net hand calculation;
7. short round-trip symmetry;
8. partial-fill aggregation;
9. multi-fill same-side accumulation;
10. inventory conservation;
11. cash conservation;
12. mark-to-market for non-flat long;
13. mark-to-market for non-flat short;
14. duplicate fill ID rejection;
15. non-positive fill quantity rejection;
16. invalid liquidity/side rejection;
17. future-observation causality guard;
18. deterministic normalized ledger serialization/hash;
19. order of identical-timestamp fills preserved by explicit sequence number;
20. unsupported inverse contract fails closed.

## 5. Terminal gate

Exact PASS:

`SC001_COMMON_ACCOUNTING_CORE_VALIDATION_PASS`

PASS requires all frozen tests to pass and report:

- real market data body accessed = False;
- strategy signal calculated = False;
- promotional PnL calculated = False;
- July/August reserved bodies accessed = False.

Any failed assertion yields:

`SC001_COMMON_ACCOUNTING_CORE_VALIDATION_REVIEW`

and blocks execution-kernel work until corrected under a new implementation identity.

## 6. Relationship to historical specs

Synthetic fixtures use explicit test specs only.

PASS does not claim that 2024 historical `tickSz`, `lotSz`, `minSz`, or `ctVal` have been resolved. Historical execution-spec handling remains a separate mandatory gate before promotional execution/PnL.
