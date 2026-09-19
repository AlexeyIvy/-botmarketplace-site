# SC001 Current Roadmap and Stop Rules v4.88

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-A STRUCTURAL REJECT / B13-B D0 SOURCE CENSUS IMPLEMENTATION FROZEN**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.87.md`

## 1. Binding prior states

C11:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12:

`C12_S0_REJECT_PARITY_REVERSION`

B13-A:

`B13A_REJECT_STRUCTURAL`

No C13 ID assigned.

## 2. B13-B remains pre-candidate

B13-B mechanism:

`SCHEDULED_NEW_PERPETUAL_LAUNCH_PRICE_DISCOVERY`

Still:

`B13-B_NOT_YET_C13`

## 3. D0 purpose

Source/event-census feasibility only.

No price/headroom outcome.

## 4. Frozen D0 census

Window:

`2026-01-01 <= OKX listTime < 2026-09-01`

OKX:

- current live linear USDT SWAPs;
- official `listTime`.

Bybit reference:

- same-underlying LinearPerpetual USDT;
- launchTime at least 90 days earlier than OKX listTime.

Historical launch-day source metadata:

- OKX exact daily trade archive metadata + HEAD;
- Bybit exact public trade archive HEAD.

## 5. Survivor limitation

D0 explicitly uses current instrument catalogs.

Therefore:

`historical_launch_universe_complete = false`

even if D0 passes.

This is source feasibility only.

## 6. D0 PASS

`B13B_D0_SOURCE_FEASIBILITY_PASS_SURVIVOR_CENSORED`

requires:

- >=6 mature-reference events;
- >=3 launch months;
- >=5 dual-source-ready launch events.

REVIEW:

`B13B_D0_SOURCE_FEASIBILITY_REVIEW`

is source/design only, not a strategy reject.

## 7. Firewalls

No trade bodies.

No prices.

No relative basis.

No launch-dislocation outcome.

No execution/PnL.

No C13 assignment.

## 8. If D0 PASS

Do not open launch prices immediately.

First perform a completeness/governance review:

- historical survivor-census bias;
- official announcement cross-check availability;
- whether to use nonpromotional historical Selection only or switch B13-B to prospective-forward evidence.

Only after that review may a headroom sentinel be frozen.

## 9. Immediate next action

Run frozen B13-B D0 source census once.

Do not interpret partial event output.
