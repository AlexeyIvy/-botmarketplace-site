# SC001 — C1 SPOT Body Integrity Results v0.1

Date: 2026-09-18  
Status: **PASS — CONTAMINATED-SANDBOX SPOT DATA READY / NO ALPHA COMPUTED**  
Scope: `SCALPING RESEARCH / SC001`

## 1. Exact terminal result

The frozen C1 SPOT body acquisition/integrity runner completed on the qualified VPS with exact:

`C1_SPOT_BODY_INTEGRITY_PASS`

Exit code:

`C1_SPOT_BODY_EXIT_CODE=0`

## 2. Qualified source totals

- archive files qualified: `256 / 256`;
- reconstructed UTC asset-days qualified: `240 / 240`;
- contaminated performance asset-days: `224`;
- boundary warm-up/source-support asset-days: `16`;
- downloaded files: `256`;
- reused files: `0`;
- qualified total bytes: `273358764`.

The frozen parent metadata manifest remained the exact previously recorded identity:

- SHA256: `bfa403c5b53b2a95c0df28fd41d3382667fe0c6ced223b65f451e7b99ecd1023`;
- bytes: `118273`.

## 3. Scope

The qualified C1 SPOT universe remains exactly:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP and BCH versus USDT on OKX.

Source-label windows remain only:

- `2024-06-30..2024-07-15`;
- `2024-08-31..2024-09-15`.

Performance-role dates remain only:

- `2024-07-01..2024-07-14`;
- `2024-09-01..2024-09-14`.

Boundary labels remain source-support only.

## 4. Integrity/causality qualification

All 256 source archives passed the frozen identity/integrity path and all 240 target UTC asset-days passed causal D + D+1 reconstruction.

Minute-bucket sparsity is diagnostic only under this stage and does not modify the strategy or select observations. The final displayed BCH examples retained zero trade-id gap events while minute coverage varied, consistent with the frozen protocol's diagnostic treatment.

## 5. No-alpha firewalls

The terminal report confirmed:

- `strategy_signal_calculated=false`;
- `sentinel_outcome_calculated=false`;
- `basis_calculated=false`;
- `returns_calculated=false`;
- `pnl_calculated=false`;
- `promotional_alpha_accessed=false`.

No protected holdout or Confirmation access is authorized or implied by this PASS.

## 6. Consequence

C1 contaminated-sandbox SPOT data engineering is complete.

This PASS is **data readiness only**. It is not evidence that C1 is profitable or executable.

The next required gate before any C1-C6 sentinel outcome is:

1. shared causal trade/bar/return utility implementation;
2. synthetic/golden causality tests;
3. exact implementation freeze;
4. only then frozen C1-C6 sentinel runners under the unchanged first-pass budget of **11 variants**.
