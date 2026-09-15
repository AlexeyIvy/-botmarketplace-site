# SC001-E006 — Implementation Freeze v1.0

Date: 2026-09-15  
Status: **IMPLEMENTATION FROZEN BEFORE REAL-DATA PREFLIGHT / BEFORE ANY E006 PRICE COMPARISON**

Parent protocol:

`docs/research/sc001-e006-spot-perp-basis-convergence-executable-protocol-v1.0.md`

Preflight spec:

`docs/research/sc001-e006-implementation-preflight-spec-v1.0.md`

No E006 real-data SPOT/SWAP price comparison, basis, dislocation, paired return, P&L or alpha had been emitted before this freeze.

## 1. Frozen executable set

Complete current implementation set is present by commit:

`a415df999380e590c00c0978c9e928284d283ff6`

Files and Git blob identities:

- `research/sc001/sc001_e006_config_v1_0.json`
  - Git blob SHA: `1e0ab236fa1839a008586df875aa0e64a7842825`
- `research/sc001/sc001_e006_basis_convergence_v1.py`
  - Git blob SHA: `a4e37f4bd0bff9c16c3746c7b73b107d704b9500`
- `research/sc001/sc001_e006_preflight_v1_0.py`
  - Git blob SHA: `71857381c5fd537f8f1b422296a5c5284448a772`

The authoritative runtime SHA256 values must be computed by the VPS preflight report. Discovery is fail-closed unless the report contains exact `E006_PREFLIGHT_PASS` and matching engine/config SHA256.

## 2. Frozen financial semantics

Primary identifier:

`E006_POSBASIS_G10_VWAP10_LB6H_TRIG50_EXIT10_LAT500_H30_CAP4`

Frozen:

- primary sign: rich perpetual only;
- position: LONG BTC-USDT spot / SHORT BTC-USDT-SWAP;
- 10-second UTC grid;
- causal `[t-10s,t)` size-weighted VWAP on each leg;
- basis = `10,000 * (perp_vwap/spot_vwap - 1)` bps;
- rolling prior six-hour median baseline;
- 2,160 scheduled lookback points;
- minimum 2,052 valid prior observations;
- strict below-to-at/above +50 bps dislocation crossing;
- frozen baseline at trigger;
- 500 ms primary entry/exit proxy latency;
- 5-second per-leg proxy tolerance;
- convergence exit at <=+10 bps to frozen baseline;
- 30-minute maximum hold;
- 10-minute cooldown;
- maximum four entry decisions per UTC day;
- no new entry after 23:29 UTC;
- maximum one pair;
- no overnight carry;
- 1,000/2,000 ms latency stresses reuse primary signal/exit-decision events;
- paired gross edge normalized to one reference-leg notional;
- Discovery gross mean hurdle 40 bps plus robust median/trimmed/day/bootstrap/concentration/stress gates.

## 3. Primary sign rationale

The negative-basis sign is excluded before alpha because monetizing it would require short/borrow spot BTC or an inventory assumption. E006 v1.0 therefore tests only the directly implementable positive-basis convergence sign.

This is not outcome-driven sign selection.

## 4. Preflight boundary

Development-side synthetic audit passed `30/30` implemented checks before this freeze.

That result is not the authoritative preflight.

The qualified VPS must still run the complete v1.0 preflight against real local Discovery inputs with real-data basis/returns/P&L suppressed.

Only exact:

`E006_PREFLIGHT_PASS`

authorizes one frozen DEV-DISCOVERY run.

## 5. Firewalls

Until preflight PASS:

- no E006 Discovery;
- no Confirmation;
- no E006 L2;
- no Q2/Validation/Final;
- no TFI/FLOW_IMPULSE/E004 filtering;
- no opposite-sign exploration;
- no parameter changes based on data-stage counts.
