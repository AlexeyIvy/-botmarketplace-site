# SC001 — C8-D0 OKX/Bybit Source & Clock Semantics Protocol v0.3

Date: 2026-09-18
Status: **FROZEN OKX HISTORICAL-DISCOVERY TRANSPORT REPAIR AFTER v0.2 REVIEW / NO ALPHA**
Scope: `SCALPING RESEARCH / SC001`
Supersedes: `sc001-c8-d0-okx-bybit-source-clock-semantics-protocol-v0.2.md`

## 1. Trigger

C8-D0 v0.2 returned:

`C8_D0_V02_SOURCE_CLOCK_PREFLIGHT_REVIEW`

with `5/6` checks passed.

Only unresolved check:

`OKX historical daily trade archive exact filename`

Both public GET metadata windows failed to resolve:

`BTC-USDT-SWAP-trades-2025-01-15.zip`

No historical body, cross-venue price, return, dislocation, lag, signal or PnL was opened.

## 2. Repair basis

SC001 Q005R previously established a working historical daily-trade discovery contract on the OKX historical-data service:

`POST /priapi/v5/broker/public/trade-data/download-link`

with:

- `module=1`;
- `instType=SWAP`;
- `instQueryParam.instFamilyList=["BTC-USDT"]`;
- `dateQuery.dateAggrType="daily"`;
- exact UTC date bounds.

Therefore v0.3 changes only the OKX historical archive metadata transport.

It does not change:

- venue pair;
- instrument pair;
- fixed qualification date;
- archive filename;
- Bybit source;
- current API timestamp semantics;
- body firewall;
- any C8 economic hypothesis.

## 3. Frozen OKX historical resolver

Domains in order:

- `https://www.okx.com`;
- `https://us.okx.com`.

Endpoint:

`POST /priapi/v5/broker/public/trade-data/download-link`

Referer:

`https://www.okx.com/historical-data`

Payload:

`module = "1"`

`instType = "SWAP"`

`instQueryParam.instFamilyList = ["BTC-USDT"]`

`dateQuery.dateAggrType = "daily"`

`dateQuery.begin = 2025-01-15T00:00:00.000Z`

`dateQuery.end = 2025-01-15T23:59:59.999Z`

Exact accepted filename only:

`BTC-USDT-SWAP-trades-2025-01-15.zip`

Trusted URL rule:

- HTTPS;
- static OKX historical host;
- basename exact.

After URL de-duplication require exactly one exact trusted URL.

Then HEAD only.

## 4. Remaining six-check gate

Require:

1. OKX instrument semantics PASS;
2. Bybit instrument semantics PASS;
3. OKX current trade timestamp schema PASS;
4. Bybit current trade timestamp schema PASS;
5. OKX exact historical archive via frozen priapi resolver + HEAD PASS;
6. Bybit exact historical archive HEAD PASS.

## 5. Historical archive body firewall

D0 v0.3 must not:

- GET the OKX historical ZIP;
- GET the Bybit historical GZIP;
- open/parse either historical body;
- compare historical prices or timestamps across venues.

## 6. Exact terminal states

PASS:

`C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_PASS`

REVIEW:

`C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_REVIEW`

REVIEW remains a source/engineering state only.

## 7. Firewalls

Must remain false:

- historical_archive_body_downloaded;
- historical_archive_body_opened;
- cross_venue_price_compared;
- cross_venue_return_calculated;
- dislocation_calculated;
- lag_calculated;
- leader_selected;
- strategy_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 8. Consequence of PASS

D0 v0.3 PASS authorizes only C8-D1 historical body/schema/clock synchronization design.

No cross-venue alpha outcome is authorized.
