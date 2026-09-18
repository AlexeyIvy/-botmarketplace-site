# SC001 — C7-S0 Spread Headroom Result & Read-Only Postmortem v0.1

Date: 2026-09-18
Status: **C7_S0_REJECT_SPREAD_HEADROOM — 7/7 DATA ADEQUATE / ZERO ELIGIBLE ASSETS**
Scope: `SCALPING RESEARCH / SC001`

## 1. Execution integrity

Exact terminal state:

`C7_S0_REJECT_SPREAD_HEADROOM`

Technical completion:

- exit code: `0`;
- data gates passed: `7 / 7`;
- eligible assets: `0 / 7`;
- frozen 10 bps quoted-spread hurdle preserved;
- frozen 5-second persistence rule preserved;
- frozen universe preserved;
- no maker-order simulation, fill model, queue model, adverse-selection outcome or PnL;
- no promotional alpha accessed.

## 2. Per-asset structural evidence

Frozen non-BTC universe:

### ETH-USDT-SWAP
- data gate: PASS;
- p75 quoted spread: about `0.0401 bps`;
- share of seconds >=10 bps: `0`;
- persistent >=5s high-spread episodes: `0`;
- eligible: false.

### DOGE-USDT-SWAP
- data gate: PASS;
- p75 quoted spread: about `1.2482 bps`;
- share >=10 bps: `0`;
- persistent episodes: `0`;
- eligible: false.

### ORDI-USDT-SWAP
- data gate: PASS;
- p75 quoted spread: about `0.1637 bps`;
- share >=10 bps: about `1.16e-5`;
- persistent episodes: `0`;
- eligible: false.

### UNI-USDT-SWAP
- data gate: PASS;
- p75 quoted spread: about `1.5336 bps`;
- share >=10 bps: about `1.16e-5`;
- persistent episodes: `0`;
- eligible: false.

### XRP-USDT-SWAP
- data gate: PASS;
- p75 quoted spread: about `1.9270 bps`;
- share >=10 bps: `0`;
- persistent episodes: `0`;
- eligible: false.

### OP-USDT-SWAP
- data gate: PASS;
- p75 quoted spread: about `0.2842 bps`;
- share >=10 bps: `0`;
- persistent episodes: `0`;
- eligible: false.

### BCH-USDT-SWAP
- data gate: PASS;
- p75 quoted spread: about `3.6758 bps`;
- share >=10 bps: about `1.16e-5`;
- persistent episodes: `0`;
- eligible: false.

## 3. Economic interpretation

Primary failure class:

`AMPLE_DATA_NO_MULTI_ASSET_PASSIVE_HYBRID_SPREAD_HEADROOM`

The exact C7 structural architecture:

- non-BTC multi-asset OKX universe;
- maker entry;
- taker fail-safe exit;
- 2 bps maker fee reference;
- 5 bps taker fee reference;
- 3 bps model/adverse reserve;
- 10 bps gross quoted-spread hurdle;

has no structural headroom on the frozen calibration day.

The gap is decisive:

- all p75 spreads are far below 10 bps;
- the largest observed p75 among the seven is only about 3.68 bps;
- >=10 bps spread states are effectively absent;
- zero asset has even one persistent 5-second high-spread episode.

Queue/fill engineering cannot create missing quoted-spread headroom.

## 4. No-rescue rule

Do not:

- lower 10 bps after outcome;
- drop the maker+taker hybrid architecture;
- switch to maker-maker because hybrid failed;
- add BTC;
- select only BCH/XRP/UNI because their p75 is relatively larger;
- change date;
- select sparse one-second >=10 bps observations;
- proceed to queue/fill simulation for this exact C7 mechanism.

A materially different maker mechanism requires a new independent candidate ID and prospective architecture.

## 5. Feature-level interpretation

C7-S0 still contributes useful reference knowledge:

- quoted spread is a valid R2/R6 state feature;
- persistent high-spread regime is measurable but essentially absent under a 10 bps definition across the frozen liquid non-BTC universe;
- the non-BTC perpetual markets examined are generally too tight for a simple maker-entry/taker-exit spread-capture thesis under the conservative structural reserve.

This does not imply passive execution is globally useless; it rejects this particular economic mechanism.

## 6. Evidence disposition

C7-S0:

`REJECT_SPREAD_HEADROOM`

No queue/fill/adverse-selection stage.
No MDE/promotional Discovery.
No PnL.

## 7. Slate consequence

The frozen C7-C10 next-slate has now completed:

- C9-S1: rejected;
- C8B-S0: rejected;
- C10-S0: rejected;
- C7-S0: rejected.

No candidate from this slate survives to execution/promotion.

The next action should be a non-alpha synthesis across strategy and feature evidence before defining any new candidate IDs.
