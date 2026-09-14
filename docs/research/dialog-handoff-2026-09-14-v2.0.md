# BotMarketplace Research Dialog Handoff — 2026-09-14 v2.0

**Project:** BotMarketplace / BotMarketplace.store  
**Repository:** `AlexeyIvy/-botmarketplace-site`  
**Purpose:** self-contained continuation context for a new dialog, with emphasis on the active SC001 scalping branch, Android/Termux runtime, and the newly purchased Timeweb VPS.  
**Security:** no public IP, password, private key or API credential is intentionally recorded here.

## 1. How to resume correctly

Read in this order:
1. `docs/research/sc001-current-roadmap-and-stop-rules-v1.1.md` — current SC001 execution order and stop rules.
2. `docs/research/sc001-e002-okx-midquote-q1-confirmation-freeze-v0.1.md` — active frozen financial/statistical confirmation protocol.
3. This handoff.
4. `docs/research/dialog-handoff-2026-09-11-v1.0.md` — unchanged principal-project context for R009/R003/R010/Safe-Sleeve.
5. `docs/research/r009-r003-strategy-first-roadmap-v3.0.md` — project-wide strategy-first roadmap.

The next dialog should not redesign any active strategy merely because the compute environment changed.

## 2. Project-wide research posture

BotMarketplace remains **strategy-first, platform-second**. Broad platform feature development is frozen while strategies are falsified, validated, forward-tested and implementation-audited.

Core rules:
- freeze before observing performance;
- prefer falsification over rescue tuning;
- preserve all failed experiments;
- never move inception/holdout boundaries after results;
- do not select assets, venues, rules or capital tiers because the observed P&L looks prettier;
- historical evidence is not prospective evidence;
- demo success is not strategy proof;
- no real-money promotion yet.

SC001 is a parallel independent branch and may not retrospectively alter R009/R003/R010/S002.

## 3. Principal frozen branches — preserve, do not redesign

The detailed state is in `dialog-handoff-2026-09-11-v1.0.md`. Key clocks that must remain intact:

### R009-E002
- BTC state-dependent beta handoff forward.
- fixed inception: 2026-09-10 00:00 UTC.
- no retuning/reset.

### R003-E003 Binance
- funding/basis canonical forward.
- fixed boundary: 2026-09-10 12:00 UTC.
- preserve causality-safe launcher and persistent state.
- prior Binance HTTP 418 is a source/access issue, not permission to reset or change venue inside E003.

### R003-X003 Bybit
- separate parallel venue forward.
- fixed boundary: 2026-09-10 16:00 UTC.
- never merge/select between Binance and Bybit retrospectively.

### R010-E001
- distinct drawdown-armed recovery shadow-forward.
- fixed inception: 2026-09-11 00:00 UTC.
- no threshold/weight/reset redesign.

### Safe-Sleeve S002
- remains a separate architecture/due-diligence task.
- do not use SC001 outcomes to redesign it.

## 4. SC001 research objective

SC001 asks whether a statistically credible, economically meaningful and execution-robust **true/sub-minute BTC scalping edge** exists.

The original hourly E001 mean-reversion experiment failed and remains permanently failed. The current surviving branch is E002, an aggressive trade-flow continuation screen.

## 5. Frozen SC001 split and firewall

Performance split:
- Development: 2023-04-01 through 2024-06-30.
- Formal Validation: 2024-07-01 through 2025-06-30.
- Final: 2025-07-01 through 2026-08-31.

Internal Development split:
- DEV-DISCOVERY: 15 frozen days, 2023-Q2/Q3/Q4.
- DEV-CONFIRMATION: 10 frozen days, 2024-Q1/Q2.

Formal Validation and Final remain unopened.

Qualification-only dates permanently excluded from performance:
- 2023-04-15;
- 2024-01-15;
- 2025-01-15;
- 2026-07-15.

Inference unit is the day/event block, not millions of ticks/trades treated as IID.

## 6. E002 mechanism

Economic hypothesis: short-horizon aggressive taker-flow imbalance contains information about the next few seconds of BTC price response.

Frozen core feature:

`TFI_5s = sum(side_sign * price * size) / sum(price * size)`

For OKX:
- taker buy = +1;
- taker sell = -1.

Frozen grid/lookback/horizon: 5s / 5s / 5s.

Primary latency 100 ms; stress 250 ms; 500 ms diagnostic.

No threshold/live trade rule has yet been promoted. Full-day ex-post deciles are diagnostics only and **cannot** become a live threshold without a new freeze.

## 7. E002 evidence to date

### Binance DEV-DISCOVERY
- 15/15 positive daily Spearman at 100 ms.
- classification: `PROMISING_SCREEN`, not strategy profitability.

### Binance DEV-CONFIRMATION
- 10/10 positive daily Spearman.
- median daily Spearman about 0.0789.
- all frozen confirmation gates passed.
- exact mechanism unchanged.

### OKX transaction-price replication
Five frozen 2024-Q1 days:
- 5/5 positive daily Spearman at 100 ms;
- median daily Spearman about 0.06229;
- median extreme-decile spread about 0.2346 bps;
- 250/500 ms remained positive.

Important caveat: first-trade-after-target labels could arrive materially after nominal latency, so this was not an executable 100 ms price claim.

### OKX L2 midquote pilot — 2024-01-05
- `MIDQUOTE_PILOT_PASS`.
- 100 ms Spearman about 0.0476746.
- 100 ms extreme-decile spread about 0.249486 bps.
- 250 ms Spearman about 0.04284.
- 500 ms Spearman about 0.03416.
- effect decayed monotonically with latency.
- book-state age median 5 ms; p95 ~16 ms; p99 ~32 ms; rare very large maximum retained, not filtered.

Interpretation: the effect survived transition from trade-price labels to causal L2 midpoint, which weakens a pure bid/ask-bounce explanation.

Economic caution remains severe: about 0.2495 bps top-minus-bottom gross midpoint spread is only about 0.125 bps per side under a naive symmetric tail interpretation, before spread/fees/depth/slippage.

## 8. OKX L2 data engineering state

### Q004R
Historical 400-level L2 semantic replay schema qualified across sampled epochs. Supports price-level replay, spread/depth and conservative taker modelling; not maker queue/MBO.

### Q007
Five frozen Q1 L2 archive metadata sizes qualified. Total compressed size ~2.60 GB, so staged batches were required.

### Q008 pilot full-day replay — 2024-01-05
`FULL_DAY_PASS`.
Reference archive SHA256:
`7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`

Replay reference:
- records 7,568,405;
- snapshots 1,441;
- updates 7,566,964;
- first UTC 00:00:00.005;
- last UTC 23:59:59.990;
- 1440/1440 minutes;
- crossed 0;
- empty 0;
- delete-missing-level 0.

### Q009A
Data-only full-day replay PASS:
- 2024-01-14 `FULL_DAY_PASS`;
- 2024-01-31 `FULL_DAY_PASS`.

No alpha inspected.

### Q009B
Frozen protocol/implementation:
- protocol commit `75e5f052014d39601191e1a0f1263d52476d872e`;
- engine commit `14deaea9d5638c32e380065855cabe740b6cc61e`;
- Android launcher commit `b9cae0bf37c645fd452f35d8b0c8db46facf44a5`;
- implementation freeze `b30b777ab18344cdb83e29f52cd2e9124cfa669b`.

Local Termux final report showed:
- overall `PASS`;
- 2024-02-12 `FULL_DAY_PASS` / archive reused on final run;
- 2024-02-13 `FULL_DAY_PASS` / archive resumed on final run.

The final Q009B artifacts had not yet been uploaded to the chat for an independent artifact-level review when this handoff was written. Do not invent missing detailed metrics.

## 9. Active four-day midquote confirmation

Protocol already frozen before remaining Q1 midquote outcomes:
`docs/research/sc001-e002-okx-midquote-q1-confirmation-freeze-v0.1.md`.

Frozen days:
- 2024-01-14 ordinary weekend;
- 2024-01-31 FOMC;
- 2024-02-12 ordinary weekday;
- 2024-02-13 CPI.

Frozen gates:
- 100 ms daily Spearman positive 4/4;
- 100 ms median Spearman > 0;
- 100 ms extreme spread positive 4/4;
- median extreme spread > 0;
- event median Spearman > 0;
- ordinary median Spearman > 0;
- 250 ms >=3/4 positive and positive median;
- 500 ms diagnostic only.

Status vocabulary:
- `MIDQUOTE_CONFIRMATION_PASS`;
- `MIDQUOTE_CONFIRMATION_WEAK`;
- `MIDQUOTE_CONFIRMATION_FAIL`.

Interpretation boundary: this stage checks quote-based measurement robustness; it is **not** a fully fresh temporal OOS alpha test because these calendar days were already opened for transaction-price replication.

### Current implementation
- confirmation engine commit: `38d3ab050ff64555b0149c31c52e1ab1775ae579`;
- Termux launcher commit: `147f97985cfe2721b87e3822b4d2f0137a84482c`;
- implementation freeze commit: `696898a0f13858be16661234f78c548191182847`.

The Termux implementation:
- uses existing local trade/L2 files;
- does not download market data;
- prints replay progress every 1,000,000 L2 records;
- stores per-day computational checkpoints only for resumability;
- must not expose/interprete partial-day alpha before all four days complete.

At the last observed status, the Android `confirm` tmux session was processing the first frozen day 2024-01-14 and had reached at least 3,000,000 replayed L2 records after a restart. Final verdict is **UNKNOWN at handoff time**.

First action in the new dialog: determine whether `confirm` is still running or whether the final report exists. Do not guess the verdict from the terminal history.

## 10. Financial stop rules after confirmation

If midquote primary gates FAIL:
- materially downgrade/stop E002;
- no rescue via CPI/FOMC filters, side selection, different window/horizon, relaxed latency, post-hoc threshold, or maker fill assumptions.

If PASS:
- stop adding descriptive signal diagnostics;
- move to executable taker economics on already-open Q1 only;
- freeze the executable rule before any P&L.

If WEAK:
- follow the frozen status interpretation; do not silently reinterpret as PASS.

## 11. Required executable-economics freeze if E002 survives

Must define before P&L:
- causal threshold available at decision time;
- non-overlapping position logic;
- taker-only primary execution;
- 100/250/500 ms latency scenarios;
- arrival-time causal L2 state;
- observed spread crossing;
- visible-book VWAP consumption;
- depth haircuts 0/25/50%;
- explicit fees separate from book cost;
- historical contract/lot/tick metadata;
- gross edge / spread-depth cost / fee cost / net edge;
- predeclared threshold search budget;
- multiple-testing ledger.

Primary metric: **net edge per trade after all costs**.

2024-Q2 OKX remains protected as the one-shot same-venue temporal holdout for the final frozen executable rule.

## 12. Android compute environment

PyDroid is no longer the preferred long-run environment because Android suspended/terminated long jobs when the app was backgrounded.

Current preferred phone runtime:
- Android 10;
- Termux installed from F-Droid;
- official `packages.termux.dev` repo;
- Python 3.14.6;
- pip 26.2.1;
- tmux 3.7c;
- shared storage enabled;
- Downloads path: `~/storage/downloads`.

Standard long-run pattern:

```bash
termux-wake-lock
tmux new-session -A -s botmarket
python -u script.py
```

Detach: `Ctrl+B`, then `D`.  
Reattach: `tmux attach -t botmarket`.  
Stop: `Ctrl+C`.  
Release wake lock: `termux-wake-unlock`.

The confirmation uses tmux session name `confirm`.

New Android scripts should be checked for Termux/Python 3.14 compatibility first. Install third-party libraries explicitly if ever required. Current critical SC001 engines are mostly standard-library only.

## 13. New VPS — infrastructure state

Provider: Timeweb Cloud.  
Region: Frankfurt, Germany.  
OS: Ubuntu 24.04 LTS (login banner showed Ubuntu 24.04.5 LTS).  
Plan: 4 vCPU / 8 GB RAM / 80 GB NVMe.  
Public IPv4 and IPv6 are provisioned.

**Do not store exact IP, root password, private SSH key or any credential in GitHub or chat summaries intended for sharing.**

SSH root login from the Android SSH client was successfully established. At handoff time:
- server is reachable;
- Ubuntu booted normally;
- filesystem banner showed about 76.45 GB root filesystem and low initial usage;
- no full BotMarketplace software stack has yet been installed/configured;
- no repo clone has yet been confirmed;
- no `botmarket` user has yet been confirmed;
- SSH key hardening has not yet been confirmed;
- VPS parity benchmark has not yet been performed.

## 14. VPS setup sequence for the new dialog

Do not jump directly into new financial tests. First qualify the machine.

### Stage VPS-ENV-001 — audit
Run and record:
- OS release;
- `nproc` / CPU model;
- RAM;
- root disk;
- Python version;
- git/tmux availability.

### Stage VPS-ENV-002 — base install
Update packages and install only needed tools, e.g.:
- Python 3 + venv + pip;
- git;
- tmux;
- curl/wget;
- htop or equivalent diagnostic utility.

### Stage VPS-SEC-001 — non-root access
- create `botmarket` user;
- add sudo only as needed;
- create/use SSH public key from the phone;
- prove key login works before disabling password/root login;
- never paste private key/password into GitHub.

### Stage VPS-REPO-001
Clone `AlexeyIvy/-botmarketplace-site` and verify the expected frozen commits/files.

### Stage VPS-NET-001
Verify outbound access to:
- GitHub/raw GitHub;
- OKX historical static host;
- Binance public-data host.

### Stage VPS-PARITY-001
Before declaring the VPS primary:
- download the exact already-qualified Q008 2024-01-05 L2 archive from the frozen source;
- verify exact SHA256 `7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`;
- run the frozen replay;
- require the known Q008 replay counts/boundaries to match.

This is an infrastructure reproducibility test, not a new alpha test.

Only after parity passes should new heavy SC001 execution-economics/Validation computations move to the VPS.

## 15. Compute optimization policy

The current replay is mostly single-process Python, so 4 vCPU will not automatically accelerate one day 4x.

After parity, the first acceptable optimization is parallelizing **independent frozen days** across processes/cores. Do not expose partial results early and do not change financial rules while changing compute architecture.

Do not simultaneously change:
- environment;
- parser/replay semantics;
- financial rule;
- statistical gate.

Change one layer at a time and prove parity.

## 16. Storage/acquisition discipline on VPS

80 GB NVMe is adequate for current staged research, but not for uncontrolled full-history accumulation.

Continue minimum-necessary acquisition. Existing historical phone cap of <2 GB network bytes per run remains the current frozen acquisition rule until a separate versioned infrastructure amendment changes it. Do not silently relax it just because the VPS is larger.

## 17. Immediate first instruction for the next dialog

1. Open `docs/research/sc001-current-roadmap-and-stop-rules-v1.1.md` and this handoff.
2. Confirm the Android four-day midquote confirmation status without interpreting partial checkpoints.
3. Continue VPS setup from the successful root SSH connection: run environment audit first.
4. Do not move the in-progress confirmation to VPS mid-run merely for speed.
5. After VPS environment/security setup, perform Q008 parity.
6. If final midquote confirmation PASSes, freeze executable taker economics before any P&L.
7. If it FAILs, stop/rescope E002 according to frozen stop rules; no rescue tuning.

## 18. Do not do in the new dialog

Do not:
- reveal/commit VPS credentials;
- change current E002 signal/window/latency because execution is slow;
- interpret checkpoint alpha;
- open Q2 before the executable Q1 rule is frozen;
- open formal Validation/Final early;
- claim profitability from predictive/midquote correlation alone;
- use maker queue assumptions to rescue a failed taker strategy;
- restart broad BotMarketplace platform development inside this SC001 infrastructure task;
- alter R009/R003/R010 forward clocks from SC001 evidence.
