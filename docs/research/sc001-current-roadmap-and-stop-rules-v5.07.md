# SC001 Current Roadmap and Stop Rules v5.07

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B14-A V0.4 HTTP400 REVIEW / V0.5 QUALIFIED DAILY TRANSPORT FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.06.md`

## 1. B13-C protected collection

B13-C remains:

`B13C_COLLECTION_RUNNING`

Protected liquidation outcomes remain closed to strategy design.

## 2. B14-A v0.4 state

Observed:

`B14A_D0_V04_SOURCE_ARCHIVE_METADATA_REVIEW`

Product semantics passed:

- BTC-USD future contracts = 6;
- ETH-USD future contracts = 6;
- both inverse SWAP hedges = PASS.

Archive requests returned HTTP 400 before archive resolution.

No price outcome was opened.

## 3. Qualified transport correction

Previously passed SC001 metadata preflights use:

- `GET /api/v5/public/market-data-history`;
- `module=1`;
- exact `instIdList`;
- `dateAggrType=daily`;
- UTC day begin/end.

v0.4 used `1D`, which the live endpoint rejected.

## 4. v0.5 implementation

Protocol:

`docs/research/sc001-b14a-d0-dated-futures-source-archive-metadata-protocol-v0.4.md`

Runner:

`research/sc001/sc001_b14a_d0_dated_futures_source_archive_metadata_v0_5.py`

Freeze:

`docs/research/sc001-b14a-d0-implementation-freeze-v0.5.json`

## 5. Archive resolution

For probe label-day D:

1. query D with `dateAggrType=daily`;
2. if unresolved, query D-1 metadata window;
3. require one unique exact `INSTID-trades-D.zip`;
4. HEAD only.

## 6. Firewalls

No:

- archive body GET/open;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution;
- PnL;
- candidate ID.

## 7. Immediate next action

Run B14-A D0 v0.5 self-test.

If PASS, run metadata-only v0.5 once.
