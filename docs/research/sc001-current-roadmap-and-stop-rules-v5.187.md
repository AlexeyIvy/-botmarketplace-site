# SC001 Current Roadmap and Stop Rules v5.187

Date: 2026-09-28
Status: **B15-P2 SMOKE EXTRACTION FAILURE / TWO-PAGE ARTICLE-STRUCTURE PROBE FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.186.md`

## v0.3 network boundary result

The approved semantic network v0.3 reached:

- network preflight PASS;
- staged v0.1.4 self-test PASS;
- real two-page transport smoke START.

The smoke then returned:

`B15P2_ANNOUNCEMENT_BODY_TRANSPORT_SMOKE_V014_REVIEW`

with:

`RuntimeError: announcement article region unexpectedly short`

The fail-closed wrapper then produced:

`transport_smoke_failed_full_94_not_started`

Therefore:
- full 94-page semantic audit did **not** start;
- this is not a semantic REVIEW;
- no price/basis/return/PnL data was opened.

Canonical diagnostic:

`docs/research/sc001-b15p2-announcement-body-smoke-v014-extraction-failure-diagnostic-v0.1.json`

## Current interpretation

Transport itself is no longer the primary failure class.

The validated curl path reached page-body extraction, but the current visible-DOM extractor did not yield a sufficiently long contract-specific article region.

Do not lower the 120-character integrity threshold merely to force PASS.

## Next minimal diagnostic

Frozen two-page article-structure probe:

`scripts/research/probe-b15p2-announcement-article-structure-v0.1.py`

SHA256:

`73c14a0963a245ad9ee431f6e76d16deed99d698fddeb32f78ca4c1fb685fa81`

Approval code:

`BM-73C14A0963A2`

Its purpose is to distinguish among:

- visible DOM sufficient but an early terminator cuts the article;
- body stored in JSON-LD `articleBody`;
- body/title stored in JSON/Next.js hydration state;
- title present in raw HTML but body absent from raw visible DOM;
- unresolved structure requiring a different official-page extraction method.

The probe uses the same exact DOGUSDT and TONUSDT frozen pages and the same validated curl transport.

It persists no article text and performs no semantic classification.

## Decision after probe

- `VISIBLE_REGION_EARLY_TERMINATOR_COLLISION`:
  fix structural boundary markers only.
- `JSONLD_OR_JSON_ARTICLEBODY_CANDIDATE`:
  add a generic exact-title-bound JSON articleBody extractor, preserve visible-DOM as primary.
- `JSON_HYDRATION_TITLE_BODY_CANDIDATE`:
  add generic JSON hydration extraction with exact-title/source integrity gates.
- `NEXT_HYDRATION_SCRIPT_CONTAINS_TITLE`:
  inspect/freeze a generic Next hydration decoder before any semantic run.
- `RAW_HTML_HAS_TITLE_BUT_VISIBLE_BODY_INSUFFICIENT`:
  evaluate rendered-page or documented official source route; do not lower semantic integrity gates.
- unresolved:
  stop and redesign acquisition source before full audit.

## Firewalls

Still closed:
- semantic classification in this diagnostic;
- price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- trading.

## Strategy Manager

No trigger yet.

No terminal semantic evidence exists.

## Next state

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_ARTICLE_STRUCTURE_PROBE_BM-73C14A0963A2`
