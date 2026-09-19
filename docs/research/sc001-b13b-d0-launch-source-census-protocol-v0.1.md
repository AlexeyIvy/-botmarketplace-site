# SC001 — B13-B D0 Launch-Event Source Census Preflight v0.1

Date: 2026-09-19
Status: **FROZEN SOURCE-ONLY / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parents:

- `docs/research/sc001-current-roadmap-and-stop-rules-v4.87.md`;
- `docs/research/sc001-post-c11-independent-base-opportunity-pool-v0.1.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`.

## 1. Purpose

Test whether B13-B has a reproducible launch-event source universe before opening any price outcome.

No C13/C14 ID is assigned.

## 2. Mechanism boundary

B13-B concerns:

`scheduled new OKX USDT perpetual launch -> relative price discovery versus a mature pre-existing Bybit same-underlying perpetual`

This is not ordinary continuous-market cross-venue basis.

## 3. Frozen census window

OKX launch timestamp:

`2026-01-01 00:00 UTC <= listTime < 2026-09-01 00:00 UTC`

September 2026 is excluded because it is incomplete at freeze time.

## 4. OKX source

Use:

`GET /api/v5/public/instruments?instType=SWAP`

Admit only current rows satisfying:

- state = `live`;
- settleCcy = `USDT`;
- ctType = `linear`;
- instId exact pattern `BASE-USDT-SWAP`;
- finite positive `listTime` inside the frozen window.

The OKX API documentation defines `listTime` as instrument listing/continuous-trading start time for ordinary SWAP listings.

## 5. Bybit reference source

Use:

`GET /v5/market/instruments-info?category=linear`

with cursor pagination.

Exact reference:

`BASEUSDT`

Require:

- contractType = `LinearPerpetual`;
- quoteCoin = `USDT`;
- positive launchTime;
- Bybit launchTime <= OKX listTime - 90 days.

No alternate reference venue is substituted.

## 6. Historical launch-day source availability

For each source-eligible event, verify metadata/HEAD only.

### OKX

Resolve exact launch-day:

`BASE-USDT-SWAP-trades-YYYY-MM-DD.zip`

through official historical market-data module 1, daily aggregation.

Require trusted `static.okx.com` exact basename and positive HEAD Content-Length.

### Bybit

HEAD exact public archive:

`https://public.bybit.com/trading/BASEUSDT/BASEUSDTYYYY-MM-DD.csv.gz`

Require HTTP 200 and positive Content-Length.

No archive body GET/open.

## 7. Survivor-census limitation

This D0 uses current public instrument catalogs.

Delisted historical contracts may be absent.

Therefore every result must state:

`historical_launch_universe_complete = false`

unless a later independent official-announcement census proves completeness.

D0 cannot promote a price/headroom sentinel by itself.

## 8. Source-feasibility PASS

Exact:

`B13B_D0_SOURCE_FEASIBILITY_PASS_SURVIVOR_CENSORED`

requires:

- >=6 OKX launches with mature Bybit reference;
- >=3 distinct OKX launch calendar months;
- >=5 events with launch-day historical source metadata available on both venues;
- no event selected by price behavior.

Otherwise:

`B13B_D0_SOURCE_FEASIBILITY_REVIEW`

This is not a strategy verdict.

## 9. Required report

Per event:

- base symbol;
- OKX instId;
- OKX listTime;
- Bybit symbol;
- Bybit launchTime;
- reference age days;
- OKX archive metadata/HEAD PASS;
- Bybit archive HEAD PASS.

Aggregate:

- raw OKX launches in window;
- mature-reference launches;
- dual-source-ready launches;
- month breadth;
- explicit survivor-census flag.

## 10. Firewalls

Must remain false:

- historical_trade_body_downloaded;
- historical_trade_body_opened;
- price_accessed;
- relative_basis_calculated;
- launch_dislocation_calculated;
- strategy_signal_calculated;
- execution_model_calculated;
- pnl_calculated;
- candidate_id_assigned;
- promotional_alpha_accessed.

## 11. Consequence

PASS only establishes source feasibility under a survivor-censored census.

Before any launch-dislocation price outcome, perform a separate completeness/governance review and freeze the event set/headroom sentinel.
