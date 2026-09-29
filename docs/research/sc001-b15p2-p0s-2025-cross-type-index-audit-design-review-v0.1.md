# SC001 B15-P2 P0S — Cross-Type Index Audit Design Review v0.1

Date: 2026-09-29
Status: **DESIGN READY / EXECUTION WAITING FOR TEST EXECUTOR DAILY SLOT**

Protocol:
`docs/research/sc001-b15p2-p0s-2025-unmatched-announcement-index-cross-type-audit-protocol-v0.1.md`

Protocol SHA256:
`0bb6b61988041a54873dace0c68ce253e3dc246e7b4e197e5c8def61a0297e1d`

Implementation candidate:
`research/sc001/sc001_b15p2_p0s_2025_cross_type_index_audit_v0_1.py`

Implementation SHA256:
`2ab1203788747e857d1fb89a3e849e0d8eb47b6cdd000e13875cf683811fb2a2`

## Why this audit is the next step

The fresh 2025 source-only census found 154 in-scope closed USDT LinearPerpetual instruments but only 120 admissible exact-symbol announcement matches, or 77.9220779221%, below the unchanged 80% source gate.

The original census queried the official announcement endpoint with `type=delistings`. Bybit's official API currently defines several other announcement type keys, so the narrow type partition is a source-structure hypothesis that can be tested without opening any price outcome.

This audit removes only the announcement `type` request filter. It does not change:
- exact-symbol identity;
- numeric `publishTime` causal requirement;
- listing-episode chronology;
- the 80% source gate;
- the 2025 holdout window;
- any market-price firewall.

## Role 1 — financial expert / trader

This is appropriate source due diligence rather than strategy rescue. A delisting event communicated through a different official announcement category is still causally observable if its official `publishTime` precedes the known delivery time.

The audit does not infer tradability or edge. Its only question is whether the event clock can be sourced more completely from Bybit itself.

Verdict: proceed with the source-only audit when the authorized execution slot exists.

## Role 2 — programmer-trader / research engineering

Static checks passed:
- canonical input result SHA is hard-bound;
- the exact 34-symbol unmatched set is hard-bound and hashed;
- the known-good source parser dependency is SHA-bound;
- only `/v5/announcements/index` and `/v5/market/instruments-info` are called;
- announcement type schema is fail-closed;
- `dateTimestamp` is diagnostic only;
- exact token boundaries are retained;
- source integrity failures produce REVIEW;
- body hydration is not mixed into this first audit stage.

The implementation has a synthetic offline self-test but it has not been executed because the Test Executor UTC-day limit is already 10/10.

Verdict: prefreeze only; do not promote to executable freeze until offline self-test passes.

## Role 3 — mathematician / statistician

The threshold of four recovered symbols is not fitted to a price outcome. It follows mechanically from the already frozen source gate:

`ceil(0.80 × 154) - 120 = 124 - 120 = 4`.

Thus the audit does not lower or optimize the gate. It tests whether a documented source-partition assumption can account for enough missing event identities to make a corrected source census worth preregistering.

Even if four or more symbols are recovered, this audit alone does not make the 2025 set confirmatory. A corrected source parser must still be frozen and rerun source-only, followed by semantic and contamination review before any price experiment.

Verdict: design is admissible as source-only research.

## Joint decision

`PREFREEZE_CROSS_TYPE_INDEX_AUDIT_WAIT_EXECUTOR_SLOT`

Next operational action:
1. wait for a legal Test Executor daily slot;
2. refresh Test Executor to the canonical GitHub head;
3. run exactly one offline self-test on SHA `2ab1203788747e857d1fb89a3e849e0d8eb47b6cdd000e13875cf683811fb2a2`;
4. only if PASS, create a separate one-run public-research execution approval;
5. check the rate slot again and run once if available.

No alternate execution plane and no rate-limit bypass.
