# SC001 Current Roadmap and Stop Rules v4.45

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8-D0 v0.2 REVIEW CLASSIFIED / v0.3 PRIAPI RESOLVER FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.44.md`

## 1. Binding terminal states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 has no strategy verdict.

## 2. C8-D0 v0.2 result

Exact:

`C8_D0_V02_SOURCE_CLOCK_PREFLIGHT_REVIEW`

with:

- checks passed `5/6`;
- OKX instrument PASS;
- Bybit instrument PASS;
- OKX current trade clock PASS;
- Bybit current trade clock PASS;
- Bybit historical archive PASS;
- OKX exact historical archive unresolved through the public GET historical metadata endpoint;
- no historical archive body opened;
- no cross-venue price/return/dislocation/lag;
- no signal/PnL/promotional alpha.

Classification remains:

`SOURCE_TRANSPORT_EXACT_DATE_RESOLUTION / NOT_RESEARCH_FAIL`

## 3. v0.3 repair basis

SC001 Q005R previously established a working OKX historical daily-trade discovery route:

`POST /priapi/v5/broker/public/trade-data/download-link`

with `module=1`, `instType=SWAP`, exact family and daily date bounds.

C8-D0 v0.3 switches only the OKX historical metadata transport to this already-qualified resolver.

No C8 mechanism or body-access rule changes.

## 4. Frozen target identity

Exact OKX historical file:

`BTC-USDT-SWAP-trades-2025-01-15.zip`

Exact Bybit historical file:

`BTCUSDT2025-01-15.csv.gz`

Historical bodies remain closed in D0.

## 5. C8-D0 v0.3 frozen implementation

Protocol:

`docs/research/sc001-c8-d0-okx-bybit-source-clock-semantics-protocol-v0.3.md`

Runner:

`research/sc001/sc001_c8_d0_v03_okx_bybit_source_clock_preflight.py`

Freeze:

`docs/research/sc001-c8-d0-v0.3-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `fda14b5e263e108fdeea54f394a468526ba2fe37`;
- runner: `03f1772d154447f5dbbcdeadbd706fcce0e55e19`.

## 6. Six-check gate remains unchanged

Require:

1. OKX current instrument semantics;
2. Bybit current instrument semantics;
3. OKX current trade timestamp schema;
4. Bybit current trade timestamp schema;
5. OKX exact historical archive metadata + HEAD;
6. Bybit exact historical archive HEAD.

## 7. Exact v0.3 terminal states

PASS:

`C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_PASS`

REVIEW:

`C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_REVIEW`

REVIEW remains source/engineering state only.

## 8. Firewalls remain unchanged

Must remain false:

- historical body download/open;
- cross-venue price comparison;
- cross-venue return;
- dislocation;
- lag;
- leader selection;
- strategy signal;
- PnL;
- promotional alpha.

## 9. Consequence of PASS

Only after exact v0.3 PASS may C8-D1 be designed to download and qualify the one-day historical trade bodies and synchronization semantics.

No cross-venue alpha outcome is authorized by D0.

## 10. Immediate next action

Run frozen C8-D0 v0.3 source/clock preflight on VPS.
