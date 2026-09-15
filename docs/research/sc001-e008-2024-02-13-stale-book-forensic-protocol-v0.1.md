# SC001-E008 — 2024-02-13 Stale-Book Forensic Audit Protocol v0.1

Date: 2026-09-15  
Status: **FROZEN READ-ONLY DATA FORENSIC — NO FILLS / NO P&L**

Parent result: `E008_QUEUE_MODEL_FEASIBILITY_REVIEW`.

## Purpose

Explain the 2024-02-13 failure of the frozen `age <= 5,000 ms` queue-feasibility gate without weakening or relabelling that gate.

## Scope

Use only already-qualified local 2024-02-13 `BTC-USDT-SWAP` L2 and transaction tapes.

No hypothetical orders, queue progress, fills, spread capture, inventory, markout after hypothetical fill, fees/rebates, P&L or profitability.

## Frozen diagnostics

For every non-same-ms trade with a strictly prior valid book state, calculate only timestamp facts:

- prior-book age;
- shares with age <=1s, <=5s, <=10s, <=30s, <=60s;
- p50/p95/p99/p99.9/max book age;
- count/share of trades with age >5s;
- contiguous stale episodes, where successive >5s trades separated by <=10s belong to one episode;
- for each stale episode: first/last trade timestamp, trade count, maximum book age;
- top 10 stale episodes by trade count and by maximum age;
- L2 inter-state gap p95/p99/p99.9/max and count of gaps >5s, >10s, >30s, >60s;
- overlap between >5s trade-age observations and L2 inter-state gaps.

## Interpretation categories

- `CONCENTRATED_SOURCE_GAPS`: >=90% of >5s stale trades occur inside the top 10 stale episodes and those episodes coincide with explicit L2 inter-state gaps >5s.
- `DISTRIBUTED_STALENESS`: otherwise.

These categories are descriptive only. Neither category converts queue-feasibility v0.1 to PASS.

## Firewalls

- fills calculated = false;
- queue progress calculated = false;
- spread capture calculated = false;
- inventory calculated = false;
- P&L/profitability calculated = false;
- TFI used = false;
- Q2 / Validation / Final closed.
