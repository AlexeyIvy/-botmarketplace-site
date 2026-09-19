# SC001 Current Roadmap and Stop Rules v4.92

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-B RAW S0 SURVIVE INVALIDATED BY IDENTITY AUDIT / BINDING DEFER SAMPLE**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.91.md`

## 1. Binding prior states

C11:
`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:
`C12_S0_REJECT_PARITY_REVERSION`

B13-A:
`B13A_REJECT_STRUCTURAL`

B13-B:
`B13-B_NOT_YET_C13`

## 2. B13-B raw runner output

Literal S0 runner output:

`B13B_S0_LAUNCH_DISLOCATION_HEADROOM_SURVIVE`

Raw:

- 7/7 coactive;
- 7/7 >=50 bps;
- median ~303.63 bps.

Preserved for audit trail only.

## 3. Mandatory semantic audit

Binding:

`docs/research/sc001-b13b-cross-venue-underlying-identity-audit-v0.1.md`

Two frozen events are not same-underlying pairs:

- BB: OKX stock/equity perpetual vs Bybit BounceBit crypto;
- QNT: OKX stock/equity perpetual vs Bybit Quant crypto.

Therefore D0 ticker-only pairing was semantically insufficient.

## 4. Binding S0 research state

Correct state:

`B13B_S0_DEFER_SAMPLE`

Reason:

`CROSS_VENUE_UNDERLYING_IDENTITY_FAILURE_2_OF_7`

Semantically valid maximum = 5/7, below frozen >=6/7 sample gate.

Do not promote the five-event subset.

## 5. Historical B13-B firewall

Do not:

- replace BB/QNT;
- expand historical window;
- lower sample gate;
- open convergence;
- build execution/PnL;
- assign C13.

Historical S0 evidence is contaminated calibration evidence only.

## 6. Descriptive signal

Five non-collision events all showed raw abs launch basis >50 bps.

This is mechanistically interesting but not a formal SURVIVE verdict.

## 7. Prospective B13-B path

B13-B may continue only prospectively.

Before any future launch price access, admission must verify:

- exact same underlying, not ticker alone;
- asset class;
- full project/company identity;
- quote denomination;
- contract/face-value semantics;
- mature Bybit reference >=90 days;
- exact source availability.

Future event identities must be frozen before outcome.

## 8. Immediate next action

Freeze a prospective B13-B event-admission protocol with mandatory underlying-identity and price-denomination checks.

No historical price/convergence run is authorized.

Because prospective B13-B now requires future events, parallel SC001 work may return to source feasibility for B13-C or a new independent-base design without altering B13-B.
