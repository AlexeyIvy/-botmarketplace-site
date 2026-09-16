# SC001-E008 — Real-Data Mechanical Validation Implementation Freeze v0.1

Date: 2026-09-16  
Status: **IMPLEMENTATION FROZEN BEFORE REAL-DATA MECHANICAL RUN**

Parent protocol:
`docs/research/sc001-e008-realdata-mechanical-validation-protocol-v0.1.md`

Frozen implementation:
`research/sc001/sc001_e008_realdata_mechanical_validation.py`

Git blob identities at freeze:
- protocol blob SHA: `39256e342416a9bde1af5cda8478424e05cf1220`;
- runner blob SHA: `f22b4fb019f20439a1808e0da4ee84e5e263b074`.

Upstream mechanics dependencies remain:
- `research/sc001/sc001_e008_queue_audit_lib.py`;
- `research/sc001/sc001_e008_queue_simulator_synthetic_v0_1.py`;
- fail-closed stale-latch semantics v0.2.

Frozen engineering constants:
- exactly four contaminated Q009A/Q009B days;
- 96 scheduled probes/day, 15-minute spacing;
- alternating BUY/SELL by slot index;
- quantity 1.0 historical size unit;
- max placement lag 1,000 ms;
- TTL 60,000 ms;
- stale threshold 5,000 ms;
- full-displayed-size initial queue-ahead;
- cancellation/size decrease gives zero queue progress;
- displayed-size additions are pessimistically added ahead;
- same-ms ambiguity gives zero credit;
- level disappearance/book movement alone never implies fill;
- full snapshot while live cancels the unresolved probe before resync;
- stale latch cancels live probe and only a later snapshot restores trust.

No spread capture, markout, fees/rebates, inventory P&L, profitability, TFI, Q2, Validation or Final may be calculated in this stage.

Only exact `E008_QUEUE_SIMULATOR_MECHANICAL_PASS` allows the project to move to untouched Discovery-date selection and a separately frozen profitability protocol. A REVIEW authorizes only implementation/data-model investigation, not parameter relaxation.
