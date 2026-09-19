# SC001 Current Roadmap and Stop Rules v4.87

Date: 2026-09-19
Status: **CURRENT SC001 ROADMAP — B13-A STRUCTURAL REJECT / B13-B SOURCE CENSUS NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.86.md`

## 1. Terminal/pre-candidate history

C11 remains terminal:

`C11_TERMINAL_REJECT_DIRECTION_CAPTURE`

C12 remains terminal:

`C12_S0_REJECT_PARITY_REVERSION`

B13-A is now structurally rejected:

`B13A_REJECT_STRUCTURAL`

No C13 ID was assigned.

## 2. B13-A reason

Across 6,634 matched OKX/Bybit funding settlements:

- median differential ~0.41 bps;
- p99 ~2.22 bps;
- maximum ~27.34 bps;
- >=50 bps events = 0.

The maximum itself is below the 40 bps four-fill structural burden.

No rescue.

## 3. Next independent mechanism

Advance B13-B only:

`SCHEDULED_NEW_PERPETUAL_LAUNCH_PRICE_DISCOVERY`

No candidate ID yet.

## 4. Required B13-B D0

Before any price headroom outcome:

1. enumerate recent OKX USDT-SWAP launch events from official instrument metadata;
2. require a mature same-underlying Bybit linear perpetual reference existing before the OKX launch;
3. verify exact launch-day historical trade-source availability on both venues;
4. record survivor-census limitation explicitly;
5. do not read trade bodies or prices.

## 5. Mature reference rule

Frozen for D0:

Bybit same-underlying linear perpetual launch time must be at least:

`90 calendar days`

before the OKX launch timestamp.

This is source maturity, not alpha selection.

## 6. D0 census window

Use completed recent history only:

`2026-01-01 00:00 UTC through 2026-08-31 23:59:59 UTC`

Reason:

- recent enough for current-source identity checks;
- fully completed before current research date;
- no partial September 2026.

## 7. D0 limitation

Current public instrument endpoints enumerate current instruments.

Therefore the first D0 census is explicitly:

`CURRENT-SURVIVOR SOURCE FEASIBILITY`

It cannot by itself claim a complete historical launch universe.

No price/headroom run may follow until this limitation is dispositioned.

## 8. Immediate next action

Freeze and run B13-B D0 source/event-census preflight.

No price or strategy outcome is authorized.
