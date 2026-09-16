# SC001 Dialog Handoff — 2026-09-16 v4.0

Status: **CURRENT HANDOFF FOR NEW DIALOG**

Repository: `AlexeyIvy/-botmarketplace-site`

Branch scope: **SCALPING RESEARCH / SC001**

SC001 remains fully independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`. Nothing in SC001 may alter their frozen rules, decisions or forward clocks.

## 1. Primary infrastructure

Primary heavy-compute environment:
- Timeweb Cloud VPS;
- Ubuntu 24.04;
- 4 vCPU / 8 GB RAM / 80 GB NVMe;
- user `botmarket`;
- SSH key auth;
- repo on VPS: `~/botmarketplace-site`;
- data root: `~/sc001_data`;
- Android/Termux is the control client;
- long jobs are run inside `tmux`.

Do **not** write IPs, passwords or SSH keys into GitHub.

Connection drops are common. If SSH drops, reconnect and attach the existing tmux session before restarting anything. A historical session name currently used is `e006meta`; always run `tmux ls` first. In a freshly restarted Termux session, local shell variables such as `$VPS` may be unset.

## 2. Terminal experiment history

### E001
- terminal `FAIL`;
- no rescue tuning.

### E002
- predictive microstructure signal confirmed across multiple replications;
- standalone taker economics terminal `TAKER_ECONOMICS_FAIL`;
- preserve TFI only as future auxiliary/filter/ranking/execution-timing/meta-model knowledge;
- do not reopen E002 standalone or Q2.

### E003 — Rare Flow-Impulse Continuation
- terminal `E003_DISCOVERY_FAIL`;
- primary gross continuation mechanism negative;
- no Confirmation, no E003 L2 acquisition, no rescue.

### E004 — Volatility Compression -> Breakout
- terminal `E004_DISCOVERY_FAIL`;
- gross breakout economics effectively around zero to low-single-digit bps across frozen/read-only variants;
- read-only postmortem complete;
- no rescue.

### E005
- remains closed because viable-E004 prerequisite failed.

### E006 — Same-Venue Spot/Perp Basis Convergence
- terminal `E006_DISCOVERY_FAIL`;
- classified `event-scarcity + insufficient-economics-headroom`;
- one completed pair, gross ~27.405 bps, but sample/breadth/economic/latency gates failed;
- no Confirmation, no paired L2, no trigger/baseline/hold/sign rescue.

### E007 — Extreme 60s Displacement -> Partial Mean Reversion
- terminal `E007_DISCOVERY_FAIL`;
- moderate positive gross reversal effect but insufficient/unstable economics and latency robustness;
- visible failed metrics included pooled mean ~18.28 bps, trimmed ~21.49 bps, median daily mean ~2.99 bps, positive-day share ~63.64%, bootstrap LCB ~4.32 bps, latency means ~15.75 bps at 1s and ~11.34 bps at 2s;
- no rescue-tuning, no switch to continuation.

## 3. Strategic pivot: active experiment E008

Active family:

**SC001-E008 — conservative passive maker / spread capture on OKX `BTC-USDT-SWAP` with explicit pessimistic queue and adverse-selection handling.**

This changes the economic mechanism instead of adding another neighboring one-leg taker signal.

Base E008 excludes TFI and all prior SC001 signal families. TFI may only be tested later as a separately frozen incremental feature after an independently viable maker base exists.

## 4. E008 engineering progression already completed

### 4.1 Data inventory
`E008_DATA_INVENTORY_PASS`

All four contaminated engineering days had qualified L2 + trade tapes on VPS:
- 2024-01-14
- 2024-01-31
- 2024-02-12
- 2024-02-13

These four days are permanently **non-promotional engineering days** for E008.

### 4.2 Queue-model feasibility v0.1
Result remains permanently:

`E008_QUEUE_MODEL_FEASIBILITY_REVIEW`

Reason: 2024-02-13 had prior-book age <=5s share ~96.92%, below frozen >=99.5% gate.

Do not relabel this v0.1 result as PASS and do not weaken its threshold.

### 4.3 Feb-13 forensic
`E008_FEB13_STALE_BOOK_FORENSIC_COMPLETE`

Classification:

`CONCENTRATED_SOURCE_GAPS`

Observed facts:
- prior-valid-book trades: 1,117,953;
- age<=5s share ~0.969242;
- stale >5s trade count: 34,386;
- stale episodes: 6;
- top-10 episode trade share: 1.0;
- L2 gaps >5s: 9;
- max L2 gap: 22,170 ms.

### 4.4 Fail-closed stale-latch v0.2
`E008_STALE_LATCH_MODEL_PASS`

Frozen rule for all later E008 work:
- book age >5,000 ms => enter `STALE_LATCH`;
- no quoting/queue progress/fill credit while latched;
- incremental updates do **not** restore trust;
- only a later full snapshot restores trusted book state;
- live synthetic orders are cancelled on latch with no extra fill credit.

Passed on 4/4 engineering days.

### 4.5 Conservative synthetic queue simulator
`E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`

Tests: `22/22`.

Frozen conservative mechanics:
- initial queue-ahead = full displayed size at resting best quote;
- compatible aggressive transaction volume only advances queue;
- cancellation/size decrease gives zero progress;
- displayed-size additions are pessimistically added ahead;
- same-ms ambiguous trades give zero credit;
- level disappearance/book move alone never implies fill;
- partial fills explicit;
- stale latch cancels live order;
- exact FIFO is never claimed because order IDs are unavailable.

### 4.6 Real-data mechanical validation
`E008_QUEUE_SIMULATOR_MECHANICAL_PASS`

Passed 4/4 contaminated engineering days.

This stage used deterministic probe orders only for mechanics validation. Engineering days remain `promotional = False`. No spread capture, markout, fees, inventory P&L or profitability were calculated for promotion.

## 5. Frozen E008 promotional chronology

Discovery date freeze is deterministic and not outcome-selected.

### Discovery dates — frozen/open for data acquisition only
- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

### Confirmation dates — frozen but **still unopened**
- 2024-01-08
- 2024-01-28
- 2024-02-10
- 2024-02-20

Do not open Confirmation market-data bodies unless Discovery fully PASSes.

## 6. Frozen E008 strategy/economics protocol

Canonical protocol:
`docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

Key frozen rules include:
- instrument: OKX `BTC-USDT-SWAP`;
- flat state quotes one 1-contract order at best bid and one at best ask;
- inventory bounded to +/-1 contract;
- primary placement/cancel latency 250 ms; 500 ms stress;
- quote TTL 30 s;
- max inventory hold 60 s;
- forced taker exit only as fail-safe after max hold;
- regular-user maker fee reference 2 bps/fill;
- taker fee reference 5 bps/fill;
- no VIP/rebate rescue;
- no cycle around funding boundaries;
- preserve all conservative queue/stale rules;
- base strategy uses no TFI or prior SC001 feature.

Core Discovery gates include:
- >=100 completed cycles across all 8 days;
- 8/8 active days;
- unresolved inventory = 0;
- forced taker exit share <=10%;
- mean net edge >=1.0 bps/cycle;
- trimmed mean >=0.5 bps;
- median >=0;
- positive days >=6/8;
- median daily mean >0;
- day-block bootstrap 95% LCB >0;
- concentration limits;
- both long-first and short-first breadth;
- 500 ms stress mean >=0 and total net >0;
- 2x initial queue-ahead stress mean >=0 and unresolved inventory=0.

Any failed frozen gate => terminal `E008_DISCOVERY_FAIL` and blocks Confirmation.

## 7. E008 promotional Discovery metadata/acquisition state

### Metadata preflight
`E008_DISCOVERY_METADATA_PREFLIGHT_PASS`

Observed:
- 8/8 Discovery L2 identities available;
- expected L2 total bytes = `3,724,622,435`;
- expected unique trade total bytes = `76,647,648`;
- disk PASS;
- no promotional body downloaded by metadata stage;
- no fills/P&L/profitability calculated.

### Staged acquisition preflight
`E008_DISCOVERY_ACQUISITION_PREFLIGHT_PASS`

Frozen stages/batches:
- trades: 16 unique trade archives, ~76.6 MB;
- L2-A: 2024-01-06 + 2024-01-13, 820,010,542 bytes;
- L2-B: 2024-01-19 + 2024-01-24, 1,104,242,824 bytes;
- L2-C: 2024-02-06 + 2024-02-11, 859,021,338 bytes;
- L2-D: 2024-02-21 + 2024-02-23, 941,347,731 bytes.

### Acquisition stages already completed successfully
- `E008_DISCOVERY_TRADES_ACQUISITION_PASS` — 16/16 trade archives downloaded + verified;
- `E008_DISCOVERY_L2_A_ACQUISITION_PASS` — 2/2 L2 files;
- `E008_DISCOVERY_L2_B_ACQUISITION_PASS` — 2/2 L2 files;
- `E008_DISCOVERY_L2_C_ACQUISITION_PASS` — 2/2 L2 files;
- `E008_DISCOVERY_L2_D_ACQUISITION_PASS` — 2/2 L2 files.

At every acquisition stage:
- fills/spread capture/fees/inventory P&L/profitability remained uncalculated;
- Q2/Validation/Final/Confirmation remained closed.

## 8. Exact current stopping point

**The next command has NOT yet been confirmed as run in this dialog.**

Next action is the full local acquisition verification across all 24 files (16 trades + 8 L2):

```bash
python3 -u research/sc001/sc001_e008_discovery_staged_acquisition.py verify
```

Required exact token:

`E008_DISCOVERY_ACQUISITION_VERIFY_PASS`

Expected summary includes:
- `verified_files = 24`;
- promotional profitability calculated = False;
- Q2/Validation/Final/Confirmation = CLOSED.

Do **not** run maker Discovery immediately after acquisition verify.

After acquisition verify PASS, the next required stage is to freeze and run a **full semantic replay/integrity qualification for all 8 Discovery days**. Only after that qualification PASS may actual promotional E008 maker Discovery be considered.

## 9. Critical stop/firewall rules

Do not:
- alter E001-E007 terminal verdicts;
- use SC001 to alter any independent main-strategy frozen rules/forward clocks;
- relabel E008 queue-feasibility v0.1 REVIEW as PASS;
- weaken queue/stale rules;
- credit cancellation as queue progress;
- assume exact FIFO;
- reduce frozen fees after output or assume VIP/rebates;
- tune order size/TTL/latency/max hold/quote logic from Discovery outcomes;
- add TFI or prior strategy filters to base E008;
- open Confirmation data before Discovery PASS;
- open Q2/formal Validation/Final.

## 10. Files to read first in the next dialog

Use these as primary current context:

1. `docs/research/dialog-handoff-2026-09-16-v4.0.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v3.2.md`
3. `docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`
4. `docs/research/sc001-e008-discovery-date-freeze-v1.0.md`
5. `docs/research/sc001-e008-discovery-staged-acquisition-protocol-v1.0.md`
6. `docs/research/sc001-e008-stale-latch-data-model-protocol-v0.2.md`
7. `docs/research/sc001-e008-conservative-queue-simulator-mechanics-protocol-v0.1.md`
8. `docs/research/sc001-e008-realdata-mechanical-validation-protocol-v0.1.md`

Historical context only as needed:
- `docs/research/dialog-handoff-2026-09-15-v3.0.md`
- E006/E007 result documents;
- E002 reusable lessons.

## 11. Suggested opening message for the next dialog

Continue BotMarketplace, independent branch `SCALPING RESEARCH / SC001`, repo `AlexeyIvy/-botmarketplace-site`.

Read first:
1. `docs/research/dialog-handoff-2026-09-16-v4.0.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v3.2.md`
3. `docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`
4. `docs/research/sc001-e008-discovery-staged-acquisition-protocol-v1.0.md`

Current exact state: E001-E007 are terminal/closed; E008 engineering stack passed stale-latch, synthetic queue simulator and non-promotional real-data mechanical validation. E008 promotional Discovery dates are frozen. Metadata preflight and staged acquisition preflight passed. All 16 trade archives and all 8 L2 Discovery archives were downloaded/verified in their individual stages (Trades + L2 A/B/C/D all PASS). The full 24-file acquisition `verify` command is the immediate next step and has not yet been confirmed run. After that, do not launch maker Discovery; first freeze/run full semantic replay/integrity qualification for all 8 Discovery days. Confirmation/Q2/Validation/Final remain closed. Preserve all frozen queue/stale/fee/date/strategy rules and do not rescue-tune prior failures.
