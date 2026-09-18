# SC001 — C11-D0 Macro Calendar / Historical Trade Source Preflight v0.1

Date: 2026-09-18
Status: **FROZEN METADATA-ONLY / NO PRICE OUTCOME**
Scope: `SCALPING RESEARCH / SC001`

Parent:

`docs/research/sc001-c11-candidate-assignment-freeze-v0.1.md`

## 1. Purpose

Verify the two independent source contracts required before C11 outcome design:

1. official BLS scheduled-event metadata;
2. exact OKX BTC-USDT-SWAP historical daily trade archive availability.

No trade body is opened.

## 2. Representative event-source checks

Use exactly two representative events, one from each frozen C11 event family:

### CPI representative
- official BLS schedule page: `https://www.bls.gov/schedule/2025/01_sched_list.htm`
- date: `2025-01-15`
- release: `Consumer Price Index`
- scheduled time: `08:30 AM ET`
- frozen UTC timestamp: `2025-01-15T13:30:00Z`

### Employment representative
- official BLS schedule page: `https://www.bls.gov/schedule/2025/02_sched_list.htm`
- date: `2025-02-07`
- release: `Employment Situation`
- scheduled time: `08:30 AM ET`
- frozen UTC timestamp: `2025-02-07T13:30:00Z`

D0 may read schedule-page text only to verify event/date/time metadata.

D0 must not parse or use released macro values, surprises or revisions.

## 3. OKX current instrument semantics

Require current:

`BTC-USDT-SWAP`

with:

- instType=SWAP;
- ctType=linear;
- settleCcy=USDT;
- state=live.

## 4. Historical trade metadata

For each representative event date require exact archive metadata/HEAD only:

- `BTC-USDT-SWAP-trades-2025-01-15.zip`;
- `BTC-USDT-SWAP-trades-2025-02-07.zip`.

Use the already-qualified OKX historical trade resolver:

`POST /priapi/v5/broker/public/trade-data/download-link`

with module=1, instType=SWAP, instFamilyList=[BTC-USDT], exact daily bounds.

Require:

- unique exact trusted URL;
- HTTPS;
- static.okx.com host;
- HEAD 200;
- positive Content-Length.

No GET body.

## 5. Exact states

PASS:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS`

REVIEW:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_REVIEW`

## 6. Firewalls

Must remain false:

- historical_trade_body_downloaded;
- historical_trade_body_opened;
- macro_release_value_accessed;
- macro_surprise_calculated;
- post_release_move_calculated;
- direction_signal_calculated;
- pnl_calculated;
- promotional_alpha_accessed.

## 7. Consequence of PASS

Only after D0 PASS may C11 define and freeze:

- Selection/Calibration chronology;
- exact first-impulse rule;
- exact hold/max hold;
- structural burden;
- cheapest move-headroom sentinel.

No outcome is authorized by D0.
