# SC001 Current Roadmap and Stop Rules v4.76

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 METADATA V0.2 REVIEW / V0.3 HTML-PARSER FIX FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.75.md`

## 1. Binding prior state

All prior terminal decisions remain unchanged.

C11-S0:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1:

`C11_S1_DEFER_SAMPLE`

C12 remains terminal.

## 2. Metadata v0.2 result

The v0.2 metadata-only rerun returned:

`C11_V2_SC_METADATA_PREFLIGHT_REVIEW`

at the first frozen event:

`EMPLOYMENT 2025-07-03`

No historical trade body or price-bearing outcome was opened.

## 3. Objective diagnosis

Official BLS visibly confirms:

`Thursday, July 3, 2025 08:30 AM Employment Situation for June 2025`

The v0.2 runner applied a continuous row regex directly to raw HTML.

HTML markup between visible table cells broke the continuous raw-text pattern.

Classification:

`ENGINEERING_BLS_RAW_HTML_REGEX_DEFECT`

No chronology, market-data, economic or strategy rule is implicated.

## 4. v0.3 parser amendment

Binding protocol:

`docs/research/sc001-c11-v2-selection-metadata-preflight-protocol-v0.3.md`

Runner:

`research/sc001/sc001_c11_v2_sc_metadata_preflight_v0_3.py`

Implementation freeze:

`docs/research/sc001-c11-v2-selection-metadata-preflight-implementation-freeze-v0.3.json`

v0.3:

1. parses BLS HTML using Python standard-library `HTMLParser`;
2. extracts visible text nodes;
3. normalizes visible whitespace;
4. matches exact:
   - weekday;
   - month/day/year;
   - 08:30 AM;
   - release family.

Optional day zero-padding remains the only date-format tolerance.

## 5. Chronology remains unchanged

All 24 Selection/Calibration events remain frozen exactly as before.

No event replacement.

No Q4-2025 reopening.

Confirmation identities remain frozen prospectively exactly as before.

## 6. Rerun policy

Run all 24 metadata checks from event 1 under v0.3.

Do not combine partial v0.1 or v0.2 checks into the final PASS report.

## 7. Firewalls

Authorized:

- official BLS schedule GET;
- OKX resolver metadata;
- exact archive HEAD.

Forbidden:

- archive body GET/open;
- macro values/surprise;
- first impulse;
- residual move;
- direction;
- continuation;
- execution;
- PnL;
- Confirmation outcome.

## 8. Exact next state

Possible outputs:

- `C11_V2_SC_METADATA_PREFLIGHT_PASS`;
- `C11_V2_SC_METADATA_PREFLIGHT_REVIEW`.

If PASS, freeze Direction Rule v2 + Stage A/B gates before any price-body access.

If REVIEW, inspect only source/engineering cause. No outcome-driven changes.

## 9. Immediate next action

Syntax-check and run v0.3 across all 24 frozen events.

No price-bearing run is authorized.
