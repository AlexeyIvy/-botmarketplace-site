# SC001 — B14-B Persistent Multi-Settlement Cross-Venue Funding Carry Protocol v0.1

Date: 2026-09-27
Status: **FROZEN BEFORE FRESH 2026 FUNDING VALUE ACCESS**
Scope: `SCALPING RESEARCH / SC001 / B14-B`

## 1. Mechanism

Test whether a cross-venue funding-rate differential has enough **causal persistence** that four entry/exit fills can be amortized across a seven-calendar-day delta-neutral carry cycle.

Economic source:

`cumulative realized funding cashflow differential`

This is not one-settlement B13-A and is not a price-convergence strategy.

## 2. Fresh evidence window

Use only:

`2026-07-01T00:00:00Z <= fundingTime < 2026-09-27T00:00:00Z`

This window is fresh relative to the B13-A H1-2025 structural screen.

No B13-A funding values may be mixed into B14-B.

## 3. Frozen universe

Use the same 12 pre-existing SC001 assets without selection:

BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI.

Venues:
- OKX linear USDT perpetual;
- Bybit linear USDT perpetual.

## 4. Funding semantics

Positive funding means longs pay shorts on both venues.

Define matched signal differential:

`d_t = OKX_realized_funding_rate_t - BYBIT_realized_funding_rate_t`

Matched timestamps may differ by at most 5 minutes.

Matching is used **only for the causal entry signal**.

Actual carry cashflow uses every realized funding settlement on each venue inside the hold interval, including settlements that do not have a simultaneous counterpart.

## 5. Causal persistence signal

At a matched funding event t, inspect exactly the last three matched differentials including t.

Signal exists iff all three are strictly positive or all three are strictly negative.

No magnitude threshold.

Direction:
- three positive differentials:
  `SHORT OKX / LONG BYBIT`;
- three negative differentials:
  `LONG OKX / SHORT BYBIT`.

The position is conceptually entered only **after** the third realized funding observation is known.

The funding event that creates the signal is not credited to the new cycle.

## 6. Seven-day hold

Frozen hold horizon:

`7 * 24 hours`

For a cycle opened after signal timestamp S:

`S < fundingTime <= S + 7 days`

Carry contribution:

`gross_carry_bps = direction_sign * 10000 * (sum_OKX_realized_rates - sum_BYBIT_realized_rates)`

where:
- direction_sign = +1 for SHORT OKX / LONG BYBIT;
- direction_sign = -1 for LONG OKX / SHORT BYBIT.

Direction remains fixed for the entire cycle.

No intra-cycle switching.

## 7. Non-overlap

Within each symbol:
- once a cycle opens, ignore all later entry signals until its seven-day hold ends;
- the next cycle may start only from a matched signal observed at or after the prior cycle end.

This avoids overlapping notional and pseudo-replication of the same funding regime.

## 8. Cycle source-quality gate

A cycle is valid only when:
- full seven-day hold ends before the frozen window end;
- both venue funding histories cover the full hold;
- each venue contributes at least 7 realized funding events;
- no gap between consecutive funding observations, including cycle boundaries, exceeds 24 hours.

No funding observation is imputed.

## 9. Structural economics

Four-fill burden inherited from the already qualified cross-venue paired architecture:

`40 bps`

B14-B gross structural headroom hurdle:

`50 bps`

This is deliberately favorable to the candidate:
- it allows only 10 bps gross reserve above four-fill burden;
- it does not yet charge additional seven-day capital lock, basis drift, margin, or counterparty risk.

Therefore failure of the 50 bps gross screen is a strong structural rejection.

## 10. Frozen structural gates

Data/sample gates:
- source-eligible symbols >=8;
- valid non-overlapping cycles >=24;
- symbols with valid cycles >=8;
- cycle-start calendar months represented >=2.

Structural SURVIVE requires all:
- pooled median gross_carry_bps >=50;
- positive-cycle share >=60%;
- at least 6 symbols have positive median cycle carry;
- at least 2 calendar months have positive median cycle carry.

If data/sample gate fails:

`B14B_DEFER_SOURCE_OR_SAMPLE`

If data/sample passes and any structural gate fails:

`B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`

If all pass:

`B14B_PERSISTENT_CARRY_STRUCTURAL_SURVIVE`

SURVIVE is not profitability Confirmation.

## 11. Allowed diagnostics

May report:
- source row counts by venue;
- matched signal-pair counts/skew;
- valid cycle count;
- pooled p25/median/p75 gross carry;
- positive-cycle share;
- aggregate symbol/month breadth counts;
- per-symbol cycle count and median carry;
- per-month cycle count and median carry.

No price data is needed.

## 12. Firewalls

Forbidden in this structural screen:
- spot/perpetual price;
- basis PnL;
- mark-price convergence;
- maker rebate assumptions;
- reducing four fills;
- alternate hold horizons;
- funding magnitude threshold search;
- symbol selection;
- price PnL;
- promotional claim.

## 13. Consequence

If REJECT:
close this exact 3-confirmation / 7-day multi-settlement funding architecture and run reusable-block extraction.

If SURVIVE:
next stage must explicitly add:
- basis drift risk;
- actual account fee semantics;
- margin/liquidation buffer;
- capital lock;
- venue/counterparty risk;
before any trading candidate promotion.
