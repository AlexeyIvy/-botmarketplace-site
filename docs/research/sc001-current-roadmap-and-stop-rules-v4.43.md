# SC001 Current Roadmap and Stop Rules v4.43

Date: 2026-09-18  
Status: **CURRENT SC001 ROADMAP — C9 TERMINAL REJECT / C8-D0 SOURCE-CLOCK IMPLEMENTATION FROZEN NEXT**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v4.42.md`

## 1. Binding terminal states

C1-C6 remain terminal `REJECT_SENTINEL`.

C9-S1 remains terminal:

`C9_S1_REJECT_SENTINEL`

No C9 rescue tuning is authorized.

## 2. C9 knowledge retained

Current evidence artifacts:

- `docs/research/sc001-c9-s1-sentinel-result-readonly-postmortem-v0.1.md`;
- `docs/research/sc001-feature-evidence-registry-v0.3.md`;
- `docs/research/sc001-reusable-market-building-blocks-registry-v0.2.md`;
- `docs/research/sc001-strategy-landscape-v0.3.md`.

Key lesson:

scheduled funding state was frequent and measurable but produced essentially zero 30-minute mark/index normalization edge under the frozen mechanism.

## 3. Next orthogonal direction

Active branch:

`C8 — CROSS-VENUE SAME-ASSET`

Current stage:

`C8-D0 SOURCE / CLOCK SEMANTICS ONLY`

No cross-venue alpha is authorized.

## 4. Frozen venue/instrument engineering pair

Venue pair:

- OKX;
- Bybit.

Engineering pair:

- OKX `BTC-USDT-SWAP`;
- Bybit `BTCUSDT` linear perpetual.

This pair is selected for source/clock qualification only and is not the final C8 trading universe.

## 5. Fixed qualification date

C8-D0 historical archive identity date:

`2025-01-15 UTC`

This is the pre-existing SC001 Q001/Q002 qualification date.

No C8 outcome is inspected on this date.

## 6. C8-D0 frozen implementation

Protocol:

`docs/research/sc001-c8-d0-okx-bybit-source-clock-semantics-protocol-v0.1.md`

Runner:

`research/sc001/sc001_c8_d0_okx_bybit_source_clock_preflight_v0_1.py`

Freeze:

`docs/research/sc001-c8-d0-implementation-freeze-v0.1.json`

Frozen identities:

- protocol: `aae0ddce277ad78825ce4301ef3d4ad8cfa8f268`;
- runner: `47410abfbe9fb282a8bf725e36562b122cb999d1`.

## 7. D0 checks

D0 verifies:

1. OKX current contract mapping;
2. Bybit current contract mapping;
3. OKX current public trade timestamp schema;
4. Bybit current public trade timestamp schema;
5. OKX exact 2025-01-15 trade archive metadata/HEAD;
6. Bybit exact 2025-01-15 trade archive HEAD.

No archive body is opened.

## 8. Exact D0 states

PASS:

`C8_D0_SOURCE_CLOCK_PREFLIGHT_PASS`

REVIEW:

`C8_D0_SOURCE_CLOCK_PREFLIGHT_REVIEW`

REVIEW is an engineering/source state only.

## 9. D0 firewalls

Must remain false:

- historical archive body download/open;
- cross-venue price comparison;
- cross-venue return;
- dislocation;
- lag;
- leader selection;
- signal;
- PnL;
- promotional alpha.

## 10. Consequence of PASS

Only after D0 PASS may C8-D1 be designed.

C8-D1 will:

- download exact one-day trade bodies on both venues;
- verify historical archive schemas/timestamp units/order;
- define deterministic causal synchronization;
- run clock/synchronization golden tests;
- still calculate no cross-venue alpha.

## 11. Immediate next action

Run frozen C8-D0 source/clock preflight on VPS.

Do not open cross-venue trade bodies or outcome-bearing data until D0 PASS.
