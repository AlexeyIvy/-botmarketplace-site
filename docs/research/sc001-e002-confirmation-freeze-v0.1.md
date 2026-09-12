# SC001-E002 DEV-Confirmation Freeze v0.1

Status: **FROZEN BEFORE DEV-CONFIRMATION FEATURE ACCESS**  
Parent experiment: `SC001-E002 — Aggressive Trade-Flow Continuation Screen`

## 1. Purpose

This protocol freezes the one-time internal chronological confirmation of E002 on the previously reserved DEV-CONFIRMATION layer.

The confirmation is still a predictive feature test. It is not an executable strategy backtest and not a profitability claim.

## 2. Frozen source days

Only the 10 dates already frozen in `SC001-DATA-A002-PREFLIGHT` and the A002 Development Firewall are allowed.

### 2024-Q1 / B04
- 2024-01-05 — NFP
- 2024-01-14 — ordinary weekend
- 2024-01-31 — FOMC
- 2024-02-12 — ordinary weekday
- 2024-02-13 — CPI

### 2024-Q2 / B05
- 2024-04-10 — CPI
- 2024-04-20 — ordinary weekend
- 2024-05-01 — FOMC
- 2024-06-07 — NFP
- 2024-06-27 — ordinary weekday

No additional date may be substituted because of availability, volatility, profitability, or apparent signal strength.

## 3. Data-access sequence

1. Acquire and integrity-qualify all 10 B04/B05 aggTrades days with no E002 features and no P&L.
2. Require all 10 days to pass the same data-integrity family used in B01-B03.
3. Only after all 10 pass, run the E002 confirmation engine once on the combined 10-day set.
4. Do not inspect or report B04-only feature results before B05 is also qualified.

If a day fails for objective data-integrity reasons, stop with `ERROR/REVIEW`; do not replace it and do not compute a reduced-sample confirmation without a separately versioned protocol.

## 4. Feature and label — unchanged from E002

For every non-overlapping 5-second bucket `[t-5s,t)`:

`TFI_5s(t) = sum(sign_i * price_i * quantity_i) / sum(price_i * quantity_i)`

Aggressor sign:
- `is_buyer_maker=false` -> buyer taker -> `+1`;
- `is_buyer_maker=true` -> seller taker -> `-1`.

Decision grid: every 5 seconds at the right edge of the completed bucket.

Primary response:
- entry reference = first transaction price at or after `t+100ms`;
- exit reference = first transaction price at or after `t+5100ms`;
- response = `log(exit/entry)*10000` bps.

Stress response: same construction at 250 ms.

Diagnostic response: same construction at 500 ms.

No zero-latency result is permitted.

## 5. Primary daily statistic

`Spearman(TFI_5s, future_5s_transaction_price_response)`.

Expected sign: positive.

The UTC day is the inferential block. Individual 5-second observations are not treated as IID primary evidence.

## 6. Frozen discovery reference

Discovery median daily Spearman at 100 ms:

`0.12936691569403583`

Frozen effect-retention threshold (50%):

`0.06468345784701792`

This reference is frozen before DEV-CONFIRMATION is opened.

## 7. Primary and robustness gates

### 100 ms primary
1. positive daily Spearman count >= 9/10;
2. median daily Spearman > 0;
3. median daily Spearman >= `0.06468345784701792`;
4. 2024-Q1 median daily Spearman > 0;
5. 2024-Q2 median daily Spearman > 0;
6. event-day median daily Spearman > 0;
7. ordinary-day median daily Spearman > 0;
8. positive extreme-decile spread on >= 8/10 days;
9. median extreme-decile spread > 0.

### 250 ms stress
10. positive daily Spearman count >= 8/10;
11. median daily Spearman > 0.

500 ms is diagnostic only and cannot rescue a failed primary/stress result.

## 8. Exact sign-test references

For n=10 under a 50/50 sign null:
- >=8 positive: `0.0546875` one-sided;
- >=9 positive: `0.0107421875` one-sided;
- 10 positive: `0.0009765625`.

The primary count gate is >=9/10.

## 9. Verdict mapping

- `CONFIRMATION_PASS`: all gates 1-11 pass.
- `CONFIRMATION_WEAK`: gates 1-2 pass but at least one of gates 3-11 fails.
- `CONFIRMATION_FAIL`: gate 1 or gate 2 fails.

If `CONFIRMATION_PASS`, E002 remains a `PROMISING_SCREEN` with internal chronological confirmation. It does not become `ROBUST_HISTORICAL_CANDIDATE`.

## 10. Anti-rescue / multiple-testing rule

Under this confirmation ID there is exactly one parameterization:
- lookback 5s;
- grid 5s;
- horizon 5s;
- continuation direction;
- primary latency 100ms;
- stress latency 250ms;
- diagnostic latency 500ms.

Forbidden after seeing confirmation output:
- new windows/horizons;
- threshold tuning;
- selecting one side only;
- event exclusions;
- weekday/weekend exclusions;
- dropping dates because of weak signal;
- relaxing confirmation gates;
- opening formal Validation and retuning.

Any material change requires a new experiment ID and cannot overwrite this verdict.

## 11. Economic boundary

Confirmation still excludes:
- observed bid/ask spread;
- executable L2 depth;
- taker fees;
- market impact beyond transaction-price response;
- maker queue assumptions;
- order-size discreteness;
- capital sizing.

Therefore even `CONFIRMATION_PASS` is not evidence of positive net edge after costs.

## 12. Promotion rule

If confirmation passes, the next research stage is same-venue microstructure qualification: prove that the signal or an economically equivalent same-venue feature exists on data compatible with the venue where L2 execution will be simulated, then evaluate conservative taker economics using the already frozen latency/depth framework.

If confirmation is weak or fails, do not rescue E002 by tuning on B04/B05.