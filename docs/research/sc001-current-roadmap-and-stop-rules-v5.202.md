# SC001 Current Roadmap and Stop Rules v5.202

Date: 2026-09-29
Status: **B15-P2 P0 PRICE EXPERIMENT PRE-REGISTERED / LIMITED PRICE FIREWALL AUTHORIZATION REQUIRED**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.201.md`

## 1. Pre-registration complete

The first B15-P2 price/outcome experiment has been designed and frozen **without reading price outcomes**.

Canonical specification:

`docs/research/sc001-b15p2-pre-registered-price-experiment-spec-v0.1.json`

SHA256:

`1dc79403307177c1f9785090fa6f31aac0322ccb10864c509846e8da415856a7`

Three-role design review:

`docs/research/sc001-b15p2-price-experiment-design-review-v0.1.md`

Causal event clock freeze:

`docs/research/sc001-b15p2-causal-event-clock-freeze-v0.1.json`

The frozen 94 events reduce to 37 unique delisting timestamps, with up to 5 simultaneous events.

## 2. P0 purpose

P0 is a **structural headroom sentinel**, not a PnL backtest.

Question:

Does absolute Bybit perpetual-vs-official-index basis converge more strongly during the mechanism-defined forced-close window than during an equal-length control window immediately before it?

Primary windows:

- control: T-55m -> T-30m;
- mechanism: T-30m -> T-5m.

The last 5 minutes are excluded from the primary sentinel to avoid terminal cancel/liquidity effects.

## 3. Exact registered data

If separately authorized, P0 may access only:

1. Bybit official `/v5/market/kline`
   - category = linear;
   - interval = 1;
   - exact frozen event symbol;
   - exact fully closed candles ending at T-55m, T-30m, T-5m;
   - close, volume, turnover.

2. Bybit official `/v5/market/index-price-kline`
   - category = linear;
   - interval = 1;
   - same symbol and three exact timestamps;
   - close only.

Derived:

`B(t)=10000*(perpetual_close/index_close-1)`

No other price source or fallback is allowed.

## 4. Primary metrics

`A(t)=|B(t)|`

`C_control=A(-55)-A(-30)`

`C_event=A(-30)-A(-5)`

`D=C_event-C_control`

Primary inference unit:

**delivery timestamp cluster**, not individual contract.

Primary estimator:

median cluster D.

Uncertainty:

10,000-replication delivery-cluster bootstrap, seed 1502, two-sided 90% percentile interval.

## 5. Pre-registered gates

### Source gate

Require:

- >= 90 eligible events;
- >= 35 eligible delivery clusters;
- >= 1 eligible cluster in every frozen delivery month.

Otherwise:

`DEFER_SOURCE_COVERAGE`

### Timing-specificity gate

Require all:

- median cluster D > 0;
- 90% bootstrap lower bound > 0;
- >= 60% eligible clusters have D > 0;
- monthly median D > 0 in >= 6 of 9 months.

Otherwise:

`REJECT_MECHANISM_TIMING_SPECIFICITY`

### Economic-scale gate

The frozen screening landmarks are:

- <= 11 bps median C_event -> `REJECT_STRUCTURAL_ECONOMIC_SCALE`;
- > 11 and < 30 bps -> `DEFER_COST_HEADROOM`;
- >= 30 bps plus timing-specificity PASS -> `PASS_TO_P1_EXECUTION_FEASIBILITY`.

These are screening thresholds, not PnL claims.

## 6. Contamination controls

New registry:

`docs/research/sc001-contamination-registry-v0.31.json`

Forbidden after outcome access:

- alternate horizon search;
- winner-symbol selection;
- basis threshold optimization;
- feature/indicator rescue;
- event removal based on outcome;
- switching to another venue/source because the official source is inconvenient.

A failed P0 is terminal for this frozen basis-convergence architecture on the 94-event evidence.

## 7. Still CLOSED

The current commit does **not** authorize:

- affected-contract price access;
- official index values;
- basis calculation;
- returns;
- PnL;
- L1/L2;
- individual trades;
- funding values;
- mark/premium/spot;
- external venues;
- trading.

## 8. Next authorization boundary

The next step requires explicit user authorization for only:

**B15-P2 P0 affected-contract 1m prices + official Bybit index 1m values + derived basis at the three frozen snapshots.**

Returns, PnL and execution simulation remain closed even if P0 is authorized.

## 9. Next state

`AWAIT_EXPLICIT_AUTHORIZATION_FOR_B15P2_P0_PRICE_INDEX_BASIS_ACCESS`
