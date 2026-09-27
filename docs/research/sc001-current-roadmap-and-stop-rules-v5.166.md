# SC001 Current Roadmap and Stop Rules v5.166

Date: 2026-09-27
Status: **B15-P2 EXACT EVENT SET FROZEN / SEMANTIC-AUDIT V0.1 IMPLEMENTATION FROZEN / OFFLINE SELFTEST PENDING**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.165.md`

## Exact evidence remains frozen

The B15-P2 source census is fixed at:

- 94 exact Bybit USDT perpetual delisting events;
- 94 unique official announcement URLs;
- one causal notice per event;
- zero pre-launch or post-delivery matched notices;
- event-set SHA256:
  `1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`

No event may be added, removed or re-ranked during semantic audit.

## Semantic-audit objective

Read the exact official announcement body for every frozen event and classify the operational forced-close mechanism before any price outcome is opened.

Protocol:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-protocol-v0.1.md`

Protocol SHA256:

`4209779876e3796feff16a8310af93324cd1927862874524fb90ebf95d51d84f`

Implementation:

`research/sc001/sc001_b15p2_announcement_body_semantic_audit_v0_1.py`

Implementation SHA256:

`4fddb8c42f262dc5744ca5dda572e4e873d0894eb77c666cb973b9de144fcd02`

Implementation freeze:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-implementation-freeze-v0.1.json`

Offline self-test spec:

`docs/research/sc001-b15p2-announcement-body-semantic-audit-offline-selftest-spec-v0.1.json`

## Important design rules

- exact frozen announcement URLs only;
- official Bybit announcement pages only;
- page body, not search-engine snippets, is the audit source;
- semantic parser uses the contract-specific article region rather than page navigation/footer text;
- no full copyrighted body is promoted to GitHub;
- only source hashes and structured semantic classifications are retained;
- announced delisting time is independently parsed and compared with frozen `deliveryTime`;
- multiple explicit settlement architectures are valid findings;
- semantic PASS means resolvability/integrity, not conformity to an expected 30-minute formula.

## Allowed semantic classifications

May classify:

- trading-stop wording;
- active/conditional order cancellation;
- open-position automatic closure;
- closing-price basis;
- index-window length when explicit;
- funding mention / not stated;
- revision/postponement wording.

## Firewalls

Still forbidden:

- affected-contract price;
- external-reference price;
- observed index values;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- outcome-driven event filtering;
- horizon tuning from outcomes.

## Strategy Manager

No strategy review is triggered by implementation preparation.

If the full semantic audit passes, the resulting mechanism architecture **does** become input to the mandatory pre-price Strategy Manager gate.

## Next state

`PREPARE_AND_SEAL_B15P2_SEMANTIC_AUDIT_V01_OFFLINE_SELFTEST_NO_EXECUTION`
