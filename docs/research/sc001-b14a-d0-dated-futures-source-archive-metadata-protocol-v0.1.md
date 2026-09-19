# SC001 — B14-A D0 Dated-Futures Contract / Archive Metadata Protocol v0.1

Date: 2026-09-19
Status: **FROZEN METADATA-ONLY / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-b14a-okx-dated-futures-source-settlement-spec-audit-v0.1.md`

## 1. Exact scope

Venue:

`OKX`

Families:

- `BTC-USDT`;
- `ETH-USDT`.

FUTURES admission:

- `ruleType=normal`;
- `instCategory=1`;
- `ctType=linear`;
- `settleCcy=USDT`;
- state in {`live`, `preopen`};
- positive listTime;
- positive future expTime.

Exclude pre-market/X-Perp/non-crypto.

## 2. Future expiry census

Enumerate every currently returned eligible standard FUTURES contract with:

`expTime > D0 run time`

Record:

- instId;
- instFamily;
- listTime;
- expTime;
- state;
- ruleType;
- futureSettlement;
- ctVal;
- ctMult;
- ctValCcy;
- settleCcy;
- ctType;
- instCategory;
- groupId.

No price fields.

## 3. Contract semantic gates

Require for each admitted contract:

- exact family;
- linear;
- USDT settlement;
- crypto category;
- normal rule type;
- non-empty contract value fields;
- expTime > listTime.

## 4. SWAP hedge identity

For both families verify exact:

- BTC-USDT-SWAP;
- ETH-USDT-SWAP;

with:

- instType SWAP;
- ctType linear;
- settleCcy USDT;
- instCategory 1;
- state live.

No price access.

## 5. Historical FUTURES archive metadata probe

For each eligible FUTURES contract already live for at least one completed UTC day:

choose deterministically:

`probe_date = min(yesterday_UTC, calendar day immediately before D0 run)`

but require probe_date >= UTC date of listTime.

If an eligible contract has not completed one full UTC trading day yet, mark:

`ARCHIVE_PROBE_NOT_YET_ELIGIBLE`

and do not substitute another date.

For probe-eligible contracts, resolve exact:

`INSTID-trades-YYYY-MM-DD.zip`

through official OKX historical market-data trade module.

Require:

- exact filename;
- HTTPS;
- static.okx.com;
- HEAD 200;
- positive Content-Length.

No body GET/open.

## 6. D0 PASS

Exact PASS:

`B14A_D0_SOURCE_ARCHIVE_METADATA_PASS`

requires:

- >=2 eligible future standard FUTURES contracts per family;
- both SWAP hedge identities PASS;
- >=1 FUTURES archive metadata/HEAD PASS per family;
- all semantic fields valid.

If source semantics are valid but archive-probe breadth is insufficient:

`B14A_D0_SOURCE_ARCHIVE_METADATA_REVIEW`

This is source state only.

## 7. Firewalls

Must remain false:

- futures_trade_body_downloaded;
- futures_trade_body_opened;
- swap_trade_body_opened;
- price_accessed;
- basis_calculated;
- estimated_settlement_price_accessed;
- delivery_price_accessed;
- convergence_calculated;
- strategy_signal_calculated;
- execution_model_calculated;
- pnl_calculated;
- candidate_id_assigned.

## 8. Consequence of PASS

PASS authorizes only:

- exact future expiry identity freeze;
- Edge-to-Fill structural card;
- later nonpromotional/prospective headroom protocol design.

No price outcome.
