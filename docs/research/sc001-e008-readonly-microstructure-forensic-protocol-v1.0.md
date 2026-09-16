# SC001-E008 — Read-Only Microstructure Forensic Protocol v1.0

Date: 2026-09-16  
Status: **READ-ONLY POSTMORTEM / E008 TERMINAL FAIL PRESERVED**

## 1. Purpose

E008 remains terminal `E008_DISCOVERY_FAIL`. This stage does not rerun the maker strategy, does not alter any E008 parameter or gate, and cannot reopen Confirmation/Q2/Validation/Final.

Purpose: distinguish robust economic failure mechanisms from artifacts of the deliberately pessimistic execution/queue model by measuring the already-qualified Discovery market data directly.

## 2. Inputs

Read only:
- `~/sc001_data/SC001_E008_DISCOVERY_SEMANTIC_INTEGRITY/sc001_e008_discovery_semantic_integrity_report.json`;
- `~/sc001_data/SC001_E008_MAKER_DISCOVERY/sc001_e008_maker_discovery_report.json`;
- the exact eight L2 archives already SHA-qualified by semantic integrity.

No Confirmation bodies are permitted.

## 3. Required market diagnostics

For each frozen Discovery day and pooled across eight days compute from reconstructed top-of-book states:

- time-weighted mean quoted spread in bps;
- time share with quoted spread >= 4 bps (maker-maker fee floor);
- time share with quoted spread >= 5 bps (4 bps fees + frozen +1 bps promotion hurdle);
- time share with quoted spread >= 7 bps (maker-taker fee floor);
- time share with spread <=1 bps and <=2 bps;
- snapshot count and cadence;
- best-bid and best-ask price-change counts;
- best-level size-increase events and aggregate increase quantity when price stays best;
- best-level size-decrease events and aggregate decrease quantity when price stays best;
- prior-best disappearance counts;
- top-of-book event churn rate.

Size changes are diagnostics of aggregate displayed size only; they must not be relabeled as exact FIFO cancellations or additions ahead/behind.

## 4. Required terminal-cycle diagnostics

From the frozen E008 terminal report only:

- primary cycle duration p50/p90/p99;
- gross-positive share and net-positive share;
- forced vs maker-only cycle counts/economics;
- long-first vs short-first gross/net economics;
- per-day gross/net means and forced-exit share.

No cycle may be recomputed or re-simulated.

## 5. Interpretation firewall

This stage may identify model-bias risks, including:
- all post-placement size additions being treated ahead despite price-time priority generally placing later orders behind an already-resting order;
- zero cancellation credit preventing queue-ahead improvement;
- hypothetical own order absent from exogenous historical book, so level disappearance can create artificial cancel/reset behavior;
- periodic snapshots being treated as order-cancel/resync events in the frozen E008 implementation;
- forced taker proxy using an arbitrary next public trade rather than executable same-side book depth;
- cross-feed same-ms ambiguity.

These findings do not alter the E008 terminal decision and do not authorize an E008 rerun.

## 6. Terminal token

Exact success token:

`E008_READONLY_MICROSTRUCTURE_FORENSIC_PASS`

PASS means diagnostics completed only. It is not a strategy PASS.

## 7. Next decision

Only after reviewing this forensic may SC001 open a new independent experiment family. Any new family must be predeclared and frozen before promotional outcomes are viewed. E008 remains closed permanently.
