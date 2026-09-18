# SC001 Dialog Handoff — 2026-09-18 v6.0

Date: 2026-09-18
Status: **AUTHORITATIVE HANDOFF FOR NEXT CLEAN DIALOG**
Project: `BotMarketplace`
Branch: `SCALPING RESEARCH / SC001`
Repository: `AlexeyIvy/-botmarketplace-site`

## 1. Read first in the next dialog

Use these as primary current context:

1. `docs/research/dialog-handoff-2026-09-18-v6.0.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v4.71.md`
3. `docs/research/sc001-c11-direction-rule-v2-research-plan-v0.1.md`
4. `docs/research/sc001-c11-c12-three-role-current-state-review-v0.1.md`
5. `docs/research/sc001-strategy-landscape-v0.7.md`
6. `docs/research/sc001-feature-evidence-registry-v0.7.md`
7. `docs/research/sc001-reusable-market-building-blocks-registry-v0.6.md`

Useful supporting context:

- `docs/research/sc001-c7-c10-post-slate-mechanism-building-block-synthesis-v0.2.md`
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`
- `docs/research/sc001-independent-base-opportunity-design-brief-v0.1.md`
- `docs/research/sc001-n1-n3-non-alpha-feasibility-review-v0.1.md`
- `docs/research/sc001-custom-feature-hypothesis-backlog-v0.1.md`

## 2. Global SC001 governance

SC001 is fully independent from protected/frozen non-SC001 work.

Do not change, retune or use SC001 to back-edit:

- R009-E002;
- R003-E003 Binance;
- R003-X003 Bybit;
- R010-E001;
- Safe-Sleeve S002.

Protected holdout/Confirmation data must not be opened unless explicitly authorized by a frozen protocol.

No rescue-tuning of terminal experiments.

Anything used for design/threshold/horizon/feature selection becomes nonpromotional for that implementation.

## 3. Terminal historical SC001 state

C1-C6:

`REJECT_SENTINEL`

C7:

`C7_S0_REJECT_SPREAD_HEADROOM`

C8B:

`C8B_S0_REJECT_HEADROOM`

C9:

`C9_S1_REJECT_SENTINEL`

C10:

`C10_S0_REJECT_HEADROOM`

C12:

`C12_S0_REJECT_PARITY_REVERSION`

No direct rescue of any of these.

## 4. Key reusable lessons from C1-C10

Empirical design prior:

`ordinary liquid-crypto conditional information often appears around ~0.5-4 bps`

unless an independent structural/exogenous mechanism explains larger movement.

Strong reusable blocks include:

- causal local references/residualization;
- strict-coactive 1s cross-venue synchronization with no carry-forward;
- top-5 near-touch depth;
- causal depth normalization;
- quoted spread state;
- cross-sectional residual rank;
- weak flow-exhaustion / anti-chase context;
- weak liquidity-vacuum context.

Architecture lesson:

`informational edge scale / structural fill count / cost reserve`

must be evaluated before expensive backtests.

## 5. C7-C10 completed slate

### C7
Frozen non-BTC maker-entry/taker-exit spread screen.

Result:

`C7_S0_REJECT_SPREAD_HEADROOM`

7/7 data quality, 0/7 eligible.

Quoted spreads were far below 10 bps structural hurdle.

### C8B
Strict-coactive cross-venue relative basis.

Result:

`C8B_S0_REJECT_HEADROOM`

p99 dislocation ~2.45 bps, max ~20.8 bps, no persistent >=30 bps episodes.

Reusable engineering standard:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

### C9
Scheduled funding/mark-index normalization.

Result:

`C9_S1_REJECT_SENTINEL`

Effect essentially zero.

### C10
One-sided near-touch L2 liquidity vacuum.

Result:

`C10_S0_REJECT_HEADROOM`

Observed:

- bid-vacuum events = 6,443;
- ask-vacuum events = 6,331;
- 24 UTC hours;
- p50 abs 5s move ~0.95 bps;
- p90 ~3.58 bps;
- p99 ~8.44 bps;
- max ~39.09 bps;
- signed mean ~+0.58 bps;
- positive signed share ~58.7%.

Useful feature insight retained, standalone economics rejected.

## 6. Independent-base redesign after zero survivors

Post-slate review showed N1/N2/N3 all need an independent base opportunity.

Three base concepts were reviewed:

### B1 — Scheduled Tier-1 US Macro Release Impulse
Selected.

Assigned:

`C11`

### B2 — Same-Venue Triangular Spot Parity
Rejected structurally before backtest.

Reason:

three fills + latency/legging + public-data mismatch.

### B3 — USDC-USDT Stablecoin Parity Dislocation/Reversion
Selected.

Assigned:

`C12`

## 7. C11 current state

Candidate:

`C11 — SCHEDULED_TIER1_US_MACRO_RELEASE_IMPULSE`

Event families:

- U.S. Consumer Price Index;
- U.S. Employment Situation.

Initial market:

`BTC-USDT-SWAP`

No macro-surprise values are used.

### C11-D0

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS`

Representative BLS schedule + BTC historical archive source semantics passed.

### C11-D1

`C11_D1_H1_EVENT_ARCHIVE_METADATA_PASS`

Frozen H1-2025 batch:

12 events, all source/calendar metadata qualified.

### C11-S0

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

Frozen H1-2025 12-event result:

- valid events = 12/12;
- events abs 60s move >=20 bps = 11/12;
- median abs 60s move ~45.2622 bps;
- p75 ~88.1712 bps;
- max ~162.7487 bps;
- failed headroom gates = none.

Structural reference:

- two taker fills;
- 10 bps fee reference;
- 10 bps event spread/slippage/model reserve;
- total = 20 bps.

Meaning:

C11 has strong raw event-move headroom.

It has not yet proven direction, continuation, execution or profitability.

### C11-S1 v0.1

Frozen rule:

`sign(first 1-second post-release impulse) -> same-direction continuation through +60s`

Result:

`C11_S1_DEFER_SAMPLE`

because only 11/12 were actionable under the old nonzero-signal sample gate.

The sole problematic event:

`Employment Situation 2025-05-02`

Read-only diagnostic established:

- pre anchor valid, staleness 122 ms;
- +1s anchor valid, staleness 117 ms;
- +60s anchor valid, staleness 30 ms;
- first post-event trade latency 134 ms;
- `first_impulse_bps = 0.0`.

Therefore:

- data are valid;
- source is valid;
- direction under the frozen rule is genuinely absent;
- S1 is unresolved, not rejected.

Do not calculate an 11-event subset verdict.

## 8. C11 three-role expert review

Binding document:

`docs/research/sc001-c11-c12-three-role-current-state-review-v0.1.md`

New key insights:

### Programmer/trader
Future signal state must distinguish:

- DATA_INVALID;
- NO_TRADE;
- LONG;
- SHORT.

Metrics not computed due DEFER should be null/NOT_COMPUTED, not zero.

Opportunity funnel must be explicit:

`scheduled -> valid -> actionable -> executed`

### Financial
C11 is qualitatively different from C1-C10.

Raw movement relative to 20 bps burden:

- median ~2.26x;
- p75 ~4.41x;
- max ~8.14x.

The core problem is now capture/direction/execution, not existence of movement.

C11 calendar may also become a system-level scheduled macro risk state.

### Math/statistics
12 events are small-N.

Future gates should emphasize:

- counts;
- medians;
- actionable share;
- CPI/Employment breadth.

High quantiles should be diagnostic, not dominant.

Any no-trade filter must retain the full scheduled-event denominator.

## 9. C11 Direction Rule v2 plan

Binding:

`docs/research/sc001-c11-direction-rule-v2-research-plan-v0.1.md`

Current preferred minimal-complexity rule for critical review:

- first causal 1-second impulse >0 -> LONG;
- <0 -> SHORT;
- =0 -> NO_TRADE.

This is preferred because it changes signal semantics without searching a new window.

Do not test 1s/2s/5s/10s grids.

### Required future sequence

1. contamination audit candidate fresh chronology;
2. select chronology by calendar, not outcome;
3. freeze CPI + Employment event list;
4. source/calendar preflight;
5. prospectively split:
   - fresh Selection/Calibration;
   - untouched Confirmation;
6. freeze Stage A residual-headroom gates;
7. freeze Stage B direction/opportunity-retention gates;
8. only then open fresh price outcomes;
9. open Confirmation only if Selection/Calibration survives;
10. build execution/slippage model only after Confirmation survives.

### Stage A
Residual post-decision absolute move:

`abs_residual_move_1s_to_60s_bps`

Question:

Does enough movement remain after +1s decision latency?

### Stage B
Directional continuation on actionable events.

Required reporting:

- total scheduled;
- data-valid;
- actionable;
- NO_TRADE;
- actionable share;
- CPI actionable count;
- Employment actionable count;
- events signed continuation above burden;
- median signed continuation.

### Stage C
Untouched Confirmation.

No rule changes.

### Stage D
Event execution/slippage/fill/PnL only after confirmation.

## 10. Fresh chronology requirement

H1-2025 is contaminated for C11 direction redesign.

Do not reuse it as clean evidence for v2.

The next dialog must first audit candidate later/earlier periods for prior SC001 use.

Important:

Repo search showed prior SC001 microstructure work includes portions of 2025-07 through 2026-08, so H2-2025 must **not** be assumed fresh without a contamination audit.

No fresh chronology has yet been selected.

## 11. C12 current state

Candidate:

`C12 — USDC_USDT_STABLECOIN_PARITY_DISLOCATION_REVERSION`

### C12-D0/D1/D2/D3

All source and body semantics/integrity stages passed.

C12-D2 v0.2:

- 182/182 source archives metadata-qualified;
- combined HEAD size = 60,978,772 bytes.

C12-D3:

- 182/182 bodies integrity-qualified.

### Frozen C12-S0

- direct parity anchor = 1.0000;
- re-arm after abs deviation <=10 bps;
- entry at abs deviation >=30 bps;
- max hold =30m;
- success = return to <=10 bps;
- structural burden =15 bps.

### C12-S0 result

`C12_S0_REJECT_PARITY_REVERSION`

Data:

- 181/181 target days;
- 6/6 months.

Episodes:

- total =3;
- evaluable =3;
- successful =2;
- episode dates =3;
- episode months =1.

Magnitude:

- success share ~66.7%;
- median gross favorable reversion ~25.94 bps;
- p75 ~29.93 bps.

Failed gates:

- episodes >=12;
- dates >=6;
- months =6.

Passed magnitude gates.

Interpretation:

`ECONOMICALLY_LARGE_WHEN_PRESENT_BUT_TOO_RARE_AND_REGIME_CLUSTERED`

C12 is terminal.

Do not lower thresholds, widen band, extend hold, select active month or extend H1 to manufacture frequency.

Reusable state:

`RB019 — DIRECT_STABLECOIN_PARITY_STRESS_STATE`

Preferred future roles:

- risk/collateral warning;
- regime state;
- veto;
- execution context.

## 12. Current registries

Feature Evidence:

`docs/research/sc001-feature-evidence-registry-v0.7.md`

Reusable Blocks:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.6.md`

Strategy Landscape:

`docs/research/sc001-strategy-landscape-v0.7.md`

Current Roadmap:

`docs/research/sc001-current-roadmap-and-stop-rules-v4.71.md`

## 13. VPS/data operational state

Primary repo on VPS:

`~/botmarketplace-site`

Primary data root:

`~/sc001_data`

Historical C11 H1 archives downloaded during S0:

`~/sc001_data/SC001_C11_S0_EVENT_HEADROOM/archives/`

C12 H1 source bodies:

`~/sc001_data/SC001_C12_D3_H1_BODY_INTEGRITY/archives/`

C12-D3 checkpoint/report:

`~/sc001_data/SC001_C12_D3_H1_BODY_INTEGRITY/`

C11-S1 report:

`~/sc001_data/SC001_C11_S1_FIRST_IMPULSE/c11_s1_first_impulse_continuation_report_v0_1.json`

No active VPS run is required at handoff.

## 14. Immediate next step in new dialog

Do **not** start a new price-bearing script.

First:

### A. Audit fresh C11 chronology
Search repo/contamination history to determine which CPI + Employment periods remain clean enough for:

- fresh Selection/Calibration;
- untouched Confirmation.

Do not assume H2-2025 is clean.

### B. Freeze v2 experiment before outcome
Freeze:

- exact fresh event lists;
- 1s impulse with explicit NO_TRADE, if retained after critical review;
- residual-headroom gates;
- actionable-share gate;
- family-breadth gates;
- signed-continuation gates;
- confirmation chronology.

### C. Only then implement/run
No outcome before all above identities are frozen.

## 15. Hard stop rules for next dialog

Do not:

- reinterpret C11-S1 v0.1 as REJECT;
- drop the zero-impulse event from H1;
- calculate 11-event S1 verdict;
- search multiple impulse windows;
- use macro surprise;
- reuse H1-2025 as fresh v2 evidence;
- reopen C12;
- open C13+ while C11 remains structurally alive;
- access protected/promotional confirmation before authorization.

## 16. One-sentence current project state

SC001 has one active structural survivor:

`C11 macro-event impulse`

with decisively large raw move headroom, while the next research task is to design and validate a fresh, causal, opportunity-retention-aware direction rule without rescue tuning.
