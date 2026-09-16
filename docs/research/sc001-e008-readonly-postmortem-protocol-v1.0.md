# SC001-E008 — Read-Only Postmortem Protocol v1.0

Date: 2026-09-16  
Status: **FROZEN READ-ONLY FORENSIC STAGE — E008 REMAINS TERMINAL FAIL**

## 1. Purpose

Explain the terminal `E008_DISCOVERY_FAIL` without changing, rerunning for promotion, or rescue-tuning E008.

This stage may only inspect already-produced E008 artifacts and frozen implementation semantics. It must not alter dates, strategy parameters, fees, queue/stale rules, latency, TTL, max hold, order size, funding windows, promotion gates, or Confirmation state.

## 2. Canonical inputs

- `~/sc001_data/SC001_E008_MAKER_DISCOVERY/sc001_e008_maker_discovery_report.json`
- `~/sc001_data/SC001_E008_DISCOVERY_SEMANTIC_INTEGRITY/sc001_e008_discovery_semantic_integrity_report.json`
- `~/sc001_data/SC001_E008_MAKER_DISCOVERY/sc001_e008_maker_discovery_preflight_report.json`
- frozen runner: `research/sc001/sc001_e008_maker_discovery.py`
- frozen strategy protocol: `docs/research/sc001-e008-passive-maker-executable-protocol-v1.0.md`

Required parent states:
- terminal maker status exact `E008_DISCOVERY_FAIL`;
- semantic status exact `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`;
- maker implementation preflight exact PASS;
- maker identity gate exact PASS.

## 3. Allowed calculations

Read-only decomposition of already-recorded outcomes only:

- per-scenario and per-day cycle counts;
- forced-taker share;
- maker-only vs maker-taker cycle counts;
- gross edge, net edge and realized fee-drag (`gross_edge_bps - net_edge_bps`);
- duration distributions;
- long-first / short-first breadth;
- lifecycle counters already present in the terminal report;
- invalid/unresolved reasons already present in the terminal report;
- semantic snapshot/gap diagnostics already present in the semantic report;
- same-ms zero-credit counts relative to admitted trade rows;
- exact terminal gates already recorded.

No counterfactual rerun is permitted in this stage.

## 4. Data-semantics audit already resolved from official OKX documentation

For future interpretation, the following exchange semantics are consistent with the frozen parser:

- public trade `side` is the **taker side**;
- public trade `sz` for `SWAP` is in **contracts**;
- L2 level second field is aggregate quantity and for derivatives is in **contracts**;
- L2 level third field is aggregate order count;
- `snapshot` is full book state and `update` is incremental book data.

These points do not explain the E008 failure by themselves.

## 5. High-priority model risks to investigate

These are postmortem hypotheses, not permission to reopen E008.

### A. Own-order omission from the historical book

The simulator does not insert the hypothetical resting order into the reconstructed exogenous book. If the historical price level disappears, the frozen engine cancels the hypothetical order unfilled.

But on a real venue our own resting order would itself keep that price level present until it fills or we cancel it. Therefore exogenous level disappearance is not equivalent to disappearance of our own order.

This can be materially pessimistic and can reset queue progress excessively.

### B. Best-price logic is based on the exogenous book only

After our hypothetical order rests, exogenous best bid/ask changes are evaluated without our order included in the venue state. In some paths the historical best can move away while our own order would actually remain the best quote.

This can create excessive cancel/requote behavior and may contribute to forced exits.

### C. Queue lower-bound is intentionally severe

Frozen E008 gives:
- zero progress for cancellations/size decreases;
- all displayed size increases added ahead;
- full displayed size ahead on every replacement;
- same-ms book/trade ambiguity zero credit.

This is a valid pessimistic lower-bound experiment, but it is not an estimate of exact FIFO and can materially suppress passive completion.

Future passive-maker research should predeclare multiple queue-model bounds before promotional outcomes, rather than treating one extreme lower bound as a point estimate.

### D. Forced-taker proxy is not venue-side-specific

The frozen engine uses the first causally observed trade after the forced-exit latency as the taker proxy. A real market sell should execute against bid-side liquidity and a real market buy against ask-side liquidity.

Using the next arbitrary public trade is an execution proxy, not a literal market-order reconstruction. A future experiment should predeclare a side-specific executable-book proxy.

### E. Cross-feed timestamp causality remains approximate

Trade timestamps are trade times; order-book timestamps are book-generation timestamps. Equal-millisecond events are fail-closed in E008, but separate feed timestamps do not provide exact cross-stream sequencing beyond that.

Future work should explicitly test a predeclared cross-feed causality tolerance or use a source with exchange sequence linkage if available.

### F. Compatible trade volume may be too permissive across price levels

The queue model treats a taker print through our price as compatible queue-consuming volume. Using the full quantity of a print at a worse price to consume queue at our resting price is not a level-exact FIFO reconstruction.

This can be optimistic in some paths, offsetting some pessimistic assumptions. Future queue mechanics should distinguish same-price execution volume from price-through evidence.

### G. Snapshot handling may create extra cancellations

The frozen runner cancels live hypothetical quotes on a full snapshot resync. A data-feed snapshot is not itself an exchange cancellation of our order.

If promotional archives contain recurring snapshots beyond the initial snapshot, this may add artificial churn. Postmortem must quantify snapshot counts before assigning importance.

### H. Instrument discreteness must be frozen explicitly in future experiments

Future experiments should freeze historical `lotSz`, `minSz`, `tickSz`, `ctVal`, and contract type before simulation. Do not infer historical values from current exchange metadata.

## 6. Economic decomposition to test first

The observed primary forced-taker share was about 99.51%. With frozen 2 bps maker + 5 bps taker fees, a maker-taker cycle carries roughly 7 bps of fee burden before adverse price movement.

Because observed mean net edge was about -8.53 bps/cycle, the first forensic question is whether the remaining loss beyond fees is also negative gross edge/adverse selection. The read-only runner calculates exact realized `gross - net` fee drag from recorded cycles rather than relying on this approximation.

If mean gross edge is also negative, the failure is not merely a fee-tier artifact.

## 7. Interpretation of earlier PASS stages

Earlier PASS results are not inconsistent with terminal economic FAIL:

- data acquisition PASS proved source availability/identity;
- semantic PASS proved structural/chronological integrity;
- synthetic/mechanical PASS proved that the frozen state machine behaved as specified;
- none of those stages asserted that the trading strategy was profitable.

## 8. Terminal rule

This postmortem cannot change `E008_DISCOVERY_FAIL`.

Its purpose is to decide which mechanism lessons are reusable for a **new independently frozen experiment family**.

Confirmation/Q2/Validation/Final remain closed.