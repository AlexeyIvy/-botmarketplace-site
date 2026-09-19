# SC001 — C11 v2 Direction-Retention Read-Only Postmortem Result v0.1

Date: 2026-09-19
Status: **C11_V2_DIRECTION_RETENTION_READONLY_POSTMORTEM_PASS**
Scope: `SCALPING RESEARCH / SC001`

Parent terminal state:

`C11_V2_SC_REJECT_DIRECTION_RETENTION`

## 1. Classification

Primary classification:

`RESIDUAL_HEADROOM_EXISTS_DIRECTION_CAPTURE_WEAK`

Failure structure:

`FAILURE_CONCENTRATED_IN_WRONG_SIGN`

## 2. Core observations

- scheduled events = 24;
- actionable events = 24;
- positive signed continuation share = 14/24 = ~58.33%;
- median absolute first 1-second impulse = ~1.6398 bps;
- large residual events with abs +1s -> +60s move >=20 bps = 14.

Among those 14 large-residual events:

- signed continuation >=20 bps = 6;
- same-sign but <20 bps = 0;
- wrong-or-zero sign = 8;
- capture share among large residual events = 6/14 = ~42.86%.

Interpretation:

The frozen Direction Rule v2 does not primarily fail because correctly signed continuation is too small.

It fails because the first one-second impulse frequently points in the wrong direction relative to the larger residual move.

## 3. Family descriptives

### CPI

- actionable = 12;
- median signed continuation = ~-12.1359 bps;
- positive signed count = 6/12;
- signed continuation >=20 bps = 3/12.

### Employment

- actionable = 12;
- median signed continuation = ~+13.8280 bps;
- positive signed count = 8/12;
- signed continuation >=20 bps = 3/12.

These differences are descriptive only.

They do not authorize:

- CPI reversal;
- Employment continuation;
- family-specific strategy rules;
- family-specific threshold changes.

## 4. Boundaries preserved

The postmortem did not:

- test another impulse window;
- score reversal;
- test another threshold;
- test another continuation horizon;
- use macro surprise;
- calculate execution/PnL;
- open Confirmation.

## 5. Robust lesson

The first causal one-second move is very small in median magnitude (~1.64 bps) relative to the structural burden and relative to the residual event movement.

Large post-decision movement remains available, but the sign of that tiny first impulse is not a sufficiently reliable direction extractor.

This cleanly separates:

`event opportunity scale`

from:

`direction feature quality`.
