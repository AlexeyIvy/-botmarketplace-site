# SC001 Current Roadmap and Stop Rules v4.35

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9-D0 DATA-SEMANTICS IMPLEMENTATION FINALIZED / VPS PROBE NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.34.md`

## 1. Binding terminal states

All prior SC001 terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

No direct rescue-tuning, sign flip, parameter-neighbor retest, or post-hoc combination search is authorized.

## 2. C9-D0 final frozen implementation

Protocol:

`docs/research/sc001-c9-d0-okx-funding-mark-index-data-semantics-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c9_d0_okx_funding_mark_index_semantics_v0_1.py`

Implementation freeze:

`docs/research/sc001-c9-d0-data-semantics-implementation-freeze-v0.1.json`

Final frozen identities:

- protocol Git blob SHA: `d40ff705bb6451c75059394a6d19bf9157aff6dd`;
- runner Git blob SHA: `ff57e8f3d163ea043db928ecafd25f49a91c6b78`;
- implementation freeze Git blob SHA: `6a34bd0bda9363083f39fb90c2f4542999033261`.

## 3. Final D0 refinements

Before first run, two implementation refinements were made:

1. funding `method` must be recognized as `current_period` or `next_period`;
2. funding `formulaType` must be recognized as `noRate` or `withRate`.

A data-only `REVIEW` is not one-shot evidence and may be rerun under the exact same frozen implementation after a transient connectivity/source issue is diagnosed.

No alpha outcome existed before these refinements.

## 4. Probe scope

Exactly eight OKX USDT perpetual swaps:

BTC, ETH, DOGE, ORDI, UNI, XRP, OP, BCH.

Only already contaminated Selection/Calibration windows:

- `2024-07-01..2024-07-14`;
- `2024-09-01..2024-09-14`.

No new clean date is opened.

## 5. Data semantics only

C9-D0 may inspect:

- SWAP metadata and exact `uly`;
- funding timestamps/schema/observed intervals;
- 4H mark timestamp/schema coverage;
- 4H index timestamp/schema coverage;
- mark/index timestamp alignment;
- HTTP/data-volume facts.

Funding/price values may be parsed only for finite/schema validation and are not stored as strategy features.

## 6. Exact terminal states

PASS:

`C9_D0_DATA_SEMANTICS_PASS`

REVIEW:

`C9_D0_DATA_SEMANTICS_REVIEW`

REVIEW is not a C9 strategy FAIL.

## 7. Hard firewalls

Must remain false:

- funding values used for strategy;
- mark/index prices used for strategy;
- returns calculated;
- basis transition calculated;
- strategy signal calculated;
- sentinel outcome calculated;
- PnL calculated;
- direction selected;
- threshold selected;
- event window selected;
- protected data accessed;
- promotional alpha accessed.

## 8. Immediate next action

1. pull current GitHub state;
2. verify implementation freeze identity;
3. syntax-check C9-D0 runner;
4. run C9-D0 in tmux;
5. require exact PASS or inspect REVIEW without strategy reinterpretation;
6. only after PASS design a separate frozen C9 state-transition sentinel.

No C9 return/PnL computation is authorized yet.
