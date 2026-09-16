# SC001 Current Roadmap and Stop Rules v4.0

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — UNIVERSE GOVERNANCE FROZEN / METADATA PROBE OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v3.9.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact terminal:

`E008_DISCOVERY_FAIL`

No rescue-tuning, no promotional rerun, no E008 Confirmation, no Q2/formal Validation/Final.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Current research architecture

Binding working architecture:

- `docs/research/sc001-next-generation-multi-asset-research-framework-v0.3.md`;
- `docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`.

Future promotional simulation must separate market events, strategy intents, order lifecycle, immutable fills, independent accounting and statistics.

## 3. Historical-universe governance stage complete

Created:

`docs/research/sc001-historical-universe-selection-protocol-v0.1.md`

Initial product family for first-generation replication is frozen at the family level as:

**OKX linear USDT-margined perpetual SWAPs.**

Exact symbols are not frozen yet.

Target final universe remains roughly 10 instruments, acceptable range 8-12 only for objective eligibility/data constraints.

No current-popularity top-10 selection is allowed.

## 4. Contamination registry initiated

Created:

`docs/research/sc001-contamination-registry-v0.1.json`

The registry is explicitly partial/conservative and currently records the highest-priority known contaminated BTC periods, including:

- E008 engineering dates;
- E008 promotional Discovery dates;
- prior E008 protected Confirmation dates as non-repurposable by default;
- March 2024 BTC periods used/acquired by E003-E007 work.

Default rule:

**if prior-use status is uncertain, the date is not fresh until audited.**

The registry must be backfilled before any date is promoted as clean Discovery/Confirmation for a new implementation.

## 5. Current hard gate — metadata-only historical universe enumeration

Runner:

`research/sc001/sc001_historical_universe_metadata_probe.py`

Purpose:
- determine whether official OKX historical metadata can enumerate contemporaneous USDT-SWAP trade archives/instruments for historical dates;
- avoid reconstructing a 2024 universe from today's surviving live instruments.

The probe is metadata-only.

It must NOT:
- download trade/L2 bodies;
- open trade/L2 rows;
- calculate any signal or PnL;
- rank instruments by strategy performance;
- freeze the final promotional universe.

Exact PASS token:

`SC001_HISTORICAL_UNIVERSE_METADATA_PROBE_PASS`

If the probe returns REVIEW, do not fall back to a hand-picked current top-10 list. Investigate an alternative historically defensible enumeration source/method.

## 6. Next sequence after metadata probe PASS

1. inspect historical instrument sets/counts on probe dates;
2. determine whether archive metadata alone can reconstruct the candidate pool;
3. if necessary, freeze a dedicated pre-period liquidity calibration window that is permanently engineering/contaminated;
4. perform historical contract-spec availability audit;
5. freeze deterministic eligibility/stratification rules;
6. freeze exact 8-12 instruments;
7. freeze fresh chronology roles;
8. build common normalized data/accounting infrastructure;
9. build and validate taker execution kernel;
10. run cheap E007 economic-feasibility audit;
11. only then consider a strict new-ID E007 multi-asset replication.

Passive-maker execution v2 remains a later/parallel track and does not block E007.

## 7. Stop rules

Do not:
- download a large new multi-asset promotional body set before universe governance is complete;
- infer 2024 eligibility from today's live-instrument list alone;
- select assets based on later popularity/performance;
- label cross-asset same-date evidence as chronological Confirmation;
- reuse known contaminated BTC dates as fresh proof after redesign;
- reopen prior terminal experiments;
- build a promotional runner before common accounting/execution validation gates pass.

## 8. Immediate action on VPS

1. `git pull --ff-only`;
2. syntax-check the metadata probe;
3. run the metadata probe once;
4. report the terminal token and instrument counts;
5. do not download any market-data body as a follow-up until the output is reviewed.
