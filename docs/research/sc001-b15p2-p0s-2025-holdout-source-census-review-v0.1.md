# SC001 B15-P2 P0S — 2025 Holdout Source Census Review v0.1

Date: 2026-09-29
Status: **SOURCE_CENSUS_REVIEW / PRICE FIREWALL CLOSED**

Execution:
- Test Executor job: `job_20260929T152635Z_c6d1faee`
- repo head: `a82e971ac291bda03e7bf9d29cfaa38c76428f8b`
- network profile: `public_research`
- entrypoint SHA256: `0c0bd46961cfebb17ecf74dde8822c496c0f73198dae97681d0658abb776355d`
- exit code: 0
- timed out: false

Canonical exact result:
`docs/research/sc001-b15p2-p0s-2025-holdout-source-census-result-v0.1.json`

SHA256:
`706cc5696e863ad7cd6e81efabe1629b2f9013e2ad9cbeacad46345f17ee1c36`

Canonical log:
`docs/research/runtime-inbox/sc001-b15p2-p0s-2025-holdout-source-census-v0.1.log`

SHA256:
`84ca11c1dfba6278ce8f6af8e424fe6deea476c38e7b32beae0b126f0de259ce`

## Registered source-only result

The frozen 2025 window was:
`2025-01-01T00:00:00Z <= deliveryTime < 2026-01-01T00:00:00Z`

Observed:
- closed in-scope Bybit USDT LinearPerpetual instruments: 154;
- admitted events with causal official notice: 120;
- announcement-match coverage: 120/154 = 0.7792207792207793;
- delivery months represented: all 12 months of 2025;
- lead-time median: 71.55041666666666 hours;
- minimum positive lead: 24.091666666666665 hours;
- matched source timestamp integrity issues: 1.

Frozen gates:
- closed perpetuals >=5: PASS;
- admitted events >=5: PASS;
- all admitted lead times positive: PASS;
- >=3 delivery months: PASS;
- announcement-match coverage >=0.80: FAIL;
- matched source timestamp integrity: FAIL.

Terminal census state:
`B15P2_P0S_2025_HOLDOUT_SOURCE_CENSUS_REVIEW`

## Integrity issue

The single matched-source timestamp integrity issue is:

- symbol: `BNXUSDT`;
- issue: missing `publishTime`;
- diagnostic-only `dateTimestamp` points to an older same-symbol announcement;
- URL: `https://announcements.bybit.com/en-US/article/delisting-of-bnxusdt-perpetual-contract-blt8efa3ed073235940`.

BNXUSDT is nevertheless already admitted by a separate valid causal 2025 announcement with numeric `publishTime`. Therefore resolving this legacy-row integrity issue would not by itself repair the 77.92% announcement-match coverage gate.

## Unmatched source set

34 in-scope closed perpetual symbols did not obtain an admissible causal exact-symbol announcement match under the frozen title+description parser.

This is now a source-structure question, not a price question.

Noncanonical external search gives at least some indications that certain unmatched names (for example BALUSDT and EOSUSDT) had public Bybit delisting communications, suggesting the 2025 announcement structure may differ from the exact title+description assumptions used in the 2026 census. Such external search is diagnostic only and is not accepted as event-source evidence.

## Three-role review

### Financial expert / trader

The 2025 pool is broad enough to remain strategically interesting: 120 admitted events across all 12 months. The blocker is source provenance/matching integrity, not event scarcity. No economic conclusion is permitted because no price/index/basis was accessed.

### Programmer-trader / research engineering

The live run completed correctly and preserved every market-price firewall. Two independent source issues remain:
1. one legacy same-symbol row with missing `publishTime`;
2. 34 exact instruments unmatched by the frozen announcement title+description rule.

Do not lower the 80% gate. The correct next action is a source-structure audit of the unmatched set using official Bybit announcement bodies/metadata only, with a separately frozen parser contract.

### Mathematician / statistician

Because this stage is source-only, correcting a demonstrated source-schema mismatch before any P0S price access does not contaminate price outcomes. However the correction must be frozen before rerunning the source census, and the 80% gate must remain unchanged.

## Decision

Current state:
`P0S_2025_HOLDOUT_SOURCE_CENSUS_REVIEW`

Next allowed research action:
`DESIGN_OFFICIAL_BYBIT_2025_UNMATCHED_ANNOUNCEMENT_STRUCTURE_AUDIT_NO_PRICE`

Forbidden:
- lowering the 80% source gate;
- accepting web-search mirrors as canonical event evidence;
- opening contract prices, index values, basis, returns or PnL;
- using another venue;
- trading;
- bypassing Test Executor rate limits.

Operational note:
The Test Executor daily counter reached 10/10 after this run. No further Test Executor job is authorized until the rate window permits it.
