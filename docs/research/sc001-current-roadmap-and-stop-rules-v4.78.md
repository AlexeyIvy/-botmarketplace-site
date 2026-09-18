# SC001 Current Roadmap and Stop Rules v4.78

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — C11 V2 SELECTION V1.0 IMPLEMENTATION FAIL / HEADER DIAGNOSTIC NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.77.md`

## 1. Binding research state

All prior terminal decisions remain unchanged.

C11 remains active and unresolved.

The v2 Selection run has **no financial/statistical verdict** yet.

## 2. Selection v1.0 implementation state

Observed:

- events 1-12 progressed through body/schema processing;
- event 13 = Employment 2026-04-03;
- exact stop:
  `C11_V2_SELECTION_IMPLEMENTATION_FAIL`;
- exact error:
  `RuntimeError: header mismatch`.

Binding review:

`docs/research/sc001-c11-v2-selection-v1-implementation-fail-review-v0.1.md`

## 3. What is NOT allowed

Do not:

- call this DATA_QUALITY DEFER;
- call Stage A reject;
- call Stage B reject;
- call survive;
- alter event chronology;
- change the 1-second direction rule;
- change 60-second endpoint;
- alter 20 bps burden;
- weaken breadth/actionability gates;
- open Confirmation;
- inspect price rows merely to diagnose the header.

## 4. Exact next action

Read-only schema diagnostic on the 2026-04-03 archive only.

Inspect only:

- ZIP member identity/count;
- first raw line bytes;
- decoded first header line;
- BOM presence.

No data row/outcome access beyond what the failed authorized runner already consumed.

## 5. After diagnosis

If the mismatch is encoding/format-only:

- create a versioned engineering-only parser amendment;
- preserve all financial/statistical rules exactly;
- freeze implementation identity;
- rerun the whole 24-event Selection under one implementation version.

If genuine schema drift exists:

- map exact new schema semantics first;
- freeze a schema-version-aware parser;
- no arbitrary permissive parsing.

## 6. Confirmation

Prospective Confirmation remains fully closed.

## 7. C13+

Remain closed while C11 is unresolved.
