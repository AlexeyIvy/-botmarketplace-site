# SC001 Current Roadmap and Stop Rules v2.4

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.3.md`

## 1. Terminal history

- E001: terminal `FAIL`; no rescue tuning.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`; TFI retained only as auxiliary knowledge.
- E003: terminal `E003_DISCOVERY_FAIL`; no Confirmation/L2/rescue.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only postmortem complete.
- E005: remains closed because viable-E004 prerequisite failed.
- E006: terminal `E006_DISCOVERY_FAIL`; event-scarcity + insufficient headroom.
- E007: terminal `E007_DISCOVERY_FAIL`; moderate gross reversal effect but insufficient/unstable economics and latency robustness.

SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. E007 terminal result

Recorded in:

`docs/research/sc001-e007-discovery-results-v1.0.md`

Key E007 facts:

- completed/active-day breadth gates passed;
- pooled mean gross edge ~`18.28 bps` vs `>=30`;
- trimmed mean ~`21.49 bps` vs `>=25`;
- median active-day mean ~`2.99 bps` vs `>=25`;
- positive active-day share ~`63.64%` vs `>=70%`;
- bootstrap LCB ~`4.32 bps` vs `>15`;
- daily concentration gates failed;
- 1,000 ms / 2,000 ms mean stress degraded to ~`15.75 / 11.34 bps`.

E007 is terminal `E007_DISCOVERY_FAIL` and is not rescue-tuned.

## 3. Strategic pivot after E001-E007

The branch now has enough evidence that continuing neighboring one-leg taker variants is not the highest-value path.

Reasons:

1. confirmed predictive signals can be orders of magnitude too small for taker economics;
2. several event-driven directional mechanisms have either near-zero residual edge or insufficient robustness;
3. E007 produced the strongest broad one-leg gross response so far, yet still lacked enough headroom and latency stability;
4. repeatedly paying spread + taker fees is the common structural handicap.

Therefore the next priority changes the execution/economic mechanism rather than the directional signal family.

## 4. Active next candidate: SC001-E008

Planning document:

`docs/research/sc001-e008-passive-maker-spread-capture-research-plan-v0.1.md`

Candidate family:

**conservative passive maker spread capture on OKX BTC-USDT-SWAP with explicit queue/adverse-selection modeling.**

No E008 maker P&L or profitability is authorized.

E008 is not a rescue of E002/E007. Base E008 initially excludes TFI and all prior signal families.

## 5. Existing qualified L2 assets

Already-qualified full-day L2 research days:

Q009A:
- 2024-01-14 — `FULL_DAY_PASS`, expected archive bytes `426,641,072`;
- 2024-01-31 — `FULL_DAY_PASS`, expected archive bytes `519,114,508`.

Q009B:
- 2024-02-12 — `FULL_DAY_PASS`, expected archive bytes `601,976,188`;
- 2024-02-13 — `FULL_DAY_PASS`, expected archive bytes `550,675,409`.

These days were previously used in E002 infrastructure/midquote research, therefore E008 may use them only for data-model feasibility and simulator validation, not as sole promotional evidence.

## 6. Current hard gate: E008 data inventory / synchronization feasibility

Before any fill simulation or maker P&L:

1. verify whether the four Q009 L2 reports and archive bodies are accessible on the qualified VPS;
2. verify exact known identities/sizes and replay PASS state;
3. inventory corresponding BTC-USDT-SWAP trade tapes for the same dates;
4. determine whether L2 and trade streams can be aligned causally and deterministically;
5. determine whether the available data expose enough information for a conservative queue-ahead / fill model;
6. explicitly record limitations such as lack of order IDs / exact queue priority.

This stage is data engineering only.

Allowed terminal states:

- `E008_DATA_INVENTORY_PASS` — all required local inputs are present/qualified for the next no-P&L queue-model audit;
- `E008_DATA_INVENTORY_REVIEW` — one or more inputs must be restaged/acquired before continuing.

Neither status authorizes maker profitability calculation.

## 7. E008 base-strategy firewall

Until an independently viable passive base exists, do not use:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression;
- E006 basis;
- E007 displacement;
- winner-only side/day/hour filters;
- VIP fee/rebate assumptions selected after output.

If a base later passes, TFI may be tested only in a separately frozen incremental experiment as an adverse-selection veto/timing feature.

## 8. Conservative execution principle

E008 must prefer false negatives to optimistic fills.

Quote disappearance alone is never sufficient to claim a fill. If exact queue priority is unavailable, the future simulator must use a pessimistic lower-bound queue assumption and require causal executed-volume / price-through evidence under a frozen rule.

A strategy that profits only under generous fill assumptions is terminally rejected.

## 9. Immediate next action

Run only the E008 no-alpha/no-P&L data inventory script on the qualified VPS.

Do not calculate fills, spread capture, inventory P&L or maker profitability yet.
