# SC001 Current Roadmap and Stop Rules v4.66

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C11-S0 SURVIVE / C12-D2 v0.1 HTTP-429 REVIEW / v0.2 RATE-LIMIT REPAIR FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.65.md`

## 1. Binding prior states

All prior terminal strategy states remain immutable.

C11-S0 remains:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

No C11 direction/continuation/PnL outcome has yet been opened.

## 2. C12-D2 v0.1 result

Exact:

`C12_D2_H1_ARCHIVE_METADATA_REVIEW`

Observed error:

`resolve failed 2025-01-05: HTTP Error 429: Too Many Requests`

Exit code:

`2`

Classification:

`ENGINEERING_RATE_LIMIT_REVIEW / NOT_C12_RESEARCH_FAIL`

No historical body, peg deviation, reversion, threshold, signal, PnL or promotional alpha was opened.

Binding review:

`docs/research/sc001-c12-d2-v0.1-rate-limit-review-v0.1.md`

## 3. Research rules unchanged

C12 still requires exact metadata for:

- target H1 2025 UTC days;
- source-support archives 2025-01-01 through 2025-07-01 inclusive;
- total exact archive count = 182.

No date may be dropped because of rate limiting.

## 4. C12-D2 v0.2 engineering repair

Only request orchestration changes:

- sequential requests;
- minimum 1.5-second HTTP spacing;
- explicit HTTP 429 handling;
- Retry-After support;
- bounded exponential backoff from 15s to 240s;
- 8 attempts per HTTP operation;
- atomic checkpoint after every verified archive;
- deterministic resume.

No market/research threshold changed.

## 5. C12-D2 v0.2 frozen implementation

Protocol:

`docs/research/sc001-c12-d2-h1-archive-metadata-protocol-v0.2.md`

Runner:

`research/sc001/sc001_c12_d2_v02_h1_archive_metadata.py`

Freeze:

`docs/research/sc001-c12-d2-v0.2-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `42952c1dbc57555cabcbd933e4dbd3c7c44531ee`;
- runner: `7b42526953a147703a26ba81260fa049925e8f3e`;
- registry: `0daa3b6b05fafba8fc03b69e09416f2655b5f1ed`;
- v0.1 review: `316592980300973d122dbb81adb0848fa2eb2b5f`.

## 6. Exact v0.2 states

PASS:

`C12_D2_V02_H1_ARCHIVE_METADATA_PASS`

REVIEW:

`C12_D2_V02_H1_ARCHIVE_METADATA_REVIEW`

REVIEW remains source/engineering only.

## 7. Resume semantics

If v0.2 is interrupted or rate-limited after some dates:

- do not delete the checkpoint;
- rerun the exact same frozen v0.2 runner;
- it resumes from the first unverified date.

The checkpoint contains metadata only and carries no price outcome.

## 8. Immediate next action

Run C12-D2 v0.2.

C11 may proceed separately only after its next direction/continuation protocol is frozen; no such outcome run is authorized by this roadmap entry.
