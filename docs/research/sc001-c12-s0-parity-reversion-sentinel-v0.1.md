# SC001 — C12-S0 H1 Stablecoin Parity Dislocation/Reversion Sentinel v0.1

Date: 2026-09-18
Status: **FROZEN BEFORE FIRST C12 PEG OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c12-d2-v0.2-h1-archive-metadata-pass-result-v0.1.md`;
- `docs/research/sc001-c12-d1-spot-trade-semantics-pass-result-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.17.json`.

## 1. Purpose

Test whether direct USDC-USDT spot dislocations from 1.0000 are both frequent enough and sufficiently mean-reverting within 30 minutes to justify later execution modeling.

No local moving-average reference is used.

## 2. Frozen source window

Target UTC days:

`2025-01-01 through 2025-06-30`

Source support:

`2025-01-01 through 2025-07-01`

under qualified D+D1 SPOT semantics.

## 3. Frozen parity statistic

For every valid historical trade:

`peg_deviation_bps = 10000 * ln(USDCUSDT_trade_price / 1.0)`

The direct pair is treated as a stablecoin cross-parity state; deviations may reflect either USDC or USDT stress.

## 4. Frozen episode entry

An episode may arm only after observing a trade with:

`abs(peg_deviation_bps) <=10`

After arming, the first trade with:

`abs(peg_deviation_bps) >=30`

starts one dislocation episode.

No threshold grid.

No repeated entry while the episode remains active.

## 5. Frozen parity reversion outcome

Episode direction is the sign of entry deviation.

Success occurs at the first later trade within 30 minutes with:

`abs(peg_deviation_bps) <=10`.

If success does not occur by 30 minutes:

- use the chronologically last trade at or before the 30-minute deadline;
- require deadline staleness <=60 seconds;
- otherwise the episode is unevaluable.

Gross favorable reversion move:

`gross_reversion_bps = sign(entry_deviation) * 10000 * ln(entry_price / exit_price)`

This is not PnL.

## 6. Structural burden

Prospective pre-funded stablecoin inventory architecture:

- spot conversion entry;
- spot conversion exit;
- two structural fills;
- 10 bps total fee reference;
- 5 bps spread/slippage/model reserve;
- structural burden = `15 bps`.

No borrow assumption is needed if both stablecoin inventories are pre-funded.

## 7. Data gates

Require:

- at least `175` of 181 target UTC days contain valid reconstructed trades;
- all 6 target months represented.

Failure:

`C12_S0_DEFER_DATA_QUALITY`

## 8. Structural opportunity/reversion gates

SURVIVE only if all:

- evaluable dislocation episodes >= `12`;
- episodes span >= `6` distinct UTC dates;
- episodes span all `6` target months;
- parity-band success within 30m share >= `0.60`;
- median gross favorable reversion >= `15 bps`;
- p75 gross favorable reversion >= `20 bps`.

Exact survive token:

`C12_S0_PARITY_REVERSION_SURVIVE`

If data gates pass but any structural/reversion gate fails:

`C12_S0_REJECT_PARITY_REVERSION`

## 9. No-rescue rules

After outcome do not:

- lower 30 bps entry threshold;
- widen the 10 bps parity band;
- extend 30m hold;
- select only one deviation sign;
- remove true depeg/stress periods;
- choose famous dates;
- replace the 1.0000 anchor with a moving average.

Any materially different stablecoin mechanism requires a new ID.

## 10. Firewalls

Must remain false:

- maker_order_simulated;
- fill_model_calculated;
- queue_model_calculated;
- pnl_calculated;
- promotional_alpha_accessed.
