# SC001 Current Roadmap and Stop Rules v4.53

Date: 2026-09-18
Status: **CURRENT SC001 ROADMAP — C8B-S0 TERMINAL REJECT / C10-D0 LOCAL L2 PREFLIGHT FROZEN NEXT**
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.52.md`

## 1. Binding terminal strategy states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal `C9_S1_REJECT_SENTINEL`.

C8B-S0 remains terminal:

`C8B_S0_REJECT_HEADROOM`

No rescue tuning is authorized.

## 2. C8B evidence layer updated

Current postmortem:

`docs/research/sc001-c8b-s0-headroom-result-readonly-postmortem-v0.1.md`

Current feature registry:

`docs/research/sc001-feature-evidence-registry-v0.4.md`

Current reusable-block registry:

`docs/research/sc001-reusable-market-building-blocks-registry-v0.3.md`

Current strategy landscape:

`docs/research/sc001-strategy-landscape-v0.4.md`

## 3. Active next direction

`C10 — L2 LIQUIDITY-VACUUM / REPLENISHMENT`

C10 must remain scientifically distinct from C5.

Initial C10 core uses order-book state only.

C5 aggressive-flow labels and RB005 are excluded from the base mechanism.

## 4. First C10 stage

Current stage:

`C10-D0 LOCAL BTC L2 ELIGIBILITY PREFLIGHT`

Purpose:

- verify the exact already-qualified local BTC L2 source;
- verify Q009B and E008 inventory parent states;
- open no L2 body;
- calculate no book feature or outcome.

## 5. Frozen pilot day

Pilot day:

`2024-02-12 UTC`

Selection rule:

`ordinary weekday in the already-qualified four-day Q1 BTC L2 set`

Other known qualified days:

- 2024-01-14 ordinary weekend;
- 2024-01-31 FOMC event day;
- 2024-02-13 CPI event day.

Pilot selection is metadata/context based, not price-outcome based.

## 6. Exact C10-D0 source

Expected:

`BTC-USDT-SWAP-L2orderbook-400lv-2024-02-12.tar.gz`

Expected size:

`601,976,188 bytes`

Expected local root:

`~/sc001_data/SC001_DATA_Q009B_OKX_L2_BATCH_B/2024-02-12/`

## 7. C10-D0 frozen implementation

Protocol:

`docs/research/sc001-c10-d0-local-btc-l2-eligibility-preflight-v0.1.md`

Runner:

`research/sc001/sc001_c10_d0_local_btc_l2_eligibility_v0_1.py`

Freeze:

`docs/research/sc001-c10-d0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `a51d158acb36d1a86cf210c7ea1c365e16cb4d08`;
- runner: `ad1b1c4936a12ef24a7acd5e198d10fe78330438`.

## 8. D0 firewalls

D0 must not:

- open/hash the L2 body;
- calculate spread/depth/microprice/book slope;
- identify a liquidity-vacuum event;
- calculate future move;
- run fills/queue/PnL;
- use C5 labels;
- access promotional alpha.

## 9. Exact D0 terminal states

PASS:

`C10_D0_LOCAL_L2_ELIGIBILITY_PASS`

REVIEW:

`C10_D0_LOCAL_L2_ELIGIBILITY_REVIEW`

REVIEW is local-data/engineering state only.

## 10. Consequence of PASS

Only after exact D0 PASS:

1. explicitly register C10 reuse of the already contaminated pilot body;
2. freeze one objective book-state event family;
3. freeze one future-move horizon;
4. freeze sample/magnitude gates;
5. implement a body-reading C10 sentinel;
6. keep fill/queue/PnL closed.

## 11. Immediate next action

Run frozen C10-D0 local L2 eligibility preflight on VPS.
