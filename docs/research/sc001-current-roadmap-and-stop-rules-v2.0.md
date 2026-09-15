# SC001 Current Roadmap and Stop Rules v2.0

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v1.9.md`

## 1. Terminal history unchanged

- E001: terminal `FAIL`.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`.
- E003: terminal `E003_DISCOVERY_FAIL`.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only postmortem complete.
- E005 remains closed.

SC001 remains independent from R009/R003/R010/S002. Q2/Validation/Final remain closed.

## 2. Active candidate

SC001-E006 — same-venue OKX `BTC-USDT` SPOT / `BTC-USDT-SWAP` transient basis dislocation -> convergence.

No E006 price comparison or alpha is authorized.

## 3. Qualified upstream data

Completed:

- `E006_SPOT_METADATA_PROBE_PASS`;
- `E006_SPOT_METADATA_PREFLIGHT_PASS`;
- `E006_SPOT_BODY_INTEGRITY_PASS`.

SPOT labels 2024-03-01..21 and SWAP labels 2024-03-01..21 are local/qualified for Discovery data engineering only. March 21 is boundary-only and performance-excluded.

## 4. Synchronization audit v0.1 result

Frozen 1-second as-of synchronization audit completed:

`E006_SYNC_AUDIT_REVIEW`

Recorded in:

`docs/research/sc001-e006-sync-audit-v0.1-results-and-decision.md`

Timestamp-only facts:

- causal prior-pair availability about 99.99994%;
- pooled p99 max-leg age 5,991 ms;
- both-leg age <=1,000 ms share about 67.4%;
- both-leg age <=5,000 ms share about 98.28%.

The v0.1 result remains REVIEW and is not relaxed/relabelled.

No prices/basis/returns/P&L/alpha were calculated.

## 5. Current hard gate: window synchronization audit v0.2

Frozen protocol:

`docs/research/sc001-e006-spot-swap-window-sync-audit-protocol-v0.2.md`

Frozen implementation:

`docs/research/sc001-e006-window-sync-implementation-freeze-v0.2.md`

Executable:

`research/sc001/sc001_e006_spot_swap_window_sync_audit_v0_2.py`

The v0.2 audit tests only timestamp availability on exact 10-second UTC boundaries, with a frozen `fresh10` rule requiring a causal print from each leg no older than 10 seconds.

It must not calculate/export any prices, basis, convergence, returns, P&L or alpha.

Terminal tokens:

- `E006_WINDOW_SYNC_AUDIT_PASS`;
- `E006_WINDOW_SYNC_AUDIT_REVIEW`.

## 6. v0.2 stop rule

If v0.2 returns REVIEW, do not continue progressively loosening synchronization on the same data. Pause/stop E006 before price comparison unless a genuinely new data source or materially different pre-alpha data model is justified independently.

If v0.2 PASSes, alpha is still closed. The next step is the final pre-alpha financial/mathematical/programming audit and freeze of the exact E006 executable protocol.

## 7. Chronology

- Discovery performance candidate days: 2024-03-01..20;
- March 21: boundary-neighbor only/performance-excluded;
- future Confirmation candidate days: 2024-03-22..30 only after a later frozen Discovery PASS;
- Q2/Validation/Final remain closed.

## 8. Economics firewall

E006 is a four-taker-fill paired-cycle hypothesis. Several-bps effects are not economically relevant. Before first alpha, the executable protocol must freeze a conservative several-tens-of-bps gross promotion hurdle under explicit paired normalization.

Base E006 may not use TFI, FLOW_IMPULSE, E004 compression, or post-hoc basis sign/day/hour selection.
