# SC001 B15-P2 P0S — 2025 Cross-Type Index Audit Review v0.1

Date: 2026-09-30
Status: **SOURCE-STRUCTURE REVIEW / B15-P2 STOP-FREEZE / PRICE FIREWALL CLOSED**

## Execution record

Offline validation:
- Test Executor job: `job_20260930T001448Z_a4175115`
- network profile: `offline`
- implementation SHA256: `2ab1203788747e857d1fb89a3e849e0d8eb47b6cdd000e13875cf683811fb2a2`
- result: `B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_V01_SELF_TEST_PASS`
- exit code: 0

Authorized live source-only execution:
- Test Executor job: `job_20260930T033315Z_83502e67`
- repo head: `f749565e513d322a2ba815a050528b06689595df`
- network profile: `public_research`
- implementation SHA256: `2ab1203788747e857d1fb89a3e849e0d8eb47b6cdd000e13875cf683811fb2a2`
- exactly one live run was launched
- exit code: 2
- timed out: false

Canonical exact structured result:
`docs/research/sc001-b15p2-p0s-2025-cross-type-index-audit-result-v0.1.json`

SHA256:
`79dc9be3dcc8b9334518cc9653025bbd8a55e086cad85aa19f988a7fab7aec7a`

Canonical exact log bytes:
`docs/research/runtime-inbox/sc001-b15p2-p0s-2025-cross-type-index-audit-v0.1.log.txt`

SHA256:
`95eaa50989f3dbe53725472a3d88eae71e1f0aa848d5d0fb852131cfcc1b1bb6`

The `.log.txt` suffix is used only because repository ignore rules exclude `*.log`; the canonicalized bytes are identical to the Test Executor `run.log`.

## Observed result

Terminal runtime state:
`B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_REVIEW`

Fail-closed cause:
`UNKNOWN_ANNOUNCEMENT_TYPE:Earn`

The frozen protocol enumerated eight official announcement type keys. The live official Bybit announcement index returned a type outside that frozen schema. The implementation therefore stopped before computing recovery coverage.

This means:
- no valid cross-type recovery count was produced;
- the audit did not demonstrate the minimum four recoveries needed to reach the unchanged 80% source gate;
- it also did not prove that fewer than four recoveries exist, because coverage analysis did not complete;
- the useful finding is source-structure instability relative to the frozen protocol.

No enum expansion, parser repair, body-hydration fallback, rerun, or alternate execution plane is authorized in this branch.

## Firewalls

The live result and log explicitly preserve:
- affected-contract price: CLOSED;
- index values: CLOSED;
- basis: CLOSED;
- returns: CLOSED;
- PnL: CLOSED;
- trading: CLOSED.

The frozen protocol additionally keeps L1/L2, trades, funding, mark/premium/spot and external venues closed.

## Three-role review

### 1. Financial expert / trader

No economic edge conclusion is available because no price outcome was opened. The 2025 source census remains broad enough to be interesting as event research, but B15-P2 is still blocked at source provenance/structure before a clean price experiment can begin.

Given the explicit project objective to reach a natural STOP/FREEZE rather than create another long rescue branch, further source-engineering here has lower current research priority than returning to the strategy-level queue.

Decision: keep B15-P2 as a frozen secondary candidate. Do not treat the source error as evidence of profitability or unprofitability.

### 2. Programmer-trader / research engineering

The fail-closed behavior is correct. The exact frozen implementation encountered a live schema value not included in the preregistered type set and stopped without silently adapting.

Adding `Earn`, widening the enum, or changing normalization and immediately rerunning would be a new rescue iteration informed by the observed live source. That is specifically outside the requested stopping rule.

Decision: no implementation rescue and no second live run. Preserve the exact result as the terminal source-structure finding for this branch.

### 3. Mathematician / statistician

The frozen source gate remains 80%, requiring at least 124 admitted events out of 154, or four valid recoveries beyond the original 120. Because the live audit terminated before recovery counting, there is no statistically valid basis to claim the gate passed.

Equally, the run cannot establish a numerical coverage failure below 80%; the terminal evidence is instead that the preregistered source model was not sufficiently stable to complete the test.

Decision: do not open price outcomes from an incomplete source gate. Freezing here avoids adaptive continuation after observing a protocol-breaking source feature.

## Joint decision

`B15P2_P0S_SOURCE_STRUCTURE_STOP_FREEZE_SECONDARY`

Interpretation:
- original B15-P2 P0 verdict `DEFER_SOURCE_COVERAGE` remains unchanged;
- the 2025 source-only successor did not mature into an authorized price-outcome experiment;
- B15-P2 is frozen as a secondary research branch;
- no same-evidence rescue, enum adaptation, article-body fallback, or further B15-P2 live execution is authorized;
- reopening would require a new explicit strategy decision based on genuinely new source-level justification, not continuation of this observed failure;
- no new price/index/basis/returns/PnL outcome is opened.

Next action:
`RETURN_TO_STRATEGY_USER_GATE_WITH_B15P2_FROZEN_SECONDARY`
