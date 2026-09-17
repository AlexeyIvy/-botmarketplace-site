# SC001 Dialog Handoff — 2026-09-17 v5.0

Status: **CURRENT COMPREHENSIVE HANDOFF — CONTINUE FROM C1-C6 PREFLIGHT V0.2 MECHANICAL RERUN**

Repository: `AlexeyIvy/-botmarketplace-site`

Branch/context: **SCALPING RESEARCH / SC001**

This handoff preserves the important project, research-governance, strategy-selection, feature/indicator, contamination, sentinel and implementation context from the long 2026-09-15..17 dialog so work can continue in a clean chat without reopening settled decisions.

---

## 1. Independence / firewall

SC001 remains independent from:

- `R009-E002`;
- `R003-E003 Binance`;
- `R003-X003 Bybit`;
- `R010-E001`;
- `Safe-Sleeve S002`.

Nothing in SC001 may retrospectively alter their frozen rules, decisions or forward clocks.

Strategy-first / platform-second remains the project posture. No real-money promotion is authorized.

---

## 2. Runtime / infrastructure context

Primary runtime:

- VPS Ubuntu 24.04;
- 4 vCPU / 8 GB RAM / 80 GB NVMe;
- user: `botmarket`;
- repo: `~/botmarketplace-site`;
- SC001 data root: `~/sc001_data`;
- Android/Termux is the control client;
- long jobs should run in `tmux`;
- NumPy is now installed on the VPS and was successfully imported during E009 gross work.

SSH connection is already configured with the phone key. Do not record IP/password/private key in GitHub handoffs.

If SSH drops, reconnect and inspect `tmux ls` before restarting anything.

---

## 3. Binding terminal experiment history

All prior terminal decisions remain immutable.

### E001
Terminal FAIL. No direct retest.

### E002
Standalone taker economics terminal fail. Important lesson: short-horizon aggressive-flow / TFI contained predictive microstructure information, but the standalone taker implementation did not have sufficient economics. TFI may only be reused prospectively as an auxiliary feature under a new experiment ID and clean evidence.

### E003
Terminal fail. No direct retest.

### E004 / E005
E004 terminal Discovery FAIL; E005 remains closed because its prerequisite failed. No direct rescue retest.

### E006
Original BTC same-venue spot/perpetual basis-convergence study terminally failed its Discovery gates, with event scarcity / economic-headroom limitations. A strict multi-asset replication under a new ID `E006R1` is scientifically justified, but only after a cheap structural/sentinel feasibility screen. It is not automatically the next promotional experiment.

### E007 / E007R1
Original displacement reversal failed. A later strict multi-asset replication `E007R1` was completed and terminal:

`E007R1_GROSS_FEASIBILITY_FAIL`

Important E007R1 gross facts:

- July Discovery assets: BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH;
- pooled completed about 161;
- equal-weight mean about +5.59 bps;
- median instrument mean about +3.60 bps;
- positive instruments 4/8;
- latency 1000/2000 ms remained around +5.32/+5.07 bps;
- concentration passed but economics/breadth/latency gates failed.

No further direct E007/E007R1 retest.

### E008
Passive maker/spread-capture terminal:

`E008_DISCOVERY_FAIL`

Key economics:

- 2058 cycles;
- mean net about -8.53 bps;
- trimmed mean about -8.45 bps;
- median about -8.33 bps;
- positive days 0/8;
- forced-taker share about 99.5%;
- gross was already negative (roughly -1.54 bps), fee drag about 6.99 bps.

Separate lesson: BTC maker economics were poor AND the original queue model was too adversarial to serve as a central FIFO estimator. Improving queue modeling does not rescue the failed BTC economics. A future wider-spread maker family would require a new prospectively selected universe and a new experiment ID.

### E009
Volatility-normalized displacement reversal terminal:

`E009_GROSS_FEASIBILITY_FAIL`

Frozen gross run results:

- active assets 8/8;
- pooled completed = 322;
- equal-weight instrument mean about -0.8931 bps;
- median instrument mean about -0.7971 bps;
- positive instruments = 4/8;
- pooled 10% trimmed mean about +4.8823 bps;
- pooled median about +8.1922 bps;
- 1000 ms equal-weight mean about -0.6272 bps;
- 2000 ms equal-weight mean about -0.3090 bps;
- top instrument absolute contribution share about 0.27162.

Failed frozen gates included equal-weight mean, median-instrument mean, positive breadth, trimmed mean, pooled median and both latency gates.

Exit code 2 was intentional terminal FAIL, not a crash.

E009 read-only postmortem completed exact:

`E009_READONLY_POSTMORTEM_PASS`

Ranking by frozen primary mean:

OP, DOGE, XRP, UNI, BCH, BTC, ETH, ORDI.

- best OP about +4.3799 bps;
- worst ORDI about -6.6336 bps;
- cross-instrument mean SD about 4.0693 bps;
- max event-weight about 0.1739;
- max absolute gross-contribution share about 0.2716;
- adequate sample = true;
- cross-market average headroom insufficient = true;
- breadth insufficient = true;
- pooled robust headroom insufficient = true;
- latency robustness insufficient = true;
- concentration failure = false.

No E009 rescue, holdout, October Confirmation, August repurposing, L2 or net-PnL work.

Relevant records:

- `docs/research/sc001-e009-readonly-postmortem-results-v0.1.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v4.24.md`.

---

## 4. Major research-governance redesign after E009

The long dialog identified a portfolio-level research-concentration problem: SC001 was initially designed around true/sub-minute scalping, so much of E002-E009 clustered around event/5-second/60-second signals and nearby short-horizon mechanisms.

That original focus was not wrong, but continuing to select candidates one-by-one risked over-investing in neighboring strategy families.

Current top-level strategy-selection framework:

`docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`

Important principle:

> under-covered does not mean profitable; it only means information value is high.

The future search is prospectively expanded from sub-minute into short-horizon / micro-intraday positions up to roughly 30 minutes, without pretending that H3/H4 evidence was part of the original SC001 mandate.

No old FAIL is reopened by this expansion.

---

## 5. Time architecture — do not use one vague “timeframe” label

Every future candidate must freeze separately:

1. market-data resolution;
2. signal lookback / aggregation;
3. feature update cadence;
4. decision cadence;
5. entry latency budget;
6. expected holding horizon;
7. hard maximum hold;
8. session/overnight rule where relevant.

Signal clock and execution clock are separate.

For bar-based strategies, a completed bar is unavailable until bar close. Example: a `[12:00,12:05)` bar cannot be used for a decision before `12:05:00`, and execution must occur only after the frozen post-decision latency. Same-bar OHLC look-ahead is prohibited.

Coarse horizon labels are only coverage labels, not a technical specification. Current broad research bands span ultra-fast seconds through approximately 30-minute holds.

---

## 6. Mechanism and execution diversification

Mechanism families:

- M1 — order-flow / microstructure prediction;
- M2 — liquidity provision / spread capture;
- M3 — overshoot / mean reversion / exhaustion;
- M4 — continuation / breakout / short trend;
- M5 — relative value / basis / paired convergence;
- M6 — cross-asset information transfer;
- M7 — forced-flow / event mechanisms.

Execution archetypes:

- T1 — directional taker;
- T2 — passive maker;
- T3 — paired / multi-leg;
- T4 — hybrid.

Risk signature must also be recorded because formally different strategies can carry the same hidden risk. Capture at least:

- directional beta;
- volatility exposure;
- liquidity/adverse-selection exposure;
- inventory duration;
- funding/borrow exposure;
- legging risk;
- stress/liquidation-regime dependence;
- venue/collateral concentration.

Diversity constraints apply only after structural feasibility; do not test a bad strategy merely to fill an empty matrix cell.

---

## 7. Legacy retest policy

Binding document:

`docs/research/sc001-legacy-retest-and-replication-policy-v0.1.md`

Summary:

- E001: no direct retest;
- E002: no standalone retest; auxiliary reuse only under new ID;
- E003: no direct retest;
- E004/E005: no direct retest;
- E006: strict multi-asset `E006R1` replication is justified, subject to cheap feasibility first;
- E007/E007R1: no further direct retest;
- E008: no BTC same-rule retest; a new wider-spread maker universe is allowed only under a new ID;
- E009: no direct retest.

Changing only threshold/lookback/hold/latency after a FAIL is not a valid new experiment.

---

## 8. Feature / indicator research layer

A major addition from this dialog is a formal feature/indicator evidence layer.

Core idea: do **not** build a global indicator leaderboard. Statements such as “RSI works”, “ATR does not work” or “VWAP works” are invalid without scope.

Evidence must be scoped by:

`feature/version × role × market × horizon × mechanism × chronology × execution/cost stage`.

Current feature roles:

- R1 core signal;
- R2 state/regime;
- R3 filter/veto;
- R4 sizing/risk;
- R5 execution;
- R6 reference/normalization.

A feature may fail as a standalone signal but remain useful as a state, reference, risk or execution feature.

Current primitive taxonomy groups indicators by economic primitive instead of popular name, including price/location, trend/persistence, volatility/range, volume/activity, aggressive flow, order-book/liquidity, reference/fair-value transforms, relative-value/derivative state, cross-asset transfer, forced-flow/event state and calendar/session context.

Related indicators are not independent discoveries merely because they have different names.

Binding feature docs:

- `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
- `docs/research/sc001-feature-indicator-taxonomy-v0.1.md`;
- `docs/research/sc001-incremental-feature-testing-protocol-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.1.md`;
- `docs/research/sc001-c1-c6-feature-indicator-inventory-v0.1.md`;
- `docs/research/sc001-candidate-feasibility-card-template-v0.2.md`.

### Incremental testing rule

Where scientifically relevant, pre-register:

`BASE` vs `BASE + FEATURE`.

Prefer the same baseline opportunity set.

For filter/veto features report both:

- per-executed-trade economics;
- economics per original base opportunity;
- opportunity-retention rate;
- turnover/cost change;
- tail-risk change.

If an added feature materially changes the mechanism/opportunity definition, it becomes a new strategy experiment ID rather than a mere feature augmentation.

### Custom indicators

Proprietary/custom features are allowed only if they:

- target a defined economic primitive;
- have an exact causal formula/version;
- have a simpler comparator;
- have a complexity/interaction budget;
- have a falsification rule;
- receive fresh promotional evidence after design.

Do not optimize proprietary formulas directly on promotional PnL.

---

## 9. Current candidate slate C1-C6

C7 wider-spread maker remains reserve/lower priority. The current active non-alpha slate is:

### C1 — E006R1 multi-asset spot/perp basis convergence
M5 / T3. Same-venue spot+perp relative value. Expensive four-fill structure, legging/funding/spec complexity. Scientifically orthogonal and valid legacy replication candidate. Requires cheap event-frequency/headroom sentinel first.

Core features: synchronized spot/perp basis; causal ordinary-basis reference; pair-liquidity/cost eligibility; funding/borrow/contract state as feasibility/accounting, not rescue alpha.

### C2 — multi-minute local-reference mean reversion
M3 / T1. Genuine multi-minute deviation/reversion, not re-labeled E007/E009 60-second displacement.

Core features: causal local reference + multi-minute deviation. Optional volatility scaling or trend veto only as separately pre-registered incremental questions.

### C3 — 5m/10m continuation / volatility expansion
M4 / T1. Under-covered multi-minute continuation region. Not an E004 rescue.

Core features: completed-bar directional persistence/breakout state + movement-scale/expansion state. Optional relative volume or flow confirmation only through an explicit incremental-value question.

### C4 — BTC/ETH -> alt lead/lag
M6 / T1. Tests delayed information transmission rather than same-asset reversal/continuation.

Core features: causal leader impulse + common-market adjustment/residual + timestamp/alignment quality. Common-factor adjustment is mandatory to avoid mistaking simultaneous crypto beta for lead/lag.

### C5 — large-trade / sweep / forced-flow exhaustion
M7+M3 / T1. Objective aggressive-flow event followed by possible exhaustion/reversal.

Trade-only first. L2 depth/depletion/replenishment deferred until a cheap event-frequency/headroom sentinel survives.

### C6 — cross-sectional short-horizon dispersion/reversion
M5/M6, portfolio / multi-leg. Trade relative residual dispersion after removing common-market movement rather than predicting absolute direction.

Core features: common-market factor, residual/dislocation, neutrality/hedge weights and contemporaneous liquidity eligibility.

No historical winner asset selection from E007R1/E009.

---

## 10. Selection / Calibration Sandbox

Current contamination registry:

`docs/research/sc001-contamination-registry-v0.5.json`

Current non-promotional primary sandbox is deliberately restricted to already contaminated evidence:

### July sandbox

- assets: BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH perpetuals;
- performance dates: `2024-07-01..2024-07-14`;
- contaminated by E007R1;
- boundary sources `2024-06-30` and `2024-07-15` may be used only as causal reconstruction support.

### September sandbox

- same eight perpetual assets;
- performance dates: `2024-09-01..2024-09-14`;
- contaminated by E009;
- boundary sources `2024-08-31` and `2024-09-15` may be used only as needed.

### C1-only legacy supplement

- BTC spot/perp `2024-03-01..2024-03-20` performance context;
- March 21 boundary already used;
- legacy E006 contaminated.

Anything inspected for feature choice, parameter choice, sentinel design/outcome, variance estimation or MDE planning is non-promotional for the resulting implementation.

Any additional data downloaded to complete the sandbox on these already contaminated dates inherits `NONPROMOTIONAL_SELECTION_CALIBRATION` status.

---

## 11. Protected periods — keep closed

Do NOT open/use for current selection stage:

- July asset holdout: SOL/FIL/LTC/SUI on `2024-07-01..14`;
- unopened July gap `2024-07-16..30`;
- August protected dates `2024-08-01..30`;
- September asset holdout: SOL/FIL/LTC/SUI on `2024-09-01..14`;
- E009 October Confirmation `2024-10-01..14`;
- legacy E006 Confirmation `2024-03-22..30` as E006-role evidence.

Important clarification from the latest preflight defect: pre-existing BTC perpetual archives dated March 22-30 under `SC001_E003_OKX_MARCH_TRADES` belong to old E003 source inventory. Their mere presence on disk is not evidence that E006 Confirmation was accessed. Current preflight v0.2 may observe those filenames but must not open/hash them. E006 SPOT Confirmation bodies March 22-30 under `SC001_E006_SPOT_FEASIBILITY` would still be a hard protected hit.

---

## 12. Sentinel plan — frozen before outcomes

Binding plan:

`docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`

This is selection/calibration only, not promotional evidence.

### Cost reference

Selection-only regular-user reference:

- 5 bps per taker fill.

Screening gross hurdle = `1.5 × fee-reference floor`.

Thus:

- two-fill directional candidates: 15 bps hurdle;
- four-fill paired candidates: 30 bps hurdle.

These are screening assumptions, not exact historical execution-cost claims.

### Frozen first-pass variant budget

Exactly 11 variants:

- C1: 1;
- C2: 2;
- C3: 2;
- C4: 4;
- C5: 1;
- C6: 1.

All variants count in the research ledger even if they fail before a usable effect estimate.

Research ledger:

`docs/research/sc001-selection-research-ledger-v0.1.json`

No unlogged post-outcome threshold/horizon/indicator additions.

### C1 sentinel

Strict legacy mechanism:

- same-venue spot/perp;
- causal 10-second paired VWAP;
- prior 6-hour ordinary median basis baseline;
- positive rich-perp dislocation crossing +50 bps;
- convergence reference +10 bps relative to frozen trigger baseline;
- max resolution horizon 30 min.

Survival requires, among other frozen gates, enough eligible pairs/triggers and >=30 bps idealized contraction headroom across broad pairs. Passing does not prove four-fill executable profitability.

### C2 sentinel

Two and only two local-reference representations:

- trailing 5-minute VWAP reference;
- trailing 5-minute median of completed 1-minute VWAPs.

Opportunity if absolute deviation >=30 bps. Primary horizon next 10 minutes. Survival requires >=15 bps equal-weight/median cross-asset reversion with frozen activity/breadth gates.

### C3 sentinel

Two completed-bar variants only:

- 5-minute;
- 10-minute.

Directional expansion event requires completed-bar breakout versus previous 6 completed bars and true range >=1.5x median of previous 12 completed bars. Outcome is signed continuation over 10m (for 5m signal) or 20m (for 10m signal). Hurdle >=15 bps plus breadth/activity gates.

### C4 sentinel

Four variants only:

- leader BTC or ETH;
- impulse horizon 30s or 60s.

Extreme event: robust causal leader impulse strict crossing `|Z| >= 3.0`, with prior 60-minute same-horizon history. Target horizon 60s. Must survive common-factor residual adjustment. Raw beta-following without residual effect is classified `COMMON_BETA_NOT_LEAD_LAG`, not promoted.

### C5 sentinel

Trade-only first:

- exact 30-second boundaries;
- signed aggressive notional over previous 30s;
- robust z-score versus prior 60m non-overlapping 30s observations;
- strict crossing `|flow_Z| >= 3.0`;
- same-sign concurrent price move;
- absolute 30s price move >=10 bps;
- outcome = 5-minute signed reversal against event direction.

Survival hurdle >=15 bps plus frozen event count/breadth/day gates.

### C6 sentinel

5-minute completed bars. Residual = asset 5m return minus equal-weight universe 5m mean. Conceptually long most negative residual and short most positive residual, non-overlapping 15m slots. Four-fill screening hurdle = 30 bps. Survival also requires robust spread, day breadth and concentration gates.

Allowed selection dispositions:

- `REJECT_STRUCTURAL`;
- `REJECT_SENTINEL`;
- `DEFER_SAMPLE_INSUFFICIENT`;
- `DEFER_HIGH_SAMPLE_COST`;
- `ELIGIBLE_FOR_BATCH`.

No candidate is called a “winner” at sentinel stage.

---

## 13. MDE / sample planning

For sentinel survivors, primary planning unit is the **calendar-day block**, not event/tick observations and not same-date assets treated as independent.

Current planning rule:

- compute sandbox block SD and robust MAD scale;
- `sigma_plan = 1.25 * max(sd, 1.4826*MAD)`;
- one-sided planning alpha 0.05;
- target power 0.80;
- `n_req = ceil(((1.645 + 0.842) * sigma_plan / delta_screen)^2)`;
- `n_plan = max(20, n_req)` active calendar-day blocks.

Initial `delta_screen`:

- C2/C3/C4/C5: 15 bps;
- C1/C6: 30 bps.

Before any promoted execution study these floors must be replaced or strengthened by exact historical fee/spread/depth/funding/borrow reserve. They may not be weakened because sandbox results look small.

Too-sparse or prohibitively expensive candidates are deferred rather than rescued with weaker economics.

---

## 14. Batch-freeze rule after sentinel stage

Only after all C1-C6 receive a selection-stage disposition may a small promotional research batch be frozen.

Among credible survivors:

- avoid Pareto-dominated candidates;
- prefer 2-3 candidates spanning multiple mechanisms/horizons/risk signatures when feasible;
- freeze batch order before the first promotional outcome;
- then assign new experiment IDs and fresh Discovery / asset holdout / chronological Confirmation roles.

There is intentionally no single subjective 0-100 score.

---

## 15. Current technical checkpoint — preflight v0.1 false-positive

A no-alpha C1-C6 implementation preflight v0.1 was run on the VPS.

It successfully re-verified:

- `JULY_E007R1: verified 128/128 archive identities`;
- `SEPTEMBER_E009: verified 128/128 archive identities`.

Then it returned:

`SC001_C1C6_SELECTION_PREFLIGHT_FAIL`

only because the filesystem scanner treated pre-existing E003 BTC perpetual files `2024-03-22..30` as evidence of E006 Confirmation access.

This was classified as a **mechanical implementation false-positive**, not a research/sentinel FAIL.

No strategy signal, sentinel outcome, return or PnL was calculated.

The correction changed no economics, thresholds, chronology, universe, feature budget or sentinel rule.

Audit history is preserved; do not delete/rewrite the v0.1 failure.

---

## 16. Corrected preflight v0.2 — CURRENT HARD GATE

Current roadmap:

`docs/research/sc001-current-roadmap-and-stop-rules-v4.24.md`

Corrected protocol:

`docs/research/sc001-c1-c6-selection-preflight-protocol-v0.2.md`

Corrected runner:

`research/sc001/sc001_c1c6_selection_preflight_v0_2.py`

Identity freeze:

`docs/research/sc001-c1-c6-selection-preflight-implementation-freeze-v1.1.json`

Frozen identities:

- runner blob SHA: `750bcf75ae500a9b4da7643a4e6889658ad6326c`;
- protocol blob SHA: `4b0102d82d37e138299b140a55cc2c13624499ec`.

Exact required PASS token:

`SC001_C1C6_SELECTION_PREFLIGHT_PASS`

Current hard rule:

**NO C1-C6 SENTINEL OUTCOME BEFORE EXACT V0.2 PREFLIGHT PASS.**

### Corrected semantics

- true protected-body hits remain fail-closed;
- old E003 March 22-30 swap source presence is reported separately, not treated as E006 role access;
- v0.2 must not open/hash March 22-30 E003 swap bodies;
- optional legacy E006 verification is limited to March 1-21;
- C1 July/September multi-asset SPOT absence is an expected inventory gap, not a preflight fail.

---

## 17. Exact immediate command to run in the new dialog

On VPS:

```bash
cd ~/botmarketplace-site || exit 1

git pull --ff-only || exit 1

echo "=== 1/3 C1-C6 PREFLIGHT V0.2 SYNTAX ==="

python3 -m py_compile \
  research/sc001/sc001_c1c6_selection_preflight_v0_2.py || {
    echo "=== STOP: PY_COMPILE FAILED ==="
    exit 1
}

echo "=== 2/3 NUMPY CHECK ==="

python3 - <<'PY' || exit 1
import numpy as np
print("NUMPY_PASS version =", np.__version__)
PY

echo "=== 3/3 START CORRECTED C1-C6 PREFLIGHT V0.2 ==="

SESSION="c1c6preflight2"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "=== $SESSION ALREADY EXISTS — DUPLICATE NOT STARTED ==="
    tmux ls
else
    tmux new-session -d -s "$SESSION" \
"bash -lc 'cd ~/botmarketplace-site && set -o pipefail; \
python3 -u research/sc001/sc001_c1c6_selection_preflight_v0_2.py preflight \
2>&1 | tee ~/c1c6_selection_preflight_v0_2.log; \
rc=\${PIPESTATUS[0]}; \
echo \"=== C1C6_PREFLIGHT_V0_2_EXIT_CODE=\$rc ===\" | tee -a ~/c1c6_selection_preflight_v0_2.log; \
exit \$rc'"

    echo "=== C1-C6 PREFLIGHT V0.2 STARTED ==="
    tmux ls
fi
```

Status:

```bash
if tmux has-session -t c1c6preflight2 2>/dev/null; then
    echo "=== STILL RUNNING ==="
    tail -n 60 ~/c1c6_selection_preflight_v0_2.log
else
    echo "=== FINISHED ==="
    tail -n 180 ~/c1c6_selection_preflight_v0_2.log
fi
```

Expected successful tail contains:

- `SC001_C1C6_SELECTION_PREFLIGHT_PASS`;
- July verified 128;
- September verified 128;
- hard protected market-body hits = 0;
- legacy E003 March 22-30 source presence only = possibly non-zero and acceptable;
- legacy E003 March 22-30 bodies opened/hashed by this preflight = false;
- strategy signal calculated = false;
- sentinel outcome calculated = false;
- PnL calculated = false;
- promotional alpha accessed = false;
- exit code 0.

---

## 18. What to do immediately after exact v0.2 PASS

Do not jump directly to promotional alpha.

Sequence:

1. inspect corrected preflight report;
2. determine C1 July/September multi-asset SPOT gap;
3. if missing, freeze a **contaminated-date-only** SPOT metadata/acquisition protocol before downloading any C1 spot data;
4. implement shared causal trade -> bar/return utilities;
5. validate utilities with synthetic/golden tests and bar-causality checks;
6. implement six separate C1-C6 sentinel runners under the frozen 11-variant budget;
7. freeze runner/config identities before first sentinel outcome;
8. run all six non-promotional sentinels on the contaminated sandbox;
9. assign one terminal selection disposition to every candidate;
10. perform MDE/block planning for survivors;
11. only after all dispositions freeze a small diversified promotional batch;
12. assign new experiment IDs and fresh Discovery/asset-holdout/chronological-Confirmation roles before any clean alpha access.

---

## 19. Read-first list for the next clean dialog

Read in this order:

1. `docs/research/dialog-handoff-2026-09-17-v5.0.md` — this handoff;
2. `docs/research/sc001-current-roadmap-and-stop-rules-v4.24.md`;
3. `docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`;
4. `docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`;
5. `docs/research/sc001-contamination-registry-v0.5.json`;
6. `docs/research/sc001-c1-c6-feature-indicator-inventory-v0.1.md`;
7. `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
8. `docs/research/sc001-feature-evidence-registry-v0.1.md`;
9. `docs/research/sc001-legacy-retest-and-replication-policy-v0.1.md`;
10. `docs/research/sc001-c1-c6-selection-preflight-protocol-v0.2.md`;
11. `docs/research/sc001-c1-c6-selection-preflight-implementation-freeze-v1.1.json`.

Also keep binding:

- `docs/research/sc001-next-generation-multi-asset-research-framework-v0.3.md`;
- `docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`.

---

## 20. Recommended opening message for the new dialog

Continue BotMarketplace, independent branch `SCALPING RESEARCH / SC001`, repo `AlexeyIvy/-botmarketplace-site`.

Read first:
1. `docs/research/dialog-handoff-2026-09-17-v5.0.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v4.24.md`
3. `docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`
4. `docs/research/sc001-c1-c6-selection-calibration-sandbox-sentinel-mde-plan-v0.1.md`

Important current checkpoint: all old E001-E009 decisions remain terminal; E009 is terminal gross FAIL with read-only postmortem complete. We redesigned candidate selection across horizons/mechanisms/execution/risk signatures and added formal Feature/Indicator Evidence governance. C1-C6 non-promotional candidate/sentinel definitions are frozen. The first no-alpha selection preflight v0.1 successfully re-verified July and September 128/128 archives but produced a false-positive only because it mistook pre-existing E003 March 22-30 perpetual source files for E006 Confirmation access. This is documented as a mechanical implementation defect, not a research FAIL. Corrected v0.2 is frozen. Immediate next action is to syntax-check and run `research/sc001/sc001_c1c6_selection_preflight_v0_2.py preflight` on the VPS and require exact `SC001_C1C6_SELECTION_PREFLIGHT_PASS` before any sentinel outcome. Do not open any protected holdout/Confirmation data and do not change the frozen 11-variant sentinel budget.
