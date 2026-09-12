# SC001-E002 Pre-Test Freeze v0.1

Status: **FROZEN BEFORE FEATURE/RETURN CALCULATION**  
Experiment ID: `SC001-E002`  
Name: **Aggressive Trade-Flow Continuation Screen**

## 1. Scope

E002 is a predictive feature screen on frozen DEV-DISCOVERY only. It is **not** a strategy backtest, not an execution model, and not a profitability claim.

Allowed source data:
- B01: 2023-Q2, 5 frozen days;
- B02: 2023-Q3, 5 frozen days;
- B03: 2023-Q4, 5 frozen days.

Total: 15 frozen days.

Forbidden source data:
- B04/B05 DEV-CONFIRMATION;
- formal Validation;
- Final;
- qualification-only dates;
- any additional day chosen after seeing E002 results.

## 2. Feature

For each non-overlapping 5-second bucket `[t-5s, t)`:

`TFI_5s(t) = sum(sign_i * price_i * quantity_i) / sum(price_i * quantity_i)`

Aggressor sign:
- `is_buyer_maker = false` -> buyer taker -> `+1`;
- `is_buyer_maker = true` -> seller taker -> `-1`.

No raw underlying-trade-ID count is used.

## 3. Decision grid

Decision times occur every 5 seconds at the right edge of a completed 5-second bucket.

The signal uses only trades with timestamps strictly before decision time `t` and inside `[t-5s, t)`.

No overlapping 1-second decision grid is used.

## 4. Future response label

Primary latency: **100 ms**.

At each decision time `t`:
- entry reference price = first observed transaction price at or after `t + 100ms`;
- exit reference price = first observed transaction price at or after `t + 5100ms`;
- response = `log(exit / entry) * 10,000` basis points.

This is named **transaction-price response**, never execution P&L.

Stress latency: **250 ms** with identical 5-second response horizon.

Diagnostic latency: **500 ms** with identical 5-second response horizon.

No zero-latency result is permitted.

## 5. Primary hypothesis

Higher 5-second aggressive signed-notional imbalance predicts same-direction next-5-second transaction-price response.

Primary daily statistic:

`Spearman(TFI_5s, future_response_5s_at_100ms)`.

Expected sign: positive.

## 6. Daily diagnostics

For each day and each frozen latency calculate:
- number of valid 5-second decisions;
- Spearman correlation;
- mean response bps;
- median response bps;
- bottom score decile mean response;
- top score decile mean response;
- top-minus-bottom decile spread;
- directional hit rate across top/bottom deciles.

Deciles are used only as an effect-size diagnostic. They are not a live trading threshold and may not be promoted post hoc into an E002 strategy rule.

## 7. Primary inference unit

The UTC day is the inferential block.

Individual 5-second observations are not treated as IID evidence for the primary hypothesis.

Primary exact sign gate:
- at least **12 of 15** daily Spearman correlations must be > 0.

Under a 50/50 sign null, `P[X >= 12; n=15,p=0.5] = 0.017578125` one-sided.

## 8. Mandatory gates

E002 primary-association gates:
1. 100ms positive daily Spearman count >= 12/15;
2. median 100ms daily Spearman > 0;
3. median 100ms daily Spearman > 0 in each quarter 2023-Q2, Q3, Q4;
4. event-day median 100ms Spearman > 0;
5. ordinary-day median 100ms Spearman > 0;
6. 100ms extreme-decile spread positive on >= 10/15 days;
7. median 100ms extreme-decile spread > 0.

Stress-latency gates:
8. 250ms positive daily Spearman count >= 10/15;
9. median 250ms daily Spearman > 0.

500ms latency is diagnostic only and cannot rescue a failed primary/stress result.

## 9. Status mapping

- `PROMISING_SCREEN`: all gates 1-9 pass.
- `WEAK`: gates 1-7 pass, but gate 8 or 9 fails.
- `FAIL`: any of gates 1-7 fails.

No E002 outcome may be called `ROBUST_HISTORICAL_CANDIDATE` or `ADVANCE_TO_FORWARD`.

## 10. Multiple-testing freeze

E002 contains exactly one primary parameterization:
- lookback: 5s;
- grid: 5s;
- horizon: 5s;
- direction: continuation;
- primary latency: 100ms.

There is no sweep over:
- 1s/2s/10s windows;
- reversal vs continuation;
- thresholds;
- event exclusions;
- weekdays/weekends;
- volatility regimes;
- sides;
- capital sizes.

Any material change after results requires a new experiment ID.

## 11. Data-integrity requirements

Before E002 uses any archive it must verify:
- source batch report exists and is PASS;
- batch manifest exists and is PASS;
- source batch did not calculate strategy P&L;
- source batch did not access Validation/Final;
- frozen calendar SHA matches;
- archive exists locally;
- archive byte size matches manifest;
- archive SHA256 matches manifest.

If any check fails, E002 stops with ERROR; the date is not silently dropped.

## 12. Cross-venue boundary

E002 uses Binance aggTrades only to test whether the trade-flow feature family deserves further work.

A positive E002 does **not** authorize execution on OKX and does not establish cross-venue latency alpha.

If E002 passes, a later experiment must qualify the feature on same-venue data before any OKX execution claim.

## 13. Economic boundary

E002 deliberately does not include:
- spread;
- L2 depth;
- taker fees;
- maker fills;
- queue position;
- capital sizing;
- order-size discreteness.

Therefore E002 cannot establish net edge per trade after costs.

## 14. Anti-rescue rule

After E002 is run, the following are forbidden under the same experiment ID:
- changing 5s to another window/horizon;
- flipping continuation to reversal;
- selecting only successful event classes or ordinary days;
- excluding losing dates;
- changing 100ms/250ms gates;
- choosing a post-hoc TFI threshold;
- opening B04/B05 and then retuning E002.

If E002 fails, the failure is retained. A different economic mechanism becomes a new experiment ID.
