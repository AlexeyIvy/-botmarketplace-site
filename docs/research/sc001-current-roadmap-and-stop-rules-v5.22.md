# SC001 Current Roadmap and Stop Rules v5.22

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A COST PASS / SEP25 PROSPECTIVE P0 COLLECTOR SELF-TEST NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.21.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A structural economics frozen

Cost preflight:

`B14A_COST_PREFLIGHT_PASS`

Binding result:

`docs/research/sc001-b14a-cost-preflight-pass-result-v0.1.md`

Frozen:

- funding reserve = 1 bp;
- final structural burden = 37 bps;
- operational headroom hurdle = 50 bps.

The hurdle was fixed before any B14-A basis value was opened.

## 3. B14-A prospective P0

Protocol:

`docs/research/sc001-b14a-p0-prospective-2026-09-25-headroom-protocol-v0.1.md`

Exact expiry:

`2026-09-25T08:00:00Z`

Decision anchor:

`2026-09-25T07:30:00Z`

Frozen instruments:

- BTC-USD-260925;
- BTC-USD-SWAP;
- ETH-USD-260925;
- ETH-USD-SWAP.

## 4. Prospective capture

Runner:

`research/sc001/sc001_b14a_p0_prospective_trade_collector_v0_1.py`

Freeze:

`docs/research/sc001-b14a-p0-collector-implementation-freeze-v0.1.json`

The collector may record raw public trade prices inside the frozen capture window only.

It may not calculate basis during collection.

## 5. P0 later readout

Frozen representation:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

Search first five seconds from T0 only.

Frozen headroom hurdle:

`50 bps`

P0 classifications:

- `B14A_P0_STRONG_HEADROOM_2_OF_2`;
- `B14A_P0_MIXED_HEADROOM_1_OF_2`;
- `B14A_P0_WEAK_HEADROOM_0_OF_2`;
- `B14A_P0_DEFER_DATA`.

This is a prospective pilot, not formal Confirmation.

## 6. Firewalls

No:

- convergence after T0;
- settlePx convergence analysis;
- execution model;
- PnL;
- candidate ID;
- promotional conclusion.

## 7. Immediate next action

Run the P0 collector self-test now.

If PASS, start it in a dedicated tmux session; it will wait until the frozen event window automatically.
