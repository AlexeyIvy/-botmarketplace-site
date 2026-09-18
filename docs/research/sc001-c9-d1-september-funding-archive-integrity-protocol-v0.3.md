# SC001 — C9-D1 September Funding Archive Integrity Protocol v0.3

Date: 2026-09-18  
Status: **FROZEN IMPLEMENTATION REPAIR AFTER OCTOBER FUNDING-BODY ACCESS INCIDENT / DATA-ONLY**  
Scope: `SCALPING RESEARCH / SC001`  
Supersedes: `sc001-c9-d1-september-funding-archive-acquisition-integrity-protocol-v0.2.md`

## 1. Trigger

C9-D1 v0.2 returned:

`C9_D1_V02_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

A metadata-only audit then established that the historical metadata query returned both September and October funding ZIPs for each asset, and v0.2 downloaded/opened both before applying row timestamp bounds.

Binding incident record:

`docs/research/sc001-c9-d1-v0.2-october-funding-body-access-incident-v0.1.md`

Current contamination registry:

`docs/research/sc001-contamination-registry-v0.8.json`

## 2. Research status

This incident is not a C9 strategy result.

No return, state-transition outcome, strategy signal, threshold, event window or PnL was calculated.

However, October 2024 funding data for the eight C9 assets is now nonpromotional for any future C9 implementation using funding-state evidence.

October trade/SPOT/L2/mark/index channels remain separately governed and were not opened by this incident.

## 3. v0.3 exact-file rule

For each target instrument `INST`, the only body v0.3 may read is exactly:

`INST-fundingrates-2024-09.zip`

Examples:

- `BTC-USDT-SWAP-fundingrates-2024-09.zip`;
- `ETH-USDT-SWAP-fundingrates-2024-09.zip`.

The metadata response may contain other file nodes, including October.

v0.3 must:

- ignore all non-September file nodes;
- not HEAD them;
- not download them;
- not hash them;
- not open them;
- not inspect their CSV contents.

Exactly one September file must remain after filtering for each target instrument.

## 4. D0 identity reconciliation

The D0 v0.2 parent metadata may contain both September and October file nodes.

v0.3 must extract from D0 exactly the row whose filename equals:

`INST-fundingrates-2024-09.zip`

and require:

- host = `static.okx.com`;
- positive frozen Content-Length;
- exactly one matching row.

The current official metadata query must return the same exact September filename.

Current HEAD Content-Length for that exact September file must equal D0.

## 5. Local reuse

The already-downloaded September file from prior D1 attempts may be reused only if:

- exact path is constructed from the frozen September filename;
- local byte size equals D0 Content-Length;
- current metadata identity matches;
- current HEAD Content-Length matches;
- SHA256 is recomputed;
- ZIP CRC passes;
- CSV schema/target-row integrity passes.

The presence of a sibling October file in the same directory is ignored and must not be touched.

Do not delete prior October files; retain them as audit artifacts.

## 6. Authorized timestamp interval

For rows parsed from the exact September ZIP only, admit target funding timestamps in:

`2024-08-31T16:00:00Z <= funding_time <= 2024-09-30T16:00:00Z`

The exact end boundary is allowed.

Any target row outside that interval is a hard REVIEW.

## 7. Funding integrity checks

For each target instrument:

- target identity exact;
- funding rate finite decimal;
- timestamp positive Unix milliseconds;
- identical duplicate timestamps may deduplicate only if rate identical;
- conflicting duplicate rate is hard failure;
- >=80 unique timestamps;
- strictly increasing unique timestamp sequence;
- first coverage gap <=8h from source start;
- last coverage gap <=8h to source end boundary;
- all consecutive intervals >0;
- maximum consecutive interval <=8h.

Record only:

- row count;
- first/last timestamps;
- observed interval-hour set;
- exact September archive bytes/SHA256.

Funding-rate values are validated but not stored in the report or used for strategy design.

## 8. Exact universe

Exactly:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

## 9. Exact terminal states

PASS:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS`

REVIEW:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_REVIEW`

REVIEW remains implementation/data state only.

## 10. Report semantics

The v0.3 report must distinguish current-run access from historical incident state.

Must state:

- `october_funding_body_accessed_by_v03=false`;
- `prior_october_funding_contamination_known=true`;
- `october_funding_clean_c9_confirmation_eligible=false`;
- `mark_index_values_opened_by_v03=false`;
- `funding_values_used_for_strategy=false`;
- `returns_calculated=false`;
- `basis_transition_calculated=false`;
- `strategy_signal_calculated=false`;
- `sentinel_outcome_calculated=false`;
- `pnl_calculated=false`;
- `direction_selected=false`;
- `threshold_selected=false`;
- `event_window_selected=false`;
- `promotional_alpha_accessed=false`.

It must not falsely claim that October funding has never been accessed.

## 11. Consequence of PASS

PASS establishes the integrity and timestamp/interval semantics of the exact September funding archive only.

It does not establish C9 predictive value or profitability.

Only after PASS may a separate C9 state-transition sentinel be designed. Any future clean Confirmation using funding state must use a prospectively frozen period other than October 2024.
