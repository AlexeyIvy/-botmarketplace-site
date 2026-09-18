# SC001 Current Roadmap and Stop Rules v4.34

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9-D0 DATA-SEMANTICS IMPLEMENTATION FROZEN / VPS PROBE NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.33.md`

## 1. Binding terminal states

All prior SC001 terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

No direct rescue-tuning, sign flip, parameter-neighbor retest, or post-hoc combination search is authorized.

## 2. Reusable knowledge governance remains binding

Current reusable block registry:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.1.md`

Current second-pass refinement:

`docs/research/sc001-c1-c6-second-pass-knowledge-extraction-audit-v0.1.md`

Future candidates must separate:

- strategy verdict;
- building-block evidence;
- feature role;
- execution architecture;
- edge-to-fill structure.

## 3. C9-D0 frozen scope

Feasibility card:

`docs/research/sc001-c9-scheduled-funding-mark-index-feasibility-card-v0.1.md`

Frozen D0 protocol:

`docs/research/sc001-c9-d0-okx-funding-mark-index-data-semantics-protocol-v0.1.md`

Frozen D0 runner:

`research/sc001/sc001_c9_d0_okx_funding_mark_index_semantics_v0_1.py`

Implementation freeze:

`docs/research/sc001-c9-d0-data-semantics-implementation-freeze-v0.1.json`

Frozen identities:

- protocol Git blob SHA: `d40ff705bb6451c75059394a6d19bf9157aff6dd`;
- runner Git blob SHA: `433f35c7da90cca26c6e4863c04c34e1e5eb8c9d`.

## 4. Probe universe and dates

Probe universe exactly:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;
- DOGE-USDT-SWAP;
- ORDI-USDT-SWAP;
- UNI-USDT-SWAP;
- XRP-USDT-SWAP;
- OP-USDT-SWAP;
- BCH-USDT-SWAP.

Probe windows only:

- `2024-07-01..2024-07-14`;
- `2024-09-01..2024-09-14`.

These are already contaminated Selection/Calibration dates.

No new clean period is opened by C9-D0.

## 5. C9-D0 semantics

C9-D0 may inspect only:

- current public SWAP instrument metadata;
- exact underlying/index identifier `uly`;
- funding-history timestamps and schema;
- realized/predicted funding fields only for numeric/schema validation;
- observed funding-time intervals reconstructed from `fundingTime`;
- historical mark-price 4H timestamp/schema coverage;
- historical index-price 4H timestamp/schema coverage;
- exact mark/index timestamp alignment;
- HTTP/data-volume facts.

No price or funding value may be used to select a C9 trading rule.

## 6. Funding interval rule

Do not assume a fixed eight-hour funding cycle.

C9-D0 reconstructs observed historical funding intervals from consecutive published `fundingTime` timestamps.

Observed interval changes are data semantics, not strategy parameters.

## 7. C9-D0 exact terminal states

PASS:

`C9_D0_DATA_SEMANTICS_PASS`

REVIEW:

`C9_D0_DATA_SEMANTICS_REVIEW`

REVIEW means data/source semantics need investigation. It is not a C9 strategy FAIL.

## 8. C9-D0 hard firewalls

The report must keep all false:

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

## 9. Protected periods remain closed

Still prohibited:

- July SOL/FIL/LTC/SUI holdout;
- July 16-30 gap;
- August 1-30 protected period;
- September SOL/FIL/LTC/SUI holdout;
- October Confirmation;
- legacy E006 March 22-30 Confirmation.

## 10. Current sequence

1. pull current GitHub state;
2. verify C9-D0 freeze/runner/protocol identities;
3. syntax-check C9-D0 runner;
4. run C9-D0 public-source probe;
5. require exact `C9_D0_DATA_SEMANTICS_PASS` or inspect REVIEW without retuning;
6. only after PASS design a separate frozen C9 state-transition sentinel;
7. do not choose C9 direction, threshold, event window or execution architecture from D0 output.

Immediate next action: run the frozen C9-D0 data-semantics probe on VPS.
