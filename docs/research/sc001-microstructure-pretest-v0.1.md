# SC001 Microstructure Pretest Freeze v0.1

Status: **FROZEN BEFORE MICROSTRUCTURE P&L**  
Project branch: **SC001**  
Purpose: define the data split, sampling calendar rules, execution model, event-stress layer, and anti-overfitting boundaries before bulk microstructure acquisition and before any new SC001 microstructure P&L is inspected.

## 1. Scope and non-goals

This document governs the next SC001 microstructure research phase after Q001/Q002/Q003/Q004/Q004R data qualification.

It does **not** define a profitable strategy, does **not** authorize real-money trading, and does **not** retroactively modify SC001-E001 or any independent frozen research branch.

The objective is to create a reproducible environment in which a future microstructure hypothesis can be developed on Development data, frozen, then evaluated once on Validation and finally once on Final.

## 2. Evidence already established

Q004R established that sampled OKX `BTC-USDT-SWAP` 400-level L2 prefixes from 2023-04-15, 2024-01-15, 2025-01-15 and 2026-07-15 support deterministic **price-level** replay using:

- first record `action=snapshot`;
- subsequent `action=update` records;
- keys `action, asks, bids, instId, ts`;
- book level shape `[price, size, orders]`;
- zero-size updates as level deletions;
- nondecreasing timestamps;
- no malformed-level, crossed-book, or empty-book failures in the frozen sampled prefixes.

Boundary: this supports spread/depth/imbalance analysis and conservative taker execution. It does **not** prove exact maker queue position, market-by-order priority, or profitability.

## 3. Qualification-only dates

The following dates were already inspected during data qualification and are permanently excluded from SC001 performance evaluation:

- 2023-04-15
- 2024-01-15
- 2025-01-15
- 2026-07-15

They may be used only for parser/replay/integrity engineering.

## 4. Chronological performance split

All dates are UTC calendar dates.

### Development
`2023-04-01` through `2024-06-30`

Permitted use: exploratory feature research, candidate generation, engineering diagnostics, and strategy design.

### Validation
`2024-07-01` through `2025-06-30`

Permitted use: one frozen-candidate evaluation per experiment ID. Validation results may not be used to edit that candidate and rerun under the same experiment ID.

### Final
`2025-07-01` through `2026-08-31`

Permitted use: one final evaluation only after the candidate has passed its frozen Validation gate. No rescue or tuning after Final inspection.

## 5. Statistical unit and dependence rule

Tick, order-book message, and individual trade counts are **not** treated as independent sample counts.

Primary inference units must be aggregated at a higher level such as:

- UTC day;
- macro-event instance;
- pre-registered block of adjacent time.

Bootstrap/confidence procedures must use day/event blocks, not IID individual fills or book updates.

## 6. Deterministic ordinary-day sampling

Ordinary days must be selected without looking at price, volatility, volume, P&L, spread, or strategy output.

### 6.1 Fixed seed

Seed string:

`SC001-MICRO-v0.1-20260911`

Hash function: SHA-256.

### 6.2 Quarterly strata

For each calendar quarter intersecting the frozen split, select:

1. one **weekday ordinary day** (Monday-Friday), and
2. one **weekend ordinary day** (Saturday-Sunday).

Selection is deterministic from SHA-256 over:

`seed | YYYY-QN | stratum`

The hash integer modulo the number of eligible dates selects the date after eligible dates are sorted ascending.

If the selected date is disallowed, remove it from the eligible set before hashing/modulo selection rather than selecting a replacement based on market data.

### 6.3 Ordinary-day exclusions

An ordinary-day candidate is ineligible if it is:

- outside the relevant split;
- one of the four qualification-only dates;
- an official CPI event day;
- an official US Employment Situation / NFP event day;
- an official scheduled FOMC decision day.

No exclusion may be based on realized return, volatility, liquidity, outage severity, news impact observed after the fact, or strategy profitability.

## 7. Macro-event stress sample

Primary event classes are frozen to:

1. US CPI release;
2. US Employment Situation / NFP release;
3. scheduled FOMC policy decision.

Primary sources must be official:

- BLS for CPI;
- BLS for Employment Situation;
- Federal Reserve for FOMC.

Investing.com or similar aggregators may be used for human cross-checking only, not as the canonical research source.

### 7.1 Event selection rule

For each event class and each calendar quarter intersecting the frozen split:

- collect all official event instances whose anchor timestamp lies inside the split;
- sort them ascending by UTC timestamp;
- choose exactly one event deterministically using SHA-256 over:

`seed | YYYY-QN | EVENT_CLASS`

modulo the number of eligible event instances.

No event is chosen because it produced a large BTC move.

### 7.2 Event anchors

- CPI: official scheduled CPI release timestamp.
- NFP: official scheduled Employment Situation release timestamp.
- FOMC: official policy statement / rate-decision release timestamp.

The FOMC press conference is not a separate primary event; it is covered by the primary FOMC window and may be tagged diagnostically.

### 7.3 Event windows

Primary stress window:

`[-30 minutes, +60 minutes]` around the official event anchor.

Diagnostics only:

- `[-5, +30] minutes`
- `[-60, +180] minutes`

Diagnostic windows may not be promoted post hoc into a new primary filter under the same experiment ID.

### 7.4 Event-calendar role

Macro events are initially a **diagnostic/stress layer**, not an entry filter.

The L2 book already contains the market reaction to the event. The calendar must not add synthetic spread/slippage adjustments on top of observed L2 merely because the timestamp is an event window.

Any future rule such as "do not trade CPI" requires a separate frozen experiment.

## 8. Venue roles

### Primary microstructure venue
OKX `BTC-USDT-SWAP`.

Reason: qualified replayable historical L2 allows direct spread/depth/imbalance and conservative taker execution modeling.

### Independent trade-level replication
Binance BTCUSDT USD-M aggTrades and Bybit BTCUSDT trades.

They are used for independent trade-flow diagnostics / replication where timestamps and instrument definitions permit.

### Cross-venue latency/arbitrage
Not part of the first microstructure candidate. A cross-venue millisecond strategy requires its own clock/latency qualification and separate experiment ID.

## 9. Execution model freeze

### 9.1 Primary execution
**Taker-only**.

Maker queue-position assumptions are forbidden in the primary candidate because price-level L2 does not prove our exact priority in queue.

### 9.2 Causality
A signal at timestamp `t` may use only records with timestamps `<= t`.

An order becomes eligible to interact with the market only at its simulated arrival time `t + latency`.

The fill uses the first qualified replay state at or after the simulated arrival timestamp.

### 9.3 Latency scenarios

Frozen scenarios:

- BASE: 100 ms
- STRESS: 250 ms
- SEVERE diagnostic: 500 ms

Zero-latency execution is not permitted as the primary result. A 0-50 ms scenario, if calculated later, is upper-bound diagnostic only.

### 9.4 Book consumption

For taker orders:

- cross the observed spread;
- consume visible price levels in order until requested notional is filled;
- include all consumed-level VWAP deterioration;
- reject/mark unfilled if requested size cannot be satisfied inside the qualified visible book according to the frozen execution engine.

No fill may occur at mid-price unless the actual opposite-side book permits it.

### 9.5 Depth-haircut robustness

Primary BASE: 0% visible-depth haircut.

Robustness diagnostics:

- STRESS: 25% haircut to displayed executable size;
- SEVERE: 50% haircut.

A haircut may reduce available quantity but may not improve price.

## 10. Fee and cost ledger

Observed L2 spread and depth impact are measured directly from replay and must not be replaced by a constant synthetic spread.

Exchange fee assumptions must be stored separately from book costs and versioned in the experiment manifest.

Until an official historical tier schedule is independently frozen, the candidate may not claim fee precision finer than the documented fee assumption used in that experiment.

At minimum every experiment must report:

- gross pre-fee edge;
- observed spread/depth execution cost;
- exchange taker fee;
- total net edge per trade after all costs.

Primary economic metric remains **NET EDGE PER TRADE AFTER COSTS**.

## 11. Full-day integrity gate

Every OKX L2 day used in P&L must pass a complete streaming replay/integrity audit before it is admitted into the experiment dataset.

Mandatory checks include:

- trusted source URL / manifest metadata;
- complete download or complete streamed source consumption;
- SHA-256 of retained source or documented streamed-source identity;
- valid gzip/tar structure;
- JSON parse success;
- required key set;
- correct instrument;
- valid `snapshot/update` actions;
- nondecreasing timestamps;
- valid `[price,size,orders]` levels;
- deterministic snapshot/update replay;
- no unexplained crossed book;
- no unexplained empty book;
- explicit record of any resynchronizing snapshots.

A failed data-integrity day is excluded for a **data-quality reason only**, never because of bad P&L. The exclusion reason must be recorded before strategy results for that day are inspected.

## 12. Data-acquisition safety

Phone storage remains the operational constraint.

Frozen safety policy:

- maximum network/download budget per run: 2,000,000,000 bytes;
- minimum free-storage reserve: 4,000,000,000 bytes;
- process one large raw L2 day at a time unless a later frozen collector proves a safer bound;
- no silent full-history tick/L2 download.

Preferred staged workflow:

1. download or stream one frozen day;
2. verify full integrity;
3. generate compact derived features / replay artifacts;
4. write source URL, size, SHA-256, parser version and processing manifest;
5. retain raw file until explicit deletion approval.

## 13. Development/Validation/Final firewall

### Development
Can be used to invent features, thresholds, holding rules and candidate logic.

### Candidate freeze
Before Validation, create a new experiment ID (for example `SC001-E002`) and freeze:

- signal formula;
- all thresholds;
- entry/exit rules;
- sizing;
- execution timing;
- fees;
- cost scenarios;
- latency;
- robustness gates;
- statistical tests.

### Validation
One frozen run. If the candidate fails, it is FAIL/WEAK according to its frozen gates. Any modification becomes a new experiment ID.

### Final
Opened once only for a candidate that already passed its Validation gate. No post-Final rescue under the same experiment ID.

## 14. Multiple-testing control

The research program must count distinct candidate hypotheses, not only the final winner.

At minimum the Development log must retain:

- number of strategy families examined;
- number of material parameterizations tested;
- number of candidates promoted to Validation;
- every Validation verdict.

A large search followed by one lucky winner must not be presented as if only one hypothesis had been tested.

## 15. Capital/discreteness

Capital sizes `$250 / $500 / $1,000 / $5,000` are evaluated only **after** a positive edge exists under the frozen cost/execution model.

Minimum order size, lot size, contract value, tick size and contract multiplier must be applied using period-appropriate instrument metadata where required.

No candidate may be rescued by choosing the most favorable capital bucket post hoc.

## 16. Status vocabulary

Use the existing SC001 vocabulary:

- FAIL
- WEAK
- PROMISING_SCREEN
- ROBUST_HISTORICAL_CANDIDATE
- ADVANCE_TO_FORWARD

A Development result alone cannot receive `ROBUST_HISTORICAL_CANDIDATE`.

## 17. Immediate next step

No strategy P&L is authorized yet.

Next action: build and freeze `SC001-MICRO-CALENDAR-v0.1`, containing:

- canonical official CPI/NFP/FOMC timestamps;
- deterministic quarterly ordinary weekday/weekend dates;
- deterministic quarterly event selections;
- split labels;
- permanent qualification exclusions;
- event-window labels;
- SHA-256 of the final manifest.

Only after that calendar manifest is frozen may staged bulk acquisition begin.

## 18. Anti-rescue rule

After the calendar manifest is frozen, no date may be added, removed, reclassified, or moved between Development/Validation/Final because of observed BTC movement, spread, volatility, strategy P&L, or apparent profitability.

Corrections are allowed only for objectively documented calendar/source/integrity errors and must be versioned as a new manifest revision with the original retained.
