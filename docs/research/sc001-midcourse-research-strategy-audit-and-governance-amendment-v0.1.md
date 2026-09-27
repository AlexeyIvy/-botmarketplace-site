# SC001 — Mid-Course Research-Strategy Audit & Governance Amendment v0.1

Date: 2026-09-27
Status: **BINDING RESEARCH-STRATEGY AMENDMENT BEFORE NEXT OUTCOME-BEARING STAGE**
Scope: `SCALPING RESEARCH / SC001`

## 1. Why this audit exists

The current research program has accumulated enough negative and reusable evidence to justify a process-level review.

Three risks are now made explicit:

1. **Horizon trap** — repeatedly testing horizons so short that even total market movement is usually smaller than the economic hurdle.
2. **Mechanism duplication** — renaming a threshold/horizon/indicator variant and treating it as a new strategy even though the economic payer and causal mechanism are the same.
3. **Feature-rescue overfitting** — adding indicators to a failed strategy after seeing its outcome on the same evidence and then treating the improved historical result as new proof.

A fourth opportunity is also formalized:

4. **Proprietary indicator learning** — use completed strategy research to build reusable, causal market-state measurements without turning the program into unrestricted indicator mining.

This amendment complements, and does not weaken:
- Edge-to-Fill Structural Preflight;
- Pre-Outcome Semantic & Implementation Gate;
- Feature / Indicator Research Governance;
- Incremental Feature Testing Protocol;
- Reusable Market Building Blocks Registry;
- Terminal Experiment Reusable-Block Extraction Policy.

---

## 2. Horizon taxonomy

Every future candidate must carry both a **signal horizon** and a **position horizon** tag.

Use these position-horizon classes:

### H0 — micro
`<15 seconds`

### H1 — ultra-short scalp
`15 seconds to <2 minutes`

### H2 — scalp
`2 minutes to <15 minutes`

### H3 — extended scalp / intraday
`15 minutes to <=120 minutes`

### H4 — structural / adjacent
`>120 minutes`

H4 may be researched inside the broader BotMarketplace research program, but must not be cited as evidence about ordinary scalping economics.

This prevents the word “scalping” from silently forcing every mechanism into a seconds-only architecture, and also prevents multi-day carry research from being confused with scalp validation.

---

## 3. Minimum Viable Horizon (MVH) preflight

Before an outcome-bearing test for a price-based strategy, estimate whether the proposed horizon can physically contain enough movement to clear the frozen economic hurdle.

Define prospectively:

`economic_hurdle_bps = structural_burden_bps + required_reserve_bps`

Then, on explicitly non-promotional calibration data or independent source-only diagnostics, estimate a **market-movement envelope** for the proposed horizon.

At minimum report:
- median absolute move;
- p75 absolute move;
- p90 absolute move;
- preferably p95 for rare-event mechanisms;
- horizon-specific event frequency.

This is a necessary-condition screen, not proof of predictability.

### MVH rule

If even broad market movement at the proposed horizon is materially below the economic hurdle, and there is no independent structural/exogenous mechanism explaining why the candidate conditions on much larger moves:

`REJECT_HORIZON_STRUCTURAL`

Do not spend an outcome test on that horizon.

If the candidate has a real event mechanism capable of amplifying movement — e.g. liquidation burst, forced close, transferability outage, macro release — the short horizon may still proceed, but the candidate card must state why its event should escape the ordinary movement envelope.

### Horizon selection contamination

If calibration data are used to choose the horizon:
- that horizon selection is calibration;
- the selected implementation must use fresh promotional evidence;
- do not scan many horizons on the same outcome set and promote the best.

---

## 4. Horizon-diversification rule

Candidate selection should optimize **mechanism quality**, not maximize the number of microsecond/second experiments.

Before selecting the next outcome-bearing candidate, review the horizon coverage map.

When two mechanisms have comparable economic quality:
- prefer the under-covered H2/H3 region over another H0/H1 candidate;
- prefer a horizon that materially improves edge-to-cost plausibility;
- do not shorten a horizon merely because the branch is named “scalping”.

H0/H1 is reserved primarily for mechanisms with a credible fast structural/exogenous payer or execution advantage.

---

## 5. Mechanism Fingerprint Gate

Every new candidate must receive a **mechanism fingerprint** before any outcome access.

Fingerprint fields:

1. economic payer / source of edge;
2. causal trigger/state;
3. traded economic object(s);
4. monetization path;
5. entry architecture;
6. exit/termination anchor;
7. structural fill count;
8. position horizon class;
9. latency dependency;
10. primary risk/capital constraint.

### Duplicate rule

A proposal is **not a new independent strategy** merely because it changes:
- threshold;
- indicator;
- lookback;
- symbol subset;
- entry delay;
- exit delay;
- holding horizon;
- maker/taker assumption.

If payer + causal trigger + monetization path + exit anchor are substantially the same, classify the proposal as:

`SAME_MECHANISM_VARIANT`

not a new independent mechanism.

A materially different horizon can become a new architecture only when it changes the economics, such as:
- one-settlement transfer vs multi-settlement carry;
- forced contractual settlement vs ordinary mean reversion;
- pre-positioned two-fill inventory vs four-fill paired unwind.

Even then, fresh evidence is required.

---

## 6. Mechanism-distance review before candidate selection

Before adding a candidate to the active queue, compare its fingerprint against all terminal and active families.

Record one of:

- `INDEPENDENT_MECHANISM`;
- `RELATED_BUT_MATERIALLY_DIFFERENT_ARCHITECTURE`;
- `SAME_MECHANISM_VARIANT`;
- `DISGUISED_RESCUE_REJECT`.

Do not allocate a new outcome-bearing experiment to the last two classes.

This is now a mandatory anti-duplication gate.

---

## 7. When indicator augmentation is scientifically justified

A failed strategy must not automatically receive more indicators.

First classify the parent failure:

### A. Structural / economic magnitude failure far below hurdle

Examples:
- effect is only a small fraction of required gross headroom;
- p75/p90 still lies below structural burden.

Disposition:

`DO_NOT_RESCUE_PARENT_WITH_INDICATORS`

Extract useful features/building blocks and reuse them prospectively under another independent base opportunity.

B13-C S0 and B14-B currently fall in this category.

### B. Informationally promising / economically near-feasible

Examples:
- sign/breadth is robust;
- gross effect is in the same order of magnitude as the hurdle;
- cost/execution or opportunity retention may plausibly decide viability.

Then one or a small number of pre-registered incremental tests may be justified:

`BASE`
vs
`BASE + FEATURE_X`

Use fresh evidence after feature-role selection.

### C. No directional/informational support

Do not add indicators merely to search for a historical rescue.

Close the architecture and extract only valid measurement/method blocks.

---

## 8. Indicator augmentation rules

For any augmentation:

1. state why FEATURE_X should interact with the base mechanism;
2. freeze its role R2/R3/R4/R5/R6;
3. prefer one feature at a time;
4. freeze parameter/interaction budget;
5. use identical base opportunities when possible;
6. report:
   - retained opportunity share;
   - gross economics per executed trade;
   - economics per original base opportunity;
   - turnover change;
   - cost impact;
   - tail/risk impact;
7. if FEATURE_X materially changes opportunity identity or economic payer, assign a new strategy experiment rather than calling it an incremental feature test.

No arbitrary RSI/MACD/ATR/etc. shopping after outcome.

---

## 9. Proprietary / custom indicator program

Creating our own indicators is explicitly allowed and useful.

The preferred source of ideas is the growing library of validated market primitives and reusable blocks.

A custom indicator must begin from a measurement problem, not from a PnL optimizer.

Required record:

1. economic primitive(s);
2. causal raw inputs;
3. exact formula/version;
4. simpler comparator;
5. expected role;
6. update clock;
7. missing-data semantics;
8. normalization;
9. parameter budget;
10. falsification rule;
11. fresh evidence plan.

### Examples of legitimate custom-feature directions

These are hypotheses, not promoted signals:

- **Flow-to-Liquidity Pressure**
  `signed aggressive notional / causal opposite-side depth reference`
  from the independent lessons of aggressive-flow and L2 work.

- **Liquidation Exhaustion State**
  a prospectively defined transformation of explicit liquidation-cluster information such as RB021, on fresh post-definition events.

- **Funding Persistence State**
  a causal representation of RB022 used as holding-cost/regime context rather than standalone carry alpha.

- **Transferability / Capital-Segmentation Severity**
  if B15-P1 source collection eventually supports a causal outage-state measurement.

No custom formula may be tuned on the evidence that inspired it and then promoted on that same evidence.

---

## 10. New candidate workflow

The future default order is now:

### Gate 0 — Mechanism fingerprint
Reject duplicate/disguised rescue.

### Gate 1 — Horizon class
Tag H0-H4 and state why the horizon matches the mechanism.

### Gate 2 — Edge-to-Fill
Freeze fills, costs, reserve, opportunity rate.

### Gate 3 — Minimum Viable Horizon
Ask whether enough total movement or structural payout can exist at that horizon.

### Gate 4 — Source / semantic feasibility
Do not backtest before identity/source clocks are trustworthy.

### Gate 5 — Base-mechanism sentinel
Test the minimum sufficient architecture.

### Gate 6 — Failure decomposition
Separate:
- source;
- sample;
- direction;
- magnitude;
- costs;
- execution;
- risk.

### Gate 7 — Reusable-block extraction
Mandatory on every terminal/defer branch.

### Gate 8 — Augmentation eligibility
Only informationally credible and economically plausible parents qualify for BASE vs BASE+FEATURE research.

### Gate 9 — Custom-feature research
Separate, versioned, prospective, small complexity budget.

### Gate 10 — Confirmation / forward
Untouched time evidence only after selection.

---

## 11. Implications for completed SC001 evidence

### B13-C S0

30-second horizon was not invalid merely because it was short:
- liquidation bursts are an explicit forced-flow event capable in principle of creating fast movement.

But the real outcome showed:
- median +1.3682 bps;
- p75 +9.1050 bps;
- gross hurdle 30 bps.

Therefore the specific 30-second standalone architecture is terminal.

RB021 survives as information, not as a parent to rescue on the same evidence.

### B14-B

This was a seven-day hold, so its failure proves that **longer duration alone does not create economic edge**.

Median seven-day funding carry was +1.3863 bps against a 50 bps hurdle.

The decisive object is:

`edge scale relative to burden`

not time held by itself.

RB022 survives as a funding-regime state.

---

## 12. Current strategic conclusion

SC001 is **not** trapped in seconds-only research, but the program should make horizon feasibility more explicit before future microstructure tests.

The largest process improvement is:

`MECHANISM -> COST -> MINIMUM VIABLE HORIZON -> OUTCOME`

instead of:

`SIGNAL IDEA -> ARBITRARY SHORT HORIZON -> BACKTEST`

The second improvement is:

`MECHANISM FINGERPRINT -> NOVELTY GATE`

before creating a new branch.

The third is:

`FAILED STRATEGY -> FAILURE DECOMPOSITION -> REUSABLE BLOCK -> PROSPECTIVE AUGMENTATION ONLY WHEN ELIGIBLE`

This preserves learning while controlling overfitting and duplicate work.

---

## 13. Immediate consequence for B15-P2

The already sealed B15-P2 Bybit delisting **offline source-census self-test remains valid** because it opens no price outcome and only verifies source/event semantics.

However, before any later B15-P2 price/dislocation experiment is designed, B15-P2 must pass:
- Mechanism Fingerprint Gate;
- horizon classification;
- Edge-to-Fill;
- Minimum Viable Horizon / event-scale justification.

Do not infer that a delisting event must be traded in the last seconds simply because the forced-close event has an exact clock.
