# SC001 Current Roadmap and Stop Rules v4.49

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8-D1E CLOCK PASS / C8-D2 PRICE-CALIBRATION METADATA PREFLIGHT FROZEN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.48.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 still has no strategy verdict.

## 2. C8-D1E result

Exact:

`C8_D1E_STRICT_COACTIVE_1S_PASS`

Observed:

- OKX active seconds: 80,640;
- Bybit active seconds: 77,076;
- joint coactive seconds: 72,539;
- joint coactive share: about 0.83957;
- minimum joint-active seconds in any UTC hour: 2,378;
- median last-event skew: 150.5 ms;
- p99 last-event skew: 846.7 ms;
- failed gates: none;
- no price/return/dislocation/lag;
- no signal/PnL/promotional alpha.

Binding result:

`docs/research/sc001-c8-d1e-strict-coactive-1s-pass-result-v0.1.md`

## 3. Qualified C8 temporal representation

The only currently qualified cross-venue temporal representation is:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

The prior carry-forward architecture remains not qualified.

## 4. 2025-01-15 evidence role

The 2025-01-15 bodies remain:

`NONPROMOTIONAL_ENGINEERING_CLOCK_CALIBRATION`

They must not be reused as clean C8 price/dislocation Selection evidence.

## 5. Next C8 price-calibration date selected prospectively

Freeze:

`2025-01-20 UTC`

Selection rule:

`first Monday after 2025-01-15 engineering clock-qualification day`

This calendar rule was fixed before any cross-venue price outcome on that date.

## 6. C8-D2 is metadata-only

Before contaminating/opening 2025-01-20 price bodies, D2 verifies exact archive existence and byte sizes only.

Required exact files:

- OKX `BTC-USDT-SWAP-trades-2025-01-20.zip`;
- OKX `BTC-USDT-SWAP-trades-2025-01-21.zip` as D+1 stitch source;
- Bybit `BTCUSDT2025-01-20.csv.gz`.

No body GET/open is authorized.

## 7. C8-D2 frozen implementation

Protocol:

`docs/research/sc001-c8-d2-price-calibration-metadata-preflight-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c8_d2_price_calibration_metadata_preflight_v0_1.py`

Freeze:

`docs/research/sc001-c8-d2-implementation-freeze-v0.1.json`

Frozen identities:

- D1E result: `4c10544ae88c043da3705299d8e1a1e0d51de68e`;
- protocol: `56e90fc4eb640dc26520ef435ae6f67894a85379`;
- runner: `b08cf7cb466904565fd2389f5a4a8d7b3b5d9f0a`.

## 8. Exact D2 states

PASS:

`C8_D2_PRICE_CALIBRATION_METADATA_PASS`

REVIEW:

`C8_D2_PRICE_CALIBRATION_METADATA_REVIEW`

REVIEW is source/data availability only.

## 9. D2 firewalls

Must remain false:

- historical archive body download/open;
- cross-venue price comparison;
- cross-venue return;
- raw spread;
- dislocation;
- lag;
- strategy signal;
- PnL;
- promotional alpha.

## 10. Consequence of D2 PASS

Only after exact PASS:

1. update contamination registry before body access;
2. classify 2025-01-20 C8 price channel as nonpromotional Selection/Calibration;
3. freeze the within-second price statistic;
4. freeze a raw structural headroom sentinel before any price comparison;
5. only then open/download the three bodies.

## 11. Immediate next action

Run frozen C8-D2 metadata-only preflight on VPS.
