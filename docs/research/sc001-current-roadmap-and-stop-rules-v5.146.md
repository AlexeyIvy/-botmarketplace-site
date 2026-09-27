# SC001 Current Roadmap and Stop Rules v5.146

Date: 2026-09-27
Status: **B15-P1 W1 accumulation / B14-A P0 DEFER_DATA / B13-C S0 terminal REJECT with reusable block retained / B14-B fresh persistent-funding architecture frozen**

Supersedes: `sc001-current-roadmap-and-stop-rules-v5.145.md`

## 1. Mandatory reusable-block extraction

Binding policy:

`docs/research/sc001-terminal-experiment-reusable-block-extraction-policy-v0.1.md`

Every terminal/reject/defer experiment must now explicitly record either:
- reusable market/measurement/execution blocks; or
- `NO_REUSABLE_BLOCK_IDENTIFIED`.

A parent strategy failure must not erase separately supported market behavior.

## 2. B13-C reusable block

B13-C S0 standalone 30-second reversal remains terminal:

`B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`

Reusable block retained:

`RB021 — Explicit pure-side liquidation-burst reversal state v0.1`

Evidence:
- n=1,793;
- median +1.3682 bps;
- positive share 55.884%;
- 5/6 positive complete-day medians.

Use only as scoped R2/R3/R5 state/context under a new prospectively frozen mechanism.

No same-interval rescue tuning.

## 3. B14-B activated

Mechanism:

`PERSISTENT MULTI-SETTLEMENT CROSS-VENUE FUNDING CARRY`

Fresh evidence window:

`2026-07-01T00:00:00Z .. 2026-09-27T00:00:00Z`

This is separate from B13-A H1-2025 evidence.

Frozen architecture:
- same 12 assets;
- OKX vs Bybit USDT perpetual funding;
- entry signal = last 3 matched funding differentials have same nonzero sign;
- no magnitude threshold;
- enter only after third realized settlement is known;
- fixed direction;
- seven-calendar-day hold;
- use all realized funding cashflows on each venue inside hold;
- non-overlapping cycles per symbol;
- no price/basis outcome.

Frozen economics:
- four-fill burden = 40 bps;
- gross headroom hurdle = 50 bps.

Data/sample gates:
- >=8 source-eligible symbols;
- >=24 valid cycles;
- >=8 cycle symbols;
- >=2 cycle-start months.

Structural gates:
- pooled median gross carry >=50 bps;
- positive-cycle share >=60%;
- >=6 positive-median symbols;
- >=2 positive-median months.

## 4. B14-B implementation

Protocol:

`docs/research/sc001-b14b-persistent-multisettlement-funding-carry-protocol-v0.1.md`

Entrypoint:

`research/sc001/sc001_b14b_persistent_multisettlement_funding_carry_v0_1.py`

SHA256:

`cb288810ef8871ea1de3bfe9decf6e372cb525c1c62d0123969d4f7f459793f4`

Before any fresh 2026 funding-value access:
run the no-input offline synthetic self-test.

Expected:

`B14B_PERSISTENT_CARRY_V01_SELF_TEST_PASS`

## 5. B15-P1

Unchanged.

Collector remains operationally frozen while W1 data accumulates.

## Next state

`SEAL_B14B_PERSISTENT_CARRY_OFFLINE_SELFTEST`
