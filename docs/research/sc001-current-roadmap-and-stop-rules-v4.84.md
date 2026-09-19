# SC001 Current Roadmap and Stop Rules v4.84

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-A FUNDING STRUCTURAL PREFLIGHT IMPLEMENTATION FROZEN / RUN READY**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.83.md`

## 1. Terminal history unchanged

C11 remains terminal:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

C1-C10 remain closed.

## 2. B13-A remains pre-candidate

B13-A is still:

`B13-A_NOT_YET_C13`

No candidate ID is assigned.

## 3. Binding B13-A protocol

Protocol:

`docs/research/sc001-b13a-funding-differential-structural-preflight-v0.1.md`

Source/sign semantics:

`docs/research/sc001-b13a-funding-source-sign-semantics-freeze-v0.1.md`

Contamination registry:

`docs/research/sc001-contamination-registry-v0.22.json`

Runner:

`research/sc001/sc001_b13a_funding_differential_structural_preflight_v0_1.py`

Implementation freeze:

`docs/research/sc001-b13a-funding-differential-implementation-freeze-v0.1.json`

## 4. Frozen sources

OKX:

- historical market-data bulk funding;
- module 3;
- monthly archives;
- exact frozen 12-symbol family mapping.

Bybit:

- V5 funding history;
- linear perpetual;
- backward pagination.

No price source is used.

## 5. Frozen matching

Same symbol only.

Observed funding settlements only.

Timestamp tolerance:

`<= 5 minutes`

One-to-one nearest-skew deterministic assignment.

No fixed 8-hour assumption.

No stale carry-forward.

## 6. Frozen structural economics

Four fills.

Structural burden:

`40 bps`

Qualifying upper-bound funding differential:

`>=50 bps`

Primary statistic:

`10000 * abs(okx_rate - bybit_rate)`

This is not price PnL.

## 7. Data-quality gate

Require:

- >=8/12 source-eligible symbols;
- >=4 matched calendar months;
- >=500 matched funding settlements.

Failure:

`B13A_DEFER_SOURCE_OR_SAMPLE`

## 8. Structural gate

Require all:

- >=12 qualifying >=50 bps opportunities;
- >=8 distinct dates;
- >=3 months;
- >=4 symbols;
- no one symbol >50% of qualifying opportunities.

Failure after data-quality PASS:

`B13A_REJECT_STRUCTURAL`

Full structural survive:

`B13A_STRUCTURAL_PREFLIGHT_SURVIVE`

## 9. Consequence of SURVIVE

SURVIVE does not assign C13 automatically.

Next required step would be:

- three-role review;
- causal availability / pre-settlement predictability design;
- price/execution risk design;
- fresh chronology audit.

## 10. Hard firewalls

This run may not calculate:

- market price;
- basis;
- price convergence;
- trade/L2 signal;
- execution fills;
- strategy PnL.

No maker-rebate rescue.

No symbol selection after result.

## 11. Immediate next action

Run the frozen B13-A funding structural preflight once.

Do not interpret partial per-symbol output.
