# SC001 Current Roadmap and Stop Rules v2.1

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v2.0.md`

## 1. Terminal history unchanged

- E001: terminal `FAIL`.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`.
- E003: terminal `E003_DISCOVERY_FAIL`.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only postmortem complete.
- E005 remains closed.

SC001 remains independent from R009/R003/R010/S002. Q2/Validation/Final remain closed.

## 2. Active candidate

SC001-E006 — same-venue OKX `BTC-USDT` SPOT / `BTC-USDT-SWAP` positive basis dislocation -> convergence.

No E006 alpha has yet been authorized or observed.

## 3. Data qualification complete for Discovery

Completed:

- `E006_SPOT_METADATA_PROBE_PASS`;
- `E006_SPOT_METADATA_PREFLIGHT_PASS`;
- `E006_SPOT_BODY_INTEGRITY_PASS`;
- v0.1 one-second sync = `E006_SYNC_AUDIT_REVIEW` (retained as REVIEW);
- v0.2 ten-second window sync = `E006_WINDOW_SYNC_AUDIT_PASS`.

v0.2 result record:

`docs/research/sc001-e006-window-sync-audit-v0.2-results-and-decision.md`

Qualified chronology:

- Discovery performance: 2024-03-01..20;
- 2024-03-21 boundary/warm-up only, permanently excluded from E006 performance;
- future Confirmation candidate interval: 2024-03-22..30 only after Discovery PASS.

## 4. Frozen E006 financial protocol

Canonical executable protocol:

`docs/research/sc001-e006-spot-perp-basis-convergence-executable-protocol-v1.0.md`

Primary identifier:

`E006_POSBASIS_G10_VWAP10_LB6H_TRIG50_EXIT10_LAT500_H30_CAP4`

Frozen primary mechanism:

- LONG BTC-USDT spot / SHORT BTC-USDT-SWAP only;
- 10-second causal `[t-10s,t)` size-weighted VWAP per leg;
- basis `10,000*(perp/spot-1)` bps;
- prior six-hour median ordinary-basis baseline;
- minimum 95% valid prior grid observations;
- below-to-at/above +50 bps dislocation crossing;
- baseline frozen at trigger;
- 500 ms primary entry/exit proxy latency;
- 5-second per-leg proxy tolerance;
- convergence exit <=+10 bps to frozen baseline or 30-minute max hold;
- one pair maximum;
- 10-minute cooldown;
- maximum four entry decisions/day;
- no new entry after 23:29 UTC;
- no overnight carry;
- 1,000/2,000 ms latency stresses reuse primary decisions;
- paired gross edge normalized to one reference-leg notional.

## 5. Economics hurdle

Prior regular-user reference implies approximately 20 bps four-taker-fill fee burden per one-leg-normalized paired cycle before spread/depth/legging/funding effects.

Discovery therefore requires materially larger gross economics:

- pooled mean >=40 bps;
- trimmed mean >=35 bps;
- median >=25 bps;
- median active-day mean >=30 bps;
- positive active-day breadth >=70%;
- day-block bootstrap lower bound >20 bps;
- concentration and latency-stress gates;
- minimum 20 completed pairs / 10 active days;
- completion >=98%.

A few-bps paired effect is automatically a failure.

## 6. Current hard gate: implementation preflight

Frozen preflight spec:

`docs/research/sc001-e006-implementation-preflight-spec-v1.0.md`

Frozen implementation:

`docs/research/sc001-e006-implementation-freeze-v1.0.md`

Executable set:

- `research/sc001/sc001_e006_config_v1_0.json`;
- `research/sc001/sc001_e006_basis_convergence_v1.py`;
- `research/sc001/sc001_e006_preflight_v1_0.py`.

Development-side synthetic audit passed 30/30 implemented checks. This is not the authoritative VPS preflight.

Only exact terminal token:

`E006_PREFLIGHT_PASS`

with matching engine/config SHA256 authorizes one DEV-DISCOVERY run.

## 7. If preflight FAILs

- do not run Discovery;
- fix only implementation/data-audit defects;
- financial formula, sign, thresholds, baseline, exits and gates remain frozen;
- rerun the complete preflight with a new implementation identity if code changes.

## 8. If preflight PASSes

Run one frozen DEV-DISCOVERY on 2024-03-01..20.

Any failed primary gate => terminal `E006_DISCOVERY_FAIL`; no Confirmation/L2/rescue.

Only exact `E006_DISCOVERY_PASS_OPEN_CONFIRMATION_ONCE` opens unchanged Confirmation 2024-03-22..30.

## 9. Firewalls

Base E006 must not use:

- TFI;
- FLOW_IMPULSE;
- E004 compression;
- negative-basis/borrow-required sign;
- event/day/hour exclusions;
- maker/lower-fee assumptions;
- Q2/Validation/Final.
