# SC001 Dialog Handoff — 2026-09-16 v4.1

Status: **CURRENT RECONCILED HANDOFF FOR NEW DIALOG**

Repository: `AlexeyIvy/-botmarketplace-site`

Branch: **SCALPING RESEARCH / SC001**

This handoff reconciles the visible chat state with the latest GitHub state.

## 1. Independence / firewall

SC001 remains fully independent from:
- `R009-E002`
- `R003-E003 Binance`
- `R003-X003 Bybit`
- `R010-E001`
- `Safe-Sleeve S002`

Nothing in SC001 may change their frozen rules, decisions or forward clocks.

Q2 / formal Validation / Final remain closed.

## 2. Terminal history

- E001: terminal `FAIL`; no rescue.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`; TFI retained only as future auxiliary knowledge.
- E003: terminal `E003_DISCOVERY_FAIL`; no Confirmation/L2/rescue.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only postmortem complete.
- E005: closed because viable-E004 prerequisite failed.
- E006: terminal `E006_DISCOVERY_FAIL`; event-scarcity + insufficient-economics-headroom.
- E007: terminal `E007_DISCOVERY_FAIL`; moderate gross reversal effect but insufficient/unstable economics and latency robustness.

Do not reopen or rescue-tune E001-E007.

## 3. Active experiment: E008 passive maker

Active family:

**SC001-E008 — conservative passive maker / spread capture on OKX `BTC-USDT-SWAP` with explicit pessimistic queue and stale-book handling.**

Base E008 excludes TFI and all prior SC001 signal families.

## 4. E008 engineering stack already completed

- `E008_DATA_INVENTORY_PASS`.
- Historical queue-feasibility v0.1 remains permanently `E008_QUEUE_MODEL_FEASIBILITY_REVIEW`.
- Feb-13 forensic: `CONCENTRATED_SOURCE_GAPS`.
- `E008_STALE_LATCH_MODEL_PASS`, 4/4 engineering days.
- `E008_QUEUE_SIMULATOR_SYNTHETIC_PASS`, 22/22.
- `E008_QUEUE_SIMULATOR_MECHANICAL_PASS`, 4/4 contaminated engineering days.

Frozen queue/stale semantics:
- initial queue-ahead = full displayed size;
- compatible aggressive trades only advance queue;
- cancellations/size decreases give zero progress;
- size additions are pessimistically added ahead;
- same-ms ambiguity gives zero credit;
- level disappearance/book move alone never implies fill;
- partial fills explicit;
- book age >5s => stale latch;
- latch cancels live orders and blocks queue/fill credit;
- incremental updates do not restore trust;
- only a later full snapshot restores trusted state;
- exact FIFO is never claimed.

## 5. Frozen promotional chronology

Discovery dates:
- 2024-01-06
- 2024-01-13
- 2024-01-19
- 2024-01-24
- 2024-02-06
- 2024-02-11
- 2024-02-21
- 2024-02-23

Confirmation dates, frozen but unopened:
- 2024-01-08
- 2024-01-28
- 2024-02-10
- 2024-02-20

No Confirmation body may be opened before full E008 Discovery PASS.

## 6. Frozen E008 strategy/economics

Canonical protocol:
`docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

Core frozen rules:
- one 1-contract passive quote at best bid and one at best ask while flat;
- inventory bounded to +/-1 contract;
- 250 ms primary placement/cancel latency, 500 ms stress;
- quote TTL 30 s;
- max inventory hold 60 s;
- taker exit only as fail-safe after max hold;
- maker fee 2 bps/fill;
- taker fee 5 bps/fill;
- no VIP/rebate rescue;
- no TFI/prior-signal filters.

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

Any failed gate => terminal `E008_DISCOVERY_FAIL`.

## 7. Promotional Discovery data acquisition state

Visible chat confirmed these exact PASS stages:
- `E008_DISCOVERY_METADATA_PREFLIGHT_PASS`;
- `E008_DISCOVERY_ACQUISITION_PREFLIGHT_PASS`;
- `E008_DISCOVERY_TRADES_ACQUISITION_PASS` — 16 trade archives;
- `E008_DISCOVERY_L2_A_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_B_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_C_ACQUISITION_PASS`;
- `E008_DISCOVERY_L2_D_ACQUISITION_PASS`.

Visible chat stopped immediately after L2-D PASS, before it visibly showed the full 24-file verify command.

## 8. Important reconciliation note

The latest GitHub roadmap is already:

`docs/research/sc001-current-roadmap-and-stop-rules-v3.2.md`

and it records a later project state:
- `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`;
- 24 verified files = 16 trades + 8 L2;
- a frozen semantic-integrity protocol and runner already exist:
  - `docs/research/sc001-e008-discovery-semantic-integrity-protocol-v1.0.md`
  - `docs/research/sc001-e008-discovery-semantic-integrity-implementation-freeze-v1.0.md`
  - `research/sc001/sc001_e008_discovery_semantic_integrity.py`

Therefore the new dialog must **not blindly assume either the visible-chat checkpoint or the later GitHub checkpoint without reconciliation**.

Safe reconciliation procedure on VPS:
1. `git pull --ff-only`;
2. inspect or safely rerun `python3 -u research/sc001/sc001_e008_discovery_staged_acquisition.py verify`;
3. require exact `E008_DISCOVERY_ACQUISITION_VERIFY_PASS` and `verified_files = 24`;
4. only then follow roadmap v3.2.

The verify mode is local/read-only integrity checking and does not calculate maker profitability, so rerunning it is safe if needed.

## 9. Current GitHub-prescribed next stage after reconciliation

After exact acquisition verify PASS, current roadmap v3.2 requires the full 8-day semantic integrity qualification before any maker P&L.

Sequence:
1. `python3 -m py_compile research/sc001/sc001_e008_discovery_semantic_integrity.py`
2. `python3 -u research/sc001/sc001_e008_discovery_semantic_integrity.py preflight`
3. require exact `E008_DISCOVERY_SEMANTIC_PREFLIGHT_PASS`;
4. run inside tmux:
   `python3 -u research/sc001/sc001_e008_discovery_semantic_integrity.py run`
5. require 8/8 `DAY_PASS` and terminal `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`.

This semantic stage must calculate no hypothetical maker orders/fills, spread capture, markout, fees, inventory P&L or profitability.

Even semantic PASS still does **not** authorize maker P&L. After semantic PASS, the maker Discovery engine must be implemented/frozen and pass a separate no-alpha implementation preflight + identity gate before one frozen promotional Discovery run.

## 10. Infrastructure / connection notes

Primary environment:
- VPS Ubuntu 24.04, 4 vCPU, 8 GB RAM, 80 GB NVMe;
- user `botmarket`;
- repo `~/botmarketplace-site`;
- data root `~/sc001_data`;
- Android/Termux control client;
- use tmux for long jobs.

Do not put IPs/passwords/SSH keys in GitHub.

If SSH drops:
- reconnect;
- run `tmux ls`;
- attach the existing session before restarting anything.

A historical tmux session name used during this dialog was `e006meta`; always check `tmux ls` rather than assuming.

## 11. Read-first files in the new dialog

1. `docs/research/dialog-handoff-2026-09-16-v4.1.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v3.2.md`
3. `docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`
4. `docs/research/sc001-e008-discovery-semantic-integrity-protocol-v1.0.md`
5. `docs/research/sc001-e008-discovery-staged-acquisition-protocol-v1.0.md`
6. `docs/research/sc001-e008-discovery-date-freeze-v1.0.md`
7. `docs/research/sc001-e008-stale-latch-data-model-protocol-v0.2.md`
8. `docs/research/sc001-e008-conservative-queue-simulator-mechanics-protocol-v0.1.md`

## 12. Suggested opening message for the new dialog

Continue BotMarketplace, independent branch `SCALPING RESEARCH / SC001`, repo `AlexeyIvy/-botmarketplace-site`.

Read first:
1. `docs/research/dialog-handoff-2026-09-16-v4.1.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v3.2.md`
3. `docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`
4. `docs/research/sc001-e008-discovery-semantic-integrity-protocol-v1.0.md`

Important reconciliation: the visible prior dialog stopped after `E008_DISCOVERY_L2_D_ACQUISITION_PASS`, but current GitHub roadmap v3.2 records `E008_DISCOVERY_ACQUISITION_VERIFY_PASS` and already contains the frozen 8-day semantic-integrity stage. First reconcile on VPS by safely checking/rerunning acquisition `verify`; require exact PASS with 24 verified files. Then follow roadmap v3.2: syntax-check semantic runner, run semantic `preflight`, and only after exact preflight PASS run semantic `run` in tmux. Do not launch maker Discovery or calculate P&L yet. Preserve all frozen date/queue/stale/fee/strategy rules. Confirmation/Q2/Validation/Final remain closed.
