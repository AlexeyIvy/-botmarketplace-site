# R001 — E003-S Put-Only Robustness v0.2

**Project:** BotMarketplace / botmarketplace.store  
**Candidate:** R001 — Antifragile Convex Barbell  
**Stage:** Free-data monthly screening  
**Dataset:** Deribit/Tardis first-of-month snapshots, 2019-10-01 through 2026-09-01  
**Decision timestamp:** 12:00 UTC  
**Status:** Completed robustness screen; not final validation

---

## 1. Why this v0.2 was necessary

The first E003-S screen showed that a static 15Δ put overlay with a 2% NAV/year premium budget on a 90/10 cash/BTC portfolio had negative carry and only modest monthly-sampled drawdown improvement.

Before changing the strategy, this v0.2 performs a small, economically justified robustness matrix and improves execution realism.

Changes vs v0.1:

1. test BTC directional weights of 10%, 15%, and 20%;
2. test annual premium budgets of 1%, 2%, and 3% NAV;
3. test put deltas of 10Δ, 15Δ, and 20Δ;
4. enforce executable entry at historical ask and exit at next monthly snapshot bid;
5. cap entry quantity at historical top-of-book ask size when available;
6. cap exit quantity at historical top-of-book bid size when available; any residual that cannot be liquidated at quoted top-of-book is valued conservatively at zero for this screening stress;
7. keep the maturity rule frozen: target 90 DTE, primary 60–120 DTE, fallback 45–150 DTE;
8. keep all explicit venue fees and extra slippage at zero, which means this remains an optimistic screen aside from the top-of-book stress. If the strategy is weak here, adding fees cannot rescue it.

The purpose is not to optimize a 27-point grid. The purpose is to determine whether a broad, economically reasonable region supports a static put overlay.

---

## 2. Screening mechanics

For each first-of-month decision point:

- baseline portfolio is rebalanced monthly to the selected BTC weight with the remainder in zero-yield cash;
- select a BTC put from the actual listed Deribit chain;
- choose the expiry nearest 90 DTE inside 60–120 DTE; if none exists, use nearest liquid expiry inside 45–150 DTE and mark as fallback;
- inside the selected expiry choose the put nearest target absolute delta;
- buy at historical ask;
- monthly premium budget = annual budget / 12 × current strategy NAV;
- cap contracts by top-of-book ask amount if quoted;
- at the next first-of-month snapshot, sell the same contract at historical bid, capped by bid amount;
- add the option P&L to the exact same cash/BTC baseline return.

No mark/mid fills are used for primary screening.

---

## 3. Main robustness result

Across **all 27 coarse combinations**:

- the put overlay reduced CAGR relative to the exact no-option baseline;
- no tested combination produced positive long-run incremental geometric return;
- 15Δ was consistently the least-bad delta among 10Δ/15Δ/20Δ;
- higher premium budgets increased worst-month protection but also increased long-run drag approximately proportionally;
- 20Δ sometimes worsened sampled max drawdown despite being closer to the money, because its premium drag outweighed its incremental protection over the monthly observation horizon;
- raising the BTC sleeve from 10% to 20% did not make the static put overlay economically attractive.

This is strong evidence against the hypothesis that a permanently-on static long-put sleeve, purchased mechanically every month, is attractive at these budgets and maturities.

---

## 4. Selected results

### 10% BTC directional sleeve

| Annual put budget | Put delta | Baseline CAGR | Overlay CAGR | CAGR drag | Baseline MDD | Overlay MDD | MDD improvement | Worst-month improvement |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1% | 10Δ | 5.27% | 4.99% | -0.28 pp | -10.52% | -10.48% | +0.04 pp | +0.27 pp |
| 1% | 15Δ | 5.27% | 5.04% | -0.22 pp | -10.52% | -10.41% | +0.12 pp | +0.28 pp |
| 1% | 20Δ | 5.27% | 5.02% | -0.25 pp | -10.52% | -10.70% | -0.18 pp | -0.08 pp |
| 2% | 15Δ | 5.27% | 4.82% | -0.44 pp | -10.52% | -10.29% | +0.23 pp | +0.56 pp |
| 3% | 15Δ | 5.27% | 4.60% | -0.67 pp | -10.52% | -10.18% | +0.34 pp | +0.84 pp |

### 15% BTC directional sleeve

| Annual put budget | Put delta | Baseline CAGR | Overlay CAGR | CAGR drag | Baseline MDD | Overlay MDD | MDD improvement |
|---:|---:|---:|---:|---:|---:|---:|
| 1% | 15Δ | 7.82% | 7.60% | -0.22 pp | -15.49% | -15.37% | +0.12 pp |
| 2% | 15Δ | 7.82% | 7.39% | -0.44 pp | -15.49% | -15.26% | +0.23 pp |
| 3% | 15Δ | 7.82% | 7.16% | -0.66 pp | -15.49% | -15.15% | +0.35 pp |

### 20% BTC directional sleeve

| Annual put budget | Put delta | Baseline CAGR | Overlay CAGR | CAGR drag | Baseline MDD | Overlay MDD | MDD improvement |
|---:|---:|---:|---:|---:|---:|---:|
| 1% | 15Δ | 10.32% | 10.10% | -0.22 pp | -20.27% | -20.15% | +0.12 pp |
| 2% | 15Δ | 10.32% | 9.89% | -0.43 pp | -20.27% | -20.04% | +0.23 pp |
| 3% | 15Δ | 10.32% | 9.67% | -0.65 pp | -20.27% | -19.92% | +0.35 pp |

The near-constant absolute MDD improvement across BTC weights is an important clue: the option budget is expressed as % NAV, so the hedge benefit is mostly driven by the option budget, while the portfolio's directional risk scales with BTC allocation. Static puts therefore become proportionally less meaningful as BTC risk increases unless the premium budget is also increased, which further worsens carry.

---

## 5. Option economics

For the 15Δ family:

- payout/premium ratio remains below 1 across the tested directional weights and budgets;
- at 10% BTC / 2% annual budget, top-of-book-aware screening paid about **$16.8k** of premium and generated about **-$3.7k** cumulative option P&L;
- 15Δ was materially better than 10Δ and modestly better than 20Δ in total carry economics;
- 10Δ is cheaper per contract but wins too infrequently and recovers less premium;
- 20Δ pays substantially more for closer protection without sufficient incremental benefit on the monthly horizon.

For the 15Δ / 2% baseline, only a small number of entries were constrained by quoted top-of-book size (four months at the 10% BTC baseline). Therefore the negative result is not primarily a liquidity-cap artifact.

---

## 6. Tail behavior

The puts clearly provide real convex payoff in severe down months. Examples include the monthly windows beginning around:

- March 2020;
- May 2021;
- June 2022;
- several later >15–20% BTC down months.

For the 15Δ / 2% configuration, the put often produced multiples of premium in the largest downside months. The problem is frequency and carry: most months lose substantial portions of premium, so the cumulative insurance cost dominates the sampled drawdown reduction.

A block-bootstrap diagnostic of monthly 15Δ option return-on-premium produced a mean materially below zero, with a 95% interval that remains approximately below zero in this sample. This is not a final statistical proof, but it reinforces the economic conclusion that the static overlay has persistent negative carry rather than a hidden positive expectancy.

---

## 7. Important methodological discovery: premium budget must be interpreted relative to the risk being hedged

A 2% NAV/year option budget sounds small at portfolio level, but with only a 10% BTC sleeve it equals **20% of the directional sleeve notional per year**.

Examples:

- 10% BTC + 1% NAV premium budget = 10% of BTC sleeve notional/year;
- 10% BTC + 2% NAV = 20% of BTC sleeve/year;
- 20% BTC + 1% NAV = 5% of BTC sleeve/year;
- 20% BTC + 2% NAV = 10% of BTC sleeve/year.

This explains why the original 90/10 + 2% premium setup was structurally expensive.

Future research should therefore report **both**:

1. option premium budget as % portfolio NAV/year; and
2. option premium budget as % directional sleeve notional/year.

This prevents a misleading comparison between portfolios with different BTC weights.

---

## 8. What is justified to improve next

The static put hypothesis has now been tested enough to avoid spending time on broader brute-force optimization.

The next justified research directions are:

### A. Reduce static premium intensity

Run a small diagnostic at 0.25%, 0.5%, and 1.0% NAV/year, primarily around 15Δ, to quantify the efficient frontier between geometric drag and tail protection. This is not expected to create positive option expectancy; it tests whether a very small insurance allocation can be economically tolerable.

### B. Test regime-aware purchasing before calls or ladders

The strongest economic hypothesis left is not “buy puts every month”, but “buy convexity when it is relatively cheap.”

The next research candidate should therefore be a **pre-defined, lagged volatility-value filter** using only data available at each decision point. Candidate inputs:

- selected put mark IV;
- expanding / rolling IV percentile;
- BTC realized volatility from independent spot data;
- IV/RV ratio;
- put skew if recoverable from the same monthly chain;
- term structure.

To control overfit, thresholds must be selected on an early train window and frozen before later OOS evaluation.

### C. Do not add calls yet

Calls are not justified until the downside convexity sleeve demonstrates acceptable economics. The BTC directional sleeve already owns upside delta, so adding call premium now would increase negative carry and confound attribution.

### D. Do not add laddering yet

Laddering changes timing risk but cannot repair a fundamentally overpriced static premium stream. It should only be tested after a better option-purchase regime is identified.

---

## 9. Decision

### Static monthly long-put sleeve

**Status: REDESIGN — not PASS.**

The evidence does not support a permanently-on static 10Δ/15Δ/20Δ put overlay at 1–3% NAV/year for the tested 10–20% BTC sleeves.

### Preferred continuation of R001

Continue R001, but change the next hypothesis from:

> “constant long convexity improves the barbell”

into:

> “small or conditional long convexity may improve the barbell when protection is purchased selectively at favorable volatility pricing.”

The next experiment should be **E004-S: Low-Budget + Volatility-Value Regime Screen**, with explicit train/OOS separation and no calls/ladders yet.

---

## 10. Screening limitations

These results are intentionally conservative/limited and are not final proof because:

- only first-of-month snapshots are observed;
- intramonth path, intraday gamma, and true crisis peak option values are not captured;
- explicit historical exchange fees are not yet included;
- additional slippage beyond the quoted spread is not included;
- cash earns zero yield;
- directional BTC is represented by monthly sampled underlying prices;
- no venue/custody/stablecoin stress is included here;
- fallback maturities occur in a few early months.

However, these limitations do not provide an obvious mechanism that would reverse the static put result: most omitted execution costs would make it worse, while missing intramonth crisis peaks could make some tail exits better if the strategy had an explicit intramonth monetization rule. That is a separate hypothesis and should be tested separately rather than assumed.
