# SC001 Current Roadmap and Stop Rules v3.8

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — E008 FORENSIC COMPLETE / MULTI-ASSET RESEARCH ARCHITECTURE OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.7.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact:

`E008_DISCOVERY_FAIL`

No rescue-tuning, no promotional rerun, no E008 Confirmation, no Q2/formal Validation/Final.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. E008 read-only forensic chain complete

Completed without strategy rerun:

- `E008_READONLY_POSTMORTEM_PASS`;
- `E008_READONLY_MICROSTRUCTURE_FORENSIC_PASS`;
- forensic exit code = `0`.

E008 terminal decision remained unchanged.

## 3. Main E008 forensic conclusions

### Economics

- primary cycles = `2058`;
- forced-taker share ~= `99.514%`;
- mean realized fee drag ~= `6.9853 bps/cycle`;
- mean net edge ~= `-8.5296 bps/cycle`;
- mean gross edge already negative at about `-1.544 bps/cycle`;
- primary gross-positive share ~= `39.456%`;
- long-first mean gross/net ~= `-1.655 / -8.640 bps`;
- short-first mean gross/net ~= `-1.426 / -8.412 bps`.

Therefore E008 failure is not explained by fees alone. Frozen realized gross economics were already negative.

### Spread feasibility

Deep forensic classified:

- `MEAN_SPREAD_BELOW_MAKER_MAKER_FEE_FLOOR`;
- `SPREAD_RARELY_COVERS_4BPS_FEE_FLOOR`.

Thus naive regular-user top-of-book BTC spread capture is structurally unattractive on these inspected days even before considering realistic adverse selection and queue uncertainty.

### Execution-model risk

Observed:

- `prior-best disappearance events = 605,477`;
- `snapshots = 11,520` = exactly `1,440/day` across eight days;
- primary duration p50/p90/p99 ~= `60,632 / 61,732.3 / 64,098.45 ms`;
- semantic >5s gaps = `0`.

The forensic retained material-model-risk flags for:

- zero cancellation credit;
- all additions ahead;
- own-order absence from exogenous historical book;
- periodic snapshot cancellation semantics.

These findings mean the frozen E008 simulator should not be reused as a central FIFO estimator. They do **not** reopen E008.

## 4. Research architecture updated

Current architecture document:

`docs/research/sc001-next-generation-multi-asset-research-framework-v0.2.md`

This v0.2 incorporates the completed E008 forensic and becomes the working design source for the next SC001 phase.

Core changes:

- economics-feasibility before heavy execution simulation;
- historical multi-asset universe rather than BTC-only evidence;
- contamination registry;
- survivorship/look-ahead controls;
- instrument-day / cluster-aware statistics;
- multiple-testing ledger;
- integer tick/lot execution state;
- historical instrument/fee/funding freeze;
- own-order overlay;
- queue uncertainty bounds rather than one false FIFO estimate;
- exact-price versus price-through distinction;
- periodic snapshot != own-order cancellation;
- taker exits from opposite-side L2;
- message-rate / rate-limit feasibility;
- fresh Discovery after any execution-model redesign.

## 5. Provisional multi-asset design

Target first generation:

- roughly `10` instruments;
- acceptable range `8-12` if historical eligibility/data constraints require it;
- initially one comparable venue/product family;
- universe frozen using only pre-period information;
- stratified liquidity rather than only current top coins;
- no per-asset retuning during strict replication.

Exact symbols are not yet frozen.

## 6. Legacy Replication Program priority

All prior terminal verdicts remain immutable. Any replication receives a new experiment ID.

Provisional order:

1. E007 mechanism — highest priority strict multi-asset replication;
2. E006 mechanism — multi-asset spot/perp basis replication;
3. E002 TFI — auxiliary/incremental feature only;
4. E004 — lower-priority strict replication;
5. E003/E001 — low priority absent a concrete forensic reason;
6. E005 — no independent priority;
7. E008 — no promotional rerun; passive-maker only as a new family with execution v2 and fresh data.

## 7. Current hard gate

Do **not** open a new promotional strategy yet.

Next research stage is architecture/data design only:

1. historical universe selection protocol;
2. machine-readable contamination registry;
3. metadata-only historical universe audit;
4. first frozen multi-asset universe;
5. execution-model v2 engineering protocol;
6. execution-model v2 mechanical validation on engineering/contaminated data only;
7. fresh Discovery/Confirmation chronology freeze;
8. only then first new replication/promotion candidate.

## 8. Storage/compute constraint

Current VPS remains usable for initial sequential multi-asset work:

- 4 vCPU;
- 8 GB RAM;
- 80 GB NVMe.

BTC E008 eight-day L2 size was ~3.725 GB compressed. Ten comparable symbols could approach ~37 GB compressed L2 before reports/temp/existing data.

Operating rules:

- stream archives;
- process sequentially or max one/two heavy jobs;
- preserve 15-20 GB free reserve;
- SHA-verify every body;
- increase storage to ~200-500 GB if multi-asset L2 becomes the permanent workflow.

## 9. Immediate next action

No further E008 strategy command.

Next implementation work should create the historical-universe selection protocol and contamination registry, then perform a metadata-only audit before freezing symbols or downloading a large multi-asset body set.
