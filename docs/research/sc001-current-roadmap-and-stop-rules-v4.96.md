# SC001 Current Roadmap and Stop Rules v4.96

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-C PROSPECTIVE COLLECTOR IMPLEMENTATION FROZEN / SELF-TEST NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.95.md`

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

## 2. B13-C prospective collector

Protocol:

`docs/research/sc001-b13c-bybit-prospective-liquidation-collector-protocol-v0.1.md`

Runner:

`research/sc001/sc001_b13c_bybit_prospective_liquidation_collector_v0_1.py`

Freeze:

`docs/research/sc001-b13c-bybit-prospective-liquidation-collector-implementation-freeze-v0.1.json`

Registry:

`docs/research/sc001-contamination-registry-v0.26.json`

## 3. Frozen collection source

Bybit public linear WebSocket:

`wss://stream.bybit.com/v5/public/linear`

Topics:

`allLiquidation.SYMBOLUSDT`

Frozen 12-symbol universe:

BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI.

No symbol substitution based on liquidation activity.

## 4. Protected evidence role

All collected raw data:

`PROTECTED_PROSPECTIVE_RAW_LIQUIDATION_STREAM`

The collector may store explicit liquidation fields and source-quality metadata only.

No strategy design may inspect post-event price outcomes from this stream.

## 5. Self-test gate

Before persistent collection run:

`python3 ... --mode self-test`

must end with:

`B13C_COLLECTOR_SELF_TEST_PASS`

The self-test checks:

- freeze SHA handshake;
- frozen universe;
- parser valid fixture;
- parser rejection fixtures;
- output write path;
- websocket-client dependency.

## 6. Persistent collection

Only after self-test PASS, start:

`--mode collect`

inside tmux.

Collector records:

- raw WebSocket liquidation messages;
- normalized raw liquidation events;
- connection/reconnect/gap ledger;
- collector state.

## 7. Hard firewalls during collection

Forbidden:

- pre/post-event returns;
- continuation/reversal;
- liquidation threshold selection;
- cluster threshold;
- per-symbol alpha ranking;
- execution;
- PnL;
- candidate-ID assignment.

## 8. Parallel work

Once the collector is running, SC001 may continue a new independent-base design in parallel.

Do not inspect the protected liquidation stream for strategy design.

## 9. Immediate next action

Run B13-C collector self-test only.

If PASS, start persistent prospective collection.

No B13-C alpha outcome is authorized.
