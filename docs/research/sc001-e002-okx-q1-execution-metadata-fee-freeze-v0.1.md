# SC001-E002 OKX Q1 Execution Metadata & Fee Freeze v0.1

Date: 2026-09-15  
Status: **FROZEN BEFORE EXECUTION-ECONOMICS IMPLEMENTATION/RUN**

Scope: `BTC-USDT-SWAP`, four already-open 2024-Q1 confirmation dates only.

This document pins the external contract/fee metadata required by the Q1 taker-economics stage before any execution-economics result is observed.

## 1. Primary account tier / taker fee

Primary account assumption: **regular user / Lv1**.

Pinned taker fee:

- entry taker fee rate: `0.0005` = **0.05% = 5 bps**;
- exit taker fee rate: `0.0005` = **0.05% = 5 bps**;
- fee is charged separately on each fill notional;
- normalized round-trip fee is therefore approximately 10 bps when entry/exit notionals are similar, but implementation must calculate entry and exit fees from their actual VWAP notionals rather than hard-code 10 bps.

No VIP discount may replace the Lv1 primary fee after seeing results. A zero-fee decomposition remains diagnostic only as frozen in the parent protocol.

Official evidence:

1. OKX, `Perpetual Swap Fee Adjustment`, published 2019-10-28, effective 2019-11-04: regular Lv1 perpetual-swap maker `0.020%`, taker `0.050%`.
   - https://www.okx.com/en-us/help/okx-perpetual-swap-fee-adjustment
2. OKX, `How are futures trading fees calculated on OKX?`, published 2023-03-20: Lv1 taker `0.05%`, maker `0.02%`, and USDT-margined fee formula based on contract value × contracts × fill price × fee rate.
   - https://www.okx.com/en-eu/help/how-to-calculate-the-contract-transaction-fee

The Lv1 0.05% taker rate is therefore the predeclared historical/base-account fee used for the Q1 primary economics gate.

## 2. Contract value

Pinned contract value for the four 2024-Q1 dates:

- `ctVal = 0.01 BTC per contract`;
- contract multiplier = `1`;
- linear USDT-margined perpetual;
- settlement currency = USDT.

Official evidence:

1. OKX, `Adjustment of Face Value for USDT-margined Perpetual Swap & Futures Trading`, published 2020-03-04: BTCUSDT perpetual face value changed from `0.0001 BTC` to `0.01 BTC`, effective 2020-03-20.
   - https://www.okx.com/en-us/help/adjustment-of-face-value-for-usdt-margined-perpetual-swap-futures-trading
2. OKX perpetual-futures guide also specifies BTC/USDT contract size `0.01 BTC`.
   - https://www.okx.com/en-gb/help/i-perpetual-swaps

All frozen Q1 dates are years after the 2020 face-value change.

## 3. Q1 minimum order quantity / step size

Pinned for all four frozen dates (`2024-01-14`, `2024-01-31`, `2024-02-12`, `2024-02-13`):

- minimum order quantity: **1 contract**;
- order-size step: **1 contract**;
- equivalent base amount: **0.01 BTC**.

Official evidence:

OKX announced on 2024-04-19 that BTC/USDT perpetual minimum quantity and step would change on 2024-04-25 from **1 contract / 0.01 BTC** to **0.1 contract / 0.001 BTC**.

- https://www.okx.com/nb/help/okx-to-adjust-the-minimum-order-quantities-for-several-futures-24-04-19

Because every frozen economics date precedes 2024-04-25, the pre-adjustment value of 1 contract is the period-appropriate rule.

Do **not** use current OKX `minSz`/`lotSz` values for the Q1 backtest; those were reduced after the frozen sample.

## 4. Tick size

Pinned Q1 tick size:

- **0.1 USDT per BTC price unit**.

Evidence:

- original BTCUSDT perpetual specification listed tick size `0.1`;
- later/current OKX BTC/USDT perpetual specification remains `0.1`;
- implementation must additionally assert that all prices consumed from the already-qualified historical Q1 L2 archives lie on the `0.1` grid; any violation is an execution-metadata failure, not something to round silently.

References:

- https://www.okx.com/en-us/help/usdt-margined-perpetual-swap-now-available
- https://www.okx.com/en-gb/help/i-perpetual-swaps

## 5. Contract-quantity conversion

For a target quote notional `N` at entry:

1. reconstruct the first executable L2 state at/after arrival;
2. compute `arrival_mid_entry` from that state;
3. preliminary contracts = `floor(N / (0.01 * arrival_mid_entry))`;
4. enforce Q1 integer-contract step size;
5. if preliminary contracts < 1, use 1 contract and report that actual notional exceeds target;
6. execute exactly that many contracts against visible adjusted depth;
7. actual entry notional is `contracts * 0.01 BTC * entry_VWAP`;
8. exit the same contract quantity.

No quantity may be resized after seeing future depth or exit conditions.

## 6. Fee calculation

For each completed trade:

- `entry_fee_usdt = contracts * 0.01 * entry_vwap * 0.0005`;
- `exit_fee_usdt = contracts * 0.01 * exit_vwap * 0.0005`;
- `fee_cost_bps = (entry_fee_usdt + exit_fee_usdt) / actual_entry_notional * 10000`.

This fee ledger is separate from spread/depth cost.

## 7. Current API metadata is corroboration only

The current public instrument endpoint can be archived in run metadata for provenance, but its current `minSz/lotSz` must not overwrite the Q1 historical freeze.

Current public endpoint:

`GET https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP`

The historical minimum/step rule above is authoritative for these 2024-Q1 dates.

## 8. Firewall

This metadata freeze does not open Q2, formal Validation or Final and does not calculate alpha, P&L or execution economics.
