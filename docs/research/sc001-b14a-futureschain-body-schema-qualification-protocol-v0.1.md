# SC001 — B14-A FUTURES-Chain Body / Schema Qualification Protocol v0.1

Date: 2026-09-19
Status: **FROZEN ENGINEERING SOURCE QUALIFICATION / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-b14a-exact-12-future-expiry-identity-freeze-v0.1.json`;
- `docs/research/sc001-contamination-registry-v0.27.json`;
- `docs/research/sc001-b14a-d0-v0.8-source-archive-metadata-pass-result.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Purpose

Qualify the internal schema of OKX family-level FUTURES chain archives and prove that rows can be attributed to exact dated FUTURES contract IDs before any B14-A price/basis research.

This is engineering/source work only.

## 2. Canonical D0 identity

Canonical local report:

`~/sc001_data/SC001_B14A_D0_SOURCE_ARCHIVE/sc001_b14a_d0_source_archive_metadata_v0_8.json`

Required SHA256:

`a7a36245ee668450960873e22f0ce515c95e6c990564fa8df4fedf97d6fbd5e8`

Required D0 status:

`B14A_D0_V08_SOURCE_ARCHIVE_METADATA_PASS`

## 3. Authorized bodies

Exactly two archives for UTC 2026-09-16:

- `BTC-USD-futureschain-trades-2026-09-16.zip`;
- `ETH-USD-futureschain-trades-2026-09-16.zip`.

Before download/open:

- re-resolve exact metadata identity;
- trusted host = `static.okx.com`;
- exact basename;
- re-HEAD positive Content-Length;
- HEAD size must equal the canonical D0 report size.

No other date or family may be opened.

## 4. ZIP integrity

For each archive require:

- valid ZIP;
- CRC test PASS;
- >=1 regular CSV member;
- no non-CSV regular member.

Do not infer prices or outcomes from file size.

## 5. Allowed CSV schema

Accept exactly one of:

### LEGACY_6

`instrument_name,trade_id,side,price,size,created_time`

### SOURCE_7

`instrument_name,trade_id,side,price,size,created_time,source`

Optional UTF-8 BOM on the first header token is allowed and normalized.

Any other header:

`B14A_CHAIN_SCHEMA_REVIEW`

No permissive fallback.

## 6. Restricted row parsing

For data rows, the qualifier may parse only the first field:

`instrument_name`

The remainder of the row is not parsed into price/size/time values.

Allowed source diagnostics:

- total non-empty row count;
- distinct `instrument_name` values;
- family-prefix validity;
- exact dated-contract suffix syntax;
- target-nearest contract presence.

No per-contract liquidity ranking.

No price values are parsed, stored, printed or compared.

## 7. Contract attribution rules

For BTC family every parsed `instrument_name` must match:

`BTC-USD-[0-9]{6}`

For ETH family:

`ETH-USD-[0-9]{6}`

Require for each family:

- >=1 data row;
- >=2 distinct exact contract IDs;
- nearest frozen contract for 2026-09-25 present:
  - `BTC-USD-260925`;
  - `ETH-USD-260925`;
- every distinct ID belongs to the same family pattern.

Historical archive may contain a contract already expired by 2026-09-19; therefore not every observed ID must belong to the frozen future-12 set.

## 8. PASS

Exact PASS:

`B14A_FUTURESCHAIN_BODY_SCHEMA_PASS`

requires both family archives to pass:

- metadata/HEAD identity;
- size equality to canonical D0;
- ZIP/CSV integrity;
- accepted header;
- exact row-level contract attribution.

Otherwise:

`B14A_FUTURESCHAIN_BODY_SCHEMA_REVIEW`

## 9. Firewalls

This stage may set:

- futureschain_body_downloaded = true;
- futureschain_body_opened = true;
- header_schema_accessed = true;
- instrument_name_accessed = true.

It must keep false:

- price_values_parsed_or_stored;
- price_outcome_calculated;
- basis_calculated;
- return_calculated;
- settlePx_accessed;
- delivery_price_accessed;
- convergence_calculated;
- strategy_signal_calculated;
- execution_model_calculated;
- pnl_calculated;
- candidate_id_assigned;
- promotional_alpha_accessed.

## 10. Consequence

PASS authorizes only:

1. a B14-A Edge-to-Fill structural card;
2. later price-bearing headroom protocol design under a new contamination freeze.

It does not authorize basis/convergence/PnL by itself.
