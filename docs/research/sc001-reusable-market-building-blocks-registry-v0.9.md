# SC001 — Reusable Market Building Blocks Registry v0.9

Date: 2026-09-27
Status: **APPEND-ONLY CONTINUATION AFTER B14-B**
Parent: `sc001-reusable-market-building-blocks-registry-v0.8.md`

## 1. Inheritance

RB001-RB021 remain unchanged.

## 2. New reusable block

### RB022 — Persistent cross-venue funding-differential direction state v0.1

- source evidence:
  B14-B fresh Jul-Sep 2026 OKX/Bybit public realized funding histories;
- universe:
  12 frozen USDT perpetual assets;
- event/state definition:
  last 3 matched realized funding differentials have the same nonzero sign;
- tested architecture:
  fixed-direction, non-overlapping 7-calendar-day carry;
- valid cycles:
  `110`;
- observed behavior:
  - median seven-day signed gross carry = `+1.3863 bps`;
  - positive-cycle share = `60.9091%`;
  - positive-median symbols = `8`;
  - positive-median months = `3`;
  - p25 = `-2.5951 bps`;
  - p75 = `+3.6405 bps`;
- parent strategy verdict:
  `B14B_REJECT_PERSISTENT_CARRY_STRUCTURAL`;
- rejection reason:
  economic magnitude far below 50 bps frozen gross-headroom hurdle and below four-fill structural burden;
- evidence strength:
  `WEAK_BROAD_PROSPECTIVE_DIRECTIONAL_STATE`;
- preferred future roles:
  - R2 funding/derivative regime state;
  - R3 confirmation/veto;
  - R4 holding-cost / capital-risk context;
  - R6 cross-venue funding-state reference;
- R1 standalone status:
  rejected for the tested 7-day carry architecture;
- reusable lesson:
  cross-venue realized funding differential can have persistent sign/breadth without enough magnitude to pay for a four-fill standalone carry trade;
- forbidden reuse on this window:
  - alternate hold horizon search;
  - funding magnitude threshold search;
  - confirmation-count search;
  - winner-symbol selection;
  - extreme-event subset mining;
  - adding basis PnL to rescue B14-B;
- next valid use:
  define an independent mechanism and the exact role of RB022 before fresh evidence is read.

## 3. Method lesson

B14-B reinforces:

`DIRECTIONAL PERSISTENCE != ECONOMIC SCALE`

A statistically broad state can still be unsuitable as a standalone strategy when the transfer magnitude is orders of magnitude below the structural execution burden.
