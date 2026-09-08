# R001-E003-S — Put-Only Screening Results v0.1

**Candidate:** R001 Antifragile Convex Barbell  
**Stage:** Zero-cost monthly screening  
**Period:** 2019-10-01 to 2026-09-01  
**Decision schedule:** first day of each month, 12:00 UTC  
**Data:** free first-of-month Deribit BTC option ticker snapshots collected from Tardis  
**Status:** Screening result — REDESIGN / CONTINUE LIMITED

## Method

Baseline portfolio:

- 90% cash, zero assumed yield
- 10% BTC
- monthly rebalance to 90/10 at each decision point

Put overlay:

- same 90/10 baseline
- long BTC put only
- target absolute delta: 15Δ
- target DTE: 90
- primary DTE range: 60–120
- fallback range: 45–150 only when no primary expiry exists
- only two-sided executable markets accepted
- entry at historical ask
- next first-of-month exit / MTM at historical bid for the same contract
- annual premium budget: 2% NAV/year, allocated monthly
- continuous contract sizing for the primary screening calculation
- no explicit exchange fee added yet; bid/ask spread is included

BTC monthly proxy for this screening uses the median `underlying_price` from the shortest-DTE listed expiry at each monthly snapshot. This is adequate for screening but must be replaced/cross-checked with an independent BTC index series before final validation.

## Data quality

- 84 monthly snapshots
- 54,329 option rows
- 100% delta coverage
- 80 primary selections
- 4 fallback maturity selections
- 0 missed months
- selected 15Δ-put median absolute delta error: ~1.4 delta points
- selected-put median bid/ask spread: ~4.35%
- selected-put 95th percentile spread: ~11.7%
- selected-put worst observed spread: ~22.2%

## Primary economic result

| Metric | 90/10 baseline | 90/10 + monthly 15Δ puts |
|---|---:|---:|
| Final NAV from $100k | $141,769 | $137,667 |
| CAGR | 5.18% | 4.73% |
| Annualized volatility | 6.50% | 6.11% |
| Sharpe, rf=0 diagnostic | 0.81 | 0.79 |
| Sortino, rf=0 diagnostic | 1.53 | 1.56 |
| Max monthly-sampled drawdown | -10.47% | -10.23% |
| Worst monthly return | -3.93% | -3.37% |

Incremental option economics:

- cumulative option premium paid: ~$17,131
- cumulative option bid value recovered next month: ~$13,401
- cumulative option P&L: **-$3,730**
- recovered value / premium: **0.782**
- profitable option months: **18 of 83**
- option overlay reduced CAGR by ~0.45 percentage points/year
- max monthly-sampled drawdown improved by only ~0.23 percentage points absolute (~2.2% relative)

## Tail behaviour

The put overlay did behave directionally as intended in several large down months.

Examples:

- 2020-03: BTC proxy ~-27.2%; put overlay improved portfolio monthly return by ~0.50 percentage points
- 2021-05: BTC proxy ~-36.8%; option P&L ~+$883 and portfolio benefit ~+0.70 percentage points
- 2022-06: BTC proxy ~-39.3%; option P&L ~+$684 and portfolio benefit ~+0.57 percentage points

Across all negative BTC months, average incremental put benefit was positive (~+0.066 percentage points/month). Across positive BTC months, average incremental effect was negative (~-0.121 percentage points/month), reflecting persistent premium/spread drag.

The best option month in this screening was 2021-05. The worst option month was 2026-08, when the put premium largely decayed during a strong BTC up month.

## Interpretation

The first zero-cost screening does **not** support the hypothesis that a static 2% NAV/year monthly 15Δ put overlay on a 90/10 cash/BTC portfolio creates enough economic value to justify its drag.

The puts clearly provide crisis payoff in some severe down months, so convexity itself is real. However, under this conservative 10% BTC directional exposure, the persistent premium and spread cost dominates the modest drawdown benefit.

This is not a rejection of R001 as a whole because:

1. the 90/10 baseline has low BTC beta already, so expensive tail insurance has little portfolio risk to protect;
2. first-of-month data only observes monthly endpoints and cannot measure intramonth drawdown reduction, gamma path, or crisis monetization timing;
3. no volatility-regime filter is used yet;
4. only one delta and one premium budget are tested;
5. the BTC proxy should be independently cross-checked before final claims.

## Decision

**R001-E003-S status: REDESIGN / CONTINUE LIMITED.**

Do not proceed to calls, ladders, or production implementation yet.

Next tests should remain coarse and falsification-oriented:

1. Repeat put-only screening for directional weights 10%, 15%, and 20%.
2. Test annual put premium budgets 1%, 2%, and 3% NAV/year.
3. Test 10Δ / 15Δ / 20Δ puts without broad optimization.
4. Compare static monthly buying with a simple, ex-ante volatility-cost filter only after the static sensitivity grid is understood.
5. Cross-check the BTC monthly price proxy with a separate free BTC index/spot source.

If no broad parameter region materially improves downside protection without unacceptable geometric drag, the static put sleeve should be rejected or radically reduced before any further complexity is added.
