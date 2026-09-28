# SC001 Current Roadmap and Stop Rules v5.189

Date: 2026-09-28
Status: **B15-P2 NEXT HYDRATION CONFIRMED / TARGETED __NEXT_DATA__ STRUCTURE PROBE FROZEN**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.188.md`

## Completed article-structure probe

The corrected host wrapper completed successfully.

Both DOGUSDT and TONUSDT produced the same structural pattern:

`NEXT_HYDRATION_SCRIPT_CONTAINS_TITLE`

For each:
- raw HTML: about 38.1 KB;
- visible text: 332 characters;
- exact title count: 1;
- visible region from title: 65 characters;
- no configured terminator was present;
- 27 script tags;
- exactly one script contained the exact title;
- one JSON script;
- no JSON-LD;
- no `articleBody` candidate;
- `__NEXT_DATA__=true`;
- `self.__next_f.push=false`.

Canonical summary:

`docs/research/sc001-b15p2-announcement-article-structure-probe-v01-result-v0.1.json`

## Interpretation

The visible-DOM integrity threshold is not the cause.

The article body is not present in the visible DOM region and is not exposed as JSON-LD `articleBody`.

The exact title exists inside the Next.js hydration state. The next minimal question is which neighboring/path-specific field in `__NEXT_DATA__` contains the article body or body-like structured content.

Do not lower the 120-character semantic integrity gate.

## Targeted v0.2 probe

Script:

`scripts/research/probe-b15p2-next-data-structure-v0.2.py`

Probe SHA256:

`6bd708526944c6b875757f3f5443da1f088289cdc4792952f569642d142703a6`

Host wrapper:

`scripts/research/run-b15p2-next-data-structure-probe-v0.2.sh`

Wrapper SHA256:

`32728fcbe7b8feb733449bafaa1a8ba5bf95870166a9efedf0068cd34c98d703`

Approval code:

`BM-32728FCBE7B8`

The probe:
- locates the unique `__NEXT_DATA__` script;
- parses it as JSON;
- finds exact-title nodes;
- records the title node's parent-object field names/types/lengths/hashes;
- ranks long structural strings by generic key hints such as content/body/description/html/text;
- records only paths, lengths, hashes and HTML-like counts;
- persists no article text;
- performs no semantic classification.

## Expected consequence

If both events expose the same stable parent/path for a large HTML/text body, freeze a generic hydration extractor bound to:
- official page host;
- exact title sibling;
- stable JSON path/field identity;
- minimum body length;
- deterministic normalized-body hash.

Then re-run DOG/TON smoke before any 94-page semantic audit.

If no stable body path exists, stop and choose a different official extraction route.

## Firewalls

Still closed:
- article text persistence in diagnostics;
- semantic classification;
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

`AWAIT_EXPLICIT_APPROVAL_FOR_B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_BM-32728FCBE7B8`
