# SC001 — B14-A FUTURES-Chain Body/Schema Self-Test PASS v0.1

Date: 2026-09-19
Status: **B14A_CHAIN_SCHEMA_SELF_TEST_PASS**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-futureschain-body-schema-qualification-protocol-v0.1.md`;
- `docs/research/sc001-b14a-futureschain-body-schema-implementation-freeze-v0.1.json`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.18.md`.

## 1. Exact observed state

`B14A_CHAIN_SCHEMA_SELF_TEST_PASS`

Observed canonical D0 SHA:

`a7a36245ee668450960873e22f0ce515c95e6c990564fa8df4fedf97d6fbd5e8`

Authorized archives:

- `BTC-USD-futureschain-trades-2026-09-16.zip`;
- `ETH-USD-futureschain-trades-2026-09-16.zip`.

Observed firewalls:

- price values parsed/stored = false;
- basis = closed;
- convergence = closed;
- PnL = closed.

## 2. Self-test implication

The runner/freeze handshake passed.

The following fixtures passed:

- LEGACY_6 header;
- SOURCE_7 header with optional BOM;
- first-column instrument_name parsing;
- BTC family pattern acceptance;
- cross-family rejection.

No market archive body was opened by the self-test.

## 3. Next allowed action

Run exact two-archive body/schema qualification under the frozen protocol.

This stage may open the two frozen chain archives only for:

- ZIP/CSV integrity;
- header class;
- first-column instrument_name;
- row count;
- distinct contract IDs.

It may not parse/store price values or calculate basis/convergence/PnL.
