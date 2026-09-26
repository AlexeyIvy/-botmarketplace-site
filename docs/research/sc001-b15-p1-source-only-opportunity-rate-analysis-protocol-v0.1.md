# SC001 — B15-P1 Source-Only Opportunity-Rate Analysis Protocol v0.1

Date: 2026-09-26  
Status: **PRE-PRICE / POST-COLLECTOR-FREEZE BINDING PROTOCOL**  
Scope: `SCALPING RESEARCH / SC001 / B15-P1 / STAGE E`

Parents:

- `docs/research/sc001-b15-p1-transferability-shock-four-role-optimization-review-v0.2.md`;
- `docs/research/sc001-b15-p1-full-cycle-edge-to-fill-card-v0.1.md`;
- `docs/research/sc001-b15-p1-15-second-nonprice-collector-protocol-v0.1.md`;
- `docs/research/sc001-b15-p1-final-identity-route-v0.2.2-freeze-v1.json`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.104.md`.

## 1. Purpose

Stage E measures whether B15-P1 produces enough **prospectively observed effective-transferability events** to justify further research.

It remains source-only.

Forbidden in Stage E:

- cross-venue prices;
- spreads;
- returns;
- PnL;
- price reaction around events;
- price-based asset/network selection;
- threshold tuning from market outcomes.

The collector remains frozen and running. Stage E is a separate read-only analysis layer.

## 2. Primary inference unit

Do not treat 15-second polls, route rows, assets, or networks as independent samples.

Primary unit:

`VENUE-LEVEL EFFECTIVE-TRANSFERABILITY OUTAGE CLUSTER`

Nested observations may include:

- asset;
- canonical network representation;
- transfer direction;
- route-state transition;
- fee-source metadata.

A broad venue/network maintenance episode affecting many assets is one clustered infrastructure episode, not many independent trials.

## 3. Effective directed asset transferability

For each frozen asset and direction:

- `BYBIT_TO_OKX`;
- `OKX_TO_BYBIT`;

aggregate **all frozen common asset representations**.

Effective state:

- `ACTIVE` if at least one frozen common representation is `ACTIVE`;
- `BLOCKED` only when every frozen common representation is one of:
  - `BLOCKED_SOURCE_WITHDRAWAL`;
  - `BLOCKED_DESTINATION_DEPOSIT`;
  - `BLOCKED_BOTH`;
- `UNKNOWN` otherwise, including no active route plus any `SOURCE_UNKNOWN` or `METADATA_INVALID`.

This rule prevents false segmentation from one disabled network while another valid common route remains open.

Known one-sided representations remain route-ineligible.

## 4. Episode definition

A primary source-defined outage episode begins only on:

`effective ACTIVE -> effective BLOCKED`

It ends cleanly on:

`effective BLOCKED -> effective ACTIVE`

Rules:

- `BLOCKED -> UNKNOWN` censors the episode;
- an episode still blocked at the observation-window end is right-censored;
- an asset/direction already blocked at the observation-window start is left-censored and is not counted as a new incident;
- `UNKNOWN -> BLOCKED` is not a clean incident start;
- no state may be carried forward through a source gap.

Duration for completed episodes is bounded by first observed blocked and first observed active slots. No fabricated exchange-internal transition timestamp is created.

## 5. Blocker signature

At episode start, derive a non-price blocker signature from the frozen route states.

For `BYBIT_TO_OKX`:

- source withdrawal block -> `BYBIT_WITHDRAW`;
- destination deposit block -> `OKX_DEPOSIT`.

For `OKX_TO_BYBIT`:

- source withdrawal block -> `OKX_WITHDRAW`;
- destination deposit block -> `BYBIT_DEPOSIT`.

`BLOCKED_BOTH` contributes both applicable components.

Mixed blockers remain mixed; the analyzer must not infer a maintenance cause from route state alone.

## 6. Independent outage clustering

Primary deterministic cluster rule:

two source-defined episodes belong to the same outage cluster when:

1. they share at least one blocker component; and
2. either:
   - their start times are within `10 minutes`; or
   - their observed/censored episode intervals overlap.

Clustering is transitive.

This deliberately errs toward **under-counting independence** rather than treating rolling exchange-wide operational changes as many separate opportunities.

Primary cluster join window:

`600 seconds`

It is frozen before a Stage E opportunity-rate result is opened.

## 7. Cause classification boundary

The status API does not by itself establish:

- scheduled vs unscheduled;
- wallet maintenance vs chain-wide incident;
- protocol exploit/security event;
- migration/delisting/compliance cause.

Therefore analyzer-generated clusters are:

`CAUSE_UNCLASSIFIED`

until a separate official-source annotation process is frozen and applied.

Cause annotations may use official exchange/project/network notices with causal timestamps, but no price outcome.

No cluster may be labeled a clean venue-operational event merely from co-movement in the status feed.

## 8. Quote-side restoration diagnostic

For each clean asset outage start, record the effective USDT route state in the **opposite direction**, because the conservative full-cycle architecture restores quote inventory opposite to base restoration.

This is descriptive source evidence only.

It does not authorize price/headroom analysis.

## 9. Fee-source diagnostic

For each clean asset outage start, inspect the most recent successful authenticated account/pair fee snapshots from both venues.

Freshness rule remains frozen from the collector:

`fresh <= 8 hours`

Report:

- fee snapshot present/fresh on Bybit;
- fee snapshot present/fresh on OKX;
- both-fresh count.

Do not replace missing/stale metadata with the 10 bps fee floor for a later primary economic PASS.

## 10. Integrity gates

Stage E analysis must be fail-closed.

For closed UTC days used in analysis:

- daily manifest schema/stage/firewall must match;
- expected cadence remains 15 seconds / 5760 scheduled slots per full UTC day;
- selected poll file SHA256 must match the daily manifest;
- selected events/fee file SHA256 and row counts must match the daily manifest;
- poll hash-chain entries must recompute;
- poll chain must be continuous within and across selected days;
- `price_data_collected=false`;
- `pnl_calculated=false`;
- collector manifest must keep price/PnL authorization false.

Formal opportunity-rate inference requires at least:

- poll coverage >= 99.0% of expected slots;
- both-venue-valid poll fraction >= 99.0% of expected slots;
- no unresolved hash/chain/data-integrity failure.

Source gaps remain explicit and are removed from the usable-exposure denominator.

## 11. Observation windows

The window rules are frozen before the first Stage E source-only checkpoint.

### W0 — pipeline smoke

Current partial-day data may be used only to prove:

- input materialization works;
- collector state/manifest schema is readable;
- poll chain parses;
- event and fee files parse;
- price/PnL firewalls remain closed.

No opportunity-rate inference.

### W1 — first operational source checkpoint

`7 complete UTC days`

Allowed outputs:

- source integrity/coverage;
- source-gap duration;
- source-defined episode count;
- cluster count;
- duration diagnostics;
- fee metadata completeness;
- storage/operational observations.

This is not an automatic price-stage authorization.

### W2 — first formal opportunity-rate checkpoint

`30 complete UTC days`

Report the cluster count and normalized cluster rate per 30 **usable** source days.

Classification:

- `>=10 independent clusters`: `EVENT_RICH`;
- `1..9 independent clusters`: `EVENT_SPARSE`;
- `0 clusters`: `ZERO_EVENT_30D`.

The threshold `10` is a descriptive sample-size gate for a more meaningful duration/breadth distribution. It is **not** a profitability threshold and does not automatically authorize prices.

If zero clusters are observed, report the simple one-sided 95% Poisson upper bound:

`-ln(0.05) / usable_days * 30`

This is a rate diagnostic only; it does not assert stationarity.

### W3 — sparse-event extension

If W2 has fewer than 10 independent clusters, continue the collector toward:

`90 complete UTC days`

unless a separately reviewed scheduled clean event justifies an event-specific prospective protocol earlier.

Do not stop the collector merely because W1/W2 is sparse.

## 12. Primary source-only metrics

Report:

- complete UTC days;
- calendar observation time;
- usable exposure after source-gap union;
- poll coverage;
- both-venue-valid fraction;
- effective asset-direction time fraction:
  - ACTIVE;
  - BLOCKED;
  - UNKNOWN;
- clean episode starts;
- completed vs censored episodes;
- completed duration median / p25 / p75 / p90;
- independent outage-cluster count;
- cluster rate per 30 usable days;
- affected-asset breadth;
- blocker-component concentration;
- opposite-direction USDT state at episode start;
- both-venue fee-snapshot freshness at episode start.

No per-asset price ranking is permitted.

## 13. Frozen universe and anti-selection rule

The Stage E analyzer consumes the frozen v0.2.2 identity/route universe.

It may report source-event concentration by asset/network for diagnostics, but:

- it may not delete low-event assets;
- it may not promote high-event assets into a preferred price-test subset;
- it may not change network identity;
- it may not alter the collector.

Any later price protocol must separately state its universe rule before reading B15 price outcomes.

## 14. Stage E statuses

Before 7 complete UTC days:

`B15P1_STAGE_E_PIPELINE_OBSERVATION_ACCUMULATING`

At >=7 and <30 complete UTC days:

- `B15P1_STAGE_E_SEVEN_DAY_OPERATIONAL_CHECKPOINT_PASS`; or
- `B15P1_STAGE_E_SEVEN_DAY_OPERATIONAL_CHECKPOINT_REVIEW`.

At >=30 complete UTC days:

- `B15P1_STAGE_E_SOURCE_OPPORTUNITY_RATE_READY_EVENT_RICH`;
- `B15P1_STAGE_E_SOURCE_OPPORTUNITY_RATE_READY_EVENT_SPARSE`;
- `B15P1_STAGE_E_SOURCE_OPPORTUNITY_RATE_READY_ZERO_EVENT_30D`;
- or `B15P1_STAGE_E_SOURCE_OPPORTUNITY_RATE_REVIEW_DATA_QUALITY`.

No Stage E status automatically opens price/PnL.

## 15. Price-stage boundary

Stage F remains separately authorized.

Before any B15 price/headroom feed is opened, review:

- Stage E opportunity rate;
- cause-classification coverage;
- source integrity;
- fee-source coverage;
- whether the planned protocol is for:
  - a general future unscheduled event; or
  - a separately identified scheduled event.

Do not retrospectively inspect price reactions to Stage E events and then redesign the protocol.

## 16. Next exact implementation step

Implement and offline-validate a separate read-only Stage E analyzer.

The analyzer may consume allowlisted `sc001_data` snapshots through the offline Runner.

It must not:

- call an exchange;
- use credentials;
- modify collector files;
- restart the collector;
- access price endpoints;
- calculate PnL.

Immediate first real-data task after self-test:

`W0 REAL-DATA PIPELINE SMOKE`

No opportunity-rate conclusion is permitted from W0.
