# SC001 — B13-C Prospective Liquidation Collector Live-Start Record v0.1

Date: 2026-09-19
Status: **B13C_COLLECTION_RUNNING — PROTECTED PROSPECTIVE STREAM STARTED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b13c-collector-self-test-pass-v0.1.md`;
- `docs/research/sc001-b13c-bybit-prospective-liquidation-collector-protocol-v0.1.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v4.97.md`.

## 1. Observed live start

Collector token:

`B13C_COLLECTION_RUNNING`

Observed:

- source-qualified symbols: `12 / 12`;
- subscription ACK: `True`;
- subscribed topics: `12`;
- strategy outcomes: `CLOSED`.

Collector start timestamp:

`2026-09-19T06:47:38.969000+00:00`

This timestamp is the prospective evidence boundary for the B13-C raw liquidation stream.

## 2. Evidence role

All events collected after the recorded start remain:

`PROTECTED_PROSPECTIVE_RAW_LIQUIDATION_STREAM`

No collected event may be used for strategy design before a separate future B13-C protocol is frozen.

## 3. Operational state

The collector is running in dedicated tmux session:

`b13ccol`

Primary output root:

`~/sc001_data/SC001_B13C_PROSPECTIVE_LIQUIDATIONS/`

Expected operational files:

- raw UTC-daily JSONL;
- normalized event UTC-daily JSONL;
- connection/reconnect/gap JSONL;
- collector_state.json;
- collector.log.

## 4. Allowed monitoring

Allowed while stream is protected:

- tmux alive/stopped state;
- connection status;
- subscription ACK;
- source-qualified count;
- raw message count;
- normalized event count;
- invalid event count;
- reconnect count;
- cumulative gap duration.

## 5. Forbidden monitoring

Do not inspect or rank:

- per-symbol liquidation frequency;
- liquidation-size distribution for strategy selection;
- long-vs-short predictive behavior;
- pre/post-event returns;
- continuation/reversal;
- cluster thresholds;
- execution/PnL.

## 6. Parallel research consequence

B13-C no longer blocks SC001 research while data accumulates.

Independent-base design work may continue in parallel provided the protected liquidation stream is not used for candidate selection.
