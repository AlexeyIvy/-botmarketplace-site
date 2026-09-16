# SC001 — Pre-Period Liquidity Calibration Protocol v0.1

Date: 2026-09-16  
Status: **FROZEN BEFORE PRE-PERIOD LIQUIDITY OUTPUT**  
Scope: **SCALPING RESEARCH / SC001**

## 1. Purpose

Select a historically defensible first-generation OKX USDT-SWAP universe without using 2026 popularity, future strategy performance, or promotional PnL.

Parent candidate pool is the exact set classified `BOTH_ANCHORS_PASS` by:

`SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS`

Observed parent pool size before this protocol freeze: `66` instruments.

This stage is **engineering/calibration only**. It is not Discovery, Confirmation, Validation or Final evidence for any strategy.

## 2. Frozen calibration window

UTC dates exactly:

- 2024-02-24
- 2024-02-25
- 2024-02-26
- 2024-02-27
- 2024-02-28
- 2024-02-29

These dates become permanently contaminated for future use as untouched promotional evidence for any implementation whose universe or design is informed by this calibration.

## 3. Source

Use the official OKX public historical candlestick endpoint only:

`GET /api/v5/market/history-candles`

Instrument:

`<BASE>-USDT-SWAP`

Bar:

`1Dutc`

The response field `volCcyQuote` is used as quote-currency trading volume. Since all instruments in this stage are USDT-margined/quoted swaps, the calibration metric is directly comparable in USDT units.

No trade archive and no L2 archive is opened by this stage.

## 4. Required per-instrument integrity

For each of the 66 parent candidates require:

- exact instrument ID `<SYMBOL>-USDT-SWAP`;
- exactly one completed (`confirm=1`) `1Dutc` candle for every frozen calibration date;
- finite positive OHLC values;
- finite nonnegative `volCcyQuote`;
- no duplicate UTC day;
- no out-of-window row admitted.

An instrument with incomplete coverage is calibration-ineligible but remains recorded in the output denominator.

## 5. Frozen liquidity metric

For every instrument with 6/6 valid bars compute:

- median daily `volCcyQuote` over the six dates — **primary ranking metric**;
- mean daily `volCcyQuote` — diagnostic;
- minimum daily `volCcyQuote` — diagnostic;
- maximum daily `volCcyQuote` — diagnostic;
- total six-day `volCcyQuote` — diagnostic;
- active/valid day count.

No return, signal, alpha, response, trade trigger or PnL metric is permitted.

## 6. Frozen eligibility floor

An instrument is `LIQUIDITY_ELIGIBLE` only if:

- valid days = `6/6`;
- median daily quote turnover >= `10,000,000 USDT`.

This floor is frozen before viewing calibration output. It may not be lowered after results.

If fewer than 12 instruments pass, the stage returns REVIEW and the final universe remains unfrozen. Do not weaken the floor or silently shrink the target universe.

## 7. Frozen provisional universe rule

If at least 12 instruments are eligible:

1. sort eligible instruments by median daily quote turnover descending;
2. tie-break by exact instrument ID ascending;
3. provisional first-generation universe = first `12` instruments.

BTC and ETH are not manually forced into the top-12. Their rank is determined by the same rule. Their presence/rank is reported as a diagnostic.

No strategy output may influence selection.

## 8. Output status

Exact PASS token:

`SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS`

PASS requires:

- parent seeded probe exact PASS;
- parent both-anchor count >=16;
- all parent candidates attempted;
- at least 12 `LIQUIDITY_ELIGIBLE` instruments;
- deterministic top-12 produced;
- strategy signal/PnL = false;
- trade/L2 archive access = false.

Otherwise exact terminal token:

`SC001_PREPERIOD_LIQUIDITY_CALIBRATION_REVIEW`

## 9. Firewall

This stage must not:

- calculate E007 or any other strategy feature;
- inspect promotional strategy outcomes;
- download/open trade archives;
- download/open L2 archives;
- use current 2026 liquidity/rankings;
- tune the 10M threshold after output;
- choose/replace symbols by name, narrative or later performance.

## 10. After PASS

PASS produces a deterministic **provisional** top-12. Before that universe becomes binding for a new experiment:

1. record the six calibration dates in the contamination registry;
2. perform historical instrument-spec availability audit for the proposed top-12;
3. verify listing/spec continuity relevant to the intended research period;
4. then freeze exact symbols in a separate universe-freeze artifact.

No strategy Discovery is opened by this protocol.
