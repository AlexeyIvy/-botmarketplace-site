# SC001 Current Roadmap and Stop Rules v5.60

Date: 2026-09-24  
Status: **B15-P1 FOUNDATION PRESERVATION-COMPLETE / STAGE C STRUCTURAL PREFLIGHT SEALED**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.59.md`

## Preservation foundation

Final v0.2.2 identity/route state remains frozen and restore-verified.

Latest artifact-complete checkpoint:

`CHECKPOINT_BACKUP_RESTORE_VERIFY_PASS`

Checkpoint ID:

`botmarketplace-sc001-b15-v022-artifact-complete-checkpoint-20260924T095050Z`

Archive SHA256:

`36401bcb50b1042e6fc2df91fac28998647a03d75d280fa9feb323c54acb1279`

Full logical route graph SHA256:

`06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928`

## Stage C cost design

Frozen candidate parameters:
- reference notional = 10,000 USDT per opening leg;
- exactly 2 spot taker fills;
- fee floor = 10 bps per fill;
- two-fill minimum = 20 bps;
- legging/latency/model reserve = 10 bps;
- venue/counterparty/inventory reserve = 10 bps;
- capital lock = 3 bps per started day, minimum 7 days = 21 bps;
- minimum non-transfer structural burden = 61 bps;
- additional economic headroom = 10 bps;
- minimum hurdle before transfer costs = 71 bps;
- transfer-fee uncertainty multiplier = 1.25.

Actual account/pair trading fee may only increase the frozen fee floor.

Bybit percentage withdrawal formula is explicit under feeType=0.

OKX routes with nonzero burningFeeRate are fail-closed as:

`OKX_BURNING_FEE_FORMULA_REVIEW`

until a separate exact target-receive formula is frozen.

Unsupported fee currency is fail-closed as:

`FEE_CCY_CONVERSION_REQUIRED`

## Sealed Stage C structural preflight

Bundle:

`bundle_20260924T095623Z_f2990716`

SHA256:

`ef26b125797a70cb20cf2f9d2253279125077b8fddc9076fb295565d4779c98f`

Approval code:

`BM-EF26B125797A`

State:

`SEALED_RUN_PENDING`

The bundle is offline/non-price and contains no market-price dataset.

It verifies:
- foundation hashes/counts;
- fee-floor arithmetic;
- Bybit withdrawal formula tests;
- Bybit/OKX trading-fee adapter tests;
- amount-aware but outcome-blind route-selection tests;
- OKX fail-closed fee semantics;
- complete source-field coverage;
- one-sided quote route exclusion;
- strict price/PnL/collector firewall.

## Boundary

A PASS authorizes only:

`PREPARE_15_SECOND_NONPRICE_COLLECTOR_DESIGN`

It does not authorize:
- collector launch;
- market prices;
- PnL;
- live execution.

## Next state

`RUN_B15_P1_FULL_CYCLE_EDGE_TO_FILL_STRUCTURAL_PREFLIGHT_AFTER_USER_APPROVAL`
