# SC001 Current Roadmap and Stop Rules v4.83

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-A FUNDING DIFFERENTIAL STRUCTURAL PREFLIGHT FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.82.md`

## 1. Prior terminal state

C11:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:

`C12_S0_REJECT_PARITY_REVERSION`

All C1-C10 remain closed.

## 2. Current non-alpha candidate pool

B13-A funding differential:

`ELIGIBLE_FOR_CHEAP_STRUCTURAL_PREFLIGHT`

B13-B launch dislocation:

`ELIGIBLE_FOR_SOURCE_AND_HEADROOM_PREFLIGHT`

B13-C explicit liquidation flow:

`DEFER_DATA_FEASIBILITY`

No C13+ ID assigned yet.

## 3. B13-A structural protocol

Binding:

`docs/research/sc001-b13a-funding-differential-structural-preflight-v0.1.md`

Venues:

- OKX;
- Bybit.

Universe:

previously frozen 12 symbols.

Window:

H1-2025 nonpromotional Selection/Calibration.

## 4. Frozen structural economics

Four fills.

Cost references:

- 20 bps fee floor;
- 10 bps spread/legging reserve;
- 10 bps execution/model reserve.

Structural burden:

`40 bps`

Qualifying funding differential:

`>=50 bps`

## 5. Primary statistic

Matched same-symbol settlement records within <=5 minutes.

Upper-bound funding transfer:

`10000 * abs(okx_settled_rate - bybit_settled_rate)`

No price PnL.

## 6. Structural survival

Require all:

- >=12 qualifying funding events;
- >=8 distinct dates;
- >=3 months;
- >=4 symbols;
- no symbol >50% of qualifying events.

Data-quality gates must pass first.

## 7. Candidate-ID gate

No `C13` assignment unless B13-A structurally survives and passes follow-up three-role review.

## 8. Immediate next action

Implement and freeze the B13-A source/funding-value runner.

No market-price or PnL run is authorized.
