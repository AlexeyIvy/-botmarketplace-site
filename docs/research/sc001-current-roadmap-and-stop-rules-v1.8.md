# SC001 Current Roadmap and Stop Rules v1.8

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v1.7.md`

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

## 3. Chronology boundary

Frozen before any E006 SPOT body access:

- Discovery performance: 2024-03-01..20;
- 2024-03-21: D+1 boundary-neighbor only, permanently performance-excluded;
- future one-time Confirmation candidate interval: 2024-03-22..30, only after a later frozen Discovery PASS;
- Q2/Validation/Final remain closed.

## 4. Metadata stages complete

Single-day probe: `E006_SPOT_METADATA_PROBE_PASS`.

Full-label metadata-only preflight: `E006_SPOT_METADATA_PREFLIGHT_PASS`.

Qualified metadata facts:

- exact 21 SPOT archive labels 2024-03-01..21 resolved on trusted `static.okx.com`;
- expected total compressed body bytes: `143,891,245`;
- disk feasibility PASS on the qualified VPS;
- March 21 marked boundary-only;
- no market-data body downloaded during metadata stages;
- basis/returns/P&L not calculated.

## 5. Current hard gate: SPOT body integrity

Frozen data-only protocol:

`docs/research/sc001-e006-spot-body-integrity-protocol-v0.1.md`

Frozen implementation:

`research/sc001/sc001_e006_spot_body_integrity.py`

Next allowed action is only:

`python3 -u research/sc001/sc001_e006_spot_body_integrity.py download`

The stage may:

- download/reuse/resume only the 21 frozen SPOT ZIP identities;
- compute SHA256;
- verify ZIP CRC/member/header/schema;
- verify source timestamp/trade-ID ordering;
- reconstruct UTC Discovery days 2024-03-01..20 using Q006R-style D + D+1 semantics;
- record minute/second coverage and gap diagnostics.

It must not:

- compare SPOT prices with SWAP prices;
- calculate basis;
- calculate convergence, returns or P&L;
- access L2;
- access labels after March 21;
- access Q2/Validation/Final.

Terminal PASS token:

`E006_SPOT_BODY_INTEGRITY_PASS`

## 6. A body-integrity PASS still does not authorize alpha

After body PASS, the next mandatory stage is a separately frozen **no-alpha SPOT/SWAP synchronization-feasibility audit**.

That audit must establish causal timestamp alignment, stale-print/gap behavior and paired observation availability without computing relative prices, basis, convergence or returns.

Only after complete data qualification may we perform the final financial/mathematical audit and freeze the E006 executable protocol.

## 7. Economics firewall

E006 remains a four-taker-fill paired-cycle hypothesis. Several-bps effects are economically irrelevant. Event definition and eventual promotion hurdles must be frozen before first E006 alpha and must demand meaningful several-tens-of-bps headroom.

Base E006 must not use TFI, FLOW_IMPULSE, E004 compression or post-hoc basis sign/day/hour selection.

## 8. Infrastructure

Primary heavy compute: qualified Timeweb Cloud VPS, Ubuntu 24.04, 4 vCPU, 8 GB RAM, 80 GB NVMe, user `botmarket`, SSH key auth, tmux.

Android/Termux is the control client. Never store credentials/IP/private keys in GitHub.
