# SC001 — C8-D0 OKX/Bybit Cross-Venue Source & Clock Semantics Protocol v0.1

Date: 2026-09-18
Status: **FROZEN NO-ALPHA SOURCE/CLOCK PREFLIGHT BEFORE ANY CROSS-VENUE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-c8-cross-venue-data-clock-audit-plan-v0.1.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v4.42.md`;
- `docs/research/sc001-data-acquisition-protocol-v0.1.md`.

## 1. Purpose

Verify that OKX and Bybit can support a causal same-asset cross-venue study before opening any cross-venue dislocation outcome.

C8-D0 is source/data semantics only.

It must not calculate:

- cross-venue return;
- price spread/dislocation;
- lead/lag;
- venue leadership;
- strategy direction;
- signal;
- PnL.

## 2. Frozen venue pair and instrument pair

Venue pair:

- OKX;
- Bybit.

Engineering instrument pair:

- OKX `BTC-USDT-SWAP`;
- Bybit `BTCUSDT` linear perpetual.

BTC is used only for source/clock qualification because both venues have long public history and BTC was already used in prior SC001 data qualification.

D0 does not choose a final C8 trading universe.

## 3. Fixed historical qualification date

Exact date:

`2025-01-15 UTC`

This is the pre-existing SC001 Q001/Q002 data-qualification date.

No C8 alpha has been inspected on this date.

## 4. Current instrument semantics checks

### OKX

Public endpoint:

`GET /api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP`

Require:

- instId exact;
- instType = SWAP;
- ctType = linear;
- settleCcy = USDT;
- underlying/family corresponds to BTC-USDT;
- state = live or equivalent current tradable state.

### Bybit

Public endpoint:

`GET /v5/market/instruments-info?category=linear&symbol=BTCUSDT`

Require:

- symbol exact;
- contractType = LinearPerpetual;
- baseCoin = BTC;
- quoteCoin = USDT;
- settleCoin = USDT;
- current status indicates tradable/Trading.

Current metadata verifies product mapping only. It is not historical contract-spec evidence.

## 5. Current public trade timestamp semantics

### OKX

Use:

`GET /api/v5/market/history-trades?instId=BTC-USDT-SWAP&type=2&limit=10`

Require each returned row to expose:

- instId;
- tradeId;
- side;
- px;
- sz;
- ts.

Require `ts` parse as Unix milliseconds.

### Bybit

Use:

`GET /v5/market/recent-trade?category=linear&symbol=BTCUSDT&limit=10`

Require each returned row to expose:

- execId;
- symbol;
- price;
- size;
- side;
- time.

Require `time` parse as Unix milliseconds.

These current APIs establish current field/timestamp contracts only.

## 6. Historical archive identity

### OKX

Historical public source:

`GET /api/v5/public/market-data-history`

Frozen query:

- module = `1` (trade history);
- instType = `SWAP`;
- dateAggrType = `daily`;
- begin/end = fixed 2025-01-15 UTC day;
- instIdList = `BTC-USDT-SWAP`.

Require exact trusted filename:

`BTC-USDT-SWAP-trades-2025-01-15.zip`

Trusted historical host:

`static.okx.com`

Use HEAD only.

### Bybit

Official public trade archive identity:

`https://public.bybit.com/trading/BTCUSDT/BTCUSDT2025-01-15.csv.gz`

Require:

- HTTPS;
- final host = `public.bybit.com`;
- exact basename;
- HTTP 200;
- positive Content-Length.

Use HEAD only.

## 7. Archive body firewall

C8-D0 must not:

- GET the OKX historical trade ZIP;
- GET the Bybit historical trade GZIP;
- parse historical trade rows;
- compare cross-venue prices;
- calculate any timestamp offset from historical bodies.

Historical body/clock synchronization belongs to a separately frozen C8-D1 stage.

## 8. D0 PASS semantics

Exact PASS:

`C8_D0_SOURCE_CLOCK_PREFLIGHT_PASS`

PASS requires:

1. OKX current instrument semantics pass;
2. Bybit current instrument semantics pass;
3. OKX current public trade timestamp schema pass;
4. Bybit current public trade timestamp schema pass;
5. OKX exact historical archive metadata/HEAD pass;
6. Bybit exact historical archive HEAD pass;
7. no historical archive body opened.

REVIEW:

`C8_D0_SOURCE_CLOCK_PREFLIGHT_REVIEW`

REVIEW is a source/engineering state only, not a C8 strategy verdict.

## 9. Report firewalls

Must state:

- historical_archive_body_downloaded = false;
- historical_archive_body_opened = false;
- cross_venue_price_compared = false;
- cross_venue_return_calculated = false;
- dislocation_calculated = false;
- lag_calculated = false;
- leader_selected = false;
- strategy_signal_calculated = false;
- pnl_calculated = false;
- promotional_alpha_accessed = false.

## 10. Consequence of PASS

D0 PASS authorizes only C8-D1:

- download exact one-day historical trade bodies for the same fixed date;
- validate each archive schema/timestamp unit/order;
- define one deterministic causal synchronization rule;
- run synthetic/golden clock tests.

No cross-venue price/dislocation outcome is authorized until D1 clock semantics are frozen and pass.
