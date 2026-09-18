# SC001 — C8 Cross-Venue Same-Asset Data / Clock Audit Plan v0.1

Date: 2026-09-18  
Status: **NON-ALPHA DATA/CLOCK DESIGN — NO DISLOCATION OUTCOME AUTHORIZED**  
Parent: `sc001-c7-c10-no-alpha-data-structural-feasibility-audit-v0.1.md`

## 1. Purpose

Determine whether a cross-venue same-asset candidate can be studied causally before choosing a trading rule.

C8 is distinct from C4 because the market relationship is venue-to-venue for the same asset, not BTC/ETH-to-alt on one venue.

## 2. Candidate venue sources

Preferred first audit pair:

- OKX;
- Bybit.

Reason:

- both currently expose free historical public market data including trades;
- both advertise order-book historical data;
- this can support later quote-aware execution work without purchasing data.

Binance remains a valid alternate/third source for trade/aggTrade cross-checking.

No venue is selected because of historical strategy performance.

## 3. Data-only audit dimensions

For each venue/source:

- exact instrument mapping;
- contract type and quote currency;
- timestamp unit;
- timestamp semantic meaning;
- source ordering;
- duplicate/out-of-order behavior;
- archive day boundary;
- trade-side convention;
- quote/order-book generation timestamp where available;
- missing periods;
- checksum/identity support.

## 4. Alignment audit

Before any dislocation magnitude is examined, freeze:

- alignment clock;
- allowed timestamp tolerance;
- whether matching uses last-known causal observation or next observation;
- staleness limit;
- no future interpolation;
- session/day boundary behavior.

If timestamp uncertainty is comparable with the proposed lag, directional lead/lag research is invalid.

## 5. Execution fork must be decided without alpha

C8A directional lag:

- T1;
- two fills;
- directional exposure.

C8B paired convergence:

- T3;
- four fills;
- legging, collateral and venue-specific execution risk.

C8A and C8B are separate future candidate definitions if both are retained.

## 6. Cheapest first gate

C8-D0:

- metadata/source availability;
- instrument overlap;
- timestamp/clock compatibility;
- expected archive size;
- deterministic synchronization golden tests.

No return/dislocation/PnL outcome.

Only after C8-D0 PASS may a raw dislocation-frequency/headroom sentinel be frozen.

## 7. Reusable blocks

- RB008 causal reference semantics;
- RB004 residualization principle as a protection against false interpretation;
- venue-specific liquidity P6 may later enter execution, not the first clock audit.

No C4 lag parameters are inherited.

## 8. Contamination

Any newly opened synchronized dates become nonpromotional Selection/Calibration for the resulting C8 implementation.

Do not repurpose protected SC001 dates or independent branch forward outcomes.

## 9. Immediate implementation

After C9-D0 specification, write a lightweight network metadata probe for one common liquid asset on OKX/Bybit that retrieves no alpha outcome and only validates source identity, archive availability and timestamp semantics.
