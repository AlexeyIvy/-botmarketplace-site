# SC001 Current Roadmap and Stop Rules v5.27

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B15 MULTI-ROLE REVIEW COMPLETE / P1 SOURCE-AUDIT NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.26.md`

## 1. Background branches

B13-C:

protected prospective liquidation collection continues under systemd.

B14-A:

Sep25 P0 remains armed under systemd.

No design changes to either branch.

## 2. B15 multi-role review

Binding:

`docs/research/sc001-b15-independent-base-multi-role-critical-review-v0.1.md`

Review complete under:

- financial/economic;
- programmer + trader/execution;
- mathematics/statistics.

## 3. B15 shortlist

Lead:

`B15-P1_TRANSFERABILITY_SHOCK_CAPITAL_SEGMENTATION`

Reserve:

`B15-P3_FIXED_CONVERSION_REDEMPTION_ANCHOR`

Second reserve:

`B15-P2_SCHEDULED_DELISTING_FORCED_CLOSE`

No candidate ID assigned.

## 4. Why P1 leads

P1 has:

- independent structural payer;
- plausible large edge scale under broken arbitrage connectivity;
- potentially two initial market fills with pre-positioned inventory;
- lower latency dependence than ordinary cross-venue dislocation;
- clean conceptual independence from terminal SC001 mechanisms.

## 5. P1 hard gate

No price outcome is authorized.

Next stage:

`TRANSFERABILITY_SHOCK_SOURCE_ACCESS_SEMANTIC_FEASIBILITY_AUDIT`

Must verify:

- authoritative status source;
- public/authenticated access;
- causal state-change timestamps;
- exact chain/network identity;
- exact cross-venue asset identity;
- pre-positioned inventory architecture;
- post-reopen rebalance path;
- clean prospective event path.

## 6. Stop rule

If authoritative transferability state cannot be collected prospectively and causally, P1 is not allowed to proceed to price/headroom testing.

Do not replace missing transfer-status evidence with inferred price gaps.

## 7. Immediate next action

Perform B15-P1 source/access/semantic feasibility audit only.

No price, spread, PnL or winner-venue selection.
