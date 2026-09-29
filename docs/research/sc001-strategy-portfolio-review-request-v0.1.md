# SC001 — Strategy Portfolio Review Request v0.1

Date: 2026-09-29
Status: **READY_FOR_STRATEGY_MANAGER_REVIEW**

Scope:
`SCALPING RESEARCH / SC001 / NEXT PRIMARY RESEARCH FOCUS`

## 1. Why this review is requested

The execution project has accumulated enough evidence to justify a portfolio-level reset before launching another long research branch.

Current lesson from B15-P2:
- the delisting mechanism is semantically real and highly uniform;
- the first registered price/basis P0 was forced to `DEFER_SOURCE_COVERAGE` because exact-minute positive trade activity was sparse;
- this makes delisting better suited as a secondary/event-driven candidate than as the primary engine for a small-capital trading program;
- B15-P2 is being taken to a natural STOP/FREEZE boundary, not expanded indefinitely.

The next primary SC001 branch should therefore prioritize **frequent, repeatable, liquid intraday market states**.

## 2. User-level objective

Starting capital is small (approximately USD 1,000), so research priority should favor mechanisms with:
- many repeat opportunities per week;
- preferably multiple opportunities per day;
- applicability across multiple liquid tokens;
- modest capital occupancy;
- realistic execution for small size;
- enough gross headroom to survive fees, spread and slippage;
- no dependence on rare scheduled administrative events as the main source of opportunity.

The desired logic is:

`FREQUENT MARKET STATE -> CAUSAL MECHANISM -> CHEAP SENTINEL -> EXECUTION FEASIBILITY -> CONFIRMATION`

not:

`RARE EVENT -> LONG RESEARCH CHAIN -> LOW OPPORTUNITY FREQUENCY`

## 3. Binding research principles

Use as binding context:
- `docs/research/sc001-midcourse-research-strategy-audit-and-governance-amendment-v0.2.md`
- `docs/research/sc001-terminal-experiment-reusable-block-extraction-policy-v0.1.md`
- `docs/research/sc001-reusable-market-building-blocks-registry-v0.9.md`
- latest contamination registry;
- latest current roadmap;
- latest research-strategy state;
- all relevant terminal/deferred verdicts for B13/B14/B15.

Do not repeat already rejected architectures by relabeling thresholds, horizons or indicators.

Do not rescue failed evidence on the same outcomes.

Reusable blocks may inspire genuinely new prospectively defined mechanisms, but lineage must be explicit.

## 4. Primary strategic question

Identify the most promising next **intraday / high-frequency-of-opportunity** mechanism families for SC001.

The priority is not necessarily sub-second trading.

Candidate timescales may range from seconds to tens of minutes, or occasionally around one hour, if that timescale is dictated by the mechanism and still produces many opportunities.

## 5. Candidate requirements

Prefer candidates that satisfy most of the following:

1. occur daily or many times per day;
2. appear across a broad liquid crypto universe;
3. have a clear causal/economic payer or microstructure mechanism;
4. can be detected causally from public or already-available data;
5. are not purely correlation-mining;
6. plausibly clear an Edge-to-Fill screen before expensive testing;
7. do not require unrealistic latency for a small independent trader;
8. allow a cheap, fast falsification sentinel;
9. can produce enough independent or block-level observations for useful statistics;
10. have plausible economic relevance for approximately USD 1,000 initial capital;
11. are not structurally dependent on extremely rare events;
12. can later be forward-tested without large infrastructure expansion.

## 6. Explicit deprioritization

As the **main** strategy family, deprioritize:
- rare delistings;
- rare listings;
- one-off exchange outages;
- exceptional liquidations as the sole trigger;
- mechanisms with only a few opportunities per month;
- strategies whose gross movement scale is obviously below fees/spread/slippage;
- architectures requiring institutional colocation or sub-millisecond reaction.

These may remain secondary modules if evidence later supports them.

## 7. Requested Strategy Manager output

Produce a compact but rigorous portfolio review with **3-5 candidate mechanism families**.

For each candidate include:

### A. Mechanism identity
- family name;
- economic payer;
- causal trigger/state;
- why the effect could exist;
- nearest prior SC001 mechanism;
- whether it is genuinely independent or only a variant.

### B. Opportunity economics
- expected qualitative frequency:
  - many/day;
  - daily;
  - several/week;
  - rarer;
- expected capital occupancy;
- likely universe breadth;
- likely liquidity quality;
- small-capital suitability.

### C. Timescale
- mechanism timescale;
- proposed primary horizon;
- latency sensitivity;
- why this horizon follows from the mechanism rather than from a desire for more bps.

### D. Edge-to-Fill preflight
- structural fill count;
- likely taker/maker burden;
- spread/slippage sensitivity;
- minimum gross movement scale needed before deeper testing.

### E. Cheapest falsification test
Define the **smallest mechanism-defining sentinel** that can cheaply reject the idea before building a full backtest.

Prefer tests that:
- use frozen causal rules;
- minimize data collection;
- avoid PnL at the first stage when structural headroom can be screened first;
- produce an unambiguous PASS / REJECT / DEFER state.

### F. Data / implementation burden
- required data source(s);
- whether existing SC001 primitives can be reused;
- whether new collector/infrastructure is actually needed.

### G. Main risks
- contamination risk;
- dependence risk;
- liquidity risk;
- capacity risk;
- regime fragility;
- likely failure modes.

## 8. Portfolio-level requested decision

After evaluating the 3-5 candidates:

1. select **one primary next research candidate**;
2. optionally select **one secondary parallel candidate** only if its first sentinel is extremely cheap;
3. explain why they are preferable to continuing B15-P2 as the main line;
4. explicitly list which tempting alternatives should **not** be researched now;
5. define the next concrete task for the Execution project.

The Execution project should receive a task that is narrow enough to begin immediately:
- exact source scope;
- exact pre-price/pre-outcome freeze;
- cheapest sentinel;
- stop rule;
- expected artifact(s).

## 9. Interaction model

The intended loop is:

`STRATEGY MANAGER -> TASK -> EXECUTION PROJECT -> RESULT -> GITHUB -> STRATEGY MANAGER`

The Strategy Manager should not run research jobs or mutate collectors.

The Execution project should not independently choose the next mechanism family unless the Strategy Manager returns the decision.

## 10. B15-P2 status handling

Treat B15-P2 as:
- useful reusable knowledge;
- secondary event-driven branch;
- not the default primary capital-growth engine.

A final source-only cross-type audit is already scheduled to take B15-P2 to a natural STOP/FREEZE boundary.

Do not wait for that audit to begin the portfolio review; if it later materially changes the strategic picture, revise only the B15-P2 disposition, not the whole candidate search unless justified.

## 11. Desired final artifact

Create a canonical Strategy Manager review in GitHub and make the final section:

`NEXT_EXECUTION_TASK`

with a concrete task for the execution project.

