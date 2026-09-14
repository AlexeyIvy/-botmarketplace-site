# SC001-E002 OKX Q1 Midquote Confirmation — Results v0.1

Date: 2026-09-14  
Status: **MIDQUOTE_CONFIRMATION_PASS**

## Terminal result

The frozen four-day OKX Q1 causal-midquote confirmation completed successfully on the qualified VPS.

Terminal checks observed after completion:

- final report present: **YES**;
- verdict: `MIDQUOTE_CONFIRMATION_PASS`;
- completed days: `4`;
- final safety file present: **YES**;
- `final_verdict_written`: `true`;
- error file present: **NO**;
- 2024-Q2 OKX accessed: **NO**;
- formal Validation / Final accessed: **NO**;
- strategy P&L calculated: **NO**.

Finished timestamp reported by the frozen engine:

`2026-09-14T20:46:56.738307+00:00`

## Execution provenance

The run used the VPS infrastructure-only adapter:

`research/sc001/sc001_e002_okx_midquote_q1_confirmation_vps_launcher.py`

The adapter executed the exact frozen confirmation engine from commit:

`38d3ab050ff64555b0149c31c52e1ab1775ae579`

Frozen protocol commit:

`c6f9f01f7aed9a84786c6bb791ab88707dd1a5d7`

Phone partial checkpoints/results were not imported or inspected. The Android attempt remains classified as a technical interruption with no statistical verdict.

Before the confirmation run, VPS source staging passed for all required exact/D+1 trade archives and all four frozen Q1 L2 archives, including local size/SHA256 verification against the qualified Q006R/Q009A/Q009B parent reports.

## Interpretation

This result confirms that the frozen 5-second aggressive trade-flow signal retains positive causal L2-midquote predictability across all four predeclared non-pilot Q1 confirmation days under the frozen PASS gates.

This is still **not executable-strategy profitability proof**. No observed spread/depth execution, fees, slippage, position accounting, or strategy P&L was charged in this stage.

The result should not be treated as a fresh independent temporal OOS p-value because these Q1 dates were already opened for the earlier OKX transaction-price replication. It is a measurement-robustness confirmation.

## Stop rule and next step

Per `docs/research/sc001-current-roadmap-and-stop-rules-v1.1.md`, descriptive signal expansion now stops.

The next financial stage is to freeze a separately versioned **executable taker economics** experiment on already-open Q1 data before any P&L claim, including:

- causal live threshold/rule available at decision time;
- non-overlapping position/conflict logic;
- taker-only primary execution;
- 100 ms BASE / 250 ms STRESS / 500 ms diagnostic latency;
- first qualified L2 state at/after arrival;
- observed spread crossing;
- visible-book VWAP depth consumption;
- depth haircuts 0% / 25% / 50%;
- explicit fee ledger;
- period-appropriate lot/tick/contract metadata;
- gross edge, spread/depth cost, fee cost and net edge per trade after all costs;
- small predeclared threshold/search budget and multiple-testing ledger.

Primary economic metric: **NET EDGE PER TRADE AFTER ALL COSTS**.

2024-Q2 OKX remains unopened and protected as the next same-venue temporal holdout. If Q1 taker economics fails, do not rescue E002 by opening Q2 or post-hoc retuning.
