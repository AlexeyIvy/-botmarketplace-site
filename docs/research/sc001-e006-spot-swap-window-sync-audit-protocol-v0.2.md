# SC001-E006 — SPOT/SWAP Window Synchronization Audit Protocol v0.2

Date: 2026-09-15  
Status: **FROZEN DATA-ONLY / NO-ALPHA PROTOCOL**

Parent result: `docs/research/sc001-e006-sync-audit-v0.1-results-and-decision.md`

## 1. Purpose

Test whether qualified OKX `BTC-USDT` SPOT and `BTC-USDT-SWAP` trade tapes support a causal coarse synchronization representation suitable for later relative-value research without calculating prices, basis, convergence, returns or P&L.

The v0.1 one-second as-of audit remains terminal `E006_SYNC_AUDIT_REVIEW` and is not altered.

## 2. Inputs and chronology

Use only already-qualified local archive labels 2024-03-01..21 for both legs.

Target UTC audit days: 2024-03-01..20.

2024-03-21 remains boundary-neighbor only and permanently performance-excluded.

No network acquisition, L2, Q2, Validation or Final access is permitted.

## 3. Price firewall

The implementation must not parse prices into synchronization calculations and must not calculate/export:

- SPOT/SWAP prices;
- ratios/differences;
- basis;
- convergence;
- signed flow features;
- future response;
- returns;
- P&L;
- alpha.

Only timestamp/trade-ID identity and availability facts are allowed.

## 4. UTC reconstruction

For each target day D and each leg independently:

- reconstruct from archive labels D and D+1;
- retain only timestamps in `[D 00:00:00.000, D+1 00:00:00.000)` UTC;
- preserve duplicate timestamps in source order;
- require nondecreasing admitted timestamps;
- require zero duplicate/backward trade IDs;
- require all 1,440 UTC minutes represented.

## 5. Frozen v0.2 synchronization representation

Evaluation grid: exact UTC 10-second boundaries strictly inside each day:

`00:00:10, 00:00:20, ..., 23:59:50`.

For each boundary `t`, independently select the last admitted trade timestamp strictly before `t` for SPOT and SWAP.

A leg is `fresh10` only when:

`0 < t - last_trade_timestamp <= 10,000 ms`.

A grid point is `paired_fresh10` only when both legs are fresh10.

This is equivalent to requiring at least one causal print from each leg in the trailing half-open interval `[t-10s, t)`.

No trade at or after `t` may be used.

## 6. Required diagnostics

Per day and pooled report:

- total 10-second grid points;
- prior-trade availability share;
- paired_fresh10 count/share;
- SPOT age p50/p95/p99/max;
- SWAP age p50/p95/p99/max;
- max-leg-age p50/p95/p99/max;
- timestamp-skew p50/p95/p99/max;
- share where both leg ages <=2,000 ms;
- <=5,000 ms;
- <=10,000 ms;
- <=20,000 ms diagnostics.

No diagnostic can redefine the frozen primary `fresh10` rule after output.

## 7. Feasibility gates

Terminal `E006_WINDOW_SYNC_AUDIT_PASS` requires all:

1. upstream SPOT body-integrity status exactly `E006_SPOT_BODY_INTEGRITY_PASS`;
2. upstream SWAP March source status exactly PASS with protected-data/alpha firewalls intact;
3. exact required local identities for both legs exist for labels March 1..21;
4. all 20 UTC target days reconstruct on both legs with 1,440/1,440 minute coverage and ordering invariants;
5. causal prior-trade availability share pooled >= 99.99%;
6. pooled `paired_fresh10` share >= 99.0%;
7. every individual day `paired_fresh10` share >= 98.0%;
8. pooled p99 `max_leg_age_ms` <= 10,000 ms;
9. zero forbidden price/basis/return/P&L/alpha output;
10. no labels after March 21 and no L2/Q2/Validation/Final access.

Any failure yields `E006_WINDOW_SYNC_AUDIT_REVIEW`.

## 8. Stop rule

A v0.2 REVIEW does not authorize another progressively looser synchronization grid on the same data. E006 should pause/stop before price comparison unless a genuinely new data source or materially different pre-alpha data model is justified independently.

A PASS means only that a causal 10-second paired-tape representation is data-feasible. It still does not authorize alpha.

## 9. Next step after PASS

Only after PASS may SC001 perform the final pre-alpha financial/mathematical/programming audit and freeze the exact E006 executable protocol, including price statistic, basis formula, normalization, trigger, paired execution, exit and several-tens-of-bps economics gates.
