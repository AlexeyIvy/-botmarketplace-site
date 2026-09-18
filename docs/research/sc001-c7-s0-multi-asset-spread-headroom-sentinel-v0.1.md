# SC001 — C7-S0 Multi-Asset Quoted-Spread Structural Headroom Sentinel v0.1

Date: 2026-09-18
Status: **FROZEN BEFORE FIRST C7 HISTORICAL SPREAD OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c7-d0-multi-asset-l2-metadata-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.14.json`;
- `docs/research/sc001-c7-c10-no-alpha-data-structural-feasibility-audit-v0.1.md`.

## 1. Candidate identity

Candidate:

`C7`

Mechanism:

`SPREAD-QUALIFIED NON-BTC PASSIVE/HYBRID MAKER UNIVERSE`

This is not an E008 BTC same-rule rescue.

## 2. Purpose

Cheap structural eligibility screen:

> Do any frozen non-BTC OKX markets exhibit quoted spreads that are large and persistent enough to leave conservative headroom before queue/fill modeling?

No maker fill, queue, adverse-selection outcome or PnL is calculated.

## 3. Frozen universe

Exactly:

- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

No asset may be added/dropped after spread outcomes.

## 4. Frozen calibration date

`2024-02-12 UTC`

All seven historical L2 bodies are nonpromotional Selection/Calibration.

## 5. Frozen temporal representation

For each asset:

- reconstruct historical L2 causally;
- sample at exact UTC 1-second boundaries;
- use most recent fully applied book state with timestamp <= boundary;
- require freshness <=1000 ms;
- no future interpolation.

## 6. Frozen quoted-spread statistic

At each valid second:

- best bid;
- best ask;
- mid = (bid + ask)/2;
- quoted_spread_bps = 10000 * (ask - bid) / mid.

No own-order placement, queue or fill model.

## 7. Frozen structural cost/reference hurdle

Prospective C7 eligibility architecture:

`maker entry + taker fail-safe exit`

Reference inherited from previously frozen E008 selection assumptions:

- maker fee reference = 2 bps;
- taker fee reference = 5 bps.

Prospectively add:

- adverse-selection/model reserve = 3 bps.

Frozen gross quoted-spread hurdle:

`10 bps`

This is a structural screening reserve only, not an exact historical account-tier fee claim.

## 8. Frozen persistence definition

A high-spread episode requires:

- quoted_spread_bps >=10;
- for at least 5 consecutive valid wall-clock seconds.

Count one episode on entry into such a qualifying run.

A new episode requires at least one valid second below 10 bps before re-arming.

## 9. Per-asset data gates

Require:

- valid sampled seconds >=80,000;
- valid UTC hours =24.

Failure makes that asset structurally ineligible but does not change the universe.

## 10. Per-asset spread-eligibility gates

An asset is C7 structurally eligible only if all:

- p75 quoted spread >=10 bps;
- share of valid seconds with spread >=10 bps >=0.20;
- persistent >=5s high-spread episodes >=100;
- persistent episodes span >=12 UTC hours.

## 11. Universe survival gate

C7-S0 survives only if:

- at least 2 of 7 frozen assets satisfy all per-asset spread-eligibility gates.

Exact survive token:

`C7_S0_SPREAD_HEADROOM_SURVIVE`

If all asset data gates are adequate but fewer than 2 assets qualify:

`C7_S0_REJECT_SPREAD_HEADROOM`

If fewer than 5/7 assets meet the data gates:

`C7_S0_DEFER_DATA_QUALITY`

## 12. Report diagnostics

Per asset report:

- valid sampled seconds;
- valid UTC hours;
- p50/p75/p90 quoted spread bps;
- share spread >=10 bps;
- high-spread persistent episode count;
- episode-hour breadth;
- data gate;
- structural eligibility gate.

Universe report:

- eligible asset count;
- eligible asset identities;
- terminal status.

Archive size is not a strategy criterion.

## 13. No-rescue rules

After output do not:

- lower 10 bps hurdle;
- lower 5s persistence;
- change p75/share/episode gates;
- select only one historical winner asset;
- replace universe;
- add BTC;
- change date;
- add queue/fill simulation;
- add E008 aggressive-flow logic;
- change to maker-maker architecture because hybrid screen fails.

A materially different maker mechanism requires a new ID.

## 14. Firewalls

Must remain false:

- maker_order_simulated;
- fill_model_calculated;
- queue_model_calculated;
- adverse_selection_outcome_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 15. Consequence

SURVIVE only authorizes a later exact fee/queue/adverse-selection research stage for the prospectively eligible multi-asset universe.

REJECT kills C7 before queue/fill modeling.
