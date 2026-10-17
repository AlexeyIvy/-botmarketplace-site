# DeepSeek + Google Colab: BTC MA20/50 diagnostic backtest

External research supplied by the repository owner on 2026-10-17. The strategy
and original script are attributed to DeepSeek; the reported run used Google
Colab. The separate offline audit below checks the supplied arithmetic and
files. It does not authenticate the provider or establish a trading edge.

**Classification: diagnostic backtest; trading edge not confirmed.** This is an
isolated archival record, not a production strategy, deployment instruction,
research admission, or change to the project's shared research state.

## Files and provenance

- `original_submitted_deepseek.py`: the complete final supplied Python script,
  preserved unchanged. It includes a live `ccxt.kucoin()` download block.
  **Do not run or import this file to reproduce the archived result.** A fresh
  download can change the sample, overwrite CSVs, and include an unfinished bar.
- `btc_raw_data.csv`: original supplied frozen OHLCV input, unchanged.
- `trades_log.csv`: original supplied six-trade output, unchanged.
- `offline_verify_exact_function.py`: separate audit adapter. It extracts the
  original `run_audited_backtest` function and benchmark expression unchanged,
  runs them against the local frozen CSV, and checks the archived output without
  invoking the original download/plot/save blocks or making network calls.
- `source_provenance.json`: attribution and source-preservation record.
- `verification_results.json`: compact offline verification and source hashes.

The original script names KuCoin spot `BTC/USDT`, daily bars, `limit=1000`.
That identifies the claimed acquisition method only. No authenticated exchange
response, extraction timestamp, package lock, or original Colab runtime record
was supplied. The SHA-256 hashes identify the submitted bytes; they do not
authenticate market prices. No account balances, live trades, or trading
credentials are included. All dollar-denominated values are simulated capital.

## Fixed model and sample

- 1,000 ascending, unique, gap-free daily dates: 2024-01-22 to 2026-10-17.
  Numeric OHLCV fields are finite and positive; every bar passes OHLC bounds.
- First 700 rows: 2024-01-22 to 2025-12-21. Last 300 rows: 2025-12-22 to
  2026-10-17. No parameter fitting is performed by this final script.
- MA20 and MA50 are simple rolling means of closes computed within the test
  slice. The first 50 test rows are warm-up, through 2026-02-09.
- First equity observation/signal: 2026-02-10; first fill: 2026-02-11 open.
  There are 250 daily equity observations and 249 return intervals.
- Close-of-day signal, following observed day's open execution; long or short;
  fixed units held until reversal. Entry notional is 100% of then-current
  pre-entry capital, so dollar sizing compounds between trades.
- Initial simulated capital 10,000; fee 0.1% of notional on each entry and
  exit. Forced terminal liquidation uses the last supplied Close.

## Reproduced model diagnostics

| Metric | Result |
| --- | ---: |
| Final simulated capital | 12,488.636804 |
| Sum of six net trade PnLs | 2,488.636804 |
| Return after modeled entry/exit fees | +24.886368% |
| Total modeled fees | 116.354080 |
| Daily-close maximum drawdown | 19.484840% |
| Buy-and-hold, same equity observation window, before fees | +18.504138% |
| Buy-and-hold, same window and model fee convention | +18.285634% |
| Last long's share of total net profit | 99.6802% |

The benchmark above starts at the 2026-02-10 Close and ends at the same final
Close as the strategy. It uses the same pre-entry-capital fee convention, not
a separate cash-funded convention. The strategy is flat at its first equity
observation and begins trading at the next open. A benchmark measured over all
300 rows would include the strategy's 50-row warm-up and is not the aligned
comparison above. Drawdown is sampled at daily closes, not intraday.

The final supplied script's graph already uses this aligned gross benchmark.
Its title says it includes warm-up, but both plotted series begin after the
50 warm-up rows. The original benchmark has no fees; the fee-adjusted figure
above is a separate audit calculation. The script creates and prints the train
slice but never uses it to fit or select anything.

The first five trades contribute only 7.958569 of total net profit; the final
long contributes 2,480.678235. This concentration limits evidence of
repeatability, although it is not itself an accounting error.

## Limitations and interpretation

1. The 2026-10-17 row was supplied and checked before that UTC day ended.
   If these are UTC daily candles, its Close is provisional. The CSV has no
   candle-finality flag. Removing only that row while keeping the original
   700-row split fixed yields a separate sensitivity diagnostic of +24.924670%,
   not a replacement holdout or an independently sourced result.
2. This sample has already been inspected during strategy revisions. Calling
   its 30% slice "test" does not make it clean, untouched out-of-sample
   evidence. Six completed trades do not establish repeatable alpha.
3. Short returns are a price-PnL proxy applied to spot candles. Borrow
   availability/cost, margin, liquidation, funding, spread, slippage, order
   latency, capacity, and executable fill quality are not modeled.
4. Entry notional consumes all pre-entry capital before its fee is deducted.
   A cash-only long implementation needs reduced sizing, a fee reserve, or
   borrowing. The archived model is not repaired or recast as fully executable.
5. The earlier same-bar implementation's approximately +30.75% result is
   invalid as performance evidence because of its execution timing. It is
   superseded, not reproduced here. Differences between separately downloaded
   runs cannot be attributed solely to a code change.
6. Agreement between code and files establishes internal reproducibility only.
   It does not independently authenticate KuCoin data, eliminate sample
   selection bias, prove robustness, or authorize trading or deployment.

## Offline reproduction

Use Python 3 with pandas installed. From this folder, run:

```sh
python3 offline_verify_exact_function.py --input-dir . --output-dir /tmp/deepseek-verify
```

The verifier uses the frozen inputs and the unchanged extracted function. It
asserts the input hashes, trade-log agreement, capital reconciliation and data
checks. It prints the result and writes regenerated trades, equity, results and
checksums only into the separate output directory. The folder above is a local
example; choose a fresh writable directory appropriate to your system. It does
not install packages or access an exchange. No generated duplicate trade/equity
files need to be committed. Audit runtime details are recorded separately from
the unknown original Colab environment in `verification_results.json`.
