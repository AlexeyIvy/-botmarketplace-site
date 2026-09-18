# SC001 — Feature Evidence Registry v0.6

Date: 2026-09-18
Status: **APPEND-ONLY CONTINUATION AFTER C7-S0**
Parent: `sc001-feature-evidence-registry-v0.5.md`

## 1. Inheritance

All prior feature-evidence records remain unchanged and binding.

New evidence role:

`SELECTION_CALIBRATION_ONLY`

## 2. New records

### F023 — Quoted spread state across non-BTC OKX perpetuals

- primitive family: P6/P8 execution-state;
- source: C7-S0;
- universe: ETH/DOGE/ORDI/UNI/XRP/OP/BCH USDT perpetuals;
- date: 2024-02-12;
- role: R2 market/execution state + R6 reference;
- measurement validity: established from causal 1-second L2 top-of-book normalization;
- p75 spread scale by asset:
  - ETH ~0.0401 bps;
  - DOGE ~1.2482 bps;
  - ORDI ~0.1637 bps;
  - UNI ~1.5336 bps;
  - XRP ~1.9270 bps;
  - OP ~0.2842 bps;
  - BCH ~3.6758 bps;
- classification: `REFERENCE_PRIMITIVE_TIGHT_SPREAD_REGIME`;
- allowed conclusion: quoted spread is causally measurable and the frozen liquid non-BTC universe was overwhelmingly sub-10-bps under the calibration day;
- forbidden claim: passive execution is globally unprofitable.

### F024 — Persistent high-spread regime

- primitive family: P6/P10;
- source: C7-S0;
- definition tested: quoted spread >=10 bps for >=5 consecutive valid seconds;
- role: R2/R4 execution-eligibility state;
- observed:
  - persistent episode count = 0 for every frozen asset;
  - episode-hour breadth = 0 for every frozen asset;
  - seconds >=10 bps were zero or effectively zero;
- classification: `NEGATIVE_STRUCTURAL_EVIDENCE_AT_10BPS`;
- allowed conclusion: a persistent 10-bps spread regime was absent across the seven frozen non-BTC markets on the calibration day;
- forbidden reuse: lower the spread threshold after outcome under C7-S0.
