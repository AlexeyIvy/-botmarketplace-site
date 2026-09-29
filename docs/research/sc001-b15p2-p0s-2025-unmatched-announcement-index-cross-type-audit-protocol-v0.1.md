# SC001 B15-P2 P0S — 2025 Unmatched Announcement Index Cross-Type Audit Protocol v0.1

Date: 2026-09-29
Status: **FROZEN SOURCE-ONLY DESIGN / PRICE FIREWALL CLOSED**

Scope:
`SCALPING RESEARCH / SC001 / B15-P2 / P0S / 2025 SOURCE-STRUCTURE AUDIT`

## Purpose

Determine whether the 34 unmatched 2025 closed Bybit USDT LinearPerpetual instruments are absent because the original source census restricted the official announcement index to `type=delistings` and derivative-relevant title/description rows.

This audit is source-structure research only. It does not alter the frozen 80% census gate and does not open any market-price or outcome source.

## Frozen input

Canonical 2025 holdout source census:

`docs/research/sc001-b15p2-p0s-2025-holdout-source-census-result-v0.1.json`

SHA256:

`706cc5696e863ad7cd6e81efabe1629b2f9013e2ad9cbeacad46345f17ee1c36`

Frozen unmatched-symbol count: **34**.

Canonical compact JSON of the sorted unmatched symbol list has SHA256:

`12478369be90bc7f20cb93bd952dffb7068c165f5f33ba4a91e7f00bf73a2847`

Exact set:

`A8USDT, AGTUSDT, AVAILUSDT, BALUSDT, BDXNUSDT, CELRUSDT, COSUSDT, DMCUSDT, EOSUSDT, ETHWUSDT, FISUSDT, FRAGUSDT, FUELUSDT, GLMRUSDT, GORKUSDT, GTCUSDT, GUSDT, LAUNCHCOINUSDT, LOOKSUSDT, MAJORUSDT, NODEUSDT, OSMOUSDT, PERPUSDT, PUMPUSDT, RADUSDT, RSS3USDT, SCAUSDT, SKATEUSDT, SUNDOGUSDT, SWEATUSDT, SWELLUSDT, TANSSIUSDT, TOKENUSDT, ZRCUSDT`.

## Official source semantics

Use only:

1. `GET /v5/announcements/index`
   - locale = `en-US`;
   - **no type filter**;
   - paginate to completion.

2. `GET /v5/market/instruments-info`
   - category = `linear`;
   - status = `Closed`;
   - used only to reconstruct the exact 2025 listing episode for the frozen unmatched symbols.

Official Bybit announcement type keys frozen for schema validation:

- `new_crypto`
- `latest_bybit_news`
- `delistings`
- `latest_activities`
- `product_updates`
- `maintenance_updates`
- `new_fiat_listings`
- `other`

An unknown type key is a source-schema REVIEW, not an adaptive new category.

## Causal timestamp rule

`publishTime` remains the only causal announcement timestamp.

`dateTimestamp` is diagnostic metadata only and is never substituted for a missing or invalid `publishTime`.

For a recovered exact-symbol match to be causal:

- `publishTime` must be numeric plausible milliseconds;
- if instrument `launchTime` exists, `publishTime >= launchTime`;
- `publishTime < deliveryTime`.

## Exact-symbol rule

Search exact uppercase symbol identity in:

`announcement.title + " " + announcement.description`

using alphanumeric token boundaries.

No base-token-only inference is allowed.

No article-body hydration is performed in this v0.1 audit. Body hydration is a separately staged fallback only if the cross-type index audit does not sufficiently explain the unmatched set.

## Recovery classification

For each frozen unmatched instrument, retain all causal exact-symbol matches and classify each route:

1. `NON_DELISTINGS_TYPE`
   - exact causal match exists under an official type other than `delistings`.

2. `DELISTINGS_DERIVATIVE_FILTER`
   - type is `delistings`, but the row fails the original derivative-relevance predicate based on tags/title/description.

3. `DELISTINGS_FEED_OR_RETRIEVAL_DELTA`
   - type is `delistings` and the row satisfies the original derivative-relevance predicate even though the frozen 2025 census recorded the symbol as unmatched.

4. `NO_INDEX_RECOVERY`
   - no causal exact-symbol match exists anywhere in the complete official index.

Missing/invalid `publishTime` exact-symbol matches are retained as integrity diagnostics and never count as causal recovery.

## Frozen decision arithmetic

Original:
- closed in-scope = 154;
- admitted = 120;
- frozen source gate = coverage >= 0.80.

Minimum admitted count required:

`ceil(0.80 * 154) = 124`.

Therefore at least **4 distinct valid causal recoveries** are required to show that a corrected index parser could in principle cross the unchanged source-coverage gate.

This threshold is derived solely from the frozen source-count gate; it uses no price or economic outcome.

## Audit states

`B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_PASS_TO_PARSER_DESIGN`

requires:
- all 34 frozen unmatched instruments reconstructed exactly from official closed-instrument metadata;
- full announcement-index pagination completes without truncation;
- no unknown announcement type;
- no exact-symbol source-integrity issue with missing/invalid `publishTime`;
- at least 4 distinct unmatched symbols have a valid causal exact-symbol recovery.

`B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_DEFER_TO_BODY_AUDIT`

applies when the audit is complete and valid but fewer than 4 symbols are recovered.

`B15P2_P0S_2025_CROSS_TYPE_INDEX_AUDIT_REVIEW`

applies on schema, pagination, transport, metadata identity, unknown-type, or exact-symbol timestamp-integrity failure.

## Firewalls

Forbidden:
- `/v5/market/kline`;
- index-price kline;
- affected-contract price;
- index values;
- basis;
- mark/premium/spot;
- external venue;
- returns;
- PnL;
- L1/L2;
- individual trades;
- funding;
- outcome ranking;
- horizon/symbol/threshold search;
- trading or order execution.

## Consequence

If PASS:
design a corrected 2025 source-census parser that admits the newly demonstrated official announcement routes while leaving the 80% gate and causal `publishTime` rule unchanged. Freeze and offline-validate that parser before any live rerun.

If DEFER:
pre-register an official Bybit article-body hydration audit for the still-unmatched symbols, using the already validated BLT_RICHTEXT / DOUBLE_DASH_ART_HTML extraction machinery.

If REVIEW:
resolve source integrity only. Do not lower gates and do not open prices.

## Execution-plane constraint

Execution is authorized only through BotMarketplace Test Executor after offline validation and only when its rate slot is available.

At protocol creation time the Test Executor UTC-day counter is 10/10. No bypass and no alternate execution plane are authorized.
