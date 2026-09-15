# SC001 Current Roadmap and Stop Rules v1.7

Date: 2026-09-15  
Status: **CURRENT SC001 ROADMAP SNAPSHOT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v1.6.md`

## 1. Terminal history unchanged

- E001: terminal `FAIL`.
- E002 standalone: terminal `TAKER_ECONOMICS_FAIL`; TFI retained only as future auxiliary knowledge.
- E003: terminal `E003_DISCOVERY_FAIL`.
- E004: terminal `E004_DISCOVERY_FAIL`; read-only diagnostic postmortem complete.
- E005: remains closed because independently viable E004 prerequisite failed.

Q2, formal Validation and Final remain closed. SC001 remains independent from R009/R003/R010/S002.

## 2. Active next candidate

SC001-E006 — same-venue OKX `BTC-USDT` SPOT / `BTC-USDT-SWAP` transient basis dislocation -> convergence.

Active planning document:

`docs/research/sc001-e006-same-venue-spot-perp-basis-dislocation-research-plan-v0.2.md`

No E006 alpha is authorized.

## 3. Chronology correction frozen before SPOT body access

Metadata-only probing established D/D+1 archive-label behavior. Reconstructing Discovery UTC day March 20 requires archive label March 21, which physically contains part of March 21 UTC.

To preserve a clean later holdout:

- Discovery performance: 2024-03-01..20;
- March 21: boundary-neighbor only, permanently performance-excluded for E006;
- future one-time Confirmation candidate interval: 2024-03-22..30, only after a later frozen Discovery PASS;
- Q2/Validation/Final remain closed.

This is a source-boundary correction made before any E006 body download, basis, return or P&L.

## 4. Metadata probe result

Single-day metadata probe: `E006_SPOT_METADATA_PROBE_PASS`.

It established that the public OKX historical endpoint can identify exact `BTC-USDT` SPOT trade archives on trusted `static.okx.com` without downloading market-data bodies.

This is only source feasibility, not a data-stage PASS and not alpha evidence.

## 5. Current hard gate

Active frozen data-only protocol:

`docs/research/sc001-e006-spot-metadata-preflight-protocol-v0.1.md`

Next allowed action:

run `research/sc001/sc001_e006_spot_metadata_preflight.py` on the qualified VPS.

The preflight may inspect public metadata and HEAD only for archive labels 2024-03-01..21. It may record exact identity, host, Content-Length, aggregate expected bytes and disk feasibility.

It must not:

- download any ZIP body;
- calculate spot/perp basis;
- calculate convergence/returns/P&L;
- access L2;
- access Q2/Validation/Final.

Only terminal `E006_SPOT_METADATA_PREFLIGHT_PASS` permits design/freeze of the subsequent SPOT body-download/integrity stage.

## 6. After metadata PASS

Do not jump to alpha.

Sequence remains:

1. freeze SPOT body-download/integrity stage;
2. acquire only labels March 1..21;
3. hash/ZIP/schema/order/UTC reconstruction qualification;
4. causal spot/swap synchronization feasibility audit without basis/returns;
5. only after complete data PASS, perform final financial/mathematical audit;
6. freeze executable E006 protocol;
7. implementation preflight;
8. DEV-DISCOVERY;
9. unchanged protected Confirmation only after Discovery PASS;
10. paired L2 economics only after both gross stages PASS.

## 7. Economics firewall

E006 is a four-taker-fill paired cycle. Several-bps effects are economically irrelevant. Future gross promotion gates must require meaningful several-tens-of-bps headroom under an explicit paired normalization.

Base E006 must not use TFI, FLOW_IMPULSE, E004 compression, or post-hoc sign/day/hour selection.
