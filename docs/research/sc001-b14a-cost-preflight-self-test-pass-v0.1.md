# SC001 — B14-A Cost Preflight Self-Test PASS v0.1

Date: 2026-09-19
Status: **B14A_COST_PREFLIGHT_SELF_TEST_PASS**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-hedge-funding-settlement-cost-preflight-v0.1.md`;
- `docs/research/sc001-b14a-cost-preflight-implementation-freeze-v0.1.json`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.20.md`.

## 1. Exact observed state

`B14A_COST_PREFLIGHT_SELF_TEST_PASS`

Observed:

- instruments:
  - BTC-USD-SWAP;
  - ETH-USD-SWAP;
- funding calibration window:
  `2026-06-01 .. 2026-08-31`;
- known subtotal before funding:
  `36 bps`;
- price/basis/convergence/PnL:
  `CLOSED`.

## 2. Self-test implication

The implementation/freeze handshake passed.

Static economics fixture passed:

- 3 taker fills;
- 5 bps per taker fill;
- 1 bp expiry settlement fee;
- 10 bps spread/depth reserve;
- 10 bps execution/model reserve.

No funding values were opened during self-test.

No FUTURES or SWAP prices were accessed.

## 3. Next allowed action

Run the funding-only B14-A structural cost preflight.

Allowed:

- historical realized funding rates;
- funding timestamps;
- source metadata;
- static cost arithmetic.

Forbidden:

- FUTURES prices;
- SWAP prices;
- basis;
- returns;
- settlePx;
- delivery price;
- convergence;
- execution/PnL;
- candidate-ID assignment.
