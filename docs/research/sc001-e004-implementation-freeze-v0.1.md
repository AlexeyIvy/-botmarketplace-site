# SC001-E004 — Implementation Freeze v0.1

Date: 2026-09-15  
Status: **IMPLEMENTATION FROZEN BEFORE FIRST E004 ALPHA — FULL PREFLIGHT PENDING**

Parent protocol: `docs/research/sc001-e004-volatility-compression-breakout-protocol-v0.1.md`  
Preflight specification: `docs/research/sc001-e004-implementation-preflight-v0.1.md`

This document freezes the executable implementation boundary for SC001-E004 before any E004 compression-event, breakout-candidate, return, gross-edge or P&L output is observed on the real March-2024 data.

A local/static synthetic audit has passed. This is **not** `E004_PREFLIGHT_PASS`. Full preflight remains pending until the qualified VPS verifies the real authorized March source files under the integrity-only firewall.

## 1. Frozen file/commit identities

### Economic/statistical protocol

- file: `docs/research/sc001-e004-volatility-compression-breakout-protocol-v0.1.md`
- commit: `fbdb703ddbd1bc93b93ca3bdba4fd7859b626b41`

### Preflight specification

- file: `docs/research/sc001-e004-implementation-preflight-v0.1.md`
- commit: `14694779a5c78c92b943645c795b61e3c3432b25`

### E004 engine

- file: `research/sc001/sc001_e004_volatility_breakout_screen.py`
- current implementation commit: `6226d35164a832ffb280ea72a78dde6de1af15df`
- SHA256: `c590633effc3df6a4edacf35b9157c36ed3d9b80ee422226764e8d313ea1c623`

### E004 preflight runner

- file: `research/sc001/sc001_e004_preflight.py`
- current implementation commit: `ea0a2f52cef110e6f285b3cf413c327db8c039aa`
- SHA256: `d0754b0888216dc073eeee793ad3242a66d77b8fab21790078ed04881132dc9a`

Any executable change to either Python file before the first alpha output requires a new implementation identity and a repeat of all applicable preflight checks. A financial-rule change requires a new protocol version, not merely an implementation revision.

## 2. Pre-alpha local/static audit state

On the frozen implementation listed above:

- Python syntax/compile check: PASS;
- deterministic synthetic tests P01-P44: `44 / 44 PASS`;
- no real March E004 compression-event count inspected;
- no real March breakout-candidate count inspected;
- no real March E004 return/gross-edge/P&L inspected;
- no E004 Discovery output inspected;
- no E004 Confirmation output inspected.

Therefore current status is:

`SYNTHETIC IMPLEMENTATION AUDIT PASS — FULL E004_PREFLIGHT_PASS PENDING`

This state does **not** authorize DEV-DISCOVERY.

## 3. Source boundary

The engine and preflight runner use the already-qualified March OKX `BTC-USDT-SWAP` trade source from:

`~/sc001_data/SC001_E003_OKX_MARCH_TRADES/archives/`

Authoritative source manifest:

`~/sc001_data/SC001_E003_OKX_MARCH_TRADES/sc001_e003_okx_march_trade_stage_report.json`

Reusing this data source does not reuse the E003 alpha mechanism. E004 uses only the qualified raw trade tape and source-integrity metadata.

The implementation requires:

- source stage PASS;
- exactly the authorized 31 March archive identities;
- matching byte sizes and SHA256 values;
- ZIP CRC PASS;
- exact expected CSV header;
- target-instrument/timestamp/trade-ID integrity;
- 1440/1440 UTC-minute coverage for every E004 target day;
- Q2/Validation/Final access flags false;
- source-stage alpha/P&L flags false.

No April/Q2 body is authorized.

## 4. Day-local state

All E004 signal and position state resets at each UTC day boundary.

No prior-day compression ranges are imported into the 72-valid-block baseline. No position or arm carries overnight.

This is consistent with the frozen protocol and avoids adding an unapproved pre-sample dependency.

## 5. One-second price semantics

One-second buckets are UTC aligned, left-closed/right-open:

`[s, s+1000 ms)`.

For each second containing one or more admitted target trades:

`P_s = sum(price_i * size_i) / sum(size_i)`.

No-trade seconds remain invalid/NaN and are never forward-filled.

The one-second statistic becomes decision-available only at the bucket's right edge.

## 6. Five-minute compression-block semantics

Five-minute blocks are UTC aligned and consist of exactly 300 one-second buckets.

- valid with at least 270 valid one-second VWAPs;
- invalid with 269 or fewer;
- extrema use one-second VWAPs, not raw trade extrema;
- range is exactly `10,000 * ln(H/L)` bps.

The rolling compression baseline contains exactly the previous 72 **valid** five-minute ranges from the same UTC day.

The current block is excluded from its own q-threshold calculation and inserted only after the current compression decision.

Primary q20 nearest-rank index for 72 values is exactly zero-based index 14.

Compression uses strict inequality. Equality is not compressed.

## 7. Arm-window edge semantics

A qualifying compression block freezes its own `H` and `L` and arms the immediately following 300-second interval.

The watch interval is:

`[block_end, block_end + 300 s)`

implemented through the immediately following 300 one-second buckets.

The last eligible one-second bucket is:

`[arm_end - 1 s, arm_end)`.

Because one-second information becomes available at the bucket's right edge, a breakout in that final bucket has:

`decision_ts == arm_end`.

That decision is valid because the underlying confirming price bucket lies inside the frozen half-open arm interval. A one-second bucket beginning at `arm_end` is not part of the arm and cannot trigger the expired box.

The first strict upper/lower break consumes the box. Equality to the boundary does not trigger.

## 8. Position / re-arm boundary

The engine enforces maximum one open position and no arm creation while the position is open.

The rolling compression baseline continues to update from valid closed five-minute blocks during an open position, but a block that closes while the position is open cannot later be retroactively armed.

The actual exit proxy timestamp controls when the position becomes flat.

Frozen re-arm boundary:

**a new compression block may arm only when `arm_ts > actual_exit_ts`.**

If a five-minute block closes at exactly the same timestamp as the actual exit proxy, that block is treated as having closed while the old position was still active and is skipped for arming.

This resolves the exact-timestamp boundary conservatively and matches the protocol phrase "only a subsequently closing five-minute block may create a new arm."

## 9. Execution-proxy semantics

Primary:

- latency: 250 ms;
- horizon: 600 s;
- entry: first admitted trade at/after `decision_ts + 250 ms`;
- exit: first admitted trade at/after `decision_ts + 250 ms + 600 s`.

Same-timestamp trades preserve qualified archive stream order.

If the intended exit target is at/after UTC day end, the candidate is ineligible before fill lookup.

If entry is missing, no position opens.

If entry exists but exit is missing before day end, the scenario is treated as open through day end and all subsequent arms/candidates are blocked.

## 10. Scenario isolation

Every frozen scenario has independent arm/position/non-overlap state.

Primary:

- q20 / 250 ms / 600 s.

Mandatory stress:

- q20 / 500 ms / 600 s.

Diagnostics only:

- q15 / 250 ms / 600 s;
- q25 / 250 ms / 600 s;
- q20 / 250 ms / 300 s;
- q20 / 250 ms / 900 s;
- q20 / 1000 ms / 600 s.

No diagnostic scenario may mutate primary state or replace a failed primary/stress result.

## 11. Partial-result firewall

The engine processes independent UTC days in up to four OS processes on the qualified VPS.

Per-day stdout contains completion/progress only. It deliberately does not print per-day alpha metrics during the run.

The stage verdict is produced only after the required stage has been fully aggregated.

No partial-day or early-day result may be used to alter parameters or stop the run selectively.

## 12. Software-enforced preflight gate

The E004 engine now refuses to start **either** Discovery or Confirmation unless the following file exists:

`~/sc001_data/SC001_E004_VOLATILITY_BREAKOUT/preflight/sc001_e004_preflight_report.json`

and proves all of the following:

- stage identity `SC001-E004-PREFLIGHT`;
- version `0.1`;
- status exactly `E004_PREFLIGHT_PASS`;
- preflight engine SHA256 exactly equals the running engine SHA256;
- protocol identity matches the frozen E004 v0.1 protocol;
- real-source integrity run is true;
- archive count = 31;
- target integrity-day count = 30;
- all target days have 1440-minute coverage;
- alpha/P&L/compression-event/breakout-candidate exposure flags are false;
- Q2 and Validation/Final access flags are false.

Thus the sequence `freeze -> preflight PASS -> Discovery` is enforced in code, not merely documented.

## 13. Confirmation fail-closed gate

Even after a valid preflight PASS, Confirmation remains inaccessible unless the exact current engine has already produced a terminal Discovery report with:

- stage/version identity match;
- mode `discovery`;
- verdict exactly `E004_DISCOVERY_PASS`;
- matching engine SHA256;
- matching frozen protocol identity;
- Q2/Validation/Final firewalls intact.

A Discovery FAIL therefore leaves Confirmation closed by code.

## 14. Feature firewall

The frozen E004 base implementation does not use:

- E002 TFI;
- E003 FLOW_IMPULSE;
- side/event/time-of-day filters;
- post-hoc day exclusions;
- maker assumptions;
- lower/VIP fees;
- Q2/Validation/Final data.

The preflight static test also scans executable identifiers for TFI/FLOW_IMPULSE feature imports/usages.

## 15. Full preflight still required on qualified VPS

The next authorized operation is **not DEV-DISCOVERY**.

The next authorized operation is the full E004 preflight on the qualified Timeweb VPS, using the frozen committed files and the already-qualified March trade archives.

The full preflight must:

1. run P01-P44 and require 44/44 PASS;
2. verify all authorized March archive identities/CRC/schema;
3. perform integrity-only UTC reconstruction for 2024-03-01..30;
4. expose no compression/breakout/return/edge output;
5. write a terminal `E004_PREFLIGHT_PASS` report tied to the exact engine SHA above.

Only after that report is independently checked may DEV-DISCOVERY be run.

## 16. Current terminal interpretation

At the time of this implementation freeze:

- E004 economic/statistical protocol: **FROZEN**;
- E004 engine: **FROZEN**;
- E004 preflight runner: **FROZEN**;
- local compile/static/synthetic audit: **PASS (44/44)**;
- full real-source preflight on qualified VPS: **PENDING**;
- E004 DEV-DISCOVERY alpha: **NOT RUN / CLOSED**;
- E004 DEV-CONFIRMATION: **CLOSED**;
- E004 L2: **CLOSED**;
- Q2 / Validation / Final: **CLOSED**.
