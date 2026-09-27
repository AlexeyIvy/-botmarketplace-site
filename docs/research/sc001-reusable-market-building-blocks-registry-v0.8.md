# SC001 — Reusable Market Building Blocks Registry v0.8

Date: 2026-09-27
Status: **APPEND-ONLY CONTINUATION AFTER B13-C S0**
Parent: `sc001-reusable-market-building-blocks-registry-v0.7.md`

## 1. Inheritance

RB001-RB020 remain unchanged.

Binding extraction policy:

`docs/research/sc001-terminal-experiment-reusable-block-extraction-policy-v0.1.md`

## 2. New reusable block

### RB021 — Explicit pure-side liquidation-burst reversal state v0.1

- source evidence:
  - B13-C protected prospective Bybit liquidation stream;
  - S0 frozen simple 30-second reversal outcome;
- market/universe:
  12 frozen Bybit USDT perpetual symbols;
- exact event definition:
  - per symbol;
  - deterministic liquidation fingerprints;
  - inter-event gap <=5 seconds;
  - >=3 distinct events;
  - all events same liquidation side;
  - source-gap censoring +/-5 seconds around cluster;
- tested response:
  - wait 1 second after cluster end;
  - measure approximately 30-second signed reversal;
- valid-price sample:
  `1,793` clusters;
- observed directional behavior:
  - pooled median signed reversal = `+1.3682 bps`;
  - positive-cluster share = `55.884%`;
  - positive complete-day medians = `5/6`;
  - p25 = `-5.1393 bps`;
  - p75 = `+9.1050 bps`;
- parent strategy verdict:
  `B13C_S0_SIMPLE_REVERSAL_HEADROOM_REJECT`;
- rejection reason:
  economic magnitude far below frozen 30 bps gross-headroom hurdle;
- evidence strength:
  `WEAK_BROAD_PROSPECTIVE_DIRECTIONAL_STATE`;
- preferred future roles:
  - R2 liquidation/exhaustion state;
  - R3 confirmation or veto for an independently valid base mechanism;
  - R5 event-time execution/exit context;
- R1 standalone status:
  rejected for the tested unconditional 30-second architecture;
- reusable lesson:
  explicit forced-liquidation bursts contain a small but broad short-horizon reversal tendency; directionality can be real while standalone economic headroom is absent;
- forbidden reuse on the protected S0 interval:
  - liquidation-size threshold search;
  - event-count threshold search;
  - winner-symbol selection;
  - alternate cluster gaps;
  - alternate entry delays;
  - 5s/10s/60s/5m horizon scan;
  - sign flip;
- next valid use:
  define the role of RB021 inside a materially new mechanism before fresh post-definition evidence.

## 3. Method block retained from B13-C

The B13-C pipeline also reinforces the reusable source/analysis rule:

`DETERMINISTIC_EVENT_FINGERPRINT + SOURCE_GAP_CENSORING + CLUSTER_AS_INFERENCE_UNIT`

This is a research/clock primitive, not alpha.

Raw liquidation messages must not be treated as IID strategy samples when they belong to the same burst.

## 4. Parent-strategy distinction

B13-C S0 is terminal as:

`pure-side >=3-event cluster -> wait 1s -> 30s unconditional reversal`

RB021 remains reusable only as a scoped market-state primitive.

The registry entry must never be cited as evidence that the rejected S0 strategy is profitable.
