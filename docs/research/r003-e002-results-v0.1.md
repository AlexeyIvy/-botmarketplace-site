# R003-E002 — Self-Financing BTC Cash-and-Carry Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R003 — Funding / Basis Carry  
**Experiment:** E002  
**Date:** 2026-09-10  
**Status:** historical implementation study  
**Decision:** **IMPLEMENTATION_PROMISING**  
**Recent capital efficiency:** **MARGINAL**  
**Protocol:** `docs/research/r003-e002-self-financing-cash-carry-protocol-v0.1.md`

## 1. Executive decision

R003-E002 passes its pre-frozen implementation gate.

Formal status:

> **IMPLEMENTATION_PROMISING**

This is not production PASS and not independent OOS evidence. The result shows that the previously observed BTCUSDT funding premium survives a materially more realistic fully funded long-spot / short-perpetual implementation on the inspected Binance history.

The central result is economically meaningful but current/recent capital efficiency is only **MARGINAL**, so the candidate should be preserved and forward-observed rather than deployed or used immediately to justify option spending.

## 2. Data audit

Data gate: **PASS**.

Downloaded source rows:

- spot BTCUSDT 1h: 61,544;
- futures contract 1h: 61,395;
- futures mark 1h: 58,857;
- funding rows: 7,670.

PRIMARY_2020 common hourly grid:

- usable common rows: 58,620;
- expected rows: 58,652;
- common coverage: 99.9454%;
- maximum common gap: 6 hours;
- gate minimum coverage: 99.5%;
- gate maximum gap: 6 hours.

The data therefore passes, but note that the maximum observed common gap sits exactly on the frozen 6-hour tolerance boundary. No interpolation is used.

## 3. Canonical implementation

Frozen portfolio:

- 50% NAV long BTC spot;
- 50% NAV USDT futures collateral;
- equal-BTC short BTCUSDT perpetual;
- no external borrowing;
- no portfolio-margin assumption;
- UTC calendar month-end rebalance;
- 10 bps baseline cost per traded notional per leg;
- published realized funding;
- futures P&L marked with Binance mark price;
- conservative intrahour margin headroom checked using mark-price high.

## 4. Baseline result — 10 bps per leg

| Slice | CAGR | Max DD | Ending multiple | Funding cash | Pair/basis P&L | Execution cost | Min intrahour collateral |
|---|---:|---:|---:|---:|---:|---:|---:|
| PRIMARY_2020 | **6.60%** | **-1.33%** | **1.533x** | +0.5529 | -0.0022 | -0.0175 | **18.45%** |
| PRE_2023 | **10.14%** | **-1.33%** | **1.336x** | +0.3478 | -0.0016 | -0.0099 | **18.45%** |
| POST_2023 | **3.74%** | **-1.10%** | **1.145x** | +0.1533 | -0.0004 | -0.0076 | **33.51%** |

PRIMARY_2020 annualized volatility is ~1.71% and Calmar ~4.97.

Accounting identity is internally coherent on PRIMARY_2020:

`1 + funding contribution + pair/basis P&L - execution cost ≈ ending multiple`

`1 + 0.552924 - 0.002239 - 0.017485 ≈ 1.533200`.

This confirms that the economic result is overwhelmingly funding-driven rather than hidden directional BTC exposure or favorable basis drift.

## 5. Funding ablation

PRIMARY_2020 at 10 bps per leg:

- REALIZED_FUNDING CAGR: **+6.60%**;
- ZERO_FUNDING CAGR: **-0.23%**;
- ADVERSE_FUNDING CAGR: **+2.46%**.

Therefore realized funding is the actual source of historical return. Pair/basis movement plus execution without funding is slightly negative.

The pre-specified adverse-funding stress remains positive on PRIMARY_2020, satisfying the frozen robustness gate.

However POST_2023 adverse-funding CAGR is only about **+1.41%**, which is below the 2.5% capital hurdle. This was not a separate frozen fail gate, but it is an important risk interpretation for future economics.

## 6. Fee stress

REALIZED_FUNDING:

### PRIMARY_2020

- 5 bps/leg CAGR: ~6.70%;
- 10 bps/leg: ~6.60%;
- 25 bps/leg: ~6.28%.

### POST_2023

- 5 bps/leg CAGR: ~3.84%;
- 10 bps/leg: ~3.74%;
- 25 bps/leg: ~3.45%.

The result is not especially fee-sensitive at the frozen month-end rebalance frequency.

## 7. Margin/headroom result

No hard margin failure occurred.

PRIMARY_2020:

- minimum close collateral ratio: ~18.80%;
- minimum conservative intrahour collateral ratio: **18.45%**;
- hours below the frozen 10% headroom threshold: **0**.

The historical minimum occurred during the 2021 bull regime. Under the canonical fully funded 50/50 convention, the short leg retained meaningful modeled headroom.

This does not model exact historical Binance maintenance-margin tiers, exchange default, withdrawal freeze, collateral impairment or a discontinuous move beyond observed hourly highs.

## 8. Basis diagnostics

PRIMARY_2020 mark basis:

- mean: about -1.2 bps;
- median: about -3.3 bps;
- 1st percentile: about -8.0 bps;
- 99th percentile: about +15.7 bps;
- maximum absolute hourly mark basis: ~2.10%;
- worst 24h mark-basis widening against the short hedge: ~1.88%.

Contract-close basis reached a maximum absolute value around 2.57%.

Despite these temporary dislocations, cumulative pair/basis P&L over PRIMARY_2020 is only about -0.22% of initial NAV. The major economic contribution remains funding.

## 9. Additional technical review: mark versus executable contract price

The canonical engine marks futures P&L with mark price, which is appropriate for margin/NAV diagnostics, while actual re-hedging would execute against the tradable contract/order book rather than exactly at mark.

A post-result diagnostic using the uploaded hourly contract and mark closes at the frozen month-end rebalance times estimates the omitted mark-to-contract execution-basis effect at only about **-0.055% of initial NAV cumulatively** over PRIMARY_2020, including inception and terminal closure approximation.

This is post-hoc and not a replacement backtest, but its magnitude is far too small to explain the +53.3% cumulative net gain. The frozen E002 conclusion is therefore not plausibly driven by this accounting simplification.

A future forward/shadow implementation must nevertheless record executable bid/ask or actual contract execution prices explicitly.

## 10. Calendar-year stability

Baseline completed calendar-year returns:

- 2020: +9.85%;
- 2021: +19.45%;
- 2022: +1.94%;
- 2023: +4.12%;
- 2024: +6.50%;
- 2025: +2.56%.

All six completed years are positive, but magnitude is highly non-stationary. The largest positive completed year contributes ~43.79% of the sum of positive completed-year returns, below but fairly close to the frozen 50% concentration limit.

2026 through the frozen data cutoff is only about +0.80% cumulative.

## 11. Recent-regime warning

POST_2023 baseline CAGR is **3.74%**, so the frozen capital-efficiency classification is only **MARGINAL**: above the 2.5% hurdle but below 5%.

A descriptive, post-hoc trailing-365-day calculation from the canonical PRIMARY_2020 hourly NAV path gives only about **+1.50%** through the frozen endpoint. This is not a pre-specified decision criterion, but it strengthens the warning that the carry premium has compressed materially in the most recent regime.

Therefore do not extrapolate the 2020-2021 economics into current expected return.

## 12. Frozen decision gate

All central E002 implementation checks pass:

1. positive baseline CAGR on PRIMARY_2020 / PRE_2023 / POST_2023: PASS;
2. POST_2023 CAGR >=2.5%: PASS;
3. PRIMARY_2020 Max DD <10%: PASS;
4. no hard margin failure: PASS;
5. minimum intrahour collateral ratio >=10%: PASS;
6. 25 bps/leg stress positive PRIMARY_2020 and POST_2023: PASS;
7. adverse funding positive on PRIMARY_2020: PASS;
8. realized funding improves CAGR by >1pp versus zero funding: PASS;
9. completed-year majority positive and no single positive year >=50% of positive-year sum: PASS.

Formal result:

> **IMPLEMENTATION_PROMISING**

with the explicit qualifier:

> **RECENT CAPITAL EFFICIENCY = MARGINAL**

## 13. Research interpretation

The evidence now supports a stronger statement than E001:

> A conservative, fully funded BTC spot / BTCUSDT-perpetual carry implementation historically converted realized funding into positive low-volatility net returns after modeled basis movement, month-end re-hedging and two-leg execution costs.

It does **not** support calling the trade risk-free or production-ready.

The main unresolved risks are now operational and forward-looking rather than basic historical P&L arithmetic:

- future funding compression/reversal;
- exchange/custodian default or withdrawal freeze;
- stablecoin/collateral impairment;
- actual liquidation/maintenance-margin mechanics;
- executable spread/slippage under stress;
- legging/API outage risk;
- opportunity cost versus a real safe sleeve.

## 14. Next action

Do not tune funding-entry thresholds, leverage, collateral split or rebalance frequency on this history.

Recommended sequence:

1. preserve R003 v0.1 unchanged;
2. open a forward/shadow R003 record with actual live spot/perpetual/funding observations and executable-price diagnostics;
3. in parallel compare the risky fully funded carry against the explicit safe-sleeve opportunity cost;
4. because recent carry is marginal, do **not** yet use R003 as justification for production allocation or a long-option premium budget;
5. only if forward carry remains economically meaningful should carry-funded convexity be opened as a separate candidate.