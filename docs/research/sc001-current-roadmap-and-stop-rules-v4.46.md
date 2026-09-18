# SC001 Current Roadmap and Stop Rules v4.46

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C8-D0 v0.3 PASS / C8-D1 HISTORICAL BODY-CLOCK INTEGRITY FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.45.md`

## 1. Binding terminal states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 still has no strategy verdict.

## 2. C8-D0 v0.3 result

Exact:

`C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_PASS`

Observed:

- six source/clock checks passed;
- OKX product mapping PASS;
- Bybit product mapping PASS;
- OKX current trade timestamp schema PASS;
- Bybit current trade timestamp schema PASS;
- OKX exact historical archive metadata/HEAD PASS;
- Bybit exact historical archive HEAD PASS;
- historical bodies unopened;
- no cross-venue price/return/dislocation/lag;
- no signal/PnL/promotional alpha;
- exit code 0.

Binding result:

`docs/research/sc001-c8-d0-v0.3-source-clock-pass-result-v0.1.md`

## 3. C8-D1 body access declared before opening

Current contamination registry:

`docs/research/sc001-contamination-registry-v0.10.json`

Authorized exact engineering bodies:

- `BTC-USDT-SWAP-trades-2025-01-15.zip`;
- `BTCUSDT2025-01-15.csv.gz`.

Role:

`NONPROMOTIONAL_ENGINEERING_CLOCK_CALIBRATION`

No cross-venue price comparison is authorized.

## 4. C8-D1 frozen implementation

Protocol:

`docs/research/sc001-c8-d1-historical-trade-clock-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c8_d1_historical_trade_clock_integrity_v0_1.py`

Freeze:

`docs/research/sc001-c8-d1-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `374e0859a98a9610d71621e97cb6d80bddb9377a`;
- runner: `abc11cb2e9852f55ad34635907325d289f6b11f0`;
- contamination registry: `3e802126b1f5b0253adb8d8a89c38f537bbd55b4`;
- D0 result: `4a20d265f55ea557af02f89aab1d713e440c394a`.

## 5. D1 exact synchronization rule

Before any cross-venue outcome:

- UTC grid: 1 second;
- grid points: 00:00:01 through 23:59:59 UTC;
- causal as-of: last venue trade with event timestamp <= boundary;
- no future interpolation;
- staleness limit: 2.000 seconds.

D1 uses timestamps only for synchronization diagnostics.

## 6. D1 PASS gates

Require:

- both exact archive identities/byte sizes match D0;
- compressed integrity;
- exact/known schemas;
- zero malformed target rows;
- zero out-of-day rows;
- zero timestamp reversals;
- OKX trade IDs strictly increasing;
- one consistent OKX timestamp scale;
- each venue usable-grid share >=0.98;
- joint usable-grid share >=0.95;
- each venue p99 staleness <=1000 ms;
- each venue maximum adjacent event-time gap <=5000 ms.

## 7. Synthetic gate

Before body-derived synchronization diagnostics require exact:

`C8_D1_SYNC_GOLDEN_PASS`

Golden tests cover no-future selection, exact-boundary eligibility, stale cutoff and monotone as-of behavior.

## 8. Exact D1 states

PASS:

`C8_D1_HISTORICAL_CLOCK_INTEGRITY_PASS`

REVIEW:

`C8_D1_HISTORICAL_CLOCK_INTEGRITY_REVIEW`

REVIEW remains engineering/clock state only.

## 9. D1 firewalls

D1 may open historical price fields only for per-venue numeric schema validation.

D1 must not calculate:

- cross-venue price difference;
- cross-venue return;
- dislocation;
- lag performance;
- leader;
- strategy signal;
- PnL;
- promotional alpha.

## 10. Consequence of PASS

Only after exact D1 PASS may a separate C8 structural dislocation/headroom sentinel be designed and frozen.

Before that sentinel, execution architecture and cost/fill hurdle must be chosen prospectively.

## 11. Immediate next action

Run frozen C8-D1 historical trade body/clock integrity on VPS.
