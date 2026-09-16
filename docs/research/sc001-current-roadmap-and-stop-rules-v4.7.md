# SC001 Current Roadmap and Stop Rules v4.7

Date: 2026-09-16  
Status: **CURRENT SC001 ROADMAP — TAKER KERNEL 24/24 PASS / HISTORICAL SPEC INVENTORY OPEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.6.md`

## 1. Binding terminal state

E001-E008 remain terminal/closed. E008 remains exact `E008_DISCOVERY_FAIL`.

SC001 remains independent from `R009-E002`, `R003-E003 Binance`, `R003-X003 Bybit`, `R010-E001` and `Safe-Sleeve S002`.

## 2. Synthetic taker kernel gate complete

Observed exact:

`SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION_PASS`

Observed:

- tests passed = `24 / 24`;
- real market-data body accessed = false;
- strategy signal calculated = false;
- promotional PnL calculated = false;
- July/August reserved bodies accessed = false;
- historical exact execution specs verified = false.

The normalized schema + taker kernel are mechanically validated on synthetic fixtures only. This is not real-data execution validation.

## 3. Historical spec gate remains unresolved

Binding standard:

`docs/research/sc001-historical-execution-spec-evidence-standard-v0.1.md`

Real historical discrete execution/PnL remains blocked until July/August 2024 execution-spec intervals are resolved sufficiently for every frozen instrument.

Current API metadata may not be backfilled as historical truth.

## 4. Current hard gate — historical spec evidence inventory

Protocol:

`docs/research/sc001-historical-execution-spec-inventory-protocol-v0.1.md`

Frozen reviewed evidence pack:

`docs/research/sc001-historical-execution-spec-known-evidence-v0.1.json`

Runner:

`research/sc001/sc001_historical_execution_spec_inventory.py`

Purpose:

- fetch exact current OKX metadata for all frozen 12 as diagnostic reference;
- attach already-reviewed official dated listing/adjustment evidence;
- report unresolved historical `tickSz/lotSz/minSz/ctVal` explicitly;
- keep July/August bodies closed;
- calculate no strategy signal/PnL.

Exact PASS:

`SC001_HISTORICAL_EXECUTION_SPEC_INVENTORY_PASS`

PASS means the inventory is complete and fail-closed; it does **not** mean historical execution specs are resolved.

## 5. Known official evidence already preserved

The frozen evidence pack includes, among other reviewed events:

- 2024 minimum-order/step-size changes affecting `SOL`, `DOGE`, `BCH`, `XRP`;
- a second 2024 SOL step/minimum reduction;
- later BTC/ETH/DOGE/XRP minimum-step events that help bracket later states but do not by themselves prove July/August intervals;
- original listing baselines for ORDI, SUI, UNI, LTC, BCH and XRP;
- regular-user maker/taker fee reference evidence.

Absence from the pack is not proof of no change.

## 6. After inventory PASS

1. review the per-field gap matrix;
2. add official dated evidence needed to bracket July/August intervals;
3. if necessary freeze a small engineering-only empirical lattice window outside promotional chronology for tick/size corroboration;
4. create exact dated spec intervals per instrument;
5. freeze fee assumption separately;
6. only after all required fields resolve, build raw->normalized converters and real-data mechanical execution validation;
7. run cheap E007 economic-feasibility audit;
8. only if warranted, freeze/open one strict new-ID E007 replication.

## 7. Stop rules

Do not:

- treat inventory PASS as historical-spec PASS;
- use current instrument metadata as July/August proof;
- open July/August strategy bodies merely to fill spec gaps before the reconstruction protocol is frozen;
- calculate promotional PnL while any required spec field is unresolved;
- reopen E001-E008.

## 8. Immediate VPS action

Pull latest code, syntax-check `sc001_historical_execution_spec_inventory.py`, run it once, and report the exact terminal token. No July/August bodies should be opened afterward until the gap report is reviewed.
