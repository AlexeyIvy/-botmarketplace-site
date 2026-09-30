# SC001 — Forced-Flow S0 Input Provenance / Materialization Protocol v0.1

Date: 2026-09-30
Status: FROZEN DESIGN / NO REAL INPUT MATERIALIZATION AUTHORIZED
Task ID: SC001-NEXT-PRIMARY-PREFREEZE-01
Family: VENUE_LOCAL_FORCED_FLOW_RELATIVE_DISLOCATION
Authority: Strategy Manager Option A — PRIMARY-PIPELINE ENGINEERING ONLY

## Purpose

Define the exact deterministic input scope that may be materialized only after the frozen seven-day window closes and after separate Strategy/User authorization.

This protocol itself opens no fresh-window price/trade body and performs no S0 outcome.

## Frozen event window

Liquidation-event eligibility window:

2026-09-30T00:00:00Z <= liquidation/event time < 2026-10-07T00:00:00Z.

Frozen UTC dates:
- 2026-09-30
- 2026-10-01
- 2026-10-02
- 2026-10-03
- 2026-10-04
- 2026-10-05
- 2026-10-06

## Frozen liquidation/source inputs

Read-only inputs from the existing B13-C collector:

- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/collector_state.json
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/connection/connection_events.jsonl
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/2026-09-30.jsonl
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/2026-10-01.jsonl
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/2026-10-02.jsonl
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/2026-10-03.jsonl
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/2026-10-04.jsonl
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/2026-10-05.jsonl
- SC001_B13C_PROSPECTIVE_LIQUIDATIONS/events/2026-10-06.jsonl

No raw liquidation message body is required by the S0 materialization path unless a separately authorized integrity audit is needed.

Every materialized file must be recorded with:
- logical source path;
- exact byte count;
- SHA256;
- file role;
- materialization timestamp;
- immutable source identity.

## Frozen price-trade source scope

Venues:
- Bybit linear USDT perpetual public historical trades;
- OKX same-underlying USDT perpetual/swap public historical trades.

Frozen bases:
BTC, ETH, SOL, DOGE, ORDI, FIL, UNI, XRP, LTC, OP, BCH, SUI.

### Deterministic calendar coverage

Trade bodies required for the S0 clock are not limited to the seven event dates.

Require trade archives for:

2026-09-29 through 2026-10-07 inclusive.

Reason:
- 2026-09-29 supplies the causal prior-300-second baseline for eligible events near the opening boundary on 2026-09-30;
- 2026-10-07 supplies the +1s/<+2s observation bucket for eligible clusters ending immediately before 2026-10-07T00:00:00Z;
- all dates in between cover the exact seven-day event window.

This nine-calendar-date trade-body scope is fixed mechanically from the frozen S0 chronology and is not selected from outcomes.

Expected Bybit identity pattern:
{SYMBOL}USDT{YYYY-MM-DD}.csv.gz
under:
https://public.bybit.com/trading/{SYMBOL}USDT/

Expected OKX identity pattern:
{BASE}-USDT-SWAP-trades-{YYYY-MM-DD}.zip
resolved only through the official OKX historical-data metadata service and trusted static host.

No alternate date, symbol, venue, third-party mirror or nearest-file substitution.

## Source identity requirements

Before any body materialization:
- exact expected basename;
- trusted official host;
- positive Content-Length from frozen metadata qualification or recheck;
- HTTPS;
- no redirect to an untrusted host.

After body materialization:
- record exact compressed byte count;
- SHA256;
- archive member inventory;
- archive integrity/CRC where applicable;
- exact parser/schema qualification;
- no source row may be silently repaired using outcome information.

## Derived-input contract

Only after separately authorized body materialization may deterministic derived files be produced:

1. liquidation cluster file;
2. merged source-gap ledger;
3. Bybit last-valid-trade-per-second file;
4. OKX last-valid-trade-per-second file;
5. strict-coactive intersection file;
6. exact S0 analyzer input manifest.

Every derived artifact must record:
- parent SHA256 list;
- deterministic generator path/blob or SHA256;
- generation parameters fixed by S0 v0.2;
- output SHA256;
- row count;
- min/max timestamps;
- frozen symbol/date scope.

## Cluster semantics

Unchanged:
- per symbol;
- deterministic fingerprints;
- duplicate policy KEEP_EARLIEST_RECEIVED_COPY;
- inter-event gap <=5000 ms;
- >=3 distinct events;
- pure liquidation side;
- source-gap censor +/-5000 ms;
- no liquidation size threshold.

No cluster may be silently rescued after source-gap censoring.

## Outcome firewall

This protocol does not authorize:
- archive-body GET;
- trade-row reading;
- fresh-window price access;
- raw_basis_bps calculation;
- relative_dev_bps;
- forced_flow_dislocation_bps;
- returns;
- PnL;
- S0 execution;
- Candidate 2/3 outcome access.

## Post-window sequence

After 2026-10-07T00:00:00Z:

1. complete full-window gap/completeness readout;
2. run/confirm exact archive metadata qualification for required final dates;
3. freeze a materialization manifest containing exact source identities;
4. obtain explicit Strategy/User authorization;
5. materialize exact bodies once;
6. hash/validate them;
7. generate deterministic derived inputs;
8. create exact S0_EXECUTION_AUTHORIZED record bound to all input hashes;
9. only then may the frozen analyzer read real S0 inputs.

No outcome inspection is permitted between steps 1-8.
