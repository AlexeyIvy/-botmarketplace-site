# SC001 Current Roadmap and Stop Rules v5.121

Date: 2026-09-26  
Status: **B15-P1 W1 accumulation continues / B14-A P0 = DEFER_DATA on source validity / B13-C becomes next active research branch**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.120.md`

## 1. B15-P1

Unchanged:

`W1_7_COMPLETE_UTC_DAY_OBSERVATION_ACCUMULATING`

Collector stays frozen and running.

## 2. B14-A P0 state-only diagnostic

Runner job:

`job_20260926T204826Z_b3ce516d`

Diagnostic PASS:

`B14A_P0_STATE_ONLY_DIAGNOSTIC_PASS`

Observed collector state:
- status = `B14A_P0_COLLECTION_COMPLETE`;
- subscription_ack = false;
- raw_trade_messages = 0;
- normalized_trade_rows = 0;
- invalid_trade_rows = 0;
- reconnect_count = 67;
- connection_gap_count = 67;
- process_restart_count = 0;
- process_restart_gap_count = 0;
- basis/convergence/PnL = false.

## 3. Binding P0 disposition

Frozen P0 data validity required subscription ACK and valid coactive trade data.

Therefore exact P0 disposition is:

`B14A_P0_DEFER_DATA`

This is:
- not an economic reject;
- not an alpha reject;
- not evidence that dated-futures settlement convergence lacks headroom.

The price/headroom outcome was never opened.

Do not rescue by:
- using a different T0;
- using a different 5-second window;
- using another expiry retrospectively;
- lowering the 50 bps hurdle;
- reconstructing missing trades from another source after the event.

## 4. Technical inference

The collector writes `raw_trades.jsonl` only after at least one accepted trade message is received.

With raw_trade_messages = 0, the earlier three-input Runner materialization failure is consistent with `raw_trades.jsonl` never having been created.

A connection-only diagnostic is allowed next because it reads no price data and can identify the source/transport failure mode before the next prospective expiry.

## 5. Parallel research priority

While B14-A transport is diagnosed non-price only, activate B13-C source-quality census.

B13-C prospective liquidation collection began 2026-09-19 and its strategy outcomes remain protected.

First B13-C step must be source/data quality only:
- collector status;
- raw/event counts;
- connection/reconnect/gap integrity;
- schema validity;
- observation duration.

No post-liquidation return, threshold, symbol ranking, continuation/reversal or PnL may be opened before a new B13-C outcome protocol is frozen.

## Next state

`B14A_CONNECTION_LEDGER_DIAGNOSTIC_PLUS_B13C_SOURCE_QUALITY_CENSUS_PREPARATION`
