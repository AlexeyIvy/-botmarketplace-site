# SC001-E004 — Implementation Preflight Specification v1.1

Date: 2026-09-15  
Status: **FROZEN PREFLIGHT SPECIFICATION — NOT YET EXECUTED**  
Protocol: `sc001-e004-volatility-compression-breakout-executable-protocol-v1.0.md`  
Supersedes: `sc001-e004-implementation-preflight-spec-v1.0.md`

## 0. Reason for v1.1 and no-alpha correction boundary

Preflight v1.0 incorrectly required each individual OKX archive labeled date `D` to have all source timestamps inside UTC date `D`.

That conflicts with the already-qualified Q006R source semantics established before E004: OKX daily trade packaging is not aligned to UTC midnight; exact archive `D` begins around 16:00 UTC on the previous calendar date, and a complete UTC day `D` must be reconstructed from archive labels `D` and `D+1`, retaining only target rows in `[D 00:00:00.000 UTC, D+1 00:00:00.000 UTC)`.

This v1.1 correction is strictly a data/preflight-spec repair made before any E004 alpha output. It does **not** change:

- the E004 v1.0 financial hypothesis;
- the 15-minute compression window;
- 1,440-minute q20 threshold lookback;
- false-to-true arming rule;
- 2 bps breakout buffer;
- 15-minute arm;
- 250 ms primary latency;
- 15-minute holding horizon;
- cooldown/daily cap;
- Discovery/Confirmation dates;
- economics gates;
- diagnostic neighborhood.

No E004 return, trade, aggregate alpha metric or direction-specific performance result had been emitted before this repair.

## 1. Purpose

Prove that the implementation reproduces the frozen E004 v1.0 semantics without reading or emitting E004 returns during preflight. Preflight is a non-alpha software/data audit. DEV-DISCOVERY is forbidden until a complete machine-readable report returns exact terminal token:

`PREFLIGHT_PASS`

## 2. Output suppression firewall

Preflight may output counts, timestamps, hashes, schema checks, state-transition counts on synthetic fixtures and invariant results.

On real March data it must not output or persist:

- entry or exit prices;
- signed directions paired with future prices;
- per-trade returns;
- aggregate or daily return statistics;
- latency performance comparisons;
- any information that reveals whether E004 is profitable.

If the engine architecture cannot suppress these fields reliably, preflight FAILs.

## 3. Required code identity

Before execution record:

- repository and branch;
- full Git commit SHA;
- SHA256 of the frozen configuration file;
- SHA256 of the engine and preflight runner;
- Python version, OS and timezone;
- exact command;
- output directory;
- input manifest path.

Working tree must be clean or the report must hash and enumerate every modified executable/config file. Preferred result is a clean committed state.

## 4. Corrected Q006R source/data checks

Authoritative source semantics are the already-qualified Q006R UTC reconstruction used by the March E003 trade stage.

For E004 v1.0 use only the already-open March 2024 OKX `BTC-USDT-SWAP` archives from the qualified March source manifest. No network acquisition is authorized.

### 4.1 Archive-label checks

For every required archive label:

- explicit expected filename/date-label mapping;
- exact byte size from the qualified source manifest;
- exact SHA256 from the qualified source manifest;
- readable ZIP;
- ZIP CRC PASS;
- exactly one expected CSV member;
- exact six-column schema resolvable as:
  - `instrument_name`;
  - `trade_id`;
  - `side`;
  - `price`;
  - `size`;
  - `created_time`;
- finite positive target-instrument prices/sizes;
- timestamps parse as UTC with the qualified numeric-scale resolver;
- deterministic original source sequence exists;
- source timestamps are nondecreasing;
- source target trade IDs are strictly increasing within each archive;
- duplicate timestamp counts may be nonzero and must be reported;
- no silent deduplication.

**Do not require an individual archive label `D` to be bounded by UTC date `D`.** Its full-file min/max timestamps are diagnostics and are expected to reflect OKX's non-UTC packaging boundary.

### 4.2 UTC target-day reconstruction

For each target UTC date `D`, read exactly archive labels:

- `D`;
- `D+1`.

Admit only target-instrument rows whose parsed timestamp lies in:

`[D 00:00:00.000 UTC, D+1 00:00:00.000 UTC)`.

After admission require:

- all admitted rows lie in the target UTC interval by construction;
- target timestamps are nondecreasing in deterministic `(timestamp_ms, original_sequence)` order;
- target trade IDs have zero duplicate/backward count;
- both `buy` and `sell` occur;
- all 1,440 UTC minute buckets are represented;
- admitted row count > 0.

Trade-ID gaps are reported and are not by themselves a failure unless they imply duplicate/backward/ordering corruption or contradict the already-qualified source manifest.

### 4.3 Required dates

For DEV-DISCOVERY/preflight:

- reconstructed target UTC days: 2024-03-01 through 2024-03-20;
- source archive labels required: 2024-03-01 through 2024-03-21 inclusive because March 20 requires D+1;
- already-open later March archives may remain present locally but must not be used to compute Discovery alpha or preflight state beyond the permitted target dates.

No April/Q2 archive may be opened.

Any missing/unqualified required source file is FAIL.

## 5. Synthetic causal fixtures

The test suite must use hand-built prices with analytically known outcomes and assert all of the following:

1. a trade exactly at minute boundary `t` is excluded from `[t-15m,t)`;
2. a trade one millisecond before `t` is included;
3. `H_t`, `L_t`, `M_t`, and `C_t` match hand calculations;
4. the threshold uses exactly the preceding 1,440 minute values and excludes `C_t`;
5. nearest-rank q20 selects 1-based rank 288 with no interpolation;
6. eligibility is false with 1,439 prior values and true with 1,440;
7. compression equality `C_t == Q_t` is true and its tie is counted;
8. arming occurs only on false-to-true transition;
9. a band freezes at arming and does not drift with later prices;
10. equality to `U` or `D` does not trigger;
11. strict crossing does trigger;
12. original sequence deterministically resolves same-timestamp ordering;
13. arm expiry boundary semantics match the protocol;
14. 250 ms entry uses the first trade at or after target time;
15. no trade within the 5,000 ms entry tolerance creates an incomplete episode;
16. exit horizon begins at actual entry, not decision;
17. exit uses first trade at or after 900,000 ms;
18. no exit within tolerance creates an incomplete trade;
19. UTC-day crossing is incomplete and never carried;
20. no overlap, pyramiding or reversal occurs;
21. cooldown blocks arming for exactly 15 minutes;
22. the fifth daily decision is blocked;
23. day reset clears transient trading state but not historical indicator warm-up;
24. LONG and SHORT gross-return sign formulas match hand calculations;
25. 500/1,000 ms variants reuse the frozen primary decision events and change latency only.

Every fixture must have an expected-output object checked by exact equality where possible and tight numeric tolerance only for floating-point formulas.

## 6. Frozen implementation boundary resolutions

These are implementation clarifications of v1.0, not new financial parameters.

### 6.1 Indicator state across UTC days

Historical minute-range/compression state required for the 1,440-minute threshold carries across UTC day boundaries. Transient trading state (`ARMED`, `PENDING_ENTRY`, `OPEN`, `COOLDOWN`, `DAY_LOCKED`, daily decision count) resets at UTC midnight.

The previous compression flag `Z_{t-1}` is part of indicator chronology and therefore carries across the day boundary once threshold eligibility exists.

### 6.2 Arm-time boundary

Breakout inspection begins strictly after the arming timestamp. A raw trade with `timestamp_ms == arm_timestamp_ms` is not a breakout for that newly created arm.

This preserves causality because the arm is created only after the minute-boundary statistic is known.

### 6.3 Arm-expiry boundary

Protocol wording "no later than expiry" is implemented inclusively:

`arm_timestamp < trade_timestamp <= expiry_timestamp`.

A strict boundary crossing exactly at expiry is eligible; a later trade is not.

### 6.4 Cooldown boundary

Cooldown is half-open:

`[cooldown_start, cooldown_start + 15 minutes)`.

At exactly `cooldown_end`, the state may return to `IDLE` before evaluating that minute's arming condition.

### 6.5 Entry/exit tolerance boundary

A proxy trade exactly `5,000 ms` after the target time is within tolerance and eligible. A later print is not.

### 6.6 Daily-decision counter

The four-per-day cap counts breakout decisions, whether the later proxy entry/exit completes or not. The fourth decision immediately locks further decisions for that UTC day after that episode is processed as required by the state chronology.

## 7. Metamorphic/property tests

The implementation must PASS:

- multiplying every price by a positive constant leaves compression bps, flags, decisions and gross returns unchanged within tolerance;
- adding future trades cannot change any earlier indicator, arm or decision;
- chunked/day-by-day processing equals single-stream processing exactly;
- two consecutive identical runs produce byte-identical deterministic artifacts except explicitly excluded runtime timestamps/resource measurements;
- diagnostic configurations cannot execute before the primary verdict file exists;
- Confirmation paths cannot be addressed while Discovery status is not the exact PASS token;
- Q2/Validation/Final paths are rejected;
- TFI/FLOW_IMPULSE fields are absent from configuration and decision code paths.

## 8. Real-data dry run without alpha

Run the parser and causal state machine on reconstructed target UTC days 2024-03-01..20 with return calculation and future-price export disabled.

Allowed checks:

- first eligible minute equals `2024-03-02 00:15 UTC`;
- number of evaluated/eligible minutes;
- missing-window counts;
- compression/tie counts without threshold/range/price values;
- arm, expiry, decision, incomplete and daily-lock counts, aggregated only;
- maximum concurrent positions;
- maximum decisions per day;
- earliest/latest decision timestamps without direction;
- invariant violations;
- memory peak and wall time.

No count may be used to retune the protocol. A surprising but valid count does not authorize parameter changes.

## 9. Artifact/schema assertions

Preflight must verify that a future authorized Discovery run will write:

- frozen config and config SHA256;
- input manifest;
- deterministic event/trade schema;
- daily metrics schema;
- aggregate metrics schema;
- run-state with explicit phase and terminal token;
- atomic writes via temporary file then rename;
- refusal to overwrite an existing completed output directory unless a new explicit directory is supplied.

Forbidden fields/files during preflight are scanned after execution. Presence of any return or price output is FAIL.

## 10. Resource and failure behavior

On the qualified Ubuntu 24.04 VPS:

- peak memory must remain below 6 GiB;
- free disk before run must exceed estimated required input/output footprint plus 10 GiB reserve;
- malformed data, missing file, invariant breach or output collision => nonzero exit;
- exceptions identify file/date/check without dumping credentials;
- IPs, passwords, SSH keys, API keys and credentials never enter artifacts.

Performance optimization may not change financial semantics.

## 11. PASS gate

Preflight status is exact `PREFLIGHT_PASS` only if:

- all corrected Q006R data checks PASS;
- all synthetic tests PASS;
- all metamorphic/property tests PASS;
- real-data no-alpha dry run PASSes;
- output firewall scan finds zero forbidden fields/files;
- every state invariant holds;
- resource gates PASS;
- configuration hash and code commit are recorded;
- report contains no E004 alpha.

Otherwise status is `PREFLIGHT_FAIL`; DEV-DISCOVERY remains blocked.

Fixes are permitted only for implementation/data-audit defects and must not alter the frozen financial protocol. After a fix, commit a new code identity and rerun the entire preflight.

## 12. Required report

Write `sc001_e004_preflight_report.json` containing at least:

- protocol version;
- preflight-spec version;
- status;
- code commit SHA;
- engine/preflight SHA256;
- config SHA256;
- environment;
- qualified input hashes;
- synthetic/metamorphic test counts and failures;
- real-data no-alpha audit counts;
- invariant results;
- forbidden-output scan;
- resource results;
- started/completed UTC timestamps.

Also write a short Markdown summary. Only the terminal status and non-alpha audit facts may be discussed before Discovery authorization.
