# SC001 Current Roadmap and Stop Rules v4.44

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C8-D0 v0.1 REVIEW CLASSIFIED / v0.2 EXACT-DATE REPAIR FROZEN**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.43.md`

## 1. Binding terminal states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 has no strategy verdict.

## 2. C8-D0 v0.1 result

Exact:

`C8_D0_SOURCE_CLOCK_PREFLIGHT_REVIEW`

with:

- checks passed `5/6`;
- OKX instrument PASS;
- Bybit instrument PASS;
- OKX current trade clock PASS;
- Bybit current trade clock PASS;
- Bybit historical archive PASS;
- OKX historical exact-date archive resolution REVIEW;
- no historical archive body opened;
- no cross-venue price/return/dislocation/lag;
- no signal/PnL/promotional alpha.

Binding review record:

`docs/research/sc001-c8-d0-v0.1-source-clock-review-result-v0.1.md`

Classification:

`SOURCE_TRANSPORT_EXACT_DATE_RESOLUTION / NOT_RESEARCH_FAIL`

## 3. v0.2 repair

C8-D0 v0.2 changes only OKX historical metadata discovery.

Target file remains exactly:

`BTC-USDT-SWAP-trades-2025-01-15.zip`

Metadata query windows are frozen in order:

1. 2025-01-15 UTC label day;
2. 2025-01-14 UTC previous day.

This matches the exact-date discovery semantics already used successfully elsewhere in SC001.

No body access is added.

## 4. C8-D0 v0.2 frozen implementation

Protocol:

`docs/research/sc001-c8-d0-okx-bybit-source-clock-semantics-protocol-v0.2.md`

Runner:

`research/sc001/sc001_c8_d0_v02_okx_bybit_source_clock_preflight.py`

Freeze:

`docs/research/sc001-c8-d0-v0.2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `0ef2b1f88ac68c84acb161785d2c481ee58d3ec6`;
- runner: `6c7a5892fcb0f8a2c4d68b94f6198b7863b71fdd`.

## 5. Exact v0.2 states

PASS:

`C8_D0_V02_SOURCE_CLOCK_PREFLIGHT_PASS`

REVIEW:

`C8_D0_V02_SOURCE_CLOCK_PREFLIGHT_REVIEW`

REVIEW remains engineering/source state only.

## 6. Firewalls remain unchanged

Must remain false:

- historical archive body download/open;
- cross-venue price comparison;
- cross-venue return;
- dislocation;
- lag;
- leader selection;
- strategy signal;
- PnL;
- promotional alpha.

## 7. Consequence of PASS

Only after exact D0 v0.2 PASS may C8-D1 be designed.

C8-D1 will qualify the exact one-day historical bodies and synchronization semantics but will still not calculate cross-venue alpha.

## 8. Immediate next action

Run frozen C8-D0 v0.2 source/clock preflight on VPS.

Do not download/open historical trade bodies before D0 PASS.
