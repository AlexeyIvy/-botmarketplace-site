# SC001 Current Roadmap and Stop Rules v4.64

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C11-D1 + C12-D1 PASS / C11-S0 HEADROOM + C12-D2 H1 METADATA FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.63.md`

## 1. Binding prior terminal states

All prior terminal strategy states remain immutable.

No rescue tuning is authorized.

## 2. C11-D1 result

Exact:

`C11_D1_H1_EVENT_ARCHIVE_METADATA_PASS`

Observed:

- events verified = 12/12;
- all official CPI / Employment schedule checks passed;
- all 12 exact BTC-USDT-SWAP daily trade archives resolved and HEAD-qualified;
- no historical trade body opened;
- no macro value/surprise/impulse/move/signal/PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c11-d1-h1-event-archive-metadata-pass-result-v0.1.md`

## 3. C12-D1 result

Exact:

`C12_D1_SPOT_TRADE_SEMANTICS_PASS`

Observed:

- target UTC rows = 24,424;
- D contribution = 18,388;
- D+1 contribution = 6,036;
- SPOT trade schema/timestamp/order integrity passed;
- D+D1 UTC stitching required and qualified;
- no peg deviation / threshold / reversion / signal / PnL;
- exit code 0.

Binding result:

`docs/research/sc001-c12-d1-spot-trade-semantics-pass-result-v0.1.md`

## 4. Contamination registry

Current:

`docs/research/sc001-contamination-registry-v0.16.json`

### C11
H1-2025 12-event BTC price bodies are now authorized for:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

under the frozen C11-S0 headroom rules.

### C12
H1-2025 chronology is declared prospectively for metadata feasibility.

Historical price body access for the H1 batch remains closed until C12-D2 passes and the first parity sentinel is frozen.

## 5. C11-S0 frozen

Purpose:

Test raw 60-second BTC event-move headroom before first-impulse direction, continuation or execution modeling.

Protocol:

`docs/research/sc001-c11-s0-event-move-headroom-sentinel-v0.1.md`

Runner:

`research/sc001/sc001_c11_s0_event_move_headroom_v0_1.py`

Freeze:

`docs/research/sc001-c11-s0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `82cc855173dacff36e899ff82967e33575f2c2d7`;
- runner: `ac1decd4e039549c3b3917382bf1414778cdd612`;
- registry: `0daa3b6b05fafba8fc03b69e09416f2655b5f1ed`;
- D1 result: `42a77c3952bc8010e763a13c50a1a543a672545e`;
- freeze: `724f958444973843c80682cdc159b2b2e5a8e7b4`.

### Frozen C11-S0 structural burden

- two taker fills;
- 10 bps fee reference;
- 10 bps event spread/slippage/model reserve;
- total structural reference = 20 bps.

### Frozen C11-S0 gates

Sample:
- all 12 events must have valid pre-event and +60s anchors.

Headroom:
- >=6/12 events with abs 60s move >=20 bps;
- median abs 60s move >=20 bps;
- p75 abs 60s move >=30 bps;
- max abs 60s move >=50 bps.

Exact states:

- `C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`;
- `C11_S0_REJECT_EVENT_MOVE_HEADROOM`;
- `C11_S0_DEFER_SAMPLE`.

No direction/continuation or PnL is calculated.

## 6. C12-D2 frozen

Purpose:

Metadata-only verification of the full H1-2025 C12 calibration source chronology.

Target UTC days:

`2025-01-01 through 2025-06-30`

Required unique source archives due D+D1 semantics:

`2025-01-01 through 2025-07-01`

Count:

`182`

Protocol:

`docs/research/sc001-c12-d2-h1-archive-metadata-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c12_d2_h1_archive_metadata_v0_1.py`

Freeze:

`docs/research/sc001-c12-d2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `c249d58f420e347207690717a2caf9792fcf684b`;
- runner: `5295b4c0645d5c7ba1659ced940054bdbaa757be`;
- registry: `0daa3b6b05fafba8fc03b69e09416f2655b5f1ed`;
- D1 result: `cad9e3b769485bfc494875b98940a88709a6f41e`;
- freeze: `bae1c2a29adc82120fb06a380f1cd4a7816a7a7a`.

Exact PASS:

`C12_D2_H1_ARCHIVE_METADATA_PASS`

No historical trade body is opened in D2.

## 7. Current firewalls

### C11-S0
Must remain false:

- macro release values;
- macro surprise;
- first-impulse direction;
- continuation outcome;
- execution fill model;
- PnL;
- promotional alpha.

### C12-D2
Must remain false:

- historical trade body access;
- peg deviation;
- reversion outcome;
- threshold selection;
- strategy signal;
- PnL;
- promotional alpha.

## 8. Immediate next action

Run:

1. C11-S0 exactly once on the frozen 12-event H1 calibration batch;
2. C12-D2 metadata-only across 182 required archives.

Only after their terminal outcomes may the next candidate-specific stage be designed.
