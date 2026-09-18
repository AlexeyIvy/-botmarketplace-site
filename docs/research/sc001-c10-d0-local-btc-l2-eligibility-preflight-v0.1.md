# SC001 — C10-D0 Local BTC L2 Eligibility Preflight v0.1

Date: 2026-09-18
Status: **FROZEN NO-ALPHA LOCAL-DATA PREFLIGHT**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.52.md`;
- `docs/research/sc001-c7-c10-no-alpha-data-structural-feasibility-audit-v0.1.md`.

## 1. Purpose

Verify that a previously qualified, already contaminated OKX BTC-USDT-SWAP L2 day exists locally and is eligible for the first C10 book-state structural pilot.

No L2 body is opened in D0.

## 2. Scientific distinction

C10 is not C5 + L2.

C10 core state must be defined directly from order-book primitives.

C5 aggressive-flow labels, C5 event timestamps and RB005 are excluded from the initial C10 base mechanism.

## 3. Frozen pilot-day selection rule

Existing qualified BTC L2 candidate set:

- 2024-01-14 — ordinary weekend;
- 2024-01-31 — FOMC event day;
- 2024-02-12 — ordinary weekday;
- 2024-02-13 — CPI event day.

Freeze pilot day:

`2024-02-12 UTC`

Selection rule:

`the ordinary weekday in the already-qualified four-day Q1 BTC L2 set`.

This is metadata/context selection only and is fixed before any C10 book-state outcome.

## 4. Exact source identity

Expected L2 body:

`BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz`

Expected byte size:

`601,976,188`

Expected local root:

`~/sc001_data/SC001_DATA_Q009B_OKX_L2_BATCH_B/2024-02-12/`

Parent Q009B report:

`~/sc001_data/SC001_DATA_Q009B_OKX_L2_BATCH_B/sc001_data_q009b_okx_l2_batch_b_report.json`

Parent E008 inventory report:

`~/sc001_data/SC001_E008_DATA_INVENTORY/sc001_e008_data_inventory_report.json`

## 5. Required parent states

Q009B must have:

- stage `SC001-DATA-Q009B-OKX-L2-Q1-BATCH-B`;
- overall_status `PASS`;
- 2024-02-12 day status `FULL_DAY_PASS`;
- archive identity and SHA metadata present.

E008 inventory must have:

- status `E008_DATA_INVENTORY_PASS`;
- exact 2024-02-12 L2 identity present at expected size.

## 6. Local file checks

D0 may:

- stat the exact file;
- compare basename;
- compare byte size;
- verify parent metadata strings.

D0 must not:

- hash the L2 body;
- open tar/gzip;
- parse any L2 record;
- calculate book state;
- calculate event frequency;
- calculate future move;
- calculate PnL.

## 7. Exact terminal states

PASS:

`C10_D0_LOCAL_L2_ELIGIBILITY_PASS`

REVIEW:

`C10_D0_LOCAL_L2_ELIGIBILITY_REVIEW`

REVIEW is a local-data/engineering state only.

## 8. Firewalls

Must remain false:

- l2_body_opened;
- l2_body_hashed_by_c10_d0;
- book_feature_calculated;
- liquidity_vacuum_event_calculated;
- future_move_calculated;
- strategy_signal_calculated;
- fill_model_calculated;
- queue_model_calculated;
- pnl_calculated;
- c5_labels_used;
- promotional_alpha_accessed.

## 9. Consequence of PASS

Only after exact D0 PASS:

1. update the contamination registry explicitly for C10 reuse;
2. freeze one objective book-state event family;
3. freeze one future-move horizon and structural gates;
4. freeze a body-reading runner;
5. only then open the L2 body for C10.
