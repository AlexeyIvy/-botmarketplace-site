# SC001 — B13-C S0 Simple Post-Liquidation Reversal Sentinel Protocol v0.1

Date: 2026-09-26  
Status: **FROZEN BEFORE ANY B13-C PRICE/RETURN OUTCOME ACCESS**  
Scope: `SCALPING RESEARCH / SC001 / B13-C / S0`

## 1. Purpose

Test one simple, low-parameter hypothesis using the already protected prospective explicit liquidation stream:

`forced-liquidation burst ends -> short-horizon partial reversal`

This is an information/headroom sentinel, not Confirmation and not final PnL.

No B13-C post-event return has been inspected before this freeze.

## 2. Frozen universe

Use all 12 collector symbols without substitution:

BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, ORDIUSDT, FILUSDT, UNIUSDT, XRPUSDT, LTCUSDT, OPUSDT, BCHUSDT, SUIUSDT.

No symbol ranking or winner-only subset is allowed.

## 3. Frozen protected calibration interval

Event rows admitted only when liquidation timestamp is within:

`2026-09-19T06:47:38.969Z <= T <= 2026-09-26T21:05:32.973Z`

This interval was fixed from the source-quality census before price outcomes were opened.

Complete UTC days used for day-consistency diagnostics:

`2026-09-20 .. 2026-09-25`

The partial start/end days remain in pooled cluster statistics but are not complete-day consistency units.

## 4. Analytical event identity

Use the collector's deterministic event fingerprint.

For S0 analysis only:
- exact repeated fingerprints are treated as one analytical liquidation event;
- retain the earliest received copy;
- this does not mutate or rewrite protected raw collection.

No size threshold or size weighting is used.

## 5. Per-symbol cluster rule

Sort distinct events by `liquidation_ts_ms` within each symbol.

A cluster continues while the gap between consecutive events is <= 5,000 ms.

A new cluster begins after >5,000 ms without an event.

The 5-second inactivity rule is fixed before inspecting event timing distributions or returns.

Minimum cluster content:

`>=3 distinct liquidation fingerprints`

Direction purity:

all events in an admitted S0 cluster must have the same frozen collector semantic:
- LONG_LIQUIDATED; or
- SHORT_LIQUIDATED.

Mixed-side clusters are excluded from S0. No majority threshold is allowed.

## 6. Gap censoring

A cluster is not eligible when a recorded liquidation-source connection gap or process-restart gap intersects:

`[cluster_start - 5s, cluster_end + 5s]`

Reason: missing events could alter cluster membership or close time.

Do not impute absent liquidation events through gaps.

## 7. Price source

Use official Bybit public historical trade archives for the exact same USDT perpetual symbol:

`public.bybit.com/trading/SYMBOL/SYMBOLYYYY-MM-DD.csv.gz`

Archive body/schema must pass a separate source qualification before outcome calculation.

Do not substitute:
- candles;
- another exchange;
- spot prices;
- mark/index prices;
- carried-forward prices.

Do not drop a frozen symbol because its archive arrives later. If required files are unavailable:

`B13C_S0_DEFER_PRICE_SOURCE`

## 8. Entry/exit price anchors

Let `E` be cluster end timestamp.

Entry bucket:

`[E+1s, E+2s)`

Exit bucket:

`[E+31s, E+32s)`

Within each bucket use the chronologically last real Bybit public trade.

Both buckets must contain at least one real trade.

No carry-forward.  
No interpolation.  
No alternate horizon.

This creates approximately 30 seconds between the frozen entry and exit reference buckets while allowing one second after observed cluster completion before entry measurement.

## 9. Frozen directional hypothesis

For a pure LONG_LIQUIDATED cluster:

expected reversal direction = positive return.

For a pure SHORT_LIQUIDATED cluster:

expected reversal direction = negative return.

Define:

`signed_reversal_bps = reversal_sign * 10000 * ln(P_exit / P_entry)`

where:
- reversal_sign = +1 for LONG_LIQUIDATED;
- reversal_sign = -1 for SHORT_LIQUIDATED.

No sign flip may be selected after outcome.

## 10. Primary sample unit

Primary unit:

`SYMBOL x LIQUIDATION_CLUSTER`

Raw liquidation rows are not IID samples.

Report:
- eligible cluster count;
- valid-price cluster count;
- median signed_reversal_bps;
- p25 / p75;
- positive-cluster share;
- complete-day median signed return for Sep20-Sep25;
- count of complete days with positive median.

Do not report per-symbol performance ranking in S0.

## 11. Frozen gross-headroom sentinel

Minimum valid-price sample:

`100 clusters`

S0 SURVIVE requires all:
- valid clusters >=100;
- pooled median signed_reversal_bps >=30 bps;
- positive-cluster share >=55%;
- at least 4 of 6 complete UTC days have positive median signed reversal.

Then:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_SURVIVE`

If valid clusters >=100 and any headroom/breadth gate fails:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`

If valid clusters <100 or required source files are incomplete:

`B13C_S0_DEFER_SAMPLE`

The 30 bps gate is deliberately a gross-headroom screen, not a final profitability threshold.

## 12. Cost boundary

Current public Bybit documentation lists non-VIP perpetual/futures taker fees at 0.055% per fill, but account/region-specific rates may differ.

Therefore S0 does not claim profitability.

If S0 SURVIVES:
1. freeze account-applicable fee semantics separately;
2. add spread/slippage/execution reserve;
3. perform an execution feasibility preflight;
4. use fresh post-freeze liquidation events for forward confirmation.

## 13. Anti-rescue rules

If S0 rejects, do not rescue on the same protected interval by:
- selecting only large liquidations;
- searching size thresholds;
- changing the 5-second cluster gap;
- changing minimum event count;
- allowing mixed-side majority rules;
- changing entry delay;
- scanning 5s/10s/60s/5m horizons;
- ranking/selecting winning symbols.

Any such architecture requires a new protocol and fresh post-definition evidence.

## 14. Source availability gate

Before any S0 price computation:
- verify all required daily public trade archives exist for all 12 frozen symbols over the admitted interval;
- freeze file identities/hashes;
- validate CSV schema and timestamps without calculating returns.

Only after source qualification may a price-bearing S0 bundle be sealed.
