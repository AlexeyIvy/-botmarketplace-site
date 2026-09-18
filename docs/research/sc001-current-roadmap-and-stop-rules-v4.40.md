# SC001 Current Roadmap and Stop Rules v4.40

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9-D1 v0.3 PASS / C9-D2 15m MARK-INDEX DATA STAGE FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.39.md`

## 1. Binding terminal states

All prior SC001 terminal states remain unchanged.

C1-C6 remain terminal `REJECT_SENTINEL`.

C9 still has no strategy verdict.

## 2. C9-D1 v0.3 result

Exact:

`C9_D1_V03_FUNDING_ARCHIVE_INTEGRITY_PASS`

Observed:

- assets passed `8/8`;
- exact September funding files only;
- 90 unique funding timestamps per visible asset;
- observed interval set `[8.0]` hours;
- qualified total bytes `10729`;
- reused files `8`;
- downloaded files `0`;
- October funding body accessed by v0.3 false;
- prior October funding contamination acknowledged;
- October funding clean C9 Confirmation eligibility false;
- no return/basis-transition/signal/sentinel/PnL;
- no direction/threshold/event-window selection;
- exit code 0.

Binding result record:

`docs/research/sc001-c9-d1-v0.3-funding-archive-integrity-pass-result-v0.1.md`

## 3. Why another data stage is required

C9-D0 verified mark/index only at 4H resolution.

A scheduled funding-state transition intended for core short-horizon SC001 cannot be studied causally from 4H bars because pre/post-event state is mixed over too wide a window.

Therefore C9 requires a finer synchronized mark/index calibration tape before any outcome-bearing state-transition sentinel.

## 4. C9-D2 contamination declared before value access

Current contamination registry:

`docs/research/sc001-contamination-registry-v0.9.json`

Authorized mark/index calibration interval:

`[2024-08-31T00:00:00Z, 2024-10-01T00:00:00Z)`

for BTC/ETH/DOGE/ORDI/UNI/XRP/OP/BCH.

This interval is:

`NONPROMOTIONAL_SELECTION_CALIBRATION`

for C9 mark/index evidence.

No October UTC mark/index candle is authorized.

## 5. C9-D2 frozen implementation

Protocol:

`docs/research/sc001-c9-d2-mark-index-15m-acquisition-integrity-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c9_d2_mark_index_15m_integrity_v0_1.py`

Freeze:

`docs/research/sc001-c9-d2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `a28256790fb8e7f3953271b2cdae0583bc28c994`;
- runner: `6c16c0a3136349fb5bc63eaef4909b5e6f3d362c`;
- contamination registry: `42202c03259676c1b40937db031e9f08ba30b153`.

## 6. D2 grid

Resolution:

`15m`

Expected UTC grid per source/asset:

`2976` rows.

Require per asset:

- mark = 2976;
- index = 2976;
- aligned = 2976;
- exact UTC 15m grid;
- confirmed bars;
- positive valid OHLC;
- no synthesized gaps.

## 7. Normalized D2 output

One synchronized CSV per asset containing:

- timestamp;
- mark OHLC;
- index OHLC;
- confirmed flag.

The D2 report stores file size/SHA and counts, not individual prices.

## 8. D2 is still no-alpha

D2 may open/store mark/index values because the channel was prospectively contaminated.

It may not calculate:

- mark/index premium;
- return;
- funding-conditioned transition;
- strategy direction;
- threshold;
- event window;
- signal;
- sentinel outcome;
- PnL.

## 9. Exact D2 terminal states

PASS:

`C9_D2_MARK_INDEX_15M_INTEGRITY_PASS`

REVIEW:

`C9_D2_MARK_INDEX_15M_INTEGRITY_REVIEW`

REVIEW is a data/implementation state only.

## 10. October funding incident remains binding

October 2024 funding remains contaminated for C9.

October UTC mark/index remains protected because D2 stops strictly before `2024-10-01T00:00:00Z`.

## 11. Immediate next action

Run frozen C9-D2 mark/index 15m acquisition/integrity on VPS.

Only after exact D2 PASS may a C9 state-transition sentinel mechanism/window/cost architecture be frozen.
