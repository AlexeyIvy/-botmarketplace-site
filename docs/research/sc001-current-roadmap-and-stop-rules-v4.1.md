# SC001 Current Roadmap and Stop Rules v4.1

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — BLANK ENUMERATION REVIEW / SEEDED HISTORICAL ENUMERATION OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.0.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`.

No prior verdict is reopened. SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. First historical-universe probe result

Observed exact terminal:

`SC001_HISTORICAL_UNIVERSE_METADATA_PROBE_REVIEW`

Observed instrument count on the blank/wildcard-style enumeration path was zero.

Firewalls remained intact:
- market-data body downloaded = false;
- strategy signal/PnL calculated = false;
- promotional universe frozen = false.

Interpretation: the blank `instFamilyList` / omitted-family metadata request is not a valid method to enumerate the historical SWAP universe. It is not evidence that historical instruments were absent.

Do not rerun that method expecting a different result and do not fall back to today's top instruments.

## 3. Historically defensible fallback frozen

Protocol:

`docs/research/sc001-historical-universe-seeded-enumeration-protocol-v0.1.md`

Frozen historical seed:

`docs/research/sc001-historical-universe-seed-2023-12-30-v0.1.json`

The seed is a broad pre-period volatile/non-stable symbol pool derived from the public CoinMarketCap historical snapshot dated 2023-12-30. It is only a seed and is not the final universe or a strategy-performance ranking.

## 4. Current hard gate — exact OKX historical archive existence

Runner:

`research/sc001/sc001_historical_universe_seeded_probe.py`

For each seeded symbol the runner probes the exact OKX family `X-USDT` and exact daily trade archive on:

- 2023-12-30;
- 2024-02-29.

No archive body is downloaded.

Required exact PASS:

`SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS`

PASS also requires:
- BTC and ETH controls on both anchors;
- at least 16 symbols with exact archives on both anchors;
- no signal/PnL;
- final promotional universe still unfrozen.

## 5. Next sequence after seeded PASS

1. freeze a small pre-March non-promotional liquidity-calibration window;
2. acquire only required trade archives for the provisional candidate pool;
3. calculate exchange-specific historical trade count/turnover/activity and continuity;
4. perform contract-spec availability audit;
5. freeze deterministic eligibility and liquidity strata;
6. freeze final 8-12 instruments;
7. backfill contamination registry and freeze fresh chronology roles;
8. build common accounting + taker execution kernel;
9. run cheap E007 economic-feasibility audit;
10. only then freeze one new-ID E007 strict replication if warranted.

No L2 body acquisition is authorized by the current gate.

## 6. Stop rules

Do not:
- use today's live top-10 as the historical universe;
- treat the external historical seed itself as OKX eligibility;
- rank symbols by strategy performance during universe construction;
- download broad L2 bodies before final universe freeze;
- use same-date cross-asset evidence as chronological Confirmation;
- reopen E001-E008.

## 7. Immediate VPS action

1. `git pull --ff-only`;
2. syntax-check `research/sc001/sc001_historical_universe_seeded_probe.py`;
3. run it once;
4. report controls, both-anchor count and symbol list;
5. do not download any trade/L2 body until that output is reviewed.
