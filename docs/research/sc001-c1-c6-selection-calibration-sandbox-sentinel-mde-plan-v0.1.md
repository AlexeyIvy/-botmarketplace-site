# SC001 — C1-C6 Selection/Calibration Sandbox, Sentinel & MDE Plan v0.1

Date: 2026-09-17  
Status: **FROZEN BEFORE C1-C6 SENTINEL OUTCOMES**  
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.21.md`;
- `docs/research/sc001-strategy-selection-time-horizon-mechanism-and-feature-framework-v0.3.md`;
- `docs/research/sc001-c1-c6-feature-indicator-inventory-v0.1.md`;
- `docs/research/sc001-feature-indicator-research-governance-v0.1.md`;
- `docs/research/sc001-contamination-registry-v0.4.json`.

This stage is **selection/calibration only**. It may inspect candidate-mechanism outcomes on already contaminated periods in order to kill structurally weak ideas cheaply. Nothing measured here is promotional evidence for the resulting implementation.

---

## 1. Purpose

Before selecting the next promotional SC001 experiment, C1-C6 must each pass through the cheapest meaningful falsification test that can answer:

1. is the mechanism causally measurable with available historical data?;
2. does the raw effect have plausible headroom over the structural transaction-cost floor?;
3. is opportunity frequency high enough to support a statistically meaningful future test?;
4. is breadth sufficient to justify a multi-asset claim?;
5. can a fresh Discovery/holdout/Confirmation design later be powered without excessive research cost?

A sentinel PASS means only `ELIGIBLE_FOR_BATCH`. It is not strategy profitability proof and does not authorize live trading, holdout access or Confirmation access.

---

## 2. Frozen Selection/Calibration Sandbox

### 2.1 Primary sandbox

Use only the already contaminated eight Discovery instruments:

- BTC-USDT-SWAP
- ETH-USDT-SWAP
- DOGE-USDT-SWAP
- ORDI-USDT-SWAP
- UNI-USDT-SWAP
- XRP-USDT-SWAP
- OP-USDT-SWAP
- BCH-USDT-SWAP

and only these already outcome-seen performance windows:

- `2024-07-01..2024-07-14` UTC — contaminated by E007R1;
- `2024-09-01..2024-09-14` UTC — contaminated by E009.

Boundary source dates already accessed for causal reconstruction may be used only as necessary:

- `2024-06-30`, `2024-07-15`;
- `2024-08-31`, `2024-09-15`.

### 2.2 C1 legacy basis supplement

For C1 only, the already contaminated original E006 BTC spot/perp period may be used for engineering/calibration context:

- `2024-03-01..2024-03-20` UTC.

Old E006 profitability cannot be used as promotional evidence for E006R1.

### 2.3 Additional source acquisition on contaminated dates

If a sentinel requires a source not yet locally present — for example spot archives corresponding to July/September perpetual data — that source may be acquired **only for the same already contaminated dates** and is permanently labeled `NONPROMOTIONAL_SELECTION_CALIBRATION`.

### 2.4 Protected data remain closed

Do not access for this stage:

- July asset holdout SOL/FIL/LTC/SUI;
- July 16-30 unopened gap;
- August protected period;
- September asset holdout SOL/FIL/LTC/SUI;
- October E009 Confirmation;
- March 22-30 legacy E006 Confirmation.

No clean date may be added to calibration without a new contamination-registry version before body access.

---

## 3. Selection-only structural cost reference

This stage needs a common conservative cost hurdle without pretending that historical exact execution specs/fees have already been reconstructed.

Use the existing SC001 regular-user **selection reference** only:

`5 bps per taker fill`.

This is **not** a promoted historical fee claim. It is a screening assumption used to avoid spending engineering effort on mechanisms whose raw effect is too small even before exact spread/depth/spec reconstruction.

### 3.1 Screening hurdle

For a candidate with `N` expected taker fills per completed cycle:

`fee_reference_floor_bps = 5 * N`

`screening_gross_hurdle_bps = 1.5 * fee_reference_floor_bps`

Therefore:

- two-fill directional T1 candidate: fee reference `10 bps`, screening gross hurdle `15 bps`;
- four-fill paired T3 candidate: fee reference `20 bps`, screening gross hurdle `30 bps`.

Spread, depth, slippage, funding, borrow and execution uncertainty are not fully modeled here. Therefore a sentinel PASS only permits deeper cost/execution work.

---

## 4. Multiple-testing / feature budget before outcomes

No optional auxiliary indicator is included in the first sentinel unless explicitly listed below.

Frozen sentinel variant budget:

- C1: 1 strict legacy-mechanism variant;
- C2: 2 reference representations maximum;
- C3: 2 bar-horizon variants maximum;
- C4: 4 leader/horizon variants maximum;
- C5: 1 forced-flow event variant;
- C6: 1 cross-sectional residual variant.

Total first-pass sentinel strategy variants: **11**.

All 11 count in the research ledger even if some fail before producing a usable effect estimate.

No RSI/MACD/ADX/Stochastic/Bollinger/TFI/volatility/filter bundle may be added after seeing sentinel output. Any auxiliary feature requires a separately frozen incremental-value experiment on non-promotional data and later fresh evidence.

---

# 5. C1 Sentinel — E006R1 multi-asset spot/perp basis convergence

## 5.1 Mechanism frozen for sentinel

Use the old E006 economic mechanism without rescue tuning:

- same-venue spot/perpetual pair;
- 10-second causal paired VWAP observations;
- prior 6-hour ordinary median basis baseline;
- positive rich-perpetual dislocation crossing `+50 bps`;
- intended convergence reference `+10 bps` relative to frozen baseline;
- maximum resolution horizon `30 minutes`.

The sentinel is calibration-only and may use idealized paired prices rather than full promoted L2 execution.

## 5.2 Pair eligibility

A pair is sentinel-evaluable only if both spot and perpetual existed historically, have qualified data on the sandbox dates, and the primary long-spot/short-perp sign does not require spot borrowing.

## 5.3 Quantities to measure

- historically eligible pair count;
- trigger count by pair and calendar day;
- active pair count;
- idealized basis-contraction amount within 30 minutes;
- pair-level mean/median contraction;
- equal-weight pair mean contraction;
- fraction of pairs with positive mean contraction;
- calendar-day breadth.

## 5.4 Sentinel hurdle

Selection gross hurdle: `30 bps`.

`C1_SENTINEL_SURVIVE` requires all:

- at least 4 historically eligible/evaluable pairs;
- at least 4 pairs with >=3 triggers over the combined sandbox;
- pooled triggers >=40;
- equal-weight active-pair mean idealized contraction >=30 bps;
- median active-pair mean contraction >=30 bps;
- at least 3/4 of active pairs have positive mean contraction.

If event count is below 40 but >=10 with at least 3 active pairs, classify `C1_DEFER_SAMPLE_INSUFFICIENT` rather than changing threshold/hold.

Otherwise failure is `C1_REJECT_SENTINEL` for the current research batch.

Passing does not establish executable four-fill profitability.

---

# 6. C2 Sentinel — multi-minute local-reference mean reversion

## 6.1 Core question

Does a genuinely multi-minute deviation from a causal local reference show enough subsequent reversion to justify a new H3/P3 strategy family distinct from E007/E009?

## 6.2 Frozen calibration variants

Use causal 1-minute derived bars from qualified trades.

Two and only two local-reference representations may be compared in the sandbox:

- C2-A: trailing 5-minute VWAP reference;
- C2-B: trailing 5-minute median of completed 1-minute VWAPs.

At each completed minute boundary:

- reference uses only completed prior/current causal minute data available by the boundary;
- no same-bar future data;
- deviation is current completed 1-minute VWAP minus the selected local reference, in bps.

For sentinel opportunities require `|deviation| >= 30 bps`.

Primary evaluation horizon: next `10 minutes`.

Outcome: signed move toward the frozen reference direction, measured without overlapping future information in the signal.

## 6.3 Sentinel hurdle

Selection gross hurdle: `15 bps`.

A C2 variant survives only if all:

- pooled non-overlapping opportunities >=100;
- at least 6/8 assets have >=10 opportunities;
- equal-weight asset mean signed 10-minute reversion >=15 bps;
- median asset mean >=15 bps;
- at least 5/8 assets have positive mean signed reversion;
- at least 18 of the 28 sandbox calendar days contain an opportunity somewhere in the universe.

If neither representation survives: `C2_REJECT_SENTINEL`.

If both survive, choose neither by hidden profitability optimization: retain both in the ledger and select the simpler representation unless a predeclared non-PnL data-quality/causality reason favors one. Any later volatility/trend feature is a separate incremental question.

---

# 7. C3 Sentinel — 5m/10m continuation / volatility expansion

## 7.1 Frozen variants

Two bar horizons only:

- C3-A: 5-minute completed bars;
- C3-B: 10-minute completed bars.

For each variant, at bar close define a directional expansion event only if:

1. close breaks above the highest high or below the lowest low of the prior 6 **completed** bars;
2. current completed-bar true range is >=1.5x the median true range of the prior 12 completed bars.

No information from the next bar is visible at decision time.

Primary outcome horizon:

- 5m signal -> next 10 minutes;
- 10m signal -> next 20 minutes.

Outcome is signed continuation in breakout direction.

## 7.2 Sentinel hurdle

Selection gross hurdle: `15 bps`.

A C3 variant survives only if all:

- pooled non-overlapping events >=60;
- at least 6/8 assets active;
- equal-weight asset mean signed continuation >=15 bps;
- median asset mean >=15 bps;
- at least 5/8 assets positive;
- at least 15 active calendar days across the 28-day sandbox.

No volume, ADX, MACD, flow or time-of-day rescue is allowed after output.

If both 5m and 10m survive, both remain declared variants; final experiment selection occurs at batch stage with full multiplicity recorded.

---

# 8. C4 Sentinel — BTC/ETH -> alt lead/lag

## 8.1 Scientific question

Does an extreme causal BTC or ETH impulse contain economically material information about a subsequent **residual** alt move, rather than merely reflecting simultaneous common crypto beta?

## 8.2 Frozen variant budget

Leaders:

- BTC;
- ETH.

Leader impulse horizons:

- 30 seconds;
- 60 seconds.

Total variants: 4.

For each leader/horizon, compute a causal robust impulse z-score using only the prior 60 minutes of same-horizon leader returns. Extreme event: strict crossing to `|Z| >= 3.0`.

Target assets: the six non-leader assets among DOGE, ORDI, UNI, XRP, OP, BCH, excluding a target if it equals the leader.

Primary target horizon: next `60 seconds`.

For mechanism identification report both raw signed target response and common-factor-adjusted residual response. Causal target beta/common-factor coefficients must be estimated from information available before the event; future factor return may be used only to form the ex-post residual outcome, not the signal.

## 8.3 Sentinel hurdle

Directional two-fill screening hurdle: `15 bps`.

A C4 variant survives only if all:

- leader events occur on >=15 sandbox calendar days;
- at least 5 target assets are evaluable;
- pooled leader-event x target observations >=100;
- equal-weight target mean signed residual 60s response >=15 bps;
- median target mean residual response >=15 bps;
- at least 4 target assets have positive mean residual response.

If raw response is positive but residual response fails, classify `COMMON_BETA_NOT_LEAD_LAG` and reject the lead/lag mechanism rather than promoting a beta-timing story under the same ID.

---

# 9. C5 Sentinel — large aggressive-flow / forced-flow exhaustion

## 9.1 Frozen event definition

Use trade-only data first; no L2 yet.

At exact 30-second boundaries calculate:

- signed aggressive notional over prior 30 seconds;
- robust z-score versus the prior 60 minutes of non-overlapping 30-second signed-notional observations;
- concurrent 30-second price return.

Event requires:

- strict crossing to `|flow_Z| >= 3.0`;
- price return has the same sign as aggressive flow;
- absolute 30-second price move >=10 bps.

The hypothesis is **exhaustion/reversal** after forced directional pressure.

Primary response horizon: next `5 minutes`.

Outcome is signed reversal against the event direction.

## 9.2 Sentinel hurdle

Two-fill screening hurdle: `15 bps`.

`C5_SENTINEL_SURVIVE` requires:

- pooled non-overlapping events >=50;
- at least 5/8 assets have >=5 events;
- equal-weight asset mean 5-minute signed reversal >=15 bps;
- median active-asset mean >=15 bps;
- at least 5/8 assets positive or, if fewer than 8 active, >=70% of active assets positive;
- events span >=15 calendar days.

If event count is 15-49 with >=4 active assets, classify `C5_DEFER_SAMPLE_INSUFFICIENT`; do not lower the z threshold after observing output.

Only a surviving sentinel may justify later L2 depth/depletion/replenishment work.

---

# 10. C6 Sentinel — cross-sectional short-horizon dispersion/reversion

## 10.1 Frozen simple factor model

Use 5-minute completed bars.

At each decision boundary:

- compute each asset's completed 5-minute return;
- compute equal-weight universe mean 5-minute return;
- residual = asset return - equal-weight universe mean;
- rank the eight assets by residual.

To keep the first sentinel simple and execution-identifiable:

- LONG the single most negative residual asset conceptually;
- SHORT the single most positive residual asset conceptually;
- primary hold = 15 minutes;
- evaluate only non-overlapping 15-minute decision slots.

This is a calibration spread-return diagnostic, not promoted execution.

## 10.2 Sentinel hurdle

A long/short pair implies four taker fills per full entry/exit cycle.

Screening gross hurdle: `30 bps`.

`C6_SENTINEL_SURVIVE` requires:

- >=100 non-overlapping evaluable opportunities;
- opportunities on >=20 calendar days;
- 10% trimmed mean long-minus-short 15-minute gross spread >=30 bps;
- median opportunity spread >=20 bps;
- equal-weight calendar-day mean spread >=30 bps;
- positive calendar-day share >=0.60;
- no single asset supplies >35% of absolute gross contribution in either long or short role.

Failure is not rescued by adding factors or selecting historical winner/loser assets.

---

## 11. Prospective MDE / sample-size planning after each sentinel

Sentinel survivors must pass a statistical planning stage before promotional Discovery dates are selected.

### 11.1 Primary inference unit

Because crypto assets share common shocks, the primary planning unit is the **calendar-day block**, using an equal-weight aggregation of eligible instrument/pair outcomes within each day.

Instrument-day results remain secondary breadth diagnostics and are not treated as fully independent observations.

For C6 the natural primary block is the portfolio calendar day.

### 11.2 Economic effect floor

Initial planning effect floor:

- T1 directional candidates C2/C3/C4/C5: `delta_screen = 15 bps`;
- T3 paired candidates C1/C6: `delta_screen = 30 bps`.

Before a promoted execution test these values must be replaced or strengthened by the candidate's exact historical fee/spread/depth/funding/borrow reserve. They may not be weakened because sandbox results look small.

### 11.3 Conservative block volatility estimate

From sandbox active calendar-day block effects calculate:

- ordinary sample standard deviation `sd_block`;
- robust scale `robust_block = 1.4826 * MAD(block_effects)`.

Planning scale:

`sigma_plan = 1.25 * max(sd_block, robust_block)`.

The 25% inflation is a planning reserve for limited calibration sample and nonstationarity. It is not a confidence interval.

If fewer than 10 active calendar-day blocks exist, MDE planning is considered unreliable and the candidate is `DEFER_SAMPLE_INSUFFICIENT` unless a longer **already contaminated** calibration source is prospectively added under a new registry version.

### 11.4 Approximate required block count

For one-sided alpha 0.05 and target power 0.80:

`n_req = ceil(((1.645 + 0.842) * sigma_plan / delta_screen)^2)`.

Use at least:

`n_plan = max(20, n_req)` active calendar-day blocks.

This is a planning approximation. Final inference will use predeclared block/bootstrap or cluster-aware methods appropriate to the experiment rather than relying on IID Gaussian assumptions.

If `n_plan` is operationally excessive relative to available untouched history/data cost, classify the candidate `DEFER_HIGH_SAMPLE_COST` for the current batch rather than lowering the economic effect floor.

### 11.5 Optional stopping prohibition

Once a promotional sample size/block target is frozen:

- do not inspect partial promotional alpha to decide whether to stop early;
- do not extend the sample because the result is just below a gate;
- one-shot Discovery remains binding.

---

## 12. Sentinel disposition vocabulary

Each candidate receives exactly one first-pass disposition:

- `REJECT_STRUCTURAL` — causal/data/cost structure invalid before outcome;
- `REJECT_SENTINEL` — calibration sentinel fails frozen economic/breadth condition;
- `DEFER_SAMPLE_INSUFFICIENT` — mechanism not disproven but sandbox too sparse for a credible selection decision;
- `DEFER_HIGH_SAMPLE_COST` — required future evidence is too expensive for the current research batch;
- `ELIGIBLE_FOR_BATCH` — survives sentinel and prospective MDE/sample planning.

No candidate is called a winner at this stage.

---

## 13. Batch selection rule after all six sentinels

Only after all C1-C6 sentinels have terminal selection-stage dispositions may a research batch be frozen.

Batch selection rules:

1. structural and sentinel survivors only;
2. prefer candidates that are not Pareto-dominated on economic headroom, sample feasibility, causal quality, execution identifiability and engineering/data cost;
3. diversity is a constraint only among structurally credible survivors — never promote a bad candidate just to fill a horizon/mechanism cell;
4. where feasible freeze 2-3 candidates spanning at least two mechanism families and two horizon/risk signatures;
5. the batch order must be frozen **before** the first member's promotional outcome is opened;
6. each member gets a new experiment ID, fresh contamination audit, fresh Discovery, asset holdout where applicable, and untouched chronological Confirmation.

---

## 14. Feature-evidence rule during sentinels

Sentinel results may update the Feature Evidence Registry only with the label:

`SELECTION_CALIBRATION_ONLY`.

They cannot upgrade a feature to promotional/confirmed evidence.

Whole-strategy sentinel failure cannot be translated into a global statement that every feature inside it "does not work".

Any custom indicator derived after seeing sentinel results is a newly designed feature version and needs fresh evidence under the governance framework.

---

## 15. Immediate implementation sequence

1. audit local availability of the July/September eight-asset trade bodies and March E006 pair data;
2. for C1, inventory/acquire missing July/September spot sources only on already contaminated dates;
3. implement shared causal derived-bar/return utilities for calibration only;
4. implement sentinel runners with a run manifest containing the frozen 11-variant budget;
5. synthetic/causality checks before outcome computation;
6. run all C1-C6 sentinels on the frozen sandbox;
7. write one selection-stage report with all dispositions, including failures;
8. calculate MDE/block plans only for sentinel survivors;
9. freeze the small diversified research batch before any new promotional data access.
