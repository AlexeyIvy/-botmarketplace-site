# SC001 Current Roadmap and Stop Rules v4.5

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — UNIVERSE/CHRONOLOGY FROZEN / COMMON ACCOUNTING VALIDATION OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.4.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`.

No prior verdict is reopened. SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Governance state

Frozen first-generation universe:
`docs/research/sc001-first-generation-multi-asset-universe-freeze-v1.0.json`

Frozen fresh chronology/asset holdout:
`docs/research/sc001-fresh-chronology-and-asset-holdout-protocol-v0.1.md`

Current contamination registry:
`docs/research/sc001-contamination-registry-v0.3.json`

No July/August promotional body has been opened by these governance stages.

## 3. Frozen universe

Exact ranked set:
BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI — all OKX linear USDT SWAPs.

No later performance-based substitution is allowed.

## 4. Fresh evidence roles

Discovery assets (8): BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH on 2024-07-01..14.

Asset holdout (4): SOL, FIL, LTC, SUI on the same July block; this is cross-asset replication, not time Confirmation.

Chronological Confirmation: all 12 on 2024-08-01..14.

July 16..30 remains unopened/unassigned and may not be opportunistically mined.

## 5. Historical execution-spec status

Current structural metadata is not historical proof.

Historical exact tickSz/lotSz/minSz/ctVal/fee/funding handling remains a mandatory unresolved gate before promotional execution/PnL.

## 6. Current hard gate — common accounting core synthetic validation

Protocol:
`docs/research/sc001-common-accounting-core-validation-protocol-v0.1.md`

Core:
`research/sc001/sc001_common_accounting_core.py`

Validation runner:
`research/sc001/sc001_common_accounting_validation.py`

Exact PASS:
`SC001_COMMON_ACCOUNTING_CORE_VALIDATION_PASS`

Required:
- 20/20 frozen synthetic tests PASS;
- no real market body access;
- no strategy signal;
- no promotional PnL;
- no July/August reserved body access.

## 7. After PASS

1. freeze/resolve historical execution-spec handling for the frozen universe/chronology;
2. build normalized market-event schema;
3. build taker execution kernel for E007-class strategies;
4. validate with golden fixtures, causality, fault injection, deterministic replay and independent accounting recomputation;
5. run a cheap predeclared E007 economic-feasibility audit before full multi-asset replay;
6. only if it survives, freeze a new-ID strict E007 replication implementation;
7. open July Discovery bodies only after the one-shot manifest/identity gate.

## 8. Immediate VPS action

Pull latest code, py_compile both common accounting files, then run the synthetic validation once. Do not access fresh strategy bodies afterward until the result is reviewed.
