# SC001-E004 — Implementation Preflight v0.1

Date: 2026-09-15  
Status: **PRE-ALPHA PREFLIGHT SPEC — MUST PASS BEFORE FIRST E004 OUTPUT**

Parent protocol: `docs/research/sc001-e004-volatility-compression-breakout-protocol-v0.1.md`.

The purpose of this preflight is to prove that the implementation matches the frozen causal protocol before any E004 return, gross-edge, candidate-count or diagnostic output is inspected.

A preflight PASS is an implementation/data-integrity result only. It is not evidence that E004 has alpha.

## 1. Hard sequencing rule

Required order:

1. frozen protocol committed;
2. E004 engine implementation committed;
3. implementation SHA recorded;
4. synthetic/unit preflight PASS;
5. real-source integrity-only preflight PASS;
6. preflight report committed or archived with immutable hashes;
7. only then may DEV-DISCOVERY alpha/gross-edge calculation start.

No E004 Discovery/Confirmation return metric may be produced before items 1-6 are complete.

## 2. Real-data output firewall during preflight

On the real March archives, preflight may inspect only:

- file presence;
- byte size;
- SHA256;
- ZIP integrity;
- CSV header/schema;
- target instrument identity;
- timestamp scale/order;
- trade-ID order/stitch continuity;
- UTC target-day filtering;
- admitted row counts;
- minute/second coverage counts;
- parser/runtime compatibility;
- protocol/implementation identity.

Preflight must **not** expose on real data:

- compression thresholds;
- compression event counts;
- breakout candidate counts;
- long/short counts;
- entry/exit prices;
- trade returns;
- gross edge;
- daily means;
- diagnostic scenario outputs;
- PASS/FAIL alpha gates.

Those belong to DEV-DISCOVERY only after preflight PASS.

## 3. Source-manifest checks

Use the already-qualified E003 March source report as the authoritative manifest unless a later non-alpha data-integrity report explicitly supersedes it.

Require:

- source stage status PASS;
- exactly the authorized March archive set;
- no Q2 market-data body accessed;
- no Validation/Final body accessed;
- no alpha/P&L calculated by the source stage;
- local archive filenames exactly match the manifest;
- local byte sizes exactly match;
- local SHA256 exactly match;
- ZIP CRC test PASS;
- one expected CSV member per ZIP;
- exact expected trade header.

Any mismatch => `E004_PREFLIGHT_FAIL`.

## 4. Parser and stitch checks

For every required target day used by the stage:

- parse `created_time` with the already-qualified timestamp-scale resolver;
- retain only `BTC-USDT-SWAP` rows in target UTC day;
- require finite positive price and size;
- require side in `{buy, sell}` even though side is not an E004 feature;
- require nondecreasing source timestamps;
- require strictly increasing source trade IDs;
- require no stitched target timestamp reversal;
- require strictly increasing stitched target trade IDs;
- require no stitched target trade-ID gap under the existing qualified Q006R semantics;
- require all 1440 UTC minutes represented by admitted trades.

Any failure is terminal preflight failure; do not silently drop or repair rows.

## 5. One-second VWAP synthetic tests

Use deterministic synthetic fixtures, not March alpha data.

Mandatory tests:

### P01 — exact bucket boundaries

Trades at `s` belong to `[s, s+1s)`.

A trade timestamped exactly `s+1s` belongs to the next second.

### P02 — size-weighted VWAP

For trades `(100, size 1)` and `(102, size 3)` in one second, require:

`P_s = 101.5`.

### P03 — invalid empty second

A second with no target trade produces no `P_s`; it must not be forward-filled.

### P04 — decision time

Information from second `[s, s+1s)` must not be available before `s+1s`.

## 6. Five-minute box synthetic tests

### P05 — UTC alignment

Five-minute blocks must be aligned to UTC multiples of 300 seconds, not aligned to the first observed trade.

### P06 — valid-second threshold

- 270 valid seconds => valid block;
- 269 valid seconds => invalid block.

### P07 — box extrema

`H_k` and `L_k` must be extrema of valid one-second VWAPs only, not raw individual trade prices.

### P08 — log-range formula

Require exact implementation of:

`R_k = 10,000 * ln(H_k / L_k)`.

No arithmetic simple-return substitute is permitted.

## 7. Rolling-compression synthetic tests

### P09 — exact warm-up

No compression test may occur before exactly 72 prior valid five-minute ranges exist.

### P10 — strict prior-only baseline

The current `R_k` must not enter the q20 window until after the current compression decision.

A fixture where including the current block would change q20 must prove that the implementation uses only the prior 72.

### P11 — nearest-rank q20

For exactly 72 sorted values, require zero-based index `14` (`ceil(0.20*72)-1`).

### P12 — strict compression inequality

- `R_k < threshold` => compression;
- `R_k == threshold` => no compression;
- `R_k > threshold` => no compression.

### P13 — day-local reset

No prior-day range may enter the new UTC day's 72-block baseline.

## 8. Arm and breakout state-machine tests

### P14 — one arm only

A qualifying compression block arms exactly one box for exactly 300 seconds.

### P15 — exact arm interval

The watch interval is `[block_end, block_end+300s)`.

A confirming one-second bucket whose decision time is after expiry must not trigger the expired box.

### P16 — strict upper breakout

- one-second VWAP `> H_k` => long candidate;
- one-second VWAP `== H_k` => no candidate.

### P17 — strict lower breakout

- one-second VWAP `< L_k` => short candidate;
- one-second VWAP `== L_k` => no candidate.

### P18 — first breakout wins

If upper and lower breaks occur at different times inside the same arm, the chronologically first qualifying closed second consumes the box; no second candidate may be emitted.

### P19 — expired box cannot be reused

If no breakout occurs during the 300-second arm, later crossing of that old box must produce no candidate.

### P20 — no retroactive arm

A block that closed while a position was open may update the rolling baseline but cannot later be armed after the position closes.

## 9. Entry/exit proxy tests

### P21 — primary latency

For primary scenario:

`entry_target = decision_ts + 250 ms`.

The fill must be the first admitted trade at or after that target.

### P22 — 500 ms stress

Stress scenario must use exactly 500 ms with all other primary settings unchanged.

### P23 — primary hold

`exit_target = decision_ts + latency + 600 s`.

The fill must be the first admitted trade at or after that target.

### P24 — same-timestamp stream order

When multiple trades share a millisecond, preserve qualified archive order and select the first admitted row at/after the target.

### P25 — day-end ineligibility

If intended `exit_target >= day_end`, candidate is ineligible before fill lookup.

### P26 — missing entry

If no entry trade exists before day end, candidate is unfilled and does not open a position.

### P27 — missing exit

If entry exists but no exit trade exists before day end, the scenario is open through day end and blocks all later candidates that day.

## 10. Non-overlap tests

### P28 — maximum one position

No second position may coexist with an open position.

### P29 — actual exit timestamp controls reopening

A new arm may not be created while the position remains open through the actual exit proxy timestamp, even if intended horizon has elapsed.

### P30 — baseline still updates while open

Valid five-minute ranges must continue to enter the rolling baseline while a position is open.

### P31 — no overnight carry

All state resets at UTC day boundary.

## 11. Scenario-isolation tests

Each scenario must have independent:

- arm state;
- position state;
- skipped/ineligible/unfilled counters;
- actual exit timestamp;
- completed-trade list.

Primary scenario:

- q20 / 250 ms / 600 s.

Mandatory stress:

- q20 / 500 ms / 600 s.

Diagnostics only:

- q15 / 250 ms / 600 s;
- q25 / 250 ms / 600 s;
- q20 / 250 ms / 300 s;
- q20 / 250 ms / 900 s;
- q20 / 1000 ms / 600 s.

No diagnostic may alter primary state or vice versa.

## 12. Aggregation/gate unit tests

Use synthetic completed-trade fixtures.

### P32 — gross edge

Require exactly:

`direction * (exit / entry - 1) * 10,000`.

### P33 — 10% trimmed mean

Require `m=floor(0.10*N)` observations removed from each tail.

### P34 — inactive day handling

A zero-trade required day must count as inactive and non-positive; it must not disappear from active-day or positive-calendar-day breadth counts.

### P35 — positive-day concentration

Require `G_d`, `P_d=max(G_d,0)`, top-1 share and top-3 share exactly as defined by the protocol.

### P36 — completion rate denominator

Require:

`eligible_nonoverlap = breakout_candidates - skipped_while_open - ineligible_day_end`.

Unfilled eligible candidates remain in the denominator.

### P37 — all-gates semantics

Stage PASS requires logical AND of every mandatory gate. No weighted score or discretionary override is allowed.

## 13. Chronology/firewall tests

### P38 — Discovery date whitelist

Discovery mode must refuse any target day outside 2024-03-01..20.

### P39 — Confirmation fail-closed

Confirmation mode must refuse to run unless a terminal Discovery report exists with verdict exactly `E004_DISCOVERY_PASS`, matching protocol identity and implementation identity.

### P40 — Q2/Validation/Final denylist

Any attempt to open April/Q2, formal Validation or Final bodies under E004 v0.1 before authorized promotion must raise a hard failure.

### P41 — no E002/E003 feature imports

Static implementation review must confirm no TFI/FLOW_IMPULSE field is used to select, veto, rank, size, time or reverse E004 trades.

## 14. Causality mutation tests

These tests are mandatory and synthetic.

### P42 — future-price mutation

Changing synthetic trades strictly after a given decision timestamp must not change:

- whether earlier blocks were compressed;
- earlier frozen box levels;
- earlier breakout decision timestamps/directions.

### P43 — current-block leakage mutation

Changing only the current block range must not change the q20 threshold used to judge that same block.

### P44 — post-breakout mutation

Changing trades after the breakout decision but before the entry target may affect only the fill path at/after the entry target; it must not change the already-frozen signal direction or decision timestamp.

## 15. Real-source integrity-only dry run

After all synthetic tests PASS, run an integrity-only pass over the authorized March source files.

Allowed report fields include:

- source manifest identity;
- script SHA256;
- protocol path/version;
- implementation-freeze path/version if present;
- per-archive filename/bytes/SHA256 verification;
- ZIP/header/schema PASS;
- admitted target rows per UTC day;
- first/last admitted timestamp;
- minute coverage;
- number of valid one-second buckets;
- number of valid/invalid five-minute blocks **without evaluating compression status**;
- Q2/Validation/Final access flags all false.

Forbidden in this dry run:

- q20 values;
- compression booleans;
- arms;
- breakouts;
- candidate counts;
- direction counts;
- returns/edges.

## 16. Preflight terminal statuses

Only two terminal statuses are allowed:

- `E004_PREFLIGHT_PASS`;
- `E004_PREFLIGHT_FAIL`.

Any failed synthetic test, source mismatch, chronology issue, unexpected body access or protocol/implementation identity mismatch => `E004_PREFLIGHT_FAIL`.

No alpha stage may run after FAIL until the implementation defect is corrected and a new implementation SHA is committed. Correcting code before first alpha output does **not** change the frozen financial protocol unless the correction reveals a protocol ambiguity that requires a new protocol version.

## 17. Required PASS report fields

A PASS report must record at minimum:

- UTC run timestamp;
- protocol file path;
- protocol Git commit or content SHA where available;
- engine file path;
- engine SHA256;
- preflight runner path;
- preflight runner SHA256;
- Python version;
- host/runtime identifier excluding secrets;
- all P01-P44 statuses;
- source-manifest identity;
- source integrity summary;
- explicit flags:
  - `alpha_calculated = false`;
  - `pnl_calculated = false`;
  - `compression_events_exposed = false`;
  - `breakout_candidates_exposed = false`;
  - `q2_market_data_body_accessed = false`;
  - `validation_or_final_accessed = false`;
- terminal `status = E004_PREFLIGHT_PASS`.

## 18. Authorization after PASS

A valid `E004_PREFLIGHT_PASS` authorizes only:

**DEV-DISCOVERY on 2024-03-01..20 under the exact frozen protocol and exact committed implementation.**

It does not authorize:

- Confirmation before Discovery PASS;
- L2 acquisition;
- Q2;
- formal Validation;
- Final;
- E005/TFI overlay;
- real-money trading.
