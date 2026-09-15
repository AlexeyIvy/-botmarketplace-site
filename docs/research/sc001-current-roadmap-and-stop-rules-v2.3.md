# SC001 Current Roadmap and Stop Rules v2.3

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.2.md`

## 1. Terminal history unchanged

- E001: terminal `FAIL`; no rescue tuning.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`; TFI retained only as future auxiliary knowledge.
- E003: terminal `E003_DISCOVERY_FAIL`; no Confirmation/L2/rescue.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only postmortem complete.
- E005: remains closed because viable-E004 prerequisite failed.
- E006: terminal `E006_DISCOVERY_FAIL`; classified event-scarcity + insufficient economics headroom; no Confirmation/L2/rescue.

SC001 remains independent from R009-E002, R003-E003 Binance, R003-X003 Bybit, R010-E001 and Safe-Sleeve S002. Q2 / formal Validation / Final remain closed.

## 2. Active candidate: SC001-E007

Mechanism:

**extreme short-horizon BTC-USDT-SWAP displacement -> partial mean reversion.**

E007 is a new experiment family, not a rescue of E001-E006.

No E007 alpha has yet been authorized or observed.

## 3. Frozen E007 executable protocol

Canonical protocol:

`docs/research/sc001-e007-extreme-displacement-mean-reversion-executable-protocol-v1.0.md`

Primary identifier:

`E007_REV_G5_W60_T80_R50_LAT500_H10_CAP4`

Frozen mechanism:

- 5-second causal size-weighted VWAP;
- current `[t-5s,t)` versus anchor `[t-65s,t-60s)`;
- 60-second displacement;
- absolute threshold `80 bps`;
- trigger only on crossing from `|D| < 80` to `|D| >= 80`;
- reversal only, both signs;
- frozen arithmetic 50% retracement target;
- primary latency 500 ms, 5-second proxy tolerance;
- max hold 10 minutes;
- one position, 10-minute cooldown, max four decisions/day;
- latest entry decision 23:49 UTC;
- 1,000/2,000 ms execution-latency stresses;
- no E007 diagnostic grid.

## 4. Economics-first Discovery hurdle

All gates must pass:

- completed trades 20..80;
- active days >=10;
- completion >=95%;
- pooled mean >=30 bps;
- 10% trimmed mean >=25 bps;
- median >=20 bps;
- median active-day mean >=25 bps;
- positive active-day share >=70%;
- day-block bootstrap 95% LCB >15 bps;
- top-day concentration limits;
- >=5 completed LONG and >=5 SHORT reversals;
- max one-sign share <=80%;
- 1,000 ms mean >=25 / trimmed >=20 bps;
- 2,000 ms mean >=20 / trimmed >=15 bps;
- daily cap and one-position invariants.

Any one failure is terminal `E007_DISCOVERY_FAIL`.

## 5. Chronology

Discovery performance: 2024-03-01..20.

March 21: D+1 boundary-neighbor only, performance-excluded.

Only if Discovery PASSes all gates may one unchanged Confirmation use performance dates 2024-03-22..30, with March 21 warm-up/boundary-only and March 31 D+1 reconstruction only.

## 6. Current hard gate: implementation preflight

Frozen preflight spec:

`docs/research/sc001-e007-implementation-preflight-spec-v1.0.md`

Frozen implementation:

`docs/research/sc001-e007-implementation-freeze-v1.0.md`

Executable set:

- `research/sc001/sc001_e007_config_v1_0.json`;
- `research/sc001/sc001_e007_extreme_reversal_v1.py`;
- `research/sc001/sc001_e007_preflight_v1_0.py`.

Development-side synthetic/state-machine audit passed `38/38` checks. This is not the authoritative VPS result.

Only exact terminal token:

`E007_PREFLIGHT_PASS`

with matching engine/config SHA256 authorizes one DEV-DISCOVERY run.

## 7. Preflight firewall

Real-data preflight may inspect only source identities, timestamp chronology, 5-second bucket presence, current/anchor structural availability and resources.

It must not calculate real:

- VWAP values;
- 60-second displacements;
- E007 triggers;
- entry/exit returns;
- P&L/alpha.

## 8. Stop rules

If preflight fails:

- do not run Discovery;
- fix only implementation/data-audit defects;
- do not change 80 bps threshold, 60-second window, 50% retracement, latency, hold or economics gates.

If Discovery later fails:

- terminal E007 FAIL;
- do not lower threshold;
- do not switch to continuation;
- do not retune retracement/hold;
- do not add TFI/FLOW_IMPULSE/compression/basis filters;
- do not open Confirmation/L2/Q2/Validation/Final for rescue.

## 9. Immediate next action

On the qualified VPS:

1. pull the frozen E007 implementation;
2. Python syntax-check engine and preflight runner;
3. run `sc001_e007_preflight_v1_0.py` only;
4. inspect exact terminal status and SHA identity;
5. do not run E007 Discovery until exact matching `E007_PREFLIGHT_PASS` is independently verified.
