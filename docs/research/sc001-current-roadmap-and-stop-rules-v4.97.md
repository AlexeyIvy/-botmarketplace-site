# SC001 Current Roadmap and Stop Rules v4.97

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-C COLLECTOR SELF-TEST PASS / PROTECTED COLLECTION READY**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.96.md`

## 1. Binding prior states

C11:
`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:
`C12_S0_REJECT_PARITY_REVERSION`

B13-A:
`B13A_REJECT_STRUCTURAL`

B13-B historical:
`B13B_S0_DEFER_SAMPLE`

B13-B future:
prospective admission only.

B13-C historical:
`B13C_DEFER_HISTORICAL_DATA_FEASIBILITY`

No active C13+ strategy ID.

## 2. B13-C collector self-test passed

Exact state:

`B13C_COLLECTOR_SELF_TEST_PASS`

Binding result:

`docs/research/sc001-b13c-collector-self-test-pass-v0.1.md`

Observed:

- 12 symbols;
- 12 topics;
- websocket-client 1.7.0;
- output write path PASS;
- strategy outcomes = closed.

## 3. Persistent collection authorization

The protected prospective collector may now run continuously in `tmux`.

Collector mode:

`--mode collect`

Evidence role:

`PROTECTED_PROSPECTIVE_RAW_LIQUIDATION_STREAM`

## 4. First live operational gates

Immediately after startup verify:

- source-qualified symbols = 12/12;
- collector token = `B13C_COLLECTION_RUNNING`;
- subscription ACK = true;
- topics = 12;
- tmux session remains alive;
- collector_state.json exists.

If any source symbol fails qualification or subscription fails:

stop and review.

Do not silently reduce the universe.

## 5. Protected-stream firewall

While collector runs, do not inspect the stream for:

- best symbol;
- liquidation size threshold;
- post-event price behavior;
- continuation/reversal;
- cluster threshold;
- execution;
- PnL.

Allowed operational checks:

- connection status;
- subscription ACK;
- reconnect/gap count;
- raw message count;
- normalized event count;
- invalid-event count.

## 6. Parallel research

Once the protected collector is confirmed running, SC001 may continue independent-base design in parallel.

The accumulating liquidation stream is not available for strategy design yet.

## 7. Immediate next action

Start the collector in a dedicated tmux session and verify the first live operational state.

No alpha/backtest run is authorized.
