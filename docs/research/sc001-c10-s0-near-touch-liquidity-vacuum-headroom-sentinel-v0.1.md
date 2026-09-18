# SC001 — C10-S0 One-Sided Near-Touch Liquidity-Vacuum Structural Sentinel v0.1

Date: 2026-09-18
Status: **FROZEN BEFORE FIRST C10 L2 OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c10-d0-local-btc-l2-eligibility-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.13.json`;
- `docs/research/sc001-c7-c10-no-alpha-data-structural-feasibility-audit-v0.1.md`.

## 1. Candidate identity

Candidate:

`C10`

Mechanism:

`ONE-SIDED NEAR-TOUCH L2 LIQUIDITY VACUUM`

C10 is not C5 + L2.

C5 aggressive-flow labels, C5 event timestamps and RB005 are excluded from the base mechanism.

## 2. Purpose

Cheapest outcome-bearing structural test:

> Do objectively defined one-sided collapses in near-touch visible depth precede enough short-horizon midquote movement to justify later directional/execution research?

This is Selection/Calibration only.

It does not model fills, queue position, fees or PnL.

## 3. Frozen source

Venue/instrument:

- OKX BTC-USDT-SWAP.

Exact pilot body:

`BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz`

Exact byte size:

`601,976,188`

Pilot selection rule:

`ordinary weekday in the already-qualified four-day Q1 BTC L2 set`.

## 4. Frozen book reconstruction

Use the qualified OKX L2 semantics:

- JSONL tar.gz;
- action in `snapshot/update`;
- first action snapshot;
- apply updates causally in timestamp order;
- duplicate prices within one record invalid;
- delete missing level invalid;
- crossed/empty reconstructed book invalid.

No trade tape is used.

## 5. Frozen 1-second state sampling

UTC grid:

- every whole second from 00:00:00 through 23:59:59.

At grid second `s` use the most recent fully applied L2 state with:

`last_l2_timestamp <= grid_boundary`

and require:

`grid_boundary - last_l2_timestamp <= 1000 ms`.

If stale by more than 1000 ms, that second is invalid/missing.

No future interpolation.

## 6. Frozen book features

At each valid sampled second:

- best bid;
- best ask;
- midquote = `(best_bid + best_ask)/2`;
- near-touch bid depth = sum of displayed sizes at best 5 bid price levels;
- near-touch ask depth = sum of displayed sizes at best 5 ask price levels.

Exactly 5 levels.

No order-count, trade-flow or C5 variable enters the base event.

## 7. Frozen causal depth baseline

For each current valid second `s` and each side separately:

look back over prior wall-clock interval:

`[s-60 seconds, s)`

using valid sampled seconds only.

Require at least:

`45`

prior valid observations.

Reference depth:

`median(side_near_touch_depth over prior 60 seconds)`

Current second is excluded.

## 8. Frozen liquidity-vacuum event

Define ratios:

`bid_depth_ratio = current_bid_depth / prior_bid_depth_median`

`ask_depth_ratio = current_ask_depth / prior_ask_depth_median`

### Bid-side vacuum state

Require simultaneously:

- `bid_depth_ratio <= 1/3`;
- `ask_depth_ratio >= 2/3`.

### Ask-side vacuum state

Require simultaneously:

- `ask_depth_ratio <= 1/3`;
- `bid_depth_ratio >= 2/3`.

If neither or both conditions hold, state = NONE.

An event is counted only on **observable onset**:

- current second is BID_VACUUM or ASK_VACUUM;
- immediately previous UTC second is valid;
- previous second state = NONE.

This prevents persistent-vacuum seconds from being counted repeatedly.

## 9. Frozen future-move horizon

Primary horizon:

`5 seconds`

For an event at second `s`, require a valid sampled book at exact second:

`s + 5`.

Future absolute move:

`abs_move_5s_bps = 10000 * abs(ln(midquote[s+5] / midquote[s]))`

Directional diagnostic, not a survival gate:

- ASK_VACUUM predicted sign = +1;
- BID_VACUUM predicted sign = -1;

`signed_move_5s_bps = predicted_sign * 10000 * ln(midquote[s+5] / midquote[s])`

No side may be redefined after output.

## 10. Structural economic reference

If a later directional taker implementation were pursued:

- entry + exit = two structural fills;
- frozen taker reference = 5 bps/fill;
- fee-reference floor = 10 bps;
- structural gross move hurdle = `15 bps`.

S0 does not claim this is an exact executable cost model.

## 11. Data/sample gates

Require all:

- valid sampled seconds >= `80,000`;
- baseline-eligible sampled seconds >= `70,000`;
- evaluable vacuum events >= `50`;
- event UTC hours >= `8`;
- both BID_VACUUM and ASK_VACUUM event counts >= `10`.

If any fail:

`C10_S0_DEFER_SAMPLE`

No threshold/horizon relaxation.

## 12. Structural move-headroom gates

SURVIVE structural headroom only if all:

- events with `abs_move_5s_bps >=15` >= `10`;
- such >=15 bps events span >= `4` UTC hours;
- p90 `abs_move_5s_bps >=15 bps`;
- maximum `abs_move_5s_bps >=30 bps`.

Exact survive token:

`C10_S0_HEADROOM_SURVIVE`

If sample gates pass but any headroom gate fails:

`C10_S0_REJECT_HEADROOM`

## 13. Descriptive feature evidence

Always report separately:

- BID_VACUUM event count;
- ASK_VACUUM event count;
- p50/p90/p99 absolute 5s move;
- mean/median signed 5s move;
- positive signed-move share;
- per-side mean signed move;
- event-hour breadth.

These diagnostics do not change the strategy verdict and are not promotion evidence.

## 14. No-rescue rules

After output do not:

- change 5 levels;
- change 60-second baseline;
- change 45-observation minimum;
- loosen 1/3 or 2/3 depth ratios;
- change onset rule;
- change 5-second horizon;
- lower 15 bps structural hurdle;
- condition on C5/aggressive flow;
- select only bid or ask vacuum;
- add spread/microprice/volatility filters;
- select another day from the four known Q1 days.

A materially different L2 mechanism requires a new candidate/experiment ID.

## 15. Outputs

Strategy evidence:

`~/sc001_data/SC001_C10_S0_HEADROOM/c10_s0_strategy_evidence_v0_1.json`

Feature/building-block evidence:

`~/sc001_data/SC001_C10_S0_HEADROOM/c10_s0_feature_block_evidence_v0_1.json`

## 16. Firewalls

Must state:

- c5_labels_used = false;
- aggressive_flow_conditioning_used = false;
- fill_model_calculated = false;
- queue_model_calculated = false;
- fees_calculated = false;
- pnl_calculated = false;
- promotional_alpha_accessed = false.

## 17. Consequence

SURVIVE only justifies a later directional/replenishment/execution study.

REJECT means the exact frozen one-sided near-touch vacuum mechanism lacks raw 5-second move headroom on the frozen calibration day.

It does not imply all L2 state information is useless.
