# SC001 Current Roadmap and Stop Rules v4.47

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8-D1 v0.1 REVIEW EXPLAINED BY KNOWN OKX UTC BOUNDARY / v0.2 STITCH REPAIR FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.46.md`

## 1. Binding terminal states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8 still has no strategy verdict.

## 2. C8-D1 v0.1 result

Exact:

`C8_D1_HISTORICAL_CLOCK_INTEGRITY_REVIEW`

Golden synchronization:

`C8_D1_SYNC_GOLDEN_PASS`

Observed v0.1 diagnostics:

- OKX rows: 1,761,145;
- OKX grid share about 0.6615;
- OKX p99 staleness 1567 ms;
- Bybit rows: 2,049,441;
- Bybit grid share about 0.9757;
- Bybit p99 staleness 1752.2 ms;
- joint usable share about 0.6430;
- failed gate included `okx_zero_out_of_day`;
- no cross-venue price/return/dislocation/lag;
- no signal/PnL/promotional alpha.

## 3. Root cause of the OKX v0.1 failure

SC001 Q006R previously established that OKX historical daily trade archives use a 16:00 UTC source boundary.

A single archive D does not represent UTC day D.

Qualified rule:

`archive D + archive D+1 -> retain created_time in UTC [D,D+1)`.

C8-D1 v0.1 incorrectly used only archive D.

This is an implementation/data-boundary issue, not C8 research evidence.

## 4. No clock-gate rescue

The v0.2 repair does **not** alter:

- 1-second grid;
- 2-second staleness limit;
- 0.98 per-venue usable-share gate;
- 0.95 joint usable-share gate;
- 1000 ms p99 staleness gate;
- 5-second maximum adjacent-gap gate.

These remain frozen until the corrected OKX UTC day is measured.

## 5. Contamination registry updated before D+1 body access

Current registry:

`docs/research/sc001-contamination-registry-v0.11.json`

Authorized engineering bodies:

- OKX 2025-01-15 archive D;
- OKX 2025-01-16 archive D+1;
- Bybit 2025-01-15 archive.

Role:

`NONPROMOTIONAL_ENGINEERING_CLOCK_CALIBRATION`

No cross-venue price comparison is authorized.

## 6. C8-D1 v0.2 frozen implementation

Protocol:

`docs/research/sc001-c8-d1-historical-trade-clock-integrity-protocol-v0.2.md`

Runner:

`research/sc001/sc001_c8_d1_v02_historical_trade_clock_integrity.py`

Freeze:

`docs/research/sc001-c8-d1-v0.2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `648a0cdbac9785c9268e5f069b9f113d62a046dd`;
- runner: `9848f82583c698c6b7ebbb8f8106b0622ecd56b0`;
- contamination registry: `442a5e0462c1d2aa1a7458691c0b08223d641a13`;
- v0.1 review record: `1cd378a77b9ccd209e9235180d62f1b294a89929`.

## 7. v0.2 OKX reconstruction requirements

For D and D+1 source archives:

- exact trusted identity;
- ZIP CRC;
- exact header;
- zero malformed rows;
- source timestamps nondecreasing;
- source trade IDs strictly increasing;
- consistent timestamp scale.

For stitched target UTC day:

- retain only 2025-01-15 UTC rows;
- trade IDs strictly increasing;
- trade-ID gaps = 0;
- all 1440 UTC minute buckets;
- both buy and sell sides.

Only stitched target timestamps enter cross-venue clock diagnostics.

## 8. Exact v0.2 states

PASS:

`C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_PASS`

REVIEW:

`C8_D1_V02_HISTORICAL_CLOCK_INTEGRITY_REVIEW`

REVIEW remains engineering/clock state only.

## 9. Decision rule after v0.2

If v0.2 passes, design a separate cross-venue structural dislocation/headroom sentinel.

If v0.2 remains REVIEW after correct stitching, do not automatically loosen synchronization gates. First diagnose whether a fixed 1-second full-day as-of architecture is the right scientific representation for C8.

## 10. Immediate next action

Run frozen C8-D1 v0.2 OKX UTC-stitch clock integrity on VPS.
