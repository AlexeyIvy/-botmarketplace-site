# SC001 — Strategy Landscape v0.7

Date: 2026-09-18
Status: **CURRENT COVERAGE MAP AFTER C12-S0 / C11 RAW-HEADROOM SURVIVOR ONLY**
Supersedes: `sc001-strategy-landscape-v0.6.md`

## 1. Binding prior terminal states

All prior terminal decisions remain binding.

C1-C10 remain closed as previously documented.

C12-S0 is now terminal:

`C12_S0_REJECT_PARITY_REVERSION`

C11-S0 remains a structural survivor:

`C11_S0_EVENT_MOVE_HEADROOM_SURVIVE`

C11-S1 remains unresolved:

`C11_S1_DEFER_SAMPLE`

## 2. C12 — USDC-USDT parity dislocation/reversion

Frozen S0 terminal state:

`C12_S0_REJECT_PARITY_REVERSION`

Observed on H1-2025:

- target trading days: 181/181;
- six months represented;
- >=30 bps parity-stress episodes: 3;
- evaluable episodes: 3;
- successful <=10 bps reversion within 30m: 2;
- success share: ~66.7%;
- episode dates: 3;
- episode months: 1;
- median gross favorable reversion: ~25.94 bps;
- p75 gross favorable reversion: ~29.93 bps.

Coverage implication:

The exact direct-parity strategy had sufficient economic magnitude in the tiny observed sample but lacked opportunity frequency and regime breadth.

No threshold/hold/month rescue is authorized.

## 3. C12 reusable knowledge

Retain:

- direct external stablecoin cross-parity state;
- rare stablecoin stress regime;
- parity-band reversion as descriptive rare-event evidence.

The strongest robust conclusion is rarity/concentration, not the 2/3 success estimate.

## 4. C11 current position

C11 is the only new-generation base that passed broad structural headroom:

- 11/12 H1 macro events moved >=20 bps in 60s;
- median absolute move ~45.26 bps;
- p75 ~88.17 bps;
- max ~162.75 bps.

However the first frozen direction extractor:

`first 1-second impulse -> same-direction continuation`

could not produce a verdict because one of 12 events had an exactly zero first impulse.

No 11-event subset verdict is allowed.

## 5. Current research frontier

The main open problem is no longer:

`is there enough raw movement?`

For C11, raw movement is established.

The open problem is:

`can a prospectively defined causal direction rule extract economically usable post-entry movement without rescue tuning?`

This is a materially narrower and better-defined research question.

## 6. Current hard gate

Before any new C11 directional outcome:

1. design a new direction rule prospectively;
2. explicitly support a no-trade state;
3. choose a fresh chronology not used for the H1 C11 direction decision;
4. freeze sample/continuation gates;
5. preserve H1 as contaminated design evidence.

No new C13+ base candidate is needed while C11 remains a live unresolved survivor.
