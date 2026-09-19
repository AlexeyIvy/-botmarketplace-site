# SC001 Current Roadmap and Stop Rules v5.24

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A P0 ARMED / WAITING FOR SEP25 EVENT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.23.md`

## 1. B13-C protected collection

B13-C remains live and independent.

## 2. B14-A P0 state

Exact current state:

`B14A_P0_COLLECTION_WAITING`

Binding live-state record:

`docs/research/sc001-b14a-p0-prospective-collector-waiting-state-v0.1.md`

## 3. Frozen event clock

Connect:

`2026-09-25T07:28:30Z`

Decision anchor:

`2026-09-25T07:30:00Z`

Capture window:

`2026-09-25T07:29:00Z .. 2026-09-25T08:02:00Z`

Expiry:

`2026-09-25T08:00:00Z`

## 4. Frozen P0 economics

Final structural burden:

`37 bps`

Headroom hurdle:

`50 bps`

## 5. Until Sep25

No B14-A design changes.

Allowed:

- tmux alive check;
- collector log check;
- state-file health check.

Forbidden:

- alternative price/basis analysis;
- event substitution;
- threshold tuning;
- convergence/PnL.

## 6. Next research action

Wait for P0 capture completion.

After completion, freeze and run the already-defined coactive-1s headroom readout.

Do not open convergence unless the later P0 disposition permits it.
