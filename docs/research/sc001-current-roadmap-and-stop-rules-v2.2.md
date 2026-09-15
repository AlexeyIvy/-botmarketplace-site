# SC001 Current Roadmap and Stop Rules v2.2

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.1.md`

## 1. Terminal history

- E001: terminal `FAIL`; no rescue tuning.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`; TFI retained only as future auxiliary knowledge.
- E003: terminal `E003_DISCOVERY_FAIL`; no Confirmation/L2/rescue.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only diagnostic postmortem complete.
- E005: remains closed because viable-E004 prerequisite failed.
- E006: terminal `E006_DISCOVERY_FAIL`; no Confirmation/L2/rescue.

SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Nothing in SC001 changes their frozen rules, decisions or forward clocks.

Q2, formal Validation and Final remain closed.

## 2. E006 terminal result

Recorded in:

`docs/research/sc001-e006-discovery-results-v1.0.md`

Primary frozen E006 produced only one completed pair on one active day.

Observed primary gross edge was approximately `+27.405 bps`, but frozen promotion required substantially stronger economics and much broader evidence:

- completed pairs: 1 vs >=20;
- active days: 1 vs >=10;
- pooled mean: ~27.405 bps vs >=40;
- trimmed mean: ~27.405 bps vs >=35;
- median active-day mean: ~27.405 bps vs >=30;
- top-day concentration: 1.0 vs <=0.30;
- latency-stress mean gates failed.

The result is classified as **event-scarcity + insufficient-economics-headroom**, not a near-zero-edge mechanism failure.

E006 terminal token remains:

`E006_DISCOVERY_FAIL`

## 3. E006 stop rule

Do not:

- run E006 Confirmation;
- acquire paired L2 for E006;
- lower the +50 bps trigger;
- change the sign, six-hour baseline, 10-second VWAP/grid, exit, max hold or latency;
- add TFI/FLOW_IMPULSE/E004 filters;
- use day/hour filters;
- open Q2/Validation/Final;
- reinterpret the single positive pair as evidence of viability.

No E006 diagnostic sweep is authorized.

## 4. Consolidated lesson after E001-E006

The branch now has several distinct failure modes:

1. small predictive/microstructure effects can exist but remain far below taker costs;
2. post-event continuation can fail at the gross-mechanism level;
3. volatility-breakout residual movement can be near zero;
4. relative-value dislocations can be economically nontrivial per event yet too rare and too close to the four-fill fee burden to form a viable standalone strategy;
5. future candidates need both a natural tens-of-bps response scale and sufficient event breadth.

## 5. Active next candidate: SC001-E007

Planning document:

`docs/research/sc001-e007-extreme-displacement-mean-reversion-research-plan-v0.1.md`

Candidate family:

**extreme short-horizon BTC-USDT-SWAP displacement -> partial mean reversion.**

This is a new experiment family, not a rescue of E001-E006.

Primary economic story under consideration:

- a rare large short-horizon displacement may contain temporary liquidity-vacuum / forced-flow overshoot;
- the intended trade direction is reversal against the displacement;
- continuation is not to be selected later as the better-looking sign.

No E007 alpha is authorized.

## 6. E007 current hard gate

Before first E007 alpha:

1. critically review the planning document from financial, mathematical and programming perspectives;
2. choose one exact causal price statistic and one primary event definition from first principles;
3. freeze an absolute/economics-first displacement threshold before output;
4. freeze entry latency/tolerance, reversal direction, exit, max hold, cooldown/daily cap;
5. freeze Discovery/Confirmation chronology;
6. freeze robust gross-economics gates with material headroom above approximately 10 bps one-leg round-trip taker fees;
7. freeze implementation and no-alpha preflight;
8. only exact preflight PASS may open one DEV-DISCOVERY.

## 7. E007 data boundary

Initial Discovery design may use only already-qualified OKX `BTC-USDT-SWAP` March-2024 trade data.

Candidate Discovery performance interval:

- 2024-03-01..20.

March 21 may be used only where required for D+1 UTC reconstruction and remains performance-excluded.

No new L2, Q2, Validation or Final access is authorized before frozen gross economics justify it.

## 8. Base-feature firewall

Base E007 may not use:

- E002 TFI;
- E003 FLOW_IMPULSE;
- E004 compression;
- E006 basis;
- post-hoc event/day/hour filters;
- winner-only sign selection.

## 9. Immediate next action

Do **not** run a new script yet.

Perform the pre-alpha critical audit of E007 planning v0.1 and freeze the exact executable protocol before any E007 response/return output.
