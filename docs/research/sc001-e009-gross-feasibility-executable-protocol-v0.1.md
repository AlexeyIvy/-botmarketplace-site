# SC001-E009 — Gross Feasibility Executable Protocol v0.1

Date: 2026-09-17  
Status: **FROZEN BEFORE E009 SEPTEMBER MARKET-BODY ACCESS**

Parent plan: `docs/research/sc001-e009-volatility-normalized-displacement-reversal-research-plan-v0.1.md`

## 1. Scope

Test only the frozen E009 v0.1 volatility-normalized extreme-displacement reversal mechanism on the eight frozen Discovery assets and September 2024 Discovery period.

This stage is gross-only. It does not claim executable net PnL and does not use L2, historical lot/tick/contract specs, exact fee PnL, asset holdout or October Confirmation.

## 2. Discovery assets and time

Assets exactly:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH — OKX `*-USDT-SWAP`.

Performance dates exactly:

`2024-09-01..2024-09-14` UTC.

Boundary archive labels may include `2024-08-31` and `2024-09-15` only as objectively required for UTC reconstruction/warm-up/late-exit source access.

Asset holdout SOL/FIL/LTC/SUI remains CLOSED.

October 2024 Confirmation remains CLOSED.

## 3. Signal semantics

Grid: exact 5-second UTC boundaries.

For boundary t:

- current VWAP `C_t`: `[t-5s,t)`;
- anchor VWAP `A_t`: `[t-65s,t-60s)`;
- `r60_t = ln(C_t/A_t)`.

Consecutive valid 5-second VWAP buckets define 5-second log returns.

Robust scale uses the prior 30 minutes of causal 5-second returns, with at least 240 valid observations and no future access.

`MAD5_t = median(|r5 - median(r5)|)`

`sigma60_t = 1.4826 * MAD5_t * sqrt(12)`

`Z_t = r60_t / sigma60_t`

Require finite positive sigma. Missing/sparse buckets are invalid and never forward-filled.

## 4. Trigger

One frozen threshold:

`|Z_t| >= 3.0`

Trigger only on strict crossing from previous valid `|Z| < 3.0`.

- positive Z -> SHORT reversal;
- negative Z -> LONG reversal.

No alternative threshold/grid is authorized.

## 5. Target/state/timing

Freeze:

- 50% arithmetic retracement between frozen anchor and trigger current VWAP;
- primary latency 500 ms;
- stress latencies 1000 ms and 2000 ms;
- execution-proxy tolerance 5000 ms;
- max hold 10 minutes;
- one pending/open position maximum per instrument;
- max 4 accepted entry decisions per UTC day per instrument;
- 10-minute cooldown after completed exit;
- no new entry decision after 23:49:00 UTC;
- no overnight carry.

Stress replays reuse primary accepted events/frozen exit-decision semantics; they do not rediscover better triggers.

## 6. Gross edge

For a completed event:

`gross_edge_bps = direction * 10000 * (exit_price/entry_price - 1)`

Trade proxies are only a gross-feasibility approximation. No discrete contract PnL or exact historical net PnL is authorized.

## 7. Cross-asset denominator

All eight Discovery instruments stay in equal-weight and median-instrument denominators.

If an instrument has zero completed events, its instrument mean for equal-weight/median aggregation is `0 bps` rather than being silently removed.

Pooled event-level statistics use completed events only.

## 8. Frozen PASS gates

Exact `E009_GROSS_FEASIBILITY_PASS` requires all:

- all 8 Discovery assets attempted;
- at least 6 assets active;
- at least 4 assets with >=5 completed events;
- pooled completed events >=40;
- equal-weight mean instrument gross edge >=20 bps;
- median instrument mean gross edge >=15 bps;
- at least 5/8 instruments with positive mean gross edge;
- pooled 10% trimmed mean >=15 bps;
- pooled median >=10 bps;
- 1000 ms equal-weight mean >=15 bps;
- 2000 ms equal-weight mean >=10 bps;
- top instrument absolute gross-contribution share <=0.35.

These are intentionally the same economic/breadth hurdles used by E007R1 gross feasibility so that E009 tests the normalization change rather than receiving easier economics.

Any mandatory failure yields exact:

`E009_GROSS_FEASIBILITY_FAIL`

and blocks E009 asset holdout, October Confirmation, historical execution-spec reconstruction for promotion, L2 and net-PnL engineering.

## 9. Required diagnostics

Per instrument:

- candidate count;
- accepted decisions;
- completed events;
- active days;
- completion rate;
- mean/median/10% trimmed gross bps;
- positive event/day share;
- long/short count and means;
- 500/1000/2000 ms diagnostics;
- valid normalized-observation count/coverage;
- trigger |Z| distribution diagnostics.

Aggregate:

- equal-weight/median instrument means;
- positive-instrument breadth;
- pooled robust metrics;
- event/contribution concentration;
- calendar-day breadth.

## 10. Firewalls

Do not:

- read July E007R1 outcomes to tune E009 parameters beyond the already frozen hypothesis generation recorded before this protocol;
- change z=3, 30-minute lookback, MAD formula, target, hold, latency, cap or cooldown after September output;
- open asset holdout or October Confirmation before exact PASS;
- add TFI/flow/compression/basis features;
- access L2 in this gross screen;
- claim trade-proxy gross bps are executable net PnL.
