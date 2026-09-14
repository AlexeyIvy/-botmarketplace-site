# SC001 Current Roadmap and Stop Rules v1.1

Date: 2026-09-14  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Scope: independent SCALPING RESEARCH / SC001 branch only.

## 1. Independence retained

SC001 remains an independent parallel research branch. It must not retrospectively alter R009-E002, R003-E003, R003-X003, R010-E001 or Safe-Sleeve S002, and those branches must not become a performance target for SC001.

The project-wide strategy-first roadmap continues separately. This file is the current branch-local execution order for SC001.

## 2. Chronological research firewall remains unchanged

- Development: 2023-04-01 through 2024-06-30.
- Formal Validation: 2024-07-01 through 2025-06-30.
- Final: 2025-07-01 through 2026-08-31.

Inside Development:

`DEV-DISCOVERY -> candidate freeze -> DEV-CONFIRMATION -> same-venue execution/L2 qualification -> Q2 same-venue executable holdout -> formal Validation -> Final -> paper/demo forward`

Formal Validation and Final remain unopened.

## 3. E002 evidence ledger

### Binance DEV-DISCOVERY
Frozen 5-second signed aggressive trade-flow imbalance (TFI) screen passed 15/15 preselected days. Classification remains `PROMISING_SCREEN`, not profitability proof.

### Binance DEV-CONFIRMATION
Exact frozen mechanism passed 10/10 chronological holdout days at 100 ms. Median daily Spearman about 0.0789. No retuning occurred.

### OKX same-venue transaction-price replication
Same economic mechanism replicated on all five frozen 2024-Q1 OKX days: 5/5 positive daily Spearman at 100 ms, median about 0.0623. This reduced the plausibility of a Binance-only artifact but did not prove executable alpha.

### OKX full-day L2 qualification
Historical 400-level `BTC-USDT-SWAP` L2 supports deterministic price-level replay. Full-day replay has been qualified on the Q1 days used for the midquote layer.

### OKX midquote pilot
Pilot day 2024-01-05 preserved the effect when response changed from transaction price to causal L2 midquote. Primary 100 ms Spearman about 0.0477; extreme-decile spread about 0.2495 bps.

Economic warning remains central: that spread corresponds to only about 0.125 bps per side under a naive symmetric tail interpretation before spread crossing, taker fees, depth/VWAP deterioration, size discreteness and market impact.

### Q009A
2024-01-14 and 2024-01-31 L2 archives: `FULL_DAY_PASS`. No alpha/P&L calculated.

### Q009B
Local Termux report on the Android device showed:
- overall status `PASS`;
- 2024-02-12: `FULL_DAY_PASS`;
- 2024-02-13: `FULL_DAY_PASS`;
- data-only firewall retained.

At the time this roadmap was written, the three Q009B output artifacts had not yet been uploaded into the chat for a separate independent audit and no dedicated GitHub Q009B results document had yet been created. Treat the local PASS as sufficient for the already-frozen confirmation engine to proceed, but preserve this audit note.

## 4. Four-day Q1 midquote confirmation is the active research step

Frozen confirmation dates:
- 2024-01-14 — ordinary weekend;
- 2024-01-31 — FOMC;
- 2024-02-12 — ordinary weekday;
- 2024-02-13 — CPI.

Protocol: `docs/research/sc001-e002-okx-midquote-q1-confirmation-freeze-v0.1.md`.

Important interpretation: this is a **measurement-robustness confirmation**, not a fresh independent temporal OOS test, because the same Q1 dates were already opened for OKX transaction-price replication.

Do not combine its p-values with earlier evidence as though the tests were independent.

Frozen primary gates remain:
- 100 ms positive daily Spearman = 4/4;
- median daily Spearman > 0;
- positive extreme-decile spread = 4/4;
- median extreme spread > 0;
- event-day median Spearman > 0;
- ordinary-day median Spearman > 0;
- 250 ms stress: at least 3/4 positive and positive median.

500 ms remains diagnostic only.

## 5. Current execution state on Android

Preferred Android runtime is now **Termux + Python + tmux + termux-wake-lock**, not PyDroid.

Known local environment:
- Android 10;
- Termux from F-Droid;
- repository: `packages.termux.dev`;
- Python 3.14.6;
- pip 26.2.1;
- tmux 3.7c;
- shared Android storage mounted through `~/storage/`;
- Downloads: `~/storage/downloads`.

Long-run pattern:

```bash
termux-wake-lock
tmux new-session -A -s <session>
python -u script.py
```

Detach: `Ctrl+B`, then `D`.  
Reattach: `tmux attach -t <session>`.  
Stop Python: `Ctrl+C`.  
After work: `termux-wake-unlock`.

The active four-day midquote confirmation was launched in tmux session `confirm` with per-day computational checkpoints and progress every 1,000,000 L2 records. It does not download market data. At the last observed status before this handoff, the process had been restarted after an interruption and was replaying the first frozen confirmation day, 2024-01-14. **Final verdict was not yet known at handoff time.**

Do not infer the final confirmation result from partial checkpoints. The final report is authoritative only after all four days complete.

## 6. Stop rule after the four-day confirmation

No additional signal-family detours are allowed after this confirmation.

If primary midquote gates fail: downgrade/stop E002 under this branch; do not rescue with event exclusions, side selection, horizon/window changes, relaxed latency, new thresholds or maker assumptions.

If primary gates pass: stop descriptive signal expansion and move directly to executable taker economics on already-open Q1.

## 7. Next financial stage if confirmation passes

Before any strategy P&L, freeze a new executable-rule/economics experiment with:
- causal live threshold/rule available at decision time;
- no ex-post full-day decile as a live entry rule;
- non-overlapping position logic and conflict handling;
- taker-only primary execution;
- latency: 100 ms BASE, 250 ms STRESS, 500 ms diagnostic;
- order eligibility at `t + latency`;
- first qualified L2 state at/after arrival for execution;
- observed spread crossing;
- visible-book VWAP depth consumption;
- depth haircuts 0% / 25% / 50%;
- explicit fee ledger separate from book costs;
- period-appropriate contract/lot/tick metadata;
- gross edge, spread/depth cost, fee cost and **net edge per trade after all costs**;
- small predeclared threshold/search budget;
- multiple-testing ledger.

Primary economic metric remains **NET EDGE PER TRADE AFTER ALL COSTS**.

## 8. Q2 holdout remains protected

2024-Q2 OKX remains unopened for E002 execution economics.

Do not open it for more attractive descriptive statistics. Q2 is reserved for one-shot same-venue temporal confirmation only after the Q1 executable rule, fees, sizes, latency and promotion gates are frozen.

If Q1 taker economics fails, Q2 remains unopened and E002 is not rescued there.

## 9. VPS infrastructure migration — approved, but research semantics unchanged

A new Timeweb Cloud VPS has been purchased for heavy SC001 computation.

Configuration:
- region: Frankfurt, Germany;
- OS: Ubuntu 24.04 LTS;
- compute: 4 vCPU at advertised 3.3 GHz class;
- RAM: 8 GB;
- storage: 80 GB NVMe;
- public IPv4 and IPv6 provisioned.

Security rule: **do not commit the public IP, root password, private SSH keys, API keys or any other credentials to GitHub.** Exact address/credentials remain outside the repository.

Initial SSH login as root has been successfully established from the Android SSH client. The server had not yet been fully configured at handoff time.

### VPS migration rule
The VPS is an infrastructure change only. It must not alter frozen financial rules, thresholds, dates, gates or historical interpretation.

Do not move an already-running frozen result midway merely to obtain a prettier outcome. The currently active four-day phone confirmation should be allowed to finish on Android unless a documented technical failure requires restart under its own frozen checkpoint logic.

### Mandatory VPS qualification before primary use
1. Audit OS/CPU/RAM/disk/Python.
2. Update packages and install only required tools (`python3`, `python3-venv`, `pip`, `git`, `tmux`, `curl/wget`, `htop` as useful).
3. Create a non-root `botmarket` user with sudo.
4. Configure SSH public-key auth and only after successful key login disable password/root SSH as appropriate.
5. Clone `AlexeyIvy/-botmarketplace-site`.
6. Confirm outbound access to GitHub, OKX historical static host and Binance public-data host.
7. Reproduce one already-qualified L2 day using frozen code and exact source identity.
8. Require identical SHA256 and replay statistics before declaring the VPS the primary heavy-compute environment.

Suggested parity reference: Q008 / 2024-01-05 OKX L2.
Known reference archive SHA256:
`7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`

Known replay reference:
- records: 7,568,405;
- snapshots: 1,441;
- updates: 7,566,964;
- first UTC: 2024-01-05 00:00:00.005;
- last UTC: 2024-01-05 23:59:59.990;
- 1440/1440 minutes;
- crossed-book states: 0;
- empty-book states: 0;
- delete-missing-level: 0.

Only after parity passes should future heavy L2/execution/Validation work move to the VPS.

## 10. Compute optimization rule

Current replay code is substantially single-process Python. Four vCPU do not automatically make one day four times faster.

Optimization should occur only after parity is established. Safe first optimization is parallel processing of **independent already-frozen days**, with final results withheld until all required blocks complete. Do not combine environment migration, algorithmic optimization and financial-rule changes in one step.

## 11. Storage / acquisition discipline

80 GB NVMe is sufficient for the current staged program but not for indiscriminate full-history retention.

Retain the existing staged-acquisition philosophy. The historical phone safety limit of <2 GB network bytes per run remains in force until explicitly revised by a versioned infrastructure amendment; do not silently relax a frozen acquisition rule merely because the VPS has more storage.

## 12. Immediate next actions

1. In the new dialog, read:
   - `docs/research/dialog-handoff-2026-09-14-v2.0.md`;
   - this roadmap;
   - `docs/research/sc001-e002-okx-midquote-q1-confirmation-freeze-v0.1.md`;
   - `docs/research/dialog-handoff-2026-09-11-v1.0.md` for unchanged principal-project branches.
2. Check the Android `confirm` tmux session / final confirmation report. Do not interpret partial checkpoints.
3. In parallel, configure and qualify the new Timeweb Frankfurt VPS using the parity procedure above.
4. If four-day midquote confirmation PASSes, freeze executable taker economics before any P&L.
5. If it FAILs, stop/rescope E002 according to frozen stop rules rather than rescue-tuning.
