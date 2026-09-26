# SC001 — B14-A P0 Transport Root-Cause Review v0.1

Date: 2026-09-26  
Status: **ROOT CAUSE IDENTIFIED / P0 REMAINS DEFER_DATA / NO PRICE OUTCOME OPENED**

## Evidence

The P0 state-only diagnostic found:
- collector COMPLETE;
- subscription_ack=false;
- raw_trade_messages=0;
- normalized_trade_rows=0;
- reconnect_count=67.

The connection-ledger diagnostic found 68 complete cycles of:
- CONNECT_ATTEMPT;
- CONNECTED;
- DISCONNECTED.

All observed disconnect errors are the same semantic OKX class:

`code=60033 / Parameter id error`.

The v0.3 collector sends:

`"id":"b14ap0-sub"`

in the public WebSocket subscribe request.

Current OKX WebSocket documentation requires request `id` to be 1-32 case-sensitive alphanumeric characters (letters/numbers); it is optional. The hyphen makes the frozen collector request ID invalid.

## Binding interpretation

Exact P0 research disposition remains:

`B14A_P0_DEFER_DATA`

This is a transport/source failure, not an economic or alpha rejection.

No attempt may reconstruct the Sep25 P0 from alternative price sources or a different time window.

## Future repair

For the next prospective expiry only:

1. remove the optional WebSocket `id` field or use an alphanumeric-only ID;
2. add a pre-event live subscription-ACK transport preflight;
3. require ACK PASS before arming the future collector;
4. preserve the 50 bps headroom rule unless a separately versioned research protocol changes it before the next event;
5. preserve explicit connection/process gap logging.

The Sep25 event is not replayable and remains DEFER_DATA.
