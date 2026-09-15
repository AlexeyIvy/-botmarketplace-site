# SC001-E006 — Same-Venue Spot/Perpetual Basis Dislocation -> Convergence Research Plan v0.2

Date: 2026-09-15  
Status: **PLANNING DOCUMENT — NO E006 ALPHA AUTHORIZED**  
Supersedes: `sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.1.md`

## 1. Reason for v0.2

The metadata-only probe established that querying the March-2024 OKX `BTC-USDT` SPOT trade-history source for UTC day D returns archive labels D and D+1, consistent with the already-qualified non-UTC OKX packaging semantics used elsewhere in SC001.

Therefore reconstructing DEV-DISCOVERY UTC day `2024-03-20` requires archive label `2024-03-21`.

Because archive label `2024-03-21` physically contains data extending into March 21 UTC, treating March 21 as a later untouched Confirmation performance day would contaminate the protected boundary even if the Discovery parser admitted only March-20 rows.

This chronology correction is made before any E006 market-data body download, basis calculation, return calculation or P&L.

## 2. Corrected E006 chronology firewall

Frozen planning boundary for subsequent protocol design:

- DEV-DISCOVERY performance days: `2024-03-01..2024-03-20` inclusive;
- boundary-neighbor day: `2024-03-21` — **permanently excluded from E006 performance inference**;
- future one-time DEV-CONFIRMATION candidate days, only if later authorized by a frozen protocol after Discovery PASS: `2024-03-22..2024-03-30` inclusive;
- all 2024-Q2 bodies remain closed;
- formal Validation and Final remain closed.

Archive label `2024-03-21` may be acquired only because it is objectively required as the D+1 source neighbor for reconstructing March 20 UTC. Its March-21 UTC rows may not enter Discovery performance calculations.

## 3. Core hypothesis

A rare transient divergence between same-venue BTC spot and BTC perpetual prices may reflect short-lived derivatives-specific inventory pressure, forced flow, leverage demand or liquidity imbalance.

If the divergence subsequently converges, a paired relative-value trade may capture movement measured in many basis points while substantially reducing exposure to common BTC direction.

Initial pair:

- OKX `BTC-USDT` SPOT;
- OKX `BTC-USDT-SWAP` perpetual.

The intended edge is relative-price convergence, not BTC directional prediction.

## 4. Independence and history

E006 is a new mechanism family after terminal E001/E002-standalone/E003/E004 failures.

- E004 remains terminal `E004_DISCOVERY_FAIL`.
- E005 remains closed because its prerequisite — independently viable E004 — was not met.
- E006 does not rescue or retune E004.
- Base E006 must not use E002 TFI, E003 FLOW_IMPULSE or E004 compression state.

SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002.

## 5. Economics-first warning

A paired taker cycle requires four taker fills: two legs to open and two to close. Therefore the fee burden is materially larger than a single-instrument round trip before spread, depth, legging, funding/borrow and model error.

A several-bps convergence effect is automatically uninteresting. Before any L2 work, the future frozen gross-economics gates must demand substantial several-tens-of-bps headroom under an explicitly defined paired normalization.

Exact thresholds are not frozen by this planning document and may not be selected after E006 returns are observed.

## 6. Current data-only stage

Already qualified:

- March-2024 OKX `BTC-USDT-SWAP` trade archives.

New leg to qualify:

- OKX `BTC-USDT` SPOT historical trade archives.

Current allowed scope:

1. metadata-only full-label preflight for `2024-03-01..2024-03-21`;
2. verify exact official filenames/URLs and HEAD sizes;
3. determine expected aggregate storage footprint and disk feasibility;
4. only after metadata PASS may a separately frozen body-download/verification stage be run;
5. no basis, synchronized price statistic, convergence, return or P&L calculation;
6. no Confirmation SPOT labels beyond the required boundary label March 21;
7. no L2/Q2/Validation/Final.

## 7. Data-feasibility requirements before financial protocol freeze

The data stage must establish without alpha:

- exact archive identity and SHA256 after download;
- ZIP/CSV/schema validity;
- source timestamp/order semantics;
- Q006R-like D + D+1 UTC reconstruction for March 1..20;
- complete minute coverage and reported second-level coverage diagnostics;
- deterministic within-stream ordering;
- causal timestamp alignment feasibility between spot and swap;
- storage/runtime feasibility on the qualified VPS.

Any ambiguity => E006 data stage REVIEW/FAIL and alpha remains closed.

## 8. Mandatory financial freeze items after data PASS

Before first E006 alpha, freeze exactly:

- synchronized spot/swap causal price statistic;
- evaluation grid;
- basis formula and normalization;
- causal ordinary-basis baseline;
- dislocation trigger and tie semantics;
- tradable sign(s), including spot-borrow treatment if required;
- paired decision time;
- primary/stress latency;
- two-leg entry proxy and legging window;
- convergence/fixed exit and maximum hold;
- non-overlap and turnover cap;
- paired gross-edge normalization;
- both-leg completion definition;
- Discovery/Confirmation gates;
- robust median/trimmed/day/concentration/sign gates;
- small non-rescuing diagnostic neighborhood.

No parameter may be selected after observing E006 returns.

## 9. Stop rules

If data feasibility fails, stop/pause E006 without alpha.

If later frozen Discovery fails gross economics, E006 becomes terminal Discovery FAIL and Confirmation/L2 stay closed.

No rescue via lower/VIP fees, maker assumptions, post-hoc sign/day/hour selection, alternate synchronization, alternate baseline/lookback, alternate hold, or auxiliary E002/E003/E004 features.

## 10. Immediate next action

Run a metadata-only full-label SPOT preflight for archive labels `2024-03-01..2024-03-21`.

The preflight may record public metadata, exact filename/host/URL identity, HEAD size, aggregate expected bytes and local free disk only.

It must not download any ZIP body or calculate any E006 basis/return/P&L.
