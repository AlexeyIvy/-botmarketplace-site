# SC001 — Historical Multi-Asset Universe Selection Protocol v0.1

Date: 2026-09-16  
Status: **PRE-AUDIT GOVERNANCE PROTOCOL — NO NEW PROMOTIONAL BODY ACCESS**  
Scope: **SCALPING RESEARCH / SC001 only**

Parent architecture:
- `docs/research/sc001-next-generation-multi-asset-research-framework-v0.3.md`
- `docs/research/sc001-simulation-verification-and-accounting-standard-v0.1.md`

This protocol governs how the first SC001 multi-asset universe will be constructed. It does not authorize a strategy run and does not reopen E001-E008.

## 1. Objective

Build a historically defensible cross-asset universe that can test whether a strategy mechanism generalizes beyond BTC without introducing current-popularity, survivorship or performance-selection bias.

The first-generation universe should normally contain about 10 instruments, with an acceptable final range of 8-12 only when objective historical eligibility/data constraints require it.

## 2. Initial venue/product family freeze

For the first-generation strict replication program, the initial comparable product family is:

**OKX linear USDT-margined perpetual SWAP instruments.**

Reason:
- comparable contract family and matching/execution semantics;
- existing SC001 OKX infrastructure;
- historical tick trades are available from September 2021 onward and historical L2 from March 2023 onward according to the official OKX historical-data service;
- E007's parent mechanism was defined on `BTC-USDT-SWAP`, so same-family replication minimizes unnecessary cross-venue/product changes.

This is a research-family choice, not a claim that OKX is optimal for production.

## 3. Exact symbols are NOT frozen yet

v0.1 deliberately does not choose token names.

No symbol may be selected because:
- it is popular in 2026;
- it is known to have performed well later;
- it makes a prior SC001 strategy profitable;
- its data are more convenient after strategy outcomes are known.

The exact universe is frozen only after the stages below.

## 4. Stage U0 — metadata-only historical enumeration probe

Before downloading candidate market-data bodies, determine whether official historical metadata can enumerate the contemporaneous USDT-SWAP instrument families/files for selected historical probe dates.

Allowed:
- official metadata/download-link requests;
- filenames;
- archive URLs;
- Content-Length/HEAD if later required;
- current instrument metadata only as a clearly labeled operational cross-check, never as proof of the historical universe.

Forbidden:
- trade/L2 body download;
- returns, signals, strategy outcomes;
- ranking instruments by later performance.

Initial metadata probe dates are diagnostic only and do not become promotional dates.

## 5. Stage U1 — historical candidate-pool reconstruction

If U0 can enumerate historical archives, reconstruct the candidate pool from historical official archive existence rather than today's live-instrument list.

A candidate instrument must satisfy, before any strategy outcome is examined:

1. instrument family is linear USDT perpetual SWAP;
2. official historical source shows existence by the chosen pre-period cutoff;
3. required contract-spec identity can be established with sufficient confidence for the intended period;
4. data coverage needed by the later candidate is objectively available or has a predeclared unavailable-data rule;
5. no performance/result filter is used.

A later delisting does not automatically remove a historically eligible instrument. Treatment of listing/delisting inside the research horizon must follow a predeclared applicability rule and remain visible in breadth denominators.

## 6. Stage U2 — pre-period liquidity calibration if metadata alone is insufficient

Metadata/file existence alone may not rank liquidity reliably. If venue-specific historical turnover/trade intensity is required to stratify the universe, a dedicated **pre-period calibration window** may be opened.

Rules:
- calibration dates must precede the future Discovery window;
- calibration bodies are permanently marked engineering/contaminated;
- only universe/liquidity/capacity statistics may be calculated;
- no candidate strategy signal/PnL may be evaluated on calibration data;
- final symbols and selection rule must be frozen before any new promotional body is opened.

The exact calibration window is not frozen by v0.1; it will be chosen only after U0/U1 establish historical source availability, then written into a later freeze.

## 7. Liquidity stratification principle

The first universe should not consist only of today's or history's tightest-spread majors.

After eligibility and minimum capacity are established, use a prospective liquidity stratification so the replication can reveal whether a mechanism depends on market microstructure.

Conceptual strata:
- Tier A — very high liquidity / tight spread;
- Tier B — high-to-medium liquidity;
- Tier C — medium liquidity / wider spread but still mechanically executable for the frozen order-size rule.

Exact quantitative boundaries and quotas are not yet frozen. They must be derived from the pre-period candidate distribution and fixed before outcomes.

## 8. Sizing comparability

One contract is not comparable across instruments.

Before promotional replication, freeze an economic sizing rule using historical contract specifications, e.g. a target USD notional rounded to valid lot units and capped by a predeclared fraction of available depth/capacity.

The universe must not be selected simply because a fixed one-contract order happens to be convenient.

## 9. Survivorship and applicability accounting

Every historically eligible candidate receives an explicit status:
- selected;
- eligible-not-selected by deterministic frozen selection rule;
- ineligible with objective reason;
- later-unavailable/delisted under predeclared horizon rule;
- data-defective under predeclared integrity rule.

Do not silently remove difficult markets from the denominator after outcomes.

## 10. Contamination firewall

Before any date is assigned to engineering, Discovery, asset holdout or Confirmation, check:

`docs/research/sc001-contamination-registry-v0.1.json`

The registry is conservative and initially incomplete; any candidate date whose prior-use status is uncertain is treated as **not fresh** until backfilled/audited.

Data used to design the new execution/accounting system cannot later serve as untouched Confirmation.

## 11. Independence structure

The future multi-asset program must distinguish:

- cross-asset replication on the same dates;
- chronological replication on later dates.

Other assets on the same calendar days are not treated as independent time evidence because crypto markets share regime shocks.

At least one untouched later-time holdout remains mandatory after cross-asset work.

## 12. Minimum output of the universe audit

Before exact symbols are frozen, produce a machine-readable report containing:

- historical probe dates;
- candidate instrument IDs discovered by date;
- source/host/method identity;
- evidence of historical existence;
- metadata/source availability status;
- contract-spec availability status;
- any listing/delisting ambiguity;
- whether pre-period body calibration is required;
- candidate denominator count;
- no strategy performance fields.

## 13. Stop rules

Stop/review rather than improvise if:
- historical enumeration is incomplete and only current live instruments are available;
- historical specs cannot be established for a material fraction of candidates;
- fewer than 8 objectively eligible comparable instruments remain;
- universe selection would require looking at candidate strategy outcomes;
- required data are available only after opening intended Confirmation bodies.

Do not substitute a hand-picked top-10 list.

## 14. Immediate next step

Run only the metadata-only historical enumeration probe:

`research/sc001/sc001_historical_universe_metadata_probe.py`

The probe must download no market-data bodies and calculate no strategy result.

Only after reviewing the probe may U1/U2 be frozen more tightly and the exact multi-asset universe selected.
