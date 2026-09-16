# SC001 Current Roadmap and Stop Rules v4.2

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — SEEDED HISTORICAL UNIVERSE PASS / LIQUIDITY CALIBRATION OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.1.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`.

No prior verdict is reopened. SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Historical-universe seeded probe passed

Observed exact terminal:

`SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS`

Observed:
- BTC+ETH controls pass = true;
- both-anchor instruments = `66`;
- exact OKX archive existence confirmed on both frozen anchors;
- market-data archive body downloaded = false;
- strategy signal/PnL calculated = false;
- promotional universe frozen = false.

Therefore the provisional historical OKX candidate pool is sufficiently broad for objective pre-period liquidity calibration.

## 3. Liquidity calibration protocol frozen

Protocol:

`docs/research/sc001-preperiod-liquidity-calibration-protocol-v0.1.md`

Runner:

`research/sc001/sc001_preperiod_liquidity_calibration.py`

Calibration window, permanently engineering/non-promotional:

- 2024-02-24
- 2024-02-25
- 2024-02-26
- 2024-02-27
- 2024-02-28
- 2024-02-29

## 4. Source and cost optimization

Instead of downloading hundreds of daily trade archives merely to rank liquidity, the stage uses the official OKX historical-candlestick endpoint with `1Dutc` bars.

Primary ranking metric:

`median daily volCcyQuote` in USDT across the six calibration days.

This is a calibration/engineering market-data read only. It does not calculate strategy alpha or PnL and does not open trade/L2 archives.

## 5. Frozen eligibility and selection rule

An instrument is liquidity-eligible only when:

- exact 6/6 completed UTC daily bars are present;
- median daily quote turnover >= `10,000,000 USDT`.

If fewer than 12 instruments qualify, terminal state is REVIEW and the threshold may not be weakened after output.

If at least 12 qualify:

1. sort by median daily quote turnover descending;
2. exact instrument ID ascending as tie-break;
3. deterministic proposed universe = top `12`.

No manual inclusion/substitution by token name is permitted.

## 6. Current hard gate

Required exact terminal:

`SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS`

PASS requires at least 12 eligible instruments and deterministic proposed top-12.

The resulting top-12 remains **provisional**, not yet binding promotional universe.

## 7. Next sequence after calibration PASS

1. record the six calibration dates in the contamination registry;
2. audit historical contract/spec availability for the proposed top-12;
3. verify listing/spec continuity relevant to the planned replication horizon;
4. freeze exact first-generation multi-asset universe;
5. freeze fresh chronology roles;
6. build common normalized data/accounting infrastructure;
7. build and mechanically validate taker execution kernel;
8. run cheap E007 economic-feasibility audit;
9. only if warranted, freeze one new-ID E007 strict replication.

Passive-maker execution v2 remains a separate later track.

## 8. Stop rules

Do not:
- alter the 10M eligibility floor after output;
- manually swap symbols into/out of the proposed top-12;
- use current 2026 rankings;
- calculate strategy performance during universe selection;
- download broad L2 bodies before universe/spec/chronology freeze;
- reopen E001-E008.

## 9. Immediate VPS action

1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_preperiod_liquidity_calibration.py`;
3. run it once;
4. report terminal token, eligible count and proposed top-12;
5. do not begin strategy simulation after output until spec audit is reviewed.
