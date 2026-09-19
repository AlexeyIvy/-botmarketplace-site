# SC001 Current Roadmap and Stop Rules v4.99

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-C COLLECTION LIVE / B14-A NON-ALPHA SOURCE-SPEC PREFLIGHT NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.98.md`

## 1. Protected collection

B13-C:

`B13C_COLLECTION_RUNNING`

Prospective raw liquidation stream remains protected.

No alpha inspection.

## 2. New parallel base pool

Binding:

`docs/research/sc001-parallel-independent-base-mechanism-pool-v0.1.md`

Three concepts reviewed:

- B14-A dated-futures final-settlement convergence;
- B14-B persistent multi-settlement funding carry;
- B14-C scheduled venue resumption dislocation.

## 3. Pool dispositions

B14-A:

`SELECT_FOR_SOURCE_AND_SETTLEMENT_SPEC_PREFLIGHT`

B14-B:

`HOLD_NEW_ARCHITECTURE / LOWER_PRIORITY`

B14-C:

`DEFER_SOURCE_AND_EXECUTION_FEASIBILITY`

No candidate IDs assigned.

## 4. Why B14-A goes first

B14-A has:

- deterministic contractual terminal anchor;
- potentially three structural executions rather than four if futures settles automatically;
- no need for directional prediction;
- clear causal event clock;
- plausible public source/spec feasibility.

## 5. B14-A hard boundary

The next stage is source/specification only.

Do not calculate:

- futures basis;
- settlement convergence;
- strategy signal;
- execution;
- PnL.

## 6. New kernel gate

B14-A preflight must obey:

`docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`

including contract denomination and event-time reconciliation.

## 7. Immediate next action

Perform B14-A OKX dated-futures source / settlement-specification audit.

No VPS outcome run is authorized.
