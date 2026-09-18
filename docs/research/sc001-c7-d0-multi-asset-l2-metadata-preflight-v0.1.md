# SC001 — C7-D0 Multi-Asset Historical L2 Availability Preflight v0.1

Date: 2026-09-18
Status: **FROZEN METADATA-ONLY / NO SPREAD OUTCOME / NO BODY DOWNLOAD**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.55.md`;
- `docs/research/sc001-c7-c10-no-alpha-data-structural-feasibility-audit-v0.1.md`.

## 1. Purpose

Verify whether the pre-existing SC001 non-BTC asset set has exact historical OKX 400-level L2 bodies available on one fixed ordinary weekday before any spread/headroom calculation or heavy multi-asset acquisition.

C7-D0 is metadata/source feasibility only.

## 2. Scientific distinction

C7 is not an E008 BTC same-rule rescue.

The D0 universe excludes BTC and uses the pre-existing SC001 cross-asset set:

- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

No asset is selected or dropped by historical PnL.

## 3. Frozen qualification date

Exact date:

`2024-02-12 UTC`

Selection rule:

`same ordinary weekday already used as the C10 engineering/calibration context; metadata-only reuse for C7 historical availability`.

D0 does not open any C7 historical body.

## 4. Current instrument semantics

For each exact swap:

`GET /api/v5/public/instruments?instType=SWAP&instId=<INST>`

Require:

- exact `instId`;
- `instType=SWAP`;
- `ctType=linear`;
- `settleCcy=USDT`;
- nonempty `uly`;
- `state=live`.

Current metadata is product mapping only, not historical performance evidence.

## 5. Historical L2 metadata source

Use the already-qualified OKX historical-data resolver:

`POST /priapi/v5/broker/public/trade-data/download-link`

with:

- `module="4"`;
- `instType="SWAP"`;
- `instQueryParam.instFamilyList=[<uly>]`;
- `dateQuery.dateAggrType="daily"`;
- exact 2024-02-12 UTC date bounds.

Expected filename exactly:

`<INST>-L2orderbook-400lv-2024-02-12.tar.gz`

Trusted URL:

- HTTPS;
- host begins with `static.okx.`;
- basename exact.

Use HEAD only.

## 6. Metadata/HEAD checks

For every asset require:

- exact trusted URL resolves uniquely;
- HEAD HTTP 200;
- final URL trusted;
- exact basename;
- positive Content-Length.

Record:

- current instrument mapping;
- exact filename;
- Content-Length;
- historical availability PASS/REVIEW.

Do not compare or rank archive sizes as a strategy criterion.

## 7. D0 PASS semantics

Exact PASS:

`C7_D0_MULTI_ASSET_L2_METADATA_PASS`

requires all 7 frozen assets to pass current instrument semantics and exact historical L2 metadata/HEAD.

REVIEW:

`C7_D0_MULTI_ASSET_L2_METADATA_REVIEW`

REVIEW is source/data feasibility only, not a C7 strategy verdict.

## 8. Firewalls

Must remain false:

- historical_l2_body_downloaded;
- historical_l2_body_opened;
- spread_calculated;
- top_of_book_depth_calculated;
- maker_order_simulated;
- fill_model_calculated;
- queue_model_calculated;
- adverse_selection_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 9. Consequence of PASS

Only after D0 PASS may C7-D1 be designed.

C7-D1 must still remain non-PnL and must prospectively freeze:

- a spread/headroom eligibility rule;
- historical calibration body budget;
- fee/adverse-selection structural reserve;
- staged acquisition cap.

No multi-asset L2 body acquisition is authorized by D0.
