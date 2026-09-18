# SC001 Current Roadmap and Stop Rules v4.54

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C10-D0 PASS / C10-S0 LIQUIDITY-VACUUM SENTINEL FROZEN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.53.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8B-S0 remains terminal `C8B_S0_REJECT_HEADROOM`.

No rescue tuning is authorized.

## 2. C10-D0 result

Exact:

`C10_D0_LOCAL_L2_ELIGIBILITY_PASS`

Observed:

- pilot date = 2024-02-12;
- exact L2 body = `BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz`;
- exact bytes = 601,976,188;
- Q009B parent PASS;
- E008 inventory parent PASS;
- L2 body not opened/hashed by C10-D0;
- no feature/event/future move/fill/queue/PnL;
- C5 labels not used;
- exit code 0.

Binding result:

`docs/research/sc001-c10-d0-local-btc-l2-eligibility-pass-result-v0.1.md`

## 3. C10 calibration role declared before body reuse

Current contamination registry:

`docs/research/sc001-contamination-registry-v0.13.json`

The 2024-02-12 BTC OKX L2 body is explicitly reused for C10 as:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

C5 labels and aggressive-flow conditioning remain prohibited.

## 4. C10-S0 mechanism frozen

Protocol:

`docs/research/sc001-c10-s0-near-touch-liquidity-vacuum-headroom-sentinel-v0.1.md`

Runner:

`research/sc001/sc001_c10_s0_near_touch_liquidity_vacuum_v0_1.py`

Freeze:

`docs/research/sc001-c10-s0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `1ace4f238f1b2542ba99b8ff9a1c09b12c3c9969`;
- runner: `8ade982728c44ce66c28fcdea79b08a8b1af3d0c`;
- registry: `844bd6cbae72985a295d9c3e653c7209f9e31e7f`;
- D0 result: `4ff69067984179975c58e55a6ac6bcdf069ca605`.

## 5. Frozen book-state event

At causal 1-second sampled L2 states:

- freshness <=1000 ms;
- top 5 visible levels per side;
- side depth baseline = median over prior 60 wall-clock seconds;
- minimum 45 prior valid observations.

Bid vacuum:

- current bid near-touch depth <=1/3 of its causal median;
- current ask near-touch depth >=2/3 of its causal median.

Ask vacuum symmetric.

Event is counted only on observable onset from an immediately preceding valid NONE state.

## 6. Frozen outcome

Primary horizon:

`5 seconds`

Reference outcome:

`absolute midquote log move in bps`

Directional signed move is recorded descriptively only:

- ask vacuum -> positive/up diagnostic;
- bid vacuum -> negative/down diagnostic.

No direction optimization is allowed.

## 7. Structural reference

A later directional taker implementation would require two structural fills.

Frozen screening reference:

- 5 bps/fill;
- 10 bps fee-reference floor;
- 15 bps gross move hurdle.

S0 itself models no execution.

## 8. Sample gates

Require:

- valid sampled seconds >=80,000;
- baseline eligible seconds >=70,000;
- evaluable events >=50;
- event hours >=8;
- bid-vacuum events >=10;
- ask-vacuum events >=10.

Sample failure:

`C10_S0_DEFER_SAMPLE`

## 9. Structural headroom gates

Require all:

- >=10 events with absolute 5s move >=15 bps;
- those large-move events span >=4 UTC hours;
- p90 absolute 5s move >=15 bps;
- maximum absolute 5s move >=30 bps.

Survive:

`C10_S0_HEADROOM_SURVIVE`

Sample passes but any headroom gate fails:

`C10_S0_REJECT_HEADROOM`

## 10. Hard no-rescue rules

After output do not:

- change top-5 depth;
- change 60s baseline or 45-observation minimum;
- change 1/3 or 2/3 ratios;
- change onset rule;
- change 5s horizon;
- lower 15 bps hurdle;
- use C5 labels/aggressive flow;
- select only bid or ask events;
- change pilot day.

A materially different L2 mechanism requires a new ID.

## 11. Firewalls

C10-S0 must keep false:

- C5 labels used;
- aggressive-flow conditioning;
- fill model;
- queue model;
- fees;
- PnL;
- promotional alpha.

## 12. Immediate next action

Run frozen C10-S0 exactly once on the 2024-02-12 nonpromotional BTC L2 calibration body.
