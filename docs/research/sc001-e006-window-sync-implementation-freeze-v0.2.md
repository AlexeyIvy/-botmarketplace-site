# SC001-E006 — Window Synchronization Implementation Freeze v0.2

Date: 2026-09-15  
Status: **FROZEN BEFORE v0.2 DATA-ONLY AUDIT OUTPUT**

Parent protocol:

`docs/research/sc001-e006-spot-swap-window-sync-audit-protocol-v0.2.md`

## Frozen executable

`research/sc001/sc001_e006_spot_swap_window_sync_audit_v0_2.py`

Git blob SHA:

`76f7dd34a689aa97cff433a97a2e8acdcd2fe60c`

The script imports only timestamp/integrity helpers from the already-frozen v0.1 synchronization implementation and does not alter the v0.1 result.

## Frozen semantics

- target days: 2024-03-01..20;
- required local labels: 2024-03-01..21;
- March 21 boundary-only/performance-excluded;
- exact 10-second UTC boundaries;
- last trade strictly before boundary;
- fresh10 iff both leg ages are >0 and <=10,000 ms;
- pooled fresh10 share gate >=99.0%;
- every-day fresh10 share gate >=98.0%;
- pooled p99 max-leg age <=10,000 ms;
- causal prior-pair availability >=99.99%;
- no price/basis/return/P&L/alpha/L2/Q2/Validation/Final output.

Any implementation change after first v0.2 audit output requires a new implementation identity and cannot retroactively alter the v0.2 result.
