# SC001 Current Roadmap and Stop Rules v4.63

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C11/C12 D0 PASS / C11-D1 METADATA BATCH + C12-D1 SPOT SEMANTICS FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.62.md`

## 1. Binding terminal states

All prior terminal strategy states remain immutable.

No rescue tuning is authorized.

## 2. C11-D0 result

Exact:

`C11_D0_SOURCE_CALENDAR_PREFLIGHT_PASS`

Observed:

- representative events verified = 2/2;
- CPI representative archive bytes = 11,850,786;
- Employment representative archive bytes = 16,633,234;
- no historical body opened;
- no macro value/surprise/post-release move/direction/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c11-d0-source-calendar-pass-result-v0.1.md`

## 3. C12-D0 result

Exact:

`C12_D0_SOURCE_PARITY_PREFLIGHT_PASS`

Observed:

- USDC-USDT SPOT LIVE;
- exact historical archive resolved by priapi SPOT instIdList;
- representative 2025-01-15 archive bytes = 315,334;
- no historical body opened;
- no peg deviation/reversion/threshold/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c12-d0-source-parity-pass-result-v0.1.md`

## 4. Contamination chronology updated

Current registry:

`docs/research/sc001-contamination-registry-v0.15.json`

### C11
H1 2025 CPI + Employment event chronology is now:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

No post-release BTC price outcome is authorized yet.

### C12
2025-01-15/16 USDC-USDT historical trade bodies are authorized only for:

`NONPROMOTIONAL_ENGINEERING_SOURCE_CALIBRATION`

No peg deviation is authorized.

## 5. C11-D1 frozen stage

Purpose:

Verify the full frozen H1-2025 event calendar and exact BTC archive metadata/HEAD for 12 events.

Protocol:

`docs/research/sc001-c11-d1-h1-event-archive-metadata-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c11_d1_h1_event_archive_metadata_v0_1.py`

Freeze:

`docs/research/sc001-c11-d1-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `9eb644d067e695f137082be9dff22e851466c907`;
- runner: `e349db5398e200596170b641a2507c731a28e25c`;
- registry: `7311ee3a5e21c0d1050fdc8314af88f14b55d46d`;
- freeze: `12053f42b030ecc0d62f6bf52d92c12b4fadd4c4`.

Exact PASS:

`C11_D1_H1_EVENT_ARCHIVE_METADATA_PASS`

No body GET/open.

## 6. C12-D1 frozen stage

Purpose:

Open exactly 2025-01-15 and 2025-01-16 USDC-USDT trade archives and qualify SPOT schema/timestamp/UTC stitching semantics only.

Protocol:

`docs/research/sc001-c12-d1-spot-trade-semantics-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c12_d1_spot_trade_semantics_v0_1.py`

Freeze:

`docs/research/sc001-c12-d1-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `f57313115d5a88d707aa63d5ed5951dfa53ad563`;
- runner: `dd9f6548fac8698e1c8ffa175441b2b59f020342`;
- registry: `7311ee3a5e21c0d1050fdc8314af88f14b55d46d`;
- freeze: `2a39c14c5939863f227c03035b5954cb1ec4f5a9`.

Exact PASS:

`C12_D1_SPOT_TRADE_SEMANTICS_PASS`

Price fields may be validated numerically but may not be compared to parity.

## 7. Current firewalls

C11-D1:

- no historical trade bodies;
- no macro release value/surprise;
- no first impulse;
- no post-release move;
- no signal/PnL.

C12-D1:

- no peg deviation;
- no parity threshold;
- no reversion outcome;
- no signal/PnL.

Promotional alpha remains closed for both.

## 8. Immediate next action

Run C11-D1 and C12-D1.

Only after exact PASS:

- C11 may freeze its first outcome-bearing H1-2025 headroom sentinel;
- C12 may freeze its calendar Selection/Calibration batch and parity headroom/reversion sentinel.
