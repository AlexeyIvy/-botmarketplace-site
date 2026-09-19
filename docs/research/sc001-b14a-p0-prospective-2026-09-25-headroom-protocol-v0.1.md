# SC001 — B14-A P0 Prospective 2026-09-25 Expiry Headroom Protocol v0.1

Date: 2026-09-19
Status: **FROZEN BEFORE PROSPECTIVE PRICE CAPTURE**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-cost-preflight-pass-result-v0.1.md`;
- `docs/research/sc001-b14a-exact-12-future-expiry-identity-freeze-v0.1.json`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Purpose

Prospectively test whether the final-30-minute dated-futures basis has enough raw scale to clear the fully frozen B14-A structural hurdle.

P0 is a **prospective headroom pilot**, not Confirmation and not a final strategy verdict.

## 2. Exact event

Expiry timestamp:

`2026-09-25T08:00:00Z`

Frozen pairs:

### BTC

- FUTURES: `BTC-USD-260925`;
- hedge: `BTC-USD-SWAP`.

### ETH

- FUTURES: `ETH-USD-260925`;
- hedge: `ETH-USD-SWAP`.

No asset or expiry substitution.

## 3. Natural decision anchor

The official OKX settlement-price estimation window begins 30 minutes before expiry.

Therefore freeze:

`T0 = 2026-09-25T07:30:00Z`

No earlier/later decision anchor may be selected after observing basis.

## 4. Protected raw capture

Before T0, collect public OKX trade messages only for the four frozen instruments.

Collection window:

`2026-09-25T07:29:00Z <= receive/event time <= 2026-09-25T08:02:00Z`

The extra margins are source-quality buffers only.

Raw capture may store trade price because the analysis rule is already frozen.

During collection do not calculate:

- basis;
- sign;
- convergence;
- return;
- PnL;
- best second/window.

## 5. Frozen representation

For later P0 readout inherit:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

Per family, search only:

- [T0,T0+1s)
- [T0+1s,T0+2s)
- [T0+2s,T0+3s)
- [T0+3s,T0+4s)
- [T0+4s,T0+5s)

Use the earliest one-second bucket containing >=1 real trade in both the dated FUTURES and its SWAP hedge.

No carry-forward.

No interpolation.

Within the selected second use the chronologically last trade price from each instrument.

## 6. Headroom metric

For each family:

`abs_basis_bps = 10000 * abs(ln(P_future / P_swap))`

Both are inverse USD-quoted contracts of the same underlying.

No contract-size normalization is required for the quoted-price ratio.

Contract sizing/delta normalization remains a later execution-stage requirement.

## 7. Frozen hurdle

From B14-A cost preflight:

- final structural burden = 37 bps;
- minimum economic reserve = 10 bps;
- operational headroom hurdle = `50 bps`.

No lowering after outcome.

## 8. Data validity

A family is valid only if:

- both subscriptions acknowledged;
- no recorded connection gap intersects [T0-1s,T0+6s];
- both instruments have a trade in one of the frozen five coactive seconds;
- timestamps and prices pass schema/finite-positive checks.

Otherwise that family is `DATA_INVALID`.

If either family is DATA_INVALID:

`B14A_P0_DEFER_DATA`

No two-family headroom classification.

## 9. P0 classifications

This is intentionally not a candidate-level SURVIVE/REJECT verdict.

If both families valid:

- both >=50 bps:
  `B14A_P0_STRONG_HEADROOM_2_OF_2`
- exactly one >=50 bps:
  `B14A_P0_MIXED_HEADROOM_1_OF_2`
- neither >=50 bps:
  `B14A_P0_WEAK_HEADROOM_0_OF_2`

Because BTC and ETH share one expiry timestamp/regime, 2/2 is not treated as two independent trials.

## 10. Consequences

### STRONG

Continue B14-A prospective program and freeze the next multi-expiry validation architecture.

### MIXED

Continue prospectively; do not tune family-specific thresholds.

### WEAK

Do not rescue the final-30-minute architecture by moving T0 earlier after seeing the result.

A materially longer-horizon architecture would require a new cost/funding card.

## 11. Hard firewalls

P0 raw capture and readout do not authorize:

- convergence after T0;
- settlePx convergence analysis;
- execution fills;
- PnL;
- candidate-ID assignment;
- promotional claims.
