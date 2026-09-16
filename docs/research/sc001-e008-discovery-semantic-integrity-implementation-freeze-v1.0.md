# SC001-E008 — Discovery Semantic Integrity Implementation Freeze v1.0

Date: 2026-09-16  
Status: **FROZEN BEFORE FIRST SEMANTIC QUALIFICATION RUN**

Parent protocol:
`docs/research/sc001-e008-discovery-semantic-integrity-protocol-v1.0.md`

Frozen repository changes:
- protocol commit: `c784cbe1a16b8de154a1433ff47401fc3c7d2398`;
- runner commit: `dd2d49b6f6d54cf4d4e923fbbe0b86004da6af4a`;
- runner: `research/sc001/sc001_e008_discovery_semantic_integrity.py`.

## Frozen semantics

The runner may only:
- consume the exact 24 files already accepted by `E008_DISCOVERY_ACQUISITION_VERIFY_PASS`;
- reconstruct each target UTC trade day from exact+D+1 trade archives;
- run full semantic L2 replay on the eight frozen Discovery dates;
- write per-day data-quality checkpoints and one aggregate integrity report;
- report L2 gaps >5 s as diagnostics only.

It may not:
- place maker orders;
- simulate fills;
- calculate spread capture, markout, fees, inventory P&L or profitability;
- access Confirmation bodies;
- access Q2 / formal Validation / Final;
- alter the already-frozen Discovery dates or maker strategy rules.

## Allowed modes

- `preflight` — report/identity/path gate only; no full market-data replay;
- `run` — full semantic qualification of all eight frozen Discovery days.

## Terminal states

Preflight:
`E008_DISCOVERY_SEMANTIC_PREFLIGHT_PASS`

Full run:
- `E008_DISCOVERY_SEMANTIC_INTEGRITY_PASS`;
- `E008_DISCOVERY_SEMANTIC_INTEGRITY_REVIEW`.

Only exact full PASS may open the separate maker-engine implementation/preflight stage. It does not itself authorize maker P&L.