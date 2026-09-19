# SC001 — B14-A P0 Prospective Collector Self-Test PASS v0.1

Date: 2026-09-19
Status: **B14A_P0_COLLECTOR_SELF_TEST_PASS**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-p0-prospective-2026-09-25-headroom-protocol-v0.1.md`;
- `docs/research/sc001-b14a-p0-collector-implementation-freeze-v0.1.json`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.22.md`.

## 1. Exact observed state

`B14A_P0_COLLECTOR_SELF_TEST_PASS`

Observed:

- instruments:
  - BTC-USD-260925;
  - BTC-USD-SWAP;
  - ETH-USD-260925;
  - ETH-USD-SWAP;
- expiry UTC = `2026-09-25T08:00:00+00:00`;
- decision anchor UTC = `2026-09-25T07:30:00+00:00`;
- capture window UTC =
  `2026-09-25T07:29:00+00:00 .. 2026-09-25T08:02:00+00:00`;
- websocket-client = `1.7.0`;
- basis/convergence/PnL = CLOSED.

## 2. Implication

Collector implementation/freeze handshake passed.

No prospective price was captured during self-test.

No basis, convergence, execution or PnL was calculated.

## 3. Next allowed action

Start the frozen P0 collector in a dedicated tmux session.

The collector may:

- qualify the four frozen instrument identities;
- wait until the pre-frozen connection time;
- subscribe to the four OKX public trade topics;
- store raw trades only inside the frozen capture window;
- maintain a connection/gap ledger.

It may not calculate basis while collecting.
