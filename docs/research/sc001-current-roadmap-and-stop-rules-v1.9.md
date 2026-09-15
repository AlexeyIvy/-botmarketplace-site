# SC001 Current Roadmap and Stop Rules v1.9

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v1.8.md`

## 1. Terminal history unchanged

- E001: terminal `FAIL`.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`; TFI retained only as future auxiliary knowledge.
- E003: terminal `E003_DISCOVERY_FAIL`.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only diagnostic postmortem complete.
- E005: closed because viable-E004 prerequisite failed.

Q2, formal Validation and Final remain closed. SC001 remains independent from R009/R003/R010/S002.

## 2. Active candidate

SC001-E006 — same-venue OKX `BTC-USDT` SPOT / `BTC-USDT-SWAP` transient basis dislocation -> convergence.

Active planning document:

`docs/research/sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.2.md`

No E006 alpha is authorized.

## 3. Qualified SPOT data stages

Completed:

- `E006_SPOT_METADATA_PROBE_PASS`;
- `E006_SPOT_METADATA_PREFLIGHT_PASS`;
- `E006_SPOT_BODY_INTEGRITY_PASS`.

Qualified SPOT facts:

- 21 archive labels 2024-03-01..21 acquired;
- 20/20 Discovery UTC days 2024-03-01..20 reconstructed successfully;
- March 21 remains boundary-neighbor only and performance-excluded;
- basis/returns/P&L not calculated;
- SWAP prices not compared;
- L2/Q2/Validation/Final remain closed.

## 4. Current hard gate: no-alpha SPOT/SWAP synchronization audit

Frozen protocol:

`docs/research/sc001-e006-spot-swap-synchronization-audit-protocol-v0.1.md`

Frozen implementation:

`docs/research/sc001-e006-spot-swap-sync-implementation-freeze-v0.1.md`

Executable:

`research/sc001/sc001_e006_spot_swap_sync_audit.py`

Next allowed action is only the no-alpha synchronization audit on the qualified VPS.

The stage may calculate timestamp-only availability facts:

- causal prior-trade availability;
- trade-age distributions;
- timestamp skew;
- paired availability shares at predeclared staleness caps.

It must not calculate or export:

- SPOT/SWAP prices;
- basis;
- convergence;
- returns;
- P&L;
- alpha;
- L2;
- Q2/Validation/Final.

Terminal tokens:

- `E006_SYNC_AUDIT_PASS`;
- `E006_SYNC_AUDIT_REVIEW`.

## 5. After synchronization PASS

A synchronization PASS does not authorize alpha.

Only then may SC001 perform the final pre-alpha financial/mathematical/programming audit and freeze the exact executable E006 protocol, including:

- synchronized causal price statistic;
- basis definition/normalization;
- trigger threshold;
- eligible sign(s) and borrow treatment;
- paired entry timing/legging rule;
- exit/maximum hold;
- turnover cap;
- paired gross-edge normalization;
- conservative several-tens-of-bps economics hurdle;
- robust Discovery/Confirmation gates;
- diagnostic neighborhood.

No price comparison or E006 return may be observed before that freeze and subsequent implementation preflight.

## 6. Chronology boundary

Frozen:

- Discovery performance: 2024-03-01..20;
- 2024-03-21: boundary-neighbor only, permanently excluded from E006 performance;
- future one-time Confirmation candidate interval: 2024-03-22..30 only after a later frozen Discovery PASS;
- Q2/Validation/Final remain closed.

## 7. Economics firewall

E006 is a four-taker-fill paired-cycle hypothesis. Several-bps effects are economically irrelevant. Future promotion gates must demand meaningful several-tens-of-bps headroom before any paired L2 work.

Base E006 must not use TFI, FLOW_IMPULSE, E004 compression or post-hoc basis sign/day/hour selection.

## 8. Infrastructure

Primary heavy compute remains the qualified Timeweb Cloud VPS: Ubuntu 24.04, 4 vCPU, 8 GB RAM, 80 GB NVMe, user `botmarket`, SSH key authentication, tmux.

Android/Termux is the control client. Never store credentials/IP/private keys in GitHub.
