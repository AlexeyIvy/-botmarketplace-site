# SC001 — B13-C S0 Bybit Price-Archive Availability & Schema Preflight v0.1

Date: 2026-09-26  
Status: **SOURCE METADATA PARTIAL PASS / CURRENT UTC DAY PENDING / NO PRICE OUTCOME**

## Frozen source

Official Bybit public historical trade archive:

`https://public.bybit.com/trading/SYMBOL/SYMBOLYYYY-MM-DD.csv.gz`

Frozen S0 symbols:

BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, ORDIUSDT, FILUSDT, UNIUSDT, XRPUSDT, LTCUSDT, OPUSDT, BCHUSDT, SUIUSDT.

Frozen protected event interval:

`2026-09-19T06:47:38.969Z .. 2026-09-26T21:05:32.973Z`

## Availability observed on 2026-09-26

Direct official directory listings were inspected for all 12 frozen symbols.

Observed for every symbol:
- 2026-09-19 archive = present;
- every daily archive through 2026-09-25 = present;
- 2026-09-26 archive = not yet present while the UTC day is still in progress.

Therefore:
- available frozen-calendar files through Sep25 = 12 x 7 = 84;
- total naive full-interval files = 12 x 8 = 96;
- currently pending = 12 Sep26 files.

This is a source-publication timing state, not an S0 strategy result.

## Schema qualification

SC001 has already qualified the Bybit public-trade archive body/schema in the prior C8 engineering branch.

Binding reusable Bybit semantics:
- gzip CSV;
- first five semantic columns:
  1. `timestamp`
  2. `symbol`
  3. `side`
  4. `size`
  5. `price`
- timestamp is Unix seconds with fractional precision and is normalized to integer microseconds;
- side must be `Buy` or `Sell`;
- size and price finite and >0;
- timestamp order must be nondecreasing.

B13-C S0 must reuse these semantics rather than invent a new parser.

## Acquisition optimization before price access

Do not download all 96 files blindly.

Because the S0 liquidation-cluster rule is already frozen, an outcome-free source-only cluster census may first enumerate the exact symbol-date archive files touched by eligible clusters.

This does not:
- change the 12-symbol universe;
- inspect price;
- inspect return;
- rank symbols;
- select a size threshold;
- tune the cluster rule.

Only the exact archive files required by frozen eligible clusters, including any UTC boundary-crossing entry/exit bucket, need to be body-downloaded and hashed.

## Current disposition

`B13C_S0_ARCHIVE_SOURCE_PARTIAL_PASS_CURRENT_DAY_PENDING`

Next:
1. run source-only cluster census;
2. freeze exact required archive identities;
3. wait for any required Sep26 archive(s) to publish;
4. HEAD/size + download/hash + body/schema qualification;
5. only then open the frozen S0 price outcome.
