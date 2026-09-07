# R001 Option Selector Prototype v0.1

Status: research-only, not production trading code.

## Purpose

Validate that a historical Deribit options-chain dataset can support deterministic, look-ahead-safe selection of a BTC option by option type, target delta and target DTE before building the full R001 backtest.

## Input data contract

Expected normalized fields from a Deribit options-chain snapshot/update dataset:

- exchange
- symbol
- type
- strike_price
- OI
- bid_price / bid_amount / bid_iv
- ask_price / ask_amount / ask_iv
- mark_price / mark_iv
- underlying_index
- underlying_price
- delta / gamma / vega / theta / rho
- timestamp
- local_timestamp

## First target experiment

At a chosen historical UTC decision timestamp:

1. use only observations with exchange timestamp <= decision timestamp;
2. reconstruct the latest observation per option symbol;
3. reject stale observations older than a predefined maximum age;
4. reject expired options and quotes with invalid/non-positive bid or ask;
5. filter to BTC puts;
6. restrict to expiries within a coarse DTE window around 90 days;
7. choose the listed expiry closest to target 90 DTE;
8. within that expiry choose absolute delta closest to 0.15;
9. tie-break by narrower relative bid/ask spread and then higher open interest;
10. record the historical ask as the executable buy reference.

No weighted optimizer is used for the initial selector.

## Required audit output

Every selection must emit:

- decision timestamp;
- source quote timestamp and staleness;
- symbol;
- expiry;
- DTE;
- strike;
- underlying price;
- delta;
- bid / ask;
- relative spread;
- bid / ask IV;
- mark IV;
- open interest;
- selection parameters and rejection rules.

The record must be reproducible from the same raw input data.

## Initial research parameters

Primary smoke-test selector:

- underlying: BTC;
- venue: Deribit;
- option type: put;
- target absolute delta: 0.15;
- target DTE: 90 days;
- DTE tolerance: +/-30 days;
- maximum quote staleness: initially 10 minutes, to be validated from real data;
- entry price: historical ask.

These values are research defaults, not accepted optimal parameters.

## Non-goals

This prototype intentionally does not yet implement:

- portfolio sizing;
- premium budget accounting;
- option exits or rolls;
- mark-to-market NAV;
- settlement;
- commissions;
- slippage beyond bid/ask;
- calls;
- ladders;
- volatility-regime logic;
- production exchange integration.

## Validation gates

The selector is considered ready for the next step only when a real historical data sample demonstrates that:

1. schema fields are present and correctly interpreted;
2. historical instruments can be reconstructed without future data;
3. delta/DTE selection is deterministic;
4. selected quotes have executable-looking bid/ask values;
5. stale/missing quotes are rejected rather than silently imputed;
6. selections can be manually audited against raw rows.

After these gates pass, the next artifact is the R001 E003 put-only portfolio simulator.