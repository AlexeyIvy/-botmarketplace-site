# SC001 — B13-B D0 Launch-Event Source Census PASS Result v0.1

Date: 2026-09-19
Status: **B13B_D0_SOURCE_FEASIBILITY_PASS_SURVIVOR_CENSORED**
Scope: `SCALPING RESEARCH / SC001`

## 1. Exact terminal state

`B13B_D0_SOURCE_FEASIBILITY_PASS_SURVIVOR_CENSORED`

B13-B remains a pre-candidate and has not received a C13+ experiment ID.

## 2. Observed source census

- raw OKX launches in frozen 2026-01-01..2026-08-31 window: `206`;
- mature same-underlying Bybit-reference events: `7`;
- mature-reference launch months:
  - 2026-04;
  - 2026-05;
  - 2026-06;
  - 2026-07;
- dual-source-ready launch events: `7`.

All frozen D0 source gates passed:

- mature reference events >=6: PASS;
- launch months >=3: PASS;
- dual-source-ready events >=5: PASS.

## 3. Firewalls preserved

Observed false:

- historical trade body downloaded;
- historical trade body opened;
- price accessed;
- relative basis calculated;
- launch dislocation calculated;
- strategy signal calculated;
- execution model calculated;
- PnL calculated;
- candidate ID assigned;
- promotional alpha accessed.

## 4. Binding limitation

The D0 census is based on current public instrument catalogs.

Therefore:

`historical_launch_universe_complete = false`

and:

`survivor_censored_current_instrument_census = true`

D0 establishes source feasibility only.

It does not establish a complete historical launch universe and does not authorize a promotional historical price test.

## 5. Required next governance step

Before any price/headroom outcome:

1. freeze the exact 7 dual-source-ready event identities from the D0 report;
2. record the D0 report SHA256;
3. assess whether survivor-censored historical events may be used only as nonpromotional structural calibration;
4. preserve prospective future launch events as the only clean confirmation path;
5. freeze a launch-dislocation headroom sentinel only after this governance review.

No price body access is authorized by this PASS.
