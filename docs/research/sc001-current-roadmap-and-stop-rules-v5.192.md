# SC001 Current Roadmap and Stop Rules v5.192

Date: 2026-09-28
Status: **B15-P2 FINAL HYDRATION EXTRACTOR V0.1.5 FROZEN / SMOKE-GATED 94-EVENT BOUNDARY AUTHORIZED**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.191.md`

## Resolved source structure

The stabilized hydration mapper v0.4 completed successfully and was relayed into the GitHub runtime inbox with unchanged bytes.

Canonical runtime report SHA256:

`dc7afb944164b315c5523bb216a49ba8c2352f804feaaff7ae6af778bfe1233d`

Common exact title identity:

`__NEXT_DATA__::$.props.pageProps.articleDetail.title`

The canonical primary rich-text body is frozen as:

`$.props.pageProps.articleDetail.content.json.children`

Observed on DOGUSDT and TONUSDT:
- type: list;
- 15 top-level nodes;
- 55 descendant strings;
- 1664 normalized descendant characters;
- high-confidence score 8.

The internal CMS duplicate:

`$.props.pageProps.articleDetail.entry.entryKey.children`

has the same structural metrics. Sample leaf hashes at rich-text nodes 8 and 12 matched exactly on both branches for both events.

Therefore:
- `content.json.children` is the primary body source;
- `entry.entryKey.children` is only a consistency check;
- there is no adaptive fallback to another candidate.

Selection freeze:

`docs/research/sc001-b15p2-hydration-body-selection-freeze-v0.1.json`

## Final semantic implementation

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1_5.py`

SHA256:

`70cc8164fa1cffc8f8bde749a7e3c67744974b0eeb4c8e21b6e1d10621e8094d`

Implementation freeze:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.5.json`

The following are byte-for-byte unchanged from v0.1.4:
- semantic classifier;
- announcement timestamp parser;
- frozen input validation;
- curl transport.

Only article-region extraction changes from incomplete visible DOM to the frozen hydration path.

## Host boundary

Wrapper:

`scripts/research/run-b15p2-announcement-body-semantic-audit-v0.4.sh`

SHA256:

`f2ad6e0e1de6ef3f4fdc7e3eb0db25028a9c865ffb6593234709030564b5fb1c`

Contract:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-networked-launch-contract-v0.4.json`

Execution is covered by the user's standing delegated engineering authorization for the current B15-P2 contour.

No additional research scope is opened.

## Execution order

One launch command performs:

1. exact contract/SHA/firewall preflight;
2. root-owned, botmarket-readable, non-writable 7-file stage;
3. staged offline self-test;
4. DOGUSDT/TONUSDT hydration extraction smoke;
5. strict smoke validation;
6. only on PASS, full frozen 94-page semantic audit via async systemd.

The same exact staged v0.1.5 code is used by smoke and full audit.

## Runtime handoff

Large output is no longer reconstructed from screenshots.

VPS persists:
- hydration smoke JSON;
- terminal semantic JSON;
- persistent execution log.

The wrapper `--status` validates and relays available artifacts to:

- `docs/research/runtime-inbox/sc001-b15p2-hydration-smoke-v0.1.5-latest.json`
- `docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-latest.json`
- `docs/research/runtime-inbox/sc001-b15p2-semantic-audit-v0.1.5-latest.log`

The user normally only needs to run `--status` and say “готово”.

## Iteration budget

Delegated technical recovery budget remains:

**0 / 5 consumed**

A planned validation step is not a recovery iteration.

Before any actual recovery iteration:
- full programmer-expert review is mandatory;
- related defects should be consolidated;
- line-by-line blind patching is prohibited.

## Firewalls

Still closed:
- affected-contract price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- trading.

## Strategy Manager trigger

DOG/TON smoke is not strategy-relevant.

The first terminal full 94-event semantic PASS/REVIEW **is strategy-relevant**.

After terminal result:
1. validate and freeze result;
2. create `sc001.worker_result_manifest.v0.1`;
3. allow Strategy Watch to trigger the Research Strategy Manager;
4. keep prices closed until the mandatory pre-price mechanism review completes.

## Next state

`RUN_AUTHORIZED_B15P2_SEMANTIC_V015_SMOKE_GATE_THEN_FULL_94`
