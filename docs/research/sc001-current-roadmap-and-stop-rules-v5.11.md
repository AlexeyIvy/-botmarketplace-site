# SC001 Current Roadmap and Stop Rules v5.11

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A V0.6 PRODUCT PASS / ARCHIVE METADATA DIAGNOSTIC NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.10.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.6 result

Exact state:

`B14A_D0_V06_SOURCE_ARCHIVE_METADATA_REVIEW`

Product semantics:

PASS.

Observed:

- BTC-USD eligible future contracts = 6;
- ETH-USD eligible future contracts = 6;
- both inverse SWAP hedges = PASS.

Archive source gate remains unresolved for representative contracts:

- BTC-USD-260925;
- ETH-USD-260925.

## 3. No new transport change yet

Do not modify:

- instFamilyList semantics;
- D-3 probe lag;
- daily aggregation;
- label-day / previous-day fallback;
- exact filename filter;

until the canonical v0.6 report's per-contract error/attempt details are inspected.

## 4. Firewalls

No:

- trade body access;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL;
- candidate ID.

## 5. Immediate next action

Read-only local JSON diagnostic for representative archive probes.

No network access required.
