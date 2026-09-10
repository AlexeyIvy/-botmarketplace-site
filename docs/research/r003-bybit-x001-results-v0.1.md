# R003-X001 Bybit Structural Replication — Results v0.1

**Project:** BotMarketplace / botmarketplace.store  
**Date:** 2026-09-10  
**Status:** independent venue structural replication complete  
**Protocol:** `docs/research/r003-bybit-x001-structural-replication-protocol-v0.1.md`

## 1. Formal conclusion

> **STRUCTURAL_SIGNAL_MIXED**

Data gate: **PASS**.

Crisis financing diagnostic: **CRISIS_FINANCING_COMPATIBLE**.

Under the prospectively frozen gate, R003-X001 does **not** qualify for automatic promotion to Bybit X002 because the largest positive completed calendar year contributes more than the pre-specified 50% ceiling.

## 2. Data quality

- Venue/product: Bybit BTCUSDT LinearPerpetual.
- Instrument launch metadata: 2020-03-15 UTC.
- Retained funding history: 2020-03-25 16:00 UTC through 2026-09-10 08:00 UTC.
- Funding observations: 7,080.
- Observed funding cadence: exact 8h throughout retained history.
- Bybit daily BTC index rows: 2,360 with 100% daily coverage and 1-day maximum gap.
- Only one funding row lacks causal daily index state.

## 3. Structural metrics

| Slice | Simple funding sum | Descriptive compounded | Positive events | Median rolling 365d | Positive 365d share | Latest 365d | Worst 30d |
|---|---:|---:|---:|---:|---:|---:|---:|
| FULL_AVAILABLE | 83.02% | 129.29% | 83.83% | 9.46% | 100.00% | 2.83% | -1.45% |
| PRIMARY_FULL_YEARS | 68.81% | 98.94% | 83.03% | 7.46% | 100.00% | 2.83% | -1.00% |
| PRE_2023 | 41.24% | 51.01% | 81.60% | 10.77% | 100.00% | 2.95% | -1.00% |
| POST_2023 | 27.57% | 31.74% | 83.81% | 7.68% | 100.00% | 2.83% | -0.16% |

## 4. Calendar-year concentration

Completed full years used by the concentration gate are 2021-2025.

- 2021: +38.30%
- 2022: +2.95%
- 2023: +8.88%
- 2024: +12.02%
- 2025: +5.12%

All five completed full years are positive, but 2021 contributes approximately **56.94%** of the sum of positive completed-year funding returns.

The frozen ceiling is <50%, so this single gate fails.

This is the only failed structural check. The gate must not be relaxed after observing the result.

## 5. Crisis-state diagnostic

For Bybit index drawdowns >=35%:

- weighted mean funding rate remains positive: ~4.25e-05 per event;
- representative deep-bucket median remains positive: ~7.22e-05;
- positive funding-event share ~78.41%.

Thus the frozen crisis diagnostic is `CRISIS_FINANCING_COMPATIBLE`, but this remains an average historical classification, not a guarantee of contemporaneous crisis funding.

## 6. Comparison with Binance R003-E001

The independent venue result is economically very similar in aggregate to Binance:

- Bybit FULL_AVAILABLE simple funding sum ~83.02% vs Binance ~80.54%;
- Bybit POST_2023 ~27.57% vs Binance ~26.84%;
- Bybit rolling-365d windows are 100% positive, as on Binance;
- Bybit crisis-state average funding is also positive.

This materially strengthens the qualitative hypothesis that positive BTC perpetual funding carry is not purely a Binance-specific artifact.

However the pre-specified Bybit gate still classifies the result as MIXED because the completed-year concentration rule fails. The independent replication therefore supports portability of the mechanism but does not satisfy the full promotion rule.

## 7. Research decision

Do **not** advance directly to Bybit X002 under the frozen X001 protocol.

Do **not** rescue the result by:

- removing 2021;
- changing the 50% concentration ceiling;
- changing the first-full-year convention;
- selecting another venue;
- adding a funding threshold or leverage.

R003 remains active through its already-frozen Binance forward E003 record. The next separate falsification priority is unchanged-rule R009 on ETH, while forward clocks continue.

## 8. Evidence status

This is an independent-venue structural replication only. It is not an executable strategy pass, OOS pass, demo pass or live recommendation.
