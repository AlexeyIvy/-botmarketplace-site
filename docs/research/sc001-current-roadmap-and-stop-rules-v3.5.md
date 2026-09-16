# SC001 Current Roadmap and Stop Rules v3.5

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP SNAPSHOT — E008 TERMINAL DISCOVERY FAIL**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.4.md`

## 1. Independence / terminal history

SC001 remains fully independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`. Nothing in SC001 may change their frozen rules, decisions or forward clocks.

E001-E007 remain terminal/closed and must not be rescue-tuned.

E008 is now also terminal/closed after its single frozen promotional Discovery run.

Confirmation / Q2 / formal Validation / Final remain CLOSED.

## 2. E008 pre-Discovery gates completed

The following frozen prerequisites passed before maker economics were opened:

- `E008_DATA_INVENTORY_PASS`;
- `E008_STALE_LATCH_MODEL_PASS`;
- `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22;
- `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`, 4/4;
- `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`;
- `E008_DISCOVERY_ACQUISITION_PREFLIGHT_PASS`;
- `E008_DISCOVERY_TRADES_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_A_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_B_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_C_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_D_ACQUISITION_PASS`;
- `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`, 24 verified files;
- `E008_DISCOVERY_SEMANTIC_PREFLIGHT_PASS`;
- `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`, 8/8 `DAY_PASS`;
- `E008_MAKER_DISCOVERY_IMPLEMENTATION_PREFLIGHT_PASS`;
- `E008_MAKER_DISCOVERY_IDENTITY_GATE_PASS`;
- verified frozen implementation files = 8;
- verified market source files = 24.

Thus the promotional run was reached without weakening chronology, source identity, queue mechanics, stale handling, fees, latency, inventory limits or promotion gates.

## 3. Frozen promotional Discovery chronology

Discovery dates used exactly once:

- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

Frozen Confirmation dates remain unopened:

- 2024-01-08
- 2024-01-28
- 2024-02-10
- 2024-02-20

No date substitution is permitted.

## 4. Terminal promotional result

Exact terminal state observed on VPS:

`E008_DISCOVERY_FAIL`

Discovery runner exit code: `2`.

Primary scenario summary:

- completed cycles: `2058`;
- pooled mean net edge: `-8.529577668464214 bps/cycle`;
- 10% trimmed mean net edge: `-8.452193724687486 bps/cycle`;
- pooled median net edge: `-8.329689062082062 bps/cycle`;
- positive days: `0 / 8`;
- forced taker exit share: `0.9951409135082604` (~99.51%);
- day-block bootstrap 95% LCB: `-8.82276022998123 bps`.

Frozen stress scenarios:

- 500 ms latency mean net edge: `-8.777647506060696 bps/cycle`;
- 2x initial queue-ahead mean net edge: `-8.688137818976038 bps/cycle`.

These results are far below the frozen promotion requirements and are not borderline.

## 5. Failed gates recorded by the frozen runner

The terminal report recorded failures for:

- `source_data_integrity_8_of_8`;
- `unresolved_inventory_eq_0`;
- `forced_taker_exit_share_lte_10pct`;
- `pooled_mean_net_edge_gte_1bps`;
- `trimmed_mean_gte_0_5bps`;
- `pooled_median_gte_0`;
- `positive_days_gte_6_of_8`;
- `median_daily_mean_gt_0`;
- `day_block_bootstrap_95pct_lcb_gt_0`;
- `top1_abs_daily_contribution_lte_0_30`;
- `top3_abs_daily_contribution_lte_0_65`;
- `primary_invariants_exact_pass`;
- `latency_500ms_mean_gte_0`;
- `latency_500ms_total_net_pnl_gt_0`;
- `queue_2x_mean_gte_0`;
- `queue_2x_unresolved_eq_0`.

The high cycle count does not rescue E008: the economics are materially negative, every Discovery day is non-positive by the frozen daily gate, forced taker exits dominate, and both predeclared stress scenarios remain materially negative.

## 6. Semantic-integrity naming note discovered after the terminal run

The frozen runner's gate named `source_data_integrity_8_of_8` is implemented as `primary["valid_days"] == 8`, where `valid_days` derives from execution-day validity and includes unresolved/invariant execution conditions.

Therefore that gate label conflates source-data integrity with execution validity. It must **not** be interpreted as overturning the earlier independent `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`, which had already qualified all eight source days as exact `DAY_PASS` before maker simulation.

This is a reporting/label-semantics note only. It does not change the terminal E008 result because multiple independent economics and execution gates failed by large margins. It does not authorize a rerun, code alteration, date substitution or gate reinterpretation.

## 7. E008 stop rules now binding

E008 is terminal failed. Therefore do not:

- rerun the promotional Discovery to seek a different outcome;
- tune TTL, latency, max hold, order size, fee assumptions or funding windows;
- weaken queue-ahead or stale-latch rules;
- credit cancellations or level disappearance as fills;
- add VIP/rebate assumptions;
- cherry-pick dates, sides, hours or subsets;
- add TFI or prior SC001 features to rescue E008;
- open E008 Confirmation;
- open Q2 / formal Validation / Final from E008.

The frozen Discovery report remains the canonical E008 promotional outcome:

`~/sc001_data/SC001_E008_MAKER_DISCOVERY/sc001_e008_maker_discovery_report.json`

## 8. Interpretation retained for future research

E008 falsifies this specific frozen hypothesis: a conservative top-of-book passive maker/spread-capture strategy with full displayed queue-ahead, zero cancellation credit, fail-closed stale handling, regular-user fees, 250 ms primary latency, 30 s quote TTL, 60 s max inventory hold, and +/-1 contract inventory does not demonstrate viable Discovery economics on the eight frozen OKX BTC-USDT-SWAP days.

The dominant observed mechanism is not event scarcity: there were 2058 completed primary cycles. Rather, the frozen execution model produced near-universal forced exits and materially negative net edge, with no positive Discovery days and negative latency/queue stresses.

This result may inform the design of a **new independently frozen experiment family**, but E008 itself must not be modified or rescued.

## 9. Immediate next action

Do not execute any further E008 strategy command.

Next SC001 work, if continued, must begin as a new hypothesis/experiment with a new predeclared protocol and no post-hoc reuse of E008 outcomes to alter E008 itself. Before opening a new promotional experiment, first perform a read-only E008 postmortem focused on reusable mechanism lessons (forced-exit dominance, inventory-hold dynamics, queue economics and fee burden) without changing the terminal E008 decision.
