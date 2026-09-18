# SC001 — C11/C12 Three-Role Current-State Review v0.1

Date: 2026-09-18
Status: **NON-ALPHA EXPERT SYNTHESIS / NO TERMINAL VERDICT CHANGED**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.70.md`;
- `docs/research/sc001-strategy-landscape-v0.7.md`;
- `docs/research/sc001-c11-s0-event-move-headroom-survive-result-v0.1.md`;
- `docs/research/sc001-c11-s1-v0.1-sample-defer-review-v0.1.md`;
- `docs/research/sc001-c11-s1-2025-05-02-zero-first-impulse-diagnostic-v0.1.md`;
- `docs/research/sc001-c12-s0-parity-reversion-result-readonly-postmortem-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.7.md`;
- `docs/research/sc001-reusable-market-building-blocks-registry-v0.6.md`.

## 1. Executive conclusion

No existing verdict should be changed.

The most important current distinction is:

- C11 has demonstrated **broad exogenous raw movement headroom**, but not yet a usable causal direction extractor.
- C12 has demonstrated **rare but economically material parity-stress episodes**, but not enough opportunity breadth for the frozen systematic strategy.

The research frontier is therefore no longer generic signal discovery.

It is now:

`causal extraction + execution economics from a structurally large exogenous event`

with C11 as the primary live mechanism.

## 2. Programmer / trader review

### 2.1 Separate DATA_INVALID from SIGNAL_NO_TRADE

C11-S1 exposed a framework weakness.

The 2025-05-02 event had:

- valid pre anchor;
- valid +1s anchor;
- valid +60s anchor;
- active trading immediately after the release;
- exactly zero first-impulse price change.

That is **not invalid data**.

It is a valid observation where the direction rule has no action.

Future sentinel state machines should distinguish:

1. `DATA_INVALID`;
2. `SIGNAL_NO_TRADE`;
3. `SIGNAL_LONG`;
4. `SIGNAL_SHORT`.

A no-trade event must count in opportunity-retention statistics but must not force sample DEFER.

### 2.2 DEFER reports should use null metrics, not synthetic zeros

When a sample gate prevents a verdict, downstream strategy metrics should be serialized/printed as `null / NOT_COMPUTED`, not zero.

This prevents semantic confusion such as interpreting C11-S1 printed zero continuation counts as market evidence.

### 2.3 C11 should be decomposed into three gates

Instead of jumping from total event move directly to execution:

1. **Residual post-decision headroom**  
   Is there enough absolute move remaining after the frozen decision latency?

2. **Direction quality**  
   Does the direction rule capture that remaining move?

3. **Event execution**  
   Can slippage/spread/fill assumptions preserve the edge?

C11-S0 answered only total event headroom.

Future design should avoid conflating these three problems.

### 2.4 Minimal-complexity Direction Rule v2 is preferable

To minimize hidden rescue, the cleanest v2 design is not a window grid.

Preferred design principle:

- keep one predeclared short impulse window;
- allow explicit `NO_TRADE` if direction is non-actionable;
- freeze an actionable-retention gate;
- do not test multiple impulse windows on the same fresh chronology.

A more complex VWAP/microprice direction rule should be a separate candidate if needed, not an in-place tweak.

### 2.5 Platform-level reusable risk modes

Even if C11 directional alpha ultimately fails, S0 supports a reusable:

`SCHEDULED_MACRO_EVENT_RISK_STATE`

for execution/risk systems.

Similarly C12 supports:

`STABLECOIN_PARITY_STRESS_STATE`.

These can be useful as operational risk states without claiming alpha.

## 3. Financial-expert review

### 3.1 C11 is qualitatively different from C1-C10

C11's edge source is exogenous scheduled information arrival.

This matters because earlier SC001 endogenous mechanisms repeatedly produced ~0.5-4 bps effects.

C11 produced:

- 11/12 events >=20 bps absolute 60s move;
- median ~45.26 bps;
- p75 ~88.17 bps;
- max ~162.75 bps.

Relative to the frozen 20 bps burden reference:

- median raw headroom is ~2.26x;
- p75 is ~4.41x;
- max is ~8.14x.

This is the first SC001 candidate where the raw movement scale is clearly in the same economic order as a two-fill event architecture.

### 3.2 The main C11 risk is capture, not existence of movement

The question is no longer whether the market moves enough.

The question is how much movement remains after a causal decision can be made and whether direction can be inferred without paying away the edge.

This shifts research resources away from feature search and toward:

- decision latency;
- post-decision residual headroom;
- directional efficiency;
- event slippage/adverse selection.

### 3.3 C11 has an additional value as a risk scheduler

Because CPI/Employment timestamps are known ex ante and the frozen batch showed broad large moves, the event calendar can become a system-level risk scheduler.

Possible future operational uses:

- temporary reduction of unrelated passive exposure;
- higher execution reserves;
- no-new-order windows;
- explicit event-risk mode.

These are risk-management hypotheses, not proven profit improvements.

### 3.4 C12 should be reclassified mentally as stress insurance information

C12's economic magnitude was adequate when episodes occurred, but frequency was only:

`3 episodes / 181 days / 1 month`.

Therefore it is poorly suited to ordinary return generation but potentially valuable for:

- collateral-risk monitoring;
- stablecoin regime alerts;
- strategy kill-switch context;
- rare-event research.

Naively annualizing 3/181 into a stable yearly opportunity rate is inappropriate because all events clustered in one month.

### 3.5 C11 and C12 together reveal a broader design law

There are two distinct ways to escape the ordinary 1-4 bps SC001 edge scale:

1. **exogenous event shocks** — C11;
2. **rare structural stress** — C12.

The first has better breadth.
The second has stronger regime concentration.

Future high-headroom candidates should have an explicit economic reason to belong to one of these structural classes rather than relying on ordinary endogenous prediction.

## 4. Mathematics / statistics review

### 4.1 C11 S0 is strong but still small-N

11/12 events exceeding 20 bps is compelling calibration evidence, but 12 events are not enough for precise probability estimates.

The robust conclusion is:

`large event movement is common in this frozen batch`

not:

`the true probability is exactly 91.7%`.

Likewise p75 from only 12 events is unstable and should be more diagnostic than inferential in future confirmation design.

### 4.2 Future C11 gates should emphasize counts + medians

For small event samples, primary gates should favor:

- actionable event count/share;
- number of events clearing structural burden;
- median signed continuation;
- family breadth.

High quantiles may remain diagnostics but should not carry excessive decision weight.

### 4.3 Opportunity retention must be explicit

Once NO_TRADE exists, evaluate both:

- effect among actionable events;
- actionable share among all scheduled events.

A direction rule that looks excellent on 3/12 traded events is not automatically a useful systematic strategy.

Recommended standard outputs:

- total scheduled events;
- data-valid events;
- actionable events;
- no-trade events;
- actionable share;
- CPI actionable count;
- Employment actionable count.

### 4.4 No-trade filtering needs a matched denominator

Any future C11 v2 verdict must preserve the full scheduled-event denominator.

Do not report only traded events.

This prevents apparent edge improvement caused merely by abstaining from most events.

### 4.5 Fresh chronology should be split prospectively

H1-2025 is contaminated for C11 direction-rule design.

A new chronology should be selected by calendar before price outcome and then split into:

- fresh Selection/Calibration;
- untouched Confirmation.

A natural candidate is later calendar periods, subject to contamination audit and source availability.

### 4.6 C12 probability estimates are extremely uncertain

The observed 2/3 reversion success is descriptive only.

With only three episodes, the uncertainty around any success probability is extremely wide.

The statistically robust C12 result is not the 66.7% estimate.

It is the opportunity-breadth failure:

- 3 total episodes;
- 3 dates;
- 1 month.

## 5. Additional practical conclusions

### 5.1 Add a first-class Opportunity Retention layer

Future feature/signal evidence should always report:

`original opportunities -> valid opportunities -> actionable opportunities -> executed opportunities`

This will be especially important for veto, no-trade and execution-mode strategies.

### 5.2 Add Event Risk and Collateral Stress to the reusable state taxonomy

New state families worth preserving:

- scheduled macro-event risk;
- stablecoin cross-parity stress.

Neither must be treated as standalone alpha to create project value.

### 5.3 Research-kernel improvement

Add common enums / schema fields:

- `DATA_INVALID`;
- `NO_TRADE`;
- `LONG`;
- `SHORT`;
- `VERDICT_NOT_COMPUTED`.

This should reduce ambiguity in future automated reports.

## 6. Recommended next C11 design sequence

Before any new outcome:

1. contamination audit of candidate fresh chronology;
2. freeze one Direction Rule v2 with explicit NO_TRADE;
3. freeze opportunity-retention and event-family breadth gates;
4. freeze a residual post-decision headroom metric;
5. run fresh Selection/Calibration;
6. only if it survives, open untouched Confirmation;
7. only after confirmation, build event execution/slippage model.

Do not open C13 while C11 remains structurally alive.

## 7. Verdict of this review

No prior candidate should be revived.

No terminal decision should be changed.

The strongest new practical conclusion is:

`C11 is no longer a generic alpha-search problem; it is a causal capture-and-execution problem around an exogenous event with demonstrated raw economic scale.`

That is a materially better research position than at the start of SC001.
