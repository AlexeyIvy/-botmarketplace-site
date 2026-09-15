# SC001-E006 — SPOT/SWAP Synchronization-Feasibility Audit Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN DATA-ONLY / NO-ALPHA PROTOCOL**

Parent planning document:

`docs/research/sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.2.md`

## 1. Purpose

Establish whether the already-qualified OKX `BTC-USDT` SPOT and `BTC-USDT-SWAP` March-2024 trade tapes can be aligned causally and deterministically at a common clock without calculating any relative price, basis, convergence, return or P&L.

This is a data-feasibility audit only. It does not authorize E006 alpha.

## 2. Inputs

SPOT:

- local qualified archive bodies from `SC001_E006_SPOT_FEASIBILITY/archives`;
- required terminal upstream status: `E006_SPOT_BODY_INTEGRITY_PASS`;
- labels used: 2024-03-01..21 only.

SWAP:

- already-qualified local `BTC-USDT-SWAP` March archives from `SC001_E003_OKX_MARCH_TRADES/archives`;
- required upstream source-stage status: `PASS`;
- only labels 2024-03-01..21 may be read for this audit.

Target UTC audit days:

- 2024-03-01..20.

2024-03-21 remains boundary-neighbor only and permanently excluded from E006 performance.

No network acquisition is permitted.

## 3. Price firewall

The synchronization implementation must not calculate or export:

- SPOT or SWAP prices;
- price ratios or differences;
- basis;
- convergence;
- signed trade direction features;
- future response;
- returns;
- P&L.

The parser may validate row width/instrument/timestamp/trade-ID and ignore price/size/side fields for synchronization calculations.

## 4. UTC reconstruction

For each target UTC day D and for each leg independently:

- read archive labels D and D+1;
- admit only target-instrument rows with timestamp in `[D 00:00:00.000, D+1 00:00:00.000)` UTC;
- require nondecreasing admitted timestamps;
- require zero duplicate/backward trade IDs;
- preserve duplicate timestamps; no deduplication;
- require at least one admitted row in every UTC minute.

The reconstruction must be deterministic across repeated runs.

## 5. Causal common-clock audit

Audit grid: exact one-second UTC boundaries strictly inside each target day:

`00:00:01, 00:00:02, ..., 23:59:59`.

For each boundary `t`, separately for SPOT and SWAP select the timestamp of the last admitted trade **strictly before** `t`.

No trade at timestamp `>= t` may be used.

For each grid point, calculate timestamps only:

- `spot_age_ms = t - last_spot_trade_ts`;
- `swap_age_ms = t - last_swap_trade_ts`;
- `max_leg_age_ms = max(spot_age_ms, swap_age_ms)`;
- `leg_timestamp_skew_ms = abs(last_spot_trade_ts - last_swap_trade_ts)`.

Do not carry observations across a UTC-day boundary.

## 6. Structural diagnostics

For each day and pooled over all 20 days report:

- total one-second grid points;
- points with both causal prior trades available;
- causal-pair availability share;
- SPOT age p50/p95/p99/max;
- SWAP age p50/p95/p99/max;
- max-leg-age p50/p95/p99/max;
- timestamp-skew p50/p95/p99/max;
- share of grid points where both legs have age <= 100 ms;
- <= 250 ms;
- <= 500 ms;
- <= 1,000 ms;
- <= 5,000 ms.

These are data-availability facts only and may not be interpreted as alpha.

## 7. Feasibility gates

Terminal `E006_SYNC_AUDIT_PASS` requires all of:

1. upstream SPOT body status exactly `E006_SPOT_BODY_INTEGRITY_PASS`;
2. upstream SWAP source stage exactly `PASS` with no Q2/Validation/Final/alpha/P&L access flags;
3. exact required local archive identities exist for both legs for labels 2024-03-01..21;
4. all 20 UTC target days reconstruct on both legs with 1,440/1,440 minute coverage;
5. zero admitted timestamp reversals and zero duplicate/backward trade IDs;
6. causal prior trade available on both legs for at least 99.99% of audited one-second boundaries;
7. pooled share with both leg ages <= 1,000 ms >= 99.0%;
8. pooled share with both leg ages <= 5,000 ms >= 99.9%;
9. pooled p99 of `max_leg_age_ms` <= 1,000 ms;
10. no forbidden price/basis/return/P&L output exists;
11. no labels after 2024-03-21 and no L2/Q2/Validation/Final access.

Any failure yields `E006_SYNC_AUDIT_REVIEW`. It does not authorize changing source dates or opening protected data.

## 8. Interpretation boundary

A PASS means only that a causal paired trade-tape experiment is technically feasible on the qualified Discovery data.

A PASS does **not** select:

- the future E006 evaluation grid;
- a staleness cutoff;
- a basis formula;
- a baseline/lookback;
- a shock threshold;
- an entry sign;
- an exit rule;
- a holding period;
- an economics hurdle.

Those items require a separate final financial/mathematical/programming audit and must be frozen before any E006 price comparison or alpha output.

## 9. Firewalls

Throughout this stage:

- basis calculated = false;
- returns calculated = false;
- P&L calculated = false;
- SPOT/SWAP price comparison = false;
- L2 accessed = false;
- Q2 accessed = false;
- Validation/Final accessed = false.

## 10. Next step after PASS

Only after `E006_SYNC_AUDIT_PASS` may the project perform the final pre-alpha financial/mathematical audit and freeze the exact executable E006 protocol.

No alpha is authorized directly by this synchronization PASS.
