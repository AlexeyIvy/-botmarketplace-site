# Safe-Sleeve Hurdle Snapshot — 2026-09-10

**Project:** BotMarketplace / botmarketplace.store  
**Purpose:** freeze a dated safe-capital opportunity-cost reference before R003 forward evaluation  
**Status:** benchmark snapshot, not production allocation advice

## 1. Primary reference

Use the U.S. Treasury **13-week Treasury bill coupon-equivalent yield** as the primary short-duration safe-capital hurdle for the R003 forward paper comparison.

Latest available Treasury daily bill table before this snapshot: **2026-09-09**.

Reference rates:

- 4-week coupon equivalent: **3.72%**;
- 8-week coupon equivalent: **3.83%**;
- 13-week coupon equivalent: **3.90%**;
- 26-week coupon equivalent: **4.03%**;
- 52-week coupon equivalent: **4.16%**.

Primary frozen inception hurdle:

> **13-week Treasury bill coupon-equivalent = 3.90% annualized.**

Reason for 13-week choice: short duration, high liquidity, and closer economic role to capital intended to remain available than longer-duration bonds. It is a benchmark, not a claim that the actual production safe sleeve will hold this exact instrument.

## 2. R003 compensation floor

R003 carries risks absent from a Treasury-bill benchmark, including exchange, stablecoin/collateral, derivatives-margin, execution and access risk.

For forward research, also track:

> **Treasury hurdle + 2.00 percentage points = 5.90% annualized.**

This +2pp spread is frozen as a conservative research compensation diagnostic. It is not a tunable threshold and not a theoretical estimate of fair risk premium.

## 3. Inflation context

Latest released U.S. CPI available at snapshot time is **July 2026**, with all-items CPI up **3.4% year over year**.

The August 2026 CPI release is scheduled after this snapshot, on 2026-09-11.

Inflation is retained as purchasing-power context only. It is not the primary R003 opportunity-cost benchmark because capital can potentially earn a short Treasury yield rather than zero nominal return.

## 4. Interpretation for existing historical R003 evidence

R003-E002 POST_2023 historical implementation CAGR was approximately **3.74%** under the frozen 10 bps/leg model.

That number is below the 2026-09-09 13-week Treasury-bill reference of 3.90%, although the historical CAGR and current Treasury snapshot cover different time periods and therefore must not be treated as a matched performance comparison.

The implication is only that **current forward excess return versus safe capital must be measured explicitly before any live allocation case is made.**

## 5. Forward reporting rule

R003-E003 will report:

- strategy cumulative/annualized return;
- fixed inception Treasury hurdle at 3.90%;
- fixed research compensation floor at 5.90%;
- excess return versus each when annualization becomes meaningful.

Future Treasury rates may be recorded descriptively at review dates, but the frozen inception hurdles above must remain visible so the benchmark cannot be moved after seeing strategy results.

## 6. Non-equivalence warning

Treasury yields are market opportunity-cost references only. Actual investor access, taxes, settlement, custody and jurisdiction can differ.

This document does not recommend a security, broker, fund, bank or custodian.