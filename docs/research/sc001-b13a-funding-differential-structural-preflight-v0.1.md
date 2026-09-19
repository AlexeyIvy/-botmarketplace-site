# SC001 — B13-A Cross-Venue Funding-Differential Structural Preflight v0.1

Date: 2026-09-19
Status: **FROZEN NON-ALPHA STRUCTURAL PREFLIGHT / NO C13 ID / NO PRICE PNL**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.82.md`;
- `docs/research/sc001-post-c11-independent-base-opportunity-pool-v0.1.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-first-generation-multi-asset-universe-freeze-v1.0.json`.

## 1. Objective

Test the cheapest structural question for B13-A:

> Is the cross-venue funding-rate differential itself ever large and broad enough to plausibly cover a conservative four-fill delta-neutral architecture?

This is not a strategy backtest.

It does not calculate:

- entry/exit prices;
- basis convergence;
- mark/spot response;
- slippage from market data;
- strategy PnL.

## 2. Frozen venues

Exactly:

- OKX USDT-margined perpetual swaps;
- Bybit USDT linear perpetuals.

No venue may be selected because historical funding looks better.

## 3. Frozen symbol universe

Start from the previously frozen 12-symbol first-generation SC001 universe:

- BTC;
- ETH;
- SOL;
- DOGE;
- ORDI;
- FIL;
- UNI;
- XRP;
- LTC;
- OP;
- BCH;
- SUI.

Mapping:

- OKX: `SYMBOL-USDT-SWAP`;
- Bybit: `SYMBOLUSDT`.

A symbol is source-eligible only if both venues expose the required perpetual and funding history for the target period.

Source ineligibility must be recorded before funding-differential verdicts.

No symbol substitution.

## 4. Frozen nonpromotional chronology

Structural Selection/Calibration window:

`2025-01-01 00:00 UTC through 2025-06-30 23:59:59 UTC`

This window is nonpromotional.

Anything learned from this funding-value screen may not later be presented as untouched Confirmation evidence.

No market price body is authorized.

## 5. Official funding sources

### OKX

Primary public endpoint:

`GET /api/v5/public/funding-rate-history`

Required fields include:

- instId;
- fundingTime;
- realizedRate and/or the exact settled funding-rate field qualified by source semantics;
- method/formulaType diagnostics where present.

### Bybit

Primary public endpoint:

`GET /v5/market/funding/history`

Required fields include:

- symbol;
- fundingRate;
- fundingRateTimestamp.

Before any differential arithmetic, source semantics must establish the sign convention on both venues.

## 6. Funding-event matching

Funding intervals can vary by instrument/venue.

Do not assume every contract always uses an 8-hour interval.

Create matched settlement pairs only when:

- same underlying symbol;
- one OKX settled funding record;
- one Bybit settled funding record;
- absolute settlement timestamp difference <= `5 minutes`;
- each funding record is used at most once.

If multiple candidates exist, deterministic nearest-timestamp matching is required; tie -> earlier timestamp.

No carry-forward of stale funding records.

## 7. Structural upper-bound statistic

After sign semantics are qualified, define for each matched funding settlement:

`gross_funding_diff_bps = 10000 * abs(okx_settled_rate - bybit_settled_rate)`

This is an **upper-bound structural transfer statistic**.

It assumes the economically favorable venue orientation could be known and established.

It is not yet a causal trading result.

No price/basis return may be added.

## 8. Conservative four-fill burden

Frozen screening architecture:

- paired entry = 2 taker fills;
- paired exit = 2 taker fills;
- total = 4 structural fills.

Frozen cost references:

- fee floor = 5 bps/fill × 4 = `20 bps`;
- spread/legging reserve = `10 bps`;
- execution/model reserve = `10 bps`.

Structural burden:

`40 bps`

Minimum attractive structural funding differential:

`50 bps`

The extra 10 bps is a minimum reserve above break-even.

Do not use maker rebates in this preflight.

## 9. Data-quality gates

Require all:

- at least 8/12 symbols source-eligible on both venues;
- at least 4 calendar months represented after matching;
- at least 500 matched funding settlements total;
- no duplicate funding record reuse;
- timestamps/values finite and parseable;
- exact source identity recorded.

Otherwise:

`B13A_DEFER_SOURCE_OR_SAMPLE`

No structural economics verdict.

## 10. Structural feasibility gates

After data-quality PASS, define qualifying funding opportunities as matched settlements with:

`gross_funding_diff_bps >=50`

B13-A may receive:

`B13A_STRUCTURAL_PREFLIGHT_SURVIVE`

only if all:

- qualifying opportunities >= `12`;
- qualifying opportunities occur on >= `8 distinct UTC dates`;
- qualifying opportunities span >= `3 calendar months`;
- qualifying opportunities occur in >= `4 symbols`;
- no single symbol contributes > `50%` of qualifying opportunities.

If data-quality passes but any structural gate fails:

`B13A_REJECT_STRUCTURAL`

## 11. Diagnostics only

Report, but do not use as verdict gates:

- median gross funding differential across all matched settlements;
- p90/p99 differential;
- maximum differential;
- per-symbol counts;
- per-month counts;
- settlement timestamp skew distribution.

No best-symbol promotion.

## 12. Interpretation

SURVIVE means only:

> funding transfer magnitude/frequency is structurally large enough to justify a later causal-availability and price/execution design.

It does not prove:

- predicted funding can be known accurately enough before settlement;
- basis risk is controlled;
- both legs can be opened/closed cheaply;
- cross-venue collateral/legging risk is acceptable;
- net strategy profitability.

REJECT_STRUCTURAL means the funding transfer itself lacks sufficient scale/breadth under the frozen four-fill burden.

## 13. Anti-rescue

After output do not:

- lower 50 bps;
- lower 40 bps burden;
- choose only the best symbol;
- choose only one stress month;
- widen timestamp match after seeing output;
- add price convergence PnL;
- switch to maker assumptions;
- add C1-C12 features.

A changed architecture requires a new design.

## 14. Candidate-ID gate

B13-A is not yet `C13`.

Only a structural SURVIVE followed by three-role review may assign a candidate ID.

## 15. Immediate implementation sequence

1. freeze exact source semantics and pagination;
2. implement source-only/funding-value runner;
3. syntax/source tests;
4. run once on H1-2025;
5. write exact structural disposition;
6. no market-price access.
