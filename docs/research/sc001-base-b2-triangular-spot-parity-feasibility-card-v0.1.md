# SC001 — Independent Base Concept B2: Same-Venue Triangular Spot Parity v0.1

Date: 2026-09-18
Status: **NON-ALPHA FEASIBILITY CARD / BASE MECHANISM**
Scope: `SCALPING RESEARCH / SC001`

## 1. Identity

- provisional base concept: `B2_TRIANGULAR_SPOT_PARITY`
- candidate ID: **NOT ASSIGNED**
- mechanism family: M5 structural relative-value/no-arbitrage
- execution archetype: T3 three-leg
- Signal Horizon: S0
- Position Horizon: P0
- independence: does not use C1-C10 signals

## 2. Economic mechanism

Representative frozen design triangle for feasibility:

- ETH-USDT;
- ETH-BTC;
- BTC-USDT.

Economic payer/source:

Temporary violation of same-venue cross-rate parity due to asynchronous order-book updates.

The edge is known from executable quotes before entry; no directional forecast is needed.

## 3. Time architecture

Would require:

- synchronized executable bid/ask from all three books;
- sub-second decision and execution;
- atomic or near-atomic IOC/FOK behavior;
- near-zero intended holding time.

## 4. Feature inventory

Only executable cross-rate parity.

No RB001-RB018.

## 5. Risk signature

- directional beta: intended near-zero;
- legging risk: extreme;
- latency sensitivity: extreme;
- spread/depth exposure: three books;
- inventory duration: very short if successful;
- venue concentration: one venue.

## 6. Edge-to-Fill preflight

Structural fills:

- 3 taker fills for a complete triangle.

Conservative fee floor:

- 15 bps at 5 bps/fill reference.

Additional requirements:

- three-book spread/depth;
- legging reserve;
- latency/model reserve.

Conservative burden is therefore materially above 15 bps.

Expected information scale:

No separate economic mechanism explains why liquid same-venue parity violations should persist at tens of bps for a public-data/non-colocated participant.

The opportunity is primarily latency competition.

Edge-to-Fill classification:

`STRUCTURALLY_IMPLAUSIBLE`

for the current SC001 data/latency posture.

## 7. Data feasibility

Public books exist, but historically proving atomic executable three-leg fills requires much finer synchronized book/order semantics than the project currently has across all three spot books.

This is a data/latency mismatch, not merely a coding issue.

## 8. Cheapest sentinel

Not justified.

A metadata or historical parity test using coarse data would risk manufacturing false arbitrage because execution requires simultaneous executable depth.

## 9. Independence check

Independent from C8B because this is same-venue three-leg algebraic parity, not two-venue price convergence.

Still rejected structurally before outcome.

## 10. Disposition

`REJECT_STRUCTURAL`

Reason:

Three-fill fee burden + legging/latency requirements exceed the plausible parity edge available to the project's public historical/non-colocated architecture.

No backtest should be run.
