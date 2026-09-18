# SC001 — C9 Scheduled Funding / Mark-Index State Feasibility Card v0.1

Date: 2026-09-18  
Status: **NON-ALPHA FEASIBILITY CARD — DATA/STATE AUDIT ONLY**  
Parent: `sc001-c7-c10-no-alpha-data-structural-feasibility-audit-v0.1.md`

## 1. Candidate identity

Candidate: C9.

Mechanism family:

- M5 relative-value / derivative state;
- M7/P11 scheduled event context.

This is not C1 thresholded basis convergence.

## 2. Economic hypothesis

Scheduled funding mechanics and the joint state of:

- realized/announced funding;
- mark price;
- index price;
- perpetual/spot or mark/index deviation;

may define derivative-state transitions with larger economic scale than ordinary sub-minute directional prediction.

This is a hypothesis only. No directional sign is frozen yet.

## 3. Minimum feature stack

### C9-F1 — funding state

- primitive: P8;
- role: R2;
- exact realized funding rate at its published/settled timestamp.

### C9-F2 — scheduled funding-time context

- primitive: P11;
- role: R2;
- deterministic time-to/from funding timestamp.

### C9-F3 — mark/index relative state

- primitive: P8/P7;
- role: R6/R2;
- exact causal mark-minus-index deviation.

### C9-F4 — continuous basis state

- reusable block: RB007;
- role: R6/R2;
- optional only if spot/perp source pair is qualified.

No threshold/sign alpha rule is included in the feasibility stage.

## 4. Data-only questions

Before any outcome-bearing sentinel:

1. Which assets have continuous funding history over the intended calibration dates?
2. What funding intervals actually applied historically per asset/date?
3. Are mark and index histories available at sufficient cadence?
4. Are timestamps causal and alignable with trade/perpetual data?
5. Are scheduled events frequent enough across assets to support block-level inference?
6. What is the unconditional scale of mark/index/basis state transitions around events?
7. Which execution architecture would be required if a mechanism later survives?

## 5. Initial universe rule

Do not choose assets by historical C9 outcome.

Candidate universe must be selected prospectively using only:

- continuous historical listing;
- source completeness;
- liquidity/turnover;
- contract continuity;
- data integrity.

A small liquid multi-asset universe is preferred over BTC-only if free data coverage permits.

## 6. Evidence role and contamination

Any dates opened to inspect funding/mark/index state distributions become:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

for the resulting C9 implementation.

Do not use July/September protected asset holdouts, July gap, August protected dates, October Confirmation, or E006 Confirmation.

A new contamination-registry version is required before opening any previously fresh C9 calibration period.

## 7. Structural execution fork

No alpha outcome may be used to choose execution architecture.

Possible later architectures:

- directional post-event: T1 / two fills;
- hedged derivative-state convergence/carry: T3 / four fills plus funding/legging;
- state/filter use only: no standalone trade.

The architecture and its structural hurdle must be frozen before any C9 alpha sentinel.

## 8. Cheapest first gate

Stage C9-D0: metadata/data-semantics only.

Require:

- funding source coverage;
- historical funding interval reconstruction;
- mark/index source coverage;
- timestamp alignment;
- data volume/disk feasibility;
- no returns/PnL.

Only after C9-D0 PASS may a separate frozen state-transition sentinel be designed.

## 9. Relevant building blocks

- RB007 continuous spot/perp basis state;
- RB008 causal reference;
- P8 funding/derivative state;
- P11 scheduled context.

Do not add RB001/RB003/RB005/RB006 by default.

## 10. Kill conditions before alpha

Reject/defer C9 structurally if:

- historical funding intervals cannot be reconstructed reliably;
- mark/index timestamps are incompatible with event timing;
- multi-asset event breadth is inadequate;
- required paired execution implies a cost floor clearly larger than observable state scale before strategy design.

## 11. Immediate implementation

Prepare a metadata-only public-source probe, preferably on OKX first because one public historical service provides funding and market-data infrastructure.

No market-state outcome should be interpreted until the data-role registry and exact audit protocol are frozen.
