# SC001 Current Roadmap and Stop Rules v4.55

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C10-S0 TERMINAL REJECT / C7 NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.54.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8B-S0 remains terminal `C8B_S0_REJECT_HEADROOM`.

C10-S0 is now terminal:

`C10_S0_REJECT_HEADROOM`

No rescue tuning is authorized.

## 2. C10-S0 result integrity

Technical completion:

- exit code 0;
- sample gates all passed;
- bid-vacuum events = 6,443;
- ask-vacuum events = 6,331;
- event hours = 24;
- C5 labels/aggressive flow/fills/queue/fees/PnL = false;
- promotional alpha = false.

## 3. C10-S0 structural result

Observed:

- >=15 bps absolute 5s move events = 19;
- such event hours = 4;
- p50 absolute move ~0.9543 bps;
- p90 ~3.5799 bps;
- p99 ~8.4431 bps;
- max ~39.0877 bps;
- mean signed move ~+0.5803 bps;
- positive signed share ~58.67%.

Only frozen headroom gate that failed:

`p90_abs_move_gte15bps`

Terminal interpretation:

`AMPLE_SAMPLE_RARE_TAIL_BUT_INSUFFICIENT_BROAD_L2_VACUUM_HEADROOM`

## 4. No C10 rescue

Do not:

- isolate the 19 large events post hoc;
- change depth ratios;
- change side;
- change top levels;
- change baseline;
- change horizon;
- lower hurdle;
- add C5 labels;
- select another known Q1 day.

A materially different replenishment/tail mechanism requires a new ID.

## 5. C10 evidence outputs

Binding postmortem:

`docs/research/sc001-c10-s0-headroom-result-readonly-postmortem-v0.1.md`

Current feature registry:

`docs/research/sc001-feature-evidence-registry-v0.5.md`

Current reusable-block registry:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.4.md`

Current landscape:

`docs/research/sc001-strategy-landscape-v0.5.md`

## 6. Next remaining slate direction

Proceed to:

`C7 — SPREAD-QUALIFIED NON-BTC / MULTI-ASSET PASSIVE-HYBRID MAKER UNIVERSE`

C7 is the final direction in the previously frozen C9 -> C8 -> C10 -> C7 engineering/information-efficiency order.

## 7. C7 first-stage requirement

Before any multi-asset L2 body download:

1. freeze a pre-existing non-BTC candidate universe;
2. verify current instrument/product semantics;
3. verify exact historical 400-level L2 archive availability/size on one fixed date;
4. rank/select nothing by PnL;
5. open no historical L2 body.

## 8. Immediate next action

Freeze and run C7-D0 metadata-only multi-asset L2 availability preflight.

No spread/headroom outcome is authorized until D0 passes.
