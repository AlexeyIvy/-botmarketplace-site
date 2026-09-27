# SC001 — B15-P2 Announcement-Body Semantic Audit Protocol v0.1

Date: 2026-09-27
Status: **FROZEN BEFORE SEMANTIC-AUDIT NETWORK ACCESS**
Scope: `SCALPING RESEARCH / SC001 / B15-P2 / ANNOUNCEMENT BODY SEMANTICS`

## 1. Purpose

Classify the exact frozen 94-event Bybit scheduled-perpetual-delisting set using official announcement wording only.

This stage asks what the forced-close mechanism actually says contractually/operationally before any price outcome is opened.

It does not test profitability.

## 2. Frozen input

Only the exact frozen event set may be used:

`docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json`

Required SHA256:

`c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c`

Event-set freeze:

`docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json`

Required event-set SHA256:

`1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`

No event may be added, removed or re-ranked during this audit.

## 3. Authoritative semantic source

For each frozen event, fetch only the exact official announcement URL already frozen in the event set.

Allowed hostname:

`announcements.bybit.com`

Redirects are allowed only when the final hostname remains:

`announcements.bybit.com`

No search-engine text is an audit source.

The public Bybit Announcement API may be used only as auxiliary source metadata, not as a substitute for the exact page body when body extraction fails.

## 4. Page acquisition integrity

For each of 94 unique URLs record:

- requested URL;
- final URL;
- HTTP success;
- raw HTML SHA256;
- normalized visible-text SHA256;
- normalized visible-text length;
- extracted announcement article-region SHA256;
- article-region length.

Semantic classification MUST use the announcement article region beginning at the exact contract-specific title, not arbitrary page chrome/navigation/footer text. This prevents unrelated site-wide words such as “funding” or “updated” from becoming false semantic evidence.

Do not persist the full announcement body in GitHub.

The audit persists structured semantic classifications and hashes only.

If the exact page body cannot be extracted reliably, classify the event:

`BODY_SOURCE_UNRESOLVED`

and do not infer semantics from missing text.

## 5. Event identity check

Each page must contain an exact-symbol title/body reference consistent with:

`Delisting of <EXACT_SYMBOL> Perpetual Contract`

The body-announced delisting timestamp must be parsed independently and compared with the frozen instrument `deliveryTime`.

Classification:

- `TIME_MATCH`
- `TIME_MISMATCH`
- `TIME_UNRESOLVED`

No timestamp mismatch may be silently corrected.

## 6. Semantic fields

For every frozen event classify:

### Trading termination
- `TRADING_STOP_EXPLICIT`
- `TRADING_STOP_UNRESOLVED`

### Active-order handling
- `ACTIVE_ORDERS_AUTO_CANCEL_EXPLICIT`
- `ACTIVE_ORDER_HANDLING_UNRESOLVED`

### Open-position handling
- `OPEN_POSITIONS_AUTO_CLOSE_EXPLICIT`
- `OPEN_POSITION_HANDLING_UNRESOLVED`

### Closing-price basis
When explicit, classify:
- `AVERAGE_INDEX_PRICE_WINDOW`
- `OTHER_EXPLICIT_BASIS`
- `BASIS_UNRESOLVED`

If `AVERAGE_INDEX_PRICE_WINDOW`, extract the stated window length in minutes.

### Funding treatment
Classify:
- `FUNDING_EXPLICITLY_MENTIONED`
- `FUNDING_NOT_STATED`

Absence of a funding mention means only “not stated in the announcement,” not “no funding effect.”

### Revision/postponement wording
Classify:
- `REVISION_OR_POSTPONEMENT_MENTIONED`
- `NO_REVISION_OR_POSTPONEMENT_WORDING`

This field does not override the frozen event clock.

## 7. No semantic expectation gate

The audit MUST NOT require all events to use one predefined settlement formula.

Different explicit semantic classes are valid findings.

The audit PASS criterion is source/semantic resolvability, not conformity to an expected 30-minute rule.

## 8. Audit PASS / REVIEW

PASS requires all:

- all 94 frozen URLs fetched from the official hostname;
- all 94 exact symbols identified;
- all 94 announced delisting timestamps parsed;
- all 94 announced times match frozen deliveryTime;
- all 94 open-position handling states resolved;
- all automatic-close events have an explicit closing-price basis classification;
- zero body-source integrity errors.

Then:

`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS`

Otherwise:

`B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW`

REVIEW does not authorize dropping or replacing difficult events.

## 9. Allowed aggregate outputs

May report:

- fetched/resolved event count;
- exact time-match count;
- automatic-close count;
- closing-price semantic-class counts;
- index-window minute distribution;
- active-order cancellation count;
- trading-stop explicit count;
- funding-mentioned count;
- revision/postponement wording count;
- unresolved event identities.

No price value, index value, basis, return or PnL is allowed.

## 10. Firewalls

Forbidden:

- affected-contract price;
- external-reference price;
- index-price observations;
- basis/spread;
- returns;
- PnL;
- outcome ranking;
- outcome-driven event filtering;
- horizon tuning from outcomes.

Text such as “average index price” is a semantic rule description only; no index value may be requested or calculated.

## 11. Consequence

If PASS:

1. freeze semantic classes for all 94 events;
2. identify whether one or more materially distinct forced-close architectures exist;
3. invoke the Research Strategy Manager for the mandatory pre-price mechanism gate;
4. before any price outcome, freeze:
   - structured mechanism fingerprint;
   - mechanism timescale;
   - Edge-to-Fill;
   - two-mode Minimum Viable Horizon;
   - capital-time economics.

If REVIEW:

resolve source/semantic integrity without opening prices.
