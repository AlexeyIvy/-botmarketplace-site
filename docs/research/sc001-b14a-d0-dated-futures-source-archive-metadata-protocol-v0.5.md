# SC001 — B14-A D0 Dated-Futures Source / Archive Metadata Protocol v0.5

Date: 2026-09-19
Status: **FROZEN FUTURES-FAMILY SELECTOR + T+2 AVAILABILITY AMENDMENT / METADATA-ONLY**
Scope: `SCALPING RESEARCH / SC001`
Supersedes archive-transport semantics from v0.4 only.

Parents:

- `docs/research/sc001-b14a-d0-v0.5-futures-selector-availability-review-v0.1.md`;
- `docs/research/sc001-b14a-d0-v0.1-source-review-result.md`;
- `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`.

## 1. Product scope

Unchanged:

- BTC-USD standard crypto-margined inverse expiry futures;
- ETH-USD standard crypto-margined inverse expiry futures.

Hedges:

- BTC-USD-SWAP;
- ETH-USD-SWAP.

## 2. Historical metadata query

Use:

`GET /api/v5/public/market-data-history`

with:

- module = `1`;
- instType = `FUTURES`;
- instFamilyList = exact family;
- dateAggrType = `daily`;
- begin/end = exact metadata query-day window.

Do not use `instIdList` for FUTURES.

## 3. Probe date

Freeze source-feasibility lag:

`probe_date = current UTC calendar date - 3 days`

Rationale:

historical module 1 is normally T+2; D−3 provides one full extra day of publication margin.

This is source availability, not strategy timing.

## 4. Representative contract

Per family choose exactly one contract for archive transport qualification:

- currently eligible/live;
- listTime < probe-date UTC start;
- earliest future expTime among eligible contracts.

Do not choose by liquidity, spread, basis or return.

## 5. Metadata windows

For expected archive label D:

1. query D metadata window;
2. if unresolved, query D−1 metadata window;
3. recursively inspect returned family metadata;
4. accept only exact filename:
   `INSTID-trades-D.zip`.

## 6. Trust gate

Require:

- exactly one trusted URL;
- HTTPS;
- host `static.okx.com`;
- exact basename;
- HEAD 200;
- positive numeric Content-Length.

No body GET/open.

## 7. Contract census gates

Still require:

- >=2 future eligible BTC-USD contracts;
- >=2 future eligible ETH-USD contracts;
- both inverse SWAP hedges PASS.

Archive transport gate becomes:

- representative BTC FUTURES archive metadata/HEAD PASS;
- representative ETH FUTURES archive metadata/HEAD PASS.

## 8. PASS

`B14A_D0_V06_SOURCE_ARCHIVE_METADATA_PASS`

Otherwise:

`B14A_D0_V06_SOURCE_ARCHIVE_METADATA_REVIEW`

## 9. Firewalls

Remain false:

- trade body download/open;
- price;
- basis;
- settlePx;
- delivery price;
- convergence;
- execution/PnL;
- candidate-ID assignment.
